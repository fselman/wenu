"""Drawable layers for normalized SatChecker sampled candidate evidence."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import CoordinateSpec
from wenu.geometry.spherical import SphericalCurves, SphericalPoints
from wenu.satchecker import SatCheckerCandidateEvidence
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.sky_layer import SkyLayer


def _sample_key(norad_catalog_id, instant_utc):
    compact = "".join(
        character.lower()
        for character in instant_utc
        if character.isalnum()
    )
    return f"norad_{norad_catalog_id}__sample_{compact}"


def _display_name(evidence):
    identity = evidence.candidate.satellite
    return identity.object_name or f"NORAD {identity.norad_catalog_id}"


def _track_coordinate_spec(evidence):
    spec = evidence.candidate.field_of_view.coordinate_spec
    return replace(
        spec,
        instant=None,
        time_scale=None,
        provenance=(
            *spec.provenance,
            "SatChecker provider-sampled candidate directions",
            f"sample start: {evidence.samples[0].instant_utc} UTC",
            f"sample end: {evidence.samples[-1].instant_utc} UTC",
            "per-sample UTC instants retained in geometry metadata",
        ),
    )


def _metadata(evidence):
    identity = evidence.candidate.satellite
    return {
        "scientific_status": (
            "SatChecker sampled candidate evidence — not verified crossings"
        ),
        "semantic_entity_key": f"norad_{identity.norad_catalog_id}",
        "semantic_entity_display_name": _display_name(evidence),
        "norad_catalog_id": identity.norad_catalog_id,
        "sample_instants_utc": tuple(
            sample.instant_utc for sample in evidence.samples
        ),
        "sample_julian_dates_ut1": tuple(
            sample.julian_date_ut1 for sample in evidence.samples
        ),
        "sample_order": "provider temporal order",
        "continuous_containment_verified": False,
        "exact_crossing_events": False,
        "provider_version": evidence.provider_version,
        "response_sha256": evidence.response_sha256,
        "provider_illumination": tuple(
            sample.illuminated for sample in evidence.samples
        ),
        "warnings": tuple(evidence.candidate.warnings),
    }


class _SatelliteCandidateLayer(SkyLayer):
    """Common validation and product-frame transformation."""

    layer_name = None

    def __init__(self, evidence, *, coordinate_service=None):
        if not isinstance(evidence, SatCheckerCandidateEvidence):
            raise TypeError(
                "evidence must be a SatCheckerCandidateEvidence."
            )
        self.evidence = evidence
        self.norad_catalog_id = (
            evidence.candidate.satellite.norad_catalog_id
        )
        self.satellite_display_name = _display_name(evidence)
        self.coordinate_service = (
            CoordinateService()
            if coordinate_service is None else coordinate_service
        )

    def realize(self, context, observer, **geometry_options):
        del observer
        if not isinstance(context, LayerRealizationContext):
            raise TypeError(
                "context must be a LayerRealizationContext."
            )
        if geometry_options:
            raise TypeError(
                f"{type(self).__name__} accepts no geometry options."
            )
        native = self._native_geometry()
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


class SatelliteCandidateTrackLayer(_SatelliteCandidateLayer):
    """Draw one open sampled path, or one point for singleton evidence."""

    layer_name = "satellite_candidate_track"

    def _native_geometry(self):
        samples = self.evidence.samples
        identity = self.evidence.candidate.satellite
        name = self.satellite_display_name
        spec = _track_coordinate_spec(self.evidence)
        metadata = _metadata(self.evidence)
        key = f"norad_{identity.norad_catalog_id}__sampled_track"
        if len(samples) == 1:
            sample = samples[0]
            return SphericalPoints(
                [sample.right_ascension_deg],
                [sample.declination_deg],
                coordinate_spec=spec,
                ids=np.asarray(
                    (_sample_key(identity.norad_catalog_id, sample.instant_utc),),
                    dtype=object,
                ),
                labels=np.asarray((name,), dtype=object),
                names=np.asarray((name,), dtype=object),
                metadata={
                    **metadata,
                    "geometry_status": "singleton sample; no segment",
                },
            )
        return SphericalCurves(
            lon_deg=(
                np.asarray(
                    [sample.right_ascension_deg for sample in samples],
                    dtype=float,
                ),
            ),
            lat_deg=(
                np.asarray(
                    [sample.declination_deg for sample in samples],
                    dtype=float,
                ),
            ),
            coordinate_spec=spec,
            closed=np.asarray((False,)),
            ids=np.asarray((key,), dtype=object),
            labels=np.asarray((name,), dtype=object),
            names=np.asarray((name,), dtype=object),
            metadata={
                **metadata,
                "geometry_status": "open polyline in provider sample order",
            },
        )


class SatelliteCandidateSamplesLayer(_SatelliteCandidateLayer):
    """Draw supplied samples with optional UTC labels and no interpolation."""

    layer_name = "satellite_candidate_samples"

    def __init__(
        self,
        evidence,
        *,
        label_times=True,
        coordinate_service=None,
    ):
        super().__init__(
            evidence,
            coordinate_service=coordinate_service,
        )
        self.label_times = bool(label_times)

    def _native_geometry(self):
        samples = self.evidence.samples
        identity = self.evidence.candidate.satellite
        name = self.satellite_display_name
        labels = (
            np.asarray(
                tuple(sample.instant_utc for sample in samples),
                dtype=object,
            )
            if self.label_times
            else np.asarray(tuple(None for sample in samples), dtype=object)
        )
        return SphericalPoints(
            [sample.right_ascension_deg for sample in samples],
            [sample.declination_deg for sample in samples],
            coordinate_spec=_track_coordinate_spec(self.evidence),
            ids=np.asarray(
                tuple(
                    _sample_key(
                        identity.norad_catalog_id,
                        sample.instant_utc,
                    )
                    for sample in samples
                ),
                dtype=object,
            ),
            labels=labels,
            names=np.asarray(
                tuple(name for sample in samples),
                dtype=object,
            ),
            metadata={
                **_metadata(self.evidence),
                "geometry_status": "supplied sample points only",
                "utc_labels": self.label_times,
            },
        )
