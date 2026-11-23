*** Settings ***
Documentation       Market page renders correctly for each market - data-driven from
...                 data/web/markets.csv (1 row = 1 test; per-row tags in the CSV).
Library             DataDriver    file=../../../data/web/markets.csv    dialect=UserDefined    delimiter=;
Resource            ../keywords/market_steps.resource
Test Template       Market Overview Should Render
Test Tags           market    regression    positive


*** Test Cases ***
Market overview ${pair_slug}    USDTIDR    USDT to IDR    USDT to IDR


*** Keywords ***
Market Overview Should Render
    [Arguments]    ${pair_slug}    ${expected_header}    ${expected_title}
    User Opens Market    ${pair_slug}
    Market Header Should Be    ${expected_header}
    Page Title Should Mention    ${expected_title}
    Last Price Should Be A Positive Number
