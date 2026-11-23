*** Settings ***
Documentation       GET /api/ticker/{pair_id} - data-driven from data/ticker_pairs.csv.
...                 Add a row to the CSV to cover a new market; no code change needed.
...                 Per-row tags (smoke/P1...) come from the CSV [Tags] column.
Library             DataDriver    file=../../data/ticker_pairs.csv    dialect=UserDefined    delimiter=;
Resource            ../../keywords/market_data.resource
Test Template       Ticker For Pair Should Be Valid
Test Tags           ticker    public    regression    positive    contract


*** Test Cases ***
Ticker ${pair_id}    btcidr    vol_btc


*** Keywords ***
Ticker For Pair Should Be Valid
    [Arguments]    ${pair_id}    ${volume_field}
    ${ticker}=    Get Ticker    ${pair_id}
    Ticker Should Be Valid    ${ticker}    ${volume_field}
