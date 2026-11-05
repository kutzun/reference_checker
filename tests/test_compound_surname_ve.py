"""Regression: Turkish 've' between compound-surname author pairs."""

from extractor.metadata import extract_metadata
from models import Reference


def _authors(raw: str) -> list[str]:
    return extract_metadata(Reference(raw_text=raw)).authors


def test_altiner_sanci_uzun_2024():
    raw = (
        "Altıner, V. ve Sancı Uzun, D. (2024). Dramada kukla tekniği "
        "ile yapılan etkinliklerin ilkokul 3. sınıf öğrencilerinin "
        "hazırlıksız konuşma becerilerine etkisi. A Dergisi, 5(1), 1-10."
    )
    assert _authors(raw) == ["Altıner, V.", "Sancı Uzun, D."]


def test_aykac_cakir_ilhan_2014():
    raw = (
        "Aykaç, M. ve Çakır İlhan, A. (2014). Çocuk edebiyatı "
        "metinleriyle kurgulanan yaratıcı drama etkinliklerinin "
        "konuşma becerilerine etkisi. Ankara Üniversitesi Eğitim "
        "Bilimleri Fakültesi Dergisi, 47(1), 1-20."
    )
    assert _authors(raw) == ["Aykaç, M.", "Çakır İlhan, A."]


def test_ercan_guven_ak_2025():
    raw = (
        "Ercan Güven, A. N. ve Ak, A. (2025). Ortaokul öğrencilerinin "
        "anlatma becerilerine yönelik lisansüstü tezlerin analizi. "
        "Batı Anadolu Eğitim Bilimleri Dergisi, 16(1), 798-816. "
        "https://doi.org/10.51460/baebd.1625404"
    )
    assert _authors(raw) == ["Ercan Güven, A. N.", "Ak, A."]


def test_ozturk_pat_yilmaz_2021():
    raw = (
        "Öztürk Pat, Ö. ve Yılmaz, M. (2021). Impact of creative "
        "drama method on speaking skills. Journal of Education, "
        "5(2), 100-110."
    )
    assert _authors(raw) == ["Öztürk Pat, Ö.", "Yılmaz, M."]


def test_single_word_surnames_ve_still_works():
    """Edit B's original case — must not regress."""
    raw = "Kardaş, N. ve Akın, E. (2019). Sınıf öğretmenlerinin okuma."
    assert _authors(raw) == ["Kardaş, N.", "Akın, E."]