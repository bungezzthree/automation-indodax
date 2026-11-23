*** Settings ***
Documentation       Indodax API automation - root suite.
...                 Tag taxonomy (multi-tag per test):
...                 platform: api | level: smoke, regression | feature: pairs, ticker, orderbook, trades,
...                 summaries, server-time, auth | type: positive, negative, contract, consistency |
...                 priority: P1-P3 | env-guard: no-prod, requires-credentials
Resource            ../resources/common.resource
Suite Setup         Initialize Api Suite
Suite Teardown      Teardown Api Suite
Test Tags           api
