"""
Tests for internal-check author name normalization.

Turkish in-text citations commonly write "Anadol R." (surname followed
by initial, no comma), while the reference list writes "Anadol, R."
(surname, comma, initial). Both must reduce to the same key, or every
such citation is reported as MISSING and every such reference as
UNCITED.

The normalizer currently drops the initial only when a comma separates
it from the surname. When there is no comma, the initial survives and
the keys diverge.
"""

from internal_check.normalizer import normalize_author_name


# ---------------------------------------------------------------------------
# Turkish in-text style: surname followed by initial, no comma
# ---------------------------------------------------------------------------

def test_trailing_initial_matches_comma_form():
    assert (
        normalize_author_name("Anadol R.")
        == normalize_author_name("Anadol, R.")
    )


def test_trailing_initial_reduces_to_surname():
    assert normalize_author_name("Anadol R.") == "anadol"


def test_multiple_trailing_initials():
    assert normalize_author_name("Murray J. H.") == "murray"


def test_turkish_surname_with_trailing_initial():
    assert normalize_author_name("Yıldırım Ş.") == "yildirim"


# ---------------------------------------------------------------------------
# Contract guards
# ---------------------------------------------------------------------------

def test_particle_surname_preserved():
    """Lowercase particles are not initials and must be kept."""
    assert normalize_author_name("de Bot") == "de bot"


def test_multi_word_surname_preserved():
    assert normalize_author_name("van der Berg") == "van der berg"


def test_comma_form_unchanged():
    assert normalize_author_name("Smith, J.") == "smith"


def test_plain_surname_unchanged():
    assert normalize_author_name("Guastello") == "guastello"