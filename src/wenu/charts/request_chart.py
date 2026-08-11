"""Construct canonical chart geometry from one resolved chart request."""

from __future__ import annotations

from dataclasses import dataclass

import astropy.units as u
from astropy.coordinates import SkyCoord

from .binocular import BinocularChart
from .circumpolar import CircumpolarChart
from .full_sky import FullSkyChart
from .regional import RegionalChart
from .request_resolver import ResolvedChartRequest
from .spatial_selection import select_spatial_chart_content


@dataclass(frozen=True)
class PreparedChartRequest:
    """Resolved request paired with its canonical chart geometry."""

    chart: object
    resolved: ResolvedChartRequest


def _target_coordinate(target):
    return SkyCoord(
        ra=target.ra_deg * u.deg,
        dec=target.dec_deg * u.deg,
        frame="icrs",
    )


def _regional_chart(sky, resolved):
    subject = resolved.constellations
    frame = resolved.frame
    if subject is None:
        raise ValueError("A regional chart requires resolved constellations.")
    options = {
        "north_up": frame.position_angle_deg == 0.0,
        "position_angle_deg": frame.position_angle_deg,
        "label_selection": subject.label_constellations,
        "outside_mask_constellations": (
            subject.boundary_constellations
            if resolved.request.mask else None
        ),
    }
    if frame.field_width_deg is None:
        return RegionalChart.from_constellations(
            sky, subject.line_constellations, **options
        )
    return RegionalChart.from_constellations(
        sky,
        subject.line_constellations,
        angular_radius_deg=frame.field_height_deg / 2.0,
        aspect_ratio=frame.field_width_deg / frame.field_height_deg,
        **options,
    )


def _chart_from_resolved(sky, resolved):
    request = resolved.request
    frame = resolved.frame
    if request.family == "planisphere":
        mask = (
            resolved.constellations.boundary_constellations
            if request.mask else None
        )
        return FullSkyChart(
            position_angle_deg=frame.position_angle_deg,
            outside_mask_constellations=mask,
        )
    if request.family == "regional":
        return _regional_chart(sky, resolved)
    if request.family == "circumpolar":
        return CircumpolarChart(
            sky.observer,
            limiting_declination_deg=(
                request.frame.limiting_declination_deg
            ),
            pole=request.frame.pole,
            position_angle_deg=frame.position_angle_deg,
        )
    if request.family == "binocular":
        if resolved.target is None:
            raise ValueError("A binocular chart requires a resolved target.")
        return BinocularChart.from_coordinate(
            sky.observer,
            _target_coordinate(resolved.target),
            field_diameter_deg=frame.field_diameter_deg,
            north_up=frame.position_angle_deg == 0.0,
            position_angle_deg=frame.position_angle_deg,
        )
    raise ValueError(f"Unsupported chart family {request.family!r}.")


def prepare_chart_request(sky, resolved):
    """Construct a chart and apply immutable field-content selection."""
    if not isinstance(resolved, ResolvedChartRequest):
        raise TypeError("resolved must be a ResolvedChartRequest.")
    if getattr(sky, "observer", None) is None:
        raise TypeError("sky must provide its scientific observer.")
    chart = _chart_from_resolved(sky, resolved)
    selected = select_spatial_chart_content(sky, chart, resolved)
    return PreparedChartRequest(chart=chart, resolved=selected)
