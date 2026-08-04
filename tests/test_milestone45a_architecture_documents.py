"""Milestone 45A v0.7 architecture-document contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs" / "developer"
CURRENT = DEVELOPER / "current_architecture_v0.6.md"
TARGET = DEVELOPER / "target_architecture_v0.7.md"
ROADMAP = DEVELOPER / "wenu_migration_0.6_to_0.7.md"


def read(path):
    return path.read_text(encoding="utf-8")


def test_v07_architecture_documents_exist_and_cross_reference():
    current = read(CURRENT)
    target = read(TARGET)
    roadmap = read(ROADMAP)

    assert "**Status:** Implemented baseline" in current
    assert "**Baseline commit:** `054d0c0`" in current
    assert "target_architecture_v0.7.md" in current
    assert "wenu_migration_0.6_to_0.7.md" in current

    assert "**Status:** Implemented" in target
    assert "**Implementation baseline:** `61fc73e`" in target
    assert "current_architecture_v0.6.md" in target
    assert "wenu_migration_0.6_to_0.7.md" in target

    assert "**Status:** Complete" in roadmap
    assert "**Implemented through:** `61fc73e`" in roadmap
    assert "**Base commit:** `054d0c0`" in roadmap
    assert "current_architecture_v0.6.md" in roadmap
    assert "target_architecture_v0.7.md" in roadmap


def test_target_defines_independent_opt_in_grid_contract():
    target = read(TARGET)
    for switch in (
        "--constellation-lines",
        "--equatorial-grid",
        "--equatorial-grid-labels",
        "--ecliptic-grid",
        "--ecliptic-grid-labels",
        "--galactic-grid",
        "--galactic-grid-labels",
        "--grid-references",
        "--all-products",
    ):
        assert switch in target
    assert "all three" in target
    assert "coordinate grids and their labels" in target
    assert "are off" in target


def test_target_records_semantic_grid_line_and_label_colors():
    target = read(TARGET)
    for system, color in (
        ("Equatorial", "black"),
        ("Ecliptic", "orange"),
        ("Galactic", "blue"),
    ):
        assert f"| {system} | {color} | {color} |" in target


def test_target_records_reference_and_planisphere_repairs():
    target = read(TARGET)
    for phrase in (
        "local projected curve",
        "resolved style sky color",
        "transparent",
        "clear of the circular sky",
    ):
        assert phrase in target


def test_roadmap_is_incremental_and_preserves_ownership():
    roadmap = read(ROADMAP)
    for suffix in "ABCDEFG":
        assert f"Milestone 45{suffix}" in roadmap
    assert "keep content selection" in roadmap
    assert "keep colors, widths, fonts" in roadmap
    assert "keep legend placement in legend policy" in roadmap
    assert "## 10. Stop conditions" in roadmap


def test_assistant_instructions_name_active_v07_authority():
    instructions = read(DEVELOPER / "assistant_instructions.md")
    for name in (
        "current_architecture_v0.6.md",
        "target_architecture_v0.7.md",
        "wenu_migration_0.6_to_0.7.md",
    ):
        assert name in instructions
