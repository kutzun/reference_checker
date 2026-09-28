"""
Launcher for the packaged Reference Checker application.
"""
import sys
from pathlib import Path

# Put src/ on sys.path so top-level modules (gui, workflow, models, ...)
# import cleanly. Mirrors the `pythonpath = ["src"]` setting in
# pyproject.toml and the `where = ["src"]` package layout.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from nicegui import ui  # noqa: E402  (import after sys.path setup)
from gui.app import main  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    ui.run(
        title="Reference Checker",
        native=False,
        window_size=(1200, 800),
        favicon="📄",
        show=True,
        reload=False,
    )