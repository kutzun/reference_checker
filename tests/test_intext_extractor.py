"""
Tests for in-text citation extraction.
"""

from internal_check.intext_extractor import InTextExtractor
from internal_check.models import CitationKind
from internal_check.profiles import ENGLISH, GENERIC, TURKISH


# ---------------------------------------------------------------------------
# English: parenthetical
# ---------------------------------------------------------------------------

def test_parenthetical_single_author():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["The effect was clear (Smith, 2020)."])
    assert len(cites) == 1
    c = cites[0]
    assert c.kind == CitationKind.PARENTHETICAL
    assert c.authors == ["Smith"]
    assert c.year == 2020
    assert c.year_suffix is None


def test_parenthetical_multiple_semicolons():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["(Smith, 2020; Jones, 2019)"])
    assert len(cites) == 2
    assert cites[0].authors == ["Smith"]
    assert cites[0].year == 2020
    assert cites[1].authors == ["Jones"]
    assert cites[1].year == 2019


def test_parenthetical_and():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["(Smith and Jones, 2020)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Smith", "Jones"]


def test_parenthetical_ampersand():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["(Smith & Jones, 2020)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Smith", "Jones"]


def test_parenthetical_et_al():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["(Smith et al., 2020)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Smith"]


def test_year_suffix():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["(Smith, 2020a)"])
    assert len(cites) == 1
    assert cites[0].year == 2020
    assert cites[0].year_suffix == "a"


# ---------------------------------------------------------------------------
# English: narrative
# ---------------------------------------------------------------------------

def test_narrative_according_to():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["According to Smith (2020), this is true."])
    assert len(cites) == 1
    c = cites[0]
    assert c.kind == CitationKind.NARRATIVE
    assert c.authors == ["Smith"]
    assert c.year == 2020


def test_narrative_author_verb():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["Smith (2020) argues this."])
    assert len(cites) == 1
    assert cites[0].kind == CitationKind.NARRATIVE
    assert cites[0].authors == ["Smith"]


def test_narrative_with_page_locator():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["Smith (2020, p. 45) reports this."])
    assert len(cites) == 1
    assert cites[0].kind == CitationKind.NARRATIVE
    assert cites[0].authors == ["Smith"]
    assert cites[0].year == 2020


# ---------------------------------------------------------------------------
# Numeric
# ---------------------------------------------------------------------------

def test_numeric_single():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["See [1]."])
    assert len(cites) == 1
    assert cites[0].kind == CitationKind.NUMERIC
    assert cites[0].numbers == [1]


def test_numeric_range():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["[1-3]"])
    assert len(cites) == 1
    assert cites[0].numbers == [1, 2, 3]


def test_numeric_list_with_range():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["[1,3-5]"])
    assert len(cites) == 1
    assert cites[0].numbers == [1, 3, 4, 5]


def test_numeric_multiple_brackets():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["Numbered style [1-3] and [5]."])
    assert len(cites) == 2
    assert cites[0].numbers == [1, 2, 3]
    assert cites[1].numbers == [5]


def test_numeric_rejects_year():
    """A bare 4-digit year in brackets is not a numeric citation."""
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["[2020]"])
    assert cites == []


# ---------------------------------------------------------------------------
# Noise filter integration
# ---------------------------------------------------------------------------

def test_statistical_expression_is_ignored():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["The mean was 3.4 (M = 2.985; SD = 1.0345)."])
    assert cites == []


def test_mixed_statistic_and_citation():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["(Smith, 2020; M = 2.985)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Smith"]


# ---------------------------------------------------------------------------
# Turkish
# ---------------------------------------------------------------------------

def test_turkish_parenthetical():
    ex = InTextExtractor(TURKISH)
    cites = ex.extract(["Sonuçlar açıktır (Yılmaz, 2020)."])
    assert len(cites) == 1
    assert cites[0].authors == ["Yılmaz"]
    assert cites[0].year == 2020


def test_turkish_narrative():
    ex = InTextExtractor(TURKISH)
    cites = ex.extract(["Yılmaz (2020) bunu savunmuştur."])
    assert len(cites) == 1
    assert cites[0].authors == ["Yılmaz"]


def test_turkish_narrative_with_leading_marker():
    ex = InTextExtractor(TURKISH)
    cites = ex.extract(["Bkz. Yılmaz (2020)."])
    assert len(cites) == 1
    assert cites[0].authors == ["Yılmaz"]


def test_turkish_conjunction():
    ex = InTextExtractor(TURKISH)
    cites = ex.extract(["(Yılmaz ve Kaya, 2020)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Yılmaz", "Kaya"]


def test_turkish_et_al():
    ex = InTextExtractor(TURKISH)
    cites = ex.extract(["(Yılmaz vd., 2020)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Yılmaz"]


# ---------------------------------------------------------------------------
# Unparsed tracking and locations
# ---------------------------------------------------------------------------

def test_unparsed_is_tracked():
    ex = InTextExtractor(ENGLISH)
    ex.extract(["(some random parenthetical)"])
    assert len(ex.unparsed) == 1


def test_location_is_recorded():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["First paragraph.", "(Smith, 2020)"])
    assert len(cites) == 1
    assert cites[0].location == "paragraph 2"


def test_generic_profile_still_extracts_parenthetical():
    ex = InTextExtractor(GENERIC)
    cites = ex.extract(["(Smith, 2020)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Smith"]

def test_eg_prefix_is_stripped():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["(e.g. Kyle & Crossley, 2018)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Kyle", "Crossley"]
    assert cites[0].year == 2018


def test_ie_prefix_is_stripped():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["(i.e. Smith, 2020)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Smith"]


def test_also_prefix_is_stripped():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["(also Smith, 2020)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Smith"]


def test_but_see_prefix_is_stripped():
    ex = InTextExtractor(ENGLISH)
    cites = ex.extract(["(but see Smith, 2020)"])
    assert len(cites) == 1
    assert cites[0].authors == ["Smith"]