"""
Tests for PubMed client.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from models import Reference

from verification.exceptions import (
    VerificationProviderError,
)
from verification.pubmed_client import (
    PubMedClient,
)


def _mock_response(payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_pubmed_search_returns_records():

    client = PubMedClient()

    reference = Reference(
        raw_text="Smith, J. (2020). Writing Research.",
        title="Writing Research",
        doi="10.1234/example",
    )

    esearch = _mock_response(
        {"esearchresult": {"idlist": ["12345"]}}
    )
    esummary = _mock_response(
        {
            "result": {
                "uids": ["12345"],
                "12345": {
                    "uid": "12345",
                    "title": "Writing Research.",
                    "authors": [{"name": "Smith J"}],
                    "pubdate": "2020",
                },
            }
        }
    )

    with patch(
        "requests.get",
        side_effect=[esearch, esummary],
    ):

        result = client.search(reference)

    assert len(result) == 1

    assert result[0]["uid"] == "12345"


def test_pubmed_uses_doi_field_when_doi_present():

    client = PubMedClient()

    reference = Reference(
        raw_text="Smith, J. (2020). Writing Research.",
        title="Writing Research",
        doi="10.1234/example",
    )

    esearch = _mock_response(
        {"esearchresult": {"idlist": ["12345"]}}
    )
    esummary = _mock_response(
        {"result": {"uids": ["12345"], "12345": {"uid": "12345"}}}
    )

    with patch(
        "requests.get",
        side_effect=[esearch, esummary],
    ) as mocked_get:

        client.search(reference)

    first_params = mocked_get.call_args_list[0][1]["params"]

    assert "[doi]" in first_params["term"]

    assert "10.1234/example" in first_params["term"]


def test_pubmed_falls_back_to_title_when_no_doi():

    client = PubMedClient()

    reference = Reference(
        raw_text="Smith, J. (2020). Writing Research.",
        title="Writing Research",
    )

    esearch = _mock_response(
        {"esearchresult": {"idlist": ["12345"]}}
    )
    esummary = _mock_response(
        {"result": {"uids": ["12345"], "12345": {"uid": "12345"}}}
    )

    with patch(
        "requests.get",
        side_effect=[esearch, esummary],
    ) as mocked_get:

        client.search(reference)

    first_params = mocked_get.call_args_list[0][1]["params"]

    assert "[Title]" in first_params["term"]


def test_pubmed_returns_empty_when_no_pmids():

    client = PubMedClient()

    reference = Reference(
        raw_text="Smith, J. (2020). Writing Research.",
        title="Writing Research",
    )

    esearch = _mock_response(
        {"esearchresult": {"idlist": []}}
    )

    with patch(
        "requests.get",
        return_value=esearch,
    ):

        result = client.search(reference)

    assert result == []


def test_pubmed_network_failure():

    client = PubMedClient()

    reference = Reference(
        raw_text="Smith, J. (2020). Writing Research.",
        title="Writing Research",
    )

    with patch(
        "requests.get",
        side_effect=requests.RequestException("network failure"),
    ):

        with pytest.raises(VerificationProviderError):
            client.search(reference)


def test_pubmed_invalid_response():

    client = PubMedClient()

    reference = Reference(
        raw_text="Smith, J. (2020). Writing Research.",
        title="Writing Research",
    )

    response = Mock()

    response.raise_for_status.return_value = None

    response.json.side_effect = ValueError("invalid json")

    with patch(
        "requests.get",
        return_value=response,
    ):

        with pytest.raises(VerificationProviderError):
            client.search(reference)