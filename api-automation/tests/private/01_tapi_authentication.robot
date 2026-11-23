*** Settings ***
Documentation       Indodax private API (POST /tapi) - authentication guard rails.
...                 Negative cases need no real credentials and are safe in every env.
...                 Authenticated cases are skipped unless INDODAX_API_KEY/SECRET are exported.
Resource            ../../keywords/private_api.resource
Test Tags           auth    private


*** Test Cases ***
Request Without Sign Header Is Rejected
    [Tags]    smoke    regression    negative    P1
    ${body}=    Call Private Method    getInfo    api_key=DUMMYKEY    sign=${False}
    Private Call Should Be Rejected With    ${body}    sign_not_found

Request With Invalid Credentials Is Rejected
    [Tags]    regression    negative    P1
    ${body}=    Call Private Method    getInfo    api_key=DUMMYKEY    api_secret=dummy-secret
    Private Call Should Be Rejected With    ${body}    invalid_credentials

Authenticated GetInfo Returns Account Balance
    [Documentation]    Read-only call; still guarded by `requires-credentials`.
    [Tags]    regression    positive    requires-credentials    P1
    Skip Unless Credentials Are Configured
    ${body}=    Call Private Method    getInfo
    Should Be Equal As Integers    ${body}[success]    1    msg=getInfo failed: ${body}
    Dictionary Should Contain Key    ${body}[return]    balance
