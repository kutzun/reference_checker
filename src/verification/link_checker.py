"""
Link liveness checker.

Issues a lightweight HTTP request to a URL and classifies the result
as LIVE, DEAD, or UNKNOWN. Used to add context to references whose
bibliographic metadata could not be matched by any provider.

This is not a scraper. It does not read the page body. It only checks
whether the URL currently resolves, so the report can tell the user
"I couldn't verify this citation, but the link works" (or "the link
is broken").
"""

from enum import StrEnum

import requests


class LinkStatus(StrEnum):
    """Outcome of a link liveness check."""

    LIVE = "live"
    DEAD = "dead"
    UNKNOWN = "unknown"


class LinkChecker:
    """
    Classifies a URL as live, dead, or unknown.

    - 2xx or 3xx              → LIVE
    - 404, 410, ConnectionError → DEAD
    - 4xx other, timeout, other errors → UNKNOWN

    A 403 or 429 is UNKNOWN, not DEAD: many servers legitimately refuse
    programmatic clients without meaning the link is broken. Reporting
    those as DEAD would produce false positives in the report.
    """

    DEFAULT_TIMEOUT = 8

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout

    def check(self, url: str) -> LinkStatus:
        """
        Check whether *url* resolves.

        Args:
            url: The URL to check. Empty string returns UNKNOWN.

        Returns:
            LinkStatus.
        """
        if not url or not url.strip():
            return LinkStatus.UNKNOWN

        url = url.strip()

        # Only http/https are meaningful to check.
        if not url.lower().startswith(("http://", "https://")):
            return LinkStatus.UNKNOWN

        try:
            # stream=True means the body is not downloaded; we only
            # care about the status line and redirect chain.
            response = requests.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                stream=True,
                headers={"User-Agent": "ReferenceChecker/1.1"},
            )
            status = response.status_code
            response.close()
        except requests.ConnectionError:
            return LinkStatus.DEAD
        except requests.Timeout:
            return LinkStatus.UNKNOWN
        except requests.RequestException:
            return LinkStatus.UNKNOWN

        if 200 <= status < 400:
            return LinkStatus.LIVE
        if status in (404, 410):
            return LinkStatus.DEAD
        return LinkStatus.UNKNOWN