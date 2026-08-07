"""
Text-based metadata extraction.

Extracts authors and titles from raw reference strings.
"""

import re


def extract_authors(
    text: str,
) -> list[str]:
    """
    Extract authors from a reference string.

    Assumes author list appears before publication year.

    Args:
        text:
            Raw reference text.

    Returns:
        List of author strings.
    """

    year_match = re.search(
        r"\((19|20)\d{2}\)",
        text,
    )

    if year_match is None:
        return []

    author_part = text[: year_match.start()]

    author_part = author_part.strip()

    if not author_part:
        return []

    author_part = re.sub(
        r",\s*$",
        "",
        author_part,
    )

    authors = re.split(
        r",\s*(?=[A-Z][a-z]+)",
        author_part,
    )

    return [author.strip() for author in authors if author.strip()]


def extract_title(
    text: str,
) -> str | None:
    """
    Extract title after publication year.

    Assumes APA-like format:

    Authors. (Year). Title.

    Args:
        text:
            Raw reference text.

    Returns:
        Title or None.
    """

    match = re.search(
        r"\(\d{4}\)\.\s*(.+?)(?:\.\s+[A-Z][^.]*)",
        text,
    )

    if match is None:
        return None

    title = match.group(1).strip()

    return title or None
