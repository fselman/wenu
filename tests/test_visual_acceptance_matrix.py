"""Structural contracts for the Milestone 46D.8 visual handoff."""

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "render_46d8_visual_matrix.py"
REVIEW = (
    ROOT / "docs" / "developer" / "archive" / "acceptance_history"
    / "visual_acceptance_46d8.md"
)
FAMILIES = {
    "all-sky", "planisphere", "regional-single", "regional-group",
    "circumpolar", "binocular",
}


def _module():
    spec = importlib.util.spec_from_file_location("visual_matrix", PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_matrix_contains_canonical_style_mode_pairs_and_unique_outputs():
    matrix = _module().MATRIX
    names = [entry.name for entry in matrix]

    assert len(matrix) == 18
    assert len(names) == len(set(names))
    for family in FAMILIES:
        assert f"canonical-{family}-atlas-print" in names
        assert f"canonical-{family}-cartoon-presentation" in names


def test_diagnostics_cover_every_visual_closure_role():
    matrix = _module().MATRIX
    arguments = " ".join(
        argument for entry in matrix for argument in entry.arguments
    )

    for option in (
        "--mask", "--horizon", "--horizon-mask",
        "--field-width", "--field-height", "--position-angle",
        "--altaz-grid", "--equatorial-grid", "--ecliptic-grid",
        "--galactic-grid", "--grid-references", "--poles",
        "--legends", "--star-counts", "--credits",
    ):
        assert option in arguments


def test_mask_diagnostics_do_not_conflate_independent_openings():
    entries = {entry.name: entry for entry in _module().MATRIX}
    all_sky = entries["diagnostic-all-sky-constellation-mask"].arguments
    regional = entries["diagnostic-regional-explicit-field-mask"].arguments

    for arguments in (all_sky, regional):
        assert "--mask" in arguments
        assert "--horizon-mask" not in arguments
        assert "--horizon" not in arguments


def test_horizon_diagnostic_uses_a_family_with_a_proven_crossing():
    entries = {entry.name: entry for entry in _module().MATRIX}
    arguments = entries["diagnostic-circumpolar-horizon"].arguments

    assert "--horizon" in arguments
    assert "--horizon-mask" in arguments
    assert arguments[arguments.index("--limiting-declination") + 1] == "-40"


def test_every_entry_selects_one_supported_product():
    matrix = _module().MATRIX

    for entry in matrix:
        arguments = entry.arguments
        style = arguments[arguments.index("--style") + 1]
        mode = arguments[arguments.index("--mode") + 1]
        assert (style, mode) in {
            ("atlas", "print"),
            ("cartoon", "presentation"),
        }


def test_every_entry_has_the_fixed_acceptance_magnitude_limit():
    for entry in _module().MATRIX:
        arguments = entry.arguments
        magnitude = arguments[arguments.index("--magnitude-limit") + 1]
        expected = "11.0" if "binocular" in entry.name else "5.0"

        assert magnitude == expected


def test_review_records_shared_remediation_owners_and_current_baseline():
    review = REVIEW.read_text(encoding="utf-8")

    assert "**Reviewed source commit:** `84baedb`" in review
    assert "**Review record commit:** `a6739a7`" in review
    for finding in (
        "GRID-1", "GRID-2", "GRID-3", "DETAIL-1", "CARTOON-1",
        "MASK-1", "MASK-2", "HORIZON-1", "BINOCULAR-1",
        "BINOCULAR-2",
    ):
        assert f"| {finding} |" in review


def test_review_closes_truthfully_without_claiming_a_deferred_rerun():
    review = REVIEW.read_text(encoding="utf-8")

    assert "**Accepted source commit:** `2883e67`" in review
    assert "complete post-remediation 18-product rerun deferred" in review
    assert "Fernando Selman, 2026-08-15 (final closure acceptance)" in review
    assert "not represented by newly\nchecked product rows" in review
