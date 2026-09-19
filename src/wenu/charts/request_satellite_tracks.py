"""Request-owned presentation of already-realized exact satellite tracks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from wenu.coordinates import PositionStatus
from wenu.satellites.exact_tracks import ExactLocalSatelliteTrack
from wenu.sky.satellite_exact_track_layer import (
    SatelliteExactTrackEventsLayer,
    SatelliteExactTrackLayer,
)


@dataclass(frozen=True)
class SatelliteExactTrackDisplayRequest:
    """Presentation controls for one immutable exact local track."""

    track: ExactLocalSatelliteTrack
    draw_path: bool = True
    draw_events: bool = True
    label_events: bool = False

    def __post_init__(self):
        if not isinstance(self.track, ExactLocalSatelliteTrack):
            raise TypeError("track must be an ExactLocalSatelliteTrack.")
        for name in ("draw_path", "draw_events", "label_events"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a bool.")
        if not self.draw_path and not self.draw_events:
            raise ValueError("An exact satellite track must draw a path or events.")
        if self.label_events and not self.draw_events:
            raise ValueError("label_events requires draw_events.")


def _utc_datetime(value):
    if not isinstance(value, str):
        raise ValueError("The crossing field requires a UTC reference instant.")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    instant = datetime.fromisoformat(candidate)
    if instant.tzinfo is None:
        raise ValueError("The crossing field requires a UTC reference instant.")
    return instant.astimezone(timezone.utc)


def validate_satellite_exact_track_requests(request):
    """Fail closed unless every display request matches one chart context."""
    displays = tuple(request.satellite_exact_tracks)
    if any(
        not isinstance(value, SatelliteExactTrackDisplayRequest)
        for value in displays
    ):
        raise TypeError(
            "satellite_exact_tracks must contain "
            "SatelliteExactTrackDisplayRequest values."
        )
    identities = tuple(
        value.track.track_identity_sha256 for value in displays
    )
    if len(set(identities)) != len(identities):
        raise ValueError("satellite_exact_tracks cannot repeat a track identity.")
    if not displays:
        return displays
    if request.family not in {"regional", "binocular"}:
        raise ValueError(
            "Exact satellite tracks are supported only by regional and "
            "binocular charts."
        )
    if (
        request.projection != "stereographic"
        or request.coordinate_frame != "horizontal"
    ):
        raise ValueError(
            "Exact satellite tracks require stereographic horizontal charts."
        )
    latitude, longitude, elevation, instant = (
        request.observer.scientific_identity()
    )
    instant = instant.astimezone(timezone.utc)
    for display in displays:
        track = display.track
        crossing = track.crossing
        candidate = crossing.candidate
        observer = candidate.observer
        field_spec = candidate.field_of_view.coordinate_spec
        if (
            observer.latitude_deg != latitude
            or observer.longitude_deg != longitude
            or observer.elevation_m != elevation
        ):
            raise ValueError(
                "Exact satellite track observer does not match chart observer."
            )
        if (
            observer.refraction_policy != "vacuum"
            or observer.earth_orientation_policy
            not in {"astropy", "iers-a-bundled"}
        ):
            raise ValueError(
                "Exact satellite track coordinate policies do not match the "
                "chart observer contract."
            )
        if (
            field_spec.frame != "gcrs-axes"
            or field_spec.origin != "topocentric-direction"
            or field_spec.position_status is not PositionStatus.GEOMETRIC
            or field_spec.time_scale != "utc"
            or field_spec.instant is None
        ):
            raise ValueError(
                "Exact satellite track field must declare geometric "
                "topocentric GCRS axes at a UTC reference instant."
            )
        if _utc_datetime(field_spec.instant) != instant:
            raise ValueError(
                "Exact satellite track field reference instant does not "
                "match chart observer instant."
            )
        if track.sample_time_scale != "utc":
            raise ValueError("Exact satellite track samples must use UTC.")
    return displays


def configure_chart_request_satellite_tracks(sky, request):
    """Install request-owned exact path and event layers in supplied order."""
    displays = validate_satellite_exact_track_requests(request)
    layers = []
    try:
        for display in displays:
            if display.draw_path:
                layer = SatelliteExactTrackLayer(display.track)
                sky.add(layer)
                layers.append(layer)
            if display.draw_events:
                layer = SatelliteExactTrackEventsLayer(
                    display.track,
                    label_events=display.label_events,
                )
                sky.add(layer)
                layers.append(layer)
    except BaseException:
        for layer in reversed(layers):
            sky.remove(layer)
        raise
    return tuple(layers)


def satellite_exact_track_provenance(request):
    """Return deterministic bounded summaries without serializing samples."""
    summaries = []
    for display in request.satellite_exact_tracks:
        track = display.track
        crossing = track.crossing
        identity = crossing.candidate.satellite
        summaries.append(
            {
                "track_identity_sha256": track.track_identity_sha256,
                "norad_catalog_id": identity.norad_catalog_id,
                "display_name": (
                    identity.object_name
                    or f"NORAD {identity.norad_catalog_id}"
                ),
                "field_id": crossing.candidate.field_of_view.field_id,
                "entry_instant_utc": crossing.entry_instant,
                "closest_approach_instant_utc": (
                    crossing.closest_approach_instant
                ),
                "exit_instant_utc": crossing.exit_instant,
                "snapshot_sha256": crossing.candidate.snapshot_sha256,
                "draw_path": display.draw_path,
                "draw_events": display.draw_events,
                "label_events": display.label_events,
            }
        )
    return tuple(summaries)


def chart_request_provenance_parameters(request):
    """Mirror dataclass provenance while bounding exact-track content."""
    from dataclasses import asdict, replace

    parameters = asdict(replace(request, satellite_exact_tracks=()))
    parameters["satellite_exact_tracks"] = satellite_exact_track_provenance(
        request
    )
    return parameters
