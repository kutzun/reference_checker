"""
Tests for Turkish book-reference author extraction.

Regression tests for four entries from a real Turkish manuscript whose
first authors were extracted as the given name instead of the surname,
because the surname regex in extractor/text_metadata.py did not include
Latin Extended-A characters (ı, ğ, İ, ş) or the Turkish uppercase
initials in the initials class.

Downstream effect: the reference parser produces a wrong authors[0],
the matcher keys the reference under the wrong name, and the internal
check reports both a false MISSING (for the in-text citation) and a
false UNCITED (for the reference).
"""

from extractor.text_metadata import extract_authors


def _surname(authors: list[str]) -> str:
    """Return the surname portion of the first parsed author."""
    assert authors, "no authors extracted"
    return authors[0].split(",")[0].strip()


def test_kilic_surname_extracted():
    """Kılıç, Mahmud Erol, Sûfî ve Şiir: … 2017. -> surname Kılıç."""
    text = (
        "Kılıç, Mahmud Erol, Sûfî ve Şiir: Osmanlı Tasavvuf Şiirinin "
        "Poetikası, Sufi Kitap, İstanbul 2017."
    )
    assert _surname(extract_authors(text)) == "Kılıç"


def test_kutlug_surname_extracted():
    """Kutluğ, Yakup Fikret, Türk Musikisinde Makamlar, … 2000."""
    text = (
        "Kutluğ, Yakup Fikret, Türk Musikisinde Makamlar, "
        "Yapı Kredi Yayınları, İstanbul 2000."
    )
    assert _surname(extract_authors(text)) == "Kutluğ"


def test_bardakci_surname_extracted():
    """Bardakçı, Murat, Maragalı Abdülkadir: … 1986."""
    text = (
        "Bardakçı, Murat, Maragalı Abdülkadir: XV. yy. Bestecisi ve "
        "Müzik Nazariyatçısının Hayat Hikâyesiyle Eserleri Üzerine "
        "Bir Çalışma, Pan Yayıncılık, İstanbul 1986."
    )
    assert _surname(extract_authors(text)) == "Bardakçı"


def test_ahmed_i_dai_surname_extracted():
    """Ahmed-i Dâ'î, Çengnâme: … 1992. -> surname Ahmed-i Dâ'î."""
    text = (
        "Ahmed-i Dâ'î, Çengnâme: İnceleme-Tenkidli Metin, haz. Gönül "
        "Alpay Tekin, Harvard Üniversitesi Yakındoğu Dilleri ve "
        "Medeniyetleri Bölümü, Cambridge 1992."
    )
    assert _surname(extract_authors(text)) == "Ahmed-i Dâ'î"


def test_english_reference_still_works():
    """Contract guard: the fix must not break plain English entries."""
    text = "Smith, J. (2020). Example article. Journal of Examples, 1(1), 1-10."
    assert _surname(extract_authors(text)) == "Smith"