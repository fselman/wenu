#!/usr/bin/env python3
"""Generate deterministic offline 50S.6G.3B acceptance specimens."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from math import cos, radians, sin
from pathlib import Path

from wenu import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    Observer,
    DetailOverrides,
    SatelliteExactTrackDisplayRequest,
    build_chart_request,
    export_prepared_chart,
)
from wenu.charts.request_chart import PreparedChartRequest
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
    SatelliteCrossingCandidate,
    SatelliteCrossingResult,
    SatelliteFieldOfView,
    SatelliteIdentity,
    SatelliteObserver,
)
from wenu.satellites.exact_tracks import (
    ExactLocalSatelliteTrack,
    ExactLocalSatelliteTrackSample,
    ExactLocalTrackPolicy,
)
from wenu.coordinate_service import CoordinateService


START = datetime(2026, 9, 19, 1, 0, tzinfo=timezone.utc)
LATITUDE_DEG = -32.443342
LONGITUDE_DEG = -71.230289
ELEVATION_M = 52.0


def iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def direction(longitude_deg, latitude_deg=0.0):
    longitude = radians(longitude_deg)
    latitude = radians(latitude_deg)
    scale = cos(latitude)
    return (
        scale * cos(longitude),
        scale * sin(longitude),
        sin(latitude),
    )


def specimen_track():
    field_spec = CoordinateSpec(
        frame="gcrs-axes",
        origin="topocentric-direction",
        position_status=PositionStatus.GEOMETRIC,
        instant=iso(START),
        time_scale="utc",
        provider="50S.6G.3B deterministic specimen",
    )
    candidate = SatelliteCrossingCandidate(
        satellite=SatelliteIdentity(
            900001, "50S.6G.3B TEST SAT", "2026-001A", "U"
        ),
        observer=SatelliteObserver(
            "la-ligua",
            LONGITUDE_DEG,
            LATITUDE_DEG,
            ELEVATION_M,
            refraction_policy="vacuum",
            earth_orientation_policy="iers-a-bundled",
        ),
        field_of_view=SatelliteFieldOfView(
            "50s6g3b-specimen-field",
            6.0,
            0.0,
            8.0,
            field_spec,
        ),
        interval=InclusiveTimeInterval(
            iso(START), iso(START + timedelta(seconds=12))
        ),
        source_provider="wenu deterministic specimen",
        orbit_solution_id="50s6g3b-synthetic-orbit",
        snapshot_sha256="a" * 64,
        element_epoch=iso(START),
        provenance=("constructed immutable acceptance evidence",),
    )
    crossing = SatelliteCrossingResult(
        candidate=candidate,
        entry_instant=iso(START),
        closest_approach_instant=iso(START + timedelta(seconds=6)),
        exit_instant=iso(START + timedelta(seconds=12)),
        closest_approach_deg=0.0,
        range_km=500.0,
        angular_rate_deg_per_s=1.0,
        provenance=("deterministic 50S.6G.3B specimen",),
    )
    samples = []
    for seconds, longitude, latitude, roles in (
        (0, 3.0, 0.0, ("entry",)),
        (3, 4.5, 4.0, ()),
        (6, 6.0, 0.0, ("closest_approach",)),
        (9, 7.5, -4.0, ()),
        (12, 9.0, 0.0, ("exit",)),
    ):
        vector = direction(longitude, latitude)
        samples.append(
            ExactLocalSatelliteTrackSample(
                instant_utc=iso(START + timedelta(seconds=seconds)),
                direction=vector,
                longitude_deg=longitude,
                latitude_deg=latitude,
                range_km=500.0,
                roles=roles,
                provenance=("constructed retained specimen vertex",),
            )
        )
    return ExactLocalSatelliteTrack(
        crossing=crossing,
        samples=tuple(samples),
        coordinate_spec=CoordinateSpec(
            frame="gcrs-axes",
            origin="topocentric-direction",
            position_status=PositionStatus.GEOMETRIC,
            provider="50S.6G.3B deterministic specimen",
            model="fixed GCRS-axis retained directions",
        ),
        policy=ExactLocalTrackPolicy(
            angular_chord_tolerance_deg=0.01,
            maximum_step_seconds=6.0,
        ),
        provenance=("constructed immutable acceptance evidence",),
    )


def horizontal_center(track):
    observer = Observer(
        time=iso(START),
        lat_deg=LATITUDE_DEG,
        lon_deg=LONGITUDE_DEG,
        elevation_m=ELEVATION_M,
    )
    try:
        middle = track.samples[1]
        native = SphericalPoints(
            [middle.longitude_deg],
            [middle.latitude_deg],
            coordinate_spec=track.coordinate_spec,
        )
        transformed = CoordinateService().transform(
            native,
            observer_altaz_spec(
                observer,
                position_status=PositionStatus.GEOMETRIC,
                provider="50S.6G.3B specimen chart",
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
            field_width_deg=8.0,
            field_height_deg=6.0,
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
            time=iso(START),
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
            "Exact satellite track — regional"
            if family == "regional"
            else "Exact satellite track — binocular"
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_directory", type=Path)
    arguments = parser.parse_args()
    output_directory = arguments.output_directory.expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    track = specimen_track()
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

    for output in outputs:
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"missing specimen: {output}")
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
