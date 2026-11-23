"""Listener #2 - enforces the 10 RPS ceiling *before* and *during* the run.

Before: refuse to start a constant-profile run whose users x USER_RPS exceeds MAX_RPS.
During: every second, if the observed RPS exceeds MAX_RPS (+tolerance) for 3 consecutive
seconds, stop the test - we must never hammer a third-party service beyond the agreement.
"""
from __future__ import annotations

import logging

import gevent
from locust import events
from locust.runners import STATE_CLEANUP, STATE_STOPPED, STATE_STOPPING, WorkerRunner

from config.settings import SETTINGS

log = logging.getLogger("rps_guard")


@events.init.add_listener
def _validate_configuration(environment, **_):
    opts = environment.parsed_options
    if opts is None or environment.shape_class is not None:
        return
    planned = (opts.num_users or 0) * SETTINGS.user_rps
    if planned > SETTINGS.max_rps:
        raise SystemExit(f"[rps_guard] {opts.num_users} users x {SETTINGS.user_rps} rps = "
                         f"{planned} RPS exceeds MAX_RPS={SETTINGS.max_rps}. Lower --users.")
    log.info("rps_guard: planned %.1f RPS <= MAX_RPS %.1f", planned, SETTINGS.max_rps)


@events.test_start.add_listener
def _start_watchdog(environment, **_):
    if isinstance(environment.runner, WorkerRunner):
        return
    gevent.spawn(_watchdog, environment)


def _watchdog(environment):
    limit = SETTINGS.max_rps * (1 + SETTINGS.rps_tolerance_pct / 100)
    breaches = 0
    runner = environment.runner
    while runner and runner.state not in (STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP):
        gevent.sleep(1)
        current = environment.stats.total.current_rps
        breaches = breaches + 1 if current > limit else 0
        if breaches >= 3:
            log.error("rps_guard: %.1f RPS > limit %.1f for 3s - stopping test", current, limit)
            environment.process_exit_code = 2
            runner.quit()
            return
