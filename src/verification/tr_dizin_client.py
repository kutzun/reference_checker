"""
TR Dizin search API client.

Handles communication with TR Dizin (TÜBİTAK ULAKBİM's national
citation index). The endpoint is the public search API used by the
TR Dizin web frontend — no API key, no authentication, no CAPTCHA.
"""

import requests

from .exceptions import VerificationProviderError


class TrDizinClient:
    """
    Lightweight TR Dizin HTTP client.
    """

    BASE_URL = (
        "https://search.trdizin.gov.tr/api/defaultSearch/publication/"
    )

    def __init__(self, timeout: int = 10, limit: int = 5):
        self.timeout = timeout
        self.limit = limit

    def search(self, query: str) -> list[dict]:
        """
        Search TR Dizin for the given query.

        Args:
            query: Free-text search query.

        Returns:
            List of _source dicts from the response hits. Empty list
            if nothing matched.

        Raises:
            VerificationProviderError: On transport errors or malformed
            responses.
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
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise VerificationProviderError(
                "TR Dizin request failed."
            ) from exc
        except ValueError as exc:
            raise VerificationProviderError(
                "Invalid TR Dizin response."
            ) from exc

        hits = payload.get("hits", {}).get("hits", [])
        return [hit.get("_source", {}) for hit in hits if hit.get("_source")]