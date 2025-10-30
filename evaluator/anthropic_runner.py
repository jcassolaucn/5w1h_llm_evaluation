from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from openai import OpenAI
from pydantic_models.output_pydantic_models import DetailedEvaluation


Task = Tuple[str, str, str, str]


@dataclass
class ModelConfig:
    provider: str
    model: str
    temperature: float = 0.0
    max_output_tokens: int = 1200


class AnthropicEvaluator:
    """
    Anthropic runner implemented via the OpenAI Python client by switching base_url and API key,
    mirroring the notebook's approach.
    """
    def __init__(self, cfg: Dict):
        llm = cfg.get('llm', {})
        self.model_cfg = ModelConfig(
            provider=llm.get('provider', 'anthropic'),
            model=llm.get('model', 'claude-3-5-haiku-latest'),
            temperature=float(llm.get('temperature', 0.2)),
            max_output_tokens=int(llm.get('max_output_tokens', 1200)),
        )

        prompts = cfg.get('prompts', {})
        from core.utils import read_text_file
        from pathlib import Path
        self.system_prompt = read_text_file(Path(prompts.get('system_prompt_path', 'prompts/system_evaluation_prompt.txt')))
        self.user_prompt_template = read_text_file(Path(prompts.get('user_prompt_path', 'prompts/user_evaluation_prompt.txt')))

        run_cfg = cfg.get('run', {})
        self.verbose: bool = bool(run_cfg.get('verbose', True))

        # Build OpenAI-compatible client targeting Anthropic endpoint
        api_key = os.getenv("ANTHROPIC_API_KEY") or llm.get('api_key')
        base_url = "https://api.anthropic.com/v1/"
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Set it as an environment variable, put it in a .env file, "
                "or provide llm.api_key in config.yaml."
            )
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        if self.verbose:
            print(f"OpenAI client (Anthropic via base_url) initialized. Model: {self.model_cfg.model}. Max tokens: {self.model_cfg.max_output_tokens}")

    def build_user_prompt(self, original_document: str, extraction_to_evaluate: str) -> str:
        return self.user_prompt_template.format(
            original_document=original_document,
            extraction_to_evaluate=extraction_to_evaluate,
        )

    def evaluate(self, tasks: Iterable[Task]) -> List[Dict]:
        results: List[Dict] = []
        if self.verbose:
            print("=== EVALUATION START (Anthropic via OpenAI client) ===")
            print(f"Model: {self.model_cfg.model} | Max output tokens: {self.model_cfg.max_output_tokens}")

        for i, (doc_id, original_text, extraction, model_name) in enumerate(tasks, start=1):
            if self.verbose:
                short_doc = str(doc_id)
                if len(short_doc) > 80:
                    short_doc = short_doc[:77] + "..."
                print(f"[{i}] Evaluating doc_id={short_doc} | summary_from={model_name} → calling Anthropic (OpenAI client)…")

            user_prompt = self.build_user_prompt(original_text, extraction)

            # Use OpenAI Chat Completions with function tools, forcing the call, identical to openai runner
            completion = self.client.chat.completions.create(
                model=self.model_cfg.model,
                # temperature=self.model_cfg.temperature,
                max_completion_tokens=self.model_cfg.max_output_tokens,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "save_evaluation",
                            "description": "Saves the structured evaluation result of an extraction.",
                            "parameters": DetailedEvaluation.model_json_schema(),
                        },
                    }
                ],
                tool_choice={"type": "function", "function": {"name": "save_evaluation"}},
            )

            # Parse tool call arguments (JSON string)
            try:
                msg = completion.choices[0].message
                tool_calls = getattr(msg, "tool_calls", None) or []
                if tool_calls:
                    json_arguments = tool_calls[0].function.arguments  # str
                    evaluation = DetailedEvaluation.model_validate_json(json_arguments)
                else:
                    content = msg.content or "{}"
                    evaluation = DetailedEvaluation.model_validate(json.loads(content))
            except Exception as e:
                if self.verbose:
                    print(f"[!] Parsing error for doc_id={doc_id} | model={model_name}: {e}")
                raise RuntimeError(f"Failed to parse model output as DetailedEvaluation: {e}")

            usage = completion.usage
            token_usage = {
                "prompt_tokens": getattr(usage, 'prompt_tokens', None),
                "completion_tokens": getattr(usage, 'completion_tokens', None),
                "total_tokens": getattr(usage, 'total_tokens', None),
            } if usage else {}

            if self.verbose:
                pt = token_usage.get("prompt_tokens")
                ct = token_usage.get("completion_tokens")
                tt = token_usage.get("total_tokens")
                print(f"    ✓ Received evaluation. Tokens: prompt={pt} | completion={ct} | total={tt}")

            results.append({
                "document_idx": doc_id,
                "model_evaluated": model_name,
                "evaluation_data": evaluation.model_dump(),
                "token_usage": token_usage,
            })

        if self.verbose:
            total = sum(((r.get("token_usage", {}) or {}).get("total_tokens") or 0) for r in results)
            print(f"=== EVALUATION END — items: {len(results)}, total_tokens: {total} ===")
        return results
