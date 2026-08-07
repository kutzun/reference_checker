"""
Author similarity utilities.
"""

import re


def normalize_author(
    author: str,
) -> str:
    """
    Normalize author name.
    """

    author = author.lower()

    author = re.sub(
        r"[^a-z\s]",
        "",
        author,
    )

    return author.strip()


def author_similarity(
    reference_authors: list[str],
    candidate_authors: list[str],
) -> float:
    """
    Calculate author overlap.

    Returns:
        Value between 0 and 1.
    """

    if not reference_authors or not candidate_authors:
        return 0.0

    reference = {normalize_author(author) for author in reference_authors}

    candidate = {normalize_author(author) for author in candidate_authors}

    if not reference or not candidate:
        return 0.0

    overlap = reference & candidate

    return len(overlap) / len(reference)
