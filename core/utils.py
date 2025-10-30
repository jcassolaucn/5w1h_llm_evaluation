from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text_file(path: Path) -> str:
    with path.open('r', encoding='utf-8') as f:
        return f.read()


def write_json(path: Path, data: Dict[str, Any]) -> None:
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def result_filename(env: str, dataset: str, provider: str, model: str, results_dir: Path) -> Path:
    # Normalize names similar to existing outputs
    dataset_up = dataset.upper()
    provider_norm = provider.replace('/', '_').replace(':', '_')
    model_norm = model.replace('/', '_').replace(':', '_').replace(' ', '_')
    ts = timestamp()
    name = f"{ts}_{env}_{dataset_up}_{provider_norm}_{model_norm}.json"
    return results_dir / name


def review_filename(base_json: Path) -> Path:
    return base_json.with_name(base_json.stem + "_review.json")
