"""
OpenLibrary API client with built‑in rate limiting.

OpenLibrary is a free, open book catalogue run by the Internet Archive.
No API key is required.  The service asks for polite usage; a 1‑second
delay between requests keeps you well within acceptable limits.
"""

import time
import threading
import requests

from .exceptions import VerificationProviderError


class OpenLibraryClient:
    """
    Lightweight OpenLibrary HTTP client.
    """

    BASE_URL = "https://openlibrary.org"

    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        delay_between_requests: float = 1.0,
    ):
        """
        Args:
            timeout: HTTP timeout in seconds.
            max_retries: Maximum number of retries on 429 / network errors.
            backoff_factor: Base backoff multiplier (exponential).
            delay_between_requests: Minimum delay between requests (seconds).
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.delay_between_requests = delay_between_requests

        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "ReferenceChecker/1.0 (university tool; mailto:admin@example.com)"
        })

        self._last_request_time = 0.0
        self._lock = threading.Lock()

    def _wait_for_delay(self) -> None:
        """Thread‑safe enforcement of the minimum interval."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self.delay_between_requests:
                time.sleep(self.delay_between_requests - elapsed)
            self._last_request_time = time.monotonic()

    def search(self, query: str) -> dict:
        """
        Search OpenLibrary for books matching *query*.

        Args:
            query: Title / author search string.

        Returns:
            Decoded JSON response dictionary.

        Raises:
            VerificationProviderError: If all retries are exhausted.
        """
        params = {"q": query, "limit": 5}
        endpoint = f"{self.BASE_URL}/search.json"

        for attempt in range(self.max_retries + 1):
            try:
                self._wait_for_delay()

                response = self._session.get(
                    endpoint,
                    params=params,
                    timeout=self.timeout,
                )

                if response.status_code == 429:
                    if attempt == self.max_retries:
                        raise VerificationProviderError(
                            "OpenLibrary rate limit exceeded after retries."
                        )
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else self.backoff_factor * (2 ** attempt)
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.RequestException as exc:
                if attempt == self.max_retries:
                    raise VerificationProviderError(
                        "OpenLibrary request failed after retries."
                    ) from exc
                time.sleep(self.backoff_factor * (2 ** attempt))

            except ValueError as exc:
                raise VerificationProviderError(
                    "Invalid OpenLibrary response."
                ) from exc

        raise VerificationProviderError("Unexpected retry loop exit.")