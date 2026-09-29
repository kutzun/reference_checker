"""
doi.org resolver client.

Handles DOI resolution via the doi.org content-negotiation endpoint.
Unlike Crossref, this is not a search — it resolves one DOI at a time
and returns registered metadata in CSL-JSON.
"""

import requests
from urllib.parse import quote

from .exceptions import VerificationProviderError


class DoiOrgClient:
    """
    Lightweight doi.org HTTP client.
    """

    BASE_URL = "https://doi.org"
    CSL_JSON = "application/vnd.citationstyles.csl+json"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def resolve(self, doi: str) -> dict | None:
        """
        Resolve a DOI to CSL-JSON metadata.

        Args:
            doi: The DOI to resolve.

        Returns:
            Parsed CSL-JSON dict, or None if the DOI does not resolve
            (HTTP 404). A non-resolving DOI is a normal, expected
            outcome — the cascade continues to the next provider.

        Raises:
            VerificationProviderError: On transport errors or unexpected
            response shapes.
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/{quote(doi, safe='')}",
                headers={"Accept": self.CSL_JSON},
                timeout=self.timeout,
                allow_redirects=True,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:
            raise VerificationProviderError(
                f"doi.org request failed for {doi}"
            ) from exc
        except ValueError as exc:
            raise VerificationProviderError(
                f"Invalid doi.org response for {doi}"
            ) from exc