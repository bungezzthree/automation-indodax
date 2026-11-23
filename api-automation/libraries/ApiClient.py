"""HTTP client keyword library - the single place where HTTP happens.

Responsibilities (and nothing else):
  * session management + base URL resolution
  * retry with exponential backoff for transient failures (network, 429, 5xx)
  * HMAC-SHA512 signing for Indodax private API (TAPI)
  * structured request/response logging into the Robot log, with secrets masked
  * raising a descriptive ApiClientError instead of leaking raw stack traces

Assertions live in keywords/ and MarketAssertions.py, never here.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode, urljoin

import requests
from robot.api import logger
from robot.api.deco import keyword, library

RETRYABLE_STATUS = {429, 502, 503, 504}
MASKED_HEADERS = {"key", "sign", "authorization"}
MAX_LOGGED_BODY = 2_000  # chars - /api/pairs returns ~1MB, never dump it whole


class ApiClientError(AssertionError):
    """Raised when a request cannot be completed (after retries)."""


@library(scope="GLOBAL", auto_keywords=False)
class ApiClient:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json",
                                      "User-Agent": "qa-automation-poc/1.0"})
        self._base_url = ""
        self._timeout = 10
        self._max_retries = 2
        self._backoff_s = 1.0

    # ------------------------------------------------------------------ setup
    @keyword("Create Api Session")
    def create_api_session(self, base_url: str, timeout_s: int = 10,
                           max_retries: int = 2, backoff_s: float = 1.0):
        self._base_url = base_url.rstrip("/") + "/"
        self._timeout = int(timeout_s)
        self._max_retries = int(max_retries)
        self._backoff_s = float(backoff_s)
        logger.info(f"API session -> {self._base_url} (timeout={self._timeout}s, "
                    f"retries={self._max_retries})")

    @keyword("Close Api Session")
    def close_api_session(self):
        self._session.close()

    # --------------------------------------------------------------- requests
    @keyword("GET Request")
    def get_request(self, path: str, params: dict | None = None,
                    expected_status: int | str = 200) -> requests.Response:
        """GET ``path`` (relative to base URL). ``expected_status=any`` disables the check."""
        return self._send("GET", path, params=params, expected_status=expected_status)

    @keyword("POST Signed TAPI Request")
    def post_signed_tapi_request(self, tapi_url: str, method: str, api_key: str = "",
                                 api_secret: str = "", sign: bool = True,
                                 expected_status: int | str = 200, **params) -> requests.Response:
        """Calls an Indodax private API method.

        ``sign=False`` deliberately omits the Sign header (negative testing).
        """
        body = {"method": method, "timestamp": int(time.time() * 1000), "recvWindow": 5000, **params}
        encoded = urlencode(body)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if api_key:
            headers["Key"] = api_key
        if sign:
            headers["Sign"] = hmac.new(api_secret.encode(), encoded.encode(),
                                       hashlib.sha512).hexdigest()
        return self._send("POST", tapi_url, data=encoded, headers=headers,
                          expected_status=expected_status, retry=False)

    # -------------------------------------------------------------- internals
    def _send(self, verb: str, path: str, expected_status=200, retry: bool = True,
              **kwargs) -> requests.Response:
        if not path.startswith("http") and not self._base_url:
            raise ApiClientError("No API session: call 'Create Api Session' (done by the root "
                                 "suite setup - run the 'tests' directory, not a single file).")
        url = path if path.startswith("http") else urljoin(self._base_url, path.lstrip("/"))
        attempts = (self._max_retries if retry else 0) + 1
        last_error: Exception | None = None
        response = None

        for attempt in range(1, attempts + 1):
            try:
                response = self._session.request(verb, url, timeout=self._timeout, **kwargs)
                self._log_exchange(response, attempt)
                if response.status_code not in RETRYABLE_STATUS or attempt == attempts:
                    break
                last_error = None
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_error = exc
                logger.warn(f"{verb} {url} attempt {attempt}/{attempts} failed: {exc}")
                if attempt == attempts:
                    raise ApiClientError(f"{verb} {url} failed after {attempts} attempt(s): "
                                         f"{type(exc).__name__}: {exc}") from exc
            delay = self._backoff_s * 2 ** (attempt - 1)
            logger.info(f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{attempts})")
            time.sleep(delay)

        if response is None:  # pragma: no cover - defensive
            raise ApiClientError(f"{verb} {url} produced no response: {last_error}")

        if str(expected_status).lower() != "any" and response.status_code != int(expected_status):
            raise ApiClientError(
                f"{verb} {url} -> expected HTTP {expected_status}, got {response.status_code}. "
                f"Body: {response.text[:500]}")
        return response

    @staticmethod
    def _log_exchange(response: requests.Response, attempt: int):
        req = response.request
        headers = {k: ("***" if k.lower() in MASKED_HEADERS else v) for k, v in req.headers.items()}
        body = response.text
        try:
            body = json.dumps(response.json(), indent=2)
        except ValueError:
            pass
        if len(body) > MAX_LOGGED_BODY:
            body = body[:MAX_LOGGED_BODY] + f"\n... <truncated, {len(response.text)} chars total>"
        logger.info(
            f"<b>{req.method} {req.url}</b> (attempt {attempt}) -> "
            f"<b>{response.status_code}</b> in {response.elapsed.total_seconds() * 1000:.0f} ms"
            f"<details><summary>request headers</summary><pre>{json.dumps(headers, indent=2)}</pre></details>"
            f"<details><summary>response body</summary><pre>{_escape(body)}</pre></details>",
            html=True)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
