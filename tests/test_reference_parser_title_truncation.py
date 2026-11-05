"""
Regression tests for two reference-parser bugs exposed by 55.docx.

Bug 1: title truncated at Turkish ordinal notation ("3. sınıf").
    extract_title Pattern 6 stopped at the first digit-followed-by-period
    because the terminator regex had no digit guard.

Bug 2: second author dropped when 've' separated two "Surname, Given"
    pairs ("Kardaş, N. ve Akın, E."). _AND_AMPERSAND_RE matched only
    'and' / '&', so 've' was not treated as a separator, and the
    truncation loop dropped everything past the first comma group.
"""

from __future__ import annotations

from extractor.metadata import extract_metadata
from models import Reference


def _parse(raw: str) -> Reference:
    return extract_metadata(Reference(raw_text=raw))


# ---- Bug 1: title truncation at N. ------------------------------------

def test_title_with_ilkokul_3_keeps_full_title() -> None:
    ref = _parse(
        "Altıner, V. (2023). Dramada kukla tekniği ile yapılan "
        "etkinliklerin ilkokul 3. sınıf öğrencilerinin hazırlıksız "
        "konuşma becerilerine etkisi (Yüksek lisans tezi). "
        "https://tez.yok.gov.tr/UlusalTezMerkezi/"
    )
    assert ref.title is not None
    assert "3. sınıf öğrencilerinin" in ref.title
    assert not ref.title.endswith("ilkokul 3")


def test_title_with_6_sinif_keeps_full_title() -> None:
    ref = _parse(
        "Maden, S. (2010). İlköğretim 6. sınıf Türkçe dersinde drama "
        "yönteminin temel dil becerilerinin kazanımına etkisi "
        "(Doktora tezi). https://tez.yok.gov.tr/UlusalTezMerkezi/"
    )
    assert ref.title is not None
    assert "6. sınıf Türkçe" in ref.title
    assert not ref.title.endswith("İlköğretim 6")


def test_title_with_8_siniflar_keeps_full_title() -> None:
    ref = _parse(
        "Millî Eğitim Bakanlığı (MEB). (2024). Ortaokul Türkçe dersi "
        "öğretim programı (5, 6, 7 ve 8. sınıflar) Türkiye yüzyılı "
        "maarif modeli. https://tymm.meb.gov.tr/upload/program.pdf"
    )
    assert ref.title is not None
    assert "8. sınıflar" in ref.title
    assert "maarif modeli" in ref.title


# ---- Bug 2: 've' separating two Surname, Initials pairs ---------------

def test_ve_between_surname_initials_pairs_splits() -> None:
    ref = _parse(
        "Kardaş, N. ve Akın, E. (2019). Drama etkinliklerinin 7. sınıf "
        "öğrencilerinin Türkçe konuşma kaygılarına etkisi. Kuram ve "
        "Uygulamada Sosyal Bilimler Dergisi, 3(2), 91-113."
    )
    assert len(ref.authors) == 2
    assert ref.authors[0].startswith("Kardaş")
    assert ref.authors[1].startswith("Akın")


def test_ve_inside_title_not_split() -> None:
    ref = _parse(
        "Wright, O. (1994). A Preliminary Version. Bulletin of the "
        "School of Oriental and African Studies, 58(3), 455-478."
    )
    # Sanity check: 've' is not present, this test locks the no-split case.
    assert len(ref.authors) == 1


def test_ve_in_publisher_not_split() -> None:
    ref = _parse(
        "Öztürk, A. (2020). Bir kitap. Alfa ve Omega Yayınları."
    )
    assert len(ref.authors) == 1
    assert ref.authors[0].startswith("Öztürk")