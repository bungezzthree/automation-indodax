*** Settings ***
Documentation       GET /api/summaries
Resource            ../../keywords/market_data.resource
Test Tags           summaries    public


*** Test Cases ***
Summaries Contain Key Markets
    [Tags]    regression    positive    contract    P2
    ${summaries}=    Get Market Summaries
    FOR    ${ticker_id}    IN    btc_idr    usdt_idr    eth_idr
        Dictionary Should Contain Key    ${summaries}[tickers]    ${ticker_id}
        Should Be Positive Number    ${summaries}[tickers][${ticker_id}][last]    ${ticker_id}.last
    END
