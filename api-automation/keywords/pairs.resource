*** Settings ***
Documentation       Business keywords for the pair catalogue (/api/pairs).
Resource            market_data.resource


*** Keywords ***
Pair Catalogue Should Satisfy Contract
    [Arguments]    ${pairs}
    Json Should Match Schema    ${pairs}    pairs.json
    Pairs Should Have Unique Ids    ${pairs}

Pair Should Have Attributes
    [Documentation]    Compares a pair against reference data from data/pair_catalog.yaml.
    [Arguments]    ${pairs}    ${pair_id}    ${expected}
    ${pair}=    Find Pair By Id    ${pairs}    ${pair_id}
    FOR    ${key}    ${value}    IN    &{expected}
        Should Be Equal As Strings    ${pair}[${key}]    ${value}
        ...    msg=Pair '${pair_id}' field '${key}': expected '${value}', got '${pair}[${key}]'
    END

Pair Should Be Tradable
    [Arguments]    ${pairs}    ${pair_id}
    ${pair}=    Find Pair By Id    ${pairs}    ${pair_id}
    Should Be Equal As Integers    ${pair}[is_maintenance]    0    msg=${pair_id} is under maintenance
    Should Be Equal As Integers    ${pair}[is_market_suspended]    0    msg=${pair_id} is suspended

Fees Should Be Consistent
    [Documentation]    Maker fee must never exceed taker fee.
    [Arguments]    ${pairs}
    FOR    ${pair}    IN    @{pairs}
        IF    'trade_fee_percent_maker' in $pair and 'trade_fee_percent_taker' in $pair
            Should Be True    ${pair}[trade_fee_percent_maker] <= ${pair}[trade_fee_percent_taker]
            ...    msg=${pair}[id]: maker fee > taker fee
        END
    END

Every Pair Should Have A Live Ticker
    [Documentation]    Cross-endpoint consistency: catalogue entries are resolvable by /api/ticker.
    [Arguments]    ${pairs}    @{pair_ids}
    FOR    ${pair_id}    IN    @{pair_ids}
        ${pair}=    Find Pair By Id    ${pairs}    ${pair_id}
        ${ticker}=    Get Ticker    ${pair}[id]
        Should Be Positive Number    ${ticker}[last]    ${pair_id}.last
    END
