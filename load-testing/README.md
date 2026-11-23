# Load Testing — Locust vs dummy.restapiexample.com (max 10 RPS)

## Quick start

```powershell
cd load-testing
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
locust                                   # headless, step profile 2→5→8→10 RPS (locust.conf)
$env:LOAD_PROFILE="constant"; locust --users 10 --run-time 2m   # flat 10 RPS
locust --tags read                       # selective: read endpoints only
```

Outputs in `results/`: `report.html` (Locust), `locust_stats*.csv` (time series),
`summary.json` + **`summary.md`** (SLA verdict + interpretation), `locust.log`.
Exit code: `0` all SLAs pass · `1` SLA breach · `2` RPS guard tripped.

## Structure

```
load-testing/
├── locustfile.py                 # composition only
├── locust.conf                   # default run parameters
├── config/settings.py            # target, MAX_RPS, SLA thresholds (env-var overridable)
├── users/
│   ├── employee_api_user.py      # task mix 60/25/10/5, tags read|write, constant_throughput pacing
│   └── load_shapes.py            # StepLoadShape 2 → 5 → 8 → 10 RPS
├── validators/response_validators.py   # assertions: status, JSON envelope, schema, echo, id match
└── listeners/
    ├── metrics_collector.py      # status codes per endpoint, latency per load level, per-second RPS
    ├── rps_guard.py              # blocks configs > 10 RPS, aborts if live RPS > 10 (+10%) for 3 s
    └── sla_listener.py           # SLA assertions, exit code, summary.json/md + interpretation
```

## How the 10 RPS ceiling is guaranteed

1. **Pacing** – `constant_throughput(USER_RPS=1)`: each user sends ≤ 1 req/s regardless of latency,
   so *RPS = users*. The shape never schedules more than `MAX_RPS` users.
2. **Pre-flight check** – `rps_guard` refuses to start if `users × USER_RPS > MAX_RPS`.
3. **Runtime watchdog** – stops the run if observed RPS stays above the limit for 3 seconds.
4. **Post-run assertion** – average and peak 3-second-average RPS are SLA checks in the verdict.

## Assertions

| Level | Check |
|---|---|
| Per request (`catch_response`) | HTTP 200; JSON body; `status == "success"`; `data` present; employee fields & types; `GET /employee/{id}` returns the requested id; `POST /create` echoes payload |
| Per run (`sla_listener`) | p95 ≤ 2000 ms · p99 ≤ 4000 ms · avg ≤ 1000 ms · error rate ≤ 5 % · avg & peak RPS ≤ 10 (+10 %) |

Failure reasons are normalised (`HTTP 429 rate limited`, `HTTP 5xx server error`,
`Connection error / timeout`, `status != success`) so the report groups them meaningfully.

## Performance interpretation

`summary.md` is generated after every run with totals, SLA table, per-endpoint status-code
distribution, a per-load-level table (to find the knee) and rule-based observations.
See [RESULTS.md](RESULTS.md) for the analysis of the reference run.

**What to expect from this target** (observed while building the PoC): the public dummy API
enforces an aggressive per-IP rate limit — even two sequential `curl` calls a second apart
returned `HTTP 429 Too Many Requests` (an HTML page, not JSON). A run at 2–10 RPS will
therefore fail the error-rate SLA. That is a *correct* result: the test shows the service
cannot sustain 10 RPS for a single client, and the listener separates throttling (429) from
genuine server failures (5xx) and from latency degradation so the cause is clear.
