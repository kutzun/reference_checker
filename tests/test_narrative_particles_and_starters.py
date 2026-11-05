"""
Regression tests for narrative citation extraction.

Two narrative forms fail on current code:

  1. Surname with a lowercase particle, common in Dutch, German,
     Romance, and Arabic-transliterated names: "de Bot (2008)". The
     lookback walk stops at the lowercase "de" and collects only
     "Bot", producing key "bot:2008" against a reference key of
     "de bot:2008".

  2. Surname preceded by a capitalized clause-starter: "Following
     Guastello (2002)". The walk collects the starter word as if it
     were part of the author phrase, producing "Following Guastello"
     and key "following guastello:2002" against "guastello:2002".

Both symptoms appear in a real manuscript as a MISSING citation
paired with an UNCITED reference for the same work.
"""

from models import Reference

from internal_check.models import CitationKind
from internal_check.profiles import ENGLISH
from internal_check.service import InternalCheckService


def _ref(raw: str, authors: list[str], year: int) -> Reference:
    return Reference(raw_text=raw, authors=authors, year=year)


def _narrative(result):
    return [c for c in result.citations if c.kind == CitationKind.NARRATIVE]


# ---------------------------------------------------------------------------
# Case 1 — lowercase particles
# ---------------------------------------------------------------------------

def test_particle_surname_de_bot():
    body = (
        "Pioneered by Larsen-Freeman (1997) and de Bot (2008), CDST "
        "shifts applied linguistics from static competence to emergent "
        "development."
    )
    refs = [
        _ref(
            "Larsen-Freeman, D. (1997). Chaos/complexity science and "
            "second language acquisition. Applied Linguistics, 18(2), 141-165.",
            ["Larsen-Freeman", "D."],
            1997,
        ),
        _ref(
            "de Bot, K. (2008). Introduction: Second Language Development "
            "as a Dynamic Process. The Modern Language Journal, 92(2), 166-178.",
            ["de Bot", "K."],
            2008,
        ),
    ]

    service = InternalCheckService(profile=ENGLISH)
    result = service.check_text(body, refs)

    narratives = _narrative(result)
    assert len(narratives) == 2, (
        f"expected two narrative citations, got {len(narratives)}: "
        f"{[(c.raw, c.authors) for c in narratives]!r}"
    )
    author_lists = [c.authors for c in narratives]
    assert ["Larsen-Freeman"] in author_lists
    assert ["de Bot"] in author_lists

    assert result.missing_references() == []
    assert result.uncited_references() == []


def test_particle_surname_van_der_berg_narrative():
    body = "A classic result was reported by van der Berg (2020)."
    refs = [
        _ref(
            "van der Berg, P. (2020). Some title. Publisher.",
            ["van der Berg", "P."],
            2020,
        ),
    ]

    service = InternalCheckService(profile=ENGLISH)
    result = service.check_text(body, refs)

    assert result.missing_references() == []
    assert result.uncited_references() == []


# ---------------------------------------------------------------------------
# Case 2 — capitalized clause-starter before the surname
# ---------------------------------------------------------------------------

def test_clause_starter_following():
    body = (
        "The Cusp Catastrophe Model identified potential performance "
        "shifts. Following Guastello (2002), the formula determines "
        "this structure."
    )
    refs = [
        _ref(
            "Guastello, S. J. (2002). Managing emergent phenomena: "
            "Nonlinear dynamics in work organizations. Lawrence Erlbaum.",
            ["Guastello", "S. J."],
            2002,
        ),
    ]

    service = InternalCheckService(profile=ENGLISH)
    result = service.check_text(body, refs)

    narratives = _narrative(result)
    assert len(narratives) == 1, (
        f"expected one narrative citation, got {len(narratives)}: "
        f"{[(c.raw, c.authors) for c in narratives]!r}"
    )
    assert narratives[0].authors == ["Guastello"], (
        f"expected authors ['Guastello'], got {narratives[0].authors!r}"
    )

    assert result.missing_references() == []
    assert result.uncited_references() == []


# ---------------------------------------------------------------------------
# Contract guards — existing forms must still work.
# ---------------------------------------------------------------------------

def test_multi_author_and_still_works():
    body = "Smith and Jones (2020) argued that the effect is robust."
    refs = [
        _ref(
            "Smith, J., & Jones, B. (2020). Some title. Journal.",
            ["Smith", "Jones"],
            2020,
        ),
    ]
    service = InternalCheckService(profile=ENGLISH)
    result = service.check_text(body, refs)
    assert result.missing_references() == []
    assert result.uncited_references() == []


def test_et_al_still_works():
    body = "Smith et al. (2020) reported a strong correlation."
    refs = [
        _ref(
            "Smith, J., Brown, C., & Davis, E. (2020). Title. Journal.",
            ["Smith", "Brown", "Davis"],
            2020,
        ),
    ]
    service = InternalCheckService(profile=ENGLISH)
    result = service.check_text(body, refs)
    assert result.missing_references() == []
    assert result.uncited_references() == []