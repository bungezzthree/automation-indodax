*** Settings ***
Documentation       Screen objects: market list & pair detail. Platform-neutral.
Resource            ../../../resources/mobile_common.resource


*** Keywords ***
# ---------------------------------------------------------------- market list
Search Pair
    [Arguments]    ${keyword}
    Tap If Present    ${MARKET_SEARCH_ICON}
    Wait Until Element Is Visible    ${MARKET_SEARCH_INPUT}
    Clear Text    ${MARKET_SEARCH_INPUT}
    Input Text    ${MARKET_SEARCH_INPUT}    ${keyword}
    Run Keyword And Ignore Error    Hide Keyboard

Open Pair From List
    [Arguments]    ${pair_name}
    ${item}=    Format Locator    ${MARKET_LIST_ITEM_BY_NAME}    name=${pair_name}
    Wait Until Element Is Visible    ${item}
    Click Element    ${item}

Pair Is Listed
    [Arguments]    ${pair_name}
    ${item}=    Format Locator    ${MARKET_LIST_ITEM_BY_NAME}    name=${pair_name}
    ${listed}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${item}
    RETURN    ${listed}

# ---------------------------------------------------------------- pair detail
Wait For Pair Detail
    [Arguments]    ${pair_name}
    ${title}=    Format Locator    ${PAIR_DETAIL_TITLE}    name=${pair_name}
    Wait Until Element Is Visible    ${title}

Get Pair Last Price
    Wait Until Element Is Visible    ${PAIR_LAST_PRICE}
    ${text}=    Get Text    ${PAIR_LAST_PRICE}
    ${price}=    Parse Indonesian Number    ${text}
    RETURN    ${price}

Trade Buttons Are Visible
    ${buy}=     Run Keyword And Return Status    Element Should Be Visible    ${PAIR_BUY_BUTTON}
    ${sell}=    Run Keyword And Return Status    Element Should Be Visible    ${PAIR_SELL_BUTTON}
    RETURN    ${{ $buy and $sell }}
