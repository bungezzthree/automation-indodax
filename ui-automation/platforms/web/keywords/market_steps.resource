*** Settings ***
Documentation       Business-level steps for the web market page (Given/When/Then friendly).
...                 Tests call ONLY keywords from this file. Every assertion carries a message that
...                 includes the actual value, so a failure is understandable from report.html alone.
Resource            ../pages/market_page.resource


*** Keywords ***
# ------------------------------------------------------------------- actions
User Opens Market
    [Arguments]    ${pair_slug}
    Open Market Page    ${pair_slug}

User Searches Market For
    [Arguments]    ${keyword}
    Search Market    ${keyword}

User Selects Market From List
    [Arguments]    ${pair_id}
    Open Market From List    ${pair_id}

# ---------------------------------------------------------------- assertions
Market Header Should Be
    [Arguments]    ${expected}
    Get Text    ${MARKET_HEADER}    ==    ${expected}    Market header mismatch

Page Title Should Mention
    [Arguments]    ${expected}
    Get Title    contains    ${expected}    Page title does not mention '${expected}'

Last Price Should Be A Positive Number
    ${price}=    Get Last Price
    Number Should Be Positive    ${price}    last price

Order Book Should Show Both Sides
    [Arguments]    ${min_levels}=5
    Wait For Order Book
    ${asks}=    Get Order Book Row Count    sell
    ${bids}=    Get Order Book Row Count    buy
    Should Be True    ${asks} >= ${min_levels}    Only ${asks} sell levels shown (min ${min_levels})
    Should Be True    ${bids} >= ${min_levels}    Only ${bids} buy levels shown (min ${min_levels})

Order Book Should Not Be Crossed
    [Documentation]    Best bid and best ask come from the SAME snapshot; reading them at two
    ...                different instants on a live book could flag a false cross.
    ${book}=    Get Order Book Snapshot
    Should Not Be Empty    ${book}[sell]    Sell side empty
    Should Not Be Empty    ${book}[buy]    Buy side empty
    ${ask}=    Set Variable    ${book}[sell][0]
    ${bid}=    Set Variable    ${book}[buy][0]
    Should Be True    ${bid} < ${ask}    Crossed book on UI: best bid ${bid} >= best ask ${ask}

Order Book Sides Should Be Sorted
    ${book}=    Get Order Book Snapshot
    ${asks}=    Set Variable    ${book}[sell]
    ${bids}=    Set Variable    ${book}[buy]
    ${sorted_asks}=    Evaluate    sorted($asks)
    ${sorted_bids}=    Evaluate    sorted($bids, reverse=True)
    Lists Should Be Equal    ${asks}    ${sorted_asks}    Sell side is not ascending
    Lists Should Be Equal    ${bids}    ${sorted_bids}    Buy side is not descending

Last Price Should Sit Inside The Spread Tolerance
    [Documentation]    Last traded price should be near best bid/ask (live data -> 1% tolerance).
    ${last}=    Get Last Price
    ${ask}=    Get Best Ask Price
    Numbers Should Be Within Tolerance    ${last}    ${ask}    1    last price vs best ask

Trade History Should Show Recent Trades
    [Arguments]    ${allowed_types}
    Wait For Trade History
    ${count}=    Get Trade History Row Count
    Should Be True    ${count} > 0    Trade history is empty
    ${types}=    Get Trade Types
    FOR    ${type}    IN    @{types}
        Should Contain    ${allowed_types}    ${type}    Unexpected trade type '${type}'
    END

Market List Should Contain
    [Arguments]    ${pair_id}
    Wait For Condition    Element Count    ${IDR_MARKET_ROWS}    >    0
    ${listed}=    Market Row Is Listed    ${pair_id}
    ${visible}=    Get Visible Market Pairs
    Should Be True    ${listed}    '${pair_id}' not in filtered market list: ${visible}

Search Should Narrow The Market List
    [Documentation]    The filter must actually reduce the list (guards against a no-op search
    ...                that would make `Market List Should Contain` pass trivially).
    [Arguments]    ${keyword}    ${max_results}=50
    ${visible}=    Get Visible Market Pairs
    ${count}=    Get Length    ${visible}
    Should Be True    0 < ${count} <= ${max_results}
    ...    Search '${keyword}' returned ${count} markets (expected 1..${max_results}): ${visible}

Browser Should Navigate To Market
    [Arguments]    ${pair_slug}
    Wait For Condition    Url    contains    ${pair_slug}
