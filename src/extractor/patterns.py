"""
Regular expression patterns used for reference metadata extraction.
"""

import re

# Four-digit publication year (1900-2099)
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


# DOI pattern following common DOI formats
DOI_PATTERN = re.compile(
    r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b",
    re.IGNORECASE,
)


# URL pattern for web references
URL_PATTERN = re.compile(
    r"https?://[^\s<>]+",
    re.IGNORECASE,
)


# ORCID identifier pattern
ORCID_PATTERN = re.compile(
    r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b",
    re.IGNORECASE,
)


def find_year(text: str) -> int | None:
    """
    Extract the first plausible publication year.

    Args:
        text:
            Raw reference text.

    Returns:
        Four-digit year or None.
    """

    match = YEAR_PATTERN.search(text)

    if match is None:
        return None

    return int(match.group())


def find_doi(text: str) -> str | None:
    """
    Extract DOI from reference text.

    Args:
        text:
            Raw reference text.

    Returns:
        DOI string or None.
    """

    match = DOI_PATTERN.search(text)

    if match is None:
        return None

    return match.group().rstrip(".,;)")


def find_url(text: str) -> str | None:
    """
    Extract first URL from reference text.

    Args:
        text:
            Raw reference text.

    Returns:
        URL string or None.
    """

    match = URL_PATTERN.search(text)

    if match is None:
        return None

    return match.group()


def find_orcid(text: str) -> str | None:
    """
    Extract ORCID identifier.

    Args:
        text:
            Raw reference text.

    Returns:
        ORCID string or None.
    """

    match = ORCID_PATTERN.search(text)

    if match is None:
        return None

    return match.group()
