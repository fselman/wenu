"""Milestone 44A v0.6 architecture-document contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs/developer"
CURRENT = DEVELOPER / "current_architecture_v0.5.md"
TARGET = DEVELOPER / "target_architecture_v0.6.md"
ROADMAP = DEVELOPER / "wenu_migration_0.5_to_0.6.md"


def read(path):
    return path.read_text(encoding="utf-8")


def test_v06_architecture_documents_exist_and_cross_reference():
    current = read(CURRENT)
    target = read(TARGET)
    roadmap = read(ROADMAP)

    assert "**Status:** Implemented baseline" in current
    assert "**Baseline commit:** `33cd5aa`" in current
    assert "target_architecture_v0.6.md" in current
    assert "wenu_migration_0.5_to_0.6.md" in current

    assert "**Status:** Implemented" in target
    assert "current_architecture_v0.5.md" in target
    assert "wenu_migration_0.5_to_0.6.md" in target

    assert "**Status:** Complete" in roadmap
    assert "**Base commit:** `33cd5aa`" in roadmap
    assert "current_architecture_v0.5.md" in roadmap
    assert "target_architecture_v0.6.md" in roadmap


def test_audit_and_final_example_contract_are_recorded():
    current = read(CURRENT)
    target = read(TARGET)
    roadmap = read(ROADMAP)

    assert "23 scripts" in current
    assert "760 tests pass" in current
    for name in (
        "planisphere.py",
        "regional_constellation_group.py",
        "regional_constellation.py",
        "circumpolar.py",
        "binocular_object.py",
    ):
        assert name in target
    assert "20 products" in target
    assert "Replace before deleting" in roadmap


def test_requested_chart_furniture_is_owned_by_the_target():
    target = read(TARGET)
    for concept in (
        "outside mask",
        "Ecliptic",
        "Galactic plane",
        "NCP",
        "SCP",
        "NEP",
        "SEP",
        "NGP",
        "SGP",
        "copyright",
        "application name",
        "cumulative visible-star count",
    ):
        assert concept in target
    assert "actually rendered chart stars" in target
    assert "less than or equal to `m`" in target


def test_roadmap_is_incremental_and_closes_at_44k():
    roadmap = read(ROADMAP)
    for suffix in "ABCDEFGHIJK":
        assert f"Milestone 44{suffix}" in roadmap
    assert "## 15. Stop conditions" in roadmap
    assert "## 16. Completion definition" in roadmap


def test_assistant_instructions_name_the_active_authority():
    instructions = read(DEVELOPER / "assistant_instructions.md")
    for name in (
        "current_architecture_v0.5.md",
        "target_architecture_v0.6.md",
        "wenu_migration_0.5_to_0.6.md",
    ):
        assert name in instructions
