"""
PubMed API client.

Uses NCBI E-utilities (keyless) to search PubMed.

Search strategy:
  1. If the reference has a DOI, search the [doi] field (most precise).
  2. Otherwise search [Title] constrained by first author, but only when
     the first author is in "Family, Given" form and the surname is
     therefore unambiguous.
  3. Always fall back to a [Title]-only search.

NCBI asks that automated clients identify themselves. `email` and
`tool` are optional but recommended; both are sent on every request.
"""

import requests

from models import Reference

from .exceptions import VerificationProviderError


class PubMedClient:
    """
    Lightweight PubMed HTTP client built on NCBI E-utilities.

    Keyless. Without a key, NCBI rate-limits to ~3 requests/second.
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    MAX_RESULTS = 5

    def __init__(
        self,
        timeout: int = 10,
        email: str | None = None,
        tool: str = "reference-checker",
    ) -> None:
        self.timeout = timeout
        self.email = email
        self.tool = tool

    def search(self, reference: Reference) -> list[dict]:
        """
        Search PubMed for records matching a reference.

        Returns:
            List of esummary record dicts. Empty if no matches.
        """
        pmids = self._find_pmids(reference)
        if not pmids:
            return []
        return self._esummary(pmids)

    # -- query building -----------------------------------------------------

    def _find_pmids(self, reference: Reference) -> list[str]:
        if reference.doi:
            pmids = self._esearch(self._doi_term(reference.doi))
            if pmids:
                return pmids

        if not reference.title:
            return []

        surname = self._first_author_surname(reference)
        if surname:
            pmids = self._esearch(self._title_term(reference, surname))
            if pmids:
                return pmids

        return self._esearch(self._title_term(reference, surname=None))

    @staticmethod
    def _doi_term(doi: str) -> str:
        return f'"{doi.strip()}"[doi]'

    @staticmethod
    def _title_term(reference: Reference, surname: str | None) -> str:
        title = reference.title.strip().strip('"')
        term = f'"{title}"[Title]'
        if surname:
            term += f' AND "{surname}"[Author]'
        return term

    @staticmethod
    def _first_author_surname(reference: Reference) -> str | None:
        """
        Extract the first author's surname when it is unambiguous.

        Only "Family, Given" form is trusted; the surname is everything
        before the first comma. Other forms ("Given Family", "Family
        Initials") are skipped rather than guessed, because a wrong
        constraint guarantees a miss while no constraint merely
        broadens the search.
        """
        if not reference.authors:
            return None
        author = reference.authors[0].strip()
        if "," not in author:
            return None
        surname = author.split(",", 1)[0].strip()
        return surname or None

    # -- HTTP ---------------------------------------------------------------

    def _polite_params(self) -> dict:
        params: dict = {"tool": self.tool}
        if self.email:
            params["email"] = self.email
        return params

    def _esearch(self, term: str) -> list[str]:
        params = {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "retmax": self.MAX_RESULTS,
            **self._polite_params(),
        }
        data = self._get("esearch.fcgi", params)
        return data.get("esearchresult", {}).get("idlist", [])

    def _esummary(self, pmids: list[str]) -> list[dict]:
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
            **self._polite_params(),
        }
        data = self._get("esummary.fcgi", params)
        result = data.get("result", {})
        uids = result.get("uids", [])
        return [result[uid] for uid in uids if uid in result]

    def _get(self, path: str, params: dict) -> dict:
        try:
            response = requests.get(
                f"{self.BASE_URL}/{path}",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise VerificationProviderError(
                "PubMed request failed."
            ) from exc
        except ValueError as exc:
            raise VerificationProviderError(
                "Invalid PubMed response."
            ) from exc