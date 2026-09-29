Document: GUI_SPEC.md
Version: 1.0
Status: Frozen
Last Updated: 2026-08-07
Author: Kutay Uzun

# GUI_SPEC.md

# Reference Checker User Interface Specification

---

# 1. Purpose

This document specifies the graphical user interface (GUI) of Reference Checker.

The GUI is designed to provide a simple, intuitive, and responsive workflow for verifying bibliographic references while exposing only the controls necessary for the verification process.

The interface shall prioritize clarity, speed, and reliability over visual complexity.

---

# 2. Design Principles

The GUI shall follow these principles.

- Simplicity
- Consistency
- Responsiveness
- Accessibility
- Explainability
- Non-destructive operation

The GUI shall never modify the original manuscript.

---

# 3. User Workflow

The primary workflow is:

```
Launch Application

↓

Select File(s)

↓

Configure Options

↓

Start Verification

↓

Monitor Progress

↓

Review Results

↓

Export Report

↓

Finish
```

The user should be able to complete the entire workflow from a single main window.

---

# 4. Main Window

The application consists of one primary window.

Sections:

1. Toolbar
2. File Selection
3. Verification Options
4. Output Options
5. Progress
6. Activity Log
7. Control Buttons

---

# 5. Toolbar

Contains:

- Open Files
- Open Folder
- Settings
- Help
- About

---

# 6. File Selection

Displays selected files.

Functions:

- Add Files
- Add Folder
- Remove Selected
- Clear List

Supported file type:

- .docx

Drag-and-drop shall be supported.

---

# 7. Verification Options

Users may configure:

- Crossref
- OpenAlex
- Cache usage
- Cache lifetime
- API timeout
- Maximum concurrent requests

Reasonable defaults shall be provided.

---

# 8. Output Options

Users may select one or more report formats.

Supported formats:

- Excel (.xlsx)
- CSV (.csv)
- PDF (.pdf)

Users may choose an output directory.

---

# 9. Progress Display

Three progress indicators shall be displayed.

## Batch Progress

Overall processing progress.

Example:

```
Documents

12 / 40
```

---

## Document Progress

Current document.

Example:

```
paper12.docx
```

---

## Reference Progress

Current reference.

Example:

```
Reference

18 / 56
```

---

Additional information:

- Elapsed time
- Estimated remaining time

---

# 10. Activity Log

Displays important events.

Examples:

```
Loading document...

Bibliography detected.

Extracted 48 references.

Checking cache...

Querying Crossref...

Querying OpenAlex...

Generating report...
```

The log shall auto-scroll.

---

# 11. Verification Results

After completion, the GUI displays summary statistics.

Examples:

Total References

Verified

Manual Review

Failed

Skipped

Processing Time

Average Verification Time

Cache Hit Rate

---

# 12. Export

Buttons:

Open Report

Open Output Folder

Copy Summary

Close

---

# 13. Status Indicators

Every reference receives one status.

Verified

Manual Review

Failed

Skipped

Status shall be represented using both text and color.

---

# 14. Error Messages

Errors shall be informative.

Example:

Crossref unavailable.

Using OpenAlex.

Another example:

Output folder is not writable.

Choose another folder.

Errors shall never expose internal exceptions.

---

# 15. Settings Window

Contains:

General

Verification

Cache

API

Reports

Advanced

Users shall be able to restore default settings.

---

# 16. About Window

Displays:

Software version

Database version

Supported providers

License

Project website (future)

---

# 17. Accessibility

The interface shall support:

Resizable window

Keyboard navigation

High-DPI displays

Screen readers where supported

Scalable fonts

Color-independent status indicators

---

# 18. Responsiveness

The GUI shall remain responsive during processing.

Long-running tasks shall execute in background worker threads.

The user shall be able to:

Pause

Resume

Cancel

Batch processing.

---

# 19. Future Expansion

The GUI architecture shall allow future addition of:

Dark mode

Additional verification providers

Plugin system

Command-line mode

Web interface

Additional report formats

Without redesigning the existing interface.