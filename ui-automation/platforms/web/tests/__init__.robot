*** Settings ***
Documentation       Web UI suite - Robot Framework + Browser (Playwright).
...                 Lifecycle: 1 browser per run, 1 isolated context per test, screenshot on failure.
Resource            ../../../resources/web_common.resource
Suite Setup         Open Web Session
Suite Teardown      Close Web Session
Test Setup          Start Clean Context
Test Teardown       Capture Evidence On Failure
Test Tags           web    ui
