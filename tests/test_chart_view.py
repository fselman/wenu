"""Ordinary observer-bound geometrical chart-view facade."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from wenu import (
    CANONICAL_MAXIMAL_SPHERE_PROFILE,
    CHART_VIEW_DEFAULTS,
    CelestialSphere,
    ChartView,
    ChartViewDefaults,
    chart_view_defaults,
    get_chart_view,
)


def observer():
    return SimpleNamespace(
        utc_datetime=datetime(
            2026, 8, 16, 1, 0,
            tzinfo=timezone.utc,
        ),
        lat_deg=-32.4524,
        lon_deg=-71.2317,
        elevation_m=48.0,
        timezone_name="America/Santiago",
    )


def sky():
    return SimpleNamespace(
        load_profile=CANONICAL_MAXIMAL_SPHERE_PROFILE,
        observer=None,
    )


def prepared(resolved):
    return SimpleNamespace(chart=object(), resolved=resolved)


def test_view_resolves_friendly_target_and_frame_without_presentation(
    monkeypatch,
):
    source = sky()
    observing = observer()
    calls = []

    def prepare(actual_sky, resolved, *, observer):
        calls.append((actual_sky, observer))
        return prepared(resolved)

    monkeypatch.setattr("wenu.charts.view.prepare_chart_request", prepare)
    view = get_chart_view(
        source,
        observing,
        family="binocular",
        target="M57",
        field_diameter_deg=5.0,
        position_angle_deg=12.0,
    )

    assert isinstance(view, ChartView)
    assert view.sky is source
    assert view.observer is observing
    assert view.projection_name == "stereographic"
    assert view.coordinate_frame == "horizontal"
    assert view.projection_selection.name == "stereographic"
    assert view.projection_selection.coordinate_frame == "horizontal"
    assert view.family == "binocular"
    assert view.mask is False
    assert view.target.key == "m57"
    assert view.frame.field_diameter_deg == pytest.approx(5.0)
    assert view.frame.position_angle_deg == pytest.approx(12.0)
    assert calls == [(source, observing)]
    assert not hasattr(view, "style")
    assert not hasattr(view, "output")


def test_public_family_defaults_are_immutable_and_geometrical():
    binocular = chart_view_defaults("binocular")
    single = chart_view_defaults("regional")
    group = chart_view_defaults("regional", group=True)
    planisphere = chart_view_defaults("planisphere")
    circumpolar = chart_view_defaults("circumpolar")
    all_sky = chart_view_defaults("all_sky")

    assert isinstance(binocular, ChartViewDefaults)
    assert binocular.field_diameter_deg == pytest.approx(6.5)
    assert single.framing == "constellation-geometry"
    assert group.framing == "packaged-group"
    assert planisphere.framing == "visible-hemisphere"
    assert circumpolar.pole == "south"
    assert circumpolar.limiting_declination_deg == pytest.approx(-69.75)
    assert all_sky.framing == "complete-sphere"
    assert all_sky.projection == "mollweide"
    assert all_sky.coordinate_frame == "galactic"
    assert single.orientation == "celestial-north-up"
    assert group.orientation == "celestial-north-up"
    assert binocular.orientation == "celestial-north-up"
    assert single.position_angle_deg is None
    assert planisphere.position_angle_deg == pytest.approx(0.0)
    assert circumpolar.position_angle_deg == pytest.approx(0.0)
    with pytest.raises(TypeError):
        CHART_VIEW_DEFAULTS["binocular"] = planisphere


def test_circumpolar_view_uses_public_defaults_when_omitted(monkeypatch):
    monkeypatch.setattr(
        "wenu.charts.view.prepare_chart_request",
        lambda sky, resolved, *, observer: prepared(resolved),
    )

    view = get_chart_view(sky(), observer(), family="circumpolar")

    assert view.frame.pole == "south"
    assert view.frame.limiting_declination_deg == pytest.approx(-69.75)
    assert view.frame.position_angle_deg == pytest.approx(0.0)


def test_all_sky_view_uses_galactic_mollweide_defaults(monkeypatch):
    monkeypatch.setattr(
        "wenu.charts.view.prepare_chart_request",
        lambda sky, resolved, *, observer: prepared(resolved),
    )

    view = get_chart_view(sky(), observer(), family="all_sky")

    assert view.projection_name == "mollweide"
    assert view.coordinate_frame == "galactic"
    assert view.frame.position_angle_deg == pytest.approx(0.0)


def test_explicit_geometry_overrides_public_defaults(monkeypatch):
    monkeypatch.setattr(
        "wenu.charts.view.prepare_chart_request",
        lambda sky, resolved, *, observer: prepared(resolved),
    )

    view = get_chart_view(
        sky(),
        observer(),
        family="circumpolar",
        pole="north",
        limiting_declination_deg=72.0,
        position_angle_deg=15.0,
    )

    assert view.frame.pole == "north"
    assert view.frame.limiting_declination_deg == pytest.approx(72.0)
    assert view.frame.position_angle_deg == pytest.approx(15.0)


def test_view_preserves_serpens_resolution_and_automatic_framing(
    monkeypatch,
):
    monkeypatch.setattr(
        "wenu.charts.view.prepare_chart_request",
        lambda sky, resolved, *, observer: prepared(resolved),
    )

    view = get_chart_view(
        sky(),
        observer(),
        family="regional",
        constellations=("Ser",),
        mask=True,
    )

    assert view.constellations.line_constellations == ("Ser1", "Ser2")
    assert view.constellations.boundary_constellations == ("Ser",)
    assert view.frame.automatic_from_geometry


def test_arbitrary_multi_constellation_view_uses_group_defaults(
    monkeypatch,
):
    import wenu.charts.view as view_module

    calls = []
    actual_defaults = view_module.chart_view_defaults
    monkeypatch.setattr(
        view_module,
        "chart_view_defaults",
        lambda family, *, group, configuration: (
            calls.append((family, group, configuration))
            or actual_defaults(
                family,
                group=group,
                configuration=configuration,
            )
        ),
    )
    monkeypatch.setattr(
        view_module,
        "prepare_chart_request",
        lambda sky, resolved, *, observer: prepared(resolved),
    )

    get_chart_view(
        sky(),
        observer(),
        family="regional",
        constellations=("Cyg", "Lyr", "Aql"),
    )

    assert calls == [("regional", True, None)]


def test_view_rejects_unsupported_projection_before_preparation():
    with pytest.raises(ValueError, match="stereographic"):
        get_chart_view(
            sky(), observer(), family="planisphere", projection="gnomonic"
        )


def test_view_rejects_unimplemented_coordinate_frame_before_preparation():
    with pytest.raises(ValueError, match="horizontal"):
        get_chart_view(
            sky(), observer(), family="planisphere",
            coordinate_frame="galactic",
        )


def test_view_rejects_an_observer_without_scientific_identity():
    with pytest.raises(TypeError, match="scientific location and instant"):
        get_chart_view(sky(), object(), family="planisphere")


def test_view_is_frozen_and_does_not_own_the_observer(monkeypatch):
    observing = observer()
    monkeypatch.setattr(
        "wenu.charts.view.prepare_chart_request",
        lambda sky, resolved, *, observer: prepared(resolved),
    )
    view = get_chart_view(sky(), observing, family="planisphere")

    with pytest.raises(FrozenInstanceError):
        view.observer = object()
    assert view.observer is observing
    assert not hasattr(view, "close")


def test_real_preparation_uses_an_observer_independent_sphere():
    source = CelestialSphere(None)
    source.load_profile = CANONICAL_MAXIMAL_SPHERE_PROFILE
    observing = observer()

    view = get_chart_view(source, observing, family="planisphere")

    assert source.observer is None
    assert view.observer is observing
    assert view.chart.center_alt_deg == pytest.approx(90.0)
