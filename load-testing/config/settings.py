"""Load-test configuration. Every value can be overridden by an environment variable."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default, cast=str):
    raw = os.getenv(name)
    return cast(raw) if raw is not None else default


@dataclass(frozen=True)
class Settings:
    # Target
    host: str = _env("TARGET_HOST", "https://dummy.restapiexample.com")
    api_prefix: str = _env("API_PREFIX", "/api/v1")

    # Load model - each virtual user is paced to USER_RPS requests/second
    max_rps: float = _env("MAX_RPS", 10.0, float)           # hard ceiling from the assessment
    user_rps: float = _env("USER_RPS", 1.0, float)
    load_profile: str = _env("LOAD_PROFILE", "step")        # step | constant

    # SLA / pass-fail criteria (evaluated by listeners/sla_listener.py)
    sla_p95_ms: float = _env("SLA_P95_MS", 2000.0, float)
    sla_p99_ms: float = _env("SLA_P99_MS", 4000.0, float)
    sla_avg_ms: float = _env("SLA_AVG_MS", 1000.0, float)
    sla_error_rate_pct: float = _env("SLA_ERROR_RATE_PCT", 5.0, float)
    rps_tolerance_pct: float = _env("RPS_TOLERANCE_PCT", 10.0, float)   # allowed overshoot of MAX_RPS

    # Request
    request_timeout_s: float = _env("REQUEST_TIMEOUT_S", 10.0, float)
    results_dir: str = _env("RESULTS_DIR", "results")


SETTINGS = Settings()
