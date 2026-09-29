"""
Recorded responses from the Google Books API.

Endpoint:

    GET https://www.googleapis.com/books/v1/volumes?q={query}

Response shape (documented at
https://developers.google.com/books/docs/v1/reference/volumes):

    kind            "books#volumes"
    totalItems      integer
    items[]         list of Volume resources

Each Volume has:

    id              Google Books volume ID
    volumeInfo      {title, subtitle, authors[], publisher,
                     publishedDate, industryIdentifiers[],
                     pageCount, language, ...}
    saleInfo        pricing and availability
    accessInfo      viewability

NOTE: This fixture is constructed from the documented structure.
Re-record with a live keyed call to confirm exact field values.
"""

# Source: constructed from documented Volume resource structure.
# Query that would produce this: q=intitle:İnsan+ve+değerleri+inauthor:Kuçuradi
INSAN_VE_DEGERLERI = {
    "kind": "books#volumes",
    "totalItems": 1,
    "items": [
        {
            "kind": "books#volume",
            "id": "abc123XYZ",
            "etag": "test",
            "selfLink": (
                "https://www.googleapis.com/books/v1/volumes/abc123XYZ"
            ),
            "volumeInfo": {
                "title": "İnsan ve değerleri",
                "authors": ["İoanna Kuçuradi"],
                "publisher": "Türkiye Felsefe Kurumu",
                "publishedDate": "1998",
                "industryIdentifiers": [
                    {"type": "ISBN_10", "identifier": "9757744017"},
                    {"type": "ISBN_13", "identifier": "9789757744016"},
                ],
                "pageCount": 180,
                "printType": "BOOK",
                "language": "tr",
                "infoLink": (
                    "https://books.google.com/books?id=abc123XYZ"
                ),
                "canonicalVolumeLink": (
                    "https://books.google.com/books/about/"
                    "%C4%B0nsan_ve_de%C4%9Ferleri.html?id=abc123XYZ"
                ),
            },
            "saleInfo": {
                "country": "TR",
                "saleability": "NOT_FOR_SALE",
                "isEbook": False,
            },
            "accessInfo": {
                "country": "TR",
                "viewability": "NO_PAGES",
                "embeddable": False,
                "publicDomain": False,
            },
        }
    ],
}

# Source: constructed from documented Volume resource structure.
# Query that would produce this: q=intitle:Masal+inauthor:Günay
MASAL_GUNAY = {
    "kind": "books#volumes",
    "totalItems": 1,
    "items": [
        {
            "kind": "books#volume",
            "id": "def456UVW",
            "etag": "test",
            "selfLink": (
                "https://www.googleapis.com/books/v1/volumes/def456UVW"
            ),
            "volumeInfo": {
                "title": "Masal",
                "authors": ["Umur Günay"],
                "publisher": "Türk Kültürünü Araştırma Enstitüsü",
                "publishedDate": "1992",
                "industryIdentifiers": [
                    {"type": "ISBN_10", "identifier": "9754567890"},
                ],
                "pageCount": 321,
                "printType": "BOOK",
                "language": "tr",
            },
            "saleInfo": {
                "country": "TR",
                "saleability": "NOT_FOR_SALE",
                "isEbook": False,
            },
            "accessInfo": {
                "country": "TR",
                "viewability": "NO_PAGES",
                "embeddable": False,
                "publicDomain": False,
            },
        }
    ],
}

# An empty result set, for testing no-match behavior.
EMPTY_RESPONSE = {
    "kind": "books#volumes",
    "totalItems": 0,
}