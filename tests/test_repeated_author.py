"""
Tests for repeated-author markers (———, ---, ------, –––).

Each sequence is a consecutive run from a bibliography. The parser
should resolve the marker in every entry after the first by copying
the previous entry's first author.
"""

import pytest

from internal_check.normalizer import normalize_author_name
from parser.reference_parser import ReferenceParser

from test_data.turkish_references.repeated_author import SEQUENCES


@pytest.mark.parametrize(
    "seq",
    SEQUENCES,
    ids=[s[0] for s in SEQUENCES],
)
def test_repeated_author_marker(seq):
    seq_id, raw_entries, expected_authors = seq

    parser = ReferenceParser()
    refs = parser.parse(raw_entries)

    assert len(refs) == len(expected_authors), (
        f"[{seq_id}] parser returned {len(refs)} refs, "
        f"expected {len(expected_authors)}"
    )

    for i, (ref, exp) in enumerate(zip(refs, expected_authors)):
        got = normalize_author_name(ref.authors[0]) if ref.authors else ""
        assert got == exp, (
            f"[{seq_id}] entry {i}: got {got!r}, expected {exp!r} "
            f"(raw: {ref.raw_text[:60]!r})"
        )