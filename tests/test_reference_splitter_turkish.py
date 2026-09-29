"""
Test the reference splitter against a real Turkish musicology manuscript.

Source: 31 paragraphs → 25 references. Six references span two paragraphs
(a citation line followed by a URL or shelf-mark). Three contain pre-1900
years. Two use the Turkish "(t.y.)" no-date marker.
"""

from parser.reference_splitter import split_references

from test_data.turkish_references.reference_splitter import (
    TURKISH_MUSIC_2025_PARAGRAPHS,
    TURKISH_MUSIC_2025_EXPECTED,
)


def test_turkish_music_manuscript_count():
    result = split_references(TURKISH_MUSIC_2025_PARAGRAPHS)
    assert len(result) == len(TURKISH_MUSIC_2025_EXPECTED), (
        f"Splitter returned {len(result)} entries, "
        f"expected {len(TURKISH_MUSIC_2025_EXPECTED)}"
    )


def test_turkish_music_manuscript_contents():
    result = split_references(TURKISH_MUSIC_2025_PARAGRAPHS)

    for i, expected in enumerate(TURKISH_MUSIC_2025_EXPECTED):
        if i >= len(result):
            raise AssertionError(
                f"Missing entry {i}: expected {expected!r}"
            )
        assert result[i] == expected, (
            f"Entry {i} differs:\n"
            f"  got:      {result[i]!r}\n"
            f"  expected: {expected!r}"
        )