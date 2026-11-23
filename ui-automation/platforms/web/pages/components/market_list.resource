*** Settings ***
Documentation       Component object: market list panel (search + IDR market table).
Variables           ../../locators/market_page.py


*** Keywords ***
Search Market
    [Documentation]    The table filter listens to keyboard events, so type (not fill).
    [Arguments]    ${keyword}
    Wait For Elements State    ${MARKET_SEARCH_BOX}    visible
    Type Text    ${MARKET_SEARCH_BOX}    ${keyword}    delay=30 ms    clear=True

Get Visible Market Pairs
    [Documentation]    Returns `data-pair` ids of rows currently rendered in the IDR market table.
    ${rows}=    Get Elements    ${IDR_MARKET_ROWS}
    ${pairs}=    Create List
    FOR    ${row}    IN    @{rows}
        ${pair}=    Get Attribute    ${row}    data-pair
        Append To List    ${pairs}    ${pair}
    END
    RETURN    ${pairs}

Market Row Is Listed
    [Arguments]    ${pair_id}
    ${locator}=    Format Locator    ${MARKET_ROW_BY_PAIR}    pair=${pair_id}
    ${count}=    Get Element Count    ${locator}
    RETURN    ${{ ${count} > 0 }}

Open Market From List
    [Arguments]    ${pair_id}
    ${locator}=    Format Locator    ${MARKET_ROW_NAME_CELL}    pair=${pair_id}
    Click    ${locator}
