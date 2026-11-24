"""Locators for https://indodax.com/market/<PAIR> (Robot variable file).

Locator strategy (priority order - pick the first that is available):
  1. Stable ids              ->  #sell_orders, #searchbox_market
  2. Domain data attributes  ->  tr[data-pair="ethidr"]
  3. Semantic class names    ->  .last_price_val, h1.custom-h1
  4. Text / role             ->  only for copy that is part of the requirement
Never: positional XPath (div[3]/span[2]), Tailwind utility classes (text-[#232832]),
generated ids (tradingview_2b91b).

Parametrised locators are Python format strings, resolved by
`Format Locator` in resources/web_common.resource.
"""

# ---------------------------------------------------------------- page header
MARKET_HEADER = "css=h1.custom-h1"
LAST_PRICE = "css=h4.last_price_val"
VOLUME = "css=.vol_val"
PRICE_ALARM_BUTTON = "css=#btn_price_alarm"

# ----------------------------------------------- "Personalisasi Tampilan" modal
PREFERENCE_MODAL = "css=#modal-user-preference"
PREFERENCE_MODAL_SAVE = "css=#modal-user-preference >> text=Simpan Tampilan"

# ------------------------------------------------------------ onboarding tour
GUIDE_POPUP = "css=#guide-popup"
GUIDE_NEXT_BUTTON = "css=#p-btn-next"

# ---------------------------------------------------------------- order book
SELL_ORDERS_TABLE = "css=#sell_orders"
BUY_ORDERS_TABLE = "css=#buy_orders"
SELL_ORDER_ROWS = "css=#sell_orders tbody tr[price]"
BUY_ORDER_ROWS = "css=#buy_orders tbody tr[price]"
BEST_ASK_ROW = "css=#sell_orders tbody tr[price] >> nth=0"
BEST_BID_ROW = "css=#buy_orders tbody tr[price] >> nth=0"

# ------------------------------------------------------------- trade history
LAST_TRADES_TABLE = "css=#last_trades"
LAST_TRADE_ROWS = "css=#last_trades tbody tr[price]"
LAST_TRADE_TYPE_CELLS = "css=#last_trades tbody tr[price] td:nth-child(2)"

# --------------------------------------------------------- market list panel
MARKET_SEARCH_BOX = "css=#searchbox_market"
IDR_MARKET_TABLE = "css=#marketbox-table-idr"
IDR_MARKET_ROWS = "css=#marketbox-table-idr tbody tr.market-row"
MARKET_ROW_BY_PAIR = 'css=#marketbox-table-idr tbody tr.market-row[data-pair="{pair}"]'
MARKET_ROW_NAME_CELL = 'css=#marketbox-table-idr tbody tr.market-row[data-pair="{pair}"] td:nth-child(2)'
MARKET_ROW_PRICE = "css=#marketbox-table-idr span.price_{pair}_val"
