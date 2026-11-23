"""Locust entry point - composition only (no logic here).

  users/       -> who generates load (task mix, pacing)
  validators/  -> what a correct response is (assertions)
  listeners/   -> metrics collection, 10 RPS guard, SLA verdict + interpretation
  config/      -> thresholds and target, overridable by env vars

Run:  locust            (reads locust.conf: headless, step profile up to 10 RPS)
      LOAD_PROFILE=constant locust --users 10 --run-time 2m
"""
from config.settings import SETTINGS

# Listeners register themselves on import.
import listeners.metrics_collector  # noqa: F401
import listeners.rps_guard  # noqa: F401
import listeners.sla_listener  # noqa: F401
from users.employee_api_user import EmployeeApiUser  # noqa: F401

if SETTINGS.load_profile == "step":
    from users.load_shapes import StepLoadShape  # noqa: F401
