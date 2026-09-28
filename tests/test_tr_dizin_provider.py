"""
Tests for TrDizinProvider.

TrDizinProvider queries the TR Dizin search API and converts returned
records into ReferenceMatch objects. Tests inject a fake client so no
HTTP request is made.
"""

from models import Reference
from models.enums import Provider, ReferenceType
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