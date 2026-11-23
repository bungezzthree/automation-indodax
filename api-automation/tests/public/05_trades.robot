*** Settings ***
Documentation       GET /api/trades/{pair_id}
Resource            ../../keywords/market_data.resource
Test Tags           trades    public


*** Test Cases ***
Recent Trades Are Valid
    [Tags]    smoke    regression    positive    contract    P1
    [Template]    Recent Trades Of Pair Should Be Valid
    usdtidr
    btcidr

Recent Trades Are Ordered Newest First
    [Tags]    regression    positive    P2
    ${trades}=    Get Recent Trades    usdtidr
    ${dates}=     Evaluate    [int(t["date"]) for t in $trades]
    ${sorted}=    Evaluate    sorted($dates, reverse=True)
    Lists Should Be Equal    ${dates}    ${sorted}    msg=Trades are not ordered newest first


*** Keywords ***
Recent Trades Of Pair Should Be Valid
    [Arguments]    ${pair_id}
    ${trades}=    Get Recent Trades    ${pair_id}
    Trades Should Be Valid    ${trades}
