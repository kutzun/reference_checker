"""
Crossref verification provider.

Queries Crossref metadata services and converts
results into ReferenceMatch objects.
"""

from models import (
    Reference,
    ReferenceMatch,
)

from .provider import VerificationProvider


class CrossrefProvider(VerificationProvider):
    """
    Verification provider using Crossref.
    """

    @property
    def name(self) -> str:
        """
        Provider identifier.

        Returns:
            Provider name.
        """

        return "crossref"

    def search(
        self,
        reference: Reference,
    ) -> list[ReferenceMatch]:
        """
        Search Crossref for matching references.

        Args:
            reference:
                Parsed reference metadata.

        Returns:
            Candidate matches.
        """

        # API implementation will be added next.
        # Returning an empty list keeps the provider
        # interface testable before networking.

        return []
