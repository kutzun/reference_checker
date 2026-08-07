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
