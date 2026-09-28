"""
Regular expression patterns used for reference metadata extraction.
"""

import re

# Four-digit publication year (1900-2099), optional single-letter suffix
# for disambiguating same-author-same-year references ("2019a", "2019b").
# The trailing \b prevents "2019belge" from matching as "2019b".
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}[a-z]?\b", re.IGNORECASE)


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


def find_year(text: str) -> str | None:
    """
    Extract the first plausible publication year.

    Returns the year as a string so that single-letter disambiguation
    suffixes are preserved ("2019a", "2019b"). For references without
    a suffix, this is still a four-digit string like "2019".

    Args:
        text:
            Raw reference text.

    Returns:
        Year string (optionally suffixed) or None.
    """

    match = YEAR_PATTERN.search(text)

    if match is None:
        return None

    return match.group()


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
