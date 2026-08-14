"""Reusable projected boundaries and coordinate-label anchors."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.geometry.projected import ProjectedCurve
from wenu.geometry.viewport import Viewport
from wenu.rendering.label_placement import CurveLabelPlacement


def _above_line(x, y):
    return CurveLabelPlacement(
        float(x), float(y), rotation_deg=0.0, normal_offset_em=0.65
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
        index = int(np.argmax(radius))
        return self.inset * float(x[index]), self.inset * float(y[index])


@dataclass(frozen=True)
class RectangularLabelAnchor:
    """Place RA labels at bottom and declination labels at left."""

    inset: float = 0.015

    def __post_init__(self):
        if not 0.0 <= float(self.inset) < 0.5:
            raise ValueError("inset must be in the interval [0, 0.5).")

    def __call__(self, curve, ax):
        finite = curve.finite
        if not np.any(finite):
            return None
        x = np.asarray(curve.x[finite], dtype=float)
        y = np.asarray(curve.y[finite], dtype=float)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        name = str(curve.name or "")
        if name.startswith("right_ascension_"):
            target = min(ylim) + self.inset * abs(ylim[1] - ylim[0])
            index = int(np.argmin(np.abs(y - target)))
        elif name.startswith("declination_"):
            target = min(xlim) + self.inset * abs(xlim[1] - xlim[0])
            index = int(np.argmin(np.abs(x - target)))
        else:
            index = int(np.argmax(y))
        if name.startswith("declination_"):
            return _above_line(x[index], y[index])
        return float(x[index]), float(y[index])


def apply_coordinate_label_anchor(layer_options, anchor):
    """Return layer options with grid label anchors replaced safely."""
    resolved = {
        layer: dict(options)
        for layer, options in layer_options.items()
    }
    for layer, options in resolved.items():
        render = options.get("render")
        if not isinstance(render, dict):
            continue
        if (
            "label_formatter" not in render
            and "label_anchor" not in render
        ):
            continue
        updated_render = dict(render)
        updated_render["label_anchor"] = anchor
        options["render"] = updated_render
    return resolved
