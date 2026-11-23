*** Settings ***
Documentation       Mobile UI suite (Android & iOS) - one codebase, platform picked at runtime:
...                 python run.py --platform android   |   python run.py --platform ios
Resource            ../../../resources/mobile_common.resource
Suite Setup         Open Mobile Session
Suite Teardown      Close Mobile Session
Test Teardown       Capture Mobile Evidence On Failure
Test Tags           mobile    ui
