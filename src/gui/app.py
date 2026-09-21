"""
Reference Checker GUI – built with NiceGUI.
Elegant, user‑friendly interface for non‑programmers.
Supports single and batch manuscript verification via the editor.
"""

import asyncio
import json
import tempfile
import webbrowser
from pathlib import Path
from typing import Any, Optional

from nicegui import ui

from workflow.manuscript import ManuscriptProcessor
from models import Reference
from verification.runner import verify_references
from report.exporter import ReportExporter

from internal_check.service import InternalCheckService
from internal_check.profiles import ENGLISH, TURKISH, GENERIC
from internal_check.models import IssueType

COLORS = {
    "primary": "#243f90",
    "secondary": "#cb9932",
    "support": "#77aed5",
    "danger": "#A91101",
    "success": "#2e7d32",
    "warning": "#ed6c02",
    "bg": "#f5f7fb",
    "card_bg": "#ffffff",
    "text": "#333333",
    "text_light": "#666666",
    "white": "#ffffff",
}

state: dict[str, Any] = {
    "references": [],
    "running": False,
    "editor_container": None,
    "results_container": None,
    "progress_label": None,
    "progress_bar": None,
    "progress_done": 0,
    "progress_total": 0,
    "report": None,
    "editor_rows": [],
    "editor_grid": None,
    "source_map": {},      # raw_text -> source filename
    "internal_check_result": None,
    "internal_check_profile": "en",
    "internal_check_container": None,
    "internal_check_file_name": "",
    "internal_check_results_container": None,
    "uploaded_files": [],       # list of {"name": str, "bytes": bytes}
}

tabs_ref: Optional[ui.tabs] = None
status_label: Optional[ui.label] = None


# -------- Upload (multi‑file) --------------------------------------------
async def handle_upload_multi(event):
    """Called when one or more files are uploaded (multiple=True)."""
    # event is a MultiUploadEventArguments; it has .files (list)
    files = event.files

    if state["running"]:
        ui.notify("Verification already in progress.", type="warning")
        return

    if not files:
        return

    state["uploaded_files"] = []

    status_label.set_text("Processing files...")
    ui.notify(f"Received {len(files)} file(s). Extracting references...", type="info")

    combined_rows = []
    source_map = {}

    for upload_item in files:
        # --- Robustly read file content --------------------------------
        file_bytes = None
        try:
            # Some versions expose .content as an async property
            if hasattr(upload_item, 'content'):
                content = upload_item.content
                if callable(content):
                    file_bytes = await content()
                else:
                    file_bytes = await content.read()
            # Some versions expose .file (async file-like)
            elif hasattr(upload_item, 'file'):
                file_bytes = await upload_item.file.read()
            # Last resort: maybe the item itself has .read()
            elif hasattr(upload_item, 'read'):
                file_bytes = await upload_item.read()
            else:
                # Log available attributes for debugging
                ui.notify(f"Cannot read {getattr(upload_item, 'name', 'unknown')}", type="negative")
                continue
        except Exception as read_exc:
            ui.notify(f"Failed to read upload: {read_exc}", type="negative")
            continue

        if not file_bytes:
            continue

        # Create a temporary file in the system temp directory
        # (always writable, even for installed apps)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        temp_file.write(file_bytes)
        temp_file.close()
        temp_path = Path(temp_file.name)

        # Get original filename
        file_name = getattr(upload_item, 'name', 'unknown.docx')
        state["uploaded_files"].append({"name": file_name, "bytes": file_bytes})

        try:
            processor = ManuscriptProcessor()
            refs = processor.extract_references(temp_path)
            for ref in refs:
                authors = "; ".join(ref.authors) if ref.authors else ""
                title = ref.title or ""
                year = str(ref.year) if ref.year else ""
                raw_text = ref.raw_text or ""
                row = {
                    "authors": authors,
                    "title": title,
                    "year": year,
                    "raw_text": raw_text,
                    "source": file_name,
                }
                combined_rows.append(row)
                source_map[raw_text] = file_name
        except Exception as exc:
            ui.notify(f"Error processing {file_name}: {exc}", type="negative")
        finally:
            # Remove the temporary file
            temp_path.unlink(missing_ok=True)

    if not combined_rows:
        status_label.set_text("No references found in the selected files.")
        ui.notify("No references found.", type="warning")
        return

    state["editor_rows"] = combined_rows
    state["source_map"] = source_map
    state["references"] = []
    status_label.set_text(f"Found {len(combined_rows)} references in {len(files)} file(s).")
    ui.notify(f"Found {len(combined_rows)} references. Review them in the Editor tab.", type="positive")

    build_editor_page()
    if tabs_ref:
        tabs_ref.value = "Editor"


# -------- Editor page (AG Grid, full width, editable) --------------------
def build_editor_page():
    if state["editor_container"] is None:
        return
    state["editor_container"].clear()

    rows = state["editor_rows"]

    with state["editor_container"]:
        ui.label("Review Extracted References").style(
            f"font-size: 1.8rem; font-weight: bold; color: {COLORS['primary']};"
        )
        ui.label("Single‑click any cell to edit. Changes are saved automatically.").style(
            f"color: {COLORS['text_light']};"
        )
        ui.space()

        grid_options = {
            "columnDefs": [
                {"headerName": "Source", "field": "source", "editable": True, "resizable": True},
                {"headerName": "Authors", "field": "authors", "editable": True, "resizable": True},
                {"headerName": "Title", "field": "title", "editable": True, "resizable": True},
                {"headerName": "Year", "field": "year", "editable": True, "resizable": True},
                {"headerName": "Raw Text", "field": "raw_text", "editable": True, "resizable": True},
            ],
            "rowData": rows,
            "defaultColDef": {"resizable": True, "sortable": True},
            "rowSelection": "multiple",
            "enableCellChangeFlash": True,
            "domLayout": "autoHeight",
            "width": "100%",
        }

        grid = ui.aggrid(grid_options).classes("w-full").style(
            f"border-radius: 8px; overflow: auto; width: 100% !important;"
        )
        state["editor_grid"] = grid

        def resize_grid():
            ui.run_javascript("""
                setTimeout(() => {
                    const grid = document.querySelector('.ag-theme-alpine');
                    if (grid && grid.__agGridInstance) {
                        grid.__agGridInstance.api.sizeColumnsToFit();
                    }
                }, 100);
            """)
        ui.timer(0.2, resize_grid, once=True)

        # Hidden input for delete selection
        hidden_input = ui.input(value="", label="").props("type=hidden id='editor-selection'").style("display:none")
        hidden_input.on_value_change(lambda e: on_editor_selection(e.value))

        with ui.row().classes("gap-2 mt-2"):
            ui.button("Add Row", on_click=add_row).props("outline color='secondary'")
            ui.button("Delete Selected", on_click=lambda: delete_selected()).props("outline color='negative'")
            ui.space()
            ui.button("Start Verification", on_click=start_verification).props("push color='secondary' text-color=white")
            ui.button("Back", on_click=lambda: setattr(tabs_ref, "value", "Upload") if tabs_ref else None).props("flat")


def add_row():
    new_row = {"source": "", "authors": "", "title": "", "year": "", "raw_text": ""}
    state["editor_rows"].append(new_row)
    build_editor_page()
    ui.timer(0.1, lambda: resize_grid(), once=True)


def delete_selected():
    ui.run_javascript("""
        const grid = document.querySelector('.ag-theme-alpine');
        if (grid && grid.__agGridInstance) {
            const api = grid.__agGridInstance.api;
            const selectedRows = api.getSelectedRows();
            const indices = selectedRows.map(row => api.getRowNode(row.__objectID).rowIndex);
            const input = document.getElementById('editor-selection');
            if (input) {
                input.value = JSON.stringify(indices);
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    """)


def on_editor_selection(value: str):
    if not value:
        return
    try:
        indices = json.loads(value)
    except Exception:
        return
    for idx in sorted(indices, reverse=True):
        if 0 <= idx < len(state["editor_rows"]):
            del state["editor_rows"][idx]
    build_editor_page()
    ui.timer(0.1, lambda: resize_grid(), once=True)


def start_verification():
    if state["running"]:
        return
    rows = state["editor_rows"]
    if not rows:
        ui.notify("No references to verify.", type="warning")
        return

    # Build Reference objects and preserve source mapping
    refs = []
    source_map = {}
    for row in rows:
        authors = [a.strip() for a in row["authors"].split(";") if a.strip()] if row["authors"] else []
        title = row["title"] or None
        year = int(row["year"]) if row["year"].isdigit() else None
        raw_text = row["raw_text"] or ""
        refs.append(Reference(raw_text=raw_text, title=title, authors=authors, year=year))
        if raw_text:
            source_map[raw_text] = row.get("source", "")

    state["source_map"] = source_map
    state["running"] = True
    state["progress_done"] = 0
    state["progress_total"] = len(refs)

    if tabs_ref:
        tabs_ref.value = "Progress"
    if state["progress_label"]:
        state["progress_label"].set_text("Verifying references...")
    if state["progress_bar"]:
        state["progress_bar"].value = 0

    asyncio.create_task(run_verification_bg(refs))


async def run_verification_bg(refs: list[Reference]):
    output_dir = Path.home() / "ReferenceChecker_Reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        def progress_callback(done: int, total: int):
            state["progress_done"] = done
            state["progress_total"] = total
            if total > 0:
                percent = done / total * 100
                if state["progress_bar"]:
                    state["progress_bar"].value = done / total
                if state["progress_label"]:
                    state["progress_label"].set_text(
                        f"Processing {done} of {total} ({percent:.1f}%)"
                    )

        report = await asyncio.to_thread(
            verify_references,
            refs,
            output_dir,
            progress_callback,
            source_name=None,
        )

        # Attach raw_text and source to each reference in the report
        source_map = state.get("source_map", {})
        for ref_dict, orig_ref in zip(report.get("references", []), refs):
            raw = orig_ref.raw_text or ""
            ref_dict["raw_text"] = raw
            ref_dict["source"] = source_map.get(raw, "")

        state["report"] = report
        build_results_page(report)
        if state["progress_label"]:
            state["progress_label"].set_text("Verification complete.")
        ui.notify("Verification complete.", type="positive")
    except Exception as e:
        ui.notify(f"Verification failed: {e}", type="negative")
        if state["progress_label"]:
            state["progress_label"].set_text("Verification failed.")
    finally:
        state["running"] = False
        if tabs_ref:
            tabs_ref.value = "Results"


# -------- Results page ---------------------------------------------------
def build_results_page(report: dict):
    if state["results_container"] is not None:
        state["results_container"].clear()

    with state["results_container"]:
        ui.label("Verification Complete").style(
            f"font-size: 1.8rem; font-weight: bold; color: {COLORS['primary']}; margin-bottom: 0.5rem;"
        )
        ui.label("Here is a summary of your manuscript's references.").style(f"color: {COLORS['text_light']};")
        ui.space()

        summary = report.get("summary", {})
        with ui.row().classes("justify-center gap-4 flex-wrap"):
            cards_data = [
                ("Total", summary.get("total", 0), COLORS["primary"]),
                ("Verified", summary.get("verified", 0), COLORS["success"]),
                ("Manual Review", summary.get("manual_review", 0), COLORS["warning"]),
                ("Failed", summary.get("failed", 0), COLORS["danger"]),
                ("Avg Confidence", f"{summary.get('average_confidence', 0):.3f}", COLORS["primary"]),
            ]
            for label, value, color in cards_data:
                with ui.card().style(
                    f"background-color: {COLORS['card_bg']}; border-radius: 12px; "
                    f"box-shadow: 0 2px 12px rgba(0,0,0,0.08); min-width: 120px; padding: 1rem;"
                ):
                    ui.label(str(value)).style(
                        f"font-size: 2.2rem; font-weight: bold; color: {color}; text-align: center;"
                    )
                    ui.label(label).style(f"color: {COLORS['text_light']}; text-align: center; font-size: 0.85rem;")

        ui.space()

        ui.button("📥 Download Report (HTML)", on_click=lambda: download_report(report)).props(
            "push color='secondary' text-color=white"
        ).classes("mb-4")

        refs = report.get("references", [])
        table_rows = []
        for ref in refs:
            status = ref.get("status", "unknown")
            if status == "verified":
                status_display = "Verified"
            elif status == "manual_review":
                status_display = "Manual Review"
            else:
                status_display = status.replace("_", " ").title()

            row = {
                "title": ref.get("raw_text") or ref.get("title", "Unknown"),
                "status": status_display,
                "confidence": f"{ref.get('confidence', 0):.3f}",
            }
            if ref.get("source"):
                row["source"] = ref["source"]
            table_rows.append(row)

        columns = [
            {"name": "title", "label": "Title", "field": "title", "align": "left"},
        ]
        if any("source" in r for r in table_rows):
            columns.append({"name": "source", "label": "Source", "field": "source", "align": "left"})
        columns.extend([
            {"name": "status", "label": "Status", "field": "status", "align": "left"},
            {"name": "confidence", "label": "Confidence", "field": "confidence", "align": "center"},
        ])

        ui.table(columns=columns, rows=table_rows).classes("w-full mt-4").style(f"border-radius: 8px; overflow: hidden;")

        manual_refs = [r for r in refs if r.get("search_url")]
        if manual_refs:
            ui.space()
            ui.label("References that need manual review").style(
                f"font-size: 1.4rem; font-weight: bold; color: {COLORS['primary']}; margin-top: 2rem;"
            )
            with ui.column().classes("gap-4"):
                for ref in manual_refs:
                    with ui.card().style(
                        f"background-color: {COLORS['card_bg']}; border-radius: 12px; "
                        f"box-shadow: 0 2px 12px rgba(0,0,0,0.08); padding: 1.5rem;"
                    ):
                        raw_text = ref.get("raw_text", ref.get("title", "Unknown"))
                        if ref.get("source"):
                            raw_text = f"[{ref['source']}] {raw_text}"
                        ui.label(raw_text).style(
                            f"font-weight: bold; color: {COLORS['text']}; white-space: pre-wrap;"
                        )
                        ui.label(f"Confidence: {ref.get('confidence', 0):.3f}").style(
                            f"color: {COLORS['text_light']}; font-size: 0.9rem;"
                        )
                        ui.link("Search in Google", ref["search_url"], new_tab=True).props(
                            f"outline color='primary' size=sm"
                        )
        else:
            ui.label("All references were verified. 🎉").style(
                f"color: {COLORS['success']}; font-weight: bold; margin-top: 1.5rem;"
            )


async def download_report(report: dict):
    """Generate HTML report and open it in the default web browser."""
    try:
        exporter = ReportExporter()
        tmp = Path(tempfile.gettempdir()) / "reference_report.html"
        await asyncio.to_thread(exporter.export_html, report, tmp)
        # Open the report in the default browser – works in any interface mode
        webbrowser.open(f"file://{tmp.as_posix()}")
        ui.notify("Report opened in your browser.", type="positive")
    except Exception as e:
        ui.notify(f"Failed to generate report: {e}", type="negative")

# -------- Internal Check page -------------------------------------------
def run_internal_check():
    """Run the internal consistency check on the uploaded manuscript."""
    if state.get("internal_check_running"):
        return

    files = state.get("uploaded_files", [])
    if not files:
        ui.notify("Please upload a manuscript first (Upload tab).", type="warning")
        return

    file_data = files[0]
    file_name = file_data["name"]
    file_bytes = file_data["bytes"]

    profile_map = {"en": ENGLISH, "tr": TURKISH, "generic": GENERIC}
    profile = profile_map.get(state["internal_check_profile"], ENGLISH)

    # Use editor references if the user has reviewed them; otherwise fresh parse.
    refs = None
    if state.get("editor_rows"):
        refs = []
        for row in state["editor_rows"]:
            authors = (
                [a.strip() for a in row["authors"].split(";") if a.strip()]
                if row["authors"] else []
            )
            title = row["title"] or None
            year = int(row["year"]) if row["year"].isdigit() else None
            raw_text = row["raw_text"] or ""
            refs.append(
                Reference(
                    raw_text=raw_text,
                    title=title,
                    authors=authors,
                    year=year,
                )
            )

    state["internal_check_running"] = True
    ui.notify("Running internal check...", type="info")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    temp_file.write(file_bytes)
    temp_file.close()
    temp_path = Path(temp_file.name)

    try:
        service = InternalCheckService(profile=profile)
        if refs is not None:
            result = service.check_docx_with_references(temp_path, refs)
        else:
            result = service.check_docx(temp_path)
        state["internal_check_result"] = result
        state["internal_check_file_name"] = file_name
        _refresh_internal_check_results()
        ui.notify("Internal check complete.", type="positive")
    except Exception as e:
        ui.notify(f"Internal check failed: {e}", type="negative")
    finally:
        temp_path.unlink(missing_ok=True)
        state["internal_check_running"] = False


def build_internal_check_page():
    """Render the Internal Check tab from current state."""
    container = state.get("internal_check_container")
    if container is None:
        return
    container.clear()

    with container:
        ui.label("Internal Consistency Check").style(
            f"font-size: 1.8rem; font-weight: bold; color: {COLORS['primary']};"
        )
        ui.label(
            "Verify that every in-text citation has a reference and every "
            "reference is cited in text."
        ).style(f"color: {COLORS['text_light']}; margin-bottom: 0.5rem;")
        ui.space()

        with ui.row().classes("items-center gap-4"):
            label_to_key = {"English": "en", "Turkish": "tr", "Generic": "generic"}
            key_to_label = {v: k for k, v in label_to_key.items()}
            ui.select(
                options=list(label_to_key.keys()),
                value=key_to_label.get(state["internal_check_profile"], "English"),
                label="Language Profile",
                on_change=lambda e: state.update(
                    {"internal_check_profile": label_to_key.get(e.value, "en")}
                ),
            ).classes("min-w-[220px]")
            ui.button(
                "Run Internal Check",
                on_click=run_internal_check,
            ).props("push color='secondary' text-color=white")
            if state.get("editor_rows"):
                ui.label("Using edited references from the Editor tab.").style(
                    f"color: {COLORS['success']}; font-size: 0.85rem;"
                )
            else:
                ui.label("No edited references. Will extract from the DOCX.").style(
                    f"color: {COLORS['text_light']}; font-size: 0.85rem;"
                )

        ui.space()

        # Results live in their own child container, so refreshing them
        # does not destroy the controls above.
        results_container = ui.column().classes("w-full")
        state["internal_check_results_container"] = results_container
        _render_results_into(results_container)


def _render_results_into(results_container):
    """Render the current result (if any) into the given container."""
    with results_container:
        result = state.get("internal_check_result")
        if result is None:
            ui.label(
                "No check has been run yet. Upload a manuscript, then click Run."
            ).style(f"color: {COLORS['text_light']}; margin-top: 1rem;")
        else:
            render_internal_check_results(result)


def _refresh_internal_check_results():
    """Rebuild only the results area; leave the controls intact."""
    results_container = state.get("internal_check_results_container")
    if results_container is None:
        return
    results_container.clear()
    _render_results_into(results_container)


def render_internal_check_results(result):
    """Render summary cards and issue tables for a completed check."""
    summary = result.summary

    with ui.row().classes("justify-center gap-4 flex-wrap"):
        cards = [
            ("Citations", summary.get("citations_found", 0), COLORS["primary"]),
            ("References", summary.get("references_found", 0), COLORS["primary"]),
            ("Missing", summary.get("missing_references", 0), COLORS["danger"]),
            ("Uncited", summary.get("uncited_references", 0), COLORS["warning"]),
        ]
        for label, value, color in cards:
            with ui.card().style(
                f"background-color: {COLORS['card_bg']}; border-radius: 12px; "
                f"box-shadow: 0 2px 12px rgba(0,0,0,0.08); min-width: 120px; padding: 1rem;"
            ):
                ui.label(str(value)).style(
                    f"font-size: 2.2rem; font-weight: bold; color: {color}; text-align: center;"
                )
                ui.label(label).style(
                    f"color: {COLORS['text_light']}; text-align: center; font-size: 0.85rem;"
                )

    ui.space()

    missing = result.missing_references()
    uncited = result.uncited_references()

    if missing:
        ui.label("Missing References").style(
            f"font-size: 1.4rem; font-weight: bold; color: {COLORS['danger']}; margin-top: 1rem;"
        )
        rows = []
        for issue in missing:
            c = issue.citation
            rows.append({
                "citation": c.raw if c else "",
                "location": c.location if c and c.location else "",
                "message": issue.message,
            })
        ui.table(
            columns=[
                {"name": "citation", "label": "Citation", "field": "citation", "align": "left"},
                {"name": "location", "label": "Location", "field": "location", "align": "left"},
                {"name": "message", "label": "Detail", "field": "message", "align": "left"},
            ],
            rows=rows,
        ).classes("w-full").style("border-radius: 8px; overflow: hidden;")

    if uncited:
        ui.label("Uncited References").style(
            f"font-size: 1.4rem; font-weight: bold; color: {COLORS['warning']}; margin-top: 1.5rem;"
        )
        rows = []
        for issue in uncited:
            ref = issue.reference
            text = ref.raw_text[:160] if ref and ref.raw_text else issue.message
            rows.append({"reference": text, "message": issue.message})
        ui.table(
            columns=[
                {"name": "reference", "label": "Reference", "field": "reference", "align": "left"},
                {"name": "message", "label": "Detail", "field": "message", "align": "left"},
            ],
            rows=rows,
        ).classes("w-full").style("border-radius: 8px; overflow: hidden;")

    if not missing and not uncited:
        ui.label("All citations and references are consistent. 🎉").style(
            f"color: {COLORS['success']}; font-weight: bold; margin-top: 1.5rem;"
        )

# -------- About page -----------------------------------------------------
def build_about_page():
    with ui.column().classes("w-full items-center"):
        ui.label("About Reference Checker").style(
            f"font-size: 2rem; font-weight: bold; color: {COLORS['primary']}; margin-bottom: 1rem;"
        )
        ui.label("Verify your manuscript's references with confidence.").style(
            f"font-size: 1.2rem; color: {COLORS['text_light']}; margin-bottom: 2rem;"
        )
        with ui.card().style(
            f"background-color: {COLORS['card_bg']}; border-radius: 12px; "
            f"box-shadow: 0 2px 12px rgba(0,0,0,0.08); padding: 2rem; width: 600px; max-width: 90%;"
        ):
            ui.label("Software Information").style(f"font-weight: bold; color: {COLORS['primary']};")
            ui.separator()
            ui.label("Reference Checker v1.0").style(f"color: {COLORS['text']};")
            ui.label("A tool for verifying bibliographic references in academic manuscripts.").style(
                f"color: {COLORS['text']};"
            )
            ui.label("License: MIT – Open to everyone. Free to use, modify, and distribute.").style(f"color: {COLORS['text']};")
            ui.space()
            ui.label("Developer Information").style(f"font-weight: bold; color: {COLORS['primary']};")
            ui.separator()
            ui.label("Developed by: Kutay Uzun").style(f"color: {COLORS['text']};")
            ui.label("Contact: kutayuzun@trakya.edu.tr").style(f"color: {COLORS['text']};")
            ui.space()
            ui.label("Acknowledgments").style(f"font-weight: bold; color: {COLORS['primary']};")
            ui.separator()
            ui.label("This tool uses Crossref and OpenLibrary APIs for metadata verification. The tool has been developed with assisstance from Deepseek-v4.").style(
                f"color: {COLORS['text']};"
            )


# -------- Main page ------------------------------------------------------
@ui.page("/")
def main():
    global tabs_ref, status_label

    ui.colors(primary=COLORS['primary'], secondary=COLORS['secondary'], accent=COLORS['support'])

    ui.add_head_html(f"""
    <style>
        body {{
            background-color: {COLORS['bg']};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: {COLORS['text']};
        }}
        .q-tab {{
            font-weight: 500;
            color: {COLORS['text_light']} !important;
        }}
        .q-tab--active {{
            color: {COLORS['primary']} !important;
            font-weight: bold;
        }}
        .q-tabs__indicator {{
            background-color: {COLORS['primary']} !important;
        }}
    </style>
    """)

    with ui.header().style(
        f"background-color: {COLORS['primary']}; color: {COLORS['white']}; "
        "padding: 1rem 2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.15);"
    ):
        ui.label("📄 Reference Checker").style("font-size: 1.6rem; font-weight: bold;")
        ui.label("Verify your manuscript's references effortlessly.").style("opacity: 0.85; font-size: 0.9rem;")

    with ui.tabs().classes("w-full justify-center").style(
        f"background-color: {COLORS['white']}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);"
    ) as tabs:
        tabs_ref = tabs
        ui.tab("Upload", icon="upload")
        ui.tab("Editor", icon="edit")
        ui.tab("Progress", icon="hourglass_empty")
        ui.tab("Results", icon="verified")
        ui.tab("Internal Check", icon="rule")
        ui.tab("About", icon="info")
        tabs.value = "Upload"

    with ui.tab_panels(tabs, value="Upload", keep_alive=True).classes("w-full").style(
        f"padding: 2rem; background-color: {COLORS['bg']};"
    ):
        with ui.tab_panel("Upload"):
            with ui.column().classes("items-center"):
                ui.label("Upload Your Manuscript").style(
                    f"font-size: 1.8rem; font-weight: bold; color: {COLORS['primary']}; margin-bottom: 0.5rem;"
                )
                ui.label("Drop one or more .docx files below or click to browse.").style(
                    f"color: {COLORS['text_light']}; margin-bottom: 2rem;"
                )
                # Use on_multi_upload for multi-file support
                ui.upload(
                    label="Drop your DOCX files here or click to browse",
                    multiple=True,
                    auto_upload=True,
                    on_multi_upload=handle_upload_multi,
                ).props('accept=".docx"').style(
                    f"border: 2px dashed {COLORS['support']}; border-radius: 12px; "
                    f"padding: 2rem; background-color: {COLORS['white']};"
                )
                status_label = ui.label().style(
                    f"margin-top: 1.5rem; font-size: 1rem; color: {COLORS['text_light']};"
                )

        with ui.tab_panel("Editor"):
            state["editor_container"] = ui.column().classes("w-full")

        with ui.tab_panel("Progress"):
            with ui.column().classes("w-full items-center"):
                ui.spinner(size="lg", color=COLORS["primary"])
                state["progress_label"] = ui.label("Waiting for verification to start...").style(
                    f"font-size: 1.2rem; color: {COLORS['text_light']}; margin-top: 1rem;"
                )
                state["progress_bar"] = ui.linear_progress(value=0).props(
                    "size=20px color=primary"
                ).classes("w-1/2 mt-4")

        with ui.tab_panel("Results"):
            state["results_container"] = ui.column().classes("w-full")

        with ui.tab_panel("Internal Check"):
            state["internal_check_container"] = ui.column().classes("w-full")
            build_internal_check_page()

        with ui.tab_panel("About"):
            build_about_page()

    # Rebuild editor when Editor tab is selected
    def on_tab_change(e):
        if e.value == "Editor":
            build_editor_page()
    tabs.on_value_change(on_tab_change)

    with ui.footer().style(
        f"background-color: {COLORS['white']}; padding: 0.8rem; text-align: center; "
        f"color: {COLORS['text_light']}; font-size: 0.85rem; border-top: 1px solid #e0e0e0;"
    ):
        ui.label("Reference Checker v1.0").style("margin: 0 auto;")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Reference Checker", native=False, window_size=(1200, 800), favicon="📄", show=True)