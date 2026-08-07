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

    reference.year = find_year(reference.raw_text)

    reference.doi = find_doi(reference.raw_text)

    reference.url = find_url(reference.raw_text)

    return reference
