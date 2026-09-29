"""
Tests for text-based metadata extraction.
"""

from extractor.text_metadata import (
    extract_authors,
    extract_title,
)


def test_extract_single_author():
    text = (
        "Smith, J. (2020). "
        "The impact of writing instruction. "
        "Journal of Writing Research, 12(3), 45-67."
    )

    assert extract_authors(text) == ["Smith, J."]


def test_extract_multiple_authors():
    text = (
        "Smith, J., Brown, A. (2020). "
        "The impact of writing instruction. "
        "Journal of Writing Research."
    )

    assert extract_authors(text) == [
        "Smith, J.",
        "Brown, A.",
    ]


def test_extract_title():
    text = (
        "Smith, J. (2020). "
        "The impact of writing instruction. "
        "Journal of Writing Research, 12(3), 45-67."
    )

    assert extract_title(text) == "The impact of writing instruction"


def test_missing_year_returns_no_authors():
    text = "Smith, J. " "The impact of writing instruction."

    assert extract_authors(text) == []


def test_missing_title_returns_none():
    text = "Smith, J. (2020)."

    assert extract_title(text) is None
