"""
Verification provider interface.

Defines the contract that external metadata providers
must implement.
"""

from abc import ABC, abstractmethod

from models import Reference, ReferenceMatch


class VerificationProvider(ABC):
    """
    Abstract interface for reference verification providers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Provider name.

        Returns:
            Human-readable provider identifier.
        """
        pass

    @abstractmethod
    def search(
        self,
        reference: Reference,
    ) -> list[ReferenceMatch]:
        """
        Search provider database for matching references.

        Args:
            reference:
                Parsed reference metadata.

        Returns:
            Candidate reference matches.
        """
        pass
