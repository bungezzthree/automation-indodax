*** Settings ***
Documentation       Page Object: Indodax market page (/market/<PAIR>).
...                 Only page *interactions* and *getters* live here - no assertions on business
...                 expectations (those belong to keywords/market_steps.resource).
...                 Composed from components: order book, trade history, market list.
Resource            ../../../resources/web_common.resource
Resource            components/order_book.resource
Resource            components/trade_history.resource
Resource            components/market_list.resource
Variables           ../locators/market_page.py


*** Keywords ***
Open Market Page
    [Arguments]    ${pair_slug}
    New Page    ${WEB_BASE_URL}/market/${pair_slug}
    Fail If Blocked By Edge Protection
    Wait For Elements State    ${MARKET_HEADER}    visible
    Dismiss Preference Modal If Shown
    Dismiss Onboarding Tour If Shown

Dismiss Preference Modal If Shown
    [Documentation]    SAFETY NET only. Normally never fires: contexts start with isLiteMode preseeded
    ...                (see web_common.resource > Build Preseeded User State). If the site changes the
    ...                mechanism, accept the default classic layout once; the page reloads on save.
    ${display}=    Get Style    ${PREFERENCE_MODAL}    display
    IF    '${display}' != 'none'
        Log    Preference modal appeared despite preseeded state - dismissing    level=WARN
        Click    ${PREFERENCE_MODAL_SAVE}
        Wait For Elements State    ${PREFERENCE_MODAL}    hidden
        Wait For Elements State    ${MARKET_HEADER}    visible
    END

Fail If Blocked By Edge Protection
    [Documentation]    Distinguish "environment blocked the runner" (Cloudflare/WAF page) from a
    ...                real product defect, so triage does not chase a missing-element timeout.
    ${body}=    Get Text    body
    IF    'CLOUDFLARE_ERROR' in $body or 'Attention Required' in $body
        Fail    ENVIRONMENT BLOCK, not a product defect: Cloudflare served a block page to this runner. Whitelist the runner IP or use a staging URL.
    END

Dismiss Onboarding Tour If Shown
    [Documentation]    The spotlight tour is rendered with opacity 0 when inactive, so element
    ...                visibility is not enough - check opacity, then click through its steps.
    FOR    ${step}    IN RANGE    10
        ${count}=    Get Element Count    ${GUIDE_POPUP}
        IF    ${count} == 0    BREAK
        ${opacity}=    Get Style    ${GUIDE_POPUP}    opacity
        IF    float(${opacity}) == 0    BREAK
        Click    ${GUIDE_NEXT_BUTTON}
    END

Get Market Header
    ${text}=    Get Text    ${MARKET_HEADER}
    RETURN    ${text}

Get Last Price
    [Documentation]    Waits until the realtime widget has rendered a value, then parses it.
    ${text}=    Get Text    ${LAST_PRICE}    matches    ^[0-9][0-9.,]*$
    ${price}=    Parse Indonesian Number    ${text}
    RETURN    ${price}
