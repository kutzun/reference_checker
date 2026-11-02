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
        email: str | None = None,
    ):
        """
        Initialize client.

        Args:
            timeout:
                HTTP timeout in seconds.
            email:
                Optional contact email. When set, Crossref adds the
                request to its "polite pool" with 2x-3x higher rate
                limits. Optional.
        """

        self.timeout = timeout
        self.email = email

    def _build_params(self, query: str) -> dict:
        """Build request params. Includes mailto if an email is set."""
        params = {
            "query.bibliographic": query,
            "rows": 5,
        }
        if self.email:
            params["mailto"] = self.email
        return params

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
                params=self._build_params(query),
                timeout=self.timeout,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:
            raise VerificationProviderError("Crossref request failed.") from exc

        except ValueError as exc:
            raise VerificationProviderError("Invalid Crossref response.") from exc
