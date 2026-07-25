"""Generate the four demonstrations required by Wenu Milestone 5.

This revision includes the full-sky reference curves, constellation
boundaries, and roadmap keypoints.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np

from wenu import CelestialSphere, Observer, StereographicProjection
from wenu.regional_chart import draw_regional_chart
from wenu.renderers.matplotlib_axes import apply_viewport
from wenu.spherical_frame import SphericalFrame
from wenu.viewport import Viewport


LOCATION = "La Ligua"
OBSERVATION_TIME = "2026-08-15 21:00"


def build_sky(selected=None, *, boundaries=False):
    observer = Observer(
        location=LOCATION,
        time=OBSERVATION_TIME,
    )
    sky = CelestialSphere(observer)
    sky.add_stars(
        catalog="hipparcos",
        magnitude_limit=5.5,
    )
    sky.add_constellations(
        system="western",
        selected=selected,
    )
    if boundaries:
        sky.add_constellation_boundaries(
            boundaries="iau",
            constellations=selected,
        )
    return sky


def constellation_endpoint_indices(sky, abbreviations):
    stars = sky.stars
    geometry = stars.spherical_geometry(
        sky.observer,
        alt_min=-90.0,
    )
    geometry_index = {
        int(hip_id): index
        for index, hip_id in enumerate(geometry.ids)
    }

    hip_ids = set()
    edges = []
    for abbreviation in abbreviations:
        selected_edges = (
            sky.constellations.lines.edges_by_constellation.get(
                abbreviation,
                [],
            )
        )
        edges.extend(selected_edges)
        for hip1, hip2 in selected_edges:
            hip_ids.update((hip1, hip2))

    indices = {
        hip_id: geometry_index[hip_id]
        for hip_id in hip_ids
        if hip_id in geometry_index
    }
    if not indices:
        raise RuntimeError(
            "No Hipparcos endpoints were found for "
            f"{', '.join(abbreviations)}."
        )
    return geometry, indices, edges


def spherical_mean_altaz(sky, abbreviations):
    geometry, indices, _ = constellation_endpoint_indices(
        sky,
        abbreviations,
    )
    selected = np.asarray(list(indices.values()), dtype=int)
    altitude = np.radians(geometry.lat_deg[selected])
    azimuth = np.radians(geometry.lon_deg[selected])

    vectors = np.column_stack(
        (
            np.cos(altitude) * np.cos(azimuth),
            np.cos(altitude) * np.sin(azimuth),
            np.sin(altitude),
        )
    )
    mean = np.mean(vectors, axis=0)
    mean /= np.linalg.norm(mean)

    center_alt_deg = np.degrees(np.arcsin(mean[2]))
    center_az_deg = np.degrees(
        np.arctan2(mean[1], mean[0])
    ) % 360.0
    return float(center_alt_deg), float(center_az_deg)


def crossing_angular_radius(
    sky,
    abbreviations,
    *,
    center_alt_deg,
    center_az_deg,
    projection_radius=2.0,
):
    geometry, indices, edges = constellation_endpoint_indices(
        sky,
        abbreviations,
    )
    projection = StereographicProjection(
        radius=projection_radius,
        flip_ew=True,
        frame=SphericalFrame(
            pole_lon_deg=center_az_deg,
            pole_lat_deg=center_alt_deg,
        ),
    )

    projected_radius_by_hip = {}
    for hip_id, index in indices.items():
        if geometry.lat_deg[index] <= 0.0:
            continue
        x, y = projection.project(
            geometry.lat_deg[index],
            geometry.lon_deg[index],
        )
        projected_radius_by_hip[hip_id] = max(
            abs(float(x)),
            abs(float(y)),
        )

    candidates = []
    for hip1, hip2 in edges:
        if (
            hip1 not in projected_radius_by_hip
            or hip2 not in projected_radius_by_hip
        ):
            continue
        radius1 = projected_radius_by_hip[hip1]
        radius2 = projected_radius_by_hip[hip2]
        difference = abs(radius1 - radius2)
        if difference > 1.0e-8:
            candidates.append(
                (difference, radius1, radius2, hip1, hip2)
            )

    if not candidates:
        raise RuntimeError(
            "No visible constellation edge can be made to cross "
            "a centered regional viewport."
        )

    _, radius1, radius2, hip1, hip2 = max(candidates)
    projected_limit = (radius1 + radius2) / 2.0
    angular_radius_deg = np.degrees(
        2.0 * np.arctan(projected_limit / projection_radius)
    )

    return float(angular_radius_deg), (hip1, hip2)


def configure_axes(ax, title):
    ax.set_facecolor("midnightblue")
    ax.figure.set_facecolor("white")
    ax.set_title(title)
    ax.set_xticks([])
    ax.set_yticks([])


def save_regional(
    output,
    *,
    selected,
    angular_radius_deg,
    boundaries=False,
    title,
):
    sky = build_sky(selected, boundaries=boundaries)
    center_alt_deg, center_az_deg = spherical_mean_altaz(
        sky,
        selected,
    )

    figure, ax = plt.subplots(figsize=(7, 7))
    configure_axes(ax, title)
    result = draw_regional_chart(
        sky,
        ax,
        center_alt_deg=center_alt_deg,
        center_az_deg=center_az_deg,
        angular_radius_deg=angular_radius_deg,
        selected_constellations=selected,
        draw_boundaries=boundaries,
        star_kwargs={"color": "white"},
        save_path=output,
        savefig_kwargs={
            "dpi": 150,
            "bbox_inches": "tight",
        },
    )
    plt.close(figure)
    return result


def generate(output_directory):
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    single = output_directory / "01-crux.png"
    save_regional(
        single,
        selected=["Cru"],
        angular_radius_deg=18.0,
        boundaries=True,
        title="Crux",
    )

    multiple = output_directory / "02-crux-centaurus.png"
    save_regional(
        multiple,
        selected=["Cru", "Cen"],
        angular_radius_deg=35.0,
        title="Crux and Centaurus",
    )

    crossing_sky = build_sky(["Cru"])
    center_alt_deg, center_az_deg = spherical_mean_altaz(
        crossing_sky,
        ["Cru"],
    )
    crossing_radius, crossing_edge = crossing_angular_radius(
        crossing_sky,
        ["Cru"],
        center_alt_deg=center_alt_deg,
        center_az_deg=center_az_deg,
    )
    crossing = output_directory / "03-edge-crossing.png"
    figure, ax = plt.subplots(figsize=(7, 7))
    configure_axes(
        ax,
        f"Crux edge crossing: HIP {crossing_edge[0]}–"
        f"{crossing_edge[1]}",
    )
    draw_regional_chart(
        crossing_sky,
        ax,
        center_alt_deg=center_alt_deg,
        center_az_deg=center_az_deg,
        angular_radius_deg=crossing_radius,
        selected_constellations=["Cru"],
        save_path=crossing,
        savefig_kwargs={
            "dpi": 150,
            "bbox_inches": "tight",
        },
    )
    plt.close(figure)

    full_sky = output_directory / "04-full-sky.png"
    sky = build_sky(boundaries=True)
    points = sky.add_points()
    points.add_equatorial_pole(pole="visible")
    points.add_ecliptic_pole(pole="visible")
    points.add_galactic_center()
    points.add_ecliptic_keypoints()
    projection = StereographicProjection(
        radius=2.0,
        flip_ew=True,
    )
    viewport = Viewport.centered(
        width=4.0,
        height=4.0,
    )
    figure, ax = plt.subplots(figsize=(7, 7))
    configure_axes(ax, "Full-sky planisphere regression")
    apply_viewport(ax, viewport)
    ax.add_patch(
        Circle(
            (0.0, 0.0),
            radius=2.0,
            facecolor="none",
            edgecolor="white",
            linewidth=0.8,
        )
    )
    sky.draw_equatorial(
        ax=ax,
        projection=projection,
        color="deepskyblue",
        linewidth=0.7,
        alpha=0.8,
        zorder=3,
    )
    sky.draw_ecliptic(
        ax=ax,
        projection=projection,
        color="gold",
        linewidth=0.7,
        alpha=0.8,
        zorder=3,
    )
    sky.draw_galactic_plane(
        ax=ax,
        projection=projection,
        color="white",
        linewidth=0.8,
        linestyle="--",
        alpha=0.55,
        zorder=3,
    )
    sky.star_renderer.draw(
        ax=ax,
        projection=projection,
        color="white",
    )
    sky.constellations.draw(
        ax=ax,
        projection=projection,
        draw_lines=True,
        draw_labels=True,
        draw_boundaries=True,
    )
    sky.points.draw(
        ax=ax,
        projection=projection,
    )
    figure.savefig(
        full_sky,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(figure)

    outputs = [single, multiple, crossing, full_sky]
    for output in outputs:
        if not output.exists() or output.stat().st_size == 0:
            raise RuntimeError(
                f"Expected chart was not produced: {output}"
            )
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output_directory",
        nargs="?",
        default="milestone5-output",
    )
    arguments = parser.parse_args()

    for output in generate(arguments.output_directory):
        print(output)


if __name__ == "__main__":
    main()
