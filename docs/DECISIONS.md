Document: DECISIONS.md
Version: 1.0
Status: Living Document
Last Updated: 2026-08-07
Author: Kutay Uzun

# DECISIONS.md

# Reference Checker Engineering Decisions

---

# Purpose

This document records significant architectural and engineering decisions made during the development of Reference Checker.

Each decision includes the reasoning behind it and its expected impact on the project.

This document is updated whenever a major design decision is made.

---

# Decision Template

Every new decision shall follow this format.

## DEC-XXX

**Date:**

YYYY-MM-DD

**Status:**

Accepted | Superseded | Rejected

**Decision**

A concise description of the decision.

**Reason**

Why this decision was made.

**Consequences**

Expected impact on the project.

---

# Decision Log

---

## DEC-001

**Date**

2026-08-07

**Status**

Accepted

**Decision**

Reference Checker will be a desktop application.

**Reason**

Target users primarily work with local manuscript files and require offline-capable verification.

**Consequences**

No cloud infrastructure is required.

---

## DEC-002

**Date**

2026-08-07

**Status**

Accepted

**Decision**

Microsoft Word (.docx) is the only supported input format in Version 1.

**Reason**

The overwhelming majority of submitted manuscripts use DOCX.

**Consequences**

PDF parsing and OCR are postponed to future versions.

---

## DEC-003

**Date**

2026-08-07

**Status**

Accepted

**Decision**

Crossref is the primary verification authority.

**Reason**

Crossref provides authoritative DOI metadata with excellent coverage.

**Consequences**

Every verification attempts Crossref before any secondary provider.

---

## DEC-004

**Date**

2026-08-07

**Status**

Accepted

**Decision**

OpenAlex serves as the secondary verification provider.

**Reason**

It complements Crossref when DOI information is unavailable or incomplete.

**Consequences**

Verification coverage increases without changing the core architecture.

---

## DEC-005

**Date**

2026-08-07

**Status**

Accepted

**Decision**

The software shall not use AI or LLM services.

**Reason**

Deterministic, explainable verification is required by the university.

**Consequences**

All verification relies on authoritative metadata rather than probabilistic text generation.

---

## DEC-006

**Date**

2026-08-07

**Status**

Accepted

**Decision**

SQLite is the only local database.

**Reason**

It requires no installation, is lightweight, and is well suited for desktop applications.

**Consequences**

Deployment remains simple and cross-platform.

---

## DEC-007

**Date**

2026-08-07

**Status**

Accepted

**Decision**

The database functions primarily as a cache.

**Reason**

The application is not intended to archive manuscripts or maintain a document repository.

**Consequences**

Storage requirements remain small and API requests are minimized.

---

## DEC-008

**Date**

2026-08-07

**Status**

Accepted

**Decision**

The GUI shall never communicate directly with external APIs.

**Reason**

Business logic should remain independent of the user interface.

**Consequences**

The Verification Engine controls all processing.

---

## DEC-009

**Date**

2026-08-07

**Status**

Accepted

**Decision**

The architecture follows a layered modular design.

**Reason**

Modularity improves maintainability, testing, and future expansion.

**Consequences**

Each module has a single responsibility.

---

## DEC-010

**Date**

2026-08-07

**Status**

Accepted

**Decision**

The software processes documents in read-only mode.

**Reason**

Original manuscripts must never be modified.

**Consequences**

All output is generated as separate report files.

---

## DEC-011

**Date**

2026-08-07

**Status**

Accepted

**Decision**

Reference verification decisions shall always be explainable.

**Reason**

Editors must understand why a reference was classified in a particular way.

**Consequences**

Every verification result includes supporting evidence.

---

## DEC-012

**Date**

2026-08-07

**Status**

Accepted

**Decision**

Batch processing is supported from Version 1.

**Reason**

Editorial workflows often involve multiple manuscripts.

**Consequences**

Progress tracking operates at both document and reference levels.

---

# Future Decisions

Future decisions shall continue the numbering sequence.

Decision identifiers are permanent and shall never be reused.