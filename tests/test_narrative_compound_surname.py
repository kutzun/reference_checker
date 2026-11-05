"""Regression: narrative walk captures compound surnames."""

from internal_check.intext_extractor import InTextExtractor
from internal_check.profiles import TURKISH


def _authors(paragraph: str) -> list[list[str]]:
    extractor = InTextExtractor(profile=TURKISH)
    return [c.authors for c in extractor.extract([paragraph]) if c.authors]


def test_compound_surname_before_paren():
    # Öztürk Pat is one compound surname, not "Öztürk" + "Pat".
    text = (
        "Kardaş (2018), Öztürk Pat (2017), Uysal (2014) tezlerinde "
        "bulunmuştur."
    )
    results = _authors(text)
    flat = [" ".join(a) for a in results]
    assert "Öztürk Pat" in flat
    assert "Pat" not in flat


def test_compound_surname_after_ampersand():
    text = "Altıner & Sancı Uzun (2024) bu konuda öncüdür."
    results = _authors(text)
    assert ["Altıner", "Sancı Uzun"] in results


def test_compound_surname_before_ampersand():
    text = "Öztürk Pat & Yılmaz (2021) aynı sonuca ulaşmıştır."
    results = _authors(text)
    assert ["Öztürk Pat", "Yılmaz"] in results


def test_sentence_starting_as_not_swallowed():
    # "As" precedes the surname but is a sentence starter, not part of
    # a compound surname.
    text = "... previous sentence ends. As Brown (2019) argued."
    results = _authors(text)
    flat = [" ".join(a) for a in results]
    assert "Brown" in flat
    assert "As Brown" not in flat


def test_see_marker_not_swallowed():
    text = "... previous sentence ends. See Brown (2019) for details."
    results = _authors(text)
    flat = [" ".join(a) for a in results]
    assert "Brown" in flat
    assert "See Brown" not in flat


def test_single_surname_unchanged():
    # Plain single-word surname stays intact.
    text = "Kollmuss ve Agyeman (2002) çevre okuryazarlığı üzerine."
    results = _authors(text)
    assert ["Kollmuss", "Agyeman"] in results