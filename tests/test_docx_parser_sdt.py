"""Regression: citations wrapped in <w:sdt> must be visible."""

from docx.oxml import parse_xml

from parser.docx_parser import DocxParser

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class _FakeParagraph:
    def __init__(self, element):
        self._element = element


def test_paragraph_text_includes_sdt_content():
    xml = (
        f'<w:p xmlns:w="{_W_NS}">'
        '<w:r><w:t xml:space="preserve">before </w:t></w:r>'
        '<w:sdt><w:sdtContent>'
        '<w:r><w:t>(Çongur, 1999, s. 15)</w:t></w:r>'
        '</w:sdtContent></w:sdt>'
        '<w:r><w:t xml:space="preserve"> after</w:t></w:r>'
        '</w:p>'
    )
    p = _FakeParagraph(parse_xml(xml))
    assert (
        DocxParser._paragraph_text(p)
        == "before (Çongur, 1999, s. 15) after"
    )


def test_paragraph_text_excludes_deleted_text():
    xml = (
        f'<w:p xmlns:w="{_W_NS}">'
        '<w:r><w:t>kept</w:t></w:r>'
        '<w:del><w:r><w:delText>removed</w:delText></w:r></w:del>'
        '</w:p>'
    )
    p = _FakeParagraph(parse_xml(xml))
    assert DocxParser._paragraph_text(p) == "kept"