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

Get Order Book Prices
    [Arguments]    ${side}
    ${locator}=    Set Variable If    '${side}' == 'sell'    ${SELL_ORDER_ROWS}    ${BUY_ORDER_ROWS}
    ${rows}=    Get Elements    ${locator}
    ${prices}=    Create List
    FOR    ${row}    IN    @{rows}
        ${price}=    Get Attribute    ${row}    price
        Append To List    ${prices}    ${{ float($price) }}
    END
    RETURN    ${prices}
