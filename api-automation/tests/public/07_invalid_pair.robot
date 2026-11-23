*** Settings ***
Documentation       Negative scenarios for public endpoints - data-driven from data/invalid_pairs.csv.
Library             DataDriver    file=../../data/invalid_pairs.csv    dialect=UserDefined    delimiter=;
Resource            ../../keywords/market_data.resource
Test Template       Unknown Pair Should Be Rejected
Test Tags           public    regression    negative


*** Test Cases ***
${endpoint} rejects ${pair_id}    ticker    zzzidr


*** Keywords ***
Unknown Pair Should Be Rejected
    [Arguments]    ${endpoint}    ${pair_id}
    ${resp}=    Request Public Endpoint With Pair    ${endpoint}    ${pair_id}
    Response Should Be Invalid Pair Error    ${resp}
