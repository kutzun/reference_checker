Document: DATABASE_SCHEMA.md
Version: 1.0
Status: Frozen
Last Updated: 2026-08-07
Author: Kutay Uzun

# DATABASE_SCHEMA.md

# Reference Checker Database Schema

---

# 1. Purpose

This document defines the SQLite database schema used by Reference Checker.

The database serves as a local cache and configuration store. It is not intended to permanently archive manuscripts or verification results.

Its primary objectives are:

- Reduce unnecessary API requests
- Improve verification speed
- Store user configuration
- Maintain application logs
- Support offline reuse of previously verified references

---

# 2. Database Engine

Version 1 uses:

- SQLite 3

Reasons:

- No installation required
- Cross-platform
- Lightweight
- Reliable
- Excellent read performance
- Suitable for desktop applications

---

# 3. Database Principles

The database shall:

- Never store complete manuscripts.
- Never store complete bibliography sections.
- Store only metadata required for verification.
- Store normalized data whenever possible.
- Minimize duplicated information.
- Support future schema migrations.

---

# 4. Tables

Version 1 contains the following tables.

## references_cache

Stores normalized reference metadata returned by verification providers.

Fields:

| Field | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY |
| doi | TEXT |
| title | TEXT |
| authors | TEXT |
| journal | TEXT |
| year | INTEGER |
| volume | TEXT |
| issue | TEXT |
| pages | TEXT |
| publisher | TEXT |
| reference_type | TEXT |
| crossref_score | REAL |
| openalex_score | REAL |
| verified_source | TEXT |
| verified_date | DATETIME |
| cache_expiry | DATETIME |

Purpose:

Avoid repeated API queries.

---

## verification_history

Stores document-level verification history.

Fields:

| Field | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| filename | TEXT |
| processed_date | DATETIME |
| total_references | INTEGER |
| verified | INTEGER |
| manual_review | INTEGER |
| failed | INTEGER |
| processing_time | REAL |

Purpose:

Statistics and processing history.

---

## settings

Stores user preferences.

Fields:

| Field | Type |
|--------|------|
| key | TEXT PRIMARY KEY |
| value | TEXT |

Examples:

- Theme
- Language
- Crossref email
- API timeout
- Cache lifetime
- Batch size
- Maximum concurrent requests
- Output directory

---

## api_keys

Stores optional API credentials.

Fields:

| Field | Type |
|--------|------|
| provider | TEXT PRIMARY KEY |
| api_key | TEXT |
| email | TEXT |

API keys shall be encrypted before storage.

---

## logs

Stores application events.

Fields:

| Field | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| timestamp | DATETIME |
| level | TEXT |
| module | TEXT |
| message | TEXT |

Purpose:

Debugging and diagnostics.

---

# 5. Relationships

```
references_cache

↓

verification_history

(no foreign key required)

settings

(independent)

api_keys

(independent)

logs

(independent)
```

The database intentionally contains very few relationships to maximize simplicity and performance.

---

# 6. Indexes

Version 1 creates indexes on:

- DOI
- Title
- Year
- Verified Date
- Cache Expiry

These indexes improve lookup performance.

---

# 7. Cache Strategy

The cache follows these rules.

- DOI lookup first.
- If DOI unavailable, use metadata lookup.
- Expired entries are automatically refreshed.
- Cache entries remain valid until expiration.
- Duplicate cache entries are not permitted.

---

# 8. Cache Expiration

Default cache lifetime:

365 days

Expired entries:

- remain available
- are refreshed automatically during future verification

This minimizes unnecessary API traffic.

---

# 9. Transactions

Database writes use transactions.

Each verification batch commits only after successful completion.

Failed transactions are rolled back automatically.

---

# 10. Concurrency

SQLite operates in WAL (Write-Ahead Logging) mode.

Benefits:

- Better read performance
- Better concurrent access
- Reduced locking

Only one write operation occurs at any time.

---

# 11. Security

The database shall:

- Never store manuscripts.
- Never store bibliography text.
- Encrypt stored API keys.
- Store only required metadata.
- Validate all database inputs.

---

# 12. Backup

Users may export:

- Settings
- Cache
- Logs

Database backups are optional.

---

# 13. Future Expansion

Future versions may include:

- Europe PMC cache
- DataCite cache
- Semantic Scholar cache
- ORCID cache
- Shared institutional cache
- Usage statistics
- Verification analytics

Version 1 shall remain backward compatible with future schema migrations.