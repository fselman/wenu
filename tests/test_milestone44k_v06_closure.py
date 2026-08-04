"""Milestone 44K v0.6 migration-closure contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs" / "developer"


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_historical_architecture_documents_record_v06_completion():
    target = read("docs/developer/target_architecture_v0.6.md")
    roadmap = read("docs/developer/wenu_migration_0.5_to_0.6.md")
    assert "**Status:** Implemented" in target
    assert "**Status:** Complete" in roadmap
    assert "Milestone 44K completed the migration" in roadmap


def test_public_status_and_assistant_authority_are_current():
    readme = read("README.md")
    readme_es = read("README.es.md")
    instructions = read("docs/developer/assistant_instructions.md")

    assert (
        "v0.7 explicit-reference architecture and migration are complete"
        in readme
    )
    assert (
        "target_architecture_v0.7.md` (implemented architecture)"
        in readme
    )
    assert (
        "wenu_migration_0.6_to_0.7.md` (completed roadmap)"
        in readme
    )
    assert (
        "target_architecture_v0.6.md` as the implemented architecture"
        in instructions
    )
    assert "completed migration history" in instructions
    assert "migración v0.7 están" in readme_es
    assert "completas" in readme_es


def test_exact_canonical_example_set_is_preserved():
    expected = {
        "binocular_object.py",
        "circumpolar.py",
        "planisphere.py",
        "regional_constellation.py",
        "regional_constellation_group.py",
    }
    assert {path.name for path in (ROOT / "examples").glob("*.py")} == expected


def test_closure_records_dependency_warning_and_visual_audits():
    roadmap = read("docs/developer/wenu_migration_0.5_to_0.6.md")

    for phrase in (
        "20 required style/mode products",
        "README image provenance",
        "package dependency directions",
        "916 tests passing without a warning summary",
        "Sgr-Sco-Oph-Ser",
    ):
        assert phrase in roadmap

    assert (ROOT / "tests/test_milestone22_package_boundaries.py").is_file()
    assert (ROOT / "tests/test_warning_policy.py").is_file()
    assert (ROOT / "tests/test_milestone44i_user_guide.py").is_file()
