#!/usr/bin/env python
"""Single entry point for UI suites - web (Playwright) and mobile (Appium).

Examples
  python run.py                                           # web, prod, smoke
  python run.py --platform web --scope regression --headed
  python run.py --platform web --include orderbook-ui     # selective run
  python run.py --platform android --scope smoke          # needs Appium + device
  python run.py --platform ios --env staging
  python run.py --platform web --scope regression --rerun-failed
  python run.py --platform web --processes 3              # parallel via pabot (optional)

Every test automatically gets the platform tag (web/android/ios) via --settag, so results
from all 4 platforms (incl. the API project) can be merged and filtered in one rebot report.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from robot import rebot_cli, run_cli

ROOT = Path(__file__).resolve().parent
SCOPES = {"smoke": ["smoke"], "regression": ["regression"], "all": []}
PROD_GUARD_TAGS = ["no-prod"]
TEST_DIRS = {"web": ROOT / "platforms" / "web" / "tests",
             "android": ROOT / "platforms" / "mobile" / "tests",
             "ios": ROOT / "platforms" / "mobile" / "tests"}


def build_args(opts, output_dir: Path) -> list[str]:
    args = [
        "--variablefile", f"{ROOT / 'config' / 'env_config.py'}:{opts.env}:{opts.platform}",
        "--outputdir", str(output_dir),
        "--listener", str(ROOT / "libraries" / "listeners" / "ResultSummaryListener.py"),
        "--xunit", "xunit.xml",
        "--name", f"Indodax UI {opts.platform} [{opts.env}]",
        "--metadata", f"Environment:{opts.env}",
        "--metadata", f"Platform:{opts.platform}",
        "--metadata", f"Scope:{opts.scope}",
        "--settag", opts.platform,
        "--pythonpath", str(ROOT),
        "--tagstatexclude", "P?",
    ]
    for tag in SCOPES[opts.scope] + (opts.include or []):
        args += ["--include", tag]
    for tag in (opts.exclude or []) + (PROD_GUARD_TAGS if opts.env == "prod" else []):
        args += ["--exclude", tag]
    for test in opts.test or []:
        args += ["--test", test]
    if opts.dryrun:
        args.append("--dryrun")
    return args


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--platform", default="web", choices=list(TEST_DIRS))
    parser.add_argument("--env", default="prod", choices=["dev", "staging", "prod"])
    parser.add_argument("--scope", default="smoke", choices=list(SCOPES))
    parser.add_argument("--include", action="append")
    parser.add_argument("--exclude", action="append")
    parser.add_argument("--test", action="append")
    parser.add_argument("--headed", action="store_true", help="web: show the browser")
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"])
    parser.add_argument("--trace", action="store_true", help="web: record Playwright traces")
    parser.add_argument("--processes", type=int, default=1, help=">1 runs suites in parallel with pabot")
    parser.add_argument("--rerun-failed", action="store_true")
    parser.add_argument("--dryrun", action="store_true")
    opts = parser.parse_args()

    # CLI flags become env-var overrides picked up by config/env_config.py
    if opts.headed:
        os.environ["HEADLESS"] = "false"
    if opts.browser:
        os.environ["BROWSER"] = opts.browser
    if opts.trace:
        os.environ["TRACING"] = "true"

    output_dir = ROOT / "results" / opts.platform / opts.env / datetime.now().strftime("%Y%m%d-%H%M%S")
    args = build_args(opts, output_dir)
    tests = str(TEST_DIRS[opts.platform])

    if opts.processes > 1:
        rc = subprocess.call([sys.executable, "-m", "pabot.pabot", "--processes",
                              str(opts.processes), *args, tests])
    else:
        rc = run_cli(args + [tests], exit=False)

    if rc and opts.rerun_failed and not opts.dryrun:
        first = output_dir / "output.xml"
        shutil.copy(first, output_dir / "first_run.xml")
        print("\n=== Re-running failed tests once ===")
        run_cli(args + ["--rerunfailed", str(first), "--output", "rerun.xml",
                        "--log", "NONE", "--report", "NONE", tests], exit=False)
        rc = rebot_cli(["--outputdir", str(output_dir), "--output", "output.xml", "--merge",
                        "--xunit", "xunit.xml", str(output_dir / "first_run.xml"),
                        str(output_dir / "rerun.xml")], exit=False)

    print(f"\nReport: {output_dir / 'report.html'}\nLog:    {output_dir / 'log.html'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
