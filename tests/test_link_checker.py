"""
Tests for LinkChecker.

HTTP calls are mocked — no network access. Each test asserts the
correct LinkStatus for a given response shape or exception.
"""

from unittest.mock import Mock, patch

import requests

from verification.link_checker import LinkChecker, LinkStatus


def test_live_url_200():
    with patch("verification.link_checker.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=200)
        assert LinkChecker().check("https://example.com") == LinkStatus.LIVE


def test_live_url_after_redirect():
    with patch("verification.link_checker.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=301)
        assert LinkChecker().check("http://example.com") == LinkStatus.LIVE


def test_gone_url_404():
    with patch("verification.link_checker.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=404)
        assert LinkChecker().check("https://example.com/gone") == LinkStatus.DEAD


def test_gone_url_410():
    with patch("verification.link_checker.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=410)
        assert LinkChecker().check("https://example.com/gone") == LinkStatus.DEAD


def test_forbidden_is_unknown():
    with patch("verification.link_checker.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=403)
        assert LinkChecker().check("https://blocked.example.com") == LinkStatus.UNKNOWN


def test_timeout_is_unknown():
    with patch("verification.link_checker.requests.get") as mock_get:
        mock_get.side_effect = requests.Timeout()
        assert LinkChecker().check("https://slow.example.com") == LinkStatus.UNKNOWN


def test_connection_error_is_dead():
    with patch("verification.link_checker.requests.get") as mock_get:
        mock_get.side_effect = requests.ConnectionError()
        assert LinkChecker().check("https://nowhere.invalid") == LinkStatus.DEAD


def test_empty_url_is_unknown():
    assert LinkChecker().check("") == LinkStatus.UNKNOWN