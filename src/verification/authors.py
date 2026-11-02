"""
Author similarity utilities.

Comparisons are format‑agnostic and tolerant of missing middle initials.
"""

import re
import unicodedata


def _parse_name(name: str) -> tuple[str, str] | None:
    """Return (lowercase_surname, first_initial) or None."""
    name = name.strip().rstrip(".,;:")
    name = re.sub(r"\s+", " ", name)
    # Turkish dotless i has no Unicode decomposition — must map explicitly.
    name = name.replace("ı", "i").replace("İ", "I")
    # Fold remaining Latin diacritics to ASCII: Ç→C, Ş→S, Ü→U, etc.
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))

    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        surname = parts[0]
        given = parts[1] if len(parts) > 1 else ""
    else:
        tokens = name.split()
        if len(tokens) == 1:
            surname = tokens[0]
            given = ""
        elif (
            len(tokens) >= 2
            and tokens[0].isupper()
            and tokens[0].isalpha()
            and not tokens[-1].isupper()
        ):
            # "SURNAME Given" — Turkish/European convention, e.g.
            # "ALPAY Gönül", "TANRIOKUR Cinuçen". Crossref and TrDizin
            # frequently return this form.
            # ``isalpha()`` excludes initials like "O.", "J.", "K." —
            # ``"O.".isupper()`` is True, and without this guard an
            # initial-first candidate "O. Wright" would be parsed as
            # surname "O." (score 0 against the real reference).
            surname = tokens[0]
            given = " ".join(tokens[1:])
        else:
            surname = tokens[-1]
            given = " ".join(tokens[:-1])

    surname = re.sub(r"[^a-z\-']", "", surname.lower())
    if not surname:
        return None

    given_clean = given.replace(".", " ").strip()
    first_initial = None
    if given_clean:
        first_token = given_clean.split()[0]
        first_initial = first_token[0].lower()

    return (surname, first_initial)


def author_similarity(
    reference_authors: list[str],
    candidate_authors: list[str],
) -> float:
    """
    Fraction of reference authors that match a candidate author
    (same surname and first initial).
    """
    if not reference_authors or not candidate_authors:
        return 0.0

    cand_set = set()
    for name in candidate_authors:
        parsed = _parse_name(name)
        if parsed and parsed[1] is not None:
            cand_set.add(parsed)

    if not cand_set:
        return 0.0

    matched = 0
    for name in reference_authors:
        parsed = _parse_name(name)
        if parsed and parsed[1] is not None:
            if parsed in cand_set:
                matched += 1

    return matched / len(reference_authors) if reference_authors else 0.0