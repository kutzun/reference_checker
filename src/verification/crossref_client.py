"""
Crossref API client.

Handles communication with Crossref services.
"""

import requests

from .exceptions import (
    VerificationProviderError,
)


class CrossrefClient:
    """
    Lightweight Crossref HTTP client.
    """

    BASE_URL = "https://api.crossref.org"

    def __init__(
        self,
        timeout: int = 10,
    ):
        """
        Initialize client.

        Args:
            timeout:
                HTTP timeout in seconds.
        """

        self.timeout = timeout

    def search(
        self,
        query: str,
    ) -> dict:
        """
        Search Crossref works endpoint.

        Args:
            query:
                Search query string.

        Returns:
            JSON response.

        Raises:
            VerificationProviderError:
                If Crossref request fails.
        """

        try:
            response = requests.get(
                f"{self.BASE_URL}/works",
                params={
                    "query.bibliographic": query,
                    "rows": 5,
                },
                timeout=self.timeout,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:
            raise VerificationProviderError("Crossref request failed.") from exc

        except ValueError as exc:
            raise VerificationProviderError("Invalid Crossref response.") from exc
