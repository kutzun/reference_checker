"""
Similarity utilities for reference matching.
"""

import re


def normalize_text(
    text: str,
) -> str:
    """
    Normalize text for comparison.
    """

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def token_similarity(
    first: str,
    second: str,
) -> float:
    """
    Calculate simple token overlap similarity.

    Returns:
        Value between 0 and 1.
    """

    first_tokens = set(normalize_text(first).split())

    second_tokens = set(normalize_text(second).split())

    if not first_tokens or not second_tokens:
        return 0.0

    intersection = first_tokens & second_tokens

    union = first_tokens | second_tokens

    return len(intersection) / len(union)
