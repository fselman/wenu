"""Actual-size single-save export contracts for the folded polar pouch."""

from pathlib import Path

import pytest

from wenu import (
    PolarPouchFaceExportResult,
    PolarPouchPairExportResult,
    export_polar_pouch_pages,
)
from wenu.charts.regional import ExportOptions

from test_polar_pouch_rendering import pouches


def test_paired_export_saves_each_a4_face_once(monkeypatch, tmp_path):
    calls = []

    def fake_save(self, figure, path):
        calls.append((self, figure, path))
        return path

    monkeypatch.setattr(ExportOptions, "save", fake_save)
    south = tmp_path / "front.pdf"
    north = tmp_path / "back.pdf"
    result = export_polar_pouch_pages(
        pouches(),
        south_path=south,
        north_path=north,
        source_revision="9a930c0",
    )

    assert isinstance(result, PolarPouchPairExportResult)
    assert all(
        isinstance(item, PolarPouchFaceExportResult) for item in result.faces
    )
    assert tuple(item.output for item in result.faces) == (south, north)
    assert tuple(item.face for item in result.faces) == ("south", "north")
    assert len(calls) == 2
    for options, figure, _ in calls:
        assert figure.get_size_inches()[0] == pytest.approx(210.0 / 25.4)
        assert figure.get_size_inches()[1] == pytest.approx(297.0 / 25.4)
        assert options.bbox_inches is None
        assert options.transparent is False
        assert options.facecolor == "white"
        assert options.metadata["Subject"] == "Source revision 9a930c0"


def test_export_validates_resolved_inputs_and_provenance():
    arguments = {
        "south_path": "front.pdf",
        "north_path": "back.pdf",
        "source_revision": "9a930c0",
    }
    with pytest.raises(TypeError, match="pouches"):
        export_polar_pouch_pages(object(), **arguments)
    with pytest.raises(ValueError, match="source_revision"):
        export_polar_pouch_pages(
            pouches(),
            south_path="front.pdf",
            north_path="back.pdf",
            source_revision="",
        )
    with pytest.raises(ValueError, match="dpi"):
        export_polar_pouch_pages(pouches(), dpi=0, **arguments)


def test_review_tool_uses_export_boundary_and_has_no_direct_save():
    source = (
        Path(__file__).parents[1] / "tools/render_48g2_polar_pouch.py"
    ).read_text(encoding="utf-8")

    assert "export_polar_pouch_sheet(" in source
    assert "export_polar_planisphere_pages(" in source
    assert "compose_polar_pouch_sheet_preview(" in source
    assert '"fabrication_pdfs_are_clean": True' in source
    assert "figure.savefig" not in source
    assert "plt.savefig" not in source
    assert 'value.add_argument("--source-revision", required=True)' in source
    assert '"--title"' in source
    assert 'default="Muchos cielos, un firmamento"' in source
    assert '"polar-pouch-single-sheet-a4.pdf"' in source
    assert '"polar-pouch-single-sheet-a4.png"' in source
    assert 'manifest = destination / "manifest.json"' in source


def test_rendering_and_export_types_are_public():
    import wenu

    for name in (
        "PolarPouchFaceRendering",
        "draw_polar_pouch_face",
        "PolarPouchFaceExportResult",
        "PolarPouchPairExportResult",
        "export_polar_pouch_pages",
    ):
        assert name in wenu.__all__
