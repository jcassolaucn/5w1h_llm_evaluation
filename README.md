# 5W1H LLM Evaluation — Modular Runner

This repository evaluates 5W1H extractions with LLMs over pluggable datasets (e.g., BASSE, FLARES). It replaces the notebook with a scalable, configurable application. Pipelines are split into independent steps: preprocessing, preparation, evaluation, and validation.

## Project Structure
```
├── core/
│   ├── __init__.py
│   ├── config_loader.py          # YAML config loader
│   ├── datasets.py               # Dataset plugin registry (BASSE, FLARES)
│   ├── utils.py                  # IO helpers, filenames
├── evaluator/
│   ├── __init__.py               # Evaluator factory (selects provider)
│   ├── openai_runner.py          # OpenAI via Chat Completions + Tools
│   ├── anthropic_runner.py       # Claude via OpenAI client (base_url switch)
│   └── gemini_runner.py          # Gemini via OpenAI client (base_url switch)
├── preparation/
│   ├── basse_preparation.py
│   └── flares_preparation.py
├── preprocessing/
│   ├── basse_preprocessing.py
│   └── flares_preprocessing.py
├── prompts/
│   ├── system_evaluation_prompt_v4.txt
│   └── user_evaluation_prompt_v4.txt
├── pydantic_models/
│   └── output_pydantic_models.py
├── validation/
│   ├── create_expert_review_task.py
│   └── json_to_excel.py
├── data/
│   ├── basse/BASSE.jsonl
│   └── flares/*.json
├── results/
├── notebooks/                  # legacy notebooks (kept for reference)
├── main.py                     # Central runner
├── config.yaml                 # Your local config (copy from config.example.yaml)
├── config.example.yaml         # Sample config
├── requirements.txt
├── README.md
└── .env-example                # Example for environment variables                           
└── .env                        # your API keys (optional, if using python-dotenv)
```

## Quickstart
1. Install dependencies:
```
pip install -r requirements.txt
```

2. Create a config:
```
copy config.example.yaml config.yaml    # Windows
# or manually create/adjust config.yaml
```
Adjust `run.dataset`, `paths`, and `llm` settings as needed.

3. Set your API key(s) depending on the provider:
- OpenAI: set `OPENAI_API_KEY`
- Anthropic (Claude): set `ANTHROPIC_API_KEY`
- Google Gemini: set `GEMINI_API_KEY`

Options to set keys:
- Environment variables in your shell, e.g. PowerShell (current session):
  ```powershell
  $env:OPENAI_API_KEY = "..."; $env:ANTHROPIC_API_KEY = "..."; $env:GEMINI_API_KEY = "..."
  ```
- Or put them in a `.env` file and the app will load it automatically.

4. Choose provider and model in `config.yaml`:
```yaml
llm:
  provider: openai    # openai | anthropic | gemini
  model: gpt-5-mini-2025-08-07
run:
  verbose: true
validation:
  generate_review_task: true
  generate_excel: true   # also auto-creates an Excel next to the review JSON
```

5. Run the pipeline (all steps):
```
python main.py --step evaluate --dataset BASSE --limit 5
# or rely on config.yaml defaults: python main.py
```
Outputs are saved under `results/` with timestamped filenames, e.g.:
```
YYYY-MM-DD_HH-MM-SS_environment_DATASET_provider_model.json
```
If review generation is enabled, you will also get `*_review.json` and, if `generate_excel: true`, a `*_review.xlsx`.

### Run individual steps
- Preprocess only (produce internal doc objects):
```
python main.py --step preprocess --dataset FLARES --limit 10
```
- Prepare only (produce evaluation tasks):
```
python main.py --step prepare --dataset BASSE --limit 10
```

## Multi‑provider support (OpenAI, Anthropic/Claude, Gemini)
All providers are called via the OpenAI Python SDK. We only switch the API key and the base URL internally:
- openai: uses default base URL (no change).
- anthropic: `base_url = https://api.anthropic.com/v1/` and `ANTHROPIC_API_KEY`.
- gemini: `base_url = https://generativelanguage.googleapis.com/v1beta/openai/` and `GEMINI_API_KEY`.

You select the provider in `config.yaml` under `llm.provider`. Example values and models:
- `openai` → `gpt-5`, `o3`, `gpt-4.1`.
- `anthropic` → `claude-3-5-haiku-latest`, `claude-3-5-sonnet-latest`.
- `gemini` → `gemini-2.5-flash`, `gemini-2.5-pro`.

All evaluators use the same flow: Chat Completions with Tools (function calling) and forced call to `save_evaluation`. The tool output is parsed and validated against the Pydantic model `DetailedEvaluation`.

### Quick examples per provider
```powershell
# OpenAI
python main.py --step evaluate --dataset BASSE --limit 1

# Gemini
# In config.yaml: llm.provider: gemini, llm.model: gemini-2.5-flash
python main.py --step evaluate --dataset BASSE --limit 1

# Anthropic (Claude)
# In config.yaml: llm.provider: anthropic, llm.model: claude-3-5-haiku-latest
python main.py --step evaluate --dataset BASSE --limit 1
```
Ensure the corresponding API key is set in your environment or `.env`.

## Add a New Dataset
To support a new dataset (e.g., `MYDATA`) without touching the core pipeline:
1. Create preprocessing and preparation modules:
   - `preprocessing/mydata_preprocessing.py` → expose a function that returns a `List[dict]` of documents.
   - `preparation/mydata_preparation.py` → expose a generator that yields tasks `(doc_id, original_text, summary_to_evaluate, model_name)` for each document.
2. Register the dataset in `core/datasets.py` with two lightweight wrappers:
   - `_mydata_preprocess(cfg) -> List[Doc]`
   - `_mydata_prepare_tasks(doc) -> Iterable[Task]`
3. Add file paths in `config.yaml` under `paths:` and set `run.dataset: MYDATA`.
That’s it — the runner will pick it up. No other changes required.

## Configuration
See `config.example.yaml` for all options:
- `run`: environment, step, dataset, processing limits, and verbosity.
- `paths`: input data and output directories.
- `llm`: provider/model and generation parameters.
- `prompts`: template files used by the evaluator.
- `validation.generate_review_task`: also generate expert review JSON.
- `validation.generate_excel`: also generate the Excel file next to the review JSON.

## Validation: JSON → Excel
There are two ways to get the Excel for expert review:
- Automatically during `main.py` if `validation.generate_excel: true` and `validation.generate_review_task: true`.
- Or manually from any review JSON:
```
cd validation
python json_to_excel.py ..\results\your_results_review.json ..\results\review.xlsx
```

## Notes & troubleshooting
- Steps are independent: `preprocess` → `prepare` → `evaluate` → `validate` can run separately.
- The output is validated with Pydantic (`DetailedEvaluation`).
- If you see an API key error, confirm the env var is visible in your current shell:
  ```powershell
  python -c "import os; print(bool(os.getenv('OPENAI_API_KEY')))"  # or ANTHROPIC_API_KEY / GEMINI_API_KEY
  ```
- Models must support tool/function calling. If a model doesn’t return a tool call, the runner tries a JSON fallback and logs a helpful message when `run.verbose: true`.


## Run with Docker

You can run the evaluator in a container without installing local Python dependencies.

### 1) Build the image
```
docker build -t llm-as-a-judge-5w1h-eval:latest .
```

### 2) Prepare config and environment
- Copy `config.example.yaml` to `config.yaml` and adjust it as usual.
- Create a `.env` file with your API keys (the app auto-loads `.env`; Docker Compose also uses it):
  ```
  OPENAI_API_KEY=...
  ANTHROPIC_API_KEY=...
  GEMINI_API_KEY=...
  ```

### 3) Run with plain Docker
Examples below mount your local `data/` and `results/` so inputs/outputs stay on your host, and pass in `config.yaml`.

- Evaluate with defaults from `config.yaml`:
  ```powershell
  docker run --rm \
    -v ${PWD}/data:/app/data \
    -v ${PWD}/results:/app/results \
    -v ${PWD}/config.yaml:/app/config.yaml:ro \
    -e OPENAI_API_KEY=$env:OPENAI_API_KEY \
    -e ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY \
    -e GEMINI_API_KEY=$env:GEMINI_API_KEY \
    llm-as-a-judge-5w1h-eval:latest
  ```

- Override step/dataset/limit:
  ```powershell
  docker run --rm \
    -v ${PWD}/data:/app/data \
    -v ${PWD}/results:/app/results \
    -v ${PWD}/config.yaml:/app/config.yaml:ro \
    --env-file .env \
    llm-as-a-judge-5w1h-eval:latest \
    python main.py --step evaluate --dataset BASSE --limit 5
  ```

On PowerShell, `${PWD}` expands to the current directory. If using CMD, replace `${PWD}` with the full absolute path (e.g., `C:\Users\My_UserName\MyProject\5w1h-llm-evaluation`).

### 4) Run with Docker Compose
A `docker-compose.yml` is provided for convenience.

- Evaluate with defaults from `config.yaml`:
  ```powershell
  docker compose up --build
  ```

- Override parameters at runtime using environment variables (Compose injects them into the command):
  ```powershell
  $env:STEP="evaluate"; $env:DATASET="FLARES"; $env:LIMIT="10"
  docker compose up --build
  ```

- One-off runs without keeping the container:
  ```powershell
  docker compose run --rm app
  ```

Compose mounts these volumes by default:
- `./data -> /app/data`
- `./results -> /app/results`
- `./config.yaml -> /app/config.yaml:ro`

And it reads API keys from your local `.env` file (along with any other variables you include there).

### Notes for Docker usage
- The app loads environment variables from the container environment and from `.env` (thanks to `python-dotenv`). When using Compose, keep your keys in the `.env` file next to `docker-compose.yml`.
- Large datasets stay outside the image due to `docker-compose` volume mounts and `.dockerignore`.
- If you change only code (not `requirements.txt`), Docker layer caching will make rebuilds faster.
