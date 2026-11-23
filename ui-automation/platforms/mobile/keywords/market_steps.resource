*** Settings ***
Documentation       Business steps for the mobile app - shared by Android and iOS.
Resource            ../screens/home_screen.resource
Resource            ../screens/market_screen.resource


*** Keywords ***
User Launches The App
    Dismiss Launch Interruptions

User Opens Market List
    Go To Market Tab

User Searches And Opens Pair
    [Arguments]    ${search_keyword}    ${pair_name}
    Search Pair    ${search_keyword}
    ${listed}=    Pair Is Listed    ${pair_name}
    Should Be True    ${listed}    '${pair_name}' not found after searching '${search_keyword}'
    Open Pair From List    ${pair_name}

Pair Detail Should Show Live Price
    [Arguments]    ${pair_name}
    Wait For Pair Detail    ${pair_name}
    ${price}=    Get Pair Last Price
    Number Should Be Positive    ${price}    ${pair_name} last price

Trade Actions Should Be Available
    ${visible}=    Trade Buttons Are Visible
    Should Be True    ${visible}    Buy/Sell buttons are not both visible on pair detail
