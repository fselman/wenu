"""Ordinary chart-request layer-realization context contracts."""

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from astropy.time import Time

from wenu.charts.product_options import ChartProductOptions
from wenu.charts.reference_policy import CelestialReferencePolicy
from wenu.charts.request import ChartObserverRequest, ChartRequest
from wenu.charts.request_realization import chart_request_realization_context
from wenu.coordinates import PositionStatus


class Observer:
    lat_deg = -33.0
    lon_deg = -71.0
    elevation_m = 100.0
    t_astropy = Time("2026-08-30T00:00:00", scale="utc")


def request(frame, *, equinox="J2000"):
    projection = "mollweide" if frame == "galactic" else "stereographic"
    return ChartRequest(
        observer=ChartObserverRequest(
            lat_deg=-33.0,
            lon_deg=-71.0,
            elevation_m=100.0,
            time="2026-08-30T00:00:00Z",
        ),
        family="all_sky" if frame == "galactic" else "planisphere",
        projection=projection,
        coordinate_frame=frame,
        product=ChartProductOptions(output=Path("chart.svg")),
        reference_policy=CelestialReferencePolicy(equinox),
    )


@pytest.mark.parametrize(
    ("frame", "expected"),
    (("horizontal", "altaz"), ("galactic", "galactic")),
)
def test_request_context_maps_product_frame_without_conflating_equinox(
    monkeypatch, frame, expected
):
    monkeypatch.setattr(
        ChartObserverRequest, "matches", lambda self, observer: True
    )

    context = chart_request_realization_context(request(frame), Observer())
    spec = context.product_coordinate_spec

    assert spec.frame == expected
    assert spec.origin == "observer"
    assert spec.position_status is PositionStatus.APPARENT
    assert spec.epoch is None
    assert spec.equinox is None
    assert spec.instant == "2026-08-30T00:00:00.000"
    assert spec.time_scale == "utc"
    assert context.reference_equinox == "J2000"
    assert context.evaluation_instant == spec.instant
    assert context.evaluation_time_scale == "utc"
    assert context.observation.instant == spec.instant


def test_of_date_reference_is_separate_from_product_frame(monkeypatch):
    monkeypatch.setattr(
        ChartObserverRequest, "matches", lambda self, observer: True
    )

    context = chart_request_realization_context(
        request("horizontal", equinox="of_date"), Observer()
    )

    assert context.product_coordinate_spec.frame == "altaz"
    assert context.product_coordinate_spec.equinox is None
    assert "2026-08-30" in context.reference_equinox


def test_request_context_rejects_an_unmatched_observer(monkeypatch):
    monkeypatch.setattr(
        ChartObserverRequest, "matches", lambda self, observer: False
    )

    with pytest.raises(ValueError, match="does not match"):
        chart_request_realization_context(request("horizontal"), Observer())


def test_request_context_accepts_the_chart_view_utc_datetime_contract(
    monkeypatch,
):
    monkeypatch.setattr(
        ChartObserverRequest, "matches", lambda self, observer: True
    )
    observer = SimpleNamespace(
        utc_datetime=datetime(
            2026, 8, 30, 0, 0, tzinfo=timezone.utc
        ),
        lat_deg=-33.0,
        lon_deg=-71.0,
        elevation_m=100.0,
    )

    context = chart_request_realization_context(
        request("horizontal"), observer
    )

    assert context.observation.instant == "2026-08-30T00:00:00.000"
    assert context.observation.time_scale == "utc"
