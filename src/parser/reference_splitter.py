"""
Reference entry splitting.

Separates a reference section into individual reference entries.
"""

import re


def split_references(
    paragraphs: list[str],
) -> list[str]:
    """
    Split reference section paragraphs into entries.

    Currently assumes each reference occupies one paragraph.

    Args:
        paragraphs:
            Reference section paragraphs.

    Returns:
        List of individual reference strings.
    """

    references = []

    for paragraph in paragraphs:
        cleaned = clean_reference(paragraph)

        if cleaned:
            references.append(cleaned)

    return references


def clean_reference(
    text: str,
) -> str:
    """
    Clean a single reference entry.

    Removes:
    - leading/trailing whitespace
    - repeated spaces

    Args:
        text:
            Raw reference text.

    Returns:
        Cleaned reference.
    """

    text = text.strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text
