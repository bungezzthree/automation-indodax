*** Settings ***
Documentation       GET /api/depth/{pair_id}
Resource            ../../keywords/market_data.resource
Test Tags           orderbook    public


*** Test Cases ***
Order Book Is Sorted And Not Crossed
    [Tags]    smoke    regression    positive    contract    P1
    [Template]    Order Book Of Pair Should Be Consistent
    usdtidr
    btcidr

Order Book Best Prices Align With Ticker
    [Documentation]    Best bid from depth must be close to ticker buy price. Both are read
    ...                seconds apart on a live market, so a 1% tolerance is applied.
    [Tags]    regression    consistency    P2
    ${book}=      Get Order Book    usdtidr
    ${ticker}=    Get Ticker    usdtidr
    ${low}=     Evaluate    float($ticker["buy"]) * 0.99
    ${high}=    Evaluate    float($ticker["buy"]) * 1.01
    Value Should Be Between    ${book}[buy][0][0]    ${low}    ${high}    best bid


*** Keywords ***
Order Book Of Pair Should Be Consistent
    [Arguments]    ${pair_id}
    ${book}=    Get Order Book    ${pair_id}
    Order Book Should Be Consistent    ${book}
