"""
Verification evidence data model.

Stores all evidence collected during the verification process.
This module does not make final verification decisions.
"""

from dataclasses import dataclass, field
from datetime import datetime

from .enums import Provider
from .reference_match import ReferenceMatch


@dataclass
class VerificationEvidence:
    """
    Collection of evidence gathered for a reference.

    Evidence may come from cache or external providers.
    Decision logic belongs to VerificationResult, not this class.
    """

    matches: list[ReferenceMatch] = field(default_factory=list)

    providers_checked: list[Provider] = field(default_factory=list)

    doi_found: str | None = None

    cache_hit: bool = False

    verification_time: datetime | None = None

    notes: list[str] = field(default_factory=list)

    def add_match(self, match: ReferenceMatch) -> None:
        """
        Add a verification candidate.

        Args:
            match:
                Candidate match from a provider.
        """
        self.matches.append(match)

    def add_provider(self, provider: Provider) -> None:
        """
        Record that a provider was queried.

        Args:
            provider:
                Verification provider.
        """
        if provider not in self.providers_checked:
            self.providers_checked.append(provider)

    def best_match(self) -> ReferenceMatch | None:
        """
        Return the highest-scoring candidate match.

        Returns:
            Best available match, or None if no matches exist.
        """
        if not self.matches:
            return None

        scored_matches = [
            match for match in self.matches if match.overall_score is not None
        ]

        if not scored_matches:
            return self.matches[0]

        return max(
            scored_matches,
            key=lambda match: match.overall_score,
        )
