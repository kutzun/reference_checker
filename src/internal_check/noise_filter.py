"""
Noise filter for internal citation checks.

Rejects parenthetical segments that are statistical or mathematical
expressions rather than citations. Examples of what this filter rejects:

    (M = 2.985)
    (SD = 1.0345)
    (t(38) = 2.45, p = .02)
    (F(2, 45) = 3.21, p < .05)
    (95% CI [1.2, 3.4])
    (n = 120)
    (r = .45, p < .001)
    (χ² = 5.67, df = 2)
    (2.985)
    (M = 2,985)            # Turkish decimal separator
    (2,985)                # bare Turkish decimal

The filter is deliberately conservative: it only rejects segments that
contain signals which cannot plausibly appear in a real citation. When
in doubt, it lets the segment through and relies on later stages of
the pipeline to handle it.

This module is dependency-free and has no knowledge of the rest of the
internal_check package, so it can be tested in isolation.
"""

import re


# Mathematical and statistical operators.
# A real citation never contains these.
_STAT_OPERATOR_RE = re.compile(r"[=<>≤≥≈±]")

# Greek letters commonly used in statistics (chi, beta, alpha, eta, rho,
# sigma, mu, and the rest of the Greek alphabet).
_GREEK_LETTER_RE = re.compile(
    r"["
    r"\u03b1-\u03c9"   # lowercase Greek
    r"\u0391-\u03a9"   # uppercase Greek
    r"]"
)

# Percent sign — "45% female", "95% CI", etc.
_PERCENT_RE = re.compile(r"%")

# English-format decimal number with two or more digits after the dot.
# Examples: 2.985, 1.0345, 0.001, 3.14
# Real citations do not contain these; years are integers, page numbers
# use hyphens, and volumes are usually integers.
_DECIMAL_RE = re.compile(r"\d+\.\d{2,}")

# Turkish-format decimal number: comma as decimal separator, with three
# or more digits after the comma. Examples: 2,985 / 1,0345 / 0,001.
#
# Three digits (not two) is deliberate. Turkish statistics report 3–4
# decimal places, while numeric citations like "(1, 23)" or "(1, 45)"
# have at most two digits after the comma. Requiring three digits
# catches statistics without rejecting realistic citation number lists.
_TURKISH_DECIMAL_RE = re.compile(r"\d+,\d{3,}")


def is_non_citation(text: str) -> bool:
    """
    Return True if *text* looks like statistical or mathematical noise.

    Args:
        text:
            A single parenthetical segment, e.g. the content between
            semicolons in ``(Smith, 2020; M = 2.985)``. Do not pass
            the entire parenthetical; split it first.

    Returns:
        True if the segment is almost certainly not a citation.
        False if it might be a citation (and should be passed to the
        citation extractor).
    """
    if not text:
        return True

    stripped = text.strip()
    if not stripped:
        return True

    if _STAT_OPERATOR_RE.search(stripped):
        return True

    if _GREEK_LETTER_RE.search(stripped):
        return True

    if _PERCENT_RE.search(stripped):
        return True

    if _DECIMAL_RE.search(stripped):
        return True

    if _TURKISH_DECIMAL_RE.search(stripped):
        return True

    return False


def filter_citations(segments: list[str]) -> list[str]:
    """
    Return only the segments that are not statistical noise.

    Convenience wrapper around :func:`is_non_citation` for the common
    case of filtering a list of already-split segments.
    """
    return [seg for seg in segments if not is_non_citation(seg)]