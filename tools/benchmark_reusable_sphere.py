"""Benchmark one reusable Wenu sphere without enforcing timing thresholds."""

from __future__ import annotations

import argparse
import cProfile
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import pstats
from time import perf_counter

from wenu import (
    Observer,
    draw_chart_view,
    generate_celestial_sphere,
    get_chart_view,
)


VIEW_REQUESTS = (
    ("planisphere", {"family": "planisphere"}),
    ("regional-single", {"family": "regional", "constellations": ("Cru",)}),
    ("regional-group", {"family": "regional", "group": "galactic-center"}),
    (
        "circumpolar",
        {
            "family": "circumpolar",
            "pole": "south",
            "limiting_declination_deg": -69.75,
        },
    ),
    (
        "binocular",
        {
            "family": "binocular",
            "target": "omega-centauri",
            "field_diameter_deg": 6.5,
        },
    ),
    ("all-sky", {"family": "all_sky"}),
)

PROFILE_GROUPS = {
    "selection": ("wenu/charts/spatial_selection.py",),
    "projection": ("wenu/projections/",),
    "preparation": ("wenu/rendering/preparation.py",),
    "rendering": (
        "wenu/rendering/matplotlib.py",
        "wenu/rendering/_matplotlib_primitives.py",
    ),
    "export": (
        "wenu/charts/export_workflow.py",
        "matplotlib/backends/backend_agg.py",
    ),
}


@dataclass(frozen=True)
class TimedOperation:
    """One measured public operation."""

    name: str
    seconds: float


def _timed(name, operation):
    started = perf_counter()
    value = operation()
    return value, TimedOperation(name, perf_counter() - started)


def _profile_totals(profile):
    stats = pstats.Stats(profile)
    totals = {}
    for group, fragments in PROFILE_GROUPS.items():
        totals[group] = sum(
            value[3]
            for (filename, _line, _name), value in stats.stats.items()
            if any(fragment in filename for fragment in fragments)
        )
    return totals


def _cache_counts(sky):
    values = {}
    layers = (
        "stars",
        "nonstellar",
        "galaxies",
        "open_clusters",
        "globular_clusters",
        "supernova_remnants",
        "planetary_nebulae",
        "milky_way_isophotes",
        "constellation_boundaries",
    )
    for name in layers:
        layer = getattr(sky, name, None)
        if layer is not None:
            caches = {
                key: len(value)
                for key, value in vars(layer).items()
                if key.endswith("_cache") and isinstance(value, dict)
            }
            if caches:
                values[name] = caches
    for cloud, layer in sky.magellanic_cloud_isophotes.items():
        caches = {
            key: len(value)
            for key, value in vars(layer).items()
            if key.endswith("_cache") and isinstance(value, dict)
        }
        if caches:
            values[f"magellanic_clouds.{cloud}"] = caches
    return values


def benchmark(destination):
    """Run and return the reusable-sphere benchmark report."""
    destination.mkdir(parents=True, exist_ok=True)
    operations = []
    sky, timing = _timed("catalogue_loading", generate_celestial_sphere)
    operations.append(timing)
    observers = (
        Observer(location="La Ligua", time="2026-08-15 21:00"),
        Observer(location="La Ligua", time="2026-08-16 00:00"),
        Observer(location="Papudo", time="2026-08-15 21:00"),
    )
    profile = cProfile.Profile()
    try:
        profile.enable()
        views = []
        for observer_index, observer in enumerate(observers):
            for name, arguments in VIEW_REQUESTS:
                view, timing = _timed(
                    f"view.{observer_index}.{name}",
                    lambda arguments=arguments, observer=observer: (
                        get_chart_view(sky, observer, **arguments)
                    ),
                )
                views.append((observer_index, name, view))
                operations.append(timing)
        for observer_index, name, view in views:
            output = destination / f"{observer_index}-{name}.png"
            _result, timing = _timed(
                f"draw_export.{observer_index}.{name}",
                lambda view=view, output=output: draw_chart_view(
                    view, output, style="atlas", mode="print"
                ),
            )
            operations.append(timing)
        profile.disable()
        before_repeat = _cache_counts(sky)
        sky.stars.observed_altaz(observers[0])
        after_repeat = _cache_counts(sky)
    finally:
        profile.disable()
        for observer in observers:
            observer.close()

    return {
        "canonical_sphere_build_count": 1,
        "sphere_observer_independent": sky.observer is None,
        "canonical_layer_count": len(sky.layers),
        "observer_count": len(observers),
        "view_count": len(VIEW_REQUESTS) * len(observers),
        "operations": [asdict(value) for value in operations],
        "profile_cumulative_seconds": _profile_totals(profile),
        "cache_entries_before_compatible_repeat": before_repeat,
        "cache_entries_after_compatible_repeat": after_repeat,
        "compatible_repeat_added_cache_entry": before_repeat != after_repeat,
    }


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument(
        "--output",
        type=Path,
        default=Path("output/benchmark-reusable-sphere"),
    )
    value.add_argument(
        "--report",
        type=Path,
        default=Path("output/benchmark-reusable-sphere.json"),
    )
    return value


def main():
    arguments = parser().parse_args()
    report = benchmark(arguments.output)
    arguments.report.parent.mkdir(parents=True, exist_ok=True)
    arguments.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(arguments.report)


if __name__ == "__main__":
    main()
