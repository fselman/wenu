"""Render the Milestone 48E.2 north/south physical-style checkpoint."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import astropy.units as u
from astropy.coordinates import BarycentricTrueEcliptic, SkyCoord

from wenu import (
    ChartFurnitureOptions,
    DetailOverrides,
    ExportOptions,
    FooterOptions,
    MatplotlibRenderer,
    Observer,
    PoleAnnotations,
    PolarCalendarFurnitureRequest,
    PolarPlanispherePairRequest,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
    compose_chart,
    generate_celestial_sphere,
)
from wenu.configuration import load_packaged_defaults


MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def _draw_calendar(ax, face, scale, *, color, label_color, typography):
    for tick in face.ticks:
        x = (tick.inner[0] * scale, tick.outer[0] * scale)
        y = (tick.inner[1] * scale, tick.outer[1] * scale)
        ax.plot(
            x,
            y,
            color=color,
            linewidth=(
                0.55
                if tick.month_boundary
                else 0.36 if tick.labeled_day else 0.18
            ),
            alpha=1.0,
            solid_capstyle="butt",
            zorder=30,
        )
    for label in face.day_labels:
        ax.text(
            label.position[0] * scale,
            label.position[1] * scale,
            label.text,
            color=label_color,
            fontsize=typography.day_label_fontsize,
            fontweight=typography.day_label_fontweight,
            ha="center",
            va="baseline",
            rotation=label.rotation_deg,
            rotation_mode="anchor",
            zorder=31,
        )
    for label in face.month_labels:
        ax.text(
            label.position[0] * scale,
            label.position[1] * scale,
            MONTH_NAMES[label.month - 1],
            color=label_color,
            fontsize=typography.month_label_fontsize,
            fontweight=typography.month_label_fontweight,
            ha="center",
            va="baseline",
            rotation=label.rotation_deg,
            rotation_mode="anchor",
            zorder=31,
        )


def _projected_anchor(chart, observer, *, frame, angle_deg):
    if frame == "equatorial":
        ra_deg, dec_deg = float(angle_deg), 0.0
    else:
        point = SkyCoord(
            lon=float(angle_deg) * u.deg,
            lat=0.0 * u.deg,
            frame=BarycentricTrueEcliptic(equinox=observer.t_astropy),
        ).transform_to(observer.icrs_frame)
        ra_deg, dec_deg = float(point.ra.deg), float(point.dec.deg)
    x, y = chart.projection.project_spherical(
        np.asarray((ra_deg,)), np.asarray((dec_deg,))
    )
    return float(x[0]), float(y[0])


def _polar_reference_annotations(chart, observer):
    values = load_packaged_defaults()["grids_references"][
        "polar_planisphere_label_anchors"
    ][chart.pole]
    labeled = lambda text, anchor: ReferencePlaneAnnotation(
        state="labeled", label=text, anchor=anchor
    )
    return ReferenceAnnotations(
        celestial_equator=labeled(
            "Celestial equator",
            _projected_anchor(
                chart, observer, frame="equatorial",
                angle_deg=values["equatorial_right_ascension_deg"],
            ),
        ),
        ecliptic=labeled(
            "Ecliptic",
            _projected_anchor(
                chart, observer, frame="ecliptic",
                angle_deg=values["ecliptic_longitude_deg"],
            ),
        ),
        galactic_plane=ReferencePlaneAnnotation(
            state="labeled", label="Galactic plane"
        ),
    )


def _render_face(chart, furniture, sky, observer, destination):
    composition = compose_chart(
        chart,
        style="atlas",
        mode="print",
        detail_overrides=DetailOverrides(
            enabled_layer_additions=frozenset({"equatorial_grid"}),
        ),
        furniture=ChartFurnitureOptions(
            references=_polar_reference_annotations(chart, observer),
            poles=PoleAnnotations(
                celestial="both",
                ecliptic="both",
                galactic="both",
                labels=True,
            ),
            footer=FooterOptions(
                application=True,
                application_name="Wenu",
                include_version=True,
            ),
        ),
    )
    figure, ax = plt.subplots(figsize=(8.0, 8.0))
    composition.style.configure_axes(ax)
    renderer = MatplotlibRenderer(ax)
    application = composition.layer_options(sky)
    chart.render(
        sky,
        renderer,
        observer=observer,
        style=composition.style,
        layer_options=application.layer_options,
    )
    from wenu.charts.reference_furniture import (
        draw_celestial_reference_furniture,
    )

    draw_celestial_reference_furniture(
        chart,
        sky,
        renderer,
        composition,
        observer=observer,
    )
    unit_per_mm = chart.boundary_radius / furniture.star_disk_radius_mm
    _draw_calendar(
        ax,
        furniture,
        unit_per_mm,
        color=composition.style.canvas.foreground_color,
        label_color=composition.style.canvas.foreground_color,
        typography=composition.style.calendar,
    )
    outer = furniture.outer_radius_mm * unit_per_mm
    margin = outer * 1.035
    ax.set_xlim(-margin, margin)
    ax.set_ylim(-margin, margin)
    ax.set_aspect("equal")
    ax.set_axis_off()
    figure.subplots_adjust(0.0, 0.0, 1.0, 1.0)
    from wenu.charts.footer_furniture import draw_chart_footer

    draw_chart_footer(
        renderer,
        composition.furniture.footer,
        composition.mode,
        color=composition.style.canvas.foreground_color,
    )
    output = ExportOptions(
        dpi=180,
        bbox_inches="tight",
        facecolor=composition.style.canvas.sky_color,
        padding=0.02,
    ).save(figure, destination)
    plt.close(figure)
    return output


def render_preview(destination, *, projection_name):
    """Render two deterministic diagnostic PNGs and one manifest."""
    destination.mkdir(parents=True, exist_ok=True)
    pair = PolarPlanispherePairRequest(
        projection_name=projection_name,
        calendar_radius_mm=78.0,
    ).resolve()
    calendar = PolarCalendarFurnitureRequest().resolve(pair)
    sky = generate_celestial_sphere()
    observer = Observer(location="La Ligua", time="2026-08-15 21:00")
    try:
        outputs = tuple(
            _render_face(
                chart,
                furniture,
                sky,
                observer,
                destination / f"polar-planisphere-{name}.png",
            )
            for name, chart, furniture in (
                ("south", pair.south, calendar.south),
                ("north", pair.north, calendar.north),
            )
        )
    finally:
        observer.close()
    manifest = destination / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "projection": projection_name,
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
    return outputs, manifest


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument(
        "--output",
        type=Path,
        default=Path("output/48e2-polar-preview"),
    )
    value.add_argument(
        "--projection",
        choices=("polar_azimuthal_equidistant", "stereographic"),
        default="polar_azimuthal_equidistant",
    )
    return value


def main(argv=None):
    arguments = parser().parse_args(argv)
    outputs, manifest = render_preview(
        arguments.output,
        projection_name=arguments.projection,
    )
    print(*(str(path) for path in (*outputs, manifest)), sep="\n")


if __name__ == "__main__":
    main()
