*** Settings ***
Documentation       Mobile infrastructure layer (Android + iOS) on Appium.
...                 The platform is chosen at runtime (`--variablefile config/env_config.py:<env>:<android|ios>`),
...                 which also selects the platform's locator file (${SCREEN_LOCATORS}).
...                 AppiumLibrary captures a screenshot automatically when a keyword fails.
Library             AppiumLibrary    timeout=${MOBILE_TIMEOUT}    run_on_failure=Capture Page Screenshot
Library             Collections
Library             OperatingSystem
Library             ../libraries/UiHelpers.py
Variables           ${SCREEN_LOCATORS}


*** Keywords ***
Open Mobile Session
    Log    Capabilities: ${CAPABILITIES}
    TRY
        Open Application    ${APPIUM_SERVER_URL}    &{CAPABILITIES}
    EXCEPT    AS    ${error}
        Fatal Error    Cannot start ${PLATFORM} session on ${APPIUM_SERVER_URL} - is Appium running
        ...    and the device connected? Root cause: ${error}
    END
    Set Suite Metadata    Platform    ${PLATFORM}
    Set Suite Metadata    Environment    ${ENV}

Close Mobile Session
    Run Keyword And Ignore Error    Close All Applications

Capture Mobile Evidence On Failure
    IF    '${TEST_STATUS}' == 'FAIL'
        Run Keyword And Ignore Error    Capture Page Screenshot
        ${status}    ${source}=    Run Keyword And Ignore Error    Get Source
        Run Keyword And Ignore Error    Create File    ${OUTPUT_DIR}/page-source/${TEST_NAME}.xml    ${source}
    END

Tap If Present
    [Documentation]    Best-effort tap for optional UI (promos, permission dialogs, coach marks).
    [Arguments]    ${locator}    ${timeout}=3s
    ${present}=    Run Keyword And Return Status
    ...    Wait Until Page Contains Element    ${locator}    timeout=${timeout}
    IF    ${present}    Click Element    ${locator}
    RETURN    ${present}
