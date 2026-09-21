"""
Tests for the internal-check service.
"""

from pathlib import Path

from docx import Document

from models import Reference

from internal_check.profiles import ENGLISH, GENERIC, TURKISH
from internal_check.service import InternalCheckService


def _ref(raw: str, authors: list[str], year: int | None) -> Reference:
    return Reference(raw_text=raw, authors=authors, year=year)


# ---------------------------------------------------------------------------
# check_text: English
# ---------------------------------------------------------------------------

def test_english_all_matched():
    service = InternalCheckService(profile=ENGLISH)
    body = "The effect was clear (Smith, 2020)."
    refs = [_ref("Smith 2020", ["Smith, J."], 2020)]
    result = service.check_text(body, refs)
    assert result.issues == []
    assert result.summary["citations_found"] == 1
    assert result.summary["references_found"] == 1


def test_english_missing_reference():
    service = InternalCheckService(profile=ENGLISH)
    body = "The effect was clear (Smith, 2020)."
    refs: list[Reference] = []
    result = service.check_text(body, refs)
    assert result.summary["missing_references"] == 1


def test_english_uncited_reference():
    service = InternalCheckService(profile=ENGLISH)
    body = "Nothing cited here."
    refs = [_ref("Smith 2020", ["Smith, J."], 2020)]
    result = service.check_text(body, refs)
    assert result.summary["uncited_references"] == 1


def test_english_statistics_ignored():
    service = InternalCheckService(profile=ENGLISH)
    body = "Mean was (M = 2.985; SD = 1.0345)."
    refs: list[Reference] = []
    result = service.check_text(body, refs)
    assert result.summary["citations_found"] == 0


# ---------------------------------------------------------------------------
# check_text: Turkish
# ---------------------------------------------------------------------------

def test_turkish_all_matched():
    service = InternalCheckService(profile=TURKISH)
    body = "Sonuçlar açıktır (Yılmaz, 2020)."
    refs = [_ref("Yilmaz 2020", ["Yilmaz, A."], 2020)]
    result = service.check_text(body, refs)
    assert result.issues == []


def test_turkish_narrative():
    service = InternalCheckService(profile=TURKISH)
    body = "Yılmaz (2020) bunu savunmuştur."
    refs = [_ref("Yilmaz 2020", ["Yilmaz, A."], 2020)]
    result = service.check_text(body, refs)
    assert result.issues == []


# ---------------------------------------------------------------------------
# Numeric
# ---------------------------------------------------------------------------

def test_numeric_all_matched():
    service = InternalCheckService(profile=GENERIC)
    body = "See [1] and [2]."
    refs = [
        _ref("First", ["A"], 2020),
        _ref("Second", ["B"], 2021),
    ]
    result = service.check_text(body, refs)
    # In numeric mode the reference keys are ignored; only positions
    # matter. But the matcher also runs the author-year pass because
    # there is at least one non-numeric citation type in the list. Since
    # no author-year citations are present here, the author-year pass
    # is skipped and only numeric matching applies.
    assert result.summary["missing_references"] == 0
    assert result.summary["uncited_references"] == 0


# ---------------------------------------------------------------------------
# check_docx: full pipeline
# ---------------------------------------------------------------------------

def _make_docx(tmp_path: Path) -> Path:
    path = tmp_path / "manuscript.docx"
    doc = Document()
    doc.add_paragraph("Introduction")
    doc.add_paragraph("The effect was clear (Smith, 2020).")
    doc.add_paragraph("References")
    doc.add_paragraph("Smith, J. (2020). Example article.")
    doc.save(path)
    return path


def test_check_docx_success(tmp_path: Path):
    path = _make_docx(tmp_path)
    service = InternalCheckService(profile=ENGLISH)
    result = service.check_docx(path)
    assert result.summary["citations_found"] == 1
    assert result.summary["references_found"] == 1
    assert result.summary["missing_references"] == 0
    assert result.summary["uncited_references"] == 0


def test_check_docx_missing_reference(tmp_path: Path):
    path = tmp_path / "manuscript.docx"
    doc = Document()
    doc.add_paragraph("Introduction")
    doc.add_paragraph("The effect was clear (Smith, 2020).")
    doc.add_paragraph("References")
    doc.add_paragraph("Jones, A. (2019). Another article.")
    doc.save(path)

    service = InternalCheckService(profile=ENGLISH)
    result = service.check_docx(path)
    assert result.summary["missing_references"] == 1
    assert result.summary["uncited_references"] == 1


def test_unparsed_property_is_empty_when_all_clean():
    service = InternalCheckService(profile=ENGLISH)
    body = "(Smith, 2020)"
    refs = [_ref("Smith 2020", ["Smith, J."], 2020)]
    service.check_text(body, refs)
    assert service.unparsed == []