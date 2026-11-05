"""
Harman verification provider.

Converts TÜBİTAK ULAKBİM Harman records into ReferenceMatch objects.
Covers:

- Turkish Master's/PhD theses (YÖK National Thesis Center)
- DergiPark journals, including English- and German-language articles
  published in Turkish journals
- Turkish university institutional repositories

Because Harman aggregates a superset of TR Dizin, this provider is
placed before TrDizinProvider in the cascade. Its ``supports()``
deliberately does NOT reuse ``is_turkish_looking``: DergiPark hosts
many English- and German-language articles, and that filter would
silently exclude them.
"""

import json
import re

from models import (
    Provider,
    Reference,
    ReferenceMatch,
    ReferenceType,
)

from .harman_client import HarmanClient
from .provider import VerificationProvider


class HarmanProvider(VerificationProvider):
    """Verification provider using Harman metadata."""

    def __init__(self, client: HarmanClient | None = None) -> None:
        self.client = client if client is not None else HarmanClient()

    @property
    def name(self) -> str:
        return "harman"

    def supports(self, reference: Reference) -> bool:
        """
        Return True when querying Harman could plausibly help.

        - Pre-1900 references: Harman indexes nothing that old.
        - References without a title: Harman search is title-driven;
          a raw-text query full of URLs and access dates returns
          irrelevant hits. Fall through to the next provider.
        """
        if reference.year is not None and reference.year < 1900:
            return False
        return bool(reference.title or reference.book_title)

    def search(self, reference: Reference) -> list[ReferenceMatch]:
        query = (reference.title or reference.book_title or "").strip()
        if not query:
            return []

        # Harman's relevance engine is sensitive to query length: a
        # full reference title with a subtitle and Roman-numeral
        # tokens can return zero hits even when the record is indexed
        # and a shorter query ("İzmir Bölgesi Maden İşçiliği") finds
        # it. Try the full title first; if it produces no hits, fall
        # back to progressively shorter prefixes. The first variant
        # that returns hits wins, so behaviour for references whose
        # full title already works is unchanged.
        for variant in self._query_variants(query):
            try:
                payload = self.client.search(variant)
            except Exception:
                # A single broken provider must never crash the
                # pipeline. Mirrors the exception handling in
                # service.py. Fail fast on transport errors: retrying
                # five timed-out variants would multiply latency for
                # no benefit when Harman is unreachable.
                return []

            hits = (payload.get("hits") or {}).get("hits") or []
            if hits:
                return [self._convert_hit(hit) for hit in hits]

        return []

    @staticmethod
    def _query_variants(title: str) -> list[str]:
        """
        Return query strings to try against Harman, longest first.

        The full title is always tried first. If it returns no hits,
        shorter variants are tried in order:

        1. Subtitle head - everything before the first colon. This is
           the exact form that recovered the Keskin (2009) thesis
           after the full title returned zero hits.
        2. Prefixes of 10, 8, and 6 words (after replacing colons
           with spaces so punctuation does not fuse tokens).

        Duplicates are removed so the same query is never issued
        twice.
        """
        variants: list[str] = [title]

        if ":" in title:
            head = title.split(":", 1)[0].strip()
            if head and head not in variants:
                variants.append(head)

        words = title.replace(":", " ").split()
        for n in (10, 8, 6):
            if len(words) > n:
                prefix = " ".join(words[:n]).rstrip(",.;:")
                if prefix not in variants:
                    variants.append(prefix)

        return variants

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def _convert_hit(self, hit: dict) -> ReferenceMatch:
        source = hit.get("_source") or {}
        meta = source.get("metadata") or {}
        if isinstance(meta, str):
            # Harman occasionally returns metadata JSON-encoded.
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}

        institution = self._institution(source)
        doc_id = hit.get("_id") or hit.get("id") or ""
        slug = source.get("slug") or ""

        detail_url = ""
        if doc_id:
            detail_url = (
                "https://search.harman.ulakbim.gov.tr/tr/yayin/detay/"
                f"{doc_id}/{slug}"
            ).rstrip("/")

        return ReferenceMatch(
            provider=Provider.HARMAN,
            reference_type=self._reference_type(meta, institution),
            record_id=str(doc_id) if doc_id else None,
            title=self._title(meta, source),
            authors=self._authors(meta) or None,
            journal=self._journal(meta),
            publisher=institution,
            year=self._year(meta),
            url=detail_url or None,
        )

    @staticmethod
    def _title(meta: dict, source: dict) -> str | None:
        raw = (
            meta.get("title")
            or meta.get("dc:title")
            or source.get("title")
        )
        if isinstance(raw, list) and raw:
            value = str(raw[0]).strip()
        elif isinstance(raw, str):
            value = raw.strip()
        else:
            value = ""
        return value or None

    @staticmethod
    def _authors(meta: dict) -> list[str]:
        raw = (
            meta.get("creator")
            or meta.get("dc:creator")
            or meta.get("author")
            or []
        )
        if isinstance(raw, list):
            return [str(a).strip() for a in raw if str(a).strip()]
        if isinstance(raw, str) and raw.strip():
            return [raw.strip()]
        return []

    @staticmethod
    def _journal(meta: dict) -> str | None:
        """
        Extract journal/serial name from ``metadata["source"]``.

        Harman formats the citation as
        ``"<Journal> <Year> <Volume>(<Issue>), <Pages>"``. The journal
        name is everything before the first whitespace-delimited
        4-digit year. Returns None for non-serial records (theses,
        books) — their ``source`` has no year in that shape, so the
        regex does not match.
        """
        raw = meta.get("source")
        if isinstance(raw, list) and raw:
            raw = raw[0]
        if not isinstance(raw, str):
            return None
        text = raw.strip()
        m = re.search(r"\s+\d{4}\b", text)
        if not m:
            return None
        name = text[: m.start()].strip().rstrip(",.;")
        return name or None

    @staticmethod
    def _year(meta: dict) -> int | None:
        """
        Return the record's publication year.

        Harman exposes three year-bearing fields with different
        semantics:

        * ``publication_year``  — the actual publication year (int).
          Authoritative when present.
        * ``publication_date``  — the same year as an ISO string
          (``"2008-01-01T00:00:00"``). Secondary source.
        * ``date`` / ``originalDates`` — HARVEST timestamps from when
          Harman crawled the record (``["2026-10-23T…", "2026-10-23T…",
          "2008-…"]``). The first entry is *not* the publication year;
          it is the crawl date. Using it produced 2026 for a 2008
          article and 2019 for a 2018 article.

        Falls back to ``None`` rather than a harvest timestamp. A
        missing year skips the year weight in the matcher (score
        stays at its title+author value) — far better than feeding
        the matcher a confidently wrong year that demotes a correct
        match to Manual Review.
        """
        # 1. Explicit integer publication year.
        raw_year = meta.get("publication_year")
        if isinstance(raw_year, int):
            return raw_year
        if isinstance(raw_year, str):
            digits = raw_year.strip()
            if digits.isdigit() and len(digits) == 4:
                return int(digits)

        # 2. ISO publication date string.
        raw_date = meta.get("publication_date")
        if isinstance(raw_date, list) and raw_date:
            raw_date = raw_date[0]
        if isinstance(raw_date, str) and len(raw_date) >= 4:
            digits = "".join(ch for ch in raw_date[:4] if ch.isdigit())
            if len(digits) == 4:
                return int(digits)

        # 3. Fallback for records that lack ``publication_year`` and
        # ``publication_date`` (Harman is inconsistent here). Only
        # bare 4-digit years count as evidence in this branch:
        #
        #   * Arkan 2026       date: ['2026']             → 2026
        #   * Kahyaoğlu (real) date: ['2026-…','2026-…','2008-…']
        #                      → no bare years, rule 1 already
        #                      returned the right year from
        #                      publication_year
        #   * Harvest-only     date: ['2026-10-23T…']     → None
        #
        # The distinction is shape: a bare year is what repositories
        # write for a publication date, while an ISO timestamp
        # ("YYYY-MM-DDThh:mm:ss") is what Harman writes when it
        # records the harvest date. Every timestamp we have seen
        # carries a time component; no bare year does. So we accept
        # bare years, ignore timestamps, and refuse to guess when
        # the only evidence is timestamp-shaped. A missing year is
        # harmless — the matcher skips the year weight — while a
        # confidently wrong year demotes a correct match to Manual
        # Review.
        for field in ("date", "originalDates"):
            raw = meta.get(field)
            entries = raw if isinstance(raw, list) else [raw] if raw else []
            bare_years: set[int] = set()
            for entry in entries:
                s = str(entry).strip()
                if len(s) == 4 and s.isdigit():
                    bare_years.add(int(s))
            if len(bare_years) == 1:
                return bare_years.pop()

        return None

    @staticmethod
    def _institution(source: dict) -> str | None:
        """
        Human-readable repository/aggregator name.

        Harman returns ``repoNameAllFacet`` as a plain string in most
        records (e.g. "TR Dizin", "YÖK Ulusal Tez Merkezi") but as a
        list in some. Fall back to ``repo`` only if it is a string, so
        a dict-typed ``repo`` object never leaks into the display.
        """
        facet = source.get("repoNameAllFacet")
        if isinstance(facet, list) and facet:
            return str(facet[0]).strip() or None
        if isinstance(facet, str) and facet.strip():
            return facet.strip()

        repo = source.get("repo")
        if isinstance(repo, str) and repo.strip():
            return repo.strip()
        if isinstance(repo, dict):
            name = (
                repo.get("name")
                or repo.get("repoName")
                or repo.get("title")
            )
            if isinstance(name, str) and name.strip():
                return name.strip()
        return None

    @staticmethod
    def _reference_type(
        meta: dict,
        institution: str | None,
    ) -> ReferenceType:
        """
        Map a Harman record to an internal ReferenceType.

        Primary signal is ``metadata.originalType``, which uses the
        OpenAIRE vocabulary ("info:eu-repo/semantics/article",
        "info:eu-repo/semantics/doctoralThesis", ...). Fall back to the
        institution name only if ``originalType`` is absent, since that
        string is not standardised across repositories.
        """
        raw_types = meta.get("originalType") or []
        if isinstance(raw_types, str):
            raw_types = [raw_types]

        for raw in raw_types:
            low = str(raw).casefold()
            # Order matters: "bookpart" before "book", "article" before
            # "conference" (conference articles are sometimes typed as
            # both).
            if "article" in low or "journal" in low:
                return ReferenceType.JOURNAL_ARTICLE
            if "thesis" in low or "tez" in low:
                return ReferenceType.THESIS
            if "bookpart" in low or "chapter" in low:
                return ReferenceType.BOOK_CHAPTER
            if "book" in low:
                return ReferenceType.BOOK
            if "conference" in low or "proceeding" in low:
                return ReferenceType.CONFERENCE_PROCEEDING
            if "report" in low:
                return ReferenceType.REPORT

        # Fallback: institution heuristic (rarely hit).
        if institution:
            low = institution.casefold()
            if "tez" in low or "thesis" in low:
                return ReferenceType.THESIS
            if "dergi" in low or "journal" in low or "park" in low:
                return ReferenceType.JOURNAL_ARTICLE
        return ReferenceType.UNKNOWN