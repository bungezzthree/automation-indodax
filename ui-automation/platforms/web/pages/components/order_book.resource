*** Settings ***
Documentation       Component object: order book (sell / buy tables) on the market page.
Variables           ../../locators/market_page.py


*** Keywords ***
Wait For Order Book
    Wait For Elements State    ${SELL_ORDERS_TABLE}    visible
    Wait For Elements State    ${BUY_ORDERS_TABLE}    visible
    Wait For Elements State    ${BEST_ASK_ROW}    attached
    Wait For Elements State    ${BEST_BID_ROW}    attached

Get Order Book Row Count
    [Arguments]    ${side}
    ${locator}=    Set Variable If    '${side}' == 'sell'    ${SELL_ORDER_ROWS}    ${BUY_ORDER_ROWS}
    ${count}=    Get Element Count    ${locator}
    RETURN    ${count}

Get Best Ask Price
    [Documentation]    Each row carries the raw price in its `price` attribute - no text parsing needed.
    ${price}=    Get Attribute    ${BEST_ASK_ROW}    price
    RETURN    ${price}

Get Best Bid Price
    ${price}=    Get Attribute    ${BEST_BID_ROW}    price
    RETURN    ${price}

Get Order Book Snapshot
    [Documentation]    Atomic read of both sides in ONE browser round trip.
    ...                The order book is a live feed that re-renders rows every few hundred ms.
    ...                Looping `Get Elements` + `Get Attribute` per row (51 round trips) races with
    ...                those updates - a row handle can vanish mid-loop and Playwright waits for it
    ...                until timeout. A single in-page read always sees one consistent DOM state.
    ...                Returns a dict: {sell: [prices ascending as displayed], buy: [...]}.
    ${snapshot}=    Evaluate JavaScript    ${None}
    ...    () => {
    ...        const read = (id) => Array.from(document.querySelectorAll('#' + id + ' tbody tr[price]'))
    ...            .map(r => parseFloat(r.getAttribute('price')));
    ...        return {sell: read('sell_orders'), buy: read('buy_orders')};
    ...    }
    RETURN    ${snapshot}

Get Order Book Prices
    [Arguments]    ${side}
    ${snapshot}=    Get Order Book Snapshot
    RETURN    ${snapshot}[${side}]
