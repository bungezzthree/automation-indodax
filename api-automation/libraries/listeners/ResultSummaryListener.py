"""Robot Framework listener (API v3) that produces a machine-readable run summary.

Robot's own log.html/report.html are great for humans; CI bots, Slack notifiers and
dashboards need something smaller. This listener writes ``summary.json`` next to
output.xml with totals, per-feature breakdown, and every failure with its message
and tags - so a failed nightly can be triaged without opening the HTML log.

Usage: robot --listener libraries/listeners/ResultSummaryListener.py ...
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from robot.libraries.BuiltIn import BuiltIn

FEATURE_TAGS = {"pairs", "ticker", "orderbook", "trades", "summaries", "server-time", "auth",
                "market", "search", "orderbook-ui", "trade-history"}


class ResultSummaryListener:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self):
        self.started = datetime.now(timezone.utc)
        self.totals = defaultdict(int)
        self.by_feature = defaultdict(lambda: defaultdict(int))
        self.failures: list[dict] = []
        self.slowest: list[tuple[float, str]] = []
        self.output_dir: Path | None = None

    def start_suite(self, data, result):
        if self.output_dir is None:
            self.output_dir = Path(BuiltIn().get_variable_value("${OUTPUT DIR}", "."))

    def end_test(self, data, result):
        status = result.status  # PASS / FAIL / SKIP
        self.totals[status] += 1
        for tag in result.tags:
            if tag in FEATURE_TAGS:
                self.by_feature[tag][status] += 1
        self.slowest.append((result.elapsed_time.total_seconds(), result.longname))
        if status == "FAIL":
            self.failures.append({
                "test": result.longname,
                "message": result.message[:1000],
                "tags": sorted(result.tags),
                "priority": next((t for t in result.tags if t in ("P1", "P2", "P3")), "n/a"),
            })

    def close(self):
        total = sum(self.totals.values())
        executed = total - self.totals["SKIP"]
        summary = {
            "started_utc": self.started.isoformat(timespec="seconds"),
            "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "totals": {"total": total, **self.totals},
            "pass_rate_pct": round(100 * self.totals["PASS"] / executed, 2) if executed else None,
            "p1_failures": sum(1 for f in self.failures if f["priority"] == "P1"),
            "by_feature": {k: dict(v) for k, v in sorted(self.by_feature.items())},
            "slowest_tests": [{"test": n, "seconds": round(s, 2)}
                              for s, n in sorted(self.slowest, reverse=True)[:5]],
            "failures": self.failures,
        }
        out = (self.output_dir or Path(".")) / "summary.json"
        out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nRun summary written to {out}  "
              f"(pass={self.totals['PASS']} fail={self.totals['FAIL']} skip={self.totals['SKIP']})")
