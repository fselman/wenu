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
from wenu.configuration import packaged_furniture_product_export_defaults


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
        lambda sky, request, *, frame, observer: configured.append(
            (sky, request, frame, observer)
        ),
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_horizon",
        lambda sky, request, *, state=None: configured_horizons.append((sky, request)),
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
    assert configured[0][3] is chart_view.observer
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


def test_ordinary_drawing_uses_packaged_neutral_furniture_by_default(
    monkeypatch, tmp_path
):
    chart_view = view()
    requests = []
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_grids",
        lambda sky, request, *, frame, observer: requests.append(request),
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_horizon",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.export_prepared_chart",
        lambda *args, **kwargs: SimpleNamespace(
            exports=(export_result(tmp_path / "chart.png"),)
        ),
    )

    draw_chart_view(chart_view, tmp_path / "chart.png")

    expected = packaged_furniture_product_export_defaults()
    configured = expected.furniture_by_family["planisphere"]
    assert requests[0].furniture.references is configured.references
    assert requests[0].furniture.poles is configured.poles
    assert requests[0].furniture.footer is configured.footer
    assert requests[0].furniture.legends is None
    assert requests[0].furniture.context is None


def test_repeated_drawings_reuse_geometry_without_request_state_leak(
    monkeypatch, tmp_path
):
    chart_view = view()
    original_request = chart_view._prepared.resolved.request
    requests = []
    prepared = []
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_grids",
        lambda sky, request, *, frame, observer: requests.append(request),
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


@pytest.mark.parametrize(
    ("horizon", "horizon_mask"),
    ((False, False), (True, False), (False, True), (True, True)),
)
def test_python_facade_preserves_independent_horizon_controls(
    monkeypatch, tmp_path, horizon, horizon_mask
):
    chart_view = view()
    requests = []
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_grids",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_horizon",
        lambda sky, request, *, state=None: requests.append(request),
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.export_prepared_chart",
        lambda *args, **kwargs: SimpleNamespace(
            exports=(export_result(tmp_path / "chart.png"),)
        ),
    )

    draw_chart_view(
        chart_view,
        tmp_path / "chart.png",
        horizon=horizon,
        horizon_mask=horizon_mask,
    )

    assert requests[0].horizon is horizon
    assert requests[0].horizon_mask is horizon_mask


def test_all_sky_drawing_defaults_to_labeled_galactic_grid(
    monkeypatch, tmp_path
):
    requests = []
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_grids",
        lambda sky, request, *, frame, observer: requests.append(request),
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



def _drawing_scope_fixture(monkeypatch, tmp_path, failure_stage=None):
    """Constructed resource/configuration seams; no provider or geometry work."""
    from wenu.charts.drawing import chart_view_request
    from wenu.sky.sky_layer import SkyLayer
    from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG

    class Layer(SkyLayer):
        layer_name = "scope-fixture"

        def spherical_geometry(self, observer):
            raise AssertionError("scope tests must not evaluate scientific geometry")

    chart_view = view()
    sky = chart_view.sky
    old_resolver = object()
    retained = Layer()
    retained.source_resolver = old_resolver
    sky.add(retained)
    sky.solar_system_bodies["retained"] = retained
    original_alias = object()
    sky.horizon_reference = original_alias
    descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve("ceres")
    # Explicit None must be distinguished from an absent entity alias.
    setattr(sky, descriptor.entity_key, None)
    request = chart_view_request(chart_view, tmp_path / "scope.png")
    request = SimpleNamespace(**vars(request))
    request.minor_body_descriptors = (descriptor,)
    sessions, observer_closes, exports, order = [], [], [], []
    chart_view.observer.close = lambda: observer_closes.append(True)
    error = RuntimeError("synthetic drawing scope failure: " + str(failure_stage))
    cleanup_error = RuntimeError("synthetic drawing cleanup failure")

    class Session:
        def __init__(self, directory, observer):
            assert observer is chart_view.observer
            if failure_stage == "session":
                raise error
            self.closes = 0
            self.fail_close = failure_stage == "export-close"
            sessions.append(self)

        def source_binding(self, *args):
            raise AssertionError("scope tests must not resolve source state")

        def close(self):
            self.closes += 1
            if self.fail_close:
                raise cleanup_error

    def add(descriptor):
        point = Layer()
        point.descriptor = descriptor
        point.source_resolver = old_resolver
        sky.solar_system_bodies[descriptor.selection_key] = point
        setattr(sky, descriptor.entity_key, point)
        sky.add(point)
        if failure_stage == "add":
            raise error
        return point

    monkeypatch.setattr(sky, "add_solar_system_body", add)
    monkeypatch.setattr("wenu.minor_body_resources.request_minor_body_descriptors", lambda value: (descriptor,))
    monkeypatch.setattr("wenu.minor_body_resources.MinorBodyResourceSession", Session)
    monkeypatch.setattr("wenu.charts.drawing.ChartRequest", SimpleNamespace)
    before = tuple(sky.layers)

    def configure(stage):
        def operation(actual_sky, actual_request, **options):
            assert actual_sky is sky and actual_request is request
            order.append(stage)
            state = options.get("state")
            if state is not None:
                state.remember_attribute(sky, "horizon_reference")
            # Grids only mutate the registry; the following helper journals its alias.
            if stage != "grids":
                assert state is not None and sky._active_chart_request_state is not None
                sky.horizon_reference = object()
            sky.add(Layer())
            if stage == failure_stage:
                raise error
        return operation

    for stage in ("grids", "horizon", "track", "disks"):
        monkeypatch.setattr("wenu.charts.drawing.configure_chart_request_" + stage, configure(stage))

    def export(actual_sky, prepared, *, observer):
        assert actual_sky is sky and observer is chart_view.observer
        assert sky._active_chart_request_state is not None
        assert prepared.chart is chart_view.chart
        assert retained.source_resolver.__self__ is sessions[-1]
        exports.append(prepared)
        if failure_stage in {"export", "export-close"}:
            raise error
        return SimpleNamespace(exports=(SimpleNamespace(output=tmp_path / "scope.png"),))

    monkeypatch.setattr("wenu.charts.drawing.export_prepared_chart", export)
    return SimpleNamespace(view=chart_view, sky=sky, request=request, error=error, cleanup_error=cleanup_error,
                           before=before, alias=original_alias, descriptor=descriptor,
                           sessions=sessions, retained=retained, old_resolver=old_resolver,
                           observer_closes=observer_closes, exports=exports, order=order)


def _assert_drawing_scope_restored(fixture, *, closes=1):
    assert tuple(fixture.sky.layers) == fixture.before
    assert fixture.sky.horizon_reference is fixture.alias
    assert getattr(fixture.sky, fixture.descriptor.entity_key) is None
    assert fixture.descriptor.selection_key not in fixture.sky.solar_system_bodies
    assert fixture.retained.source_resolver is fixture.old_resolver
    assert not hasattr(fixture.sky, "_active_chart_request_state")
    assert fixture.observer_closes == []
    assert all(session.closes == closes for session in fixture.sessions)


@pytest.mark.parametrize("failure_stage", ["add", "session", "grids", "horizon", "track", "disks", "export"])
def test_drawing_scope_restores_partial_setup_and_export_failures(monkeypatch, tmp_path, failure_stage):
    from wenu.charts.drawing import draw_chart_view_request

    fixture = _drawing_scope_fixture(monkeypatch, tmp_path, failure_stage)
    with pytest.raises(RuntimeError) as caught:
        draw_chart_view_request(fixture.view, fixture.request)
    assert caught.value is fixture.error
    _assert_drawing_scope_restored(fixture)


def test_drawing_scope_restores_after_success_and_reuses_the_original_view(monkeypatch, tmp_path):
    from wenu.charts.drawing import draw_chart_view_request

    fixture = _drawing_scope_fixture(monkeypatch, tmp_path)
    for _ in range(2):
        result = draw_chart_view_request(fixture.view, fixture.request)
        assert result.output == tmp_path / "scope.png"
        _assert_drawing_scope_restored(fixture)
    assert fixture.order == ["grids", "horizon", "track", "disks"] * 2
    assert len(fixture.exports) == 2


def test_drawing_scope_rejects_an_active_build_before_any_configuration(monkeypatch, tmp_path):
    from wenu.charts.drawing import draw_chart_view_request
    from wenu.charts.request_generation import open_chart_request_scope

    fixture = _drawing_scope_fixture(monkeypatch, tmp_path)
    with open_chart_request_scope(fixture.sky):
        with pytest.raises(RuntimeError, match="already active"):
            draw_chart_view_request(fixture.view, fixture.request)
        assert fixture.order == []
        assert fixture.sessions == []
    _assert_drawing_scope_restored(fixture)



def test_drawing_cleanup_failure_preserves_original_error_and_lease_for_retry(monkeypatch, tmp_path):
    from wenu.charts import drawing

    fixture = _drawing_scope_fixture(monkeypatch, tmp_path, "export-close")
    scopes = []
    original_open = drawing.open_chart_request_scope

    def capture(*args, **kwargs):
        scope = original_open(*args, **kwargs)
        scopes.append(scope)
        return scope

    monkeypatch.setattr(drawing, "open_chart_request_scope", capture)
    with pytest.raises(RuntimeError) as caught:
        drawing.draw_chart_view_request(fixture.view, fixture.request)
    assert caught.value is fixture.cleanup_error
    assert caught.value.__context__ is fixture.error
    assert tuple(fixture.sky.layers) == fixture.before
    assert fixture.sky.horizon_reference is fixture.alias
    assert fixture.retained.source_resolver is fixture.old_resolver
    with pytest.raises(RuntimeError, match="already active"):
        original_open(fixture.sky)
    fixture.sessions[0].fail_close = False
    scopes[0].close()
    _assert_drawing_scope_restored(fixture, closes=2)
