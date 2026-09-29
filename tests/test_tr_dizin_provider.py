"""
Tests for TrDizinProvider.

TrDizinProvider queries the TR Dizin search API and converts returned
records into ReferenceMatch objects. Tests inject a fake client so no
HTTP request is made.
"""

from models import Reference
from models.enums import Provider, ReferenceType
from models import Reference as _Ref  # (already imported as Reference)
from verification.tr_dizin_provider import TrDizinProvider

from test_data.providers.tr_dizin import MASAL_AI, MASAL_PROPP


class FakeTrDizinClient:
    """
    Returns a canned list of raw _source dicts for any query.
    """

    def __init__(self, sources):
        self.sources = sources

    def search(self, query: str):
        return self.sources


def test_tr_dizin_provider_converts_record_with_doi():
    reference = Reference(
        raw_text="Perk, D. (2019). Masal Uyarlamalarının ...",
        title=(
            "Masal Uyarlamalarının Vladimir Propp'un Yaklaşımı ile "
            "İncelenmesi “Pamuk Prenses” Masalı Örneği*"
        ),
    )

    provider = TrDizinProvider(
        client=FakeTrDizinClient([MASAL_PROPP]),
    )

    matches = provider.search(reference)

    assert len(matches) == 1
    match = matches[0]

    assert match.provider == Provider.TR_DIZIN
    assert match.reference_type == ReferenceType.JOURNAL_ARTICLE
    assert match.title == (
        "Masal Uyarlamalarının Vladimir Propp'un Yaklaşımı ile "
        "İncelenmesi “Pamuk Prenses” Masalı Örneği*"
    )
    assert match.authors == ["Derya Perk"]
    assert match.journal == "Hacettepe Üniversitesi Edebiyat Fakültesi Dergisi"
    assert match.year == 2019
    assert match.doi == "10.32600/huefd.454263"


def test_tr_dizin_provider_prefers_turkish_title():
    """
    When both a Turkish and an English abstract exist, the Turkish
    title is used. orderTitle is ignored (it has spaces removed).
    """
    reference = Reference(
        raw_text="Ilıcak, N. G. & Çinko, K. (2021). Yapay zekânın ...",
        title="YAPAY ZEKÂNIN YARATTIĞI MASAL: PRENSES İLE TİLKİ",
    )

    provider = TrDizinProvider(
        client=FakeTrDizinClient([MASAL_AI]),
    )

    matches = provider.search(reference)

    assert len(matches) == 1
    match = matches[0]

    assert match.title == "YAPAY ZEKÂNIN YARATTIĞI MASAL: PRENSES İLE TİLKİ"
    assert match.year == 2021
    assert match.doi is None
    assert match.journal == (
        "Uluslararası Türkçe Edebiyat Kültür Eğitim (TEKE) Dergisi"
    )
    assert match.authors == ["N. Gamze Ilıcak", "KEMAL ÇİNKO"]


def test_tr_dizin_provider_returns_empty_for_no_results():
    reference = Reference(
        raw_text="Nonexistent reference.",
        title="This does not exist anywhere",
    )

    provider = TrDizinProvider(
        client=FakeTrDizinClient([]),
    )

    matches = provider.search(reference)

    assert matches == []

# --- supports() ---------------------------------------------------------

def test_supports_skips_pre_1900_reference():
    """TR Dizin holds nothing from before the twentieth century, so
    an 1829 German journal should never be queried against it."""
    ref = Reference(
        raw_text="Allgemeiner Musikalischer Anzeiger. Leipzig 1829.",
        year=1829,
    )
    assert TrDizinProvider().supports(ref) is False


def test_supports_skips_clearly_non_turkish_reference():
    ref = Reference(
        raw_text=(
            "Berliner allgemeine musikalische Zeitung, (AmZ), "
            "(30). 301-316."
        ),
    )
    assert TrDizinProvider().supports(ref) is False


def test_supports_accepts_turkish_book():
    ref = Reference(
        raw_text="Tanyeli, U. (2017). Yıkarak yapmak. Metis Yayınları.",
        year=2017,
    )
    assert TrDizinProvider().supports(ref) is True


def test_supports_accepts_turkish_article():
    ref = Reference(
        raw_text=(
            "Kaçar, G. Y. (2008). Türk Mûsikîsinde Makam. "
            "İstem, 6(11), 145-158."
        ),
        year=2008,
    )
    assert TrDizinProvider().supports(ref) is True


def test_supports_accepts_modern_reference_without_year():
    """If the year is unknown we cannot rule the reference out."""
    ref = Reference(
        raw_text=(
            "Yılmaz, A. Osmanlı tarihi üzerine notlar. "
            "İstanbul Üniversitesi."
        ),
    )
    assert TrDizinProvider().supports(ref) is True


def test_supports_accepts_diacritic_stripped_turkish_title():
    """Function words carry the language signal when diacritics are
    absent. Without this, a Turkish book whose title was typed in
    plain ASCII would be skipped."""
    ref = Reference(
        raw_text="Yikarak yapmak ve mimarlik eyleminin modernligi. Metis.",
    )
    assert TrDizinProvider().supports(ref) is True