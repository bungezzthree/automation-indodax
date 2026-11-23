# Load Test Results & Analysis

Run: 2026-11-23, step profile 2 → 5 → 8 → 10 RPS (150 s), target `https://dummy.restapiexample.com`,
single client IP. Raw output: `results/summary.md`, `results/report.html`, `results/locust_stats*.csv`.

## Result

| Requests | Failures | Error rate | Avg | p95 | p99 | Avg RPS | Peak RPS (3 s avg) |
|---|---|---|---|---|---|---|---|
| 1052 | 1049 | **99.71 %** | 267 ms | 340 ms | 640 ms | 6.96 | 10.33 |

**Verdict: FAIL** — latency SLAs and the 10 RPS ceiling pass, the error-rate SLA (≤ 5 %) fails.

| SLA | Actual | Threshold | |
|---|---|---|---|
| p95 latency | 340 ms | ≤ 2000 ms | PASS |
| p99 latency | 640 ms | ≤ 4000 ms | PASS |
| Avg latency | 267 ms | ≤ 1000 ms | PASS |
| Error rate | 99.71 % | ≤ 5 % | **FAIL** |
| Avg / peak RPS | 6.96 / 10.33 | ≤ 11 (10 + 10 %) | PASS |

## Analysis

1. **The target rate-limits this client, not the application collapsing.** 1049 of 1052 responses
   were HTTP 429 and only 3 requests succeeded across the whole run. Errors were 100 % already at
   the first step (2 RPS) and stayed flat up to 10 RPS, so there is no load "knee": the limit sits
   below 2 RPS for a single IP (consistent with earlier manual `curl` calls getting 429 within seconds).
2. **Latency is unaffected by load** (p95 ≈ 320–340 ms at 2, 5, 8 and 10 RPS) — but these are
   mostly 429 responses, which the limiter answers quickly. Latency says nothing about real
   capacity here; only 3 successful samples exist.
3. **No 5xx and no timeouts** — the backend did not fail; it protected itself.
4. **Conclusion:** capacity at 10 RPS cannot be assessed against this public service from one IP.
   For a meaningful result use a target without per-IP throttling (own instance / allow-listed IP),
   or distribute load. As a pass/fail signal the test is working: it detects and classifies the throttling.

## Caveats

* The first run measured a peak of 13 RPS using 1-second completion buckets; I changed the metric to a
  rolling 3 s average and ramp users at 1/s (instead of a synchronized burst) and re-ran. The 1 s
  figure is a completion-time artefact (count of finished responses), not 13 requests sent in a second,
  but it is the reason the metric was changed — the original and the revised definition differ.
* Locust prints a harmless `ValueError: I/O operation on closed file` from its CSV writer when the
  run ends in the `quitting` phase (seen in run 1; none in the rerun).
