from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple

# Types
Doc = dict
Task = Tuple[str, str, str, str]  # doc_id, original_text, extraction_to_evaluate, model_name


@dataclass
class DatasetPlugin:
    name: str
    preprocess: Callable[[Dict], List[Doc]]  # takes config dict -> list of docs
    prepare_tasks: Callable[[Doc], Iterable[Task]]  # generator over a single doc -> tasks


# ---- BASSE plugin wrappers ---------------------------------------------------

def _basse_preprocess(cfg: Dict) -> List[Doc]:
    from pathlib import Path
    from preprocessing.basse_preprocessing import process_basse_extractions

    path = cfg.get('paths', {}).get('basse_jsonl')
    if not path:
        raise ValueError("Missing 'paths.basse_jsonl' in config for BASSE dataset")
    p = Path(path)
    return process_basse_extractions(str(p))


def _basse_prepare_tasks(doc: Doc):
    from preparation.basse_preparation import prepare_basse_tasks

    yield from prepare_basse_tasks(doc)


# ---- FLARES plugin wrappers --------------------------------------------------

def _flares_preprocess(cfg: Dict) -> List[Doc]:
    from preprocessing.flares_preprocessing import load_and_merge_datasets, process_and_flatten_data

    train = cfg.get('paths', {}).get('flares_train')
    trial = cfg.get('paths', {}).get('flares_trial')
    paths = [p for p in [train, trial] if p]
    if not paths:
        raise ValueError("Missing FLARES file paths in config ('paths.flares_train' and/or 'paths.flares_trial')")
    merged = load_and_merge_datasets(paths)
    flat = process_and_flatten_data(merged)
    return flat


def _flares_prepare_tasks(doc: Doc):
    from preparation.flares_preparation import prepare_flares_tasks

    yield from prepare_flares_tasks(doc)


# ---- Registry ----------------------------------------------------------------

_REGISTRY: Dict[str, DatasetPlugin] = {
    'BASSE': DatasetPlugin('BASSE', _basse_preprocess, _basse_prepare_tasks),
    'FLARES': DatasetPlugin('FLARES', _flares_preprocess, _flares_prepare_tasks),
}


def get_plugin(dataset_name: str) -> DatasetPlugin:
    key = (dataset_name or '').strip().upper()
    if key not in _REGISTRY:
        raise KeyError(f"Unknown dataset '{dataset_name}'. Available: {', '.join(_REGISTRY.keys())}")
    return _REGISTRY[key]
