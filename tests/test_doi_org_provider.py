"""
Tests for DoiOrgProvider.

DoiOrgProvider resolves a DOI via doi.org and converts the returned
CSL-JSON into a ReferenceMatch. Tests inject a fake client so no HTTP
request is made.
"""

from models import Reference
from models.enums import Provider, ReferenceType
from verification.doi_org_provider import DoiOrgProvider

from test_data.providers.doi_org import ALHARBI_2022


class FakeDoiOrgClient:
    """
    Returns a canned CSL-JSON response (or None) for any DOI.
    """

    def __init__(self, response):
        self.response = response

    def resolve(self, doi: str):
        return self.response


def test_doi_org_provider_converts_csl_json():
    reference = Reference(
        raw_text="Al-Harbi, A.I. & Badawi, N.S. (2022). ...",
        doi="10.1108/JIMA-08-2019-0171",
    )

    provider = DoiOrgProvider(
        client=FakeDoiOrgClient(ALHARBI_2022),
    )

    matches = provider.search(reference)

    assert len(matches) == 1
    match = matches[0]

    assert match.provider == Provider.DOI_ORG
    assert match.reference_type == ReferenceType.JOURNAL_ARTICLE
    assert match.title == ALHARBI_2022["title"]
    assert match.journal == "Journal of Islamic Marketing"
    assert match.year == 2021  # issued date, not published-print
    assert match.doi == "10.1108/jima-08-2019-0171"
    assert match.publisher == "Emerald"
    assert match.authors == [
        "Ahlam Ibrahim Al-Harbi",
        "Nada Saleh Badawi",
    ]


def test_doi_org_provider_returns_empty_without_doi():
    reference = Reference(
        raw_text="Something without a DOI.",
        title="Something",
    )

    provider = DoiOrgProvider(
        client=FakeDoiOrgClient(ALHARBI_2022),
    )

    matches = provider.search(reference)

    assert matches == []


def test_doi_org_provider_handles_unresolvable_doi():
    reference = Reference(
        raw_text="Fake reference.",
        doi="10.9999/does-not-exist",
    )

    provider = DoiOrgProvider(
        client=FakeDoiOrgClient(None),
    )

    matches = provider.search(reference)

    assert matches == []