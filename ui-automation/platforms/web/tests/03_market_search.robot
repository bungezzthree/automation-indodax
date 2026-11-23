*** Settings ***
Documentation       Market list search & navigation - data-driven from data/web/market_search.csv.
Library             DataDriver    file=../../../data/web/market_search.csv    dialect=UserDefined    delimiter=;
Resource            ../keywords/market_steps.resource
Test Setup          Open USDT Market In Clean Context
Test Template       Searching Should Find Market
Test Tags           search    regression    positive


*** Test Cases ***
Search '${keyword}' finds ${pair_id}    ETH    ethidr


*** Keywords ***
Open USDT Market In Clean Context
    Start Clean Context
    User Opens Market    USDTIDR

Searching Should Find Market
    [Arguments]    ${keyword}    ${pair_id}
    User Searches Market For    ${keyword}
    Market List Should Contain    ${pair_id}
    Search Should Narrow The Market List    ${keyword}
