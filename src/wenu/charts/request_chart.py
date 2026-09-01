"""Construct canonical chart geometry from one resolved chart request."""

from __future__ import annotations

from dataclasses import dataclass

import astropy.units as u
from astropy.coordinates import SkyCoord

from .binocular import BinocularChart
from .all_sky import AllSkyChart
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


def _regional_chart(sky, resolved, observer):
    subject = resolved.constellations
    frame = resolved.frame
    if subject is None:
        raise ValueError("A regional chart requires resolved constellations.")
    options = {
        "orientation": frame.orientation,
        "position_angle_deg": frame.position_angle_deg,
        "label_selection": subject.label_constellations,
        "outside_mask_constellations": (
            subject.boundary_constellations
            if resolved.request.mask else None
        ),
        "framing_constellations": subject.boundary_constellations,
    }
    if frame.center_altitude_deg is not None:
        from .regional import resolve_chart_orientation

        if frame.field_width_deg is None:
            raise ValueError(
                "fixed horizontal center requires field width and height."
            )
        resolved_orientation = resolve_chart_orientation(
            observer,
            center_alt_deg=frame.center_altitude_deg,
            center_az_deg=frame.center_azimuth_deg,
            orientation=frame.orientation,
            position_angle_deg=frame.position_angle_deg,
        )
        return RegionalChart(
            center_alt_deg=frame.center_altitude_deg,
            center_az_deg=frame.center_azimuth_deg,
            field_width_deg=frame.field_width_deg,
            field_height_deg=frame.field_height_deg,
            position_angle_deg=resolved_orientation.position_angle_deg,
            resolved_orientation=resolved_orientation,
            label_selection=subject.label_constellations,
            outside_mask_constellations=(
                subject.boundary_constellations
                if resolved.request.mask else None
            ),
        )
    if frame.field_width_deg is None:
        return RegionalChart.from_constellations(
            sky, subject.line_constellations, observer=observer, **options
        )
    return RegionalChart.from_constellations(
        sky,
        subject.line_constellations,
        observer=observer,
        angular_radius_deg=frame.field_height_deg / 2.0,
        aspect_ratio=frame.field_width_deg / frame.field_height_deg,
        **options,
    )


def _chart_from_resolved(sky, resolved, observer):
    request = resolved.request
    frame = resolved.frame
    from .request_disks import FrozenEarthSolarSystemDiskSequenceDisplayRequest

    if isinstance(
        request.solar_system_disk_sequence,
        FrozenEarthSolarSystemDiskSequenceDisplayRequest,
    ):
        from .request_realization import chart_request_realization_context

        sun_layers = tuple(
            layer for layer in sky.layers
            if getattr(layer, "layer_name", "") == "frozen_earth_sun"
        )
        if len(sun_layers) != 1:
            raise RuntimeError(
                "frozen-Earth sequence requires one fixed Sun layer."
            )
        geometry = sun_layers[0].disk_realization.realize(
            chart_request_realization_context(request, observer), observer
        )
        return RegionalChart(
            center_alt_deg=float(geometry.sun.lat_deg[0]),
            center_az_deg=float(geometry.sun.lon_deg[0]),
            field_width_deg=frame.field_width_deg or 90.0,
            field_height_deg=frame.field_height_deg or 70.0,
            position_angle_deg=0.0,
            flip_ew=False,
        )
    if request.family == "planisphere":
        mask = (
            resolved.constellations.boundary_constellations
            if request.mask else None
        )
        return FullSkyChart(
            position_angle_deg=frame.position_angle_deg,
            horizon_color="#707070",
            horizon_linewidth=0.8,
            outside_mask_constellations=mask,
        )
    if request.family == "all_sky":
        mask = (
            resolved.constellations.boundary_constellations
            if request.mask else None
        )
        return AllSkyChart(outside_mask_constellations=mask)
    if request.family == "regional":
        return _regional_chart(sky, resolved, observer)
    if request.family == "circumpolar":
        return CircumpolarChart(
            observer,
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
            observer,
            _target_coordinate(resolved.target),
            field_diameter_deg=frame.field_diameter_deg,
            orientation=frame.orientation,
            position_angle_deg=frame.position_angle_deg,
        )
    raise ValueError(f"Unsupported chart family {request.family!r}.")


def prepare_chart_request(sky, resolved, *, observer=None):
    """Construct a chart and apply immutable field-content selection."""
    if not isinstance(resolved, ResolvedChartRequest):
        raise TypeError("resolved must be a ResolvedChartRequest.")
    resolved_observer = getattr(sky, "observer", None) if observer is None else observer
    if resolved_observer is None:
        raise TypeError("chart preparation requires an observer.")
    chart = _chart_from_resolved(sky, resolved, resolved_observer)
    selected = select_spatial_chart_content(
        sky, chart, resolved, observer=resolved_observer
    )
    return PreparedChartRequest(chart=chart, resolved=selected)
