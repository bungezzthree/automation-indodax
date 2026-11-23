*** Settings ***
Documentation       Business keywords for Indodax PUBLIC market-data endpoints.
...                 Naming: "Get ..." = action (returns data), "... Should ..." = assertion.
Resource            ../resources/common.resource


*** Variables ***
${SERVER_TIME_PATH}     /api/server_time
${PAIRS_PATH}           /api/pairs
${TICKER_PATH}          /api/ticker
${DEPTH_PATH}           /api/depth
${TRADES_PATH}          /api/trades
${SUMMARIES_PATH}       /api/summaries


*** Keywords ***
# ----------------------------------------------------------------- actions
Get Server Time
    ${resp}=    GET Request    ${SERVER_TIME_PATH}
    Response Time Should Be Within SLA    ${resp}    ${RESPONSE_TIME_SLA_MS}
    ${body}=    Get Json Body    ${resp}
    RETURN    ${body}

Get All Pairs
    ${resp}=    GET Request    ${PAIRS_PATH}
    Response Should Be Json    ${resp}
    ${body}=    Get Json Body    ${resp}
    RETURN    ${body}

Get Ticker
    [Arguments]    ${pair_id}
    ${resp}=    GET Request    ${TICKER_PATH}/${pair_id}
    Response Time Should Be Within SLA    ${resp}    ${RESPONSE_TIME_SLA_MS}
    ${body}=    Get Json Body    ${resp}
    Dictionary Should Not Contain Key    ${body}    error
    ...    msg=Ticker for '${pair_id}' returned error: ${body}
    RETURN    ${body}[ticker]

Get Order Book
    [Arguments]    ${pair_id}
    ${resp}=    GET Request    ${DEPTH_PATH}/${pair_id}
    ${body}=    Get Json Body    ${resp}
    Json Should Match Schema    ${body}    depth.json
    RETURN    ${body}

Get Recent Trades
    [Arguments]    ${pair_id}
    ${resp}=    GET Request    ${TRADES_PATH}/${pair_id}
    ${body}=    Get Json Body    ${resp}
    Json Should Match Schema    ${body}    trades.json
    RETURN    ${body}

Get Market Summaries
    ${resp}=    GET Request    ${SUMMARIES_PATH}
    ${body}=    Get Json Body    ${resp}
    Json Should Match Schema    ${body}    summaries.json
    RETURN    ${body}

Request Public Endpoint With Pair
    [Documentation]    Raw call for negative testing - no status / error assertion.
    [Arguments]    ${endpoint}    ${pair_id}
    ${resp}=    GET Request    /api/${endpoint}/${pair_id}    expected_status=any
    RETURN    ${resp}

# -------------------------------------------------------------- assertions
Ticker Should Be Valid
    [Documentation]    Contract + business rules for one ticker.
    [Arguments]    ${ticker}    ${volume_field}
    Json Should Match Schema    ${{ {"ticker": $ticker} }}    ticker.json
    Dictionary Should Contain Key    ${ticker}    ${volume_field}
    ...    msg=Ticker is missing volume field '${volume_field}'
    FOR    ${field}    IN    buy    sell    last    high    low
        Should Be Positive Number    ${ticker}[${field}]    ${field}
    END
    Should Be Non Negative Number    ${ticker}[${volume_field}]    ${volume_field}
    Should Be Non Negative Number    ${ticker}[vol_idr]    vol_idr
    Value Should Be Between    ${ticker}[last]    ${ticker}[low]    ${ticker}[high]    last
    Best Bid Should Not Exceed Best Ask    ${ticker}[buy]    ${ticker}[sell]
    Timestamp Should Be Recent    ${ticker}[server_time]    unit=s

Order Book Should Be Consistent
    [Arguments]    ${book}
    Should Not Be Empty    ${book}[buy]    msg=Buy side of order book is empty
    Should Not Be Empty    ${book}[sell]    msg=Sell side of order book is empty
    Order Book Side Should Be Sorted    ${book}[buy]    buy
    Order Book Side Should Be Sorted    ${book}[sell]    sell
    Best Bid Should Not Exceed Best Ask    ${book}[buy][0][0]    ${book}[sell][0][0]

Trades Should Be Valid
    [Arguments]    ${trades}
    Should Not Be Empty    ${trades}    msg=No recent trades returned
    FOR    ${trade}    IN    @{trades}
        Should Be Positive Number    ${trade}[price]    price (tid ${trade}[tid])
        Should Be Positive Number    ${trade}[amount]    amount (tid ${trade}[tid])
    END
    Timestamp Should Be Recent    ${trades}[0][date]    max_drift_s=86400

Response Should Be Invalid Pair Error
    [Documentation]    Indodax returns HTTP 200 with an error envelope for unknown pairs.
    ...                Assert the envelope, not just the status code.
    [Arguments]    ${response}
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Get Json Body    ${response}
    Json Should Match Schema    ${body}    public_error.json
    Should Be Equal    ${body}[error]    invalid_pair
    Should Be Equal    ${body}[error_description]    Invalid Pair
