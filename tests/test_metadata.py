"""
Tests for reference metadata extraction.
"""

from extractor.metadata import extract_metadata
from models import Reference


def test_extract_year():
    reference = Reference(raw_text=("Smith, J. (2020). " "Example article."))

    result = extract_metadata(reference)

    assert result.year == 2020


def test_extract_doi():
    reference = Reference(
        raw_text=(
            "Smith, J. (2020). "
            "Example article. "
            "https://doi.org/10.1234/example.doi"
        )
    )

    result = extract_metadata(reference)

    assert result.doi == "10.1234/example.doi"


def test_extract_url():
    reference = Reference(raw_text=("Available at " "https://example.com/article"))

    result = extract_metadata(reference)

    assert result.url == "https://example.com/article"


def test_extract_multiple_metadata_fields():
    reference = Reference(
        raw_text=(
            "Smith, J. (2022). "
            "Example article. "
            "https://doi.org/10.5678/test "
            "https://example.com"
        )
    )

    result = extract_metadata(reference)

    assert result.year == 2022
    assert result.doi == "10.5678/test"
    assert result.url == "https://doi.org/10.5678/test"


def test_missing_metadata():
    reference = Reference(raw_text="Smith, J. Example article.")

    result = extract_metadata(reference)

    assert result.year is None
    assert result.doi is None
    assert result.url is None


def test_extract_authors_and_title():
    reference = Reference(
        raw_text=(
            "Smith, J. (2020). "
            "The impact of writing instruction. "
            "Journal of Writing Research."
        )
    )

    result = extract_metadata(reference)

    assert result.authors == ["Smith, J."]

    assert result.title == "The impact of writing instruction"
