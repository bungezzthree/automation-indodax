*** Settings ***
Documentation       Infrastructure layer shared by every API suite:
...                 library imports, environment wiring, suite lifecycle hooks.
...                 Tests never import libraries directly - they import keyword resources,
...                 which import this file.
Library             Collections
Library             ../libraries/ApiClient.py
Library             ../libraries/SchemaValidator.py
Library             ../libraries/MarketAssertions.py
Variables           ../config/env_config.py


*** Keywords ***
Initialize Api Suite
    [Documentation]    Suite Setup for every API suite.
    Create Api Session    ${API_BASE_URL}    timeout_s=${TIMEOUT_S}    max_retries=${MAX_RETRIES}
    Set Suite Metadata    Environment    ${ENV}
    Set Suite Metadata    Base URL    ${API_BASE_URL}

Teardown Api Suite
    Close Api Session

Get Json Body
    [Documentation]    Parses the body and fails with the raw text if it is not JSON.
    [Arguments]    ${response}
    TRY
        ${json}=    Call Method    ${response}    json
    EXCEPT    AS    ${err}
        Fail    Response from ${response.url} is not valid JSON (${err}): ${response.text}[:300]
    END
    RETURN    ${json}

Response Should Be Json
    [Arguments]    ${response}
    Should Start With    ${response.headers}[Content-Type]    application/json
    ...    msg=Expected JSON content-type but got '${response.headers}[Content-Type]'
