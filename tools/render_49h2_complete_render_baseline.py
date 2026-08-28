#!/usr/bin/env python3
"""Generate and characterize the 49H.2 complete-render baseline."""

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
    generate_fixed_sky_complete_render_baseline,
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
        default=Path("/tmp/wenu-49h2-baseline"),
    )
    value.add_argument("--start", default=DEFAULT_START)
    value.add_argument("--stop", default=DEFAULT_STOP)
    value.add_argument("--frames", type=int, default=3)
    value.add_argument("--display-timezone", default=DEFAULT_TIMEZONE)
    value.add_argument("--location", default="La Ligua")
    value.add_argument("--pole", choices=("north", "south"), default="south")
    value.add_argument("--limiting-declination", type=float, default=-50.0)
    value.add_argument(
        "--restart-policy",
        choices=("restart", "resume"),
        default="restart",
    )
    return value


def aware_datetime(value: str, *, option: str) -> datetime:
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise SystemExit(f"{option} must include a UTC offset.")
    return instant


def baseline_request(arguments: argparse.Namespace):
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
            output=arguments.output / "candidate-reserved",
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
        title="49H.2 fixed-sky complete-render baseline",
    )
    return FixedSkyRotatingHorizonSequenceRequest(
        chart=chart,
        timeline=timeline,
        celestial_anchor_time=start,
    )


def png_record(path: Path) -> dict:
    with Image.open(path) as image:
        dimensions = [int(value) for value in image.size]
        mode = image.mode
    payload = path.read_bytes()
    return {
        "name": path.name,
        "bytes": len(payload),
        "sha256": sha256(payload).hexdigest(),
        "dimensions": dimensions,
        "mode": mode,
    }


def audit(arguments: argparse.Namespace) -> Path:
    request = baseline_request(arguments)
    baseline_directory = arguments.output / "complete-render-baseline"
    generation = generate_fixed_sky_complete_render_baseline(
        request,
        baseline_directory,
        restart_policy=arguments.restart_policy,
    )
    manifest = json.loads(
        generation.manifest_path.read_text(encoding="utf-8")
    )
    records = [png_record(path) for path in generation.outputs]
    report = {
        "schema_version": 1,
        "audit_kind": "fixed_sky_complete_render_baseline",
        "role": "unregistered_complete_render_baseline",
        "target_pixel_oracle": False,
        "celestial_anchor_time": request.celestial_anchor_time.isoformat(),
        "baseline_directory": str(baseline_directory),
        "manifest": str(generation.manifest_path),
        "manifest_identity_sha256": manifest["identity_sha256"],
        "frame_count": request.frame_count,
        "rendered_count": generation.rendered_count,
        "reused_count": generation.reused_count,
        "simulation_times": [
            value.isoformat() for value in request.timeline.instants
        ],
        "display_times": [
            value.isoformat() for value in request.timeline.display_instants
        ],
        "frames": records,
        "uniform_dimensions": len({
            tuple(record["dimensions"]) for record in records
        }) == 1,
        "distinct_frame_hashes": len({
            record["sha256"] for record in records
        }),
    }
    if not report["uniform_dimensions"]:
        raise RuntimeError("Baseline frame dimensions are not uniform.")
    if report["distinct_frame_hashes"] < 2:
        raise RuntimeError("Baseline frames do not change across observer time.")
    destination = arguments.output / "fixed-sky-baseline-audit.json"
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
