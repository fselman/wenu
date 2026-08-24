"""Render editable print and presentation cartoon charts."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    CartoonDetailPolicy,
    DetailOverrides,
    MatplotlibRenderer,
    Observer,
    RegionalChart,
    cartoon_chart_style,
    compose_chart,
)


CONSTELLATIONS = ("Cyg", "Lyr", "Vul", "Sge", "Aql")
DEFAULT_OUTPUT = Path("output/cartoon-modes-explicit-labels")

# Edit these nine-position switches directly.
# Accepted values: ul, u, ur, cl, c, cr, ll, lc, lr.
CONSTELLATION_LABEL_POSITIONS = {
    "Cyg": "cl",
    "Lyr": "ur",
    "Vul": "ll",
    "Sge": "lr",
    "Aql": "ur",
}

# Optional fine corrections added after the position switch.
# Values are projected-chart (dx, dy) displacements.
CONSTELLATION_LABEL_OFFSETS = {
    "Cyg": (0.00, 0.00),
    "Lyr": (-0.03, 0.01),
    "Vul": (0.00, 0.00),
    "Sge": (0.00, 0.00),
    "Aql": (0.00, 0.00),
}

LABEL_CLEARANCE = (0.32, 0.36)
STAR_MAGNITUDE_LIMIT = 3.0

CARTOON_LAYERS = frozenset(
    {
        "stars",
        "constellation_lines",
        "constellation_labels",
    }
)


def build_scene():
    """Return the sky and regional chart shared by both output modes."""
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )
    sky = CelestialSphere(observer)
    sky.add_stars(
        catalog="hipparcos",
        magnitude_limit=6.5,
    )
    sky.add_constellations(
        system="western",
        selected=CONSTELLATIONS,
    )
    sky.add_milky_way_isophotes()
    chart = RegionalChart.from_constellations(
        sky,
        CONSTELLATIONS,
        angular_radius_deg=46.0,
        aspect_ratio=1.38,
        orientation="celestial-north-up",
        crop_y=0.0,
        label_selection=CONSTELLATIONS,
    )
    return sky, chart


def content_layers(mode):
    """Enable the Milky Way only in presentation mode."""
    if mode == "presentation":
        return CARTOON_LAYERS | {"milky_way"}
    return CARTOON_LAYERS


def render_mode(
    sky,
    chart,
    mode,
    output_directory=DEFAULT_OUTPUT,
):
    """Render one mode with explicit, editable label placement."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    style = cartoon_chart_style(
        mode,
        constellation_label_positions=(
            CONSTELLATION_LABEL_POSITIONS
        ),
        constellation_label_offsets=CONSTELLATION_LABEL_OFFSETS,
        constellation_label_clearance=LABEL_CLEARANCE,
    )
    composition = compose_chart(
        chart,
        style=style,
        mode=mode,
        detail=CartoonDetailPolicy(),
        detail_overrides=DetailOverrides(
            star_magnitude_limit=STAR_MAGNITUDE_LIMIT,
            enabled_layers=content_layers(mode),
        ),
    )
    resolved = composition.mode

    figure, ax = plt.subplots(
        figsize=(resolved.width_inches, resolved.height_inches),
    )
    composition.style.configure_axes(
        ax,
        title=f"The Summer Triangle — cartoon {mode} mode",
    )
    destination = output_directory / f"cartoon-{mode}.png"
    chart.export(
        sky,
        MatplotlibRenderer(ax),
        destination,
        composition=composition,
    )
    plt.close(figure)
    return destination, composition


def generate(output_directory=DEFAULT_OUTPUT):
    """Create matching print and presentation charts."""
    sky, chart = build_scene()
    products = {}
    for mode in ("print", "presentation"):
        path, composition = render_mode(
            sky,
            chart,
            mode,
            output_directory,
        )
        products[mode] = (path, composition)
    return products


def main():
    products = generate()
    for mode, (path, _) in products.items():
        print(f"{mode}: {path}")


if __name__ == "__main__":
    main()
