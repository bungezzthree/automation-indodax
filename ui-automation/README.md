# UI Automation — Web (Playwright) + Mobile (Appium: Android & iOS)

Robot Framework PoC for <https://indodax.com/market/USDTIDR> and the Indodax mobile app.

## Quick start

```powershell
cd ui-automation
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
rfbrowser init chromium                # downloads Playwright + Chromium (Node.js required)
python run.py                          # web smoke, prod, headless
python run.py --scope regression --headed
```

Mobile (needs Appium 2 server + device/emulator with the Indodax app installed):

```powershell
npm i -g appium; appium driver install uiautomator2; appium driver install xcuitest
$env:ANDROID_DEVICE_NAME="emulator-5554"
python run.py --platform android --scope smoke
```

## Layered structure (Page / Screen Object)

```
ui-automation/
├── run.py                              # --platform web|android|ios --env --scope --include ...
├── config/
│   ├── environments.yaml               # dev/staging/prod + browser & appium settings
│   ├── env_config.py                   # variable file: env + platform -> variables/locators
│   └── capabilities/{android,ios}.yaml # Appium caps, ${ENV_VARS} expanded at runtime
├── libraries/
│   ├── UiHelpers.py                    # id-ID number parsing, locator templating, tolerance asserts
│   └── listeners/ResultSummaryListener.py
├── resources/
│   ├── web_common.resource             # browser/context lifecycle, screenshot+trace on failure
│   └── mobile_common.resource          # appium session, screenshot+page-source on failure
├── platforms/
│   ├── web/
│   │   ├── locators/market_page.py     # ALL web selectors, one place
│   │   ├── pages/market_page.resource  # page object (actions + getters only)
│   │   ├── pages/components/           # order_book, trade_history, market_list
│   │   ├── keywords/market_steps.resource   # business steps + assertions
│   │   └── tests/01..04_*.robot
│   └── mobile/
│       ├── locators/android/market_screens.py   # same variable NAMES on both platforms
│       ├── locators/ios/market_screens.py       #   -> screens/tests are platform-neutral
│       ├── screens/{home,market}_screen.resource
│       ├── keywords/market_steps.resource
│       └── tests/01_market_detail.robot
└── data/
    ├── web/markets.csv, web/market_search.csv
    └── mobile/markets.csv
```

Dependency rule: `tests → keywords (steps) → pages/screens → locators + resources → libraries`.

## Locator strategy

| Priority | Web | Mobile |
|---|---|---|
| 1 | stable `id` (`#sell_orders`, `#searchbox_market`) | accessibility id |
| 2 | domain data attributes (`tr[data-pair="ethidr"]`, `tr[price]`) | resource-id / NSPredicate |
| 3 | semantic classes (`h1.custom-h1`, `.last_price_val`) | UiSelector text / class chain |
| 4 | text — only when the text *is* the requirement | XPath (never positional) |

Banned: positional XPath, Tailwind utility classes, generated ids (`tradingview_2b91b`).
Parametrised locators are format strings (`MARKET_ROW_BY_PAIR = '...[data-pair="{pair}"]'`)
resolved with `Format Locator`.

Order-book prices are read from the `price` attribute of each row instead of the
formatted cell text (`18.291`), removing locale parsing from the hot path.

## Web coverage (https://indodax.com/market/USDTIDR)

| Suite | Scenarios |
|---|---|
| 01 market overview | header, title, positive last price — USDTIDR/BTCIDR/ETHIDR (CSV) |
| 02 order book | both sides populated, sorted & not crossed, last price ≈ best ask (±1 %), trade history types ∈ {Beli, Jual} |
| 03 market search | 4 keywords (case, asset name) → expected pair listed and list narrowed (CSV) |
| 04 navigation | select ETH/IDR from list → navigates to its trade view |

## Mobile status

Screens, steps and tests are complete and platform-neutral; **locator values are a baseline that
must be confirmed with Appium Inspector** against the app build under test (no device was
available while building this PoC). Only the two `locators/*/market_screens.py` files need edits.
