"""Production configuration and orchestration for regional sky charts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from wenu.coordinates import radec_to_altaz
from wenu.projections.stereographic import StereographicProjection
from wenu.geometry.frame import SphericalFrame
from wenu.geometry.viewport import Viewport


def _spherical_mean(lon_deg, lat_deg):
    lon = np.radians(np.asarray(lon_deg, dtype=float))
    lat = np.radians(np.asarray(lat_deg, dtype=float))
    vectors = np.column_stack(
        (
            np.cos(lat) * np.cos(lon),
            np.cos(lat) * np.sin(lon),
            np.sin(lat),
        )
    )
    mean = np.mean(vectors, axis=0)
    norm = np.linalg.norm(mean)
    if norm <= 1.0e-15:
        raise ValueError("The selected directions have no spherical mean.")
    mean /= norm
    return (
        float(np.degrees(np.arctan2(mean[1], mean[0])) % 360.0),
        float(np.degrees(np.arcsin(mean[2]))),
    )


def celestial_north_position_angle(
    observer,
    *,
    center_alt_deg,
    center_az_deg,
):
    """Return the rotation placing celestial north at chart top."""
    north_alt, north_az = radec_to_altaz(
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
            (
                np.cos(altitude) * np.cos(azimuth),
                np.cos(altitude) * np.sin(azimuth),
                np.sin(altitude),
            )
        )

    center = vector(center_alt_deg, center_az_deg)
    zenith = np.asarray((0.0, 0.0, 1.0))
    chart_up = zenith - np.dot(zenith, center) * center
    norm = np.linalg.norm(chart_up)
    if norm <= 1.0e-15:
        chart_up = np.asarray((1.0, 0.0, 0.0))
    else:
        chart_up /= norm
    chart_right = np.cross(center, chart_up)

    pole = vector(north_alt[0], north_az[0])
    north = pole - np.dot(pole, center) * center
    norm = np.linalg.norm(north)
    if norm <= 1.0e-15:
        return 0.0
    north /= norm
    return float(
        np.degrees(
            np.arctan2(
                np.dot(north, chart_right),
                np.dot(north, chart_up),
            )
        )
    )


@dataclass(frozen=True)
class ExportOptions:
    """Reproducible Matplotlib export settings."""

    dpi: int = 300
    bbox_inches: str | None = "tight"
    transparent: bool = False
    facecolor: Any | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def save(self, figure, path):
        """Save a Matplotlib figure using these fixed settings."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        kwargs = {
            "dpi": int(self.dpi),
            "bbox_inches": self.bbox_inches,
            "transparent": bool(self.transparent),
            "metadata": dict(self.metadata),
        }
        if self.facecolor is not None:
            kwargs["facecolor"] = self.facecolor
        figure.savefig(path, **kwargs)
        return path


@dataclass(frozen=True)
class RegionalChart:
    """A reproducible regional stereographic chart specification."""

    center_alt_deg: float
    center_az_deg: float
    field_width_deg: float
    field_height_deg: float
    position_angle_deg: float = 0.0
    projection_radius: float = 2.0
    flip_ew: bool = True
    crop_x: float = 0.0
    crop_y: float = 0.0
    label_selection: tuple[str, ...] | None = None
    outside_mask_constellations: tuple[str, ...] | None = None

    def __post_init__(self):
        values = np.asarray(
            (
                self.center_alt_deg,
                self.center_az_deg,
                self.field_width_deg,
                self.field_height_deg,
                self.position_angle_deg,
                self.projection_radius,
                self.crop_x,
                self.crop_y,
            ),
            dtype=float,
        )
        if not np.all(np.isfinite(values)):
            raise ValueError("Regional chart values must be finite.")
        if not -90.0 <= self.center_alt_deg <= 90.0:
            raise ValueError(
                "center_alt_deg must be between -90 and 90."
            )
        for name, value in (
            ("field_width_deg", self.field_width_deg),
            ("field_height_deg", self.field_height_deg),
        ):
            if value <= 0.0 or value >= 360.0:
                raise ValueError(
                    f"{name} must be between 0 and 360 degrees."
                )
        if self.projection_radius <= 0.0:
            raise ValueError("projection_radius must be positive.")
        if self.outside_mask_constellations is not None:
            names = tuple(
                str(name).strip()
                for name in self.outside_mask_constellations
            )
            if not names or any(not name for name in names):
                raise ValueError(
                    "outside_mask_constellations must contain names."
                )
            object.__setattr__(
                self,
                "outside_mask_constellations",
                names,
            )

    @classmethod
    def from_angular_radius(
        cls,
        *,
        center_alt_deg,
        center_az_deg,
        angular_radius_deg,
        aspect_ratio=1.0,
        **kwargs,
    ):
        """Create a chart from vertical angular radius and aspect ratio."""
        aspect_ratio = float(aspect_ratio)
        if not np.isfinite(aspect_ratio) or aspect_ratio <= 0.0:
            raise ValueError("aspect_ratio must be positive and finite.")
        diameter = 2.0 * float(angular_radius_deg)
        return cls(
            center_alt_deg=float(center_alt_deg),
            center_az_deg=float(center_az_deg),
            field_width_deg=diameter * aspect_ratio,
            field_height_deg=diameter,
            **kwargs,
        )

    @classmethod
    def from_coordinate(
        cls,
        observer,
        coordinate,
        *,
        field_width_deg,
        field_height_deg,
        north_up=False,
        position_angle_deg=0.0,
        **kwargs,
    ):
        """Create a chart centered on any Astropy sky coordinate."""
        horizontal = coordinate.transform_to(observer.altaz_frame)
        altitude = float(np.asarray(horizontal.alt.deg))
        azimuth = float(np.asarray(horizontal.az.deg))
        position_angle = cls._position_angle(
            observer,
            altitude,
            azimuth,
            north_up=north_up,
            position_angle_deg=position_angle_deg,
        )
        return cls(
            center_alt_deg=altitude,
            center_az_deg=azimuth,
            field_width_deg=field_width_deg,
            field_height_deg=field_height_deg,
            position_angle_deg=position_angle,
            **kwargs,
        )

    @classmethod
    def from_constellations(
        cls,
        sky,
        constellations,
        *,
        angular_radius_deg,
        aspect_ratio=1.0,
        north_up=False,
        position_angle_deg=0.0,
        label_selection=None,
        **kwargs,
    ):
        """Center a chart on unique endpoints of selected line figures."""
        names = tuple(constellations)
        if not names:
            raise ValueError("Select at least one constellation.")
        if sky.stars is None or sky.constellation_lines is None:
            raise RuntimeError(
                "Add stars and constellations before deriving a center."
            )
        stars = sky.stars.spherical_geometry(
            sky.observer,
            alt_min=-90.0,
        )
        index = {
            int(hip_id): position
            for position, hip_id in enumerate(stars.ids)
        }
        hip_ids = set()
        for name in names:
            for first, second in (
                sky.constellation_lines.edges_by_constellation.get(
                    name,
                    (),
                )
            ):
                hip_ids.update((first, second))
        selected = [index[hip_id] for hip_id in hip_ids if hip_id in index]
        if not selected:
            raise ValueError(
                "No catalogue endpoints were found for "
                f"{', '.join(names)}."
            )
        azimuth, altitude = _spherical_mean(
            stars.lon_deg[selected],
            stars.lat_deg[selected],
        )
        position_angle = cls._position_angle(
            sky.observer,
            altitude,
            azimuth,
            north_up=north_up,
            position_angle_deg=position_angle_deg,
        )
        return cls.from_angular_radius(
            center_alt_deg=altitude,
            center_az_deg=azimuth,
            angular_radius_deg=angular_radius_deg,
            aspect_ratio=aspect_ratio,
            position_angle_deg=position_angle,
            label_selection=(
                names if label_selection is None else tuple(label_selection)
            ),
            **kwargs,
        )

    @staticmethod
    def _position_angle(
        observer,
        altitude,
        azimuth,
        *,
        north_up,
        position_angle_deg,
    ):
        if north_up and float(position_angle_deg) != 0.0:
            raise ValueError(
                "Use north_up or position_angle_deg, not both."
            )
        if north_up:
            return celestial_north_position_angle(
                observer,
                center_alt_deg=altitude,
                center_az_deg=azimuth,
            )
        return float(position_angle_deg)

    @property
    def chart_context(self):
        """Return output-neutral geometry for composition."""
        from wenu.charts.context import ChartContext

        return ChartContext(
            viewport=self.viewport,
            angular_width_deg=self.field_width_deg,
            angular_height_deg=self.field_height_deg,
            tangent_longitude_deg=self.center_az_deg,
            tangent_latitude_deg=self.center_alt_deg,
        )

    def figure_size(self, width_inches=7.0):
        """Return a figure size matching the projected viewport."""
        width_inches = float(width_inches)
        if not np.isfinite(width_inches) or width_inches <= 0.0:
            raise ValueError(
                "width_inches must be positive and finite."
            )
        return (
            width_inches,
            width_inches / self.viewport.aspect_ratio,
        )

    @property
    def projection(self):
        """Return the configured coordinate-neutral projection."""
        return StereographicProjection(
            radius=self.projection_radius,
            flip_ew=self.flip_ew,
            frame=SphericalFrame(
                pole_lon_deg=self.center_az_deg,
                pole_lat_deg=self.center_alt_deg,
                position_angle_deg=self.position_angle_deg,
            ),
        )

    @property
    def viewport(self):
        """Return the rectangular projected crop."""
        projection = self.projection
        half_width = projection.projected_radius(
            self.field_width_deg / 2.0
        )
        half_height = projection.projected_radius(
            self.field_height_deg / 2.0
        )
        return Viewport.centered(
            width=2.0 * half_width,
            height=2.0 * half_height,
            center_x=self.crop_x,
            center_y=self.crop_y,
        )

    def render(
        self,
        sky,
        renderer,
        *,
        style=None,
        layer_options=None,
    ):
        """Render this specification through ``CelestialSphere``."""
        options = (
            {} if style is None else style.layer_options(sky)
        )
        if self.label_selection is not None:
            label_options = dict(
                options.get(sky.constellation_labels, {})
            )
            geometry_options = dict(
                label_options.get("geometry", {})
            )
            geometry_options["selected"] = self.label_selection
            label_options["geometry"] = geometry_options
            options[sky.constellation_labels] = label_options
        if layer_options is not None:
            options.update(layer_options)
        projection = self.projection
        viewport = self.viewport
        result = sky.draw_chart(
            projection=projection,
            renderer=renderer,
            viewport=viewport,
            layer_options=options,
        )
        if self.outside_mask_constellations is not None:
            from wenu.charts._masking import (
                draw_constellation_outside_mask,
            )

            mask_style = (
                {
                    "facecolor": "black",
                    "edgecolor": "none",
                    "alpha": 0.35,
                    "zorder": 20.0,
                }
                if style is None
                else style.outside_mask_style()
            )
            draw_constellation_outside_mask(
                sky=sky,
                projection=projection,
                renderer=renderer,
                viewport=viewport,
                constellations=self.outside_mask_constellations,
                style=mask_style,
            )
        return result

    def export(
        self,
        sky,
        renderer,
        path,
        *,
        style=None,
        layer_options=None,
        export_options=None,
    ):
        """Render and reproducibly save a regional chart."""
        result = self.render(
            sky,
            renderer,
            style=style,
            layer_options=layer_options,
        )
        options = (
            ExportOptions()
            if export_options is None
            else export_options
        )
        output = options.save(renderer.ax.figure, path)
        return result, output
