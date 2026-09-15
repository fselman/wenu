"""Renderer-neutral reports for normalized SatChecker candidate evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
import json

from wenu.satchecker import (
    SatCheckerCandidateEvidence,
    SatCheckerQuery,
    SatCheckerResponse,
    SatCheckerTaskState,
)


SATELLITE_PRESENTATION_SCHEMA_VERSION = 1
SATELLITE_PRESENTATION_PRODUCT = (
    "wenu.satchecker_sampled_candidate_evidence"
)
SATELLITE_PRESENTATION_STATUS = (
    "SatChecker sampled candidate evidence — not verified crossings"
)


def _strings(values, *, name):
    normalized = tuple(str(value).strip() for value in values)
    if any(not value for value in normalized):
        raise ValueError(f"{name} entries must be non-empty.")
    return normalized


def _coordinate_spec_document(spec):
    return {
        "frame": spec.frame,
        "origin": spec.origin,
        "position_status": spec.position_status.value,
        "epoch": spec.epoch,
        "equinox": spec.equinox,
        "instant": spec.instant,
        "time_scale": spec.time_scale,
        "longitude_unit": spec.longitude_unit,
        "latitude_unit": spec.latitude_unit,
        "representation": spec.representation,
        "provider": spec.provider,
        "model": spec.model,
        "provenance": list(spec.provenance),
        "corrections": sorted(spec.corrections),
    }


def _candidate_document(evidence):
    candidate = evidence.candidate
    satellite = candidate.satellite
    return {
        "identity": {
            "norad_catalog_id": satellite.norad_catalog_id,
            "object_name": satellite.object_name,
            "international_designator": satellite.international_designator,
            "classification": satellite.classification,
        },
        "source_provider": candidate.source_provider,
        "provider_version": evidence.provider_version,
        "response_sha256": evidence.response_sha256,
        "orbit_solution_id": candidate.orbit_solution_id,
        "snapshot_sha256": candidate.snapshot_sha256,
        "element_epoch": candidate.element_epoch,
        "provenance": list(candidate.provenance),
        "warnings": list(candidate.warnings),
        "samples": [
            {
                "sequence_index": index,
                "instant_utc": sample.instant_utc,
                "julian_date_ut1": sample.julian_date_ut1,
                "right_ascension_deg": sample.right_ascension_deg,
                "declination_deg": sample.declination_deg,
                "angular_distance_deg": sample.angular_distance_deg,
                "altitude_deg": sample.altitude_deg,
                "azimuth_deg": sample.azimuth_deg,
                "range_km": sample.range_km,
                "provider_illuminated": sample.illuminated,
            }
            for index, sample in enumerate(evidence.samples)
        ],
    }


@dataclass(frozen=True)
class SatCheckerPresentation:
    """One deterministic presentation of a terminal SatChecker response."""

    query: SatCheckerQuery
    response: SatCheckerResponse
    cache_provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.query, SatCheckerQuery):
            raise TypeError("query must be a SatCheckerQuery.")
        if not isinstance(self.response, SatCheckerResponse):
            raise TypeError("response must be a SatCheckerResponse.")
        if not self.response.terminal:
            raise ValueError(
                "presentation requires a terminal SatChecker response."
            )
        evidence = tuple(self.response.evidence)
        if (
            self.response.state is not SatCheckerTaskState.SUCCESS
            and evidence
        ):
            raise ValueError(
                "non-success responses cannot contain candidate evidence."
            )
        identifiers = [
            value.candidate.satellite.norad_catalog_id
            for value in evidence
        ]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "candidate evidence must contain unique NORAD identities."
            )
        for value in evidence:
            if not isinstance(value, SatCheckerCandidateEvidence):
                raise TypeError(
                    "response evidence must contain "
                    "SatCheckerCandidateEvidence values."
                )
            candidate = value.candidate
            if (
                candidate.observer != self.query.observer
                or candidate.field_of_view != self.query.field_of_view
                or candidate.interval != self.query.interval
            ):
                raise ValueError(
                    "candidate query context does not match presentation query."
                )
        object.__setattr__(
            self,
            "cache_provenance",
            _strings(self.cache_provenance, name="cache_provenance"),
        )

    @property
    def evidence(self):
        """Return candidates in stable NORAD catalogue order."""
        return tuple(
            sorted(
                self.response.evidence,
                key=lambda value: value.candidate.satellite.norad_catalog_id,
            )
        )

    @property
    def document(self):
        """Return the versioned JSON-compatible report document."""
        receipt = self.response.receipt
        sample_count = sum(len(value.samples) for value in self.evidence)
        return {
            "schema_version": SATELLITE_PRESENTATION_SCHEMA_VERSION,
            "product": SATELLITE_PRESENTATION_PRODUCT,
            "scientific_status": SATELLITE_PRESENTATION_STATUS,
            "sample_coordinate_spec": _coordinate_spec_document(
                self.query.field_of_view.coordinate_spec
            ),
            "request": self.query.canonical_document,
            "response": {
                "state": self.response.state.value,
                "terminal": self.response.terminal,
                "task_id": self.response.task_id,
                "progress": self.response.progress,
                "message": self.response.message,
                "candidate_count": len(self.evidence),
                "sample_count": sample_count,
                "receipt": {
                    "endpoint": receipt.endpoint,
                    "retrieved_at_utc": receipt.retrieved_at_utc,
                    "http_status": receipt.http_status,
                    "media_type": receipt.media_type,
                    "response_sha256": receipt.body_sha256,
                },
                "cache_provenance": list(self.cache_provenance),
            },
            "candidates": [
                _candidate_document(value) for value in self.evidence
            ],
        }

    def to_json(self):
        """Serialize the deterministic report as UTF-8 JSON text."""
        return json.dumps(
            self.document,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        ) + "\n"

    def to_text(self):
        """Serialize the same report model as deterministic readable text."""
        document = self.document
        response = document["response"]
        request = document["request"]["wenu_request"]
        observer = request["observer"]
        field = request["field_of_view"]
        interval = request["interval"]
        lines = [
            SATELLITE_PRESENTATION_STATUS,
            f"State: {response['state']}",
            f"Task: {response['task_id'] or 'unknown'}",
            (
                "Observer: "
                f"{observer['observer_id']} "
                f"({observer['latitude_deg']:.6f}, "
                f"{observer['longitude_deg']:.6f}, "
                f"{observer['elevation_m']:.1f} m)"
            ),
            (
                "Field: "
                f"{field['field_id']} — closed circle, "
                f"radius {field['angular_radius_deg']:.6f} deg"
            ),
            (
                "Interval: "
                f"{interval['start_utc']} through "
                f"{interval['stop_utc']} inclusive UTC"
            ),
            (
                "Evidence: "
                f"{response['candidate_count']} candidates, "
                f"{response['sample_count']} samples"
            ),
            (
                "Receipt: "
                f"{response['receipt']['response_sha256']} "
                f"({response['receipt']['http_status']} "
                f"{response['receipt']['media_type']})"
            ),
        ]
        if response["message"]:
            lines.append(f"Message: {response['message']}")
        for provenance in response["cache_provenance"]:
            lines.append(f"Cache provenance: {provenance}")
        for candidate in document["candidates"]:
            identity = candidate["identity"]
            name = identity["object_name"] or "unnamed"
            lines.append(
                f"Candidate NORAD {identity['norad_catalog_id']}: {name}"
            )
            lines.append(
                "  Provider: "
                f"{candidate['source_provider']} "
                f"{candidate['provider_version']}"
            )
            if candidate["element_epoch"] is not None:
                lines.append(
                    f"  Element epoch: {candidate['element_epoch']}"
                )
            for warning in candidate["warnings"]:
                lines.append(f"  Warning: {warning}")
            for sample in candidate["samples"]:
                illuminated = sample["provider_illuminated"]
                provider_light = (
                    "unknown" if illuminated is None else str(illuminated).lower()
                )
                lines.append(
                    "  Sample "
                    f"{sample['sequence_index']}: "
                    f"{sample['instant_utc']} UTC; "
                    f"RA {sample['right_ascension_deg']:.8f} deg; "
                    f"Dec {sample['declination_deg']:.8f} deg; "
                    f"provider illuminated {provider_light}"
                )
        return "\n".join(lines) + "\n"
