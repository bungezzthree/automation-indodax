"""Contract (JSON Schema) assertions. Schemas live in resources/schemas/."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from robot.api.deco import keyword, library

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "resources" / "schemas"


@library(scope="GLOBAL", auto_keywords=False)
class SchemaValidator:
    def __init__(self):
        self._cache: dict[str, Draft202012Validator] = {}

    @keyword("Json Should Match Schema")
    def json_should_match_schema(self, payload, schema_name: str):
        """Validates ``payload`` against ``resources/schemas/<schema_name>``.

        Reports *all* violations at once (not only the first) with their JSON path,
        which makes contract failures fast to triage.
        """
        validator = self._validator(schema_name)
        errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            lines = [f"  - at '{'/'.join(map(str, e.absolute_path)) or '<root>'}': {e.message}"
                     for e in errors[:20]]
            more = f"\n  ... and {len(errors) - 20} more" if len(errors) > 20 else ""
            raise AssertionError(f"Response does not match schema '{schema_name}' "
                                 f"({len(errors)} violation(s)):\n" + "\n".join(lines) + more)

    def _validator(self, schema_name: str) -> Draft202012Validator:
        if schema_name not in self._cache:
            schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            self._cache[schema_name] = Draft202012Validator(schema)
        return self._cache[schema_name]
