"""
Ground-truth expectations for a first batch of real references.

Each entry is a dict with these keys:

    id            Short stable key, author+year, lowercase, no spaces.
    raw_text      Exactly the reference string as it appears in the source,
                  INCLUDING joins ("KurumuYayınları"), stray spaces before
                  commas, hard-wraps (kept as \n), and typos. This is the
                  end-user's input, so we do not clean it.
    type          A ReferenceType member VALUE (as a plain string).
    first_author  The result of normalize_author_name() on the first author.
                  Lowercase, diacritics stripped, only the surname before
                  the comma is kept. For institutional authors, keep the
                  full name (e.g. "turk dil kurumu").
    year          A string, not an int. Preserves suffixes like "2019b".
    title         The human-correct title, no trailing period. This is the
                  TARGET, not a description of current parser behavior.

New keys may be added as extraction rules expand. Old keys must not be
removed without a migration note in DECISIONS.md.

This file is data only. No imports, no logic, no fixtures framework yet.
"""

CASES = [
    # 1. Journal article with DOI, quoted title, mixed APA/Harvard.
    #    Raw joins: "Instagraminfluence", "IslamicMarketing".
    {
        "id": "alharbi2022",
        "raw_text": (
            'Al-Harbi, A.I. & Badawi, N.S. (2022), "Can opinion leaders through '
            'Instagraminfluence organic food purchase behaviour in Saudi Arabia?", '
            'Journal of IslamicMarketing, Vol. 13 No. 6, pp. 1312-1333. '
            'https://doi.org/10.1108/JIMA-08-2019-0171'
        ),
        "type": "journal_article",
        "journal": "Journal of IslamicMarketing",
        "volume": "13",
        "issue": "6",
        "pages": "1312-1333",        
        "first_author": "al harbi",
        "year": "2022",
        "title": (
            "Can opinion leaders through Instagraminfluence organic food "
            "purchase behaviour in Saudi Arabia?"
        ),
    },

    # 2. Book chapter in an edited volume.
    #    Raw joins: "RetailIndustry", "Handbook ofResearch", "RecoveringEconomy".
    {
        "id": "kasemsap2016",
        "raw_text": (
            'Kasemsap, K. (2016). Reviewing the Role of Store Brands in the '
            'Global RetailIndustry. In M. Gómez-Suárez & M. Martínez-Ruiz (Eds.), '
            'Handbook ofResearch on Strategic Retailing of Private Label Products '
            'in a RecoveringEconomy (pp. 28-53). IGI Global. '
            'https://doi.org/10.4018/978-1-5225-0220-3.ch002'
        ),
        "type": "book_chapter",
        "first_author": "kasemsap",
        "year": "2016",
        "title": (
            "Reviewing the Role of Store Brands in the Global RetailIndustry"
        ),
        "pages": "28-53",
        "publisher": "IGI Global",
    },

    # 3. Institutional report with access date.
    #    Raw quirks: "Deep Change,https://" (no space), "Date:10.09.2024".
    {
        "id": "iata2024",
        "raw_text": (
            'IATA, (2024), Global Outlook for Air Transport Deep Change,'
            'https://www.iata.org/en/iata-repository/publications/economic-reports/'
            'global-outlook-for-air-transport-june-2024-report/, '
            'Accessed Date:10.09.2024'
        ),
        "type": "report",
        "first_author": "iata",
        "year": "2024",
        "title": "Global Outlook for Air Transport Deep Change",
    },

    # 4. Journal article, ampersand separator, no DOI.
    #    Raw quirks: "itsrelationships", " ,psychosocial", "&behavior".
    {
        "id": "chen2008",
        "raw_text": (
            "Chen, Y.-F., & Peng, S. S. (2008). University students' Internet use "
            "and itsrelationships with academic performance, interpersonal "
            "relationships ,psychosocial adjustment, and self-evaluation. "
            "Cyberpsychology &behavior, 11(4), 467-469."
        ),
        "type": "journal_article",
        "journal": "Cyberpsychology &behavior",
        "volume": "11",
        "issue": "4",
        "pages": "467-469",                
        "first_author": "chen",
        "year": "2008",
        "title": (
            "University students' Internet use and itsrelationships with "
            "academic performance, interpersonal relationships ,psychosocial "
            "adjustment, and self-evaluation"
        ),
    },

    # 5. Turkish book, edition note in parentheses.
    #    Raw join: "KurumuYayınları".
    {
        "id": "kucuradi1998",
        "raw_text": (
            "Kuçuradi, İ. (1998). İnsan ve değerleri (2. baskı). "
            "Türkiye Felsefe KurumuYayınları."
        ),
        "type": "book",
        "first_author": "kucuradi",
        "year": "1998",
        "title": "İnsan ve değerleri",
        "publisher": "Türkiye Felsefe KurumuYayınları",
    },

    # 6. Newspaper web article, quoted word inside title, Turkish access date.
    #    Raw joins: "themetaverse", "worried.Toronto", "2025.https://".
    {
        "id": "alang2021",
        "raw_text": (
            'Alang, N. (2021, October 23). Facebook wants to move to '
            '"themetaverse" — here\'s what that is, and why you should be worried.'
            'Toronto Star. Erişim Tarihi: 12 Temmuz 2025.'
            'https://www.thestar.com/business/opinion/2021/10/23/facebook-wants-'
            'to-move-to-the-metaverse-heres-what-that-is-and-why-you-should-be-'
            'worried.html'
        ),
        "type": "web",
        "first_author": "alang",
        "year": "2021",
        "title": (
            'Facebook wants to move to "themetaverse" — here\'s what that is, '
            "and why you should be worried"
        ),
    },

    # 7. Translated book.
    #    Raw join: "Çev.).Librairie".
    {
        "id": "bombaci1968",
        "raw_text": (
            "Bombaci, A. (1968). Histoire de la littérature turque "
            "(I. Melikoff, Çev.).Librairie C. Klincksieck."
        ),
        "type": "book",
        "first_author": "bombaci",
        "year": "1968",
        "title": "Histoire de la littérature turque",
        "publisher": "Librairie C. Klincksieck",
    },

    # 8. Institutional author web entry, DUPLICATED in the source paste.
    #    Kept as-is: two entries back to back in one string.
    {
        "id": "tdk2024",
        "raw_text": (
            "Türk Dil Kurumu. (2024). Çağla-. https://sozluk.gov.tr/ "
            "Türk Dil Kurumu.(2024). Çağla-. https://sozluk.gov.tr/"
        ),
        "type": "web",
        "first_author": "turk dil kurumu",
        "year": "2024",
        "title": "Çağla-",
    },

    # 9. Turkish journal article, colon in title.
    #    Raw join: "Fetihve".
    {
        "id": "koc2021",
        "raw_text": (
            "Koç, Â. (2021). Halkın diliyle seslenmek: Yunus Emre'de göç kavramı. "
            "Fetihve Medeniyet, 1(2), 116–125. "
            "www.eskisehir.gov.tr/kurumlar/eskisehir.gov.tr/Dergi/"
            "dergi_2021_nisan.pdf"
        ),
        "type": "journal_article",
        "journal": "Fetihve Medeniyet",
        "volume": "1",
        "issue": "2",
        "pages": "116–125",        
        "first_author": "koc",
        "year": "2021",
        "title": "Halkın diliyle seslenmek: Yunus Emre'de göç kavramı",
    },

    # 10. Turkish book chapter, volume + page in parentheses.
    #     Raw join: "TürkKültürünü".
    {
        "id": "gunay1992",
        "raw_text": (
            "Günay, U. (1992). Masal. In Türk Dünyası El Kitabı (Cilt 3, s. 321). "
            "TürkKültürünü Araştırma Enstitüsü Yayınları."
        ),
        "type": "book_chapter",
        "first_author": "gunay",
        "year": "1992",
        "title": "Masal",
        "publisher": "TürkKültürünü Araştırma Enstitüsü Yayınları",
    },

    # 11. Turkish master's thesis with bracketed metadata.
    #     Raw joins: "vedeğerlendirilmesi", "UlusalTez".
    {
        "id": "kara2017",
        "raw_text": (
            "Kara, E. (2017). Türk destanlarında Şamanistik unsurların tespiti "
            "vedeğerlendirilmesi [Yüksek lisans tezi, Cumhuriyet Üniversitesi]. "
            "YÖK UlusalTez Merkezi. "
            "https://tez.yok.gov.tr/UlusalTezMerkezi/tezSorguSonucYeni.jsp"
        ),
        "type": "thesis",
        "first_author": "kara",
        "year": "2017",
        "title": (
            "Türk destanlarında Şamanistik unsurların tespiti "
            "vedeğerlendirilmesi"
        ),
    },

    # 12. YouTube video, Turkish date, bracketed media type.
    #     Raw join: "düğünyaptıkları".
    {
        "id": "erin2019",
        "raw_text": (
            "Erin, İ. (2019, Temmuz 23). Cinleri gören Dursun Dayı ile cinlerin "
            "düğünyaptıkları dereye gittik–paranormal olaylar [Video]. YouTube. "
            "https://www.youtube.com/watch?v=MU9IKWNXTwA&ab_channel=izzeterin"
        ),
        "type": "video",
        "first_author": "erin",
        "year": "2019",
        "title": (
            "Cinleri gören Dursun Dayı ile cinlerin düğünyaptıkları dereye "
            "gittik–paranormal olaylar"
        ),
    },

    # 13. Institutional web entry, Turkish month, English "Retrieved".
    #     Raw hard-wraps kept as \n: "Süreli\nYayınlar", "https://\nilanbis".
    {
        "id": "bik2018",
        "raw_text": (
            "Basın İlan Kurumu. (2018, Ocak). Resmî İlan ve Resmî Reklam Alan Süreli\n"
            "Yayınlar Listesi. Basın İlan Kurumu. Retrieved March 22, 2025, "
            "from https://\nilanbis.bik.gov.tr/Uygulamalar/AylikListe"
        ),
        "type": "web",
        "first_author": "basin ilan kurumu",
        "year": "2018",
        "title": "Resmî İlan ve Resmî Reklam Alan Süreli Yayınlar Listesi",
    },

    # 14. Web article, Turkish date, quoted word in title.
    #     Raw hard-wraps: "Türkiye’de\n“beka”", "https://medyascope.\ntv".
    {
        "id": "buyukbayrak2024",
        "raw_text": (
            "Büyükbayrak, B. (2024, Şubat 26). 2019’dan 2024 seçimlerine: "
            "Türkiye’de\n“beka” söylemi. Retrieved March 31, 2025, from "
            "https://medyascope.\ntv/2024/02/26/2019dan-2024-secimlerine-"
            "turkiyede-beka-soylemi/"
        ),
        "type": "web",
        "first_author": "buyukbayrak",
        "year": "2024",
        "title": "2019’dan 2024 seçimlerine: Türkiye’de “beka” söylemi",
    },

    # 15. Web report from an association.
    #     Raw join: "yansımaları.Dijital".
    #     Raw hard-wrap: "https://\nwww.newslabturkey.org".
    #     Raw joins inside URL: "GAZETEMANSETLERINDE", "SONUCLARININ".
    {
        "id": "cakici2024",
        "raw_text": (
            "Çakıcı, Z. (2024). Gazete manşetlerinde yerel seçim sonuçlarının "
            "yansımaları.Dijital Medya Araştırmaları Derneği. Retrieved "
            "August 16, 2025, from https://\n"
            "www.newslabturkey.org/wp-content/uploads/2024/05/"
            "RH-34-GAZETEMANSETLERINDE-YEREL-SECIM-SONUCLARININ-YANSIMALARI.pdf"
        ),
        "type": "web",
        "first_author": "cakici",
        "year": "2024",
        "title": "Gazete manşetlerinde yerel seçim sonuçlarının yansımaları",
    },

    # 16. Institutional news entry, quoted word in title.
    #     Raw hard-wraps: "Kılıçdaroğlu\ndönemi", "2025,\nfrom".
    #     Raw join in URL: "genelbaskan".
    {
        "id": "euronews2023",
        "raw_text": (
            "Euronews. (2023, Kasım 4). CHP’de “değişim” kurultayı: 13 yıllık "
            "Kılıçdaroğlu\ndönemi kapandı, yeni Genel Başkan Özgür Özel. "
            "Retrieved March 27, 2025,\nfrom "
            "https://tr.euronews.com/2023/11/04/chp-38-olagan-kurultayi-yeni-"
            "genelbaskan-ve-parti-meclisi"
        ),
        "type": "web",
        "first_author": "euronews",
        "year": "2023",
        "title": (
            "CHP’de “değişim” kurultayı: 13 yıllık Kılıçdaroğlu dönemi kapandı, "
            "yeni Genel Başkan Özgür Özel"
        ),
    },

    # 17. Web article, right single quote in title.
    #     Raw quirk: "Parti›den" uses › (U+203A) not ’ (U+2019).
    #     Raw hard-wraps: "ne\nyapacak", "https://www.\ndw.com".
    #     Raw join in URL: "seyapacak".
    {
        "id": "solaker2023",
        "raw_text": (
            "Solaker, G. (2023, Aralık 5). İYİ Parti›den ret: CHP yerel seçimde ne\n"
            "yapacak? DW Türkçe. Retrieved March 25, 2025, from https://www.\n"
            "dw.com/tr/i%CC%87yi%CC%87-partiden-ret-chp-yerel-"
            "se%C3%A7imde-neyapacak/a-67638021"
        ),
        "type": "web",
        "first_author": "solaker",
        "year": "2023",
        "title": "İYİ Parti›den ret: CHP yerel seçimde ne yapacak?",
    },

    # 18. Government document with letter-suffixed year.
    #     NOTE: "2019b" is the case that breaks find_year() today (returns int).
    {
        "id": "tbmm2019b",
        "raw_text": (
            "Türkiye Büyük Millet Meclisi. (2019b). Milletlerarası sözleşmeler.\n"
            "https://www.tbmm.gov.tr/komisyon/insanhaklari/pdf01/83-93.pdf"
        ),
        "type": "government_document",
        "first_author": "turkiye buyuk millet meclisi",
        "year": "2019b",
        "title": "Milletlerarası sözleşmeler",
    },

    # 19. Government gazette, law reference.
    #     Raw hard-wrap: "Kanunu (Sayı: 12362).\nhttps://".
    {
        "id": "resmigazete1966",
        "raw_text": (
            "Resmî Gazete. (1966, 30 Temmuz). Gecekondu Kanunu (Sayı: 12362).\n"
            "https://www.resmigazete.gov.tr/arsiv/12362.pdf"
        ),
        "type": "government_document",
        "first_author": "resmi gazete",
        "year": "1966",
        "title": "Gecekondu Kanunu",
    },

    # 20. Government PDF publication, edition note in brackets.
    #     Raw hard-wraps: "(1. baskı)\n[PDF]", "iletisim.gov.tr/\nimages/...".
    {
        "id": "iletisim2025",
        "raw_text": (
            "İletişim Başkanlığı. (2025, 14 Kasım). İhya ve inşa çalışmaları "
            "(1. baskı)\n[PDF]. Cumhurbaşkanlığı İletişim Yayınları. "
            "https://www.iletisim.gov.tr/\nimages/uploads/dosyalar/"
            "Ihya_ve_Insa.pdf"
        ),
        "type": "government_document",
        "first_author": "iletisim baskanligi",
        "year": "2025",
        "title": "İhya ve inşa çalışmaları",
        "publisher": "Cumhurbaşkanlığı İletişim Yayınları",
    },

    # 21. Conference presentation, bracketed type, English month.
    #     Raw hard-wraps: "ahlâkî\nve iktisadî", "Uluslararası\nKuruluşunun".
    {
        "id": "yeniterzi1999",
        "raw_text": (
            "Yeniterzi, E. (1999, April). Divan şiirinde Osmanlı Devleti’ndeki "
            "sosyal, ahlâkî\nve iktisadî çözülmenin akisleri "
            "[Conference presentation]. SÜ Uluslararası\n"
            "Kuruluşunun 700. Yıl Dönümünde Bütün Yönleriyle Osmanlı Devleti "
            "Kongresi, Konya, Türkiye."
        ),
        "type": "conference_proceeding",
        "first_author": "yeniterzi",
        "year": "1999",
        "title": (
            "Divan şiirinde Osmanlı Devleti’ndeki sosyal, ahlâkî ve iktisadî "
            "çözülmenin akisleri"
        ),
    },

        # 22. English book, publisher ends in "University Press".
    {
        "id": "burkette2018",
        "raw_text": (
            "Burkette, A., & Kretzschmar Jr, W. A. (2018). Exploring linguistic "
            "science: Language use, complexity, and interaction. Cambridge "
            "University Press."
        ),
        "type": "book",
        "first_author": "burkette",
        "year": "2018",
        "title": (
            "Exploring linguistic science: Language use, complexity, and "
            "interaction"
        ),
        "publisher": "Cambridge University Press",
    },

    # 23. English journal article, comma-separated Harvard-ish style,
    #     no Vol./No. markers. Broken URL ("https:/" with one slash).
    {
        "id": "kim2020",
        "raw_text": (
            "Kim, E., Park, M. K., & Seo, H. J. (2020). L2ers' predictions of "
            "syntactic structure and reaction times during sentence processing. "
            "Linguistic research, 37, 189-218. "
            "https:/doi.org/10.17250/khisli.37..202009.008"
        ),
        "type": "journal_article",
        "first_author": "kim",
        "year": "2020",
        "title": (
            "L2ers' predictions of syntactic structure and reaction times "
            "during sentence processing"
        ),
        "journal": "Linguistic research",
        "volume": "37",
        "pages": "189-218",
    },
]