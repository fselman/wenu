"""Reusable projected boundaries and coordinate-label anchors."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.geometry.projected import ProjectedCurve
from wenu.geometry.viewport import Viewport


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
        if self.declination_at_left and name.startswith("declination_"):
            index = int(np.argmin(x))
        else:
            index = int(np.argmax(radius))
        return (
            float(self.inset) * float(x[index]),
            float(self.inset) * float(y[index]),
        )


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
