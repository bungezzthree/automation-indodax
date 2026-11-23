# API Automation — Indodax Public & Private API

Robot Framework + `requests` PoC against [Indodax Official API](https://github.com/btcid/indodax-official-api-docs).

## Quick start

```powershell
cd api-automation
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py                        # prod, smoke
python run.py --scope regression     # full regression
```

Reports land in `results/<env>/<timestamp>/` (`report.html`, `log.html`, `output.xml`,
`xunit.xml`, `summary.json`) and are mirrored to `results/latest/`.

## Layered structure

```
api-automation/
├── run.py                       # execution entry point (env, scope, tags, rerun)
├── config/
│   ├── environments.yaml        # dev / staging / prod matrix (no secrets)
│   └── env_config.py            # Robot variable file: yaml + env-var overrides + secrets
├── libraries/                   # Python layer - technical concerns only
│   ├── ApiClient.py             # HTTP, retry/backoff, HMAC signing, masked logging
│   ├── SchemaValidator.py       # JSON-Schema contract assertions (all violations at once)
│   ├── MarketAssertions.py      # domain assertions (Decimal-safe)
│   └── listeners/ResultSummaryListener.py   # summary.json for CI / chat-ops
├── resources/
│   ├── common.resource          # library imports, suite lifecycle hooks
│   └── schemas/*.json           # API contracts
├── keywords/                    # business keywords (what), reused by every test
│   ├── market_data.resource
│   ├── pairs.resource
│   └── private_api.resource
├── data/                        # test data, separated from logic
│   ├── ticker_pairs.csv         # DataDriver: 1 row = 1 test case
│   ├── invalid_pairs.csv        # DataDriver: negative matrix
│   └── pair_catalog.yaml        # reference data for /api/pairs
└── tests/                       # test layer - reads like a specification
    ├── __init__.robot           # root suite setup (session) + `api` tag
    ├── public/01..07_*.robot
    └── private/01_tapi_authentication.robot
```

Dependency rule: `tests → keywords → resources/common → libraries`. Tests never call
`GET Request` or import a library directly.

## Coverage

| Endpoint | Scenarios | Assertion style |
|---|---|---|
| `/api/server_time` | epoch freshness, UTC | schema + drift ≤ 120 s |
| `/api/pairs` | contract, reference data, tradability, fee rule, cross-endpoint | schema + YAML reference |
| `/api/ticker/{pair}` | 5 markets (CSV) | schema + `low ≤ last ≤ high`, `bid ≤ ask`, positive numbers, SLA |
| `/api/depth/{pair}` | sorting, not crossed, aligned with ticker (±1 %) | schema + domain |
| `/api/trades/{pair}` | validity, newest-first ordering | schema + domain |
| `/api/summaries` | key markets present | schema |
| invalid pairs | 4 negatives (CSV) | error envelope `invalid_pair` (API returns HTTP 200!) |
| `POST /tapi` | missing Sign, invalid key, authenticated getInfo (skipped w/o creds) | `tapi_error.json` + `error_code` |

## Assertion strategy

1. **Transport** – status code checked inside `ApiClient` (`expected_status`), retried on 429/5xx.
2. **Contract** – JSON Schema per endpoint; reports *every* violation with its JSON path.
3. **Business rules** – Decimal-based domain assertions (`Best Bid Should Not Exceed Best Ask` …).
4. **Non-functional** – response time SLA per environment (`response_time_sla_ms`).

Every assertion has a custom message that includes the offending value.

## Private API credentials

Never commit keys. Export them only for runs that need authenticated scenarios:

```powershell
$env:INDODAX_API_KEY="..."; $env:INDODAX_API_SECRET="..."
```

`Key`/`Sign` headers are masked (`***`) in `log.html`.
