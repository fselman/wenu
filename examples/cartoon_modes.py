"""Render one canonical cartoon chart in print and presentation modes."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    MatplotlibRenderer,
    Observer,
    RegionalChart,
    compose_cartoon_chart,
    DetailOverrides,
)


CONSTELLATIONS = ("Cyg", "Lyr", "Vul", "Sge", "Aql")
DEFAULT_OUTPUT = Path("output/cartoon-modes")


def build_scene():
    """Return the shared sky and regional chart used by both modes."""
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
    chart = RegionalChart.from_constellations(
        sky,
        CONSTELLATIONS,
        angular_radius_deg=46.0,
        aspect_ratio=1.38,
        north_up=True,
        crop_y=0.0,
        label_selection=CONSTELLATIONS,
    )
    return sky, chart


def render_mode(sky, chart, mode, output_directory=DEFAULT_OUTPUT):
    """Render the shared scene using one resolved cartoon output mode."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    composition = compose_cartoon_chart(
        chart,
        mode=mode,
        detail_overrides=DetailOverrides(
            star_magnitude_limit=3.0,
        ),
        constellation_label_offsets={
            "Cyg": (-0.40, -0.02),
            "Lyr": (0.34, 0.22),
            "Vul": (-0.48, -0.16),
            "Sge": (0.38, -0.30),
        },
    )
    application = composition.layer_options(sky)
    style = composition.style
    resolved = composition.mode

    figure, ax = plt.subplots(
        figsize=(resolved.width_inches, resolved.height_inches),
    )
    style.configure_axes(
        ax,
        title=f"The Summer Triangle — cartoon {mode} mode",
    )
    destination = output_directory / f"cartoon-{mode}.png"
    chart.export(
        sky,
        MatplotlibRenderer(ax),
        destination,
        style=style,
        layer_options=application.layer_options,
    )
    figure.savefig(
        destination,
        dpi=resolved.dpi,
        bbox_inches="tight",
        transparent=resolved.transparent,
    )
    plt.close(figure)
    return destination, composition


def generate(output_directory=DEFAULT_OUTPUT):
    """Create matching print and presentation cartoon charts."""
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
