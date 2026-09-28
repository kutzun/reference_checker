Document: PROJECT_SCOPE.md
Version: 1.0
Status: Frozen Draft
Last Updated: 2026-08-07
Author: Kutay Uzun

# PROJECT_SCOPE.md

# Reference Checker

## Project Scope

**Version:** 1.0  
**Status:** Frozen Draft  
**Last Updated:** 2026-08-07

---

# 1. Project Overview

Reference Checker is a desktop application designed to verify the accuracy, authenticity, and consistency of bibliographic references contained in Microsoft Word (.docx) documents.

The software automatically detects the bibliography section of a manuscript, extracts individual references, parses their bibliographic metadata, verifies the extracted information against authoritative scholarly databases, and generates comprehensive verification reports.

The application is intended to assist journal editors, editorial assistants, universities, researchers, and graduate students by significantly reducing the amount of manual reference verification while improving consistency, transparency, and reproducibility.

---

# 2. Purpose

The primary purpose of Reference Checker is to determine whether a submitted bibliographic reference corresponds to an authoritative scholarly record.

The software assists users by identifying:

- Fabricated references
- Incorrect DOI assignments
- Metadata inconsistencies
- Missing bibliographic information
- References requiring manual review

Reference Checker does not replace editorial judgement. It provides evidence-based verification to support editorial decision making.

---

# 3. Definitions

### Reference

A bibliographic entry appearing within the bibliography section of a document.

### Bibliography

The collection of references appearing under headings such as:

- References
- Bibliography
- Works Cited
- Literature
- Kaynakça
- Kaynaklar
- Literatur
- Literaturverzeichnis
- Bibliographie

Additional headings may be supported in future versions.

### Verification

The process of determining whether a submitted reference corresponds to an authoritative scholarly record.

### Confidence Score

A numerical estimate representing the degree of agreement between the submitted reference and authoritative metadata.

---

# 4. Target Users

Reference Checker is intended for:

- Journal editors
- Editorial assistants
- University libraries
- Graduate schools
- Faculty members
- Researchers
- Graduate students

---

# 5. Project Objectives

Reference Checker aims to:

- Reduce manual verification time
- Improve editorial efficiency
- Improve verification consistency
- Detect fabricated references
- Detect metadata inconsistencies
- Produce deterministic results
- Produce explainable decisions
- Minimize unnecessary API requests through intelligent caching
- Support large-scale batch processing
- Preserve manuscript confidentiality

---

# 6. Scope

Version 1 includes:

- Microsoft Word (.docx) support
- Automatic bibliography detection
- Automatic reference extraction
- Automatic reference splitting
- Metadata parsing
- DOI validation
- Crossref verification
- OpenAlex verification
- Confidence scoring
- Explainable verification decisions
- Local SQLite caching
- Progress monitoring
- Batch processing
- Verification report generation
- Comprehensive logging
- Settings management

---

# 7. Supported Reference Types

Version 1 supports verification of:

- Journal articles
- Books
- Book chapters
- Conference proceedings
- Theses and dissertations
- Technical reports

Unsupported reference types shall be reported for manual review.

---

# 8. Out of Scope

Version 1 does not include:

- PDF parsing
- OCR
- AI or LLM functionality
- Google Scholar scraping
- Plagiarism detection
- Citation formatting
- Reference management
- Manuscript editing
- Cloud storage
- Collaborative editing
- Automatic correction of references
- In-text citation verification

These features may be considered in future versions.

---

# 9. Supported Input Formats

Version 1 accepts:

- Microsoft Word (.docx)

---

# 10. Supported Output Formats

Version 1 generates:

- Excel reports (.xlsx)
- CSV reports (.csv)
- PDF reports (.pdf)

Future versions may support additional export formats.

---

# 11. Verification Sources

Version 1 uses the following external verification providers.

## Primary Authority

- Crossref

## Secondary Authority

- OpenAlex

Crossref serves as the primary authoritative source whenever sufficient metadata are available.

OpenAlex is used as a complementary verification and discovery source when additional evidence is required.

---

# 12. Verification Philosophy

Every reference follows the same conceptual workflow.

```
Reference

↓

Metadata Extraction

↓

Authority Lookup

↓

Evidence Comparison

↓

Classification

↓

Explanation

↓

Report
```

Every verification result shall be supported by objective evidence.

---

# 13. Design Principles

Reference Checker follows these principles.

1. Local-first processing.
2. Explainable verification.
3. Deterministic behaviour.
4. Modular architecture.
5. Security by design.
6. Performance through intelligent caching.
7. Human review for ambiguous cases.
8. Read-only processing.
9. Maintainability.
10. Extensibility.

---

# 14. Security Principles

Reference Checker shall:

- Never modify the original manuscript.
- Never upload complete manuscripts.
- Never upload complete bibliography sections.
- Transmit only the minimum metadata necessary for verification.
- Store verification data locally unless explicitly configured otherwise.

---

# 15. Success Criteria

Version 1 shall:

- Reliably detect bibliography sections.
- Reliably extract references.
- Verify references against authoritative databases.
- Produce explainable verification reports.
- Support single-document processing.
- Support batch processing.
- Maintain stable operation during long processing sessions.
- Preserve the integrity of original manuscripts.

---

# 16. Version 1 Deliverables

The initial production release includes:

- Verification engine
- Desktop graphical user interface
- Batch processing
- Local caching
- Progress monitoring
- Verification reports
- Settings management
- Logging
- Error reporting
- User documentation

---

# 17. Project Philosophy

Reference Checker follows one fundamental principle.

> **Verify every reference. Explain every decision.**

Every verification result produced by the software shall be reproducible, transparent, and supported by objective evidence.

Next Document:
SOFTWARE_REQUIREMENTS.md