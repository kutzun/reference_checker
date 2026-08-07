"""
Tests for reference metadata patterns.
"""

from extractor.patterns import (
    find_doi,
    find_orcid,
    find_url,
    find_year,
)


def test_find_year():
    assert find_year("Smith, J. (2020). Example article.") == 2020

    assert find_year("No publication date available.") is None


def test_find_doi():
    assert find_doi("https://doi.org/10.1234/example.doi") == "10.1234/example.doi"

    assert find_doi("No DOI here.") is None


def test_find_url():
    assert (
        find_url("Available at https://example.com/article")
        == "https://example.com/article"
    )

    assert find_url("No URL") is None


def test_find_orcid():
    assert find_orcid("Author ORCID: 0000-0002-1825-0097") == "0000-0002-1825-0097"

    assert find_orcid("No identifier") is None
