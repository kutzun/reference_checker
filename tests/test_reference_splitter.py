"""
Tests for reference splitting.
"""

from parser.reference_splitter import (
    clean_reference,
    split_references,
)


def test_clean_reference():
    assert (
        clean_reference("  Smith, J. (2020).   Example article.  ")
        == "Smith, J. (2020). Example article."
    )


def test_split_single_line_references():
    paragraphs = [
        "Smith, J. (2020). Example article.",
        "Jones, A. (2021). Another article.",
        "Brown, P. (2022). Third article.",
    ]

    assert split_references(paragraphs) == [
        "Smith, J. (2020). Example article.",
        "Jones, A. (2021). Another article.",
        "Brown, P. (2022). Third article.",
    ]


def test_split_removes_empty_entries():
    paragraphs = [
        "Smith, J. (2020). Example article.",
        "",
        "   ",
        "Jones, A. (2021). Another article.",
    ]

    assert split_references(paragraphs) == [
        "Smith, J. (2020). Example article.",
        "Jones, A. (2021). Another article.",
    ]


def test_split_empty_input():
    assert split_references([]) == []
