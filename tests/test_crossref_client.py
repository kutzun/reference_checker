"""
Tests for Crossref client.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from verification.crossref_client import (
    CrossrefClient,
)
from verification.exceptions import (
    VerificationProviderError,
)


def test_crossref_search():

    client = CrossrefClient()

    mock_response = Mock()

    mock_response.json.return_value = {"message": {"items": []}}

    mock_response.raise_for_status.return_value = None

    with patch(
        "requests.get",
        return_value=mock_response,
    ) as mocked_get:

        result = client.search("example article")

    assert result["message"]["items"] == []

    mocked_get.assert_called_once()


def test_crossref_network_failure():

    client = CrossrefClient()

    with patch(
        "requests.get",
        side_effect=requests.RequestException("network failure"),
    ):

        with pytest.raises(VerificationProviderError):
            client.search("example article")


def test_crossref_invalid_response():

    client = CrossrefClient()

    mock_response = Mock()

    mock_response.raise_for_status.return_value = None

    mock_response.json.side_effect = ValueError("invalid json")

    with patch(
        "requests.get",
        return_value=mock_response,
    ):

        with pytest.raises(VerificationProviderError):
            client.search("example article")
