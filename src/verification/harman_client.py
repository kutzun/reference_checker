"""
Harman (TÜBİTAK ULAKBİM) API client.

Wraps the public search endpoint at
https://search.harman.ulakbim.gov.tr/api/defaultSearch/publication/,
which aggregates DergiPark journals, the YÖK National Thesis Center,
and Turkish university institutional repositories.

Returns the raw JSON payload. Record conversion belongs to
``harman_provider.py``.
"""

import requests

from .exceptions import VerificationProviderError


# Harman drops requests that do not present a desktop browser
# User-Agent. The default python-requests UA is blocked outright.
_HARMAN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


class HarmanClient:
    """Lightweight Harman HTTP client."""

    BASE_URL = (
        "https://search.harman.ulakbim.gov.tr"
        "/api/defaultSearch/publication/"
    )

    def __init__(self, timeout: int = 10, limit: int = 5) -> None:
        self.timeout = timeout
        self.limit = limit

    def search(self, query: str) -> dict:
        """
        Query the Harman publication search endpoint.

        Args:
            query: Full-text search string (typically the title).

        Returns:
            The raw JSON response dict, including the "hits" envelope.

        Raises:
            VerificationProviderError:
                If the request fails or the response is not valid JSON.
        """
        params = {
            "q": query,
            "order": "relevance-DESC",
            "page": 1,
            "limit": self.limit,
        }
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                headers=_HARMAN_HEADERS,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise VerificationProviderError(
                "Harman request failed."
            ) from exc
        except ValueError as exc:
            raise VerificationProviderError(
                "Invalid Harman response."
            ) from exc