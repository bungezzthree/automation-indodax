*** Settings ***
Documentation       GET /api/pairs - pair catalogue.
...                 The catalogue is fetched once per suite (it is ~1 MB) and shared across tests.
Resource            ../../keywords/pairs.resource
Variables           ../../data/pair_catalog.yaml
Suite Setup         Load Pair Catalogue
Test Tags           pairs    public


*** Variables ***
# Placeholder so static analysis (IDE) knows the name; the real catalogue is loaded in Suite Setup.
${PAIRS}            ${None}


*** Test Cases ***
Pair Catalogue Matches Contract
    [Tags]    smoke    regression    contract    P1
    Pair Catalogue Should Satisfy Contract    ${PAIRS}

Key Markets Have Expected Static Attributes
    [Documentation]    Data-driven from data/pair_catalog.yaml.
    [Tags]    regression    positive    P1
    [Template]    Pair Should Have Attributes
    ${PAIRS}    btcidr     ${btcidr}
    ${PAIRS}    usdtidr    ${usdtidr}
    ${PAIRS}    ethidr     ${ethidr}

Key Markets Are Tradable
    [Tags]    smoke    regression    positive    P1
    [Template]    Pair Should Be Tradable
    ${PAIRS}    btcidr
    ${PAIRS}    usdtidr

Maker Fee Never Exceeds Taker Fee
    [Tags]    regression    consistency    P2
    Fees Should Be Consistent    ${PAIRS}

Catalogue Pairs Resolve To Live Tickers
    [Documentation]    Cross-endpoint consistency between /api/pairs and /api/ticker.
    [Tags]    regression    consistency    P2
    Every Pair Should Have A Live Ticker    ${PAIRS}    btcidr    usdtidr    ethidr


*** Keywords ***
Load Pair Catalogue
    ${pairs}=    Get All Pairs
    VAR    ${PAIRS}    ${pairs}    scope=SUITE
