*** Settings ***
Documentation       Screen object: app launch / home. Platform-neutral - locators are injected.
Resource            ../../../resources/mobile_common.resource


*** Keywords ***
Dismiss Launch Interruptions
    [Documentation]    Onboarding, OS permission prompts and promo banners are optional and
    ...                vary per account/state - tap them away if they appear, never fail on them.
    Tap If Present    ${PERMISSION_DENY}
    Tap If Present    ${ONBOARDING_SKIP}
    Tap If Present    ${PROMO_CLOSE}

Go To Market Tab
    Wait Until Element Is Visible    ${BOTTOM_NAV_MARKET}
    Click Element    ${BOTTOM_NAV_MARKET}
