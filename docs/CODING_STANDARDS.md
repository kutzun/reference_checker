Document: CODING_STANDARDS.md
Version: 1.0
Status: Draft
Last Updated: 2026-08-07
Author: Kutay Uzun

# CODING_STANDARDS.md

# Reference Checker Coding Standards

---

# 1. Purpose

This document defines the coding standards for the Reference Checker project.

All source code shall conform to these standards to ensure consistency, maintainability, readability, reliability, and long-term scalability.

---

# 2. Python Version

Version 1 shall use:

Python 3.13

No code shall depend on deprecated Python features.

---

# 3. Code Style

The project follows:

- PEP 8
- Black formatting
- Ruff linting

Formatting shall be automatic whenever possible.

---

# 4. Naming Conventions

## Variables

Use:

snake_case

Example:

reference_count

---

## Functions

Use:

snake_case

Example:

parse_reference()

---

## Classes

Use:

PascalCase

Example:

ReferenceParser

---

## Constants

Use:

UPPER_CASE

Example:

DEFAULT_TIMEOUT

---

## Private Members

Prefix with:

_

Example:

_parse_title()

---

# 5. Type Hints

All public functions shall include complete type hints.

Example:

```python
def parse_reference(text: str) -> Reference:
```

Avoid the use of `Any` unless absolutely necessary.

---

# 6. Docstrings

Public classes and public functions shall include docstrings.

Google-style docstrings shall be used.

Example:

```python
def verify_reference(reference: Reference) -> VerificationResult:
    """
    Verify a bibliographic reference.

    Args:
        reference:
            Parsed reference object.

    Returns:
        Verification result.
    """
```

---

# 7. Data Models

Data-only objects shall use:

@dataclass

Examples:

- Reference
- Document
- VerificationEvidence
- VerificationResult

Business logic should not be placed inside data models.

---

# 8. Imports

Imports shall be grouped as:

1. Standard library
2. Third-party libraries
3. Project modules

Wildcard imports are prohibited.

Example:

```python
from parser import *
```

is not permitted.

---

# 9. Error Handling

Exceptions shall:

- be specific
- be logged
- provide meaningful messages

Exceptions shall never be silently ignored.

Avoid:

```python
except:
    pass
```

---

# 10. Logging

Use the logging module.

Do not use print() for application logging.

Log levels:

- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

---

# 11. Configuration

Configuration values shall never be hardcoded.

Examples:

- API timeout
- Cache lifetime
- Output directory
- Thread count

Configuration shall be read from the Configuration Manager.

---

# 12. File Paths

Never hardcode absolute paths.

Use pathlib.Path.

Example:

```python
from pathlib import Path
```

---

# 13. Strings

Use UTF-8 encoding throughout the project.

Support Unicode characters.

---

# 14. Functions

Functions should:

- perform one task
- remain short
- avoid excessive nesting
- avoid hidden side effects

Target length:

Less than 50 lines where practical.

---

# 15. Classes

Classes should have one clear responsibility.

Avoid "God classes."

The Verification Engine coordinates modules but does not implement their internal logic.

---

# 16. Dependencies

Keep external dependencies to a minimum.

Prefer the Python standard library whenever practical.

Every dependency shall have a documented purpose.

---

# 17. Database Access

All SQLite access shall occur through the Cache module.

Other modules shall never execute SQL directly.

---

# 18. API Access

All HTTP communication shall occur through the Verification Service.

Parser, GUI, Reports, and Models shall never call external APIs directly.

---

# 19. Threading

Long-running operations shall execute in worker threads.

The GUI thread shall never perform:

- network requests
- database operations
- document parsing

---

# 20. Testing

Core modules shall include unit tests.

Tests shall be deterministic.

Network access shall be mocked whenever possible.

---

# 21. Security

Never log:

- API keys
- user credentials
- complete manuscripts

Validate all external input.

Use parameterized SQL queries exclusively.

---

# 22. Performance

Prefer readability over micro-optimization.

Optimize only after profiling.

Avoid unnecessary API requests.

Reuse cached results whenever possible.

---

# 23. Git

Commit messages shall be concise and descriptive.

Examples:

Add Crossref client

Implement bibliography parser

Improve cache lookup

Avoid vague messages such as:

Update

Fix

Changes

---

# 24. Documentation

Every public module shall include a module-level docstring.

Complex algorithms shall include explanatory comments.

Comments should explain why, not what.

---

# 25. Prohibited Practices

The following are prohibited:

- Wildcard imports
- Hardcoded API keys
- Hardcoded file paths
- Global mutable state
- Silent exception handling
- Circular imports
- Duplicate code
- Unused imports
- Dead code
- print() debugging in production code

---

# 26. Code Review Checklist

Before committing code, verify:

- Code passes Ruff.
- Code is formatted with Black.
- Type hints are complete.
- Public functions have docstrings.
- Tests pass.
- Logging is appropriate.
- No hardcoded values remain.
- No unnecessary dependencies were introduced.
- Documentation has been updated if required.

---

# 27. Design Principles

Every contribution shall follow these principles:

- Simplicity
- Readability
- Maintainability
- Determinism
- Modularity
- Testability
- Explainability
- Security
- Extensibility
- Consistency

---

# 28. Project Philosophy

Code should be written for long-term maintainability rather than short-term convenience.

Every line of code should make the software easier to understand, easier to test, and easier to extend.