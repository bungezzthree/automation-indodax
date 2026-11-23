*** Settings ***
Documentation       Navigating from the market list to another market's trade view.
Resource            ../keywords/market_steps.resource
Test Tags           search    navigation    positive


*** Test Cases ***
Selecting A Market From The List Opens Its Trade View
    [Tags]    smoke    regression    P1
    User Opens Market    USDTIDR
    User Searches Market For    ETH
    Market List Should Contain    ethidr
    User Selects Market From List    ethidr
    Browser Should Navigate To Market    ETHIDR
