"""Virtual user modelling a client of the dummy Employee REST API.

Traffic mix (weights) - read-heavy, as typical for a public API:
  60%  GET  /employees          list
  25%  GET  /employee/{id}      detail
  10%  POST /create             write
   5%  DELETE /delete/{id}      write
Tags allow selective runs:  locust --tags read   |   locust --exclude-tags write
"""
from __future__ import annotations

import random

from locust import HttpUser, constant_throughput, tag, task

from config.settings import SETTINGS
from validators.response_validators import (ValidationError, validate_created_employee,
                                            validate_deleted, validate_employee_list,
                                            validate_single_employee)

KNOWN_EMPLOYEE_IDS = list(range(1, 25))   # the dummy API ships 24 seeded employees


class EmployeeApiUser(HttpUser):
    host = SETTINGS.host
    # Pacing: each user issues at most USER_RPS requests/second, independent of latency.
    # Total RPS = users x USER_RPS -> the load shape controls users to respect MAX_RPS.
    wait_time = constant_throughput(SETTINGS.user_rps)

    def on_start(self):
        self.client.headers.update({"Accept": "application/json",
                                    "User-Agent": "locust-poc/1.0"})

    # ---------------------------------------------------------------- helpers
    def _call(self, method: str, path: str, name: str, validator, **kwargs):
        url = f"{SETTINGS.api_prefix}{path}"
        with self.client.request(method, url, name=name, catch_response=True,
                                 timeout=SETTINGS.request_timeout_s, **kwargs) as resp:
            try:
                validator(resp)
                resp.success()
            except ValidationError as exc:
                resp.failure(str(exc))

    # ------------------------------------------------------------------ tasks
    @tag("read")
    @task(12)
    def list_employees(self):
        self._call("GET", "/employees", "GET /employees", validate_employee_list)

    @tag("read")
    @task(5)
    def get_employee(self):
        emp_id = random.choice(KNOWN_EMPLOYEE_IDS)
        self._call("GET", f"/employee/{emp_id}", "GET /employee/{id}",
                   lambda r: validate_single_employee(r, emp_id))

    @tag("write")
    @task(2)
    def create_employee(self):
        payload = {"name": f"qa-load-{random.randint(1000, 9999)}",
                   "salary": str(random.randint(1_000, 9_000)), "age": str(random.randint(20, 60))}
        self._call("POST", "/create", "POST /create",
                   lambda r: validate_created_employee(r, payload), json=payload)

    @tag("write")
    @task(1)
    def delete_employee(self):
        emp_id = random.choice(KNOWN_EMPLOYEE_IDS)
        self._call("DELETE", f"/delete/{emp_id}", "DELETE /delete/{id}", validate_deleted)
