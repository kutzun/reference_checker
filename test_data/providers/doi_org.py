"""
Recorded responses from doi.org for use in tests.

Each entry maps a DOI to the CSL-JSON dict returned by:

    GET https://doi.org/{DOI}
    Accept: application/vnd.citationstyles.csl+json

Responses are trimmed of bulky fields (the Crossref reference list,
abstract, link array) but preserve every field the DoiOrgProvider
reads. Do not fabricate — every fixture here must come from a real
curl request, documented in the comment above each entry.
"""

# Source: curl -LH "Accept: application/vnd.citationstyles.csl+json" \
#             https://doi.org/10.1108/JIMA-08-2019-0171
# Recorded: 2026-09-28
ALHARBI_2022 = {
    "DOI": "10.1108/jima-08-2019-0171",
    "type": "journal-article",
    "title": (
        "Can opinion leaders through Instagram influence organic food "
        "purchase behaviour in Saudi Arabia?"
    ),
    "author": [
        {"given": "Ahlam Ibrahim", "family": "Al-Harbi"},
        {"given": "Nada Saleh", "family": "Badawi"},
    ],
    "container-title": "Journal of Islamic Marketing",
    "volume": "13",
    "issue": "6",
    "page": "1312-1333",
    "publisher": "Emerald",
    "issued": {"date-parts": [[2021, 2, 11]]},
    "published-print": {"date-parts": [[2022, 4, 22]]},
    "published-online": {"date-parts": [[2021, 2, 11]]},
    "URL": "http://dx.doi.org/10.1108/JIMA-08-2019-0171",
    "language": "en",
    "ISSN": ["1759-0833", "1759-0841"],
}