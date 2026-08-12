"""Contracts for installing the packaged canonical examples."""

from pathlib import Path

from wenu.cli.examples import copy_examples


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_EXAMPLES = ROOT / "examples"
PACKAGED_EXAMPLES = ROOT / "src" / "wenu" / "example_scripts"
CANONICAL_EXAMPLE_NAMES = {
    "all_sky.py",
    "binocular_object.py",
    "circumpolar.py",
    "planisphere.py",
    "regional_constellation.py",
    "regional_constellation_group.py",
}


def example_names(directory):
    """Return the names of user example scripts in ``directory``."""
    return {
        path.name
        for path in directory.glob("*.py")
        if path.name != "__init__.py"
    }


def test_packaged_examples_match_canonical_examples():
    assert example_names(CANONICAL_EXAMPLES) == CANONICAL_EXAMPLE_NAMES
    assert example_names(PACKAGED_EXAMPLES) == CANONICAL_EXAMPLE_NAMES
    for name in example_names(CANONICAL_EXAMPLES):
        assert (PACKAGED_EXAMPLES / name).read_bytes() == (
            CANONICAL_EXAMPLES / name
        ).read_bytes()


def test_copy_examples_installs_every_script(tmp_path):
    destination = tmp_path / "wenu_examples"

    copied = copy_examples(destination)

    assert {path.name for path in copied} == example_names(CANONICAL_EXAMPLES)
    assert example_names(destination) == example_names(CANONICAL_EXAMPLES)


def test_copy_examples_preserves_existing_files_without_force(tmp_path):
    destination = tmp_path / "wenu_examples"
    destination.mkdir()
    existing = destination / "planisphere.py"
    existing.write_text("user copy\n", encoding="utf-8")

    copied = copy_examples(destination)

    assert existing.read_text(encoding="utf-8") == "user copy\n"
    assert existing not in copied


def test_copy_examples_force_replaces_existing_files(tmp_path):
    destination = tmp_path / "wenu_examples"
    destination.mkdir()
    existing = destination / "planisphere.py"
    existing.write_text("user copy\n", encoding="utf-8")

    copied = copy_examples(destination, force=True)

    assert existing in copied
    assert existing.read_bytes() == (
        CANONICAL_EXAMPLES / "planisphere.py"
    ).read_bytes()
