*** Settings ***
Documentation       Business keywords for the Indodax PRIVATE API (TAPI).
...                 Credentials come exclusively from env vars INDODAX_API_KEY / INDODAX_API_SECRET.
Resource            ../resources/common.resource


*** Keywords ***
Call Private Method
    [Arguments]    ${method}    ${api_key}=${INDODAX_API_KEY}    ${api_secret}=${INDODAX_API_SECRET}
    ...    ${sign}=${True}    &{params}
    ${resp}=    POST Signed TAPI Request    ${TAPI_URL}    ${method}    api_key=${api_key}
    ...    api_secret=${api_secret}    sign=${sign}    &{params}
    ${body}=    Get Json Body    ${resp}
    RETURN    ${body}

Private Call Should Be Rejected With
    [Arguments]    ${body}    ${expected_error_code}
    Json Should Match Schema    ${body}    tapi_error.json
    Should Be Equal    ${body}[error_code]    ${expected_error_code}

Skip Unless Credentials Are Configured
    Skip If    not ${HAS_CREDENTIALS}
    ...    INDODAX_API_KEY / INDODAX_API_SECRET not set - skipping authenticated scenario
