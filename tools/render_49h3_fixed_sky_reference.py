#!/usr/bin/env python3
"""Render the uncached 49H.3 fixed-sky and rotating-horizon reference."""

from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image

from wenu import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    DetailOverrides,
    FixedSkyRotatingHorizonSequenceRequest,
    TemporalTimeline,
    generate_fixed_sky_rotating_horizon_sequence,
)
from wenu.output_policy import OutputFormat


DEFAULT_START = "2026-08-21T21:00:00-04:00"
DEFAULT_STOP = "2026-08-22T03:00:00-04:00"
DEFAULT_TIMEZONE = "America/Santiago"


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/wenu-49h3-fixed-sky"),
    )
    value.add_argument("--start", default=DEFAULT_START)
    value.add_argument("--stop", default=DEFAULT_STOP)
    value.add_argument("--frames", type=int, default=3)
    value.add_argument("--display-timezone", default=DEFAULT_TIMEZONE)
    value.add_argument("--location", default="La Ligua")
    value.add_argument("--pole", choices=("north", "south"), default="south")
    value.add_argument("--limiting-declination", type=float, default=-50.0)
    return value


def aware_datetime(value: str, *, option: str) -> datetime:
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise SystemExit(f"{option} must include a UTC offset.")
    return instant


def reference_request(arguments: argparse.Namespace):
    start = aware_datetime(arguments.start, option="--start")
    stop = aware_datetime(arguments.stop, option="--stop")
    timeline = TemporalTimeline.uniform(
        start,
        stop,
        arguments.frames,
        display_timezone=arguments.display_timezone,
    )
    chart = ChartRequest(
        observer=ChartObserverRequest(
            time=start,
            location=arguments.location,
        ),
        family="circumpolar",
        frame=ChartFrameRequest(
            pole=arguments.pole,
            limiting_declination_deg=arguments.limiting_declination,
        ),
        product=ChartProductOptions(
            output=arguments.output / "reference-frames",
            output_format=OutputFormat.PNG,
            style="atlas",
            mode="presentation",
        ),
        horizon=True,
        detail=DetailOverrides(
            star_magnitude_limit=5.0,
            enabled_layers=frozenset({
                "stars",
                "constellation_lines",
                "constellation_labels",
                "equatorial_grid",
                "altaz_grid",
                "horizon",
            }),
            grid_label_layers=frozenset({
                "equatorial_grid",
                "altaz_grid",
            }),
            equatorial_declination_step_deg=10.0,
        ),
        title="49H.3 fixed sky and rotating horizon reference",
    )
    return FixedSkyRotatingHorizonSequenceRequest(
        chart=chart,
        timeline=timeline,
        celestial_anchor_time=start,
    )


def frame_record(result) -> dict:
    path = result.output
    with Image.open(path) as image:
        dimensions = [int(value) for value in image.size]
    payload = path.read_bytes()
    orientation = result.resolved.orientation
    frame = result.resolved.frame
    return {
        "name": path.name,
        "path": str(path),
        "simulation_time": frame.simulation_time.isoformat(),
        "display_time": frame.display_time.isoformat(),
        "position_angle_deg": orientation.position_angle_deg,
        "anchor_reference_position_angle_deg": (
            orientation.anchor_reference_position_angle_deg
        ),
        "frame_reference_position_angle_deg": (
            orientation.frame_reference_position_angle_deg
        ),
        "dimensions": dimensions,
        "bytes": len(payload),
        "sha256": sha256(payload).hexdigest(),
    }


def audit(arguments: argparse.Namespace) -> Path:
    request = reference_request(arguments)
    generation = generate_fixed_sky_rotating_horizon_sequence(request)
    records = [frame_record(frame) for frame in generation.frames]
    report = {
        "schema_version": 1,
        "audit_kind": "fixed_sky_rotating_horizon_reference",
        "role": "uncached_behavior_validation",
        "celestial_anchor_time": request.celestial_anchor_time.isoformat(),
        "frame_count": request.frame_count,
        "frames": records,
        "uniform_dimensions": len({
            tuple(record["dimensions"]) for record in records
        }) == 1,
        "distinct_frame_hashes": len({
            record["sha256"] for record in records
        }),
    }
    if not report["uniform_dimensions"]:
        raise RuntimeError("Reference frame dimensions are not uniform.")
    if report["distinct_frame_hashes"] < 2:
        raise RuntimeError("Reference frames do not change across time.")
    destination = arguments.output / "fixed-sky-reference-audit.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def main() -> None:
    print(audit(parser().parse_args()))


if __name__ == "__main__":
    main()
