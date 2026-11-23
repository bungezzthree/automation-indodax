*** Settings ***
Documentation       Market discovery on the mobile app - data-driven from data/mobile/markets.csv.
...                 Platform tag (android / ios) is added at runtime by run.py (--settag).
Library             DataDriver    file=../../../data/mobile/markets.csv    dialect=UserDefined    delimiter=;
Resource            ../keywords/market_steps.resource
Test Setup          Restart To Home
Test Template       Pair Detail Should Be Reachable
Test Tags           market    regression    positive


*** Test Cases ***
Mobile market ${pair_name}    USDT/IDR    USDT


*** Keywords ***
Restart To Home
    [Documentation]    Deterministic starting point for every test: cold-restart the app.
    ...                noReset=true keeps app data, so no re-onboarding / re-login per test.
    Run Keyword And Ignore Error    Terminate Application    ${APP_ID}
    Activate Application    ${APP_ID}
    User Launches The App

Pair Detail Should Be Reachable
    [Arguments]    ${pair_name}    ${search_keyword}
    User Opens Market List
    User Searches And Opens Pair    ${search_keyword}    ${pair_name}
    Pair Detail Should Show Live Price    ${pair_name}
    Trade Actions Should Be Available
