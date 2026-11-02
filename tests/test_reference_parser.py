"""
Tests for reference parser.
"""

from parser.reference_parser import (
    ReferenceParser,
)


def test_parse_reference_metadata():

    parser = ReferenceParser()

    result = parser.parse(
        [("Smith, J. " "(2020). " "Example article. " "doi:10.1234/example")]
    )

    reference = result[0]

    assert reference.year == 2020

    assert reference.doi == "10.1234/example"

def test_parse_quoted_title_year_at_end():
    """Regression: quoted title must win over the journal name.

    Harvard/Chicago style with the year at the end:
        Wright, Owen, "A Preliminary Version of the Kitāb al-Adwār",
        Bulletin of the School of Oriental and African Studies,
        Cilt 58, Sayı 3, 1995, s. 455-478.

    Before the fix, the final fallback picked the longest
    comma-separated segment (the journal name) as the title.
    """
    parser = ReferenceParser()
    result = parser.parse([
        'Wright, Owen, "A Preliminary Version of the Kitāb al-Adwār", '
        'Bulletin of the School of Oriental and African Studies, '
        'Cilt 58, Sayı 3, 1995, s. 455-478.'
    ])
    reference = result[0]
    assert reference.title == "A Preliminary Version of the Kitāb al-Adwār"
    assert reference.year == 1995