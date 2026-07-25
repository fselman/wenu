"""Generate the four regional-chart regression demonstrations canonically."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np

from wenu import CelestialSphere, Observer, StereographicProjection
from wenu.geometry import radec_to_altaz
from wenu.renderers import MatplotlibRenderer, layers
from wenu.rendering import (
    clip_to_latitude,
    magnitude_sizes,
    point_styles,
    radial_label_offset,
)
from wenu.spherical_frame import SphericalFrame
from wenu.viewport import Viewport


LOCATION = "La Ligua"
OBSERVATION_TIME = "2026-08-15 21:00"


def build_sky(selected=None, *, boundaries=False):
    observer = Observer(location=LOCATION, time=OBSERVATION_TIME)
    sky = CelestialSphere(observer)
    sky.add_stars(catalog="hipparcos", magnitude_limit=5.5)
    sky.add_constellations(system="western", selected=selected)
    if boundaries:
        sky.add_constellation_boundaries(
            boundaries="iau",
            constellations=selected,
        )
    return sky


def constellation_endpoint_indices(sky, abbreviations):
    geometry = sky.stars.spherical_geometry(
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
    return (
        float(np.degrees(np.arcsin(mean[2]))),
        float(np.degrees(np.arctan2(mean[1], mean[0])) % 360.0),
    )


def north_up_position_angle_deg(
    observer,
    *,
    center_alt_deg,
    center_az_deg,
):
    north_alt_deg, north_az_deg = radec_to_altaz(
        np.asarray([0.0]),
        np.asarray([90.0]),
        observer.t,
        observer.lat_deg,
        observer.lon_deg,
    )

    def vector(altitude_deg, azimuth_deg):
        altitude = np.radians(float(altitude_deg))
        azimuth = np.radians(float(azimuth_deg))
        return np.asarray(
            [
                np.cos(altitude) * np.cos(azimuth),
                np.cos(altitude) * np.sin(azimuth),
                np.sin(altitude),
            ]
        )

    center = vector(center_alt_deg, center_az_deg)
    zenith = np.asarray([0.0, 0.0, 1.0])
    local_up = zenith - np.dot(zenith, center) * center
    local_up /= np.linalg.norm(local_up)
    local_right = np.cross(center, local_up)
    pole = vector(north_alt_deg[0], north_az_deg[0])
    north = pole - np.dot(pole, center) * center
    norm = np.linalg.norm(north)
    if norm < 1.0e-12:
        return 0.0
    north /= norm
    return float(
        np.degrees(
            np.arctan2(
                np.dot(north, local_right),
                np.dot(north, local_up),
            )
        )
    )


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
    radii = {}
    for hip_id, index in indices.items():
        if geometry.lat_deg[index] <= 0.0:
            continue
        x, y = projection.project(
            geometry.lat_deg[index],
            geometry.lon_deg[index],
        )
        radii[hip_id] = max(abs(float(x)), abs(float(y)))
    candidates = []
    for hip1, hip2 in edges:
        if hip1 in radii and hip2 in radii:
            difference = abs(radii[hip1] - radii[hip2])
            if difference > 1.0e-8:
                candidates.append(
                    (difference, radii[hip1], radii[hip2], hip1, hip2)
                )
    if not candidates:
        raise RuntimeError(
            "No visible constellation edge can cross the viewport."
        )
    _, radius1, radius2, hip1, hip2 = max(candidates)
    projected_limit = (radius1 + radius2) / 2.0
    angular_radius = np.degrees(
        2.0 * np.arctan(projected_limit / projection_radius)
    )
    return float(angular_radius), (hip1, hip2)


def configure_axes(ax, title):
    ax.set_facecolor("midnightblue")
    ax.figure.set_facecolor("white")
    ax.set_title(title)
    ax.set_xticks([])
    ax.set_yticks([])


def _clip(minimum=0.0):
    return lambda spherical, projected: clip_to_latitude(
        spherical,
        projected,
        minimum=minimum,
    )


def canonical_options(sky, *, star_area_scale=1.0):
    options = {
        sky.stars: {
            "geometry": {"alt_min": 0.0},
            "render": lambda spherical, projected: {
                "style": {
                    "s": magnitude_sizes(
                        spherical.metadata["magnitude"]
                    ) * star_area_scale,
                    "c": "white",
                    "linewidths": 0,
                    "zorder": layers.STARS,
                }
            },
        },
        sky.constellation_lines: {
            "prepare": _clip(),
            "render": {
                "style": {
                    "color": "white",
                    "linewidth": 0.4,
                    "alpha": 0.7,
                    "zorder": 2,
                }
            },
        },
        sky.constellation_labels: {
            "prepare": _clip(),
            "render": {
                "style": {"s": 0.0},
                "draw_labels": True,
                "label_style": {
                    "color": "white",
                    "fontsize": 10,
                    "ha": "center",
                    "va": "center",
                    "alpha": 0.85,
                    "zorder": 5,
                },
                "label_offset": radial_label_offset(0.04),
            },
        },
    }
    if sky.constellation_boundaries is not None:
        options[sky.constellation_boundaries] = {
            "prepare": _clip(),
            "render": {
                "style": {
                    "color": "white",
                    "linewidth": 0.3,
                    "alpha": 0.4,
                    "zorder": 1,
                }
            },
        }
    if sky.points is not None:
        options[sky.points] = {
            "prepare": _clip(),
            "render": lambda spherical, projected: {
                "styles": point_styles(
                    spherical.metadata,
                    default_zorder=layers.POINTS,
                ),
                "draw_labels": True,
                "label_style": {
                    "fontsize": 9,
                    "ha": "left",
                    "va": "bottom",
                },
                "label_offset": (0.03, 0.03),
            },
        }
    return options


def save_regional(
    output,
    *,
    selected,
    angular_radius_deg,
    boundaries=False,
    north_up=False,
    title,
):
    sky = build_sky(selected, boundaries=boundaries)
    center_alt_deg, center_az_deg = spherical_mean_altaz(sky, selected)
    position_angle_deg = (
        north_up_position_angle_deg(
            sky.observer,
            center_alt_deg=center_alt_deg,
            center_az_deg=center_az_deg,
        )
        if north_up
        else 0.0
    )
    projection = StereographicProjection(
        radius=2.0,
        flip_ew=True,
        frame=SphericalFrame(
            pole_lon_deg=center_az_deg,
            pole_lat_deg=center_alt_deg,
            position_angle_deg=position_angle_deg,
        ),
    )
    viewport = projection.viewport_for_angular_radius(
        angular_radius_deg
    )
    figure, ax = plt.subplots(figsize=(7, 7))
    configure_axes(ax, title)
    result = sky.draw_chart(
        projection=projection,
        renderer=MatplotlibRenderer(ax),
        viewport=viewport,
        layer_options=canonical_options(sky),
    )
    figure.savefig(output, dpi=150, bbox_inches="tight")
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
        north_up=True,
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
    projection = StereographicProjection(
        radius=2.0,
        flip_ew=True,
        frame=SphericalFrame(
            pole_lon_deg=center_az_deg,
            pole_lat_deg=center_alt_deg,
        ),
    )
    crossing_sky.draw_chart(
        projection=projection,
        renderer=MatplotlibRenderer(ax),
        viewport=projection.viewport_for_angular_radius(
            crossing_radius
        ),
        layer_options=canonical_options(crossing_sky),
    )
    figure.savefig(crossing, dpi=150, bbox_inches="tight")
    plt.close(figure)

    full_sky = output_directory / "04-full-sky.png"
    sky = build_sky(boundaries=True)
    points = sky.add_points()
    points.add_equatorial_pole(pole="visible")
    points.add_ecliptic_pole(pole="visible")
    points.add_galactic_center()
    points.add_ecliptic_keypoints()
    equatorial = sky.add_equatorial_grid(include_equator=True)
    ecliptic = sky.add_ecliptic_grid(include_ecliptic=True)
    galactic = sky.add_galactic_grid(include_plane=True)
    projection = StereographicProjection(radius=2.0, flip_ew=True)
    viewport = Viewport.centered(width=4.0, height=4.0)
    figure, ax = plt.subplots(figsize=(7, 7))
    configure_axes(ax, "Full-sky planisphere regression")
    ax.add_patch(
        Circle(
            (0.0, 0.0),
            radius=2.0,
            facecolor="none",
            edgecolor="white",
            linewidth=0.8,
        )
    )
    options = canonical_options(sky, star_area_scale=0.25)
    options[equatorial] = {
        "prepare": _clip(),
        "render": {
            "style": {
                "color": "deepskyblue",
                "linewidth": 0.7,
                "alpha": 0.8,
                "zorder": 3,
            }
        },
    }
    options[ecliptic] = {
        "prepare": _clip(),
        "render": {
            "style": {
                "color": "gold",
                "linewidth": 0.7,
                "alpha": 0.8,
                "zorder": 3,
            }
        },
    }
    options[galactic] = {
        "prepare": _clip(),
        "render": {
            "style": {
                "color": "white",
                "linewidth": 0.8,
                "linestyle": "--",
                "alpha": 0.55,
                "zorder": 3,
            }
        },
    }
    sky.draw_chart(
        projection=projection,
        renderer=MatplotlibRenderer(ax),
        viewport=viewport,
        layer_options=options,
    )
    figure.savefig(full_sky, dpi=300, bbox_inches="tight")
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
