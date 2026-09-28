Document: ARCHITECTURE.md
Version: 1.0
Status: Frozen
Last Updated: 2026-08-07
Author: Kutay Uzun

# ARCHITECTURE.md

# Reference Checker Architecture

---

# 1. Purpose

This document defines the overall architecture of Reference Checker. It describes the major software components, their responsibilities, how they communicate, and the flow of data through the application.

This document intentionally does not describe implementation details or algorithms. Those are documented elsewhere.

---

# 2. Architectural Philosophy

Reference Checker follows a layered, modular architecture.

The primary goals are:

- Separation of responsibilities
- Deterministic behaviour
- Explainable verification
- High maintainability
- Testability
- Scalability
- Security by design

Every component shall have a single clearly defined responsibility.

---

# 3. High-Level Architecture

```
                        GUI
                         │
                         ▼
                 Verification Engine
                         │
                         ▼
              Verification Service
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Cache         Crossref Client   OpenAlex Client
        │
        ▼
     SQLite Database

Verification Engine
        │
        ▼
Parser → Reference Objects → Verification → Reports
```

The GUI never communicates directly with external services.

All verification requests pass through the Verification Engine.

---

# 4. System Components

## 4.1 GUI

Responsibilities:

- User interaction
- File selection
- Settings
- Progress display
- Displaying results
- Export requests

The GUI shall not perform parsing or verification.

---

## 4.2 Verification Engine

The Verification Engine is the central coordinator of the application.

Responsibilities:

- Manage workflow
- Coordinate all modules
- Maintain processing state
- Handle exceptions
- Produce VerificationResult objects

The Engine contains no API-specific logic.

---

## 4.3 Parser

Responsibilities:

- Read DOCX files
- Detect bibliography section
- Split references
- Extract metadata
- Produce Reference objects

The Parser never performs verification.

---

## 4.4 Verification Service

Responsibilities:

- Receive Reference objects
- Query cache
- Query verification providers
- Combine evidence
- Return VerificationEvidence

The Verification Service hides all external API details from the Engine.

---

## 4.5 Cache

Responsibilities:

- Store normalized metadata
- Reduce API requests
- Improve performance
- Support offline re-use

SQLite is used as the local cache.

---

## 4.6 Report Generator

Responsibilities:

- Generate Excel reports
- Generate CSV reports
- Generate PDF reports

Reports are generated exclusively from VerificationResult objects.

---

## 4.7 Configuration Manager

Responsibilities:

- Store application settings
- Store API keys
- Store user preferences

Configuration is independent of program logic.

---

## 4.8 Logging System

Responsibilities:

- Record application events
- Record errors
- Record warnings
- Record debugging information

Logging shall never interrupt program execution.

---

# 5. Module Responsibilities

| Module | Responsibility |
|---------|----------------|
| GUI | User interaction |
| Engine | Workflow orchestration |
| Parser | Bibliography extraction and metadata parsing |
| Verification Service | Verification coordination |
| Crossref Client | Crossref communication |
| OpenAlex Client | OpenAlex communication |
| Cache | SQLite cache |
| Reports | Report generation |
| Config | Configuration management |
| Utils | Shared helper functions |

---

# 6. Data Flow

Every document follows the same processing pipeline.

```
DOCX

↓

Document Loader

↓

Bibliography Detection

↓

Reference Splitting

↓

Metadata Parsing

↓

Reference Objects

↓

Cache Lookup

↓

Crossref Verification

↓

OpenAlex Verification (if required)

↓

Evidence Comparison

↓

Decision Engine

↓

VerificationResult

↓

Report Generation

↓

GUI
```

Each processing stage receives data, transforms it, and passes it to the next stage.

No stage modifies previous results.

---

# 7. Core Data Models

The application revolves around four primary objects.

## Document

Represents a single submitted DOCX file.

Contains:

- File path
- Metadata
- Bibliography
- Processing status

---

## Reference

Represents one bibliographic entry.

Contains parsed metadata including:

- Authors
- Title
- Journal
- Year
- Volume
- Issue
- Pages
- DOI
- URL
- Raw reference text

---

## VerificationEvidence

Represents all evidence collected during verification.

Contains:

- Cache evidence
- Crossref evidence
- OpenAlex evidence
- Similarity scores
- DOI validation
- Matching metadata

---

## VerificationResult

Represents the final decision.

Contains:

- Classification
- Confidence score
- Explanation
- Evidence
- Suggested action

---

# 8. External Services

Version 1 supports:

## Crossref

Primary verification authority.

Used whenever sufficient metadata are available.

---

## OpenAlex

Secondary verification authority.

Used when:

- DOI is missing
- Crossref cannot identify a record
- Additional confirmation is required

---

Future providers can be added without modifying the Verification Engine.

---

# 9. Storage Layer

SQLite is the only local database.

It stores:

- Cached verification results
- Normalized metadata
- Processing history
- User settings

Raw API responses are not permanently stored.

---

# 10. Cross-Cutting Services

The following services are available to every module.

- Logging
- Configuration
- Error handling
- Progress reporting
- Caching

These services remain independent from business logic.

---

# 11. Error Handling

Errors shall propagate upward.

Each module:

- Detects errors
- Logs errors
- Returns structured error objects

The application shall continue processing whenever possible.

A single failed reference shall not terminate processing of the document.

---

# 12. Security

Reference Checker follows these security principles.

- Original manuscripts are never modified.
- Only minimum bibliographic metadata are transmitted.
- API keys are stored locally.
- External communication uses HTTPS.
- No complete manuscripts are uploaded.
- No user data are shared.

---

# 13. Design Principles

The architecture follows these principles.

1. Single Responsibility Principle.
2. Separation of concerns.
3. Deterministic processing.
4. Explainable decisions.
5. Local-first operation.
6. Modular components.
7. Extensibility.
8. Testability.
9. Maintainability.
10. Read-only document processing.

---

# 14. Future Extensibility

The architecture supports future additions without redesign.

Examples include:

- Europe PMC
- DataCite
- Semantic Scholar
- Additional report formats
- PDF support
- OCR
- Command-line interface
- Web interface

New functionality should integrate through existing interfaces whenever possible.