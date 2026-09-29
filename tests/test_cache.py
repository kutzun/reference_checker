"""
Tests for verification cache.
"""

from cache.cache import (
    VerificationCache,
)


def test_cache_set_and_get(
    tmp_path,
):

    cache_file = tmp_path / "cache.json"

    cache = VerificationCache(cache_file)

    cache.set(
        "reference-1",
        {"status": "verified"},
    )

    result = cache.get("reference-1")

    assert result == {"status": "verified"}


def test_missing_cache_returns_none(
    tmp_path,
):

    cache = VerificationCache(tmp_path / "cache.json")

    result = cache.get("missing")

    assert result is None
