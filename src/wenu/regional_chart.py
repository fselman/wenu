"""Temporary adapter for the Milestone 5 regional-chart prototype.

This module deliberately bridges the current direct-drawing layer API to
the regional projection and viewport introduced in Milestone 4. It is not
the final orchestration API and must be removed during the later SkyLayer
migration.
"""

from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from typing import Any

from wenu.projection import StereographicProjection
from wenu.renderers.matplotlib_axes import apply_viewport
from wenu.spherical_frame import SphericalFrame
from wenu.viewport import Viewport


@dataclass(frozen=True)
class RegionalChartResult:
    """Objects produced by one temporary regional-chart rendering."""

    projection: StereographicProjection
    viewport: Viewport
    artists: dict[str, Any]


def draw_regional_chart(
    sky,
    ax,
    *,
    center_alt_deg: float,
    center_az_deg: float,
    angular_radius_deg: float,
    position_angle_deg: float = 0.0,
    projection_radius: float = 2.0,
    flip_ew: bool = True,
    selected_constellations=None,
    draw_labels: bool = True,
    draw_boundaries: bool = False,
    star_kwargs=None,
    label_kwargs=None,
    save_path: str | PathLike[str] | None = None,
    savefig_kwargs=None,
) -> RegionalChartResult:
    """Render a regional chart through the current layer interfaces.

    The center is expressed in the horizontal Alt/Az coordinates currently
    produced by Wenu's existing layers. ``SphericalFrame`` rotates that
    direction to the projection pole before the unchanged stereographic
    formula is evaluated.
    """
    if getattr(sky, "stars", None) is None:
        raise RuntimeError(
            "Regional chart rendering requires sky.stars to be configured."
        )

    frame = SphericalFrame(
        pole_lon_deg=float(center_az_deg),
        pole_lat_deg=float(center_alt_deg),
        position_angle_deg=float(position_angle_deg),
    )
    projection = StereographicProjection(
        radius=projection_radius,
        flip_ew=flip_ew,
        frame=frame,
    )
    viewport = projection.viewport_for_angular_radius(
        angular_radius_deg
    )
    apply_viewport(ax, viewport)

    artists: dict[str, Any] = {}
    artists["stars"] = sky.stars.draw(
        ax=ax,
        projection=projection,
        **({} if star_kwargs is None else dict(star_kwargs)),
    )

    constellations = getattr(sky, "constellations", None)
    if constellations is not None:
        resolved_label_kwargs = (
            {} if label_kwargs is None else dict(label_kwargs)
        )
        if selected_constellations is not None:
            resolved_label_kwargs.setdefault(
                "selected",
                selected_constellations,
            )
        resolved_label_kwargs.setdefault(
            "radial_cut",
            projection.projected_radius(angular_radius_deg),
        )

        artists["constellations"] = constellations.draw(
            ax=ax,
            projection=projection,
            draw_lines=True,
            draw_labels=draw_labels,
            draw_boundaries=draw_boundaries,
            label_kwargs=resolved_label_kwargs,
        )

        for artist in artists["constellations"].get("labels", []):
            artist.set_clip_on(True)

    if save_path is not None:
        ax.figure.savefig(
            save_path,
            **(
                {}
                if savefig_kwargs is None
                else dict(savefig_kwargs)
            ),
        )

    return RegionalChartResult(
        projection=projection,
        viewport=viewport,
        artists=artists,
    )
