"""Coverage contract for the shared repository-source inventory."""

from pathlib import Path

from repository_sources import ROOT, SOURCE_ROOT_NAMES, repository_sources


def test_repository_source_inventory_includes_every_applicable_python_file():
    expected = {
        path
        for name in SOURCE_ROOT_NAMES
        if (root := ROOT / name).is_dir()
        for path in root.rglob("*.py")
    }
    indexed = {source.path for source in repository_sources()}

    assert indexed == expected
    assert all(isinstance(path, Path) for path in indexed)


def test_maintenance_inventory_covers_tools_and_explicit_resource_owners():
    import json
    inventory = json.loads((ROOT / "docs/developer/kernel_migration_inventory_v1.json").read_text())
    rows = inventory["maintenance_resource_routing"]["consumers"]
    owners = {"src/curated_catalogue_packaging.py", "src/wenu/resources.py",
              "src/wenu/minor_body_acquisition.py", "src/wenu/minor_body_resources.py",
              "src/wenu/comet_discovery.py", "src/wenu/satchecker.py",
              "src/wenu/satellites/snapshot_acquisition.py"}
    expected = {str(p.relative_to(ROOT)) for p in (ROOT / "tools").rglob("*.py")} | owners
    assert set(rows) == expected
    assert all(row["classification"] in {
        "source-maintenance", "explicit-acquisition", "application-consumer",
        "independent-validation", "fixture-preparation", "manual-benchmark",
        "build-resource", "test-tooling", "external-development-helper",
    } and row["boundary"] for row in rows.values())
