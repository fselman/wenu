"""Milestone 45G documentation and v0.7 closure contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs" / "developer"
USER_GUIDE = ROOT / "docs" / "user_guide"


def read(path):
    return path.read_text(encoding="utf-8")


def test_public_references_identify_v07_as_implemented():
    readme = read(ROOT / "README.md")
    readme_es = read(ROOT / "README.es.md")
    reference = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")
    guide = read(USER_GUIDE / "index.md")

    assert "v0.7 explicit-reference architecture" in readme
    assert "Wenu v0.7 user guide" in readme
    assert "migración v0.7" in readme_es
    assert "guía de usuario v0.7" in readme_es
    assert "**Architecture version:** 0.7" in reference
    assert "**Architecture version:** 0.7" in source_tree
    assert guide.startswith("# Wenu v0.7 user guide")


def test_reference_documents_explicit_grid_contract():
    reference = read(DEVELOPER / "implementation_reference.md")
    guide = read(USER_GUIDE / "styles_modes_detail.md")

    for switch in (
        "--equatorial-grid",
        "--ecliptic-grid",
        "--galactic-grid",
        "--grid-references",
    ):
        assert switch in reference or switch in guide
    assert "black, orange, and blue" in reference
    assert "Grid labels" in guide
    assert "--coordinate-grid`" not in reference
    assert "--coordinate-grid-labels`" not in reference


def test_planisphere_documentation_records_final_composition():
    guide = read(USER_GUIDE / "planisphere.md")
    for phrase in (
        "interior is opaque",
        "outside the horizon",
        "transparent",
        "legends are placed outside",
        "Spanish title",
        "Library-wide legend defaults remain English",
    ):
        assert phrase in guide


def test_migration_is_closed_at_accepted_runtime_baseline():
    target = read(DEVELOPER / "target_architecture_v0.7.md")
    roadmap = read(DEVELOPER / "wenu_migration_0.6_to_0.7.md")

    assert "**Status:** Implemented" in target
    assert "**Implementation baseline:** `61fc73e`" in target
    assert "**Status:** Complete" in roadmap
    assert "**Implemented through:** `61fc73e`" in roadmap
    assert "995 tests with warnings treated as errors" in roadmap
    assert "shared" in roadmap
    assert "Conda base environment" in roadmap
    assert "visually approved" in roadmap
