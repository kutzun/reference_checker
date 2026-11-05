# Reference Checker

Reference Checker is a desktop application for verifying the accuracy and authenticity of bibliographic references in Microsoft Word (`.docx`) manuscripts. It is designed for journal editors, editorial assistants, universities, and researchers who need to verify references quickly, consistently, and transparently.

The application has two independent halves:

1. **Reference verification** — checks each reference against external bibliographic APIs.
2. **Internal consistency check** — compares in-text citations against the reference list.

Both halves run locally on a user-supplied DOCX. No manuscript content is uploaded to any external service; only individual bibliographic queries are sent to the metadata providers.

---

## What's new in 1.2.2

**New provider: TÜBİTAK Harman.** References are now checked against Harman (TÜBİTAK ULAKBİM's national academic search platform), which indexes DergiPark journals, the YÖK National Thesis Center, and Turkish university institutional repositories.

**Matched-record detail.** Every verified or manually reviewed reference now carries the full matched metadata: title, authors, year, journal or book, and a direct link to the record. The Results table gains a *Matched Record* column; manual-review cards carry a **Best candidate ↗** link; the HTML report renders the matched block with a clickable link; and CSV export gains six `matched_*` columns.

**Verification accuracy.**

- **Year mismatch now consumes weight.** Previously a mismatched year was silently omitted from the score, so a title-only candidate with a multi-year gap could verify at 1.000. A perfect title + perfect author with the wrong year now lands at 0.800 (borderline Verified); candidates that also miss authors drop below 0.700.
- **Harman year extraction fixed.** Harman returns three year-bearing fields — `publication_year`, `publication_date`, and the harvest timestamps in `date` / `originalDates`. The provider previously read `date[0]`, which is the crawl date, producing a spurious 2026 for a 2008 article and 2019 for a 2018 one. The provider now reads `publication_year` first, falls back to `publication_date`, and accepts a bare 4-digit `date` entry only when the shape is a bare year (not an ISO timestamp). Harvest-only records return no year, so the year weight is skipped rather than fed a confidently wrong value.
- **Harman long-title fallback.** When the full title returns zero hits, the query falls back to the subtitle head, then to 10/8/6-word prefixes. Long titles with subtitles or Roman-numeral tokens are no longer silently missed.

**Internal Check accuracy.**

- **`<w:sdt>` content controls are read.** Paragraphs whose text is wrapped in Word content controls (common in manuscripts pasted from Word mobile, Google Docs, or AI tools) were silently invisible to the paragraph extractor, so citations wrapped in `<w:sdt>` were reported as Uncited. The DOCX parser now walks every `<w:t>` descendant, while still excluding tracked deletions (`<w:delText>`).
- **Compound surnames under `ve`.** Turkish author lists like `Altıner, V. ve Sancı Uzun, D.` previously parsed as `['Altıner']` because the `ve` splitter required a single-word surname. The splitter now accepts compound surnames (`Sancı Uzun`, `Çakır İlhan`, `Ercan Güven`, `Öztürk Pat`) on both sides.
- **Narrative compound surnames.** The narrative walk that collects an author name before `(YYYY)` used to stop at the second-to-last capitalised token, so `Öztürk Pat (2017)` collapsed to `['Pat']`. The walk now extends by up to two additional capitalised tokens when the preceding token is not a sentence terminator and the candidate is not a function word (`As`, `See`, `In`, `Gibi`, `İçin`, …).
- **Institutional acronym aliasing.** A reference whose author ends in a trailing parenthetical acronym (`Millî Eğitim Bakanlığı (MEB)`) now also produces an alias key (`meb:YYYY`), so a citation `(MEB, 2024)` resolves against it. Aliasing only applies to *trailing* parentheticals; mid-name occurrences such as `Some (MEB) Thing` are not aliased.
- **Malformed parenthetical citations flagged as Unparsed.** Nested or unclosed parentheses containing a plausible year used to be silently dropped. They now appear in the Unparsed list at their paragraph location.
- **Narrative cross-language conjunction display.** A narrative citation whose author walk stepped over a foreign conjunction (`Kollmuss ve Agyeman (2002)` under the English profile) now displays in full form. The flag is retained — only the display changes.

**Other fixes from the 1.2.2 line.**

- Thesis references (any language) route to Google Scholar instead of KAŞİF. KAŞİF catalogues serials, not theses.
- Cell edits in the Editor tab are now wired to `on_cell_value_changed`; previously they were silently discarded.
- Unparsed citations in Internal Check are surfaced (card + per-citation table) instead of being invisible.
- Turkish possessive suffixes (`Banks'in`, `Yılmaz'ın`) are stripped in `normalizer.py`, so `Banks'in (2001)` resolves against `Banks, R. (2001)`.
- Turkish `ve` conjunction is recognised when the body text is auto-detected as Turkish, even under the English profile.
- `resize_grid` `NameError` in `add_row` / `on_editor_selection` fixed.
- `HarmanProvider` is imported in `runner.py`.
- HTML report "Matched:" label renamed to "Best candidate (not verified):".
- HTML report `ref.raw_text` is escaped (`Template(..., autoescape=True)`).
- CLI provider list is synced with the GUI.
- Custom right-click context menu in the web UI preserves the text selection, so Copy/Cut/Paste work on selected cells in Internal Check results.

See GitHub Releases for full release notes.

---

## Features

### Reference verification

- Microsoft Word (`.docx`) support
- Automatic bibliography detection and reference extraction
- DOI validation
- Crossref verification
- Harman verification (TÜBİTAK ULAKBİM — DergiPark, YÖK Tez, university repositories)
- PubMed verification
- TR Dizin verification (Turkish academic journals)
- OpenLibrary verification
- Google Books verification (optional, requires user-supplied API key)
- Local SQLite cache
- Batch processing
- JSON, CSV, and HTML reports
- Explainable verification decisions with per-field evidence
- Matched-record detail with direct link to the source

### Internal consistency check

- Compares in-text citations against the reference list
- Detects missing references (cited but not listed)
- Detects uncited references (listed but not cited)
- Detects ambiguous matches (two references with the same author and year)
- Detects unparsed citations (nested or unclosed parentheses containing a year)
- Handles parenthetical, narrative, and numeric citation styles
- Reads body text, Word footnotes, and text inside content controls (`<w:sdt>`)
- Institutional-acronym aliasing (e.g. `MEB` ↔ `Millî Eğitim Bakanlığı (MEB)`)
- Compound-surname support for Turkish author lists (`Sancı Uzun`, `Çakır İlhan`, `Ercan Güven`, `Öztürk Pat`)

---

## Verification cascade

References are checked against providers in this order. The cascade stops as soon as a match reaches the verification threshold (0.80).

1. DOI.org — resolves DOI-prefixed references directly.
2. Crossref — journal articles, books, chapters with DOIs.
3. Harman — DergiPark journals, YÖK theses, Turkish university repositories.
4. PubMed — biomedical and life-sciences journal articles.
5. TR Dizin — Turkish academic journals.
6. OpenLibrary — broad book coverage.
7. Google Books — optional; requires an API key configured by the user.

When no provider verifies a reference, a manually-followable search link is generated:

- **Google Scholar** for journal articles, theses, and non-Turkish material.
- **Milli Kütüphane KAŞİF** for Turkish monographs.
- **YÖK Ulusal Tez Merkezi** for Turkish theses.

---

## Internal Check

The Internal Check tab verifies internal consistency: every in-text citation must appear in the reference list, and every entry in the reference list must be cited in text.

Three citation styles are supported:

- **Parenthetical author-year:** `(Smith, 2020)`, `(Smith & Jones, 2020)`, `(Smith et al., 2020; Jones, 2019)`
- **Narrative:** `According to Smith (2020)`, `Smith (2020) argues`, `Smith (2020, p. 45)`
- **Numeric:** `[1]`, `[1-3]`, `[1,3-5]`

Statistical expressions such as `(M = 2.985; SD = 1.0345)` are recognized and ignored. Parenthetical line references such as `(594)` are treated as text references, not citations.

Language profiles: **English**, **Turkish**, **Generic**. The profiles carry language-specific markers (conjunctions, et-al forms, narrative phrases) that inform citation splitting.

The Internal Check runs locally on the same DOCX uploaded for verification and produces a report of missing references, uncited references, ambiguous matches, and unparsed citations.

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12+ |
| GUI | NiceGUI |
| Database | SQLite |
| DOCX parsing | python-docx |
| HTTP | requests |
| Testing | pytest |
| Formatter | Black |
| Linter | Ruff |

---

## Project structure

```
reference_checker-1.2.2/
├── .github/workflows/        CI build workflows (macOS)
├── docs/                     Project documentation
├── pyinstaller_hooks/        PyInstaller build hooks
├── smoke_out/                Smoke-test report outputs
├── src/
│   ├── app_logging/          Logging configuration
│   ├── cache/                SQLite result cache
│   ├── cli/                  Command-line entry point
│   ├── config/               Settings and API key handling
│   ├── extractor/            Metadata extraction from reference strings
│   ├── gui/                  NiceGUI application (single file)
│   ├── internal_check/       Internal consistency check subsystem
│   │   ├── profiles/         Language profiles (English, Turkish, Generic)
│   │   ├── intext_extractor.py
│   │   ├── matcher.py
│   │   ├── normalizer.py
│   │   ├── noise_filter.py
│   │   └── service.py
│   ├── models/               Data models and enums
│   ├── parser/               DOCX parsing and reference splitting
│   ├── report/               Report generation and export
│   ├── verification/         External verification providers
│   └── workflow/             Pipeline coordination
├── test_data/                Fixtures and provider mocks
├── tests/                    pytest test suite
├── launcher.py               Entry point for frozen builds
├── main.py                   Development entry point
├── installer.iss             Inno Setup installer script (Windows)
├── ReferenceChecker.spec     PyInstaller build specification (Windows)
├── ReferenceChecker-mac.spec PyInstaller build specification (macOS)
├── pyproject.toml            Project metadata and tool configuration
└── requirements.txt          Pinned dependencies
```

---

## Running from source

```
pip install -r requirements.txt
python launcher.py
```

The NiceGUI server starts on a local port and opens in the default browser.

---

## Building the installer

### Windows

```
pyinstaller ReferenceChecker.spec --clean
```

Then compile `installer.iss` with Inno Setup 6.x. The output is `ReferenceChecker_Setup_v122.exe`.

### macOS

```
pyinstaller ReferenceChecker-mac.spec --clean
```

A GitHub Actions workflow (`.github/workflows/build-mac.yml`) builds the macOS bundle automatically on push.

---

## Development workflow

Every change follows the same rhythm:

```
Design → Fixture → Failing test → Implementation → Green → Commit
```

Every module has a single responsibility. All implementation follows the standards defined in `docs/CODING_STANDARDS.md`.

---

## Testing

```
python -m pytest tests/ -q
```

Use `python -m pytest` (not bare `pytest`) so `test_data.*` imports resolve from the project root.

380+ tests passing as of v1.2.2.

---

## Project philosophy

> **Verify every reference. Explain every decision.**

The software prioritizes:

- Accuracy
- Determinism
- Explainability
- Maintainability
- Security

---

## Known limitations

- Citations by title (e.g. `(Yapılandırılmış Görüşme, 2025)` for an interview) are not matched under the first-author keying used by the internal check.
- Descriptive parentheticals (e.g. `(CAF, Skehan, 2009)`) are treated as citations and reported as missing. They are visible in the GUI and can be dismissed by the user.
- The internal check keys on first author + year + disambiguation suffix. Two references by the same first author in the same year *without* `a`/`b`/`c` suffixes are reported as ambiguous rather than resolved.
- Word endnotes and text boxes are not read; only body paragraphs, footnotes, and `<w:sdt>` content controls.
- Turkish academic book coverage in external APIs remains limited. Google Books (with a user-supplied key) is the primary mitigation.
- Classical Arabic/Ottoman critical editions (records containing `thk.` for tahkik, or publisher prefixes like `Dâru’l-`, `el-Mektebetü’l-`) are not covered by any provider in the cascade. The YEK portal (`portal.yek.gov.tr`) indexes this material but exposes no API and no title-searchable URL; detail pages are keyed by an internal work ID and search pages require an authenticated session. References of this genre should be expected to fall to Manual Review with no usable search link.
- Compound parentheticals containing multiple complete citations in one paren (e.g. `(Özgüç & Akok, 1958, s. 31, Özgüç, 1978, s. 31)`) silently drop the second citation. Single-citation parents and numeric parents work.
- Possessive-titled narrative phrases (e.g. `Skehan's Trade-off Hypothesis (1998)`) resolve the head noun (`Hypothesis`) as the author, not the possessor. Fixing this requires a generic-noun allowlist and possessive lookback, which risks regressing the working narrative shapes. One known false positive on a 161-citation manuscript.
- Cross-language conjunctions in a bilingual extended abstract (e.g. `Altıner and Sancı Uzun (2024)` under the Turkish profile, where `and` is English) display in full form for the editor but are correctly flagged as Missing. There is no per-paragraph profile auto-detection.
- The Internal Check runs only on the **first** uploaded file when multiple files are present. Files 2..N are verified but ignored by the internal check.

---

## License

MIT License.

---

## Authors

Kutay Uzun

---

## Acknowledgements

This project uses metadata provided by:

- Crossref
- DOI.org
- PubMed
- Harman (TÜBİTAK ULAKBİM)
- TR Dizin
- OpenLibrary
- Google Books