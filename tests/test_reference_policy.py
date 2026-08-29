"""Public celestial reference-policy contracts."""

from pathlib import Path

import pytest
from astropy.time import Time

from wenu import (
    CelestialReferencePolicy,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    DetailOverrides,
    configure_chart_request_grids,
)
from wenu.sky.celestial_sphere import CelestialSphere


class Observer:
    t_astropy = Time("2026-08-29T12:00:00")


def _request(policy):
    return ChartRequest(
        observer=ChartObserverRequest(
            location="La Ligua", time="2026-08-29 08:00"
        ),
        family="planisphere",
        product=ChartProductOptions(output=Path("chart.png")),
        detail=DetailOverrides(
            enabled_layer_additions={"equatorial_grid", "ecliptic_grid"}
        ),
        reference_policy=policy,
    )


def test_explicit_reference_equinox_reaches_coupled_grids():
    observer = Observer()
    sky = CelestialSphere(observer)
    grids = configure_chart_request_grids(
        sky, _request(CelestialReferencePolicy("J2050"))
    )

    assert [grid.coordinate_system for grid in grids] == [
        "equatorial", "ecliptic"
    ]
    assert all(
        Time(grid.equinox).jyear == pytest.approx(2050.0)
        for grid in grids
    )


def test_of_date_resolves_from_declared_observer_time():
    policy = CelestialReferencePolicy("of_date")
    assert (
        policy.resolved_equinox(Observer()).isot
        == "2026-08-29T12:00:00.000"
    )


def test_invalid_or_empty_reference_equinox_is_rejected():
    with pytest.raises(ValueError, match="cannot be empty"):
        CelestialReferencePolicy(" ")
    with pytest.raises(ValueError, match="Invalid reference equinox"):
        CelestialReferencePolicy("not-an-equinox")
