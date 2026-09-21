# Reference Checker

Reference Checker is a desktop application for verifying the accuracy and authenticity of bibliographic references in Microsoft Word (`.docx`) manuscripts.

The software is designed for journal editors, editorial assistants, universities, and researchers who need to verify references quickly, consistently, and transparently.

Version 1.1 adds an internal consistency check that compares in-text citations against the reference list.

---

# Features

- Microsoft Word (`.docx`) support
- Automatic bibliography detection
- Automatic reference extraction
- DOI validation
- Crossref verification
- OpenAlex verification
- Local SQLite cache
- Batch processing
- Excel, CSV and PDF reports
- Explainable verification decisions
- Internal consistency check (citations ↔ references)

---

# Internal Check

The Internal Check verifies the internal consistency of a manuscript: every in-text citation must appear in the reference list, and every entry in the reference list must be cited in text.

Three citation styles are supported:

- Parenthetical author-year: `(Smith, 2020)`, `(Smith & Jones, 2020)`, `(Smith et al., 2020; Jones, 2019)`
- Narrative: `According to Smith (2020)`, `Smith (2020) argues`, `Smith (2020, p. 45)`
- Numeric: `[1]`, `[1-3]`, `[1,3-5]`

Statistical expressions such as `(M = 2.985; SD = 1.0345)` are recognized and ignored.

Language profiles:

- English
- Turkish
- Generic (language-independent)

The Internal Check is available as a separate tab in the GUI. It runs locally, on the same DOCX you uploaded for verification, and produces a report of missing references and uncited references.

---

# Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.13 |
| GUI | Tkinter |
| Database | SQLite |
| Testing | pytest |
| Formatter | Black |
| Linter | Ruff |

---

# Project Structure

```
Reference_Checker/

├── docs/
├── src/
│   ├── cache/
│   ├── config/
│   ├── engine/
│   ├── gui/
│   ├── models/
│   ├── parser/
│   ├── reports/
│   ├── utils/
│   └── verifier/
│
├── tests/
├── resources/
├── output/
├── logs/
├── scripts/
│
├── main.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

# Documentation

Project documentation is located in the `docs` directory.

Core documents:

- PROJECT_SCOPE.md
- PIPELINE.md
- ARCHITECTURE.md
- DATABASE_SCHEMA.md
- GUI_SPEC.md
- CODING_STANDARDS.md
- DECISIONS.md
- PROJECT_STATE.md
- AI_INSTRUCTIONS.md

---

# Development Workflow

Every feature follows the same workflow.

```
Design

↓

Implement

↓

Test

↓

Review

↓

Commit
```

Every module should have a single responsibility.

All implementation should follow the standards defined in `CODING_STANDARDS.md`.

---

# Project Philosophy

Reference Checker is built around one principle:

> **Verify every reference. Explain every decision.**

The software prioritizes:

- Accuracy
- Determinism
- Explainability
- Maintainability
- Security

---

# Current Status

Development Status:

Architecture Complete

Current Phase:

Core Implementation

Next Milestone:

Core Data Models

---

# License

MIT Licence

---

# Authors

Kutay Uzun

---

# Acknowledgements

This project uses metadata provided by:

- Crossref
- OpenLibrary