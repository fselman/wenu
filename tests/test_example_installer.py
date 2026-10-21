"""Contracts for installing the packaged canonical examples."""

from pathlib import Path

import json
from types import SimpleNamespace
import pytest
import wenu

from wenu.cli.examples import copy_examples
from wenu.cli.notebooks import copy_notebooks


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

NOTEBOOKS = tuple(sorted((ROOT / "src/wenu/notebooks").rglob("*.ipynb")))


def test_notebook_installer_preserves_paths_bytes_and_user_edits(tmp_path):
    assert len(NOTEBOOKS) == 5
    destination = tmp_path / "notebooks"
    copied = copy_notebooks(destination)
    expected = {p.relative_to(ROOT / "src/wenu/notebooks"): p.read_bytes()
                for p in NOTEBOOKS}
    assert {p.relative_to(destination): p.read_bytes() for p in copied} == expected
    edited = copied[0]
    edited.write_text("user notebook", encoding="utf-8")
    assert copy_notebooks(destination) == []
    assert edited.read_text() == "user notebook"
    assert len(copy_notebooks(destination, force=True)) == 5
    assert {p.relative_to(destination): p.read_bytes() for p in copied} == expected


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: str(p.relative_to(ROOT / "src/wenu/notebooks")))
@pytest.mark.parametrize("failure", (None, "sphere", "view", "drawing"))
def test_notebook_cells_consume_public_results_and_release_observer(path, failure, monkeypatch):
    """Execute every cell; synthetic services isolate the notebook's ownership."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4 and notebook["nbformat_minor"] == 5
    identifiers = [cell["id"] for cell in notebook["cells"]]
    assert len(set(identifiers)) == len(identifiers)
    assert all(value and len(value) <= 64 and value.replace("-", "").isalnum() for value in identifiers)
    events = []
    observer = SimpleNamespace(close=lambda: events.append("closed"))
    sky = object()
    view = object()
    output = object()
    def make_observer(**options):
        assert options == {"location": "La Ligua", "time": "2026-08-15 21:00"}
        events.append("observer")
        return observer
    def sphere():
        events.append("sphere")
        if failure == "sphere": raise RuntimeError("public refusal")
        return sky
    def get_view(supplied, active, **options):
        assert supplied is sky and active is observer
        assert options["family"] == "planisphere"
        assert options["projection"] == "stereographic"
        assert options["mirror_ew"] is True
        events.append("view")
        if failure == "view": raise RuntimeError("public refusal")
        return view
    def draw(supplied, arguments, **options):
        assert supplied is view
        assert arguments.magnitude_limit == (6.0 if path.name.startswith("02") else 5.5)
        assert arguments.grid_references == frozenset({"equatorial", "ecliptic", "galactic"})
        assert arguments.reference_equinox == (None if path.name.startswith("02") else "of_date")
        assert options["language"] == ("es" if path.parent.name == "es" else "en")
        events.append("drawing")
        if failure == "drawing": raise RuntimeError("public refusal")
        return (SimpleNamespace(output=output),)
    for name, value in (("Observer", make_observer), ("generate_celestial_sphere", sphere),
                        ("get_chart_view", get_view), ("draw_chart_view_from_arguments", draw)):
        monkeypatch.setattr(wenu, name, value)
    namespace = {}
    def execute():
        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] == "code":
                assert cell["outputs"] == [] and cell["execution_count"] is None
                exec(compile("".join(cell["source"]), f"{path}:cell{index}", "exec"), namespace)
    if failure:
        with pytest.raises(RuntimeError, match="public refusal"):
            execute()
    else:
        execute()
        assert tuple(result.output for result in namespace["results"]) == (output,)
    assert events[-1] == "closed" and events.count("closed") == 1


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


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: str(p.relative_to(ROOT / "src/wenu/notebooks")))
def test_notebook_public_cells_export_canonical_png(path, tmp_path, monkeypatch):
    """Constructed catalogue/observer, real kernel/composition/renderer/export."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from test_fixed_sky_sequence import _fixed_kernel_environment
    from wenu.charts import request_generation
    from wenu.sky.maximal_sphere import CANONICAL_MAXIMAL_SPHERE_PROFILE
    observers, skies, realized = _fixed_kernel_environment(monkeypatch)
    def observer(**options):
        instant = datetime.fromisoformat(options["time"]).replace(tzinfo=ZoneInfo("America/Santiago"))
        value = request_generation.Observer(time=instant)
        value.location_name = options["location"]
        return value
    monkeypatch.setattr(wenu, "Observer", observer)
    def sphere():
        sky = request_generation.build_maximal_sphere(None, profile=CANONICAL_MAXIMAL_SPHERE_PROFILE)
        # Neither constructed star is a constellation-line endpoint.
        sky.stars.source_catalog["is_constellation_vertex"] = False
        sky.stars.catalog["is_constellation_vertex"] = False
        return sky
    monkeypatch.setattr(wenu, "generate_celestial_sphere", sphere)
    monkeypatch.chdir(tmp_path)
    namespace = {}
    for cell in json.loads(path.read_text(encoding="utf-8"))["cells"]:
        if cell["cell_type"] == "code":
            exec(compile("".join(cell["source"]), str(path), "exec"), namespace)
    outputs = tuple(result.output for result in namespace["results"])
    assert outputs == (namespace["OUTPUT_FILE"],)
    assert outputs[0].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert realized and all(value.closed for value in observers)
