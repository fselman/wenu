"""Contracts for the Milestone 49F.6 SVG acceptance matrix."""

import importlib.util
from pathlib import Path
import sys


PATH = Path("tools/render_49f6_svg_matrix.py")
EXPECTED = {
    "all-sky",
    "planisphere",
    "regional",
    "circumpolar",
    "binocular",
    "polar-pages",
    "polar-pouch",
}


def _module():
    spec = importlib.util.spec_from_file_location("svg_matrix", PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_matrix_covers_every_public_family_and_physical_polar_product():
    matrix = _module().MATRIX
    names = [entry.name for entry in matrix]

    assert set(names) == EXPECTED
    assert len(names) == len(set(names))
    assert {entry.kind for entry in matrix} == {
        "cli", "polar-pages", "polar-pouch"
    }


def test_cli_entries_request_svg_through_the_installed_command():
    module = _module()
    cli = [entry for entry in module.MATRIX if entry.kind == "cli"]

    assert {entry.arguments[0] for entry in cli} == {
        "all-sky", "planisphere", "regional", "circumpolar", "binocular"
    }
    for entry in cli:
        assert "--output" not in entry.arguments
        assert "--format" not in entry.arguments


def test_matrix_exercises_cross_product_svg_risk_surface():
    arguments = " ".join(
        argument
        for entry in _module().MATRIX
        for argument in entry.arguments
    )

    for option in (
        "--mask",
        "--horizon",
        "--horizon-mask",
        "--constellation-lines",
        "--constellation-labels",
        "--constellation-boundaries",
        "--equatorial-grid",
        "--equatorial-grid-labels",
        "--ecliptic-grid",
        "--ecliptic-grid-labels",
        "--galactic-grid",
        "--galactic-grid-labels",
        "--grid-references",
        "--poles",
        "--legends",
        "--star-counts",
        "--credits",
    ):
        assert option in arguments


def test_physical_products_reuse_canonical_export_owners():
    source = PATH.read_text(encoding="utf-8")

    assert "export_polar_planisphere_pages(" in source
    assert "export_polar_pouch_sheet(" in source
    assert "figure.savefig" not in source
    assert "plt.savefig" not in source


def test_inspection_records_required_structural_facts(tmp_path):
    path = tmp_path / "minimal.svg"
    path.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg"
 width="10pt" height="20pt" viewBox="0 0 10 20">
 <metadata />
 <g id="group" class="wenu-semantic-group"
    data-wenu-semantic-path="sky/stars">
  <text id="star" class="wenu-semantic-artist"
        data-wenu-semantic-path="sky/stars/symbols"
        data-wenu-edit="style">S</text>
 </g>
</svg>
""",
        encoding="utf-8",
    )

    record = _module().inspect_svg(path)

    assert record["width"] == "10pt"
    assert record["height"] == "20pt"
    assert record["view_box"] == "0 0 10 20"
    assert record["text_elements"] == 1
    assert record["image_elements"] == 0
    assert record["metadata_elements"] == 1
    assert record["semantic_artists"] == 1
    assert record["semantic_groups"] == 1
    assert record["edit_policies"] == {"style": 1}
    assert record["missing_semantic_paths"] == 0
    assert record["duplicate_ids"] == []
