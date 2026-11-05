"""
Tests for the GUI state reset performed when a new manuscript is uploaded.

Without this reset, results from a previously verified manuscript leak
into the next run: the Results tab still shows the old report, the
Internal Check tab still shows the old consistency result, and progress
counters still reflect the previous verification.
"""

from gui import app


def _seed_stale_state():
    """Populate the state dict with values that must not survive a new upload."""
    app.state["report"] = {"references": [{"title": "old manuscript"}]}
    app.state["progress_done"] = 7
    app.state["progress_total"] = 12
    app.state["internal_check_result"] = {"summary": {"citations_found": 99}}
    app.state["internal_check_file_name"] = "old.docx"
    app.state["internal_check_running"] = True


def test_reset_clears_previous_report():
    _seed_stale_state()
    app._reset_stale_state()
    assert app.state["report"] is None


def test_reset_clears_progress_counters():
    _seed_stale_state()
    app._reset_stale_state()
    assert app.state["progress_done"] == 0
    assert app.state["progress_total"] == 0


def test_reset_clears_internal_check_result_and_filename():
    _seed_stale_state()
    app._reset_stale_state()
    assert app.state["internal_check_result"] is None
    assert app.state["internal_check_file_name"] == ""


def test_reset_clears_running_flag():
    _seed_stale_state()
    app._reset_stale_state()
    assert app.state["internal_check_running"] is False


def test_reset_preserves_user_profile_choice():
    """Language profile is a user preference, not per-manuscript state."""
    app.state["internal_check_profile"] = "tr"
    app._reset_stale_state()
    assert app.state["internal_check_profile"] == "tr"


def test_reset_preserves_ui_element_references():
    """UI refs (containers, labels, bars) must survive so the app can still render."""
    app.state["progress_label"] = "sentinel"
    app.state["progress_bar"] = "sentinel"
    app.state["results_container"] = "sentinel"
    app._reset_stale_state()
    assert app.state["progress_label"] == "sentinel"
    assert app.state["progress_bar"] == "sentinel"
    assert app.state["results_container"] == "sentinel"