"""Backend-neutral placement for labels on projected curves."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.geometry.projected import ProjectedCurve


@dataclass(frozen=True)
class CurveLabelPlacement:
    """A projected label position with an optional readable rotation."""

    x: float
    y: float
    rotation_deg: float | None = None
    normal_offset_em: float = 0.0

    def __post_init__(self):
        if not np.isfinite((self.x, self.y)).all():
            raise ValueError("label position must be finite.")
        if self.rotation_deg is not None and not np.isfinite(
            self.rotation_deg
        ):
            raise ValueError("label rotation must be finite.")
        if not np.isfinite(self.normal_offset_em):
            raise ValueError("label normal offset must be finite.")
        if self.normal_offset_em < 0.0:
            raise ValueError("label normal offset cannot be negative.")


def _readable_rotation(angle_deg):
    """Normalize a line orientation so text is never upside down."""
    return float((float(angle_deg) + 90.0) % 180.0 - 90.0)


def _distinct_neighbor(curve, index, step):
    """Return the nearest distinct point in one contiguous direction."""
    x0 = float(curve.x[index])
    y0 = float(curve.y[index])
    candidate = index + step
    while 0 <= candidate < len(curve):
        if not curve.finite[candidate]:
            return None
        dx = float(curve.x[candidate]) - x0
        dy = float(curve.y[candidate]) - y0
        if np.hypot(dx, dy) > 1.0e-12:
            return candidate
        candidate += step
    return None


def tangent_label_placement(curve, position, *, normal_offset_em=0.0):
    """Return a label placement parallel to the local projected tangent.

    The tangent is measured at the finite curve sample nearest ``position``.
    It never bridges a non-finite break, and repeated samples are skipped.
    When no finite tangent exists, the position remains valid and rotation is
    left unspecified.
    """
    if not isinstance(curve, ProjectedCurve):
        raise TypeError("curve must be a ProjectedCurve.")
    x, y = (float(value) for value in position)
    if not np.isfinite((x, y)).all():
        raise ValueError("label position must be finite.")
    finite_indices = np.flatnonzero(curve.finite)
    if finite_indices.size == 0:
        return CurveLabelPlacement(
            x, y, normal_offset_em=normal_offset_em
        )
    distances = (
        (curve.x[finite_indices] - x) ** 2
        + (curve.y[finite_indices] - y) ** 2
    )
    index = int(finite_indices[np.argmin(distances)])
    before = _distinct_neighbor(curve, index, -1)
    after = _distinct_neighbor(curve, index, 1)
    if before is not None and after is not None:
        dx = float(curve.x[after] - curve.x[before])
        dy = float(curve.y[after] - curve.y[before])
    elif after is not None:
        dx = float(curve.x[after] - curve.x[index])
        dy = float(curve.y[after] - curve.y[index])
    elif before is not None:
        dx = float(curve.x[index] - curve.x[before])
        dy = float(curve.y[index] - curve.y[before])
    else:
        return CurveLabelPlacement(
            x, y, normal_offset_em=normal_offset_em
        )
    angle = _readable_rotation(np.degrees(np.arctan2(dy, dx)))
    return CurveLabelPlacement(x, y, angle, normal_offset_em)
