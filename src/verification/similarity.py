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
    Calculate token overlap similarity.

    Combines Jaccard (symmetric overlap) with containment (subset
    overlap). This fixes the subtitle-truncation case: a reference
    cites "Book: A Long Subtitle" while the provider stores only
    "Book". Jaccard alone undervalues that match because the provider
    title is a strict subset of the reference title. Containment
    treats it as a full match.

    Containment is guarded by a minimum token count so short generic
    titles ("Science", "History") do not match anything containing
    those words.

    Returns:
        Value between 0 and 1.
    """

    first_tokens = set(normalize_text(first).split())

    second_tokens = set(normalize_text(second).split())

    if not first_tokens or not second_tokens:
        return 0.0

    intersection = first_tokens & second_tokens

    union = first_tokens | second_tokens

    jaccard = len(intersection) / len(union)

    min_size = min(len(first_tokens), len(second_tokens))

    if min_size >= 3:
        containment = len(intersection) / min_size
        return max(jaccard, containment)

    return jaccard