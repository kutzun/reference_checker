"""
Tests for author similarity.
"""

from verification.authors import (
    author_similarity,
)


def test_same_authors():

    score = author_similarity(
        [
            "Smith, John",
        ],
        [
            "Smith, John",
        ],
    )

    assert score == 1.0


def test_partial_author_match():

    score = author_similarity(
        [
            "Smith, John",
            "Brown, Alice",
        ],
        [
            "Smith, John",
        ],
    )

    assert score == 0.5

def test_surname_containing_and_is_not_split():
    """Chandler must not be split on the 'and' inside it."""
    from extractor.text_metadata import extract_authors
    text = "Chandler, J. (2003). The efficacy of various kinds of error feedback."
    assert extract_authors(text) == ["Chandler, J."]


def test_surname_anderson_is_not_split():
    from extractor.text_metadata import extract_authors
    text = "Anderson, J. (2003). Some article."
    assert extract_authors(text) == ["Anderson, J."]


def test_and_conjunction_still_works():
    from extractor.text_metadata import extract_authors
    text = "Smith, J. and Jones, A. (2020). Some article."
    authors = extract_authors(text)
    assert "Smith, J." in authors
    assert "Jones, A." in authors


def test_ampersand_conjunction_still_works():
    from extractor.text_metadata import extract_authors
    text = "Kyle, K., & Crossley, S. A. (2018). Some article."
    authors = extract_authors(text)
    assert "Kyle, K." in authors
    assert "Crossley, S. A." in authors

def test_dutch_particle_van_der():
    from extractor.text_metadata import extract_authors
    text = "van der Klis, M. & Tellings, J. (2022). Generating semantic maps."
    authors = extract_authors(text)
    assert "van der Klis, M." in authors
    assert "Tellings, J." in authors


def test_dutch_particle_van():
    from extractor.text_metadata import extract_authors
    text = "van Dyke, S. (2020). Some article."
    assert extract_authors(text) == ["van Dyke, S."]


def test_german_particle_von():
    from extractor.text_metadata import extract_authors
    text = "von Neumann, J. (1945). Some article."
    assert extract_authors(text) == ["von Neumann, J."]


def test_french_particle_de():
    from extractor.text_metadata import extract_authors
    text = "de la Cruz, J. (2010). Some article."
    assert extract_authors(text) == ["de la Cruz, J."]


def test_uppercase_de_still_works():
    """De Vita (capital D) should still parse correctly."""
    from extractor.text_metadata import extract_authors
    text = "De Vita, F., Schmidt, S. (2021). Some article."
    authors = extract_authors(text)
    assert "De Vita, F." in authors
    assert "Schmidt, S." in authors