"""Platform-agnostic helpers shared by web and mobile layers."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from robot.api.deco import keyword, library


@library(scope="GLOBAL", auto_keywords=False)
class UiHelpers:

    @keyword("Parse Indonesian Number")
    def parse_indonesian_number(self, text: str) -> Decimal:
        """Converts id-ID formatted text to Decimal.

        ``"18.291"`` -> 18291, ``"14564,73268944"`` -> 14564.73268944,
        ``"Rp 1.121.689.000"`` -> 1121689000, ``"+2.66%"`` -> 2.66 (percent keeps dot).
        """
        raw = str(text).strip()
        if raw.endswith("%"):
            return self._to_decimal(re.sub(r"[^0-9.\-]", "", raw), text)
        cleaned = re.sub(r"[^0-9,.\-]", "", raw).replace(".", "").replace(",", ".")
        return self._to_decimal(cleaned, text)

    @keyword("Format Locator")
    def format_locator(self, template: str, **values) -> str:
        """Fills a parametrised locator: ``Format Locator  ${ROW}  pair=ethidr``."""
        return template.format(**values)

    @keyword("Number Should Be Positive")
    def number_should_be_positive(self, value, label: str = "value"):
        if Decimal(str(value)) <= 0:
            raise AssertionError(f"{label} should be > 0 but was {value}")

    @keyword("Numbers Should Be Within Tolerance")
    def numbers_should_be_within_tolerance(self, actual, expected, tolerance_pct=1.0,
                                           label: str = "value"):
        a, e = Decimal(str(actual)), Decimal(str(expected))
        allowed = abs(e) * Decimal(str(tolerance_pct)) / 100
        if abs(a - e) > allowed:
            raise AssertionError(f"{label}: {a} differs from {e} by more than {tolerance_pct}%")

    @staticmethod
    def _to_decimal(value: str, original: str) -> Decimal:
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise AssertionError(f"'{original}' is not a number") from exc
