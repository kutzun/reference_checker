"""
Ground-truth expectations for repeated-author markers.

A repeated-author marker replaces the author block of a consecutive
entry. Four common marker variants are covered:

    ———    3 em-dashes    (Chicago style)
    ---    3 hyphens
    ------ 6 hyphens
    –––    3 en-dashes

Structure
---------
Each entry is a 3-tuple:

    (id, [raw_text, ...], [expected_first_author, ...])

- The list of raw_text entries is a CONSECUTIVE run from a bibliography.
- The list of expected_first_author values must be the same length.
- Every expected value is the result of normalize_author_name() on the
  resolved first author. If the marker is not resolved, the current
  parser will produce "" for that position, so a failing test is a
  meaningful signal — not a crash.

Each raw_text entry preserves the exact input form, including the
paste-style period after the marker ("———. (2003b).") and any a/b
year suffix on the year.
"""

SEQUENCES = [
    (
        "chicago_em_dash",
        [
            "Smith, J. (2003a). First article on widgets. "
            "Journal of Widgets, 12(3), 45-67.",
            "———. (2003b). Second article on widgets. "
            "Journal of Widgets, 12(4), 68-89.",
        ],
        ["smith", "smith"],
    ),
    (
        "three_hyphens",
        [
            "Yılmaz, A. (2010a). Birinci çalışma. "
            "Türk Dergisi, 5(1), 10-20.",
            "---. (2010b). İkinci çalışma. "
            "Türk Dergisi, 5(2), 21-31.",
        ],
        ["yilmaz", "yilmaz"],
    ),
    (
        "six_hyphens",
        [
            "Kaya, M. (2015a). First study. Journal X, 1(1), 1-10.",
            "------. (2015b). Second study. Journal X, 1(2), 11-20.",
        ],
        ["kaya", "kaya"],
    ),
    (
        "three_en_dashes",
        [
            "Demir, S. (2018a). Alpha. Journal Y, 2(1), 1-5.",
            "–––. (2018b). Beta. Journal Y, 2(2), 6-10.",
        ],
        ["demir", "demir"],
    ),
]