*** Settings ***
Documentation       GET /api/server_time
Resource            ../../keywords/market_data.resource
Test Tags           server-time    public


*** Test Cases ***
Server Time Returns Current Epoch In Milliseconds
    [Tags]    smoke    regression    positive    contract    P1
    ${body}=    Get Server Time
    Json Should Match Schema    ${body}    server_time.json
    Should Be Equal    ${body}[timezone]    UTC
    Timestamp Should Be Recent    ${body}[server_time]    max_drift_s=120    unit=ms
