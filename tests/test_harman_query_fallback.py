"""
Regression tests for Harman query fallback.

Exposed by 44.docx / Keskin (2009): the full thesis title
("İzmir Bölgesi Maden İşçiliği: Başlangıcından MÖ III. Binyıl
Sonuna Kadar Madeni Eser Üretimi ve Ticareti") returned zero hits
from Harman, while the subtitle head ("İzmir Bölgesi Maden
İşçiliği") returned the correct record. The provider now falls
back to shorter query variants when the full title returns no hits.
"""

from __future__ import annotations

from models import Reference
from verification.harman_provider import HarmanProvider


KESKIN_TITLE = (
    "İzmir Bölgesi Maden İşçiliği: Başlangıcından MÖ III. Binyıl "
    "Sonuna Kadar Madeni Eser Üretimi ve Ticareti"
)
KESKIN_HEAD = "İzmir Bölgesi Maden İşçiliği"
KESKIN_PREFIX_10 = (
    "İzmir Bölgesi Maden İşçiliği Başlangıcından MÖ III. Binyıl "
    "Sonuna Kadar"
)


class _FakeClient:
    """Records every query it receives and returns canned payloads."""

    def __init__(self, responses: dict[str, list[dict]]) -> None:
        self.responses = responses
        self.queries: list[str] = []

    def search(self, query: str) -> dict:
        self.queries.append(query)
        return {"hits": {"hits": self.responses.get(query, [])}}


def _hit(title: str) -> dict:
    return {
        "_id": "abc",
        "_source": {
            "metadata": {"title": title, "date": "2009"},
            "slug": "thesis",
        },
    }


def test_query_variants_longest_first() -> None:
    variants = HarmanProvider._query_variants(KESKIN_TITLE)
    assert variants[0] == KESKIN_TITLE
    assert variants[1] == KESKIN_HEAD
    assert all(
        len(v.split()) < len(KESKIN_TITLE.split())
        for v in variants[1:]
    )


def test_query_variants_short_title_no_fallback() -> None:
    assert HarmanProvider._query_variants("A short title") == ["A short title"]


def test_fallback_fires_when_full_title_returns_nothing() -> None:
    client = _FakeClient({KESKIN_HEAD: [_hit(KESKIN_HEAD)]})
    provider = HarmanProvider(client=client)

    ref = Reference(
        raw_text=KESKIN_TITLE, title=KESKIN_TITLE, year=2009,
    )
    matches = provider.search(ref)

    assert client.queries[0] == KESKIN_TITLE
    assert KESKIN_HEAD in client.queries
    assert len(matches) == 1
    assert matches[0].title == KESKIN_HEAD


def test_prefix_fallback_fires_when_subtitle_head_returns_nothing() -> None:
    client = _FakeClient({KESKIN_PREFIX_10: [_hit(KESKIN_HEAD)]})
    provider = HarmanProvider(client=client)

    ref = Reference(
        raw_text=KESKIN_TITLE, title=KESKIN_TITLE, year=2009,
    )
    matches = provider.search(ref)

    assert client.queries[:3] == [KESKIN_TITLE, KESKIN_HEAD, KESKIN_PREFIX_10]
    assert len(matches) == 1


def test_full_title_hit_short_circuits_fallback() -> None:
    client = _FakeClient({KESKIN_TITLE: [_hit(KESKIN_TITLE)]})
    provider = HarmanProvider(client=client)

    ref = Reference(
        raw_text=KESKIN_TITLE, title=KESKIN_TITLE, year=2009,
    )
    matches = provider.search(ref)

    assert client.queries == [KESKIN_TITLE]
    assert len(matches) == 1