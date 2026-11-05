"""
Captured Harman API response fixtures.

Real shape, captured 2026-11-04, from:
    https://search.harman.ulakbim.gov.tr/api/defaultSearch/publication/

Each fixture is the raw JSON payload the HarmanClient receives. The
fixtures below cover the cases we care about:

    ARKAN_2026_HIT                 DergiPark article (TR Dizin repo)
    UZUN_2016_EMPTY                article not in Harman (empty hits)
    THESIS_HIT                     YÖK Tez-style record (doctoralThesis)
    ARKAN_2026_METADATA_AS_STRING  metadata serialized as JSON string
"""

ARKAN_2026_HIT = {
    "hits": {
        "total": 1,
        "hits": [
            {
                "_id": "tmdhhahs_5qcy1nh81zjd34hk9p5vkn7cn926",
                "_source": {
                    "defaultSearchField": (
                        "Methodologische Reflexion Qualitativer "
                        "Forschungsansätze im Kommunaldolmetschen: Eine "
                        "Szenario-gestützte Analyse Die Dolmetschforschung "
                        "ist seit ihren Anfängen durch den Einfluss "
                        "verschiedener Disziplinen geprägt."
                    ),
                    "metadata": {
                        "originalType": ["info:eu-repo/semantics/article"],
                        "source": [
                            "Trakya Üniversitesi Sosyal Bilimler Dergisi "
                            "2026 28(1), 44 - 58"
                        ],
                        "type": ["c_2df8fbb1"],
                        "title": [
                            "Methodologische Reflexion Qualitativer "
                            "Forschungsansätze im Kommunaldolmetschen: "
                            "Eine Szenario-gestützte Analyse"
                        ],
                        "creator": ["Yelda Arkan"],
                        "date": ["2026"],
                    },
                    "repo": {"name": "TR Dizin"},
                    "repoIdAllFacet": "tmdhhahs",
                    "repoNameAllFacet": "TR Dizin",
                    "slug": "",
                },
            }
        ],
    }
}


UZUN_2016_EMPTY = {
    "hits": {
        "total": 0,
        "hits": [],
    }
}


THESIS_HIT = {
    "hits": {
        "total": 1,
        "hits": [
            {
                "_id": "yoktez_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "_source": {
                    "defaultSearchField": (
                        "İkinci dil olarak Türkçe öğretiminde "
                        "kültürel unsurların yeri"
                    ),
                    "metadata": {
                        "originalType": [
                            "info:eu-repo/semantics/doctoralThesis"
                        ],
                        "source": [],
                        "type": ["c_2df8fbb1"],
                        "title": [
                            "İkinci dil olarak Türkçe öğretiminde "
                            "kültürel unsurların yeri"
                        ],
                        "creator": ["Ayşe Yılmaz"],
                        "date": ["2019"],
                    },
                    "repo": {"name": "YÖK Ulusal Tez Merkezi"},
                    "repoIdAllFacet": "yoktez",
                    "repoNameAllFacet": "YÖK Ulusal Tez Merkezi",
                    "slug": "",
                },
            }
        ],
    }
}


# JSON-encoded metadata shape — Harman occasionally serialises it as a
# string instead of an object. Kept small; only the fields the provider
# reads are populated.
ARKAN_2026_METADATA_AS_STRING = {
    "hits": {
        "total": 1,
        "hits": [
            {
                "_id": "tmdhhahs_5qcy1nh81zjd34hk9p5vkn7cn926",
                "_source": {
                    "metadata": (
                        '{"originalType": ["info:eu-repo/semantics/article"], '
                        '"title": ["Methodologische Reflexion Qualitativer '
                        'Forschungsansätze im Kommunaldolmetschen: Eine '
                        'Szenario-gestützte Analyse"], '
                        '"creator": ["Yelda Arkan"], "date": ["2026"], '
                        '"source": ["Trakya Üniversitesi Sosyal Bilimler '
                        'Dergisi 2026 28(1), 44 - 58"]}'
                    ),
                    "repo": {"name": "TR Dizin"},
                    "repoNameAllFacet": "TR Dizin",
                    "slug": "",
                },
            }
        ],
    }
}