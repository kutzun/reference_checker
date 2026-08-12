"""
Reference entry splitting.

Separates a reference section into individual reference entries.
Only strings that look like bibliographic references (containing a year)
are kept.
"""

import re


def split_references(
    paragraphs: list[str],
) -> list[str]:
    """
    Split reference section paragraphs into entries.

    Each paragraph is cleaned and then tested with a generic filter.
    Only paragraphs that contain a plausible publication year (or an
    in‑press / forthcoming marker) are kept.

    Args:
        paragraphs: Reference section paragraphs.

    Returns:
        List of individual reference strings.
    """

    references = []

    for paragraph in paragraphs:
        cleaned = clean_reference(paragraph)

        if cleaned and _is_likely_reference(cleaned):
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
        text: Raw reference text.

    Returns:
        Cleaned reference.
    """

    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _is_likely_reference(text: str) -> bool:
    """
    Return True if *text* looks like a bibliographic reference.

    The test is deliberately generic and does not depend on citation style.
    It requires:

    - A minimum length (30 characters).
    - A four‑digit year (19xx or 20xx) anywhere in the text, **or** one of
      the common “no year yet” markers (“in press”, “forthcoming”).
    - The line must not start with a typical appendix / figure / table heading.
    """
    # Minimum length – genuine references are rarely shorter
    if len(text) < 30:
        return False

    # Look for a four‑digit year or an in‑press marker
    has_year = bool(re.search(r'\b(?:19|20)\d{2}\b', text))
    has_no_year_marker = bool(
        re.search(r'\b(?:in press|forthcoming)\b', text, re.IGNORECASE)
    )
    if not (has_year or has_no_year_marker):
        return False

    # Exclude lines that start with typical appendix / figure / table headings
    if re.match(
        r'^\s*(?:Figure|Table|Appendix|Source\s+data)\b',
        text,
        re.IGNORECASE,
    ):
        return False

    return True