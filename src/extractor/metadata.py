"""
Reference metadata extraction.

Extracts reliable metadata fields from raw reference strings.
"""

from models import Reference

from .patterns import (
    find_doi,
    find_url,
    find_year,
)
from .text_metadata import (
    extract_authors,
    extract_title,
)


def extract_metadata(
    reference: Reference,
) -> Reference:
    """
    Extract metadata from a Reference object.

    Updates the object in place and returns it.

    Args:
        reference:
            Reference containing raw text.

    Returns:
        Updated Reference object.
    """

    text = reference.raw_text

    reference.year = find_year(text)

    reference.doi = find_doi(text)

    reference.url = find_url(text)

    reference.authors = extract_authors(text)

    reference.title = extract_title(text)

    return reference
