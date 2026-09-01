"""Scientific layer-realization context for ordinary chart requests."""

from __future__ import annotations

from wenu.coordinates import (
    CoordinateSpec,
    PositionStatus,
    observation_context,
    observer_altaz_spec,
)
from wenu.sky.realization import LayerRealizationContext

from .request import ChartRequest


def chart_request_realization_context(request, observer):
    """Build one output-neutral pre-projection context for *request*."""
    if not isinstance(request, ChartRequest):
        raise TypeError("request must be a ChartRequest.")
    if observer is None:
        raise TypeError("observer is required for layer realization.")
    if not request.observer.matches(observer):
        raise ValueError("observer does not match the chart request.")

    observation = observation_context(observer)
    frame = request.coordinate_frame
    if frame == "horizontal":
        product_spec = observer_altaz_spec(
            observer,
            position_status=PositionStatus.APPARENT,
            provider="wenu chart request",
            model="vacuum observer-horizontal product frame",
        )
    elif frame == "galactic":
        product_spec = CoordinateSpec(
            frame="galactic",
            origin="observer",
            position_status=PositionStatus.APPARENT,
            instant=observation.instant,
            time_scale=observation.time_scale,
            provider="wenu chart request",
            model="observer-origin galactic product frame",
        )
    elif frame == "ecliptic":
        sequence = request.solar_system_disk_sequence
        start = sequence.sequence.start_instant
        scale = sequence.sequence.start_time_scale
        product_spec = CoordinateSpec(
            frame="barycentric-mean-ecliptic",
            origin="frozen-earth",
            position_status=PositionStatus.GEOMETRIC,
            equinox=sequence.sequence.ecliptic_equinox,
            instant=start,
            time_scale=scale,
            provider="wenu chart request",
            model="fixed-Earth J2000 ecliptic construction",
            provenance=("Earth position frozen at sequence start",),
        )
    else:
        raise ValueError(
            f"Unsupported chart coordinate frame: {frame!r}."
        )

    reference_equinox = request.reference_policy.resolved_equinox(observer)
    return LayerRealizationContext(
        product_coordinate_spec=product_spec,
        observation=observation,
        evaluation_instant=observation.instant,
        evaluation_time_scale=observation.time_scale,
        reference_equinox=str(reference_equinox),
    )
