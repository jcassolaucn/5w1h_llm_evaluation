from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from openai import OpenAI

from core.utils import read_text_file
from pydantic_models.output_pydantic_models import DetailedEvaluation


@dataclass
class ModelConfig:
    provider: str
    model: str
    temperature: float = 0.0
    max_output_tokens: int = 1200


class OpenAIEvaluator:
    def __init__(self, cfg: Dict):
        llm = cfg.get('llm', {})
        self.model_cfg = ModelConfig(
            provider=llm.get('provider', 'openai'),
            model=llm.get('model', 'gpt-5-mini-2025-08-07'),
            temperature=float(llm.get('temperature', 0.2)),
            max_output_tokens=int(llm.get('max_output_tokens', 1200)),
        )
        prompts = cfg.get('prompts', {})
        self.system_prompt = read_text_file_path(prompts.get('system_prompt_path', 'prompts/system_evaluation_prompt.txt'))
        self.user_prompt_template = read_text_file_path(prompts.get('user_prompt_path', 'prompts/user_evaluation_prompt.txt'))

        # Logging / verbosity
        run_cfg = cfg.get('run', {})
        self.verbose: bool = bool(run_cfg.get('verbose', True))

        # Resolve API key: prefer env var, then optional cfg override at llm.api_key
        api_key = os.getenv("OPENAI_API_KEY") or llm.get('api_key')
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Set it as an environment variable, put it in a .env file, "
                "or provide llm.api_key in config.yaml. On Windows PowerShell: $env:OPENAI_API_KEY='...'; "
                "for persistent setx OPENAI_API_KEY '...' and open a new terminal."
            )
        # Initialize client with explicit key to avoid discovery issues
        self.client = OpenAI(api_key=api_key)
        if self.verbose:
            print(f"OpenAI client initialized. Model: {self.model_cfg.model}. Max tokens: {self.model_cfg.max_output_tokens}")

    def build_user_prompt(self, original_document: str, extraction_to_evaluate: str) -> str:
        return self.user_prompt_template.format(
            original_document=original_document,
            extraction_to_evaluate=extraction_to_evaluate,
        )

    def evaluate(self, tasks: Iterable[Tuple[str, str, str, str]]) -> List[Dict]:
        """
        Run evaluation over prepared tasks.
        Each task is a tuple: (doc_id, original_text, extraction_to_evaluate, model_name)
        Returns list of result dicts suitable for JSON serialization.
        """
        results: List[Dict] = []
        if self.verbose:
            print("=== EVALUATION START ===")
            print(f"Model: {self.model_cfg.model} | Max output tokens: {self.model_cfg.max_output_tokens}")
        for i, (doc_id, original_text, extraction, model_name) in enumerate(tasks, start=1):
            if self.verbose:
                short_doc = str(doc_id)
                if len(short_doc) > 80:
                    short_doc = short_doc[:77] + "..."
                print(f"[{i}] Evaluating doc_id={short_doc} | extraction_from={model_name} → calling OpenAI…")
            user_prompt = self.build_user_prompt(original_text, extraction)

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

            # Prefer tool calls (tools output is a JSON string in arguments)
            try:
                msg = completion.choices[0].message
                tool_calls = getattr(msg, "tool_calls", None) or []
                if tool_calls:
                    json_arguments = tool_calls[0].function.arguments  # str
                    evaluation = DetailedEvaluation.model_validate_json(json_arguments)
                else:
                    # Fallback: try to parse assistant content as JSON (legacy path)
                    content = msg.content or "{}"
                    raw_obj = json.loads(content)
                    evaluation = DetailedEvaluation.model_validate(raw_obj)
            except Exception:
                # Last-resort fallback to avoid crashing the whole batch
                content = (completion.choices[0].message.content or "{}")
                try:
                    raw_obj = json.loads(content)
                    evaluation = DetailedEvaluation.model_validate(raw_obj)
                except Exception as e:
                    # Do not stop iteration: record error and continue
                    if self.verbose:
                        print(f"[!] Parsing error for doc_id={doc_id} | model={model_name}: {e}")
                    usage = completion.usage
                    token_usage = {
                        "prompt_tokens": getattr(usage, 'prompt_tokens', None),
                        "completion_tokens": getattr(usage, 'completion_tokens', None),
                        "total_tokens": getattr(usage, 'total_tokens', None),
                    } if usage else {}
                    results.append({
                        "document_idx": doc_id,
                        "model_evaluated": model_name,
                        "evaluation_data": None,
                        "token_usage": token_usage,
                        "error": f"Pydantic parsing error: {e}",
                        "raw_output": content,
                    })
                    continue

            # Collect token usage if available
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


def read_text_file_path(path: str) -> str:
    from pathlib import Path
    p = Path(path)
    return read_text_file(p)
