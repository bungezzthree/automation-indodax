"""Response assertions used inside `catch_response` blocks.

Each validator raises ``ValidationError`` with a short, *stable* reason. Stable reasons
matter: Locust groups failures by message, so "HTTP 429 rate limited" aggregates into one
row instead of hundreds of unique strings (which would hide the signal in the report).
"""
from __future__ import annotations

from typing import Any

EMPLOYEE_FIELDS = {"id", "employee_name", "employee_salary", "employee_age"}


class ValidationError(Exception):
    pass


def check_status(response, expected: int = 200) -> None:
    code = response.status_code
    if code == expected:
        return
    if code == 0:
        raise ValidationError("Connection error / timeout (no HTTP response)")
    if code == 429:
        raise ValidationError("HTTP 429 rate limited")
    if code >= 500:
        raise ValidationError(f"HTTP {code} server error")
    raise ValidationError(f"HTTP {code} unexpected (expected {expected})")


def json_body(response) -> dict[str, Any]:
    try:
        return response.json()
    except ValueError as exc:
        raise ValidationError("Body is not JSON") from exc


def check_success_envelope(body: dict) -> None:
    if body.get("status") != "success":
        raise ValidationError(f"status != success ({body.get('status')!r})")
    if "data" not in body:
        raise ValidationError("'data' missing from envelope")


def check_employee(employee: dict) -> None:
    missing = EMPLOYEE_FIELDS - employee.keys()
    if missing:
        raise ValidationError(f"employee missing fields {sorted(missing)}")
    if not isinstance(employee["id"], int) or employee["id"] <= 0:
        raise ValidationError("employee.id must be a positive int")


def validate_employee_list(response) -> list[dict]:
    check_status(response)
    body = json_body(response)
    check_success_envelope(body)
    data = body["data"]
    if not isinstance(data, list) or not data:
        raise ValidationError("employee list empty")
    check_employee(data[0])
    return data


def validate_single_employee(response, expected_id: int) -> dict:
    check_status(response)
    body = json_body(response)
    check_success_envelope(body)
    data = body["data"]
    if not data:
        raise ValidationError("employee not found")
    check_employee(data)
    if data["id"] != expected_id:
        raise ValidationError("returned employee id mismatch")
    return data


def validate_created_employee(response, payload: dict) -> dict:
    check_status(response)
    body = json_body(response)
    check_success_envelope(body)
    data = body["data"]
    for key, value in payload.items():
        if str(data.get(key)) != str(value):
            raise ValidationError(f"created employee field '{key}' not echoed")
    return data


def validate_deleted(response) -> None:
    check_status(response)
    check_success_envelope(json_body(response))
