"""Reusable projected boundaries and coordinate-label anchors."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from wenu.geometry.projected import ProjectedCurve
from wenu.geometry.viewport import Viewport
from wenu.rendering.label_placement import CurveLabelPlacement


def _above_line(x, y, *, horizontal_alignment=None, normal_offset_em=0.65):
    return CurveLabelPlacement(
        float(x),
        float(y),
        rotation_deg=0.0,
        normal_offset_em=normal_offset_em,
        horizontal_alignment=horizontal_alignment,
    )


def resolved_circular_boundary_style(style):
    """Return a style-owned circular boundary appearance."""
    if style is None:
        return None
    factory = getattr(style, "chart_boundary_style", None)
    if callable(factory):
        return {
            "facecolor": "none",
            "zorder": 8.0,
            **factory(),
        }
    converter = getattr(style, "as_publication_style", None)
    resolved = converter() if callable(converter) else style
    return {
        "facecolor": "none",
        "edgecolor": resolved.boundary_color,
        "linewidth": resolved.boundary_linewidth,
        "linestyle": resolved.boundary_linestyle,
        "alpha": resolved.boundary_alpha,
        "zorder": 8.0,
    }


def circular_boundary(radius, *, samples=721, name="chart_boundary"):
    """Return a closed projected circle centered on the origin."""
    radius = float(radius)
    samples = int(samples)
    if not np.isfinite(radius) or radius <= 0.0:
        raise ValueError("radius must be positive and finite.")
    if samples < 9:
        raise ValueError("samples must be at least 9.")
    angle = np.linspace(0.0, 2.0 * np.pi, samples)
    return ProjectedCurve(
        radius * np.cos(angle),
        radius * np.sin(angle),
        closed=True,
        name=name,
    )


def viewport_from_boundary(boundary, *, padding=0.0):
    """Fit a square viewport around a finite projected boundary."""
    finite = boundary.finite
    if not np.any(finite):
        raise ValueError("boundary has no finite points.")
    x = np.asarray(boundary.x[finite], dtype=float)
    y = np.asarray(boundary.y[finite], dtype=float)
    radius = max(
        float(np.max(np.abs(x))),
        float(np.max(np.abs(y))),
    )
    radius *= 1.0 + float(padding)
    return Viewport.centered(width=2.0 * radius, height=2.0 * radius)


@dataclass(frozen=True)
class CircularLabelAnchor:
    """Place curve labels close to a circular chart boundary."""

    boundary: ProjectedCurve
    inset: float = 0.965

    def __post_init__(self):
        if not 0.0 < float(self.inset) <= 1.0:
            raise ValueError("inset must be in the interval (0, 1].")

    @property
    def radius(self):
        finite = self.boundary.finite
        if not np.any(finite):
            raise ValueError("boundary has no finite points.")
        return float(
            np.nanmedian(
                np.hypot(
                    self.boundary.x[finite],
                    self.boundary.y[finite],
                )
            )
        )

    def __call__(self, curve, ax=None):
        """Return the curve point nearest the inset boundary circle."""
        finite = curve.finite
        if not np.any(finite):
            return None
        x = np.asarray(curve.x[finite], dtype=float)
        y = np.asarray(curve.y[finite], dtype=float)
        target = self.radius * float(self.inset)
        index = int(np.argmin(np.abs(np.hypot(x, y) - target)))
        return float(x[index]), float(y[index])


@dataclass(frozen=True)
class CircularGridLabelAnchor:
    """Place coordinate labels just inside a circular chart boundary."""

    boundary: ProjectedCurve
    inset: float = 0.965
    declination_at_left: bool = False

    def __post_init__(self):
        if not 0.0 < float(self.inset) <= 1.0:
            raise ValueError("inset must be in the interval (0, 1].")

    @property
    def radius(self):
        finite = self.boundary.finite
        if not np.any(finite):
            raise ValueError("boundary has no finite points.")
        return float(
            np.nanmedian(
                np.hypot(
                    self.boundary.x[finite],
                    self.boundary.y[finite],
                )
            )
        )

    def __call__(self, curve, ax=None):
        """Return an inset edge point using coordinate semantics."""
        finite = curve.finite
        if not np.any(finite):
            return None
        x = np.asarray(curve.x[finite], dtype=float)
        y = np.asarray(curve.y[finite], dtype=float)
        radius = np.hypot(x, y)
        inside = radius <= self.radius * (1.0 + 1.0e-6)
        if not np.any(inside):
            return None
        x = x[inside]
        y = y[inside]
        radius = radius[inside]
        name = str(curve.name or "")
        if name.startswith("declination_"):
            if self.declination_at_left:
                index = int(np.argmin(x))
                label_x = float(self.inset) * float(x[index])
            else:
                upper = np.flatnonzero(y >= 0.0)
                candidates = upper if upper.size else np.arange(len(x))
                index = int(candidates[np.argmin(np.abs(x[candidates]))])
                label_x = (
                    float(self.inset) * float(x[index])
                    - 0.012 * self.radius
                )
            return _above_line(
                label_x, float(self.inset) * float(y[index])
            )
        else:
            index = int(np.argmax(radius))
        return (
            float(self.inset) * float(x[index]),
            float(self.inset) * float(y[index]),
        )


@dataclass(frozen=True)
class EllipticalGridLabelAnchor:
    """Place coordinate labels just inside an elliptical boundary."""

    boundary: ProjectedCurve
    inset: float = 0.965

    def __post_init__(self):
        if not 0.0 < float(self.inset) <= 1.0:
            raise ValueError("inset must be in the interval (0, 1].")

    @property
    def limits(self):
        finite = self.boundary.finite
        if not np.any(finite):
            raise ValueError("boundary has no finite points.")
        return (
            float(np.max(np.abs(self.boundary.x[finite]))),
            float(np.max(np.abs(self.boundary.y[finite]))),
        )

    def __call__(self, curve, ax=None):
        finite = curve.finite
        if not np.any(finite):
            return None
        x = np.asarray(curve.x[finite], dtype=float)
        y = np.asarray(curve.y[finite], dtype=float)
        x_limit, y_limit = self.limits
        radius = np.hypot(x / x_limit, y / y_limit)
        inside = radius <= 1.0 + 1.0e-6
        if not np.any(inside):
            return None
        x = x[inside]
        y = y[inside]
        radius = radius[inside]
        name = str(curve.name or "")
        latitude = any(name.startswith(prefix) for prefix in (
            "declination_", "ecliptic_latitude_", "galactic_latitude_",
        ))
        if latitude:
            index = int(np.argmin(np.abs(x)))
            return _above_line(
                self.inset * float(x[index]) - 0.012 * x_limit,
                self.inset * float(y[index]),
            )
        longitude_prefixes = (
            "right_ascension_", "ecliptic_longitude_",
            "galactic_longitude_", "azimuth_",
        )
        for prefix in longitude_prefixes:
            if name.startswith(prefix):
                value = float(name.removeprefix(prefix)) % 360.0
                if not any(
                    np.isclose(value, principal)
                    for principal in (0.0, 90.0, 180.0, 270.0)
                ):
                    return None
                break
        if name.startswith("galactic_longitude_"):
            equator_distance = np.abs(y)
            candidates = np.flatnonzero(
                np.isclose(
                    equator_distance,
                    np.min(equator_distance),
                    atol=1.0e-12,
                    rtol=0.0,
                )
            )
            if np.isclose(value, 180.0):
                expected_x = -x_limit
            elif value < 180.0:
                expected_x = -(value / 180.0) * x_limit
            else:
                expected_x = ((360.0 - value) / 180.0) * x_limit
            index = int(
                candidates[
                    np.argmin(np.abs(x[candidates] - expected_x))
                ]
            )
            if abs(float(x[index]) - expected_x) > 0.08 * x_limit:
                return None
            return CurveLabelPlacement(
                float(x[index]) + 0.012 * x_limit,
                -0.035 * y_limit,
                rotation_deg=0.0,
                horizontal_alignment="left",
                vertical_alignment="top",
            )
        index = int(np.argmax(radius))
        return self.inset * float(x[index]), self.inset * float(y[index])


@dataclass(frozen=True)
class RectangularLabelAnchor:
    """Place RA labels at bottom and declination labels at left."""

    inset: float = 0.01
    minimum_horizontal_separation: float = 0.13
    minimum_vertical_separation: float = 0.06
    _occupied: list[tuple[float, float]] = field(
        default_factory=list,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self):
        if not 0.0 <= float(self.inset) < 0.5:
            raise ValueError("inset must be in the interval [0, 0.5).")
        if float(self.minimum_horizontal_separation) <= 0.0:
            raise ValueError("minimum_horizontal_separation must be positive.")
        if float(self.minimum_vertical_separation) <= 0.0:
            raise ValueError("minimum_vertical_separation must be positive.")

    def _claim(self, x, y, xlim, ylim):
        normalized = (
            (float(x) - min(xlim)) / abs(xlim[1] - xlim[0]),
            (float(y) - min(ylim)) / abs(ylim[1] - ylim[0]),
        )
        collision = any(
            abs(normalized[0] - occupied[0])
            < self.minimum_horizontal_separation
            and abs(normalized[1] - occupied[1])
            < self.minimum_vertical_separation
            for occupied in self._occupied
        )
        if collision:
            return False
        self._occupied.append(normalized)
        return True

    def __call__(self, curve, ax):
        finite = curve.finite
        if not np.any(finite):
            return None
        x = np.asarray(curve.x[finite], dtype=float)
        y = np.asarray(curve.y[finite], dtype=float)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_min, x_max = sorted(xlim)
        y_min, y_max = sorted(ylim)
        inside = (
            (x >= x_min)
            & (x <= x_max)
            & (y >= y_min)
            & (y <= y_max)
        )
        if not np.any(inside):
            return None
        x = x[inside]
        y = y[inside]
        name = str(curve.name or "")
        if name.startswith("right_ascension_"):
            target = min(ylim) + self.inset * abs(ylim[1] - ylim[0])
            order = np.argsort(np.abs(y - target))
        elif name.startswith("declination_"):
            target = min(xlim) + self.inset * abs(xlim[1] - xlim[0])
            order = np.argsort(np.abs(x - target))
        else:
            order = np.argsort(-y)
        index = next(
            (
                int(candidate)
                for candidate in order
                if self._claim(x[candidate], y[candidate], xlim, ylim)
            ),
            None,
        )
        if index is None:
            return None
        if name.startswith("declination_"):
            return _above_line(
                x[index],
                y[index],
                horizontal_alignment="left",
            )
        if name.startswith("right_ascension_"):
            return CurveLabelPlacement(
                float(x[index]),
                float(y[index]),
                horizontal_alignment="center",
                vertical_alignment="bottom",
            )
        return float(x[index]), float(y[index])


@dataclass(frozen=True)
class HorizonGridLabelAnchor:
    """Anchor azimuth outside the horizon and altitude on selected spokes."""

    projection: object
    boundary: ProjectedCurve
    horizon_altitude_deg: float = 0.0
    altitude_label_azimuths_deg: tuple[float, ...] = (0.0, 90.0, 180.0, 270.0)

    def __call__(self, curve, ax=None):
        name = str(curve.name or "")
        if name.startswith("altitude_"):
            altitude = float(name.removeprefix("altitude_"))
            if altitude <= self.horizon_altitude_deg:
                return None
            spokes = (0.0,) if altitude == 90.0 else self.altitude_label_azimuths_deg
            placements = []
            for azimuth in spokes:
                x, y = self.projection.project_spherical(azimuth, altitude)
                if np.isfinite((x, y)).all():
                    placements.append(_above_line(
                        x, y, normal_offset_em=0.65 if altitude == 90.0 else 0.2,
                    ))
            return placements
        if name.startswith("azimuth_"):
            azimuth = float(name.removeprefix("azimuth_"))
            x, y = self.projection.project_spherical(azimuth, self.horizon_altitude_deg)
            finite = self.boundary.finite
            bx, by = self.boundary.x[finite], self.boundary.y[finite]
            # A stereographic small circle remains a circle even off zenith.
            matrix = np.column_stack((2.0 * bx, 2.0 * by, np.ones(len(bx))))
            cx, cy, _ = np.linalg.lstsq(matrix, bx**2 + by**2, rcond=None)[0]
            return CurveLabelPlacement(
                float(x), float(y), rotation_deg=0.0, normal_offset_em=0.65,
                horizontal_alignment="center", vertical_alignment="center",
                exterior_direction=(float(x - cx), float(y - cy)),
            )
        return None


def apply_coordinate_label_anchor(layer_options, anchor, *, altaz_anchor=None):
    """Return layer options with grid label anchors replaced safely."""
    resolved = {
        layer: dict(options)
        for layer, options in layer_options.items()
    }
    coordinate_grid_names = {
        "coordinates_grid",
        "altaz_grid",
        "equatorial_grid",
        "ecliptic_grid",
        "galactic_grid",
    }
    for layer, options in resolved.items():
        layer_name = (
            layer if isinstance(layer, str)
            else getattr(layer, "layer_name", None)
        )
        coordinate_system = (
            None if isinstance(layer, str)
            else getattr(layer, "coordinate_system", None)
        )
        if (
            layer_name not in coordinate_grid_names
            and coordinate_system not in {
                "altaz", "equatorial", "ecliptic", "galactic"
            }
        ):
            continue
        render = options.get("render")
        if not isinstance(render, dict):
            continue
        if (
            "label_formatter" not in render
            and "label_anchor" not in render
        ):
            continue
        updated_render = dict(render)
        updated_render["label_anchor"] = (
            altaz_anchor if altaz_anchor is not None and (
                layer_name == "altaz_grid" or coordinate_system == "altaz"
            ) else anchor
        )
        options["render"] = updated_render
    return resolved


@dataclass(frozen=True)
class ExteriorGridLabelAnchor:
    """Move an existing marginal grid anchor to a real boundary crossing."""

    delegate: object
    boundary: ProjectedCurve
    circular: bool = False

    def __call__(self, curve, ax):
        anchor = self.delegate(curve, ax)
        if anchor is None:
            return None
        target = np.array((anchor.x, anchor.y) if isinstance(anchor, CurveLabelPlacement) else anchor)
        boundary = np.column_stack((self.boundary.x, self.boundary.y))
        low, high = np.nanmin(boundary, axis=0), np.nanmax(boundary, axis=0)
        centre = (low + high) / 2.0
        radius = float(np.nanmedian(np.linalg.norm(boundary - centre, axis=1)))
        points = np.column_stack((curve.x, curve.y))
        crossings = []
        for a, b in zip(points[:-1], points[1:]):
            if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
                continue
            delta = b - a
            if self.circular:
                aa = np.dot(delta, delta)
                if aa == 0:
                    continue
                bb = 2 * np.dot(a - centre, delta)
                cc = np.dot(a - centre, a - centre) - radius ** 2
                discriminant = bb ** 2 - 4 * aa * cc
                if discriminant < 0:
                    continue
                for t in ((-bb - np.sqrt(discriminant)) / (2 * aa),
                          (-bb + np.sqrt(discriminant)) / (2 * aa)):
                    if -1e-8 <= t <= 1 + 1e-8:
                        point = a + np.clip(t, 0, 1) * delta
                        crossings.append((point, point - centre))
            else:
                for axis in (0, 1):
                    if delta[axis] == 0:
                        continue
                    for edge, sign in ((low[axis], -1), (high[axis], 1)):
                        t = (edge - a[axis]) / delta[axis]
                        point = a + t * delta
                        other = 1 - axis
                        if -1e-8 <= t <= 1 + 1e-8 and low[other] - 1e-8 <= point[other] <= high[other] + 1e-8:
                            direction = np.zeros(2); direction[axis] = sign
                            crossings.append((point, direction))
        if not crossings:
            return None
        point, direction = min(crossings, key=lambda item: np.linalg.norm(item[0] - target))
        return CurveLabelPlacement(
            *point, rotation_deg=0.0, normal_offset_em=0.65,
            horizontal_alignment="center", vertical_alignment="center",
            exterior_direction=tuple(direction),
        )
