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
    assert find_year("Smith, J. (2020). Example article.") == "2020"


def test_find_year_with_suffix():
    assert find_year("Smith, J. (2019b). Example article.") == "2019b"


def test_find_year_missing():
    assert find_year("No year here.") is None


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

def test_find_url_strips_trailing_period():
    text = "See https://example.com/page. More text follows."
    assert find_url(text) == "https://example.com/page"


def test_find_url_strips_trailing_comma():
    text = "See https://example.com/page, then something."
    assert find_url(text) == "https://example.com/page"


def test_find_url_keeps_balanced_parens():
    text = (
        "See https://imslp.org/wiki/Sonata_in_D_minor_(Speer%2C_Daniel). "
        "More text."
    )
    assert find_url(text) == (
        "https://imslp.org/wiki/Sonata_in_D_minor_(Speer%2C_Daniel)"
    )


def test_find_url_strips_unbalanced_paren():
    text = "See https://example.com/foo). More text."
    assert find_url(text) == "https://example.com/foo"
