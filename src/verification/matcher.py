"""
Reference matching logic.

Scores candidate matches against parsed references.
"""

from models import (
    Reference,
    ReferenceMatch,
)

from .authors import (
    author_similarity,
)
from .similarity import (
    token_similarity,
)


class ReferenceMatcher:
    """
    Calculates similarity between references.
    """

    def score(
        self,
        reference: Reference,
        match: ReferenceMatch,
    ) -> float:
        """
        Calculate overall match score.

        Args:
            reference:
                Original reference.

            match:
                Candidate match.

        Returns:
            Score between 0 and 1.
        """

        if reference.doi and match.doi and reference.doi.lower() == match.doi.lower():
            match.doi_match = True
            match.overall_score = 1.0

            return 1.0

        score = 0.0

        if reference.title and match.title:
            match.title_similarity = token_similarity(
                reference.title,
                match.title,
            )

            score += match.title_similarity * 0.5

        if reference.authors and match.authors:
            match.author_similarity = author_similarity(
                reference.authors,
                match.authors,
            )

            score += match.author_similarity * 0.3

        if reference.year and match.year:
            match.year_match = reference.year == match.year

            if match.year_match:
                score += 0.2

        match.overall_score = score

        return score
