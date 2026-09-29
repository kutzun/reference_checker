"""
Regression tests for the internal-check module.

These tests were written after reading the module end-to-end in a
diagnostic session. Each test targets a specific defect that was
found by inspection and is confirmed to fail on current code.

The tests exercise InternalCheckService.check_text() only — the pure
core. No DOCX, no GUI, no network. Both English and Turkish fixtures
are provided for each defect so that neither language profile can
silently diverge.

Defects covered:
    1. Narrative multi-author citations keep only the last surname.
       -> test_narrative_multi_author_english / _turkish
    2. Narrative "et al." / "vd." citations return no author at all.
       -> test_narrative_et_al_english / _turkish
    3. Reference-side year_suffix is dropped, so "2020a"/"2020b"
       citations never match their references.
       -> test_year_suffix_english / _turkish

If any of these tests pass on unmodified code, the corresponding
diagnosis is wrong and should be re-checked before any fix is applied.
"""

from models import Reference

from internal_check.models import CitationKind
from internal_check.profiles import ENGLISH, TURKISH
from internal_check.service import InternalCheckService


# ---------------------------------------------------------------------------
# Defect 1 — narrative multi-author keeps only the last surname
# ---------------------------------------------------------------------------

def test_narrative_multi_author_english():
    """
    "Smith and Jones (2020)" must yield authors ["Smith", "Jones"],
    not just ["Jones"]. When only "Jones" is retained, the matcher
    looks for a reference keyed "jones:2020", finds none, and reports
    both a MISSING citation and an UNCITED reference — two false
    issues from one sentence.
    """
    body = "Smith and Jones (2020) argued that the effect is robust."
    refs = [
        Reference(
            raw_text=(
                "Smith, J., & Jones, B. (2020). Some title. "
                "Journal of Examples, 12(3), 45-67."
            ),
            authors=["Smith", "Jones"],
            year=2020,
        )
    ]

    service = InternalCheckService(profile=ENGLISH)
    result = service.check_text(body, refs)

    narrative = [
        c for c in result.citations if c.kind == CitationKind.NARRATIVE
    ]
    assert len(narrative) == 1, (
        f"expected 1 narrative citation, got {len(narrative)}; "
        f"unparsed={service.unparsed!r}"
    )
    assert narrative[0].authors == ["Smith", "Jones"], (
        f"expected both surnames, got {narrative[0].authors!r}"
    )

    assert result.missing_references() == [], (
        "citation should have matched the reference"
    )
    assert result.uncited_references() == [], (
        "reference should have been marked as cited"
    )


def test_narrative_multi_author_turkish():
    """
    Turkish twin of test_narrative_multi_author_english.

    "Yılmaz ve Kaya (2020)" must yield authors ["Yılmaz", "Kaya"].
    The defect is language-independent but the Turkish conjunction
    ("ve") is a separate code path from "and" and must be covered.
    """
    body = "Yılmaz ve Kaya (2020) çalışmalarında bu etkinin güçlü olduğunu savunmuştur."
    refs = [
        Reference(
            raw_text=(
                "Yılmaz, A. ve Kaya, B. (2020). Bir başlık. "
                "Dergi Adı, 12(3), 45-67."
            ),
            authors=["Yılmaz", "Kaya"],
            year=2020,
        )
    ]

    service = InternalCheckService(profile=TURKISH)
    result = service.check_text(body, refs)

    narrative = [
        c for c in result.citations if c.kind == CitationKind.NARRATIVE
    ]
    assert len(narrative) == 1, (
        f"expected 1 narrative citation, got {len(narrative)}; "
        f"unparsed={service.unparsed!r}"
    )
    assert narrative[0].authors == ["Yılmaz", "Kaya"], (
        f"expected both surnames, got {narrative[0].authors!r}"
    )

    assert result.missing_references() == []
    assert result.uncited_references() == []


# ---------------------------------------------------------------------------
# Defect 2 — narrative "et al." / "vd." returns no author
# ---------------------------------------------------------------------------

def test_narrative_et_al_english():
    """
    "Smith et al. (2020)" must produce a narrative citation with
    "Smith" as the author. On current code, _find_narrative_author
    returns None because the last token before "(" is "al", which
    fails the isupper() check. The citation is silently dropped and
    the reference is falsely reported as uncited.
    """
    body = "Smith et al. (2020) reported a strong positive correlation."
    refs = [
        Reference(
            raw_text=(
                "Smith, J., Brown, C., & Davis, E. (2020). Title. "
                "Journal of Examples, 5(2), 100-120."
            ),
            authors=["Smith", "Brown", "Davis"],
            year=2020,
        )
    ]

    service = InternalCheckService(profile=ENGLISH)
    result = service.check_text(body, refs)

    narrative = [
        c for c in result.citations if c.kind == CitationKind.NARRATIVE
    ]
    assert len(narrative) == 1, (
        f"expected 1 narrative citation, got {len(narrative)}; "
        f"unparsed={service.unparsed!r}"
    )
    assert narrative[0].authors and narrative[0].authors[0] == "Smith", (
        f"expected first author 'Smith', got {narrative[0].authors!r}"
    )

    assert result.missing_references() == []
    assert result.uncited_references() == []


def test_narrative_et_al_turkish():
    """
    Turkish twin. "Yılmaz vd. (2020)" must produce a narrative
    citation with "Yılmaz" as the author. Same failure mode as the
    English case, via a different et-al marker ("vd.").
    """
    body = "Yılmaz vd. (2020) bu ilişkinin güçlü olduğunu bildirmiştir."
    refs = [
        Reference(
            raw_text=(
                "Yılmaz, A., Demir, C. ve Şahin, E. (2020). Başlık. "
                "Dergi Adı, 5(2), 100-120."
            ),
            authors=["Yılmaz", "Demir", "Şahin"],
            year=2020,
        )
    ]

    service = InternalCheckService(profile=TURKISH)
    result = service.check_text(body, refs)

    narrative = [
        c for c in result.citations if c.kind == CitationKind.NARRATIVE
    ]
    assert len(narrative) == 1, (
        f"expected 1 narrative citation, got {len(narrative)}; "
        f"unparsed={service.unparsed!r}"
    )
    assert narrative[0].authors and narrative[0].authors[0] == "Yılmaz", (
        f"expected first author 'Yılmaz', got {narrative[0].authors!r}"
    )

    assert result.missing_references() == []
    assert result.uncited_references() == []


# ---------------------------------------------------------------------------
# Defect 3 — reference-side year_suffix is dropped
# ---------------------------------------------------------------------------

def test_year_suffix_english():
    """
    A manuscript that disambiguates two works by the same author in
    the same year — standard APA "2020a"/"2020b" — must match both
    citations to their references. On current code, _reference_key
    passes year_suffix=None, so the reference keys are "smith:2020"
    while the citation keys are "smith:2020a" / "smith:2020b". No
    match, two false MISSING and two false UNCITED issues.
    """
    body = (
        "Earlier work (Smith, 2020a) established the framework. "
        "A follow-up study (Smith, 2020b) refined the method."
    )
    refs = [
        Reference(
            raw_text=(
                "Smith, J. (2020a). First title. Journal of Examples, "
                "1(1), 1-10."
            ),
            authors=["Smith"],
            year=2020,
            year_suffix="a",
        ),
        Reference(
            raw_text=(
                "Smith, J. (2020b). Second title. Journal of Examples, "
                "1(2), 11-20."
            ),
            authors=["Smith"],
            year=2020,
            year_suffix="b",
        ),
    ]

    service = InternalCheckService(profile=ENGLISH)
    result = service.check_text(body, refs)

    parenthetical = [
        c for c in result.citations
        if c.kind == CitationKind.PARENTHETICAL
    ]
    assert len(parenthetical) == 2, (
        f"expected 2 parenthetical citations, got {len(parenthetical)}; "
        f"unparsed={service.unparsed!r}"
    )
    assert sorted(c.year_suffix for c in parenthetical) == ["a", "b"]

    assert result.missing_references() == [], (
        "both suffixed citations should have matched their references"
    )
    assert result.uncited_references() == [], (
        "both suffixed references should have been marked as cited"
    )


def test_year_suffix_turkish():
    """
    Turkish twin of test_year_suffix_english. Same defect, Turkish
    surname to exercise the Turkish-aware normalizer path alongside
    the suffix logic.
    """
    body = (
        "Önceki çalışma (Yılmaz, 2020a) çerçeveyi oluşturmuştur. "
        "Takip eden çalışma (Yılmaz, 2020b) yöntemi geliştirmiştir."
    )
    refs = [
        Reference(
            raw_text=(
                "Yılmaz, A. (2020a). Birinci başlık. Dergi Adı, "
                "1(1), 1-10."
            ),
            authors=["Yılmaz"],
            year=2020,
            year_suffix="a",
        ),
        Reference(
            raw_text=(
                "Yılmaz, A. (2020b). İkinci başlık. Dergi Adı, "
                "1(2), 11-20."
            ),
            authors=["Yılmaz"],
            year=2020,
            year_suffix="b",
        ),
    ]

    service = InternalCheckService(profile=TURKISH)
    result = service.check_text(body, refs)

    parenthetical = [
        c for c in result.citations
        if c.kind == CitationKind.PARENTHETICAL
    ]
    assert len(parenthetical) == 2, (
        f"expected 2 parenthetical citations, got {len(parenthetical)}; "
        f"unparsed={service.unparsed!r}"
    )
    assert sorted(c.year_suffix for c in parenthetical) == ["a", "b"]

    assert result.missing_references() == []
    assert result.uncited_references() == []

    

# ---------------------------------------------------------------------------
# Defect 4 — comma-separated years collapse to a single citation
# ---------------------------------------------------------------------------

def test_comma_separated_years_english():
    """
    "(Köhler, 1986, 2012)" is a legal APA construct meaning BOTH
    Köhler-1986 and Köhler-2012. On current code, _YEAR_RE.search
    returns only the first year, so a single citation for 1986 is
    emitted and 2012 is silently dropped.

    When the reference list contains both works, the 2012 reference
    is falsely reported as uncited.
    """
    body = "The pattern held across scales (Köhler, 1986, 2012)."
    refs = [
        Reference(
            raw_text=(
                "Köhler, R. (1986). Zur linguistischen Synergetik. "
                "Studienverlag Dr. N. Brockmeyer."
            ),
            authors=["Köhler"],
            year=1986,
        ),
        Reference(
            raw_text="Köhler, R. (2012). Quantitative syntax analysis. De Gruyter Mouton.",
            authors=["Köhler"],
            year=2012,
        ),
    ]

    service = InternalCheckService(profile=ENGLISH)
    result = service.check_text(body, refs)

    parenthetical = [
        c for c in result.citations
        if c.kind == CitationKind.PARENTHETICAL
    ]
    assert len(parenthetical) == 2, (
        f"expected 2 parenthetical citations (one per year), "
        f"got {len(parenthetical)}; "
        f"years={[c.year for c in parenthetical]!r}"
    )
    assert [c.year for c in parenthetical] == [1986, 2012], (
        f"expected years [1986, 2012] in order, "
        f"got {[c.year for c in parenthetical]!r}"
    )

    assert result.missing_references() == []
    assert result.uncited_references() == []


def test_comma_separated_years_turkish():
    """
    Turkish twin. "(Yılmaz, 2018, 2020)" must yield two citations.
    Same defect, exercised against the Turkish profile and a surname
    that requires Turkish-aware normalization on the reference side.
    """
    body = "Bu örüntü farklı ölçeklerde tutarlıdır (Yılmaz, 2018, 2020)."
    refs = [
        Reference(
            raw_text="Yılmaz, A. (2018). Birinci çalışma. Dergi Adı, 3(1), 1-10.",
            authors=["Yılmaz"],
            year=2018,
        ),
        Reference(
            raw_text="Yılmaz, A. (2020). İkinci çalışma. Dergi Adı, 4(2), 11-20.",
            authors=["Yılmaz"],
            year=2020,
        ),
    ]

    service = InternalCheckService(profile=TURKISH)
    result = service.check_text(body, refs)

    parenthetical = [
        c for c in result.citations
        if c.kind == CitationKind.PARENTHETICAL
    ]
    assert len(parenthetical) == 2, (
        f"expected 2 parenthetical citations (one per year), "
        f"got {len(parenthetical)}; "
        f"years={[c.year for c in parenthetical]!r}"
    )
    assert [c.year for c in parenthetical] == [2018, 2020]

    assert result.missing_references() == []
    assert result.uncited_references() == []


def test_comma_separated_years_does_not_misfire_on_pages():
    """
    Contract guard for the fix, not a bug-flag test. This test PASSES
    on current code and MUST STILL PASS after the comma-separated-year
    fix is applied.

    "(Smith, 2020, p. 1945)" is a citation of Smith-2020 with a page
    locator. 1945 is a page number, not a second year. A naive fix
    that treats every 4-digit number in the segment as a year would
    emit a spurious Smith-1945 citation, producing a false MISSING
    issue against a reference list that (correctly) has no Smith-1945.
    """
    body = "As noted previously (Smith, 2020, p. 1945), the effect is robust."
    refs = [
        Reference(
            raw_text="Smith, J. (2020). Some title. Journal of Examples, 1(1), 1-10.",
            authors=["Smith"],
            year=2020,
        )
    ]

    service = InternalCheckService(profile=ENGLISH)
    result = service.check_text(body, refs)

    parenthetical = [
        c for c in result.citations
        if c.kind == CitationKind.PARENTHETICAL
    ]
    assert len(parenthetical) == 1, (
        f"expected exactly 1 citation (Smith, 2020), "
        f"got {len(parenthetical)}; "
        f"years={[c.year for c in parenthetical]!r}"
    )
    assert parenthetical[0].year == 2020
    assert result.missing_references() == []
    assert result.uncited_references() == []