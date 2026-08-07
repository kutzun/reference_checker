"""
Tests for CLI module.
"""

from cli.main import (
    create_parser,
)


def test_cli_parser():

    parser = create_parser()

    args = parser.parse_args(["article.docx"])

    assert args.document.name == "article.docx"
