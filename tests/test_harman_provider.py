"""
Tests for HarmanProvider.

Exercises the client→adapter conversion against captured JSON fixtures,
plus the ``supports()`` routing rules. The HTTP layer is replaced with
a mock client, so no network access is performed.
"""

import sys
from pathlib import Path

# Make test_data importable regardless of how pytest is invoked.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from models import Provider, Reference, ReferenceType
from verification.harman_provider import HarmanProvider

from test_data.providers.harman import (
    ARKAN_2026_HIT,
    ARKAN_2026_METADATA_AS_STRING,
    THESIS_HIT,
    UZUN_2016_EMPTY,
)


class _StubClient:
    """Records the query and returns a canned response."""

    def __init__(self, payload):
        self.payload = payload
        self.queries: list[str] = []

    def search(self, query: str) -> dict:
        self.queries.append(query)
        return self.payload


class _RaisingClient:
    def search(self, query: str):
        raise RuntimeError("network down")


def _provider(payload) -> tuple[HarmanProvider, _StubClient]:
    client = _StubClient(payload)
    return HarmanProvider(client=client), client


def _ref(**kwargs) -> Reference:
    defaults = dict(
        raw_text="Arkan, Y. (2026). Methodologische Reflexion.",
        title="Methodologische Reflexion Qualitativer Forschungsansätze",
        authors=["Arkan, Y."],
        year=2026,
    )
    defaults.update(kwargs)
    return Reference(**defaults)


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------


def test_name():
    assert HarmanProvider(client=_StubClient(UZUN_2016_EMPTY)).name == "harman"


def test_arkans_dergipark_article_is_converted():
    provider, _ = _provider(ARKAN_2026_HIT)
    matches = provider.search(_ref())

    assert len(matches) == 1
    match = matches[0]

    assert match.provider == Provider.HARMAN
    assert match.reference_type == ReferenceType.JOURNAL_ARTICLE
    assert match.title == (
        "Methodologische Reflexion Qualitativer Forschungsansätze im "
        "Kommunaldolmetschen: Eine Szenario-gestützte Analyse"
    )
    assert match.authors == ["Yelda Arkan"]
    assert match.year == 2026
    assert match.journal == "Trakya Üniversitesi Sosyal Bilimler Dergisi"
    assert match.publisher == "TR Dizin"
    assert match.url == (
        "https://search.harman.ulakbim.gov.tr/tr/yayin/detay/"
        "tmdhhahs_5qcy1nh81zjd34hk9p5vkn7cn926"
    )
    assert match.record_id == "tmdhhahs_5qcy1nh81zjd34hk9p5vkn7cn926"


def test_metadata_json_string_is_parsed():
    provider, _ = _provider(ARKAN_2026_METADATA_AS_STRING)
    matches = provider.search(_ref())

    assert len(matches) == 1
    match = matches[0]
    assert match.title is not None
    assert match.authors == ["Yelda Arkan"]
    assert match.year == 2026
    assert match.journal == "Trakya Üniversitesi Sosyal Bilimler Dergisi"


def test_thesis_record_maps_to_thesis_type():
    provider, _ = _provider(THESIS_HIT)
    ref = _ref(
        title="İkinci dil olarak Türkçe öğretiminde kültürel unsurların yeri",
        authors=["Yılmaz, A."],
        year=2019,
    )
    matches = provider.search(ref)

    assert len(matches) == 1
    match = matches[0]
    assert match.reference_type == ReferenceType.THESIS
    assert match.publisher == "YÖK Ulusal Tez Merkezi"
    # Theses have no serial source line, so journal stays None.
    assert match.journal is None


def test_empty_hits_returns_empty_list():
    provider, _ = _provider(UZUN_2016_EMPTY)
    matches = provider.search(
        _ref(
            title=(
                "Developing EAP writing skills through "
                "genre-based instruction"
            ),
            year=2016,
        )
    )
    assert matches == []


def test_client_exception_is_swallowed():
    provider = HarmanProvider(client=_RaisingClient())
    assert provider.search(_ref()) == []


# ---------------------------------------------------------------------------
# supports() routing
# ---------------------------------------------------------------------------


def test_supports_returns_true_for_normal_article():
    provider = HarmanProvider(client=_StubClient(UZUN_2016_EMPTY))
    assert provider.supports(_ref()) is True


def test_supports_rejects_pre_1900():
    provider = HarmanProvider(client=_StubClient(UZUN_2016_EMPTY))
    ref = _ref(year=1829)
    assert provider.supports(ref) is False


def test_supports_rejects_reference_without_title():
    provider = HarmanProvider(client=_StubClient(UZUN_2016_EMPTY))
    ref = Reference(
        raw_text="Some reference without a parsed title",
        title=None,
        book_title=None,
        year=2020,
    )
    assert provider.supports(ref) is False


def test_supports_accepts_book_title_without_chapter_title():
    provider = HarmanProvider(client=_StubClient(UZUN_2016_EMPTY))
    ref = Reference(
        raw_text="A book chapter without its own title",
        title=None,
        book_title="The Science of Writing",
        year=1996,
    )
    assert provider.supports(ref) is True


def test_search_uses_title_when_present():
    provider, client = _provider(ARKAN_2026_HIT)
    ref = _ref(title="Explicit Title", book_title="Ignored Book Title")
    provider.search(ref)
    assert client.queries == ["Explicit Title"]


def test_search_falls_back_to_book_title():
    provider, client = _provider(UZUN_2016_EMPTY)
    ref = Reference(
        raw_text="raw",
        title=None,
        book_title="Fallback Book Title",
        year=2020,
    )
    provider.search(ref)
    assert client.queries == ["Fallback Book Title"]