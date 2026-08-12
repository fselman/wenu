"""Ordinary drawing facade over observer-bound chart views."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from wenu import (
    CANONICAL_MAXIMAL_SPHERE_PROFILE,
    CelestialSphere,
    ChartContextOptions,
    ChartFurnitureOptions,
    DetailOverrides,
    FixedDetailPolicy,
    ResolvedDetail,
    draw_chart_view,
    get_chart_view,
)


def observer():
    return SimpleNamespace(
        utc_datetime=datetime(
            2026, 8, 16, 1, 0, tzinfo=timezone.utc
        ),
        lat_deg=-32.4524,
        lon_deg=-71.2317,
        elevation_m=48.0,
        timezone_name="America/Santiago",
    )


def view():
    sky = CelestialSphere(None)
    sky.load_profile = CANONICAL_MAXIMAL_SPHERE_PROFILE
    return get_chart_view(sky, observer(), family="planisphere")


def all_sky_view():
    sky = CelestialSphere(None)
    sky.load_profile = CANONICAL_MAXIMAL_SPHERE_PROFILE
    return get_chart_view(sky, observer(), family="all_sky")


def export_result(path):
    return SimpleNamespace(output=path)


def test_drawing_translates_direct_options_to_one_canonical_export(
    monkeypatch, tmp_path
):
    chart_view = view()
    configured = []
    configured_horizons = []
    exported = []
    furniture = ChartFurnitureOptions(
        context=ChartContextOptions(location=True)
    )
    policy = FixedDetailPolicy(
        ResolvedDetail(star_magnitude_limit=7.0)
    )
    output = tmp_path / "chart.png"
    result = export_result(output)

    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_grids",
        lambda sky, request, *, frame: configured.append(
            (sky, request, frame)
        ),
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_horizon",
        lambda sky, request: configured_horizons.append((sky, request)),
    )

    def export(sky, prepared, *, observer):
        exported.append((sky, prepared, observer))
        return SimpleNamespace(exports=(result,))

    monkeypatch.setattr(
        "wenu.charts.drawing.export_prepared_chart", export
    )
    actual = draw_chart_view(
        chart_view,
        output,
        style="cartoon",
        mode="presentation",
        detail=policy,
        detail_overrides=DetailOverrides(star_magnitude_limit=6.5),
        grids=("equatorial", "altaz_grid"),
        grid_labels=("equatorial_grid",),
        horizon=True,
        horizon_mask=True,
        furniture=furniture,
        title="Southern sky",
        language="es",
    )

    assert actual is result
    request = configured[0][1]
    assert request.product.output == output
    assert configured[0][2] is chart_view.frame
    assert request.product.style == "cartoon"
    assert request.product.mode == "presentation"
    assert request.detail.enabled_layer_additions == {
        "equatorial_grid", "altaz_grid"
    }
    assert request.detail.grid_label_layers == {"equatorial_grid"}
    assert request.horizon is True
    assert request.horizon_mask is True
    assert configured_horizons == [(chart_view.sky, request)]
    assert request.furniture is furniture
    assert request.title == "Southern sky"
    assert request.language == "es"
    assert request.product_compositions[0].detail is policy
    assert exported[0][0] is chart_view.sky
    assert exported[0][1].chart is chart_view.chart
    assert exported[0][2] is chart_view.observer


def test_repeated_drawings_reuse_geometry_without_request_state_leak(
    monkeypatch, tmp_path
):
    chart_view = view()
    original_request = chart_view._prepared.resolved.request
    requests = []
    prepared = []
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_grids",
        lambda sky, request, *, frame: requests.append(request),
    )

    def export(sky, value, *, observer):
        prepared.append(value)
        return SimpleNamespace(exports=(export_result(
            value.resolved.request.product.output
        ),))

    monkeypatch.setattr(
        "wenu.charts.drawing.export_prepared_chart", export
    )
    first = draw_chart_view(
        chart_view, tmp_path / "atlas.png", grids=("equatorial",)
    )
    second = draw_chart_view(
        chart_view,
        tmp_path / "cartoon.png",
        style="cartoon",
        grids=("galactic",),
    )

    assert first.output != second.output
    assert prepared[0].chart is prepared[1].chart is chart_view.chart
    assert requests[0].detail.enabled_layer_additions == {
        "equatorial_grid"
    }
    assert requests[1].detail.enabled_layer_additions == {
        "galactic_grid"
    }
    assert chart_view._prepared.resolved.request is original_request
    assert original_request.detail.enabled_layer_additions is None


def test_all_sky_drawing_defaults_to_labeled_galactic_grid(
    monkeypatch, tmp_path
):
    requests = []
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_grids",
        lambda sky, request, *, frame: requests.append(request),
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.export_prepared_chart",
        lambda *args, **kwargs: SimpleNamespace(
            exports=(export_result(tmp_path / "map.png"),)
        ),
    )

    draw_chart_view(all_sky_view(), tmp_path / "map.png")

    assert requests[0].detail.enabled_layer_additions == {"galactic_grid"}
    assert requests[0].detail.grid_label_layers == {"galactic_grid"}


def test_drawing_rejects_detail_beyond_sphere_profile(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_grids",
        lambda sky, request, *, frame: pytest.fail(
            "configuration must be late"
        ),
    )

    with pytest.raises(ValueError, match="star_magnitude_limit"):
        draw_chart_view(
            view(),
            tmp_path / "chart.png",
            detail_overrides=DetailOverrides(star_magnitude_limit=12.0),
        )


def test_drawing_rejects_unknown_grid_and_non_view(tmp_path):
    with pytest.raises(ValueError, match="altaz"):
        draw_chart_view(
            view(), tmp_path / "chart.png", grids=("unknown",)
        )
    with pytest.raises(TypeError, match="ChartView"):
        draw_chart_view(object(), tmp_path / "chart.png")


@pytest.mark.integration
def test_drawing_exports_one_real_product_through_canonical_pipeline(
    tmp_path,
):
    output = tmp_path / "planisphere.png"

    result = draw_chart_view(
        view(), output, style="atlas", mode="print", title="Planisphere"
    )

    assert result.output == output
    assert output.is_file()
    assert output.stat().st_size > 0
