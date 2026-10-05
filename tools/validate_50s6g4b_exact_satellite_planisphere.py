#!/usr/bin/env python3
"""Generate one physical exact-track AltAz planisphere in three formats."""

from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

from wenu import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    DetailOverrides,
    SatelliteExactTrackDisplayRequest,
    build_chart_request,
    export_prepared_chart,
)
from wenu.charts.request_chart import PreparedChartRequest
from wenu.output_policy import OutputFormat

from validate_50s6g3b_exact_satellite_charts import (
    ELEVATION_M,
    LATITUDE_DEG,
    LONGITUDE_DEG,
    REFERENCE,
    iso,
    physically_realized_track,
)


def planisphere_request(output_directory, track):
    """Return the ordinary observer-horizontal planisphere request."""
    crossing = track.crossing
    interval = (
        f"{crossing.entry_instant} to {crossing.exit_instant}"
    )
    return ChartRequest(
        observer=ChartObserverRequest(
            time=iso(REFERENCE),
            lat_deg=LATITUDE_DEG,
            lon_deg=LONGITUDE_DEG,
            elevation_m=ELEVATION_M,
        ),
        family="planisphere",
        product=ChartProductOptions(
            output=output_directory,
            output_format=OutputFormat.PNG,
        ),
        subject=ChartSubjectRequest(),
        frame=ChartFrameRequest(),
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
                label_events=True,
            ),
        ),
        title=(
            "La Ligua exact satellite pass — chart reference "
            f"{iso(REFERENCE)} — {interval}"
        ),
    )


def export_formats(request, output_directory):
    """Prepare once and export PNG, PDF, and semantic SVG."""
    outputs = []
    with build_chart_request(request) as build:
        for output_format in OutputFormat:
            output = output_directory / (
                f"50s6g4b-altaz-planisphere.{output_format.value}"
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


def verify_outputs(outputs):
    """Require all formats and bounded exact-track SVG semantics."""
    if {path.suffix for path in outputs} != {".png", ".pdf", ".svg"}:
        raise RuntimeError("expected one PNG, PDF, and semantic SVG")
    for output in outputs:
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"missing specimen: {output}")
    svg = next(path for path in outputs if path.suffix == ".svg")
    text = svg.read_text(encoding="utf-8")
    required = (
        "sky/artificial_satellites/exact_local_tracks/",
        "/track",
        "/events",
        "track_identity_sha256",
        ">entry</text>",
        ">closest approach</text>",
        ">exit</text>",
    )
    if any(value not in text for value in required):
        raise RuntimeError("semantic SVG lacks exact-track evidence")
    if '"samples":' in text:
        raise RuntimeError("SVG provenance recursively serialized samples")


def write_manifest(destination, *, source_revision, track, outputs):
    """Write event-specific context and deterministic output digests."""
    crossing = track.crossing
    manifest = destination / "50s6g4b-altaz-planisphere-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "claim": "physically propagated exact connected visit",
                "product": "ordinary observer-horizontal planisphere",
                "projection": "stereographic",
                "source_revision": source_revision,
                "observer": {
                    "site": "La Ligua",
                    "observer_id": crossing.candidate.observer.observer_id,
                    "latitude_deg": LATITUDE_DEG,
                    "longitude_deg": LONGITUDE_DEG,
                    "elevation_m": ELEVATION_M,
                },
                "coordinate_reference_instant_utc": (
                    crossing.candidate.field_of_view.coordinate_spec.instant
                ),
                "entry_instant_utc": crossing.entry_instant,
                "closest_approach_instant_utc": (
                    crossing.closest_approach_instant
                ),
                "exit_instant_utc": crossing.exit_instant,
                "track_identity_sha256": track.track_identity_sha256,
                "retained_samples": len(track.samples),
                "outputs": [
                    {
                        "path": str(path),
                        "bytes": path.stat().st_size,
                        "sha256": sha256(path.read_bytes()).hexdigest(),
                    }
                    for path in outputs
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--snapshot-directory", type=Path)
    arguments = parser.parse_args(argv)
    destination = arguments.output_directory.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    track = physically_realized_track(arguments.snapshot_directory)
    request = planisphere_request(destination, track)
    outputs = export_formats(request, destination)
    verify_outputs(outputs)
    manifest = write_manifest(
        destination,
        source_revision=arguments.source_revision,
        track=track,
        outputs=outputs,
    )

    crossing = track.crossing
    identity = crossing.candidate.satellite
    print(
        "PHYSICAL_TRACK="
        f"NORAD {identity.norad_catalog_id} {identity.object_name}; "
        f"{crossing.entry_instant} to {crossing.exit_instant}; "
        f"{len(track.samples)} retained samples; "
        f"digest {track.track_identity_sha256}"
    )
    print(*(str(path) for path in (*outputs, manifest)), sep="\n")


if __name__ == "__main__":
    main()
