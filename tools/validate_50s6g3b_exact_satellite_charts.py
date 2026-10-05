#!/usr/bin/env python3
"""Generate offline 50S.6G.3B charts from a physically propagated pass."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from wenu import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    DetailOverrides,
    Observer,
    SatelliteExactTrackDisplayRequest,
    build_chart_request,
    export_prepared_chart,
)
from wenu.charts.request_chart import PreparedChartRequest
from wenu.coordinate_service import CoordinateService
from wenu.coordinates import (
    CoordinateSpec,
    PositionStatus,
    observation_context,
    observer_altaz_spec,
)
from wenu.geometry.spherical import SphericalPoints
from wenu.output_policy import OutputFormat
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteFieldOfView,
    SatelliteObserver,
)
from wenu.satellites.crossing_oracle import (
    LocalSatelliteCrossingOracle,
    LocalSatelliteCrossingQuery,
)
from wenu.satellites.exact_tracks import (
    ExactLocalSatelliteTrackRealizer,
    ExactLocalTrackPolicy,
)
from wenu.satellites.sgp4 import Sgp4TemePropagator
from wenu.satellites.snapshots import (
    load_snapshot,
    load_snapshot_directory,
)
from wenu.satellites.topocentric import SatelliteTopocentricTransformer


REFERENCE = datetime(2026, 9, 15, 2, 35, tzinfo=timezone.utc)
LATITUDE_DEG = -32.443342
LONGITUDE_DEG = -71.230289
ELEVATION_M = 52.0
FIELD_RADIUS_DEG = 3.0
REGIONAL_FIELD_WIDTH_DEG = 20.0
REGIONAL_FIELD_HEIGHT_DEG = 16.0


def iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def satellite_observer():
    return SatelliteObserver(
        "la-ligua",
        LONGITUDE_DEG,
        LATITUDE_DEG,
        ELEVATION_M,
        refraction_policy="vacuum",
        earth_orientation_policy="iers-a-bundled",
    )


def load_specimen_snapshot(snapshot_directory):
    return (
        load_snapshot()
        if snapshot_directory is None
        else load_snapshot_directory(snapshot_directory)
    )


def physically_realized_track(snapshot_directory=None):
    """Solve and realize one pass entirely through accepted offline owners."""
    snapshot = load_specimen_snapshot(snapshot_directory)
    observer = satellite_observer()
    record = snapshot.records[0]
    digest = snapshot.manifest.content_sha256
    propagated = Sgp4TemePropagator(
        record, snapshot_sha256=digest
    ).propagate(iso(REFERENCE))
    center = SatelliteTopocentricTransformer().transform(
        propagated, observer
    )
    if center.altitude_deg <= FIELD_RADIUS_DEG:
        raise RuntimeError(
            "The physical specimen field is not completely above the "
            "geometric horizon."
        )
    field_spec = CoordinateSpec(
        frame="gcrs-axes",
        origin="topocentric-direction",
        position_status=PositionStatus.GEOMETRIC,
        instant=iso(REFERENCE),
        time_scale="utc",
        provider="wenu accepted local satellite propagation",
        model="fixed GCRS-axis topocentric field",
    )
    field = SatelliteFieldOfView(
        "50s6g3b-physical-pass-field",
        center.gcrs_axis_longitude_deg,
        center.gcrs_axis_latitude_deg,
        FIELD_RADIUS_DEG,
        field_spec,
    )
    interval = InclusiveTimeInterval(
        iso(REFERENCE - timedelta(seconds=120)),
        iso(REFERENCE + timedelta(seconds=120)),
    )
    query = LocalSatelliteCrossingQuery(
        snapshot=snapshot,
        observer=observer,
        field_of_view=field,
        interval=interval,
        time_tolerance_seconds=0.05,
        angular_tolerance_deg=1.0e-4,
    )
    crossings = tuple(
        crossing
        for crossing in LocalSatelliteCrossingOracle().solve(query)
        if (
            crossing.candidate.satellite.norad_catalog_id
            == record.norad_catalog_id
        )
    )
    if len(crossings) != 1:
        raise RuntimeError(
            "Expected exactly one crossing for the selected propagated record; "
            f"found {len(crossings)}."
        )
    crossing = crossings[0]
    if (
        crossing.entry_instant == interval.start
        or crossing.exit_instant == interval.stop
    ):
        raise RuntimeError(
            "The specimen interval did not bracket a complete crossing."
        )
    track = ExactLocalSatelliteTrackRealizer().realize(
        crossing,
        snapshot,
        ExactLocalTrackPolicy(
            angular_chord_tolerance_deg=0.005,
            maximum_step_seconds=0.5,
        ),
    )
    return track


def horizontal_center(track):
    observer = Observer(
        time=iso(REFERENCE),
        lat_deg=LATITUDE_DEG,
        lon_deg=LONGITUDE_DEG,
        elevation_m=ELEVATION_M,
    )
    try:
        field = track.crossing.candidate.field_of_view
        native = SphericalPoints(
            [field.center_longitude_deg],
            [field.center_latitude_deg],
            coordinate_spec=field.coordinate_spec,
        )
        transformed = CoordinateService().transform(
            native,
            observer_altaz_spec(
                observer,
                position_status=PositionStatus.GEOMETRIC,
                provider="50S.6G.3B physical specimen chart",
            ),
            observation_context(observer),
        )
        return float(transformed.lat_deg[0]), float(transformed.lon_deg[0])
    finally:
        observer.close()


def request_for(output, track, *, family, label_events):
    altitude, azimuth = horizontal_center(track)
    frame = (
        ChartFrameRequest(
            field_width_deg=REGIONAL_FIELD_WIDTH_DEG,
            field_height_deg=REGIONAL_FIELD_HEIGHT_DEG,
            center_altitude_deg=altitude,
            center_azimuth_deg=azimuth,
        )
        if family == "regional"
        else ChartFrameRequest(
            center_altitude_deg=altitude,
            center_azimuth_deg=azimuth,
        )
    )
    return ChartRequest(
        observer=ChartObserverRequest(
            time=iso(REFERENCE),
            lat_deg=LATITUDE_DEG,
            lon_deg=LONGITUDE_DEG,
            elevation_m=ELEVATION_M,
        ),
        family=family,
        product=ChartProductOptions(
            output=output,
            output_format=OutputFormat.PNG,
        ),
        subject=ChartSubjectRequest(),
        frame=frame,
        horizon=False,
        detail=DetailOverrides(
            enabled_layers=frozenset({
                "stars",
                "constellation_lines",
                "constellation_labels",
            }),
        ),
        satellite_exact_tracks=(
            SatelliteExactTrackDisplayRequest(
                track,
                draw_path=True,
                draw_events=True,
                label_events=label_events,
            ),
        ),
        title=(
            "Physically propagated satellite track — regional"
            if family == "regional"
            else "Physically propagated satellite track — binocular"
        ),
    )


def export_formats(request, output_directory):
    outputs = []
    with build_chart_request(request) as build:
        for output_format in OutputFormat:
            output = output_directory / (
                f"50s6g3b-{request.family}.{output_format.value}"
            )
            formatted_request = replace(
                request,
                product=ChartProductOptions(
                    output=output,
                    output_format=output_format,
                ),
            )
            prepared = PreparedChartRequest(
                chart=build.prepared.chart,
                resolved=replace(
                    build.prepared.resolved,
                    request=formatted_request,
                ),
            )
            generation = export_prepared_chart(build.sky, prepared)
            outputs.extend(generation.outputs)
    return tuple(outputs)


def verify_outputs(outputs, output_directory):
    for output in outputs:
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"missing specimen: {output}")

    regional_svg = (
        output_directory / "50s6g3b-regional.svg"
    ).read_text(encoding="utf-8")
    binocular_svg = (
        output_directory / "50s6g3b-binocular.svg"
    ).read_text(encoding="utf-8")
    required_semantics = (
        "sky/artificial_satellites/exact_local_tracks/",
        "/track",
        "/events",
        "track_identity_sha256",
    )
    if any(value not in regional_svg for value in required_semantics):
        raise RuntimeError("regional SVG lacks exact-track semantics.")
    if any(value not in binocular_svg for value in required_semantics):
        raise RuntimeError("binocular SVG lacks exact-track semantics.")
    if any(
        label not in regional_svg
        for label in (
            ">entry</text>",
            ">closest approach</text>",
            ">exit</text>",
        )
    ):
        raise RuntimeError("regional SVG lacks a visible exact event label.")
    if any(
        label in binocular_svg
        for label in (
            ">entry</text>",
            ">closest approach</text>",
            ">exit</text>",
        )
    ):
        raise RuntimeError("binocular SVG unexpectedly contains event labels.")
    if '"samples":' in regional_svg or '"samples":' in binocular_svg:
        raise RuntimeError("SVG provenance recursively serialized samples.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_directory", type=Path)
    parser.add_argument(
        "--snapshot-directory",
        type=Path,
        help=(
            "optional explicit validated snapshot directory; otherwise use "
            "the installed deterministic snapshot"
        ),
    )
    arguments = parser.parse_args()
    output_directory = arguments.output_directory.expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    track = physically_realized_track(arguments.snapshot_directory)
    outputs = []
    outputs.extend(
        export_formats(
            request_for(
                output_directory,
                track,
                family="regional",
                label_events=True,
            ),
            output_directory,
        )
    )
    outputs.extend(
        export_formats(
            request_for(
                output_directory,
                track,
                family="binocular",
                label_events=False,
            ),
            output_directory,
        )
    )
    verify_outputs(outputs, output_directory)

    crossing = track.crossing
    identity = crossing.candidate.satellite
    print(
        "PHYSICAL_TRACK="
        f"NORAD {identity.norad_catalog_id} {identity.object_name}; "
        f"{crossing.entry_instant} to {crossing.exit_instant}; "
        f"{len(track.samples)} retained samples; "
        f"digest {track.track_identity_sha256}"
    )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
