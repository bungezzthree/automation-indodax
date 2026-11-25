# Indodax QA Automation — Proof of Concept

Three independent projects, one shared architecture:

| Project | Target | Stack |
|---|---|---|
| [`api-automation/`](api-automation/README.md) | Indodax public + private API | Robot Framework · requests · JSON Schema · DataDriver |
| [`ui-automation/`](ui-automation/README.md) | Web `indodax.com/market/USDTIDR` · Indodax Android & iOS app | Robot Framework · Browser (Playwright) · AppiumLibrary |
| [`load-testing/`](load-testing/README.md) | `dummy.restapiexample.com` (≤ 10 RPS) | Locust |

Each project has its own `requirements.txt`, runner and README so it can live in its own
repository/pipeline; they share the same conventions so engineers can move between them.

> **Full design document with diagrams** (high-level architecture, sequence, CI/CD with
> VM execution for Web/API and a local device farm for mobile): [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
> The sections below are a summary.

---

## 1. Architecture

Every project follows the same dependency direction — outer layers know inner layers, never the reverse:

```
 tests/                 WHAT is verified        (readable spec, tags, data binding only)
   │
 keywords/  (steps)     business language       ("User Opens Market", "Ticker Should Be Valid")
   │
 pages/ screens/        HOW the UI is driven    (page/screen objects, components)       [UI]
 resources/common       infrastructure hooks    (sessions, setup/teardown, evidence)
   │
 locators/ schemas/     volatile details        (selectors, JSON contracts)
 libraries/ (Python)    technical capabilities  (HTTP client, assertions, parsing, listeners)
   │
 config/  data/         environment & test data (no logic)
```

Clean-code rules applied:

* **Single responsibility** – `ApiClient` only does HTTP (retry, signing, logging); assertions live
  elsewhere. Page objects expose actions/getters only; expectations live in step keywords.
* **No magic values in tests** – URLs, timeouts, SLAs in `config/`; selectors in `locators/`; inputs in `data/`.
* **Intention-revealing names** – `Get …` returns data, `… Should …` asserts, `User …` acts.
* **Fail with context** – every assertion message contains the actual value (`Crossed book: best bid 18292 > best ask 18291`).
* **Decimal arithmetic** for prices — crypto amounts have 8 decimals; floats would produce false failures.

## 2. Platform segregation (Web · API · Android · iOS)

```
api-automation/                         -> API
ui-automation/platforms/web/            -> Web      (Browser library / Playwright)
ui-automation/platforms/mobile/         -> Android + iOS (AppiumLibrary)
    locators/android/market_screens.py  ┐ same variable names,
    locators/ios/market_screens.py      ┘ different values
```

* Web and mobile **never share** page/screen objects — the UX differs — but they share
  `libraries/UiHelpers.py`, the reporting listener and the run conventions.
* Android and iOS **do share** screens, steps and tests. The platform is a runtime
  parameter (`run.py --platform ios`); `config/env_config.py` injects the matching
  capabilities and locator file. Adding a platform-specific flow = new screen keyword,
  no `IF platform == ...` branches inside tests.
* Every result is tagged with its platform (`api`, `web`, `android`, `ios` via `--settag`),
  so outputs from all four can be merged into one report: `rebot --merge */output.xml`.

## 3. Tagging strategy (multi-tag per test case)

| Dimension | Tags | Purpose |
|---|---|---|
| Platform | `api` `web` `android` `ios` (+`ui`, `mobile`) | pipeline/device routing |
| Level | `smoke` `regression` | execution scope |
| Feature | `pairs` `ticker` `orderbook` `trades` `summaries` `auth` `market` `search` `orderbook-ui` `trade-history` `navigation` | selective run by area / code owner |
| Type | `positive` `negative` `contract` `consistency` | coverage reporting |
| Priority | `P1` `P2` `P3` | triage order, `--exclude P3` for quick runs |
| Guards | `no-prod` `requires-credentials` | safety; auto-excluded / auto-skipped |

A test carries one tag per dimension, e.g. `api ticker smoke regression positive contract P1`.
Tags come from three places, merged by Robot: `Test Tags` in the suite (feature, type),
`[Tags]` per test or the CSV `[Tags]` column for data-driven rows (level, priority), and
`--settag` from the runner (platform).

Selective examples:

```powershell
python run.py --scope all --include ticker --include orderbook   # union of features
python run.py --scope regression --exclude P3                    # skip low priority
robot --include "smokeANDP1" ...                                 # boolean tag expressions
```

## 4. Environment strategy (dev / staging / prod)

* `config/environments.yaml` per project holds the non-secret matrix (base URLs, timeouts,
  retries, SLAs, `read_only`). `config/env_config.py` is a Robot *variable file* that resolves:
  **env var  >  yaml[env]  >  yaml[common]**, preserving types.
* **Secrets never live in files** — `INDODAX_API_KEY` / `INDODAX_API_SECRET` / device ids come
  from the process environment (CI secret store). The HTTP log masks `Key`/`Sign` headers.
* **Prod is read-only by construction**: the runner always appends `--exclude no-prod` when
  `--env prod`; this cannot be switched off from the CLI. Private-API positive tests are
  additionally gated by `requires-credentials` (`Skip If` with an explicit reason).
* Per-env tuning: dev → no retries, fast timeouts (surface flakiness); prod → 2 retries on
  429/5xx with exponential backoff (third-party network noise).
* Indodax exposes no public dev/staging hosts; those entries are placeholders
  (`localhost` mock / `staging.indodax.example`) to show the mechanism — override with
  `API_BASE_URL=...` / `WEB_BASE_URL=...`.

## 5. Test execution strategy

| Trigger | Scope | Command | Budget |
|---|---|---|---|
| Pull request | API smoke + Web smoke | `run.py --scope smoke` | < 3 min |
| Merge to main (staging) | API + Web regression | `run.py --env staging --scope regression` | < 15 min |
| Nightly | full regression all platforms, `--rerun-failed` | + `--platform android/ios` on device farm | < 60 min |
| Pre-release | regression + load test | `locust` (step profile) | — |
| Ad hoc / bug fix | selective by feature tag or test name | `--include orderbook` / `--test "*Crossed*"` | — |

* **Data-driven**: `DataDriver` turns each CSV row into its own test (own name, own tags,
  own pass/fail) — adding a market is a one-line CSV change. Small inline matrices use `[Template]`.
* **Isolation**: API session per run; one browser per suite but a **fresh context per test**
  (no shared cookies/storage); mobile app cold-restarted per test with `noReset` data.
* **Flakiness control**: Playwright auto-wait (no sleeps), retries only at transport level
  (429/5xx) — never on assertions — and an explicit `--rerun-failed` pass whose result is
  *merged* (rebot) so reruns are visible, not hidden.
* **Parallelism**: `run.py --processes N` (pabot) for UI suites.
* `.github/workflows/automation.yml` shows the pipeline wiring.

## 6. Error handling & reporting strategy

**Error handling**

| Layer | Mechanism |
|---|---|
| Transport (API) | `ApiClient` retries `ConnectionError`/`Timeout`/429/502/503/504 with exponential backoff, then raises `ApiClientError` with method, URL, status and body excerpt |
| Parsing | `Get Json Body` fails with the raw text when a body is not JSON (e.g. an HTML 429 page) |
| Contract | `Json Should Match Schema` reports **all** violations with JSON paths, not just the first |
| Web | auto full-page screenshot on any failing Browser keyword (`run_on_failure`), failing URL logged, optional Playwright trace (`--trace`) |
| Mobile | auto screenshot + page-source XML dump on failure; `Fatal Error` with root cause if Appium/device is unreachable (stops the run instead of 50 identical failures) |
| Optional UI | promos/permission dialogs/onboarding handled by `Tap If Present` / `Dismiss Onboarding Tour If Shown` — tolerated, never fail a test |
| Load | stable failure reasons (`HTTP 429 rate limited`) so Locust aggregates them; RPS guard aborts if > 10 RPS |

**Reporting**

* Robot `report.html` / `log.html` (request/response bodies in collapsible blocks, truncated
  at 2 KB, secrets masked), `output.xml` for merging, `xunit.xml` for CI test tabs.
* `summary.json` from `ResultSummaryListener`: totals, pass-rate, P1 failures, per-feature
  breakdown, slowest tests, every failure with message & tags — consumed by chat-ops/dashboards.
* Results stored under `results/<platform>/<env>/<timestamp>/` (+ `results/latest/`), metadata
  (env, scope, platform) stamped into the report header.
* Locust: HTML report, CSV time series, and `summary.md`/`summary.json` with SLA verdict,
  per-endpoint status-code distribution, per-load-level percentiles and an automated
  interpretation; non-zero exit code on SLA breach.

---

## Repository layout

```
.
├── README.md                      <- this document (summary)
├── docs/ARCHITECTURE.md           <- full architecture design + diagrams
├── .github/workflows/automation.yml
├── api-automation/
├── ui-automation/
└── load-testing/
```

## Prerequisites

Python 3.11+, Node.js 18+ (Playwright via `rfbrowser init`), Appium 2 + device/emulator for mobile.

## Verified status (2026-11-23, Windows, Python 3.15.2)

| Project | Result |
|---|---|
| API | 23 tests: 22 pass, 1 skipped (authenticated `getInfo`, needs `INDODAX_API_KEY/SECRET`) |
| Locust | runs; verdict FAIL by design (99.7 % HTTP 429 from the target) - see `load-testing/RESULTS.md` |
| Web | first run: 6/12 passed (order book, search); later runs blocked by a Cloudflare page for this machine's IP. The runner now reports that as an *environment block*. Re-run from an allow-listed IP/staging to confirm all 12 |
| Android/iOS | dry-run only (no device); locators unconfirmed |

Troubleshooting: if Robot crashes with `unknown encoding: utf-8:surrogateescape`, set `PYTHONIOENCODING=utf-8`.
Requirements are unpinned (`>=`) because pinned versions lacked wheels for Python 3.15.
