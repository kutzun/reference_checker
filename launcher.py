"""
Launcher for the packaged Reference Checker application.
"""
from src.gui.app import main  # imports the page definition
from nicegui import ui
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    # Use browser mode for compatibility; can be changed to native=True if desired
    ui.run(
        title="Reference Checker",
        native=False,
        window_size=(1200, 800),
        favicon="📄",
        show=True,
        reload=False,
    )