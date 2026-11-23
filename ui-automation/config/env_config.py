"""Robot Framework variable file for UI suites.

Usage:
  robot --variablefile config/env_config.py:prod:web      platforms/web/tests
  robot --variablefile config/env_config.py:prod:android  platforms/mobile/tests
  robot --variablefile config/env_config.py:prod:ios      platforms/mobile/tests

Resolution order (highest wins): env var > environments.yaml[env] > environments.yaml[common].
For mobile, capabilities/<platform>.yaml is loaded and ${VARS} inside it are expanded from
the process environment (device name, UDID, app path ... differ per machine / device farm).
"""
import os
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent
PLATFORMS = ("web", "android", "ios")


def _override(name: str, default):
    raw = os.getenv(name)
    if raw is None:
        return default
    if isinstance(default, bool):
        return raw.strip().lower() in ("1", "true", "yes")
    return type(default)(raw) if default is not None else raw


def _load_capabilities(platform: str) -> dict:
    raw = yaml.safe_load((CONFIG_DIR / "capabilities" / f"{platform}.yaml").read_text(encoding="utf-8"))
    caps = {}
    for key, value in raw.items():
        if isinstance(value, str):
            value = os.path.expandvars(value)
            if value.startswith("$"):          # unresolved placeholder -> drop, let Appium default
                continue
        caps[key] = value
    return caps


def get_variables(env: str | None = None, platform: str = "web") -> dict:
    config = yaml.safe_load((CONFIG_DIR / "environments.yaml").read_text(encoding="utf-8"))
    env = (env or os.getenv("TEST_ENV") or config["default_env"]).lower()
    platform = platform.lower()
    if env not in config["environments"]:
        raise ValueError(f"Unknown env '{env}'. Valid: {sorted(config['environments'])}")
    if platform not in PLATFORMS:
        raise ValueError(f"Unknown platform '{platform}'. Valid: {PLATFORMS}")

    merged = {**config["common"], **config["environments"][env]}
    variables = {k.upper(): _override(k.upper(), v) for k, v in merged.items()}
    variables.update(ENV=env, PLATFORM=platform)

    if platform in ("android", "ios"):
        caps = _load_capabilities(platform)
        variables["CAPABILITIES"] = caps
        variables["APP_ID"] = caps.get("appium:appPackage") or caps.get("appium:bundleId", "")
        # Platform-specific locator file - same variable names, different values.
        variables["SCREEN_LOCATORS"] = str(
            CONFIG_DIR.parent / "platforms" / "mobile" / "locators" / platform / "market_screens.py")
    return variables
