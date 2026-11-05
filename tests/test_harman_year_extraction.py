"""Regression: Harman year comes from publication_year, not harvest date."""

from verification.harman_provider import HarmanProvider


def _year(meta: dict) -> int | None:
    return HarmanProvider._year(meta)


def test_prefers_publication_year_over_harvest_date():
    # Shape taken from the Kahyaoğlu 2008 record that mis-verified as 2026.
    meta = {
        "date": [
            "2026-10-23T18:06:26",
            "2026-10-23T18:06:26",
            "2008-01-01T00:00:00",
        ],
        "originalDates": [
            "2026-10-23T18:06:26Z",
            "2026-10-23T18:06:26Z",
            "2008",
        ],
        "publication_date": "2008-01-01T00:00:00",
        "publication_year": 2008,
    }
    assert _year(meta) == 2008


def test_falls_back_to_publication_date_string():
    meta = {"publication_date": "2019-06-15T00:00:00"}
    assert _year(meta) == 2019


def test_accepts_publication_year_as_string():
    meta = {"publication_year": "2018"}
    assert _year(meta) == 2018


def test_missing_authoritative_year_returns_none():
    # Harvest date present but no publication_year / publication_date.
    # Must return None, not 2026.
    meta = {"date": ["2026-10-23T18:06:26"]}
    assert _year(meta) is None


def test_empty_meta_returns_none():
    assert _year({}) is None

def test_bare_year_in_date_is_accepted():
    # Arkan 2026 fixture shape: date is a bare 4-digit year, not
    # a timestamp. This is a real publication date.
    meta = {"date": ["2026"]}
    assert _year(meta) == 2026


def test_iso_timestamp_alone_is_rejected():
    # Harvest-only records: date carries a full ISO timestamp with
    # no bare year anywhere. Must return None.
    meta = {"date": ["2026-10-23T18:06:26"]}
    assert _year(meta) is None