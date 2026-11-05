"""
Google Books API client.

Handles communication with the Google Books Volumes API. Requires an
API key: keyless requests return 429 with quota_limit_value "0", so
the client refuses to construct without one.
"""

import requests

from .exceptions import VerificationProviderError


class GoogleBooksClient:
    """
    Lightweight Google Books HTTP client.
    """

    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    def __init__(
        self,
        api_key: str,
        timeout: int = 10,
        max_results: int = 5,
    ):
        if not api_key:
            raise ValueError("GoogleBooksClient requires an api_key")

        self.api_key = api_key
        self.timeout = timeout
        self.max_results = max_results

    def search(self, query: str) -> dict:
        """
        Search Google Books.

        Args:
            query: Search string, may include intitle:/inauthor: operators.

        Returns:
            Parsed JSON response dict.

        Raises:
            VerificationProviderError: On transport errors or malformed
            responses.
        """
        params = {
            "q": query,
            "maxResults": self.max_results,
            "key": self.api_key,
        }

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise VerificationProviderError(
                "Google Books request failed."
            ) from exc
        except ValueError as exc:
            raise VerificationProviderError(
                "Invalid Google Books response."
            ) from exc