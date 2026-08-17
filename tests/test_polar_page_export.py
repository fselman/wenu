"""Canonical one-save export contracts for paired physical polar pages."""

from types import SimpleNamespace

import pytest

from wenu import (
    ChartExportResult,
    PolarCalendarFurnitureRequest,
    PolarPageFurnitureRequest,
    PolarPagePairExportResult,
    PolarPlanispherePairRequest,
    ReferenceAnnotations,
    export_polar_planisphere_pages,
)
from wenu.charts.polar_planisphere import PolarPlanisphereChart


def resolved_values():
    pair = PolarPlanispherePairRequest(calendar_radius_mm=86.0).resolve()
    calendar = PolarCalendarFurnitureRequest().resolve(pair)
    pages = PolarPageFurnitureRequest(
        source_revision="7fd4649"
    ).resolve(pair)
    return pair, calendar, pages


def empty_sky():
    return SimpleNamespace(
        stars=None,
        nonstellar=None,
        galaxies=None,
        milky_way_isophotes=None,
        magellanic_clouds=None,
        globular_clusters=None,
        open_clusters=None,
        supernova_remnants=None,
        planetary_nebulae=None,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=None,
        coordinate_grids=(),
        points=None,
        layers=(),
    )


def test_paired_export_uses_canonical_face_export_once_per_a4_page(
    monkeypatch,
    tmp_path,
):
    import wenu.charts.polar_page_export as module

    pair, calendar, pages = resolved_values()
    monkeypatch.setattr(
        module,
        "_polar_reference_annotations",
        lambda chart, observer: ReferenceAnnotations(),
    )
    calls = []

    def fake_export(self, sky, renderer, path, **kwargs):
        calls.append((self, sky, renderer, path, kwargs))
        return ChartExportResult(
            rendering=object(),
            output=path,
            composition=kwargs["composition"],
            layer_options={},
            export_options=kwargs["export_options"],
        )

    monkeypatch.setattr(PolarPlanisphereChart, "export", fake_export)
    south = tmp_path / "south.pdf"
    north = tmp_path / "north.pdf"
    sky = object()
    observer = object()

    result = export_polar_planisphere_pages(
        pair,
        calendar,
        pages,
        sky,
        observer,
        south_path=south,
        north_path=north,
    )

    assert isinstance(result, PolarPagePairExportResult)
    assert tuple(item.output for item in result.faces) == (south, north)
    assert len(calls) == 2
    assert tuple(call[0].pole for call in calls) == ("south", "north")
    assert tuple(call[3] for call in calls) == (south, north)
    for _, called_sky, _, _, options in calls:
        assert called_sky is sky
        assert options["observer"] is observer
        assert callable(options["additional_furniture"])
        composition = options["composition"]
        assert composition.mode.width_inches == pytest.approx(210.0 / 25.4)
        assert composition.mode.height_inches == pytest.approx(297.0 / 25.4)
        export = options["export_options"]
        assert export.bbox_inches is None
        assert export.transparent is False
        assert export.padding == pytest.approx(0.0)
        assert export.metadata["Subject"] == "Source revision 7fd4649"


def test_canonical_export_runs_additional_furniture_before_single_save(
    monkeypatch,
):
    from wenu.charts.export_workflow import export_composed_chart

    pair, _, _ = resolved_values()
    chart = pair.south
    from wenu import compose_chart

    composition = compose_chart(chart, style="atlas", mode="print")
    calls = []
    figure = SimpleNamespace(
        set_size_inches=lambda *args, **kwargs: calls.append("size")
    )
    renderer = SimpleNamespace(ax=SimpleNamespace(figure=figure))
    monkeypatch.setattr(
        PolarPlanisphereChart,
        "render",
        lambda *args, **kwargs: calls.append("render") or "sky-rendering",
    )

    class Options:
        def save(self, saved_figure, path):
            assert saved_figure is figure
            calls.append("save")
            return path

    def furniture(**kwargs):
        assert kwargs["rendering"] == "sky-rendering"
        calls.append("furniture")
        return "page-rendering"

    result = export_composed_chart(
        chart,
        empty_sky(),
        renderer,
        "page.pdf",
        observer=object(),
        composition=composition,
        export_options=Options(),
        additional_furniture=furniture,
    )

    assert calls == ["size", "render", "furniture", "save"]
    assert result.output == "page.pdf"
    assert result.additional_furniture_rendering == "page-rendering"


def test_paired_export_validates_resolved_inputs():
    pair, calendar, pages = resolved_values()
    arguments = dict(
        sky=object(),
        observer=object(),
        south_path="south.pdf",
        north_path="north.pdf",
    )

    with pytest.raises(TypeError, match="pair"):
        export_polar_planisphere_pages(
            object(), calendar, pages, **arguments
        )
    with pytest.raises(TypeError, match="calendar"):
        export_polar_planisphere_pages(
            pair, object(), pages, **arguments
        )
    with pytest.raises(TypeError, match="pages"):
        export_polar_planisphere_pages(
            pair, calendar, object(), **arguments
        )
    with pytest.raises(ValueError, match="dpi"):
        export_polar_planisphere_pages(
            pair, calendar, pages, dpi=0, **arguments
        )


def test_actual_size_review_tool_uses_paired_export_and_no_direct_save():
    from pathlib import Path

    source = (
        Path(__file__).parents[1] / "tools/render_48e4_polar_pages.py"
    ).read_text(encoding="utf-8")

    assert "export_polar_planisphere_pages(" in source
    assert "figure.savefig" not in source
    assert "plt.savefig" not in source
    assert 'value.add_argument("--source-revision", required=True)' in source
    assert '"polar-planisphere-south-a4.pdf"' in source
    assert '"polar-planisphere-north-a4.pdf"' in source
    assert 'manifest = destination / "manifest.json"' in source
    assert "calendar_radius_mm=86.0" in source
    assert '"stellar_aperture_diameter_mm"' in source
