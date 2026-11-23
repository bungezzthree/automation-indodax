"""Robot Framework variable file: resolves the active environment.

Usage:  robot --variablefile config/env_config.py:prod tests/
Resolution order (highest wins): env var  >  environments.yaml[env].
"""
import os
from pathlib import Path

import yaml

_CONFIG_FILE = Path(__file__).with_name("environments.yaml")
_SECRET_VARS = ("INDODAX_API_KEY", "INDODAX_API_SECRET")


def _override(name: str, default):
    """Env-var override that keeps the YAML value's type (int/float/bool/str)."""
    raw = os.getenv(name)
    if raw is None:
        return default
    if isinstance(default, bool):
        return raw.strip().lower() in ("1", "true", "yes")
    return type(default)(raw) if default is not None else raw


def get_variables(env: str | None = None) -> dict:
    config = yaml.safe_load(_CONFIG_FILE.read_text(encoding="utf-8"))
    env = (env or os.getenv("TEST_ENV") or config["default_env"]).lower()
    if env not in config["environments"]:
        raise ValueError(f"Unknown env '{env}'. Valid: {sorted(config['environments'])}")

    resolved = {key.upper(): _override(key.upper(), value)
                for key, value in config["environments"][env].items()}

    # Secrets are only ever read from the process environment, never from files.
    for secret in _SECRET_VARS:
        resolved[secret] = os.getenv(secret, "")

    resolved["ENV"] = env
    resolved["HAS_CREDENTIALS"] = all(resolved[s] for s in _SECRET_VARS)
    return resolved
