"""
Tests for reference section detection.
"""

from parser.reference_section import (
    find_reference_end,
    find_reference_start,
    is_end_section_heading,
    is_reference_heading,
    normalize_heading,
)


def test_normalize_heading():
    assert normalize_heading("References:") == "references"
    assert normalize_heading("  KAYNAKÇA  ") == "kaynakça"


def test_reference_heading_detection():
    assert is_reference_heading("References")
    assert is_reference_heading("Bibliography")
    assert is_reference_heading("Kaynakça")
    assert is_reference_heading("Literaturverzeichnis")

    assert not is_reference_heading("Introduction")
    assert not is_reference_heading("Previous Studies")


def test_end_section_heading_detection():
    assert is_end_section_heading("Appendix")
    assert is_end_section_heading("Supplementary Material")
    assert is_end_section_heading("Ekler")
    assert is_end_section_heading("Anhang")

    assert not is_end_section_heading("References")
    assert not is_end_section_heading("Results")


def test_find_reference_start():
    paragraphs = [
        "Introduction",
        "Method",
        "Results",
        "References",
        "Smith, J. (2020). Example.",
    ]

    assert find_reference_start(paragraphs) == 3


def test_find_reference_end():
    paragraphs = [
        "Introduction",
        "References",
        "Smith, J. (2020). Example.",
        "Jones, A. (2021). Example.",
        "Appendix",
        "Additional information.",
    ]

    assert (
        find_reference_end(
            paragraphs,
            1,
        )
        == 4
    )


def test_reference_without_following_section():
    paragraphs = [
        "Introduction",
        "References",
        "Smith, J. (2020). Example.",
    ]

    assert (
        find_reference_end(
            paragraphs,
            1,
        )
        is None
    )


def test_missing_reference_section():
    paragraphs = [
        "Introduction",
        "Method",
        "Results",
    ]

    assert find_reference_start(paragraphs) is None
