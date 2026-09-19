"""Output-neutral layers for exact local satellite track evidence."""

from __future__ import annotations

import numpy as np

from wenu.coordinate_service import CoordinateService
from wenu.geometry.spherical import SphericalCurves, SphericalPoints
from wenu.satellites.exact_tracks import (
    EXACT_LOCAL_TRACK_STATUS,
    ExactLocalSatelliteTrack,
)
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.sky_layer import SkyLayer


def _display_name(track):
    identity = track.crossing.candidate.satellite
    return identity.object_name or f"NORAD {identity.norad_catalog_id}"


def _visit_key(track):
    identity = track.crossing.candidate.satellite
    return (
        f"norad_{identity.norad_catalog_id}__visit_"
        f"{track.track_identity_sha256[:16]}"
    )


def _metadata(track):
    crossing = track.crossing
    return {
        "scientific_status": EXACT_LOCAL_TRACK_STATUS,
        "semantic_entity_key": f"norad_{crossing.candidate.satellite.norad_catalog_id}",
        "semantic_entity_display_name": _display_name(track),
        "visit_key": _visit_key(track),
        "norad_catalog_id": crossing.candidate.satellite.norad_catalog_id,
        "field_id": crossing.candidate.field_of_view.field_id,
        "entry_instant_utc": crossing.entry_instant,
        "closest_approach_instant_utc": crossing.closest_approach_instant,
        "exit_instant_utc": crossing.exit_instant,
        "sample_instants_utc": tuple(item.instant_utc for item in track.samples),
        "sample_time_scale": track.sample_time_scale,
        "sample_roles": tuple(item.roles for item in track.samples),
        "track_identity_sha256": track.track_identity_sha256,
        "snapshot_sha256": crossing.candidate.snapshot_sha256,
        "continuous_containment_verified": True,
        "exact_crossing_events": True,
        "sampling_certificate": (
            "each accepted leaf passed midpoint chord-deviation and "
            "maximum-time-step tests"
        ),
        "global_continuous_error_proven": False,
        "angular_chord_tolerance_deg": (
            track.policy.angular_chord_tolerance_deg
        ),
        "maximum_step_seconds": track.policy.maximum_step_seconds,
        "provenance": track.provenance,
        "warnings": track.warnings,
    }


class _ExactSatelliteTrackLayer(SkyLayer):
    layer_name = None

    def __init__(self, track, *, coordinate_service=None):
        if not isinstance(track, ExactLocalSatelliteTrack):
            raise TypeError("track must be an ExactLocalSatelliteTrack.")
        self.track = track
        self.norad_catalog_id = (
            track.crossing.candidate.satellite.norad_catalog_id
        )
        self.satellite_display_name = _display_name(track)
        self.visit_key = _visit_key(track)
        self.coordinate_service = (
            CoordinateService()
            if coordinate_service is None else coordinate_service
        )

    def realize(self, context, observer, **geometry_options):
        del observer
        if not isinstance(context, LayerRealizationContext):
            raise TypeError("context must be a LayerRealizationContext.")
        if geometry_options:
            raise TypeError(
                f"{type(self).__name__} accepts no geometry options."
            )
        native = self._native_geometry()
        if native.coordinate_spec == context.product_coordinate_spec:
            return native
        return self.coordinate_service.transform(
            native,
            context.product_coordinate_spec,
            context.observation,
        )

    def spherical_geometry(self, observer):
        del observer
        raise RuntimeError(
            f"{type(self).__name__} requires a LayerRealizationContext."
        )


class SatelliteExactTrackLayer(_ExactSatelliteTrackLayer):
    """Expose one exact connected visit as an open curve or singleton point."""

    layer_name = "satellite_exact_track"

    def _native_geometry(self):
        samples = self.track.samples
        name = self.satellite_display_name
        metadata = _metadata(self.track)
        if len(samples) == 1:
            sample = samples[0]
            return SphericalPoints(
                [sample.longitude_deg],
                [sample.latitude_deg],
                coordinate_spec=self.track.coordinate_spec,
                ids=np.asarray((f"{self.visit_key}__all_events",), dtype=object),
                labels=np.asarray((name,), dtype=object),
                names=np.asarray((name,), dtype=object),
                metadata={
                    **metadata,
                    "geometry_status": "zero-duration visit; no segment",
                },
            )
        return SphericalCurves(
            lon_deg=(
                np.asarray(
                    [item.longitude_deg for item in samples], dtype=float
                ),
            ),
            lat_deg=(
                np.asarray(
                    [item.latitude_deg for item in samples], dtype=float
                ),
            ),
            coordinate_spec=self.track.coordinate_spec,
            closed=np.asarray((False,)),
            ids=np.asarray((f"{self.visit_key}__track",), dtype=object),
            labels=np.asarray((name,), dtype=object),
            names=np.asarray((name,), dtype=object),
            metadata={
                **metadata,
                "geometry_status": "open exact connected-visit polyline",
            },
        )


class SatelliteExactTrackEventsLayer(_ExactSatelliteTrackLayer):
    """Expose exact event markers by selecting retained evidence vertices."""

    layer_name = "satellite_exact_track_events"

    def _native_geometry(self):
        selected = tuple(
            (sample, role)
            for sample in self.track.samples
            for role in sample.roles
        )
        name = self.satellite_display_name
        labels = {
            "entry": "entry",
            "closest_approach": "closest approach",
            "exit": "exit",
        }
        return SphericalPoints(
            [sample.longitude_deg for sample, _role in selected],
            [sample.latitude_deg for sample, _role in selected],
            coordinate_spec=self.track.coordinate_spec,
            ids=np.asarray(
                tuple(
                    f"{self.visit_key}__{role}"
                    for _sample, role in selected
                ),
                dtype=object,
            ),
            labels=np.asarray(
                tuple(labels[role] for _sample, role in selected),
                dtype=object,
            ),
            names=np.asarray(
                tuple(name for _sample, _role in selected),
                dtype=object,
            ),
            metadata={
                **_metadata(self.track),
                "geometry_status": "exact event views over retained samples",
                "event_roles": tuple(role for _sample, role in selected),
                "recomputed": False,
            },
        )
