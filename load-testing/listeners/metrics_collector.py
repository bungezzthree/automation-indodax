"""Listener #1 - collects raw metrics Locust does not aggregate by itself.

* status-code distribution per endpoint (Locust only keeps failure messages)
* latency samples grouped by load level (active users == target RPS), to locate the knee
* per-second request counts, to prove the 10 RPS ceiling was respected
"""
from __future__ import annotations

import time
from collections import Counter, defaultdict

from locust import events


def percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    k = max(0, min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1))))
    return ordered[k]


class MetricsCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.started_at: float | None = None
        self.finished_at: float | None = None
        self.status_codes: dict[str, Counter] = defaultdict(Counter)
        self.latency_by_level: dict[int, list[float]] = defaultdict(list)
        self.errors_by_level: dict[int, int] = defaultdict(int)
        self.requests_per_second: Counter = Counter()

    # ------------------------------------------------------------- derived data
    @property
    def duration_s(self) -> float:
        if not self.started_at:
            return 0.0
        return max(1e-6, (self.finished_at or time.time()) - self.started_at)

    @property
    def peak_rps(self) -> float:
        """Highest average RPS over any rolling 3 s window.

        Completions (not sends) are counted, so single 1 s buckets jitter when a slow
        response and its successors finish together. A 3 s window removes that artefact
        while still catching sustained overshoot (the rps_guard uses the same 3 s idea).
        """
        window = 3
        if not self.requests_per_second:
            return 0.0
        first, last = min(self.requests_per_second), max(self.requests_per_second) - 1  # drop partial last second
        if last - first + 1 < window:
            return float(max(self.requests_per_second.values()))
        counts = [self.requests_per_second.get(t, 0) for t in range(first, last + 1)]
        return round(max(sum(counts[i:i + window]) / window for i in range(len(counts) - window + 1)), 2)

    def level_summary(self) -> list[dict]:
        rows = []
        for level in sorted(self.latency_by_level):
            samples = self.latency_by_level[level]
            errors = self.errors_by_level.get(level, 0)
            rows.append({
                "users": level,
                "requests": len(samples),
                "error_rate_pct": round(100 * errors / len(samples), 2) if samples else 0.0,
                "p50_ms": round(percentile(samples, 50)),
                "p95_ms": round(percentile(samples, 95)),
                "max_ms": round(max(samples)) if samples else 0,
            })
        return rows


COLLECTOR = MetricsCollector()


@events.test_start.add_listener
def _on_test_start(environment, **_):
    COLLECTOR.reset()
    COLLECTOR.started_at = time.time()


_RUNNER = {"ref": None}


@events.init.add_listener
def _on_init(environment, **_):
    _RUNNER["ref"] = environment.runner


@events.request.add_listener
def _on_request(name, response_time, response=None, exception=None, **_):
    code = getattr(response, "status_code", 0) if response is not None else 0
    COLLECTOR.status_codes[name][str(code or "conn-error")] += 1
    runner = _RUNNER["ref"]
    level = getattr(runner, "user_count", 0) if runner else 0   # users == target RPS level
    COLLECTOR.latency_by_level[level].append(response_time)
    if exception is not None:
        COLLECTOR.errors_by_level[level] += 1
    COLLECTOR.requests_per_second[int(time.time())] += 1


@events.test_stop.add_listener
def _on_test_stop(environment, **_):
    COLLECTOR.finished_at = time.time()
