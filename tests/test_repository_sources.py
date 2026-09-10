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
