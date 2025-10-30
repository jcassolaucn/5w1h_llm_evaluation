from pathlib import Path
from typing import Any, Dict, Optional


def _read_text(path: Path) -> str:
    with path.open('r', encoding='utf-8') as f:
        return f.read()


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load YAML configuration. If no path is provided, tries `config.yaml` then `config.example.yaml`.
    """
    base = Path('.')
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        return _parse_yaml(path)

    # Try config.yaml then fallback to example
    primary = base / 'config.yaml'
    if primary.exists():
        return _parse_yaml(primary)

    fallback = base / 'config.example.yaml'
    if fallback.exists():
        return _parse_yaml(fallback)

    raise FileNotFoundError("No configuration file found. Please create `config.yaml` or copy `config.example.yaml`.")


def _parse_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "PyYAML is required to parse configuration files. Please install `pyyaml` or add it to requirements.txt"
        ) from e

    text = _read_text(path)
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Top-level YAML must be a mapping (dict). File: {path}")
    return data
