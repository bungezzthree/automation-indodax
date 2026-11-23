*** Settings ***
Documentation       Component object: "last trades" table on the market page.
Variables           ../../locators/market_page.py


*** Keywords ***
Wait For Trade History
    Wait For Elements State    ${LAST_TRADES_TABLE}    visible
    Wait For Elements State    ${LAST_TRADE_ROWS} >> nth=0    attached

Get Trade History Row Count
    ${count}=    Get Element Count    ${LAST_TRADE_ROWS}
    RETURN    ${count}

Get Trade Types
    [Documentation]    Returns the localized trade side labels, e.g. ['Jual', 'Beli', ...].
    ${cells}=    Get Elements    ${LAST_TRADE_TYPE_CELLS}
    ${types}=    Create List
    FOR    ${cell}    IN    @{cells}
        ${text}=    Get Text    ${cell}
        Append To List    ${types}    ${text.strip()}
    END
    RETURN    ${types}
