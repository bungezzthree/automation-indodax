#!/usr/bin/env python
"""Single entry point for executing the API suite (local and CI).

Examples
  python run.py                                  # prod, smoke
  python run.py --env staging --scope regression
  python run.py --scope all --include ticker --include orderbook   # selective run (OR)
  python run.py --scope regression --exclude P3
  python run.py --scope regression --rerun-failed                   # retry flaky failures once
  python run.py --dryrun                                            # syntax/keyword check only

Execution strategy
  smoke       -> --include smoke            (PR gate, < 1 min)
  regression  -> --include regression       (nightly / pre-release)
  all         -> everything
  prod        -> always adds --exclude no-prod (read-only guard, cannot be disabled)
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from robot import rebot_cli, run_cli

ROOT = Path(__file__).resolve().parent
SCOPES = {"smoke": ["smoke"], "regression": ["regression"], "all": []}
PROD_GUARD_TAGS = ["no-prod"]


def build_args(opts: argparse.Namespace, output_dir: Path) -> list[str]:
    args = [
        "--variablefile", f"{ROOT / 'config' / 'env_config.py'}:{opts.env}",
        "--outputdir", str(output_dir),
        "--listener", str(ROOT / "libraries" / "listeners" / "ResultSummaryListener.py"),
        "--xunit", "xunit.xml",
        "--name", f"Indodax API [{opts.env}]",
        "--metadata", f"Environment:{opts.env}",
        "--metadata", f"Scope:{opts.scope}",
        "--loglevel", opts.loglevel,
        "--pythonpath", str(ROOT),
        "--tagstatexclude", "P?",          # keep the tag statistics table readable
    ]
    for tag in SCOPES[opts.scope] + (opts.include or []):
        args += ["--include", tag]
    excludes = list(opts.exclude or [])
    if opts.env == "prod":
        excludes += PROD_GUARD_TAGS
    for tag in excludes:
        args += ["--exclude", tag]
    for test in opts.test or []:
        args += ["--test", test]
    if opts.dryrun:
        args.append("--dryrun")
    return args


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--env", default="prod", choices=["dev", "staging", "prod"])
    parser.add_argument("--scope", default="smoke", choices=list(SCOPES))
    parser.add_argument("--include", action="append", help="extra include tag (repeatable)")
    parser.add_argument("--exclude", action="append", help="exclude tag (repeatable)")
    parser.add_argument("--test", action="append", help="run test(s) by name / pattern")
    parser.add_argument("--rerun-failed", action="store_true", help="rerun failures once and merge")
    parser.add_argument("--loglevel", default="INFO", choices=["TRACE", "DEBUG", "INFO"])
    parser.add_argument("--dryrun", action="store_true")
    opts = parser.parse_args()

    output_dir = ROOT / "results" / opts.env / datetime.now().strftime("%Y%m%d-%H%M%S")
    args = build_args(opts, output_dir)
    rc = run_cli(args + [str(ROOT / "tests")], exit=False)

    if rc and opts.rerun_failed and not opts.dryrun:
        first = output_dir / "output.xml"
        shutil.copy(first, output_dir / "first_run.xml")
        print("\n=== Re-running failed tests once ===")
        run_cli(args + ["--rerunfailed", str(first), "--output", "rerun.xml",
                        "--log", "NONE", "--report", "NONE", str(ROOT / "tests")], exit=False)
        rc = rebot_cli(["--outputdir", str(output_dir), "--output", "output.xml", "--merge",
                        "--xunit", "xunit.xml", str(output_dir / "first_run.xml"),
                        str(output_dir / "rerun.xml")], exit=False)

    latest = ROOT / "results" / "latest"
    shutil.rmtree(latest, ignore_errors=True)
    shutil.copytree(output_dir, latest)
    print(f"\nReport: {output_dir / 'report.html'}\nLog:    {output_dir / 'log.html'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
