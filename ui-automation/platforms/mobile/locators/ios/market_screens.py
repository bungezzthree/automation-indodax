"""iOS locators for the Indodax app - same variable names as android/market_screens.py.

Strategy (priority): accessibility id > predicate= (NSPredicate) > chain= (class chain) > XPath.
Values are a PoC baseline - confirm with Appium Inspector against the build under test.
"""

# --------------------------------------------------------------- onboarding
ONBOARDING_SKIP = "predicate=label MATCHES[c] '(lewati|skip|nanti)'"
PERMISSION_DENY = "predicate=type == 'XCUIElementTypeButton' AND label IN {\"Don’t Allow\", \"Jangan Izinkan\"}"
PROMO_CLOSE = "predicate=name MATCHES[c] '(close|tutup)'"

# --------------------------------------------------------------------- home
BOTTOM_NAV_MARKET = "predicate=type == 'XCUIElementTypeButton' AND label MATCHES[c] '(market|pasar)'"

# ------------------------------------------------------------------- market
MARKET_SEARCH_ICON = "predicate=name MATCHES[c] '.*(search|cari).*'"
MARKET_SEARCH_INPUT = "chain=**/XCUIElementTypeSearchField"
MARKET_LIST_ITEM_BY_NAME = "predicate=label CONTAINS '{name}'"

# ------------------------------------------------------------- pair detail
PAIR_DETAIL_TITLE = "predicate=label CONTAINS '{name}'"
PAIR_LAST_PRICE = "predicate=name MATCHES[c] '.*last_?price.*'"
PAIR_BUY_BUTTON = "predicate=type == 'XCUIElementTypeButton' AND label ==[c] 'beli'"
PAIR_SELL_BUTTON = "predicate=type == 'XCUIElementTypeButton' AND label ==[c] 'jual'"
