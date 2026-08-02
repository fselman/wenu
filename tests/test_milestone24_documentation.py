"""Milestone 24 active-documentation contract tests."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
ACTIVE = (
    ROOT / "README.md",
    ROOT / "docs/developer/current_architecture_v0.5.md",
    ROOT / "docs/developer/implementation_reference.md",
    ROOT / "docs/developer/source_tree.md",
    ROOT / "docs/developer/target_architecture_v0.6.md",
    ROOT / "docs/developer/wenu_migration_0.5_to_0.6.md",
    ROOT / "docs/developer/deprecations_v0.5.md",
)

OBSOLETE = (
    "wenu.spherical",
    "wenu.projected",
    "wenu.spherical_frame",
    "wenu.clipping",
    "wenu.viewport",
    "wenu.projection",
    "wenu.chart",
    "wenu.regional",
    "wenu.styles",
    "wenu.renderers",
)


def test_active_documents_exist():
    assert [path for path in ACTIVE if not path.is_file()] == []


def test_active_documents_do_not_recommend_obsolete_imports():
    violations = []
    for path in ACTIVE:
        text = path.read_text()
        for obsolete in OBSOLETE:
            pattern = re.compile(
                rf"\b(?:from|import)\s+{re.escape(obsolete)}"
                rf"(?=\s|$)"
            )
            if pattern.search(text):
                violations.append(f"{path.relative_to(ROOT)}: {obsolete}")
    assert violations == []


def test_public_api_documents_name_both_chart_apis():
    for path in (
        ROOT / "README.md",
        ROOT / "docs/developer/implementation_reference.md",
    ):
        text = path.read_text()
        assert "RegionalChart" in text
        assert "FullSkyChart" in text


def test_v05_migration_documents_are_closed():
    target = (
        ROOT / "docs/developer/target_architecture_v0.5.md"
    ).read_text()
    roadmap = (
        ROOT / "docs/developer/wenu_migration_0.4_to_0.5.md"
    ).read_text()
    assert "Status: implemented" in target
    assert "Status: complete" in roadmap
    assert "current_architecture_v0.4.md" in target
    assert "target_architecture_v0.5.md" in roadmap


def test_historical_documents_are_archived():
    archive = ROOT / "docs/developer/archive"
    assert (archive / "target_architecture_v0.3.md").is_file()
    assert (archive / "wenu_migration_roadmap_v0.3.md").is_file()
    assert not (
        ROOT / "docs/developer/target_architecture_v0.3.md"
    ).exists()
    assert not (
        ROOT / "docs/developer/wenu_migration_roadmap_v0.3.md"
    ).exists()
