*** Settings ***
Documentation       Web infrastructure layer: browser lifecycle, evidence on failure.
...                 Browser library = Robot Framework wrapper around Playwright.
...                 `run_on_failure` takes a full-page screenshot automatically on every failing keyword.
Library             Browser    run_on_failure=Take Screenshot \ failure-{index} \ fullPage=True
...                 auto_closing_level=SUITE
Library             Collections
Library             ../libraries/UiHelpers.py


*** Keywords ***
Open Web Session
    [Documentation]    Suite Setup: one browser per suite, one fresh context (cookies, storage) per test.
    Set Browser Timeout    ${BROWSER_TIMEOUT}
    New Browser    browser=${BROWSER}    headless=${HEADLESS}
    Set Suite Metadata    Environment    ${ENV}
    Set Suite Metadata    Base URL    ${WEB_BASE_URL}
    Set Suite Metadata    Browser    ${BROWSER} (headless=${HEADLESS})

Start Clean Context
    [Documentation]    Test Setup: isolated context so tests never share state.
    ${trace}=    Set Variable If    ${TRACING}    ${OUTPUT_DIR}/traces/${TEST_NAME}.zip    ${False}
    ${state}=    Build Preseeded User State
    New Context    viewport={'width': ${VIEWPORT_WIDTH}, 'height': ${VIEWPORT_HEIGHT}}
    ...    locale=${LOCALE}    tracing=${trace}    storageState=${state}

Build Preseeded User State
    [Documentation]    Known user state applied to EVERY context, so tests never meet one-time UI.
    ...                `isLiteMode=true` = user already chose the classic ("Trade Klasik") layout, which
    ...                suppresses the "Personalisasi Tampilan Trade" modal (it shows only when the key
    ...                is unset on a >=1024px viewport) and keeps /market/<PAIR> on the classic layout
    ...                our locators target. The site reads it from BOTH localStorage and cookie.
    ${path}=    Build Storage State    ${WEB_BASE_URL}    ${OUTPUT_DIR}/state/user_state.json
    ...    local_storage=${{ {"isLiteMode": "true"} }}    cookies=${{ {"isLiteMode": "true"} }}
    RETURN    ${path}

Close Web Session
    Close Browser    ALL

Capture Evidence On Failure
    [Documentation]    Test Teardown: extra evidence beyond the automatic screenshot.
    IF    '${TEST_STATUS}' == 'FAIL'
        ${status}    ${url}=    Run Keyword And Ignore Error    Get Url
        Log    ${TEST_NAME} failed on URL: ${url}    level=WARN
    END
    Close Context
