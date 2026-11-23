"""Load profiles. Because every user is paced at USER_RPS, users == target RPS / USER_RPS.

StepLoadShape ramps 2 -> 5 -> 8 -> 10 RPS. Holding each step lets us see *where*
latency or error rate starts to degrade (the "knee"), instead of only one data point.
"""
from __future__ import annotations

import math

from locust import LoadTestShape

from config.settings import SETTINGS

# (duration_s, target_rps)
STEPS = [(30, 2), (30, 5), (30, 8), (60, 10)]


class StepLoadShape(LoadTestShape):
    def tick(self):
        elapsed = self.get_run_time()
        boundary = 0
        for duration, rps in STEPS:
            boundary += duration
            if elapsed < boundary:
                rps = min(rps, SETTINGS.max_rps)
                users = max(1, math.floor(rps / SETTINGS.user_rps))
                return users, 1              # 1 user/s: avoids a synchronized burst when a step starts
        return None                          # end of test
