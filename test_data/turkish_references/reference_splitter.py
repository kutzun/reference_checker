"""
Reference-section splitting fixture.

Source: Turkish musicology manuscript provided by the user on
2026-09-28. Contains 25 references in an unconventional mixed style:
some are single paragraphs, some span 2 paragraphs (a citation line
followed by a URL or shelf-mark line).

The splitter must join continuation lines and reject non-reference
fragments, producing exactly 25 entries.

Notes on the raw paragraphs:
- `\xa0` (non-breaking space) appears where the source DOCX had one.
  The splitter's clean_reference() normalizes these to regular spaces,
  so the expected entries use regular spaces.
"""

TURKISH_MUSIC_2025_PARAGRAPHS = [
    "Settings\xa0(Doctoral dissertation) University of Georgia.",
    "Allgemeiner Musikalischer Anzeiger,\xa0(AmA), (1829). (1) Leipzig, Winterthur: Rieter-Biedermann. 2-208. urn:nbn:de:bvb:12-bsb10598185-1.",
    "Berliner allgemeine musikalische Zeitung,\xa0(AmZ), (30). 301-316.",
    "bsb10527978_00179_u001",
    "Bis, German Music for Trombones.",
    "https://eclassical.textalk.se/shop/17115/art34/4444634-1e2637-BIS-644_booklet.pdf Erişim Tarihi: 05.06.2026.",
    "Classical Music Daily, (t.y.).",
    "https://www.classicalmusicdaily.com/articles/o/w/woo.htm. Erişim Tarihi: 03.06.2026.",
    "Classical Music, (2023).",
    "https://www.classical-music.com/articles/miserere-mei-lyrics. Erişim Tarihi: 05.06.2026.",
    "Cloutier, D. R. (2009).\xa0Ludwig van Beethoven's orchestration of the trombone. West Virginia University.",
    "Dunn, T. D. (1969).\xa0The instrumental music of Biagio Marini. Yale University.",
    "Fineartamerica, (2023).",
    "https://fineartamerica.com/featured/funeral-of-ludwig-van-beethoven-franz-stober.html.",
    "Guion, D. M. (2014).\xa0Trombone: Its History and Music, 1697-1811. Routledge.",
    "Kemneer, S. (t. y.). The Choral Sublıme: A Study Of Beethoven’s\xa0Dreı Equale, Music & Practice, Volume 8. https://www.musicandpractice.org/volume-8/the-choral-sublime-a-study-of-beethovens-drei-equale/#_ftnref20.",
    "Kim, G. H. (2023).\xa0Coram Deo: The Trombone and the Sublime in Works by Beethoven. (Doctoral dissertation). University of California, Los Angeles.",
    "Kinder, K. (2000).\xa0The wind and wind-chorus music of Anton Bruckner. Bloomsbury, USA.",
    "Mansfield, O. A. (1916). Some Anomalies in Orchestral Accompaniments to Church Music.\xa0The Musical Quarterly,\xa02 (2), 199-209. http://www.jstor.org/stable/737953.",
    "Marx, A. B. (Ed.), (1828).\xa0Berliner allgemeine musikalische Zeitung,\xa0(AmZ), (5). Schlesingersche Buch-Musikhandlung. 2-494. urn:nbn:de:bvb:12-bsb10528067-2.",
    "McGrattan, A. (2019). George Edward Case and the Introduction of Beethoven’s Equali and Schütz’s Lamentatio Davidis (Fili mi, Absalon) into Britain. Historical Brass Journal, (31), 35-50. https://www.historicbrass.org/images/hbj/hbj-2019/HBSJ_2019_JL01_002_McGrattan.pdf.",
    "Mumford, M. H. (1988).\xa0The development of the trombone as an ensemble instrument during the seventeenth and eighteenth centuries\xa0(Doctoral dissertation). University of Tasmania.",
    "Parker, R. C. (2018).\xa0A Performance guide for trombone quartet: An Application of pedagogical concepts and techniques for developing ensembles. The University of Iowa.",
    "Sadie, S. (Ed.), (2001), The New Grove Dictionary of Musiv and Musicians. (Second Edition), Oxford University Press.",
    "Scherman, T. K., Biancolli, L. (1972). The Beethoven Companion, Doubleday & Company.",
    "Scholes, P. A., (ed. Ward, J. O.), (1964).\xa0The concise Oxford dictionary of music. (second edition), Oxford University Press.",
    "Speer, D. (1686). Re Minor Sonata.",
    "https://imslp.org/wiki/Sonata_in_D_minor_(Speer%2C_Daniel). Erişim Tarihi: 08.06.2026.",
    "Switzer, C. R. (2025).\xa0A Pedagogical Guide to and Analysis of Sixty Trombone Quartets\xa0(Doctoral dissertation, University of Oklahoma–Graduate College).",
    "Thayer, A. W. (çev. Krehbiel, H. E.). (1921).\xa0The life of Ludwig van Beethoven\xa0(Vol. 2). Beethoven association.",
    "Weiner, H. (2002). Beethoven's Equali (WoO 30): A New Perspective. (vol 14), Historical Brass Journal, 215-.277. DOİ: 10.2153/0120020011010.",
]

TURKISH_MUSIC_2025_EXPECTED = [
    "Settings (Doctoral dissertation) University of Georgia.",
    "Allgemeiner Musikalischer Anzeiger, (AmA), (1829). (1) Leipzig, Winterthur: Rieter-Biedermann. 2-208. urn:nbn:de:bvb:12-bsb10598185-1.",
    "Berliner allgemeine musikalische Zeitung, (AmZ), (30). 301-316. bsb10527978_00179_u001",
    "Bis, German Music for Trombones. https://eclassical.textalk.se/shop/17115/art34/4444634-1e2637-BIS-644_booklet.pdf Erişim Tarihi: 05.06.2026.",
    "Classical Music Daily, (t.y.). https://www.classicalmusicdaily.com/articles/o/w/woo.htm. Erişim Tarihi: 03.06.2026.",
    "Classical Music, (2023). https://www.classical-music.com/articles/miserere-mei-lyrics. Erişim Tarihi: 05.06.2026.",
    "Cloutier, D. R. (2009). Ludwig van Beethoven's orchestration of the trombone. West Virginia University.",
    "Dunn, T. D. (1969). The instrumental music of Biagio Marini. Yale University.",
    "Fineartamerica, (2023). https://fineartamerica.com/featured/funeral-of-ludwig-van-beethoven-franz-stober.html.",
    "Guion, D. M. (2014). Trombone: Its History and Music, 1697-1811. Routledge.",
    "Kemneer, S. (t. y.). The Choral Sublıme: A Study Of Beethoven’s Dreı Equale, Music & Practice, Volume 8. https://www.musicandpractice.org/volume-8/the-choral-sublime-a-study-of-beethovens-drei-equale/#_ftnref20.",
    "Kim, G. H. (2023). Coram Deo: The Trombone and the Sublime in Works by Beethoven. (Doctoral dissertation). University of California, Los Angeles.",
    "Kinder, K. (2000). The wind and wind-chorus music of Anton Bruckner. Bloomsbury, USA.",
    "Mansfield, O. A. (1916). Some Anomalies in Orchestral Accompaniments to Church Music. The Musical Quarterly, 2 (2), 199-209. http://www.jstor.org/stable/737953.",
    "Marx, A. B. (Ed.), (1828). Berliner allgemeine musikalische Zeitung, (AmZ), (5). Schlesingersche Buch-Musikhandlung. 2-494. urn:nbn:de:bvb:12-bsb10528067-2.",
    "McGrattan, A. (2019). George Edward Case and the Introduction of Beethoven’s Equali and Schütz’s Lamentatio Davidis (Fili mi, Absalon) into Britain. Historical Brass Journal, (31), 35-50. https://www.historicbrass.org/images/hbj/hbj-2019/HBSJ_2019_JL01_002_McGrattan.pdf.",
    "Mumford, M. H. (1988). The development of the trombone as an ensemble instrument during the seventeenth and eighteenth centuries (Doctoral dissertation). University of Tasmania.",
    "Parker, R. C. (2018). A Performance guide for trombone quartet: An Application of pedagogical concepts and techniques for developing ensembles. The University of Iowa.",
    "Sadie, S. (Ed.), (2001), The New Grove Dictionary of Musiv and Musicians. (Second Edition), Oxford University Press.",
    "Scherman, T. K., Biancolli, L. (1972). The Beethoven Companion, Doubleday & Company.",
    "Scholes, P. A., (ed. Ward, J. O.), (1964). The concise Oxford dictionary of music. (second edition), Oxford University Press.",
    "Speer, D. (1686). Re Minor Sonata. https://imslp.org/wiki/Sonata_in_D_minor_(Speer%2C_Daniel). Erişim Tarihi: 08.06.2026.",
    "Switzer, C. R. (2025). A Pedagogical Guide to and Analysis of Sixty Trombone Quartets (Doctoral dissertation, University of Oklahoma–Graduate College).",
    "Thayer, A. W. (çev. Krehbiel, H. E.). (1921). The life of Ludwig van Beethoven (Vol. 2). Beethoven association.",
    "Weiner, H. (2002). Beethoven's Equali (WoO 30): A New Perspective. (vol 14), Historical Brass Journal, 215-.277. DOİ: 10.2153/0120020011010.",
]