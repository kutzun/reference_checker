"""
Reference matching logic.

Scores candidate matches against parsed references using an evidence‑weighted
average. Missing metadata reduces the total weight of evidence, not the score.
Exact identifier matches (DOI, ISBN) always yield a score of 1.0.
"""

from models import Reference, ReferenceMatch, ReferenceType

from .authors import author_similarity
from .similarity import token_similarity


class ReferenceMatcher:
    """
    Calculates similarity between a reference and a candidate match.
    """

    def score(self, reference: Reference, match: ReferenceMatch) -> float:
        """
        Return a confidence score in [0, 1].

        * Exact DOI or ISBN match → 1.0.
        * Otherwise, a weighted average of the available evidence.
        """
        # ----- Exact identifier matches ---------------------------------
        # A DOI that resolves is not proof that the reference is correct:
        # an AI-fabricated DOI can point at a real paper on an unrelated
        # topic. Compute title similarity first, and refuse to verify if
        # the DOI's title has nothing to do with the reference's title.
        if (
            reference.doi
            and match.doi
            and reference.doi.lower() == match.doi.lower()
        ):
            match.doi_match = True

            title_sim = None
            if reference.title and match.title:
                title_sim = token_similarity(reference.title, match.title)
                match.title_similarity = title_sim

            if title_sim is not None and title_sim < 0.3:
                # DOI resolves to a different paper. Score 0 so the
                # cascade continues and this match cannot verify.
                match.evidence_weight = 1.0
                match.overall_score = 0.0
                return 0.0

            match.evidence_weight = 1.0
            match.overall_score = 1.0
            return 1.0

        if (
            reference.isbn
            and match.isbn
            and reference.isbn.replace("-", "")
            == match.isbn.replace("-", "")
        ):
            match.evidence_weight = 1.0
            match.overall_score = 1.0
            return 1.0

        # ----- Evidence‑based weighted average ---------------------------
        weighted_sum = 0.0
        total_weight = 0.0

        # Title (weight 0.5)
        # For a book chapter, the candidate returned by every provider
        # is the book itself — its "title" field holds the book title,
        # not the chapter title. Compare the reference's book_title
        # against it; comparing the chapter title produces a low score
        # for a correct match.
        is_chapter = reference.reference_type == ReferenceType.BOOK_CHAPTER
        title_for_compare = (
            reference.book_title if is_chapter else reference.title
        )
        if title_for_compare and match.title:
            match.title_similarity = token_similarity(
                title_for_compare, match.title
            )
            w = 0.5
            weighted_sum += match.title_similarity * w
            total_weight += w

        # Book title (weight 0.15)
        if reference.book_title and match.book_title:
            book_sim = token_similarity(
                reference.book_title, match.book_title
            )
            w = 0.15
            weighted_sum += book_sim * w
            total_weight += w
            match.book_title_similarity = book_sim

        # Authors (weight 0.3)
        # For a book chapter, the chapter author is not the book
        # author; comparing them penalises every correct match. Skip
        # the author signal entirely for chapters.
        if (
            not is_chapter
            and reference.authors
            and match.authors
        ):
            match.author_similarity = author_similarity(
                reference.authors, match.authors
            )
            w = 0.3
            weighted_sum += match.author_similarity * w
            total_weight += w

        # Editors (weight 0.05)
        if reference.editors and match.editors:
            editor_sim = author_similarity(
                reference.editors, match.editors
            )
            w = 0.05
            weighted_sum += editor_sim * w
            total_weight += w
            match.editor_similarity = editor_sim

        # Year (weight 0.2) – positive evidence only (mismatch ignored)
        if reference.year is not None and match.year is not None:
            if reference.year == match.year:
                match.year_match = True
                w = 0.2
                weighted_sum += 1.0 * w
                total_weight += w
            else:
                match.year_match = False

        # Publisher (weight 0.05)
        if reference.publisher and match.publisher:
            pub_sim = token_similarity(
                reference.publisher, match.publisher
            )
            w = 0.05
            weighted_sum += pub_sim * w
            total_weight += w
            match.publisher_similarity = pub_sim

        # ----- Final score -----------------------------------------------
        if total_weight > 0:
            score = weighted_sum / total_weight
        else:
            score = 0.0

        score = min(score, 1.0)

        # Demote title-only containment false positives: short ref title
        # vs much longer candidate title, with ≥3-year gap. Catches
        # "Locating the Field: …" matching "The Discipline and Practice
        # of Qualitative Research" (2018 vs 2025). Does not touch correct
        # reprints (Δyear small), long ref titles (Wright 1978/1994), or
        # short candidates — all Verified on 5.docx remain Verified.
        if (
            score >= 0.7
            and reference.title and match.title
            and reference.year and match.year
            and abs(reference.year - match.year) >= 3
        ):
            if len(reference.title.split()) <= 8 and len(match.title.split()) >= 12:
                score *= 0.6

        match.evidence_weight = total_weight
        match.overall_score = score
        self._log_containment_signature(reference, match, score)
        return score

    def _log_containment_signature(self, reference, match, score):
        """Tier-1 diagnostic: print matches whose title similarity is
        likely driven by token_similarity's symmetric containment
        (containment > jaccard). Purely observational — no score change.
        Uses print() to stderr because root logger may already be
        configured by imported modules, making logging.basicConfig a no-op.
        """
        import sys
        if not getattr(match, "title_similarity", None):
            return
        if match.title_similarity < 0.7:
            return
        rt = set((reference.title or "").lower().split())
        ct = set((match.title or "").lower().split())
        if not rt or not ct:
            return
        min_size = min(len(rt), len(ct))
        if min_size < 3:
            return
        containment = len(rt & ct) / min_size
        jaccard = len(rt & ct) / len(rt | ct) if (rt | ct) else 0.0
        if containment <= jaccard:
            return
        print(
            f"containment-driven: score={score:.3f} "
            f"title_sim={match.title_similarity:.3f} "
            f"ref_tok={len(rt)} cand_tok={len(ct)} "
            f"ref_year={reference.year} cand_year={match.year} "
            f"ref={reference.title!r} cand={match.title!r}",
            file=sys.stderr,
        )