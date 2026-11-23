"""Domain assertions for market data. Pure functions -> easy to unit test.

Prices/amounts come back from Indodax as *strings*; we compare them as Decimal to
avoid float rounding issues on 8-decimal crypto amounts.
"""
from __future__ import annotations

import time
from decimal import Decimal, InvalidOperation

from robot.api.deco import keyword, library


def _dec(value, field: str = "value") -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise AssertionError(f"{field} '{value}' is not numeric") from exc


@library(scope="GLOBAL", auto_keywords=False)
class MarketAssertions:

    @keyword("Should Be Positive Number")
    def should_be_positive_number(self, value, field: str = "value"):
        if _dec(value, field) <= 0:
            raise AssertionError(f"{field} must be > 0 but was {value}")

    @keyword("Should Be Non Negative Number")
    def should_be_non_negative_number(self, value, field: str = "value"):
        if _dec(value, field) < 0:
            raise AssertionError(f"{field} must be >= 0 but was {value}")

    @keyword("Value Should Be Between")
    def value_should_be_between(self, value, low, high, field: str = "value"):
        v, lo, hi = _dec(value, field), _dec(low, "low"), _dec(high, "high")
        if not lo <= v <= hi:
            raise AssertionError(f"{field}={v} is outside [{lo}, {hi}]")

    @keyword("Best Bid Should Not Exceed Best Ask")
    def best_bid_should_not_exceed_best_ask(self, bid, ask):
        if _dec(bid, "bid") > _dec(ask, "ask"):
            raise AssertionError(f"Crossed book: best bid {bid} > best ask {ask}")

    @keyword("Order Book Side Should Be Sorted")
    def order_book_side_should_be_sorted(self, levels: list, side: str):
        """``buy`` must be price-descending, ``sell`` price-ascending."""
        prices = [_dec(level[0], f"{side} price") for level in levels]
        expected = sorted(prices, reverse=(side == "buy"))
        if prices != expected:
            first_bad = next(i for i, (a, b) in enumerate(zip(prices, expected)) if a != b)
            raise AssertionError(f"{side} side not sorted at level {first_bad}: "
                                 f"{[str(p) for p in prices[max(0, first_bad - 2):first_bad + 3]]}")

    @keyword("Timestamp Should Be Recent")
    def timestamp_should_be_recent(self, epoch, max_drift_s: int = 300, unit: str = "s"):
        """Guards against stale/cached data. ``unit`` is ``s`` or ``ms``."""
        ts = float(epoch) / (1000 if unit == "ms" else 1)
        drift = abs(time.time() - ts)
        if drift > float(max_drift_s):
            raise AssertionError(f"Timestamp {epoch} drifts {drift:.0f}s from now "
                                 f"(allowed {max_drift_s}s)")

    @keyword("Response Time Should Be Within SLA")
    def response_time_should_be_within_sla(self, response, sla_ms):
        elapsed = response.elapsed.total_seconds() * 1000
        if elapsed > float(sla_ms):
            raise AssertionError(f"{response.request.method} {response.url} took {elapsed:.0f} ms "
                                 f"(SLA {sla_ms} ms)")

    @keyword("Pairs Should Have Unique Ids")
    def pairs_should_have_unique_ids(self, pairs: list):
        seen, dupes = set(), set()
        for p in pairs:
            (dupes if p["id"] in seen else seen).add(p["id"])
        if dupes:
            raise AssertionError(f"Duplicate pair ids: {sorted(dupes)}")

    @keyword("Find Pair By Id")
    def find_pair_by_id(self, pairs: list, pair_id: str) -> dict:
        for p in pairs:
            if p["id"] == pair_id:
                return p
        raise AssertionError(f"Pair '{pair_id}' not found among {len(pairs)} pairs")
