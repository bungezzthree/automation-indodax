"""Android locators for the Indodax app (package id.co.bitcoin).

SCREEN ABSTRACTION CONTRACT: android/ and ios/ locator files expose the SAME variable
names. Screen objects (platforms/mobile/screens/*.resource) only reference these names,
so one set of screens/tests runs on both platforms; only this file differs.

Strategy (priority): accessibility id > resource-id > UiSelector text > XPath (last resort,
never positional).

NOTE: values below are a PoC baseline and MUST be confirmed with Appium Inspector against
the app build under test (resource-ids change between releases). Ask the mobile team to
add stable content-descriptions (accessibility ids) for the elements marked `# a11y-request`.
"""

# --------------------------------------------------------------- onboarding
ONBOARDING_SKIP = 'android=new UiSelector().textMatches("(?i)(lewati|skip|nanti)")'
PERMISSION_DENY = "id=com.android.permissioncontroller:id/permission_deny_button"
PROMO_CLOSE = 'android=new UiSelector().descriptionMatches("(?i)(close|tutup)")'

# --------------------------------------------------------------------- home
BOTTOM_NAV_MARKET = 'android=new UiSelector().textMatches("(?i)^(market|pasar)$")'

# ------------------------------------------------------------------- market
MARKET_SEARCH_ICON = 'android=new UiSelector().descriptionMatches("(?i)(search|cari)")'   # a11y-request
MARKET_SEARCH_INPUT = "class=android.widget.EditText"
MARKET_LIST_ITEM_BY_NAME = 'android=new UiSelector().textContains("{name}")'

# ------------------------------------------------------------- pair detail
PAIR_DETAIL_TITLE = 'android=new UiSelector().textContains("{name}")'
PAIR_LAST_PRICE = 'android=new UiSelector().resourceIdMatches(".*(last_?price|tv_price).*")'  # a11y-request
PAIR_BUY_BUTTON = 'android=new UiSelector().textMatches("(?i)^beli$")'
PAIR_SELL_BUTTON = 'android=new UiSelector().textMatches("(?i)^jual$")'
