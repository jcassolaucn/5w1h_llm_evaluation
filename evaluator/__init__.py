from __future__ import annotations

from typing import Dict, Protocol, Iterable, List, Tuple


Task = Tuple[str, str, str, str]


class Evaluator(Protocol):
    def evaluate(self, tasks: Iterable[Task]) -> List[Dict]:
        ...


def get_evaluator(cfg: Dict) -> Evaluator:
    provider = (cfg.get('llm', {}) or {}).get('provider', 'openai').strip().lower()
    if provider == 'openai':
        from .openai_runner import OpenAIEvaluator
        return OpenAIEvaluator(cfg)
    elif provider in ('anthropic', 'claude'):
        from .anthropic_runner import AnthropicEvaluator
        return AnthropicEvaluator(cfg)
    elif provider in ('gemini', 'google', 'googleai', 'google-genai'):
        from .gemini_runner import GeminiEvaluator
        return GeminiEvaluator(cfg)
    else:
        raise ValueError(f"Unknown LLM provider '{provider}'. Supported: openai | anthropic | gemini")
