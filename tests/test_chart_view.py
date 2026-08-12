"""Ordinary observer-bound geometrical chart-view facade."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from wenu import (
    CANONICAL_MAXIMAL_SPHERE_PROFILE,
    CelestialSphere,
    ChartView,
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
    assert view.family == "binocular"
    assert view.mask is False
    assert view.target.key == "m57"
    assert view.frame.field_diameter_deg == pytest.approx(5.0)
    assert view.frame.position_angle_deg == pytest.approx(12.0)
    assert calls == [(source, observing)]
    assert not hasattr(view, "style")
    assert not hasattr(view, "output")


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


def test_view_rejects_unsupported_projection_before_preparation():
    with pytest.raises(ValueError, match="stereographic"):
        get_chart_view(
            sky(), observer(), family="planisphere", projection="gnomonic"
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
