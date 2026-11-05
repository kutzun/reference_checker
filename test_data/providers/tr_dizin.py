"""
Recorded responses from the TR Dizin search API.

The endpoint:

    GET https://search.trdizin.gov.tr/api/defaultSearch/publication/
        ?q={query}&order=relevance-DESC&page=1&limit=N

Response shape (only fields TrDizinProvider reads are kept):

    _source.abstracts[]   list of {title, language, id}
    _source.authors[]     list of {name, orcid, order}
    _source.journal.name
    _source.issue         {volume, number, year}
    _source.publicationYear
    _source.doi
    _source.startPage, _source.endPage
    _source.docType       "PAPER" or "PROJECT"
    _source.publicationType

NOTE: There is no top-level title. The title lives inside abstracts[]
      keyed by language. Do not use _source.orderTitle — it is a
      search-index artifact with spaces removed.
"""

# Source: curl "https://search.trdizin.gov.tr/api/defaultSearch/publication/?q=masal&order=relevance-DESC&page=1&limit=2"
# Recorded: 2026-09-28
# Hit 1 of 2 (no DOI).
MASAL_AI = {
    "id": 482283,
    "abstracts": [
        {
            "id": 840156,
            "language": "TUR",
            "title": "YAPAY ZEKÂNIN YARATTIĞI MASAL: PRENSES İLE TİLKİ",
        },
        {
            "id": 20371,
            "language": "ENG",
            "title": (
                "THE FAIRY TALE CREATED BY ARTIFICIAL INTELLIGENCE: "
                "THE PRINCESS AND THE FOX"
            ),
        },
    ],
    "authors": [
        {"name": "N. Gamze Ilıcak", "orcid": "0000-0002-1193-5384", "order": 1},
        {"name": "KEMAL ÇİNKO", "orcid": "0000-0002-6019-3313", "order": 2},
    ],
    "journal": {
        "eissn": "2147-0146",
        "issn": "",
        "name": "Uluslararası Türkçe Edebiyat Kültür Eğitim (TEKE) Dergisi",
    },
    "issue": {"volume": "10", "number": "2", "year": "2021"},
    "publicationYear": 2021,
    "doi": None,
    "startPage": "703",
    "endPage": "719",
    "docType": "PAPER",
    "publicationType": "RESEARCH",
    "language": "TUR",
}

# Hit 2 of 2 (with DOI).
MASAL_PROPP = {
    "id": 326006,
    "abstracts": [
        {
            "id": 573431,
            "language": "TUR",
            "title": (
                "Masal Uyarlamalarının Vladimir Propp'un Yaklaşımı ile "
                "İncelenmesi “Pamuk Prenses” Masalı Örneği*"
            ),
        },
        {
            "id": 199964,
            "language": "ENG",
            "title": (
                "Analysis of Fairy Tale Adaptations by Vladimir Propp's "
                "Approach Based on The Example “Snow White”"
            ),
        },
    ],
    "authors": [
        {"name": "Derya Perk", "orcid": "0000-0002-1283-4315", "order": 1},
    ],
    "journal": {
        "eissn": "2630-5976",
        "issn": "1301-5737",
        "name": "Hacettepe Üniversitesi Edebiyat Fakültesi Dergisi",
    },
    "issue": {"volume": "36", "number": "1", "year": "2019"},
    "publicationYear": 2019,
    "doi": "10.32600/huefd.454263",
    "startPage": "122",
    "endPage": "132",
    "docType": "PAPER",
    "publicationType": "RESEARCH",
    "language": "TUR",
}