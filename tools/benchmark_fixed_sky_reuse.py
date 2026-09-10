#!/usr/bin/env python3
"""Compare loaded-sphere fixed-sky execution with the cold oracle.

Outputs and the JSON report must live outside the repository. The diagnostic
runs the accepted three-frame workload through both explicit execution modes,
retains raw timings, and verifies scientific plus exported-product evidence.
"""

from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass, replace
from datetime import datetime
from enum import Enum
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from time import perf_counter_ns

import numpy as np

from benchmark_cold_frames import default_sequence
from wenu.charts.fixed_sky_baseline import (
    available_pdf_page_renderer,
    compare_normalized_svg,
    compare_png_frames,
    render_pdf_page_rgba,
)
from wenu.charts.fixed_sky_sequence import (
    FixedSkySequenceExecution,
    generate_fixed_sky_rotating_horizon_sequence,
)
from wenu.output_policy import OutputFormat


FORMATS = (OutputFormat.PNG, OutputFormat.SVG, OutputFormat.PDF)
MODES = (
    FixedSkySequenceExecution.COLD,
    FixedSkySequenceExecution.REUSE_LOADED_SPHERE,
)


def _outside_repository(path: Path, *, name: str) -> Path:
    path = Path(path).expanduser().resolve()
    repository = Path(__file__).resolve().parents[1]
    if path == repository or repository in path.parents:
        raise ValueError(f"{name} must be outside the repository.")
    return path


def _canonical(value, active=None):
    """Encode inspectable scientific records without renderer object identity."""
    if active is None:
        active = set()
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return {"float_hex": value.hex()}
    if isinstance(value, Path):
        # Mode outputs deliberately live in different parent directories.
        return {"output_name": value.name}
    if isinstance(value, (datetime, Enum)):
        return str(getattr(value, "value", value))
    if isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        if array.dtype.hasobject:
            return {
                "ndarray_dtype": str(array.dtype),
                "shape": array.shape,
                "items": [
                    _canonical(item, active)
                    for item in array.reshape(-1).tolist()
                ],
            }
        return {
            "ndarray_dtype": str(array.dtype),
            "shape": array.shape,
            "sha256": hashlib.sha256(array.view(np.uint8)).hexdigest(),
        }
    if isinstance(value, np.generic):
        return _canonical(value.item(), active)
    identity = id(value)
    if identity in active:
        return {"cycle": type(value).__qualname__}
    active.add(identity)
    try:
        if is_dataclass(value) and not isinstance(value, type):
            return {
                "type": f"{type(value).__module__}.{type(value).__qualname__}",
                "fields": {
                    field.name: _canonical(getattr(value, field.name), active)
                    for field in fields(value)
                    if field.name not in {"artist", "artists", "renderer"}
                },
            }
        if isinstance(value, dict):
            return {
                str(key): _canonical(item, active)
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            }
        if isinstance(value, (tuple, list)):
            return [_canonical(item, active) for item in value]
        if isinstance(value, (set, frozenset)):
            items = [_canonical(item, active) for item in value]
            return sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
        unit = getattr(value, "unit", None)
        raw = getattr(value, "value", None)
        if unit is not None and raw is not None:
            return {"unit": str(unit), "value": _canonical(raw, active)}
        if type(value).__module__.startswith("matplotlib."):
            return {"matplotlib_artist": type(value).__qualname__}
        public = getattr(value, "__dict__", None)
        if public is not None:
            return {
                "type": f"{type(value).__module__}.{type(value).__qualname__}",
                "attributes": {
                    name: _canonical(item, active)
                    for name, item in sorted(public.items())
                    if not name.startswith("_")
                    and name not in {"artist", "artists", "renderer"}
                },
            }
        raise TypeError(
            f"Unsupported scientific evidence type: {type(value).__module__}."
            f"{type(value).__qualname__}"
        )
    finally:
        active.remove(identity)


def _digest(value) -> str:
    encoded = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _frame_evidence(frame):
    exports = frame.generation.exports
    return {
        "request": _digest(frame.resolved.chart_request),
        "orientation": _digest(frame.resolved.orientation),
        "scientific_and_projected": _digest(tuple(
            (
                export.rendering.projection,
                export.rendering.viewport,
                tuple(
                    (
                        layer.semantic_identity,
                        layer.spherical,
                        layer.projected,
                        layer.semantic_artists,
                    )
                    for layer in export.rendering.layers
                ),
            )
            for export in exports
        )),
        "composition_and_clipping": _digest(tuple(
            (export.composition, export.export_options)
            for export in exports
        )),
        "furniture": _digest(tuple(
            (
                export.furniture_rendering,
                export.footer_rendering,
                export.additional_furniture_rendering,
            )
            for export in exports
        )),
    }


def _run(root: Path, output_format, execution, completed, total):
    destination = root / output_format.value / execution.value
    request = default_sequence(destination)
    request = replace(
        request,
        chart=replace(
            request.chart,
            product=replace(
                request.chart.product,
                output_format=output_format,
            ),
        ),
    )
    print(
        f"[{completed}/{total} {round(100 * completed / total)}%] "
        f"starting {output_format.value} {execution.value}",
        flush=True,
    )
    started = perf_counter_ns()
    generation = generate_fixed_sky_rotating_horizon_sequence(
        request, execution=execution
    )
    duration = perf_counter_ns() - started
    completed += 1
    print(
        f"[{completed}/{total} {round(100 * completed / total)}%] "
        f"completed in {duration / 1e9:.3f}s",
        flush=True,
    )
    return generation, duration


def benchmark(destination: Path):
    """Run both modes and return comparison plus raw performance evidence."""
    pdf_renderer = available_pdf_page_renderer()
    root = _outside_repository(destination, name="output")
    root.mkdir(parents=True, exist_ok=True)
    runs = {}
    completed = 0
    total = len(FORMATS) * len(MODES)
    for output_format in FORMATS:
        runs[output_format.value] = {}
        for execution in MODES:
            generation, duration = _run(
                root, output_format, execution, completed, total
            )
            completed += 1
            runs[output_format.value][execution.value] = (
                generation,
                duration,
            )

    png_cold = runs["png"]["cold"][0]
    png_reuse = runs["png"]["reuse_loaded_sphere"][0]
    scientific = []
    products = {name: [] for name in ("png", "svg", "pdf")}
    for cold, reuse in zip(png_cold.frames, png_reuse.frames, strict=True):
        cold_evidence = _frame_evidence(cold)
        reuse_evidence = _frame_evidence(reuse)
        scientific.append({
            "index": cold.resolved.frame.index,
            "cold": cold_evidence,
            "reuse_loaded_sphere": reuse_evidence,
            "equal": cold_evidence == reuse_evidence,
        })
    for output_format in FORMATS:
        cold_generation = runs[output_format.value]["cold"][0]
        reuse_generation = runs[output_format.value]["reuse_loaded_sphere"][0]
        for cold, reuse in zip(
            cold_generation.frames, reuse_generation.frames, strict=True
        ):
            if output_format is OutputFormat.PNG:
                comparison = compare_png_frames(reuse.output, cold.output)
                evidence = {
                    "dimensions": comparison.dimensions,
                    "changed_pixels": comparison.changed_pixels,
                    "max_channel_delta": comparison.max_channel_delta,
                    "mean_absolute_channel_delta": (
                        comparison.mean_absolute_channel_delta
                    ),
                    "equal": comparison.changed_pixels == 0,
                }
            elif output_format is OutputFormat.SVG:
                evidence = {
                    "normalized_graphical_and_semantic_equal": (
                        compare_normalized_svg(reuse.output, cold.output)
                    )
                }
                evidence["equal"] = evidence[
                    "normalized_graphical_and_semantic_equal"
                ]
            else:
                rendered = (
                    root
                    / "rendered_pdf"
                    / f"frame-{cold.resolved.frame.index:04d}"
                )
                cold_png = render_pdf_page_rgba(
                    cold.output,
                    rendered.with_name(rendered.name + "-cold.png"),
                    renderer=pdf_renderer,
                )
                reuse_png = render_pdf_page_rgba(
                    reuse.output,
                    rendered.with_name(rendered.name + "-reuse.png"),
                    renderer=pdf_renderer,
                )
                comparison = compare_png_frames(reuse_png, cold_png)
                evidence = {
                    "renderer": pdf_renderer,
                    "dpi": 150 if pdf_renderer == "pdftoppm" else None,
                    "dimensions": comparison.dimensions,
                    "changed_pixels": comparison.changed_pixels,
                    "max_channel_delta": comparison.max_channel_delta,
                    "mean_absolute_channel_delta": (
                        comparison.mean_absolute_channel_delta
                    ),
                    "equal": comparison.changed_pixels == 0,
                }
            evidence["index"] = cold.resolved.frame.index
            products[output_format.value].append(evidence)

    timings = {
        fmt: {
            mode: data[1]
            for mode, data in values.items()
        }
        for fmt, values in runs.items()
    }
    cold_ns = timings["png"]["cold"]
    reuse_ns = timings["png"]["reuse_loaded_sphere"]
    accepted = (
        all(item["equal"] for item in scientific)
        and all(
            item["equal"]
            for format_evidence in products.values()
            for item in format_evidence
        )
    )
    return {
        "schema": "wenu.fixed-sky-reuse-comparison.v1",
        "environment": {
            "commit": subprocess.run(
                ("git", "rev-parse", "HEAD"), check=True,
                capture_output=True, text=True
            ).stdout.strip(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "acceptance": {
            "threshold": "exact",
            "accepted": accepted,
            "scientific_frames": scientific,
            "products": products,
        },
        "performance": {
            "threshold": None,
            "raw_sequence_duration_ns": timings,
            "png_reuse_over_cold_ratio": reuse_ns / cold_ns,
            "png_speedup_factor": cold_ns / reuse_ns,
        },
        "execution": {
            mode.value: {
                "canonical_sphere_build_count": (
                    runs["png"][mode.value][0].canonical_sphere_build_count
                ),
            }
            for mode in MODES
        },
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
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(report_path)
    if not report["acceptance"]["accepted"]:
        raise SystemExit("fixed-sky reuse equivalence failed")


if __name__ == "__main__":
    main()
