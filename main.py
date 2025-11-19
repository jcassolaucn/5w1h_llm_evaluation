from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Tuple
import os

# Load environment variables from a .env file if present (before importing anything that might use them)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # If python-dotenv is not available or any error occurs, continue; environment variables may still be set externally
    pass

from core.config_loader import load_config
from core.datasets import get_plugin
from core.utils import ensure_dir, result_filename, review_filename, write_json
from evaluator import get_evaluator
from validation.create_expert_review_task import create_expert_review_task
from validation.json_to_excel import create_excel_for_review


Task = Tuple[str, str, str, str]  # doc_id, original_text, extraction_to_evaluate, model_name


def iter_tasks(plugin_name: str, cfg: dict, limit: int | None = None) -> Iterable[Task]:
    plugin = get_plugin(plugin_name)

    run_cfg = cfg.get('run', {})
    verbose: bool = bool(run_cfg.get('verbose', True))

    # Step 1: Preprocess -> docs
    if verbose:
        print(f"=== PREPROCESS START [{plugin_name}] ===")
    docs = plugin.preprocess(cfg)
    if limit and limit > 0:
        docs = docs[:limit]
    if verbose:
        print(f"Preprocess: produced {len(docs)} docs for dataset {plugin_name}")
        if docs:
            example_keys = list(docs[0].keys())[:8]
            print(f"Preprocess: first doc keys: {example_keys}")

    # Step 2: Prepare -> tasks
    if verbose:
        print(f"=== PREPARE START [{plugin_name}] ===")
    produced = 0
    for doc in docs:
        for task in plugin.prepare_tasks(doc):
            yield task
            produced += 1
            if verbose and produced % 10 == 0:
                print(f"Prepare: yielded {produced} tasks…")
            if limit and limit > 0 and produced >= limit:
                if verbose:
                    print(f"Prepare: reached limit {limit}.")
                return


def run_preprocess_only(dataset: str, cfg: dict, limit: int | None = None) -> List[dict]:
    plugin = get_plugin(dataset)
    docs = plugin.preprocess(cfg)
    if limit and limit > 0:
        docs = docs[:limit]
    print(f"Preprocess: produced {len(docs)} docs for dataset {dataset}")
    return docs


def run_prepare_only(dataset: str, cfg: dict, limit: int | None = None) -> List[Task]:
    plugin = get_plugin(dataset)
    docs = plugin.preprocess(cfg)
    if limit and limit > 0:
        docs = docs[:limit]
    tasks: List[Task] = []
    for doc in docs:
        for t in plugin.prepare_tasks(doc):
            tasks.append(t)
            if limit and limit > 0 and len(tasks) >= limit:
                break
        if limit and limit > 0 and len(tasks) >= limit:
            break
    print(f"Prepare: produced {len(tasks)} tasks for dataset {dataset}")
    return tasks


def run_evaluate(dataset: str, cfg: dict, limit: int | None = None) -> dict:
    env = cfg.get('run', {}).get('environment', 'development')
    provider = cfg.get('llm', {}).get('provider', 'openai')
    model = cfg.get('llm', {}).get('model', 'gpt-5-mini-2025-08-07')
    verbose = bool(cfg.get('run', {}).get('verbose', True))

    results_dir = Path(cfg.get('paths', {}).get('results_dir', 'results'))
    ensure_dir(results_dir)

    if verbose:
        print(f"=== EVALUATE START [{dataset}] ===")
        print(f"Env={env} | Provider={provider} | Model={model} | Limit={limit if limit else 'no limit'}")
        print("Building tasks and initializing evaluator…")

    evaluator = get_evaluator(cfg)

    # Build tasks once (cache) to avoid re-running preprocess/prepare
    tasks = list(iter_tasks(dataset, cfg, limit=limit))
    results_list = evaluator.evaluate(iter(tasks))

    # Build final JSON structure similar to existing outputs
    final = {
        "total_tokens": sum((r.get("token_usage", {}) or {}).get("total_tokens", 0) or 0 for r in results_list),
        "results": results_list,
    }

    results_path = result_filename(env, dataset, provider, model, results_dir)
    write_json(results_path, final)
    print(f"Saved evaluation results to: {results_path}")

    # Optional: generate review tasks JSON
    if (cfg.get('validation', {}) or {}).get('generate_review_task', False):
        review_objects = []
        
        # Use cached tasks to extract original_text and extraction without re-running preprocess/prepare
        for r, t in zip(results_list, tasks):
            doc_id, original_text, extraction_to_evaluate, model_name = t
            from pydantic_models.output_pydantic_models import DetailedEvaluation
            evaluation_object = DetailedEvaluation.model_validate(r["evaluation_data"])  # type: ignore
            review_obj = create_expert_review_task(
                doc_id=doc_id,
                model_name=model_name,
                original_text=original_text,
                extraction_to_evaluate=extraction_to_evaluate,
                evaluation_object=evaluation_object,
            )
            review_objects.append(review_obj)

        review_json = {
            "review_batch_info": {
                "dataset": dataset,
                "environment": env,
                "provider": provider,
                "model": model,
            },
            "review_items": review_objects,
        }
        review_path = review_filename(results_path)
        write_json(review_path, review_json)
        print(f"Saved expert review tasks to: {review_path}")

        # Optional: also create an Excel file for expert review if enabled
        if (cfg.get('validation', {}) or {}).get('generate_excel', False):
            try:
                excel_path = review_path.with_suffix('.xlsx')
                print(f"=== GENERATE EXCEL REVIEW FILE START ===")
                create_excel_for_review(str(review_path), str(excel_path))
                print(f"Saved expert review Excel to: {excel_path}")
                print(f"=== GENERATE EXCEL REVIEW FILE END ===")
            except Exception as e:
                print(f"Warning: Failed to create Excel review file: {e}")

    return final


def main():
    parser = argparse.ArgumentParser(description="5W1H LLM Evaluation Runner")
    parser.add_argument("--config", type=str, default=None, help="Path to YAML config file")
    parser.add_argument("--dataset", type=str, default=None, help="Override dataset name (e.g., BASSE, FLARES)")
    parser.add_argument("--step", type=str, default=None, help="Override step: preprocess|prepare|evaluate|validate|all")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of docs/tasks")
    args = parser.parse_args()

    cfg = load_config(args.config)

    dataset = args.dataset or cfg.get('run', {}).get('dataset', 'BASSE')
    step = (args.step or cfg.get('run', {}).get('step', 'all')).lower()
    limit = args.limit if args.limit is not None else cfg.get('run', {}).get('limit', None)

    if step in ("all", "evaluate"):
        run_evaluate(dataset, cfg, limit=limit)
    elif step == "preprocess":
        run_preprocess_only(dataset, cfg, limit=limit)
    elif step == "prepare":
        run_prepare_only(dataset, cfg, limit=limit)
    else:
        raise ValueError(f"Unsupported step: {step}")


if __name__ == "__main__":
    main()
