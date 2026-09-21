"""
Citation profiles for in-text citation extraction.

A profile is a bundle of language-specific markers used by the
extractor to clean narrative citations. The profiles contain data
only — no logic. The extractor owns the logic; the profiles tell it
which words to strip.

Adding a new language means adding one ``CitationProfile`` instance
at the bottom of this file. The extractor does not need to change.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CitationProfile:
    """Language-specific markers for in-text citation extraction."""

    name: str

    # Author-list conjunctions: "Smith and Jones", "Smith & Jones".
    conjunctions: frozenset[str] = field(default_factory=frozenset)

    # "et al." equivalents: "Smith et al.", "Yılmaz vd.".
    et_al_markers: frozenset[str] = field(default_factory=frozenset)

    # Phrases that appear *before* the author in a narrative citation.
    # Example (English): "According to Smith (2020)" -> strip
    # "according to", leaving "Smith" as the author phrase.
    # Example (Turkish): "bkz. Yılmaz (2020)" -> strip "bkz.".
    # Multi-word entries are matched as whole phrases.
    narrative_leading: frozenset[str] = field(default_factory=frozenset)

    # Phrases that appear *after* the year-parenthesis and belong to
    # the citation. Example (Turkish): "Smith (2020)'e göre" -> strip
    # "göre". Matched in the text immediately after the closing ")".
    narrative_trailing: frozenset[str] = field(default_factory=frozenset)


GENERIC = CitationProfile(name="generic")


ENGLISH = CitationProfile(
    name="en",
    conjunctions=frozenset({"and", "&"}),
    et_al_markers=frozenset({"et al.", "et al", "et. al.", "et. al"}),
    narrative_leading=frozenset({
        # Simple prepositions
        "according to",
        "as",
        "by",
        "see",
        "see also",
        "cf.",
        "from",
        "per",
        "in",
        # Secondary-source markers
        "cited in",
        "as cited in",
        "quoted in",
        "as quoted in",
        # Explicit attributions ("as [verb] by")
        "as noted by",
        "as argued by",
        "as shown by",
        "as stated by",
        "as reported by",
        "as discussed by",
        "as suggested by",
        "as described by",
        "as demonstrated by",
        "as observed by",
        "as indicated by",
        "as proposed by",
        "as outlined by",
        "as emphasized by",
        "as highlighted by",
        "as defined by",
        "as detailed by",
        "as established by",
        "as claimed by",
        "as asserted by",
        "as maintained by",
        "as identified by",
        "as documented by",
        "as stressed by",
        "as explained by",
        # Direct active constructs
        "work by",
        "works by",
        "study by",
        "studies by",
        "research by",
        "findings of",
        "findings by",
        "model proposed by",
        "framework introduced by",
    }),
    # Left empty for now. English markers like "and colleagues" sit
    # *between* the author and the year, not after the closing paren.
    # If the extractor later needs a "middle markers" field, we will
    # add them there rather than shoehorn them into narrative_trailing.
    narrative_trailing=frozenset(),
)


TURKISH = CitationProfile(
    name="tr",
    conjunctions=frozenset({"ve", "ile", "&"}),
    et_al_markers=frozenset({
        "vd.",
        "vd",
        "ve ark.",
        "ve ark",
        "ve diğerleri",
        "ve diğ.",
        "ve diğ",
    }),
    narrative_leading=frozenset({
        "bkz.",
        "bkz",
        "bakınız",
        "karşılaştırınız",
        "krş.",
        "krş",
        "örneğin",
        "ör.",
        "ör",
        "aktaran",
        "aktaran:",
    }),
    narrative_trailing=frozenset({
        # Postpositions (postpositional phrases)
        "göre",
        "tarafından",
        "uyarınca",
        "doğrultusunda",
        "ekseninde",
        "paralelinde",
        "paralel olarak",
        "ışığında",
        "kapsamında",
        "çerçevesinde",
        "aracılığıyla",
        "vasıtasıyla",
        # Passive / participial clauses
        "belirtildiği üzere",
        "belirtildiği gibi",
        "ifade edildiği üzere",
        "ifade edildiği gibi",
        "vurgulandığı üzere",
        "vurgulandığı gibi",
        "öne sürüldüğü gibi",
        "savunulduğu gibi",
        "ileri sürüldüğü üzere",
        "gösterildiği gibi",
        "gösterildiği üzere",
        "aktarıldığı kadarıyla",
        "kaydedildiği gibi",
        # Reporting verbs (past / present perfect)
        "belirtmiştir",
        "belirtmektedir",
        "ifade etmiştir",
        "ifade etmektedir",
        "vurgulamıştır",
        "vurgulamaktadır",
        "savunmuştur",
        "savunmaktadır",
        "ileri sürmüştür",
        "öne sürmüştür",
        "göstermiştir",
        "açıklamıştır",
        "tartışmıştır",
        "tespit etmiştir",
        "önermiştir",
        "bildirmiştir",
        "saptamıştır",
    }),
)


# Lookup table used by the GUI to map a short name to a profile.
PROFILES: dict[str, CitationProfile] = {
    "generic": GENERIC,
    "en": ENGLISH,
    "tr": TURKISH,
}