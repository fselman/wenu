"""Structural contracts for the Milestone 46D.8 visual handoff."""

import importlib.util
from pathlib import Path
import sys


PATH = Path("tools/render_46d8_visual_matrix.py")
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
