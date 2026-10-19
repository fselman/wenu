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


def chart_cluster_motion_options(request, observer):
    """Prepare one explicit immutable cluster model/context for this request.

    No shared layer mutation or acquisition. Source admission/observer realization
    remain in their existing owners; chart code only composes public services.
    """
    selection = request.cluster_motion
    if selection.model == "lookup":
        return {}
    if request.coordinate_frame != "horizontal" or not request.observer.matches(observer):
        raise ValueError("Cluster motion requires a matching horizontal observer request.")
    if observer.elevation_m != selection.height_wgs84_m:
        raise ValueError("Observer elevation must match caller-qualified WGS84 height_wgs84_m.")
    from importlib.resources import as_file, files
    from math import floor
    from wenu.astrometric_observation import ErfaReceptionBackend
    from wenu.cluster_state import load_cluster_motion
    from wenu_kernel.records import TimePoint, TimeSpan

    def point(jd, scale):
        whole = floor(jd + .5)
        return TimePoint(whole, jd-whole, scale)

    backend = ErfaReceptionBackend(leap_seconds_path=selection.leap_seconds_path,
        leap_seconds_sha256=selection.leap_seconds_sha256,
        eop_path=selection.eop_path,eop_sha256=selection.eop_sha256,
        backend_identity=selection.backend_identity,
        coverage=TimeSpan(point(selection.start_jd_tt,'tt'),point(selection.stop_jd_tt,'tt')))
    reception = backend.prepare(observer.utc_datetime.isoformat().replace('+00:00','Z'),
        longitude_deg=observer.lon_deg,latitude_deg=observer.lat_deg,height_m=selection.height_wgs84_m)
    selected = tuple(value for value in selection.identifiers
        if value not in request.exclusions.open_clusters
        and (request.content.open_clusters is None or value in request.content.open_clusters))
    if not selected:
        return {'open_clusters': {'enabled': False}}
    data = files('wenu.data.catalogs.open_clusters')
    with as_file(data.joinpath('open_clusters_hunt_astrometry_v1.ecsv')) as source:
        with as_file(data.joinpath('open_clusters_hunt_motion_admission_v1.json')) as admission:
            motion = load_cluster_motion(source, admission,
                coverage=TimeSpan(point(selection.start_jd_tcb,'tcb'),point(selection.stop_jd_tcb,'tcb')))
    return {'open_clusters': {'geometry': {'motion': motion, 'reception': reception,
        'selected': selected}}}
