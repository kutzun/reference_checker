"""
Tests for mononym (single-name) authors in multi-author references.

Some authors — Indonesian, Javanese, and many historical figures — use
a single name with no surname/given-name split. In an APA reference
this appears as e.g. ``Rosmawati, & Lowie, W. (2024). ...``, where the
comma before ``&`` is the Oxford comma and the ``&`` separates two
authors whose first is a mononym.

On the previous parser, normalization turned ``&`` into ``,`` and the
whole string collapsed into ``Rosmawati, L.`` (one author with a
fabricated initial), losing the second author entirely.
"""

from extractor.text_metadata import extract_authors


def test_mononym_with_ampersand_comma():
    """The exact form from a real manuscript: comma before &."""
    text = (
        "Rosmawati, & Lowie, W. (2024). Using a multifractal analysis "
        "approach to explore (multi)fractality in L2 writing in English. "
        "In W. Lowie, Rosmawati, & V. de Wilde (Eds.), Research methods "
        "in complex dynamic systems theory approaches to second language "
        "development (pp. 191-215). John Benjamins."
    )
    authors = extract_authors(text)
    assert authors == ["Rosmawati", "Lowie, W."], (
        f"expected two authors, got {authors!r}"
    )


def test_mononym_with_ampersand_no_comma():
    text = "Rosmawati & Lowie, W. (2024). Some article."
    assert extract_authors(text) == ["Rosmawati", "Lowie, W."]


def test_mononym_with_and():
    text = "Rosmawati and Lowie, W. (2024). Some article."
    assert extract_authors(text) == ["Rosmawati", "Lowie, W."]


def test_mononym_alone():
    text = "Rosmawati (2024). Some article."
    assert extract_authors(text) == ["Rosmawati"]


# ---------------------------------------------------------------------------
# Contract guards — behaviour must not change for standard forms.
# ---------------------------------------------------------------------------

def test_initialed_authors_with_ampersand_unchanged():
    text = "Kyle, K., & Crossley, S. A. (2018). Some article."
    assert extract_authors(text) == ["Kyle, K.", "Crossley, S. A."]


def test_initialed_authors_with_and_unchanged():
    text = "Smith, J. and Jones, A. (2020). Some article."
    assert extract_authors(text) == ["Smith, J.", "Jones, A."]


def test_comma_separated_authors_unchanged():
    text = "Smith, J., Brown, A. (2020). Some article."
    assert extract_authors(text) == ["Smith, J.", "Brown, A."]


def test_dutch_particles_unchanged():
    text = "van der Klis, M. & Tellings, J. (2022). Some article."
    assert extract_authors(text) == ["van der Klis, M.", "Tellings, J."]