*** Settings ***
Documentation       Order book & trade history widgets on https://indodax.com/market/USDTIDR
Resource            ../keywords/market_steps.resource
Test Setup          Open USDT Market In Clean Context
Test Tags           orderbook-ui    positive


*** Variables ***
@{TRADE_TYPES}      Beli    Jual


*** Test Cases ***
Order Book Shows Buy And Sell Levels
    [Tags]    smoke    regression    P1
    Order Book Should Show Both Sides    min_levels=5

Order Book Is Sorted And Not Crossed
    [Tags]    regression    P1
    Order Book Should Not Be Crossed
    Order Book Sides Should Be Sorted

Last Price Is Consistent With Order Book
    [Tags]    regression    consistency    P2
    Order Book Should Show Both Sides
    Last Price Should Sit Inside The Spread Tolerance

Trade History Shows Recent Buy And Sell Trades
    [Tags]    trade-history    smoke    regression    P1
    Trade History Should Show Recent Trades    ${TRADE_TYPES}


*** Keywords ***
Open USDT Market In Clean Context
    Start Clean Context
    User Opens Market    USDTIDR
