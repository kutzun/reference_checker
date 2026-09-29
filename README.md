# Reference Checker

Reference Checker is a desktop application for verifying the accuracy and authenticity of bibliographic references in Microsoft Word (`.docx`) manuscripts. It is designed for journal editors, editorial assistants, universities, and researchers who need to verify references quickly, consistently, and transparently.

The application has two independent halves:

1. **Reference verification** — checks each reference against external bibliographic APIs.
2. **Internal consistency check** — compares in-text citations against the reference list.

Both halves run locally on a user-supplied DOCX. No manuscript content is uploaded to any external service; only individual bibliographic queries are sent to the metadata providers.

---

## What's new in 1.2

- Book-chapter verification now extracts the book title, queries it, and scores against it.
- Internal check handles Turkish in-text citation style (surname + initial without comma), narrative surname particles (`de Bot`), clause starters (`Following Guastello`), and multi-year parentheticals (`(Köhler, 1986, 2012)`).
- Footnotes are read by the parser and merged into the paragraph carrying their marker.
- Turkish surname extraction fixed for extended-Latin characters (`Kılıç`, `Kutluğ`, `Bardakçı`).
- Mononym authors (`Rosmawati, & Lowie, W.`) preserved.
- KAŞİF search links fixed (literal `:` and `,`, short-title quoting).
- APA journal articles route to Google Scholar instead of KAŞİF.

See GitHub Releases for full 1.2.0 notes.

---

## Features

### Reference verification

- Microsoft Word (`.docx`) support
- Automatic bibliography detection and reference extraction
- DOI validation
- Crossref verification
- TR Dizin verification (Turkish academic journals)
- OpenLibrary verification
- Google Books verification (optional, requires user-supplied API key)
- Local SQLite cache
- Batch processing
- JSON, CSV, and HTML reports
- Explainable verification decisions with per-field evidence

### Internal consistency check

- Compares in-text citations against the reference list
- Detects missing references (cited but not listed)
- Detects uncited references (listed but not cited)
- Detects ambiguous matches (two references with the same author and year)
- Handles parenthetical, narrative, and numeric citation styles
- Reads body text and Word footnotes

---

## Verification cascade

References are checked against providers in this order. The cascade stops as soon as a match reaches the verification threshold (0.80).

1. DOI.org — resolves DOI-prefixed references directly.
2. Crossref — journal articles, books, chapters with DOIs.
3. TR Dizin — Turkish academic journals.
4. OpenLibrary — broad book coverage.
5. Google Books — optional; requires an API key configured by the user.

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

The Internal Check runs locally on the same DOCX uploaded for verification and produces a report of missing references and uncited references.

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
reference_checker/
├── docs/                     Project documentation
├── pyinstaller_hooks/        PyInstaller build hooks
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
├── installer.iss             Inno Setup installer script
├── ReferenceChecker.spec     PyInstaller build specification
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

```
pyinstaller ReferenceChecker.spec --clean
```

Then compile `installer.iss` with Inno Setup 6.x. The output is `ReferenceChecker_Setup_v120.exe`.

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
python -m pytest -q
```

309 tests passing as of v1.2.0.

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
- The internal check keys on first author only. Two references by the same first author in the same year are reported as ambiguous rather than resolved.
- Word endnotes and text boxes are not read; only body paragraphs and footnotes.
- Turkish academic book coverage in external APIs remains limited. Google Books (with a user-supplied key) is the primary mitigation.

---

## License

MIT Licence.

---

## Authors

Kutay Uzun

---

## Acknowledgements

This project uses metadata provided by:

- Crossref
- DOI.org
- TR Dizin
- OpenLibrary
- Google Books