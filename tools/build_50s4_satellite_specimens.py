"""Build deterministic 50S.4E propagated sampled specimens offline."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
import json
from pathlib import Path

from wenu.satellite_crossings import SatelliteObserver
from wenu.satellites.sgp4 import Sgp4TemePropagator
from wenu.satellites.snapshots import DEFAULT_SNAPSHOT_ID, load_snapshot
from wenu.satellites.topocentric import SatelliteTopocentricTransformer


OUTPUT_NAME = "propagated-sampled-specimens.json"
SPECIMEN_LABEL = "propagated sampled specimens — not verified crossings"
DEFAULT_START_UTC = "2026-09-15T00:00:00.000000Z"
DEFAULT_STEP_SECONDS = 300
DEFAULT_SAMPLE_COUNT = 3
DEFAULT_FIELD_RADIUS_DEG = 1.0


def _utc(value: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not value.strip():
        raise TypeError("start_utc must be a non-empty UTC string.")
    value = value.strip()
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        instant = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValueError("start_utc must be an ISO-8601 UTC instant.") from error
    if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
        raise ValueError("start_utc must be an ISO-8601 UTC instant.")
    instant = instant.astimezone(timezone.utc)
    normalized = instant.isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )
    return normalized, instant


def _positive_integer(value, *, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a positive integer.")
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _positive_float(value, *, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be positive.")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be positive.") from error
    if result <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return result


def _instants(start_utc, step_seconds, sample_count):
    normalized, start = _utc(start_utc)
    step_seconds = _positive_integer(step_seconds, name="step_seconds")
    sample_count = _positive_integer(sample_count, name="sample_count")
    values = tuple(
        (start + timedelta(seconds=index * step_seconds))
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
        for index in range(sample_count)
    )
    return normalized, values


def _observer_mapping(observer):
    return {
        "observer_id": observer.observer_id,
        "longitude_deg": observer.longitude_deg,
        "latitude_deg": observer.latitude_deg,
        "elevation_m": observer.elevation_m,
        "refraction_policy": observer.refraction_policy,
        "earth_orientation_policy": observer.earth_orientation_policy,
    }


def _earth_orientation_identity(evidence):
    return {
        "table_class": evidence.table_class,
        "source_sha256": evidence.source_sha256,
        "astropy_version": evidence.astropy_version,
        "astropy_iers_data_version": evidence.astropy_iers_data_version,
        "coverage_start_mjd": evidence.coverage_start_mjd,
        "coverage_stop_mjd": evidence.coverage_stop_mjd,
    }


def _sample_mapping(state):
    teme = state.teme_state
    evidence = state.earth_orientation
    return {
        "evaluation_utc": teme.evaluation_utc,
        "element_age_days": teme.element_age_days,
        "teme": {
            "frame": teme.frame,
            "center": teme.center,
            "representation": teme.representation,
            "position_km": list(teme.position_km),
            "velocity_km_per_s": list(teme.velocity_km_per_s),
            "status_code": teme.status_code,
        },
        "topocentric": {
            "range_km": state.range_km,
            "azimuth_deg": state.azimuth_deg,
            "altitude_deg": state.altitude_deg,
            "gcrs_axis_longitude_deg": state.gcrs_axis_longitude_deg,
            "gcrs_axis_latitude_deg": state.gcrs_axis_latitude_deg,
            "direction_identity": (
                "topocentric geometric direction expressed in GCRS axes"
            ),
        },
        "earth_orientation_values": {
            "ut1_minus_utc_s": evidence.ut1_minus_utc_s,
            "polar_motion_x_arcsec": evidence.polar_motion_x_arcsec,
            "polar_motion_y_arcsec": evidence.polar_motion_y_arcsec,
            "ut1_status": evidence.ut1_status,
            "polar_motion_status": evidence.polar_motion_status,
        },
    }


def build_specimens(
    output_directory,
    *,
    snapshot_id=DEFAULT_SNAPSHOT_ID,
    start_utc=DEFAULT_START_UTC,
    step_seconds=DEFAULT_STEP_SECONDS,
    sample_count=DEFAULT_SAMPLE_COUNT,
    observer=None,
    field_radius_deg=DEFAULT_FIELD_RADIUS_DEG,
):
    """Write one bounded sampled-track document to an explicit directory."""
    output_directory = Path(output_directory).expanduser().resolve()
    if output_directory.exists() and not output_directory.is_dir():
        raise ValueError("output_directory must identify a directory.")
    output_directory.mkdir(parents=True, exist_ok=True)

    start_utc, evaluation_instants = _instants(
        start_utc, step_seconds, sample_count
    )
    field_radius_deg = _positive_float(
        field_radius_deg, name="field_radius_deg"
    )
    if field_radius_deg > 180.0:
        raise ValueError("field_radius_deg must not exceed 180.")
    if observer is None:
        observer = SatelliteObserver(
            observer_id="la-ligua",
            longitude_deg=-71.230289,
            latitude_deg=-32.443342,
            elevation_m=52.0,
            refraction_policy="vacuum",
            earth_orientation_policy="iers-a-bundled",
        )
    if not isinstance(observer, SatelliteObserver):
        raise TypeError("observer must be a SatelliteObserver.")

    snapshot = load_snapshot(snapshot_id)
    transformer = SatelliteTopocentricTransformer()
    tracks = []
    earth_orientation = None
    for record in snapshot.records:
        propagator = Sgp4TemePropagator(
            record,
            snapshot_sha256=snapshot.manifest.content_sha256,
        )
        states = tuple(
            transformer.transform(teme, observer)
            for teme in propagator.propagate_many(evaluation_instants)
        )
        identity = _earth_orientation_identity(states[0].earth_orientation)
        if earth_orientation is None:
            earth_orientation = identity
        elif identity != earth_orientation:
            raise ValueError(
                "sampled states do not share one Earth-orientation resource."
            )
        middle = states[len(states) // 2]
        tracks.append({
            "identity": {
                "norad_catalog_id": record.norad_catalog_id,
                "object_name": record.object_name,
                "international_designator": record.international_designator,
                "source_record_sha256": record.source_record_sha256,
            },
            "propagator": {
                "identity": middle.teme_state.implementation,
                "sgp4_version": middle.teme_state.sgp4_version,
                "gravity_model": middle.teme_state.gravity_model,
                "operation_mode": middle.teme_state.operation_mode,
            },
            "samples": [_sample_mapping(state) for state in states],
            "query_input": {
                "interval_start_utc": evaluation_instants[0],
                "interval_stop_utc": evaluation_instants[-1],
                "field_center_longitude_deg": (
                    middle.gcrs_axis_longitude_deg
                ),
                "field_center_latitude_deg": middle.gcrs_axis_latitude_deg,
                "field_radius_deg": field_radius_deg,
                "coordinate_identity": (
                    "topocentric geometric direction expressed in GCRS axes"
                ),
                "claim": "sampled query input only; no crossing result",
            },
        })

    document = {
        "schema_version": 1,
        "label": SPECIMEN_LABEL,
        "scope": (
            "Deterministic offline samples and query inputs for later "
            "50S.5 crossing-oracle development."
        ),
        "snapshot": {
            "snapshot_id": snapshot.manifest.snapshot_id,
            "content_sha256": snapshot.manifest.content_sha256,
            "record_count": snapshot.manifest.record_count,
            "record_order": [
                record.norad_catalog_id for record in snapshot.records
            ],
        },
        "evaluation_grid": {
            "start_utc": start_utc,
            "step_seconds": step_seconds,
            "sample_count": sample_count,
            "instants_utc": list(evaluation_instants),
        },
        "observer": _observer_mapping(observer),
        "earth_orientation": earth_orientation,
        "software": {
            "wenu_version": version("wenu"),
            "builder": "tools/build_50s4_satellite_specimens.py",
        },
        "tracks": tracks,
        "prohibitions": [
            "not a verified crossing",
            "not a complete catalogue search",
            "not a production crossing solver or tolerance authority",
        ],
    }
    output = output_directory / OUTPUT_NAME
    output.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--snapshot-id", default=DEFAULT_SNAPSHOT_ID)
    parser.add_argument("--start-utc", default=DEFAULT_START_UTC)
    parser.add_argument(
        "--step-seconds", type=int, default=DEFAULT_STEP_SECONDS
    )
    parser.add_argument(
        "--sample-count", type=int, default=DEFAULT_SAMPLE_COUNT
    )
    parser.add_argument(
        "--field-radius-deg", type=float, default=DEFAULT_FIELD_RADIUS_DEG
    )
    arguments = parser.parse_args()
    output = build_specimens(
        arguments.output_directory,
        snapshot_id=arguments.snapshot_id,
        start_utc=arguments.start_utc,
        step_seconds=arguments.step_seconds,
        sample_count=arguments.sample_count,
        field_radius_deg=arguments.field_radius_deg,
    )
    print(output)


if __name__ == "__main__":
    main()
