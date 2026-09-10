"""Benchmark cold independent circumpolar frames through the canonical route.

The exclusive timings are diagnostic accounting, not pass/fail thresholds.
Every interval observed by the Python profiler belongs to exactly one stage;
time outside a declared stage is reported as the residual.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
from statistics import median
import subprocess
import sys
from time import perf_counter_ns

from PIL import Image

from wenu.charts.fixed_sky_sequence import (
    FixedSkyRotatingHorizonSequenceRequest,
    resolve_fixed_sky_rotating_horizon_frame,
)
from wenu.charts.product_options import ChartProductOptions
from wenu.charts.request import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartRequest,
)
from wenu.charts.request_generation import generate_chart_request
from wenu.output_policy import OutputFormat
from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS
from wenu.sky.maximal_sphere import CANONICAL_MAXIMAL_SPHERE_PROFILE
from wenu.temporal import TemporalTimeline


STAGES = (
    "request_orchestration",
    "catalogue_resource_loading",
    "provider_evaluation",
    "astronomical_transformation",
    "projection",
    "chart_preparation",
    "rendering",
    "encoding_export",
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _outside_repository(path, *, name):
    resolved = Path(path).resolve()
    if resolved == REPOSITORY_ROOT or resolved.is_relative_to(REPOSITORY_ROOT):
        raise ValueError(f"{name} must be outside the repository.")
    return resolved


def _normalized_filename(frame):
    return frame.f_code.co_filename.replace("\\", "/")


def _stage_for_frame(frame):
    """Classify one active Python frame by its narrowest timing owner."""
    filename = _normalized_filename(frame)
    name = frame.f_code.co_name
    if name == "save" and filename.endswith("/wenu/charts/regional.py"):
        return "encoding_export"
    if "/matplotlib/backends/" in filename:
        return "encoding_export"
    if filename.endswith("/wenu/coordinate_service.py"):
        return "astronomical_transformation"
    if "/wenu/projections/" in filename:
        return "projection"
    if (
        "/wenu/rendering/preparation.py" in filename
        or filename.endswith("/wenu/charts/spatial_selection.py")
        or filename.endswith("/wenu/charts/request_chart.py")
        or (
            filename.endswith("/wenu/sky/celestial_sphere.py")
            and name in {"draw_chart", "_pipeline_options"}
        )
    ):
        return "chart_preparation"
    if (
        "/wenu/rendering/" in filename
        or "_furniture.py" in filename
        or "legend" in Path(filename).name
        or filename.endswith("/wenu/chart_document.py")
        or ("/wenu/charts/" in filename and name == "render")
    ):
        return "rendering"
    if (
        filename.endswith("/wenu/ephemeris.py")
        or filename.endswith("/wenu/skyfield_ephemeris.py")
        or filename.endswith("/wenu/solar_system_directions.py")
        or filename.endswith("/wenu/solar_system_appearance.py")
        or "/wenu/sky/solar_system" in filename
        or name in {"spherical_geometry", "realize", "observed_altaz"}
    ):
        return "provider_evaluation"
    if "/skyfield/iokit.py" in filename or (
        filename.endswith("/wenu/sky/maximal_sphere.py")
        and name in {"build_maximal_sphere", "generate_celestial_sphere"}
    ):
        return "catalogue_resource_loading"
    if (
        filename.endswith("/wenu/charts/request_generation.py")
        or filename.endswith("/wenu/charts/fixed_sky_sequence.py")
        or filename.endswith("/wenu/charts/fixed_sky_orientation.py")
    ):
        return "request_orchestration"
    return None


class ExclusiveStageTimer:
    """Assign elapsed profiler intervals to one deepest declared owner."""

    def __init__(self, clock=perf_counter_ns):
        self.clock = clock
        self.stage_ns = {stage: 0 for stage in STAGES}
        self.residual_ns = 0
        self._stack = []
        self._last_ns = None

    def _owner(self):
        for frame in reversed(self._stack):
            stage = _stage_for_frame(frame)
            if stage is not None:
                return stage
        return None

    def _charge(self, now):
        if self._last_ns is None:
            self._last_ns = now
            return
        elapsed = now - self._last_ns
        owner = self._owner()
        if owner is None:
            self.residual_ns += elapsed
        else:
            self.stage_ns[owner] += elapsed
        self._last_ns = now

    def __call__(self, frame, event, argument):
        del argument
        now = self.clock()
        self._charge(now)
        if event == "call":
            self._stack.append(frame)
        elif event in {"return", "exception"}:
            if self._stack and self._stack[-1] is frame:
                self._stack.pop()
        return self

    def measure(self, operation):
        """Run one operation and return its exclusive nanosecond account."""
        started = self.clock()
        self._last_ns = started
        sys.setprofile(self)
        try:
            value = operation()
        finally:
            sys.setprofile(None)
            finished = self.clock()
            self._charge(finished)
        complete = finished - started
        classified = sum(self.stage_ns.values())
        # Profiler callback overhead and the final unprofiled edge are made
        # explicit in residual so accounting closes exactly.
        self.residual_ns += complete - classified - self.residual_ns
        return value, {
            **self.stage_ns,
            "unclassified_residual": self.residual_ns,
            "complete_frame": complete,
        }


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _commit():
    try:
        return subprocess.run(
            ("git", "rev-parse", "HEAD"),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def default_sequence(destination):
    """Return the fixed, offline three-frame 49J.4 workload."""
    start = datetime(2026, 8, 22, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 22, 7, tzinfo=timezone.utc)
    return FixedSkyRotatingHorizonSequenceRequest(
        chart=ChartRequest(
            observer=ChartObserverRequest(
                time=start,
                location="La Ligua",
            ),
            family="circumpolar",
            frame=ChartFrameRequest(
                pole="south",
                limiting_declination_deg=-60.0,
            ),
            product=ChartProductOptions(
                output=Path(destination),
                output_format=OutputFormat.PNG,
            ),
        ),
        timeline=TemporalTimeline.uniform(
            start,
            end,
            3,
            display_timezone="America/Santiago",
        ),
        celestial_anchor_time=start,
    )


def _json_value(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}.")


def benchmark(destination):
    """Measure three fresh canonical frames and return raw evidence."""
    destination = _outside_repository(destination, name="output")
    destination.mkdir(parents=True, exist_ok=True)
    sequence = default_sequence(destination)
    frames = []
    for frame in sequence.frames:
        measured = {}

        def generate_frame():
            resolved = resolve_fixed_sky_rotating_horizon_frame(frame)
            measured["resolved"] = resolved
            return generate_chart_request(
                resolved.chart_request,
                configuration=sequence.configuration,
            )

        timer = ExclusiveStageTimer()
        generation, timings = timer.measure(generate_frame)
        resolved = measured["resolved"]
        output = generation.outputs[0]
        rendering = generation.exports[0].rendering
        with Image.open(output) as image:
            dimensions = image.size
        frames.append({
            "index": frame.index,
            "simulation_time": frame.simulation_time.isoformat(),
            "display_time": frame.display_time.isoformat(),
            "request": asdict(resolved.chart_request),
            "orientation": asdict(resolved.orientation),
            "timings_ns": timings,
            "output": {
                "path": str(output),
                "format": output.suffix.removeprefix(".").lower(),
                "dimensions_px": dimensions,
                "size_bytes": output.stat().st_size,
                "sha256": _sha256(output),
            },
            "canonical_oracle": "generate_chart_request",
            "semantic_projection_evidence": {
                "layer_count": len(rendering.layers),
                "semantic_paths": [
                    layer.semantic_identity.semantic_path_text
                    for layer in rendering.layers
                    if layer.semantic_identity is not None
                ],
                "projected_types": [
                    type(layer.projected).__name__
                    for layer in rendering.layers
                ],
            },
        })
    names = STAGES + ("unclassified_residual", "complete_frame")
    summary = {}
    for name in names:
        observations = [frame["timings_ns"][name] for frame in frames]
        summary[name] = {
            "median_ns": median(observations),
            "minimum_ns": min(observations),
            "maximum_ns": max(observations),
            "range_ns": max(observations) - min(observations),
        }
    ephemeris_path = DEFAULT_DATA_DIRECTORY / DEFAULT_EPHEMERIS
    return {
        "schema": "wenu.cold-independent-frame-benchmark.v1",
        "environment": {
            "commit": _commit(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "resources": {
            "ephemeris": {
                "name": DEFAULT_EPHEMERIS,
                "sha256": (
                    _sha256(ephemeris_path)
                    if ephemeris_path.is_file()
                    else None
                ),
            },
            "catalogue_profile": asdict(CANONICAL_MAXIMAL_SPHERE_PROFILE),
        },
        "measurement": {
            "clock": "time.perf_counter_ns",
            "exclusive": True,
            "threshold": None,
            "stage_order": STAGES + ("unclassified_residual",),
            "summary": summary,
        },
        "timeline": asdict(sequence.timeline),
        "frames": frames,
    }


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--output", type=Path, required=True)
    value.add_argument("--report", type=Path, required=True)
    return value


def main():
    arguments = parser().parse_args()
    report = benchmark(arguments.output)
    report_path = _outside_repository(arguments.report, name="report")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, default=_json_value, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(report_path)


if __name__ == "__main__":
    main()
