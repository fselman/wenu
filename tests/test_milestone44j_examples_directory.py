"""Milestone 44J canonical example-directory contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
CANONICAL_EXAMPLES = {
    "binocular_object.py",
    "circumpolar.py",
    "planisphere.py",
    "regional_constellation.py",
    "regional_constellation_group.py",
}


def test_examples_directory_contains_only_canonical_families():
    assert {
        path.name
        for path in EXAMPLES.iterdir()
        if path.is_file()
    } == CANONICAL_EXAMPLES


def test_regression_fixtures_are_test_local():
    fixtures = ROOT / "tests" / "fixtures" / "example_regressions"
    assert fixtures.is_dir()
    assert all(
        path.suffix == ".py"
        for path in fixtures.iterdir()
        if path.is_file()
    )


def test_tests_do_not_reference_deleted_user_examples():
    deleted = {
        path.name
        for path in (
            ROOT / "tests" / "fixtures" / "example_regressions"
        ).iterdir()
    }
    for test in (ROOT / "tests").glob("test_*.py"):
        source = test.read_text(encoding="utf-8")
        for name in deleted:
            assert f"examples/{name}" not in source
