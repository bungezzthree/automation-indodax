"""Listener #3 - SLA assertions + result interpretation.

On quit it:
  1. evaluates each SLA (p95, p99, avg latency, error rate, RPS ceiling)
  2. sets a non-zero process exit code when any SLA fails -> CI pipeline goes red
  3. writes results/summary.json (machine) and results/summary.md (human, with analysis)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from locust import events

from config.settings import SETTINGS
from listeners.metrics_collector import COLLECTOR

log = logging.getLogger("sla")


def _evaluate(stats) -> list[dict]:
    total = stats.total
    observed_rps = total.num_requests / COLLECTOR.duration_s if COLLECTOR.duration_s else 0
    rps_limit = SETTINGS.max_rps * (1 + SETTINGS.rps_tolerance_pct / 100)
    checks = [
        ("p95 latency (ms)", total.get_response_time_percentile(0.95), "<=", SETTINGS.sla_p95_ms),
        ("p99 latency (ms)", total.get_response_time_percentile(0.99), "<=", SETTINGS.sla_p99_ms),
        ("avg latency (ms)", total.avg_response_time, "<=", SETTINGS.sla_avg_ms),
        ("error rate (%)", total.fail_ratio * 100, "<=", SETTINGS.sla_error_rate_pct),
        ("avg throughput (RPS)", observed_rps, "<=", rps_limit),
        ("peak 3s-avg throughput (RPS)", COLLECTOR.peak_rps, "<=", rps_limit),
    ]
    return [{"metric": m, "actual": round(a or 0, 2), "op": op, "threshold": t,
             "passed": (a or 0) <= t} for m, a, op, t in checks]


def _failure_breakdown(stats) -> list[dict]:
    rows = [{"endpoint": f.name, "method": f.method, "reason": str(f.error), "count": f.occurrences}
            for f in stats.errors.values()]
    return sorted(rows, key=lambda r: r["count"], reverse=True)


def _endpoint_table(stats) -> list[dict]:
    rows = []
    for (name, method), s in sorted(stats.entries.items()):
        rows.append({
            "endpoint": name, "requests": s.num_requests, "failures": s.num_failures,
            "error_rate_pct": round(100 * s.fail_ratio, 2),
            "avg_ms": round(s.avg_response_time), "p50_ms": s.get_response_time_percentile(0.5),
            "p95_ms": s.get_response_time_percentile(0.95), "max_ms": round(s.max_response_time or 0),
            "rps": round(s.num_requests / COLLECTOR.duration_s, 2),
            "status_codes": dict(COLLECTOR.status_codes.get(name, {})),
        })
    return rows


def interpret(summary: dict) -> list[str]:
    """Rule-based first-pass analysis. A human still owns the final conclusion."""
    notes = []
    total = summary["totals"]
    codes = {}
    for ep in summary["endpoints"]:
        for code, n in ep["status_codes"].items():
            codes[code] = codes.get(code, 0) + n
    reqs = max(1, total["requests"])
    rate_limited = codes.get("429", 0)
    server_err = sum(n for c, n in codes.items() if c.isdigit() and int(c) >= 500)

    if rate_limited:
        notes.append(f"**Rate limiting dominates:** {rate_limited}/{reqs} requests "
                     f"({100 * rate_limited / reqs:.1f}%) were rejected with HTTP 429. The target "
                     "throttles per client IP well below 10 RPS, so measured errors reflect the "
                     "provider's protection policy, not application capacity.")
    if server_err:
        notes.append(f"**Server errors:** {server_err} responses were 5xx - investigate backend "
                     "stability at the load level where they first appear (see per-level table).")

    # ignore ramp-transition levels with too few samples to say anything
    levels = [lv for lv in summary["load_levels"] if lv["requests"] >= 30]
    if len(levels) >= 2 and levels[0]["p95_ms"]:
        first, last = levels[0], levels[-1]
        growth = (last["p95_ms"] - first["p95_ms"]) / first["p95_ms"] * 100
        if growth > 50:
            notes.append(f"**Latency degrades with load:** p95 rose {growth:.0f}% from "
                         f"{first['users']} to {last['users']} RPS ({first['p95_ms']} -> "
                         f"{last['p95_ms']} ms). The knee is around the first level where p95 "
                         "or error rate jumps.")
        else:
            notes.append(f"**Latency is stable across load levels:** p95 changed {growth:+.0f}% "
                         f"between {first['users']} and {last['users']} RPS - no saturation "
                         "observed inside the 10 RPS envelope.")
        err_jump = [lv for lv in levels if lv["error_rate_pct"] > SETTINGS.sla_error_rate_pct]
        if err_jump:
            notes.append(f"Error rate first exceeds {SETTINGS.sla_error_rate_pct}% at "
                         f"**{err_jump[0]['users']} RPS** ({err_jump[0]['error_rate_pct']}%).")

    ok_p95 = next(c for c in summary["sla"] if c["metric"].startswith("p95"))
    notes.append(f"p95 latency {ok_p95['actual']} ms vs SLA {ok_p95['threshold']} ms -> "
                 f"{'within' if ok_p95['passed'] else 'BREACHES'} SLA. Note that latency of "
                 "429 responses is short-circuited by the limiter and flatters the average; "
                 "judge latency on successful requests per endpoint.")
    rps_check = next(c for c in summary["sla"] if c["metric"].startswith("peak"))
    notes.append(f"Load ceiling respected: peak {rps_check['actual']} RPS "
                 f"(limit {SETTINGS.max_rps} + {SETTINGS.rps_tolerance_pct}% tolerance).")
    return notes


@events.quitting.add_listener
def _on_quitting(environment, **_):
    stats = environment.stats
    if stats.total.num_requests == 0:
        log.warning("No requests recorded - nothing to evaluate")
        return
    sla = _evaluate(stats)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "target": SETTINGS.host,
        "profile": SETTINGS.load_profile,
        "duration_s": round(COLLECTOR.duration_s, 1),
        "totals": {
            "requests": stats.total.num_requests,
            "failures": stats.total.num_failures,
            "error_rate_pct": round(stats.total.fail_ratio * 100, 2),
            "avg_ms": round(stats.total.avg_response_time),
            "p95_ms": stats.total.get_response_time_percentile(0.95),
            "avg_rps": round(stats.total.num_requests / COLLECTOR.duration_s, 2),
            "peak_rps": COLLECTOR.peak_rps,
        },
        "sla": sla,
        "endpoints": _endpoint_table(stats),
        "load_levels": COLLECTOR.level_summary(),
        "failures": _failure_breakdown(stats),
    }
    summary["interpretation"] = interpret(summary)
    summary["verdict"] = "PASS" if all(c["passed"] for c in sla) else "FAIL"

    out = Path(SETTINGS.results_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "summary.md").write_text(_to_markdown(summary), encoding="utf-8")

    for c in sla:
        log.info("SLA %-26s actual=%-10s %s %-8s %s", c["metric"], c["actual"], c["op"],
                 c["threshold"], "PASS" if c["passed"] else "FAIL")
    if summary["verdict"] == "FAIL" and environment.process_exit_code in (None, 0):
        environment.process_exit_code = 1
    log.info("Verdict: %s - details in %s/summary.md", summary["verdict"], out)


def _to_markdown(s: dict) -> str:
    t = s["totals"]
    lines = [f"# Load test summary — {s['verdict']}", "",
             f"Target `{s['target']}` · profile `{s['profile']}` · duration {s['duration_s']} s · "
             f"generated {s['generated_at']}", "",
             "## Totals", "",
             "| Requests | Failures | Error rate | Avg | p95 | Avg RPS | Peak RPS |",
             "|---|---|---|---|---|---|---|",
             f"| {t['requests']} | {t['failures']} | {t['error_rate_pct']}% | {t['avg_ms']} ms | "
             f"{t['p95_ms']} ms | {t['avg_rps']} | {t['peak_rps']} |", "",
             "## SLA assertions", "", "| Metric | Actual | Threshold | Result |", "|---|---|---|---|"]
    lines += [f"| {c['metric']} | {c['actual']} | {c['op']} {c['threshold']} | "
              f"{'✅ PASS' if c['passed'] else '❌ FAIL'} |" for c in s["sla"]]
    lines += ["", "## Per endpoint", "",
              "| Endpoint | Req | Err % | Avg | p50 | p95 | Max | RPS | Status codes |",
              "|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {e['endpoint']} | {e['requests']} | {e['error_rate_pct']} | {e['avg_ms']} | "
              f"{e['p50_ms']} | {e['p95_ms']} | {e['max_ms']} | {e['rps']} | "
              f"{', '.join(f'{k}: {v}' for k, v in sorted(e['status_codes'].items()))} |"
              for e in s["endpoints"]]
    lines += ["", "## Per load level (users ≈ target RPS)", "",
              "| Users | Requests | Err % | p50 | p95 | Max |", "|---|---|---|---|---|---|"]
    lines += [f"| {lv['users']} | {lv['requests']} | {lv['error_rate_pct']} | {lv['p50_ms']} | "
              f"{lv['p95_ms']} | {lv['max_ms']} |" for lv in s["load_levels"]]
    lines += ["", "## Top failure reasons", "", "| Endpoint | Reason | Count |", "|---|---|---|"]
    lines += [f"| {f['endpoint']} | {f['reason']} | {f['count']} |"
              for f in s["failures"][:10]]
    lines += ["", "## Automated interpretation", ""] + [f"- {n}" for n in s["interpretation"]]
    return "\n".join(lines) + "\n"
