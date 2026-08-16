"""Renderer-neutral A4 pouch furniture for paired polar overlays."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.polar_horizon_overlay import PolarHorizonPairOverlay


_HOURS = (19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5)


@dataclass(frozen=True)
class PolarPouchLabel:
    """One fixed paper label, independent of projected sky orientation."""

    role: str
    text: str
    position_mm: tuple[float, float]


@dataclass(frozen=True)
class PolarPouchDateWindow:
    """One annular date-viewing window at the physical disk edge."""

    index: int
    center_mm: tuple[float, float]
    inner_radius_mm: float
    outer_radius_mm: float
    start_angle_deg: float
    end_angle_deg: float

    @property
    def span_deg(self):
        return self.end_angle_deg - self.start_angle_deg


@dataclass(frozen=True)
class PolarPouchHourMark:
    """One fixed observation-hour numeral and its external short mark."""

    hour: int
    angle_deg: float
    numeral_position_mm: tuple[float, float]
    numeral_rotation_deg: float
    tick_start_mm: tuple[float, float]
    tick_end_mm: tuple[float, float]


@dataclass(frozen=True)
class PolarPouchGlueStrip:
    """One rectangular side-gluing zone in page coordinates."""

    side: str
    lower_left_mm: tuple[float, float]
    upper_right_mm: tuple[float, float]


@dataclass(frozen=True)
class PolarPouchFaceFurniture:
    """Resolved physical construction and furniture for one pouch face."""

    face: str
    page_size_mm: tuple[float, float]
    safe_margin_mm: float
    fold_y_mm: float
    disk_center_mm: tuple[float, float]
    disk_radius_mm: float
    horizon_segments_mm: tuple[tuple[tuple[float, float], ...], ...]
    date_windows: tuple[PolarPouchDateWindow, ...]
    hour_circle_radius_mm: float
    hour_marks: tuple[PolarPouchHourMark, ...]
    labels: tuple[PolarPouchLabel, ...]
    glue_strips: tuple[PolarPouchGlueStrip, ...]

    @property
    def fold_line_mm(self):
        return (
            (self.safe_margin_mm, self.fold_y_mm),
            (self.page_size_mm[0] - self.safe_margin_mm, self.fold_y_mm),
        )


@dataclass(frozen=True)
class PolarPouchPairFurniture:
    """Matched front/back furniture for one folded A4 pouch."""

    south: PolarPouchFaceFurniture
    north: PolarPouchFaceFurniture

    @property
    def faces(self):
        return self.south, self.north


@dataclass(frozen=True)
class PolarPouchFurnitureRequest:
    """Resolve the accepted folded-pouch construction in millimetres."""

    safe_margin_mm: float = 5.0
    glue_strip_width_mm: float = 2.0
    date_window_span_deg: float = 37.5
    date_window_gap_deg: float = 5.0
    date_window_count: int = 3
    date_window_inner_radius_fraction: float = 0.945
    date_window_outer_radius_fraction: float = 0.99
    hour_circle_radius_fraction: float = 0.80
    hour_numeral_radius_fraction: float = 0.86
    hour_tick_inner_radius_fraction: float = 0.91
    hour_tick_outer_radius_fraction: float = 0.94
    south_title: str = "Un firmamento, muchos cielos"
    horizon_label: str = "HORIZONTE"

    def __post_init__(self):
        numeric = np.asarray(
            (
                self.safe_margin_mm,
                self.glue_strip_width_mm,
                self.date_window_span_deg,
                self.date_window_gap_deg,
                self.date_window_inner_radius_fraction,
                self.date_window_outer_radius_fraction,
                self.hour_circle_radius_fraction,
                self.hour_numeral_radius_fraction,
                self.hour_tick_inner_radius_fraction,
                self.hour_tick_outer_radius_fraction,
            ),
            dtype=float,
        )
        if not np.all(np.isfinite(numeric)):
            raise ValueError("Polar pouch furniture values must be finite.")
        if self.safe_margin_mm <= 0.0 or self.glue_strip_width_mm <= 0.0:
            raise ValueError("Safe margin and glue width must be positive.")
        if self.date_window_span_deg <= 0.0:
            raise ValueError("date_window_span_deg must be positive.")
        if self.date_window_gap_deg < 0.0:
            raise ValueError("date_window_gap_deg must be non-negative.")
        if int(self.date_window_count) != 3:
            raise ValueError("The classroom pouch requires three date windows.")
        radii = numeric[4:]
        if not np.all((radii > 0.0) & (radii < 1.0)):
            raise ValueError("Pouch radial fractions must lie between 0 and 1.")
        if not (
            self.hour_circle_radius_fraction
            < self.hour_numeral_radius_fraction
            < self.hour_tick_inner_radius_fraction
            < self.hour_tick_outer_radius_fraction
            < self.date_window_inner_radius_fraction
            < self.date_window_outer_radius_fraction
        ):
            raise ValueError("Pouch radial furniture must be strictly ordered.")
        for name in ("south_title", "horizon_label"):
            value = str(getattr(self, name)).strip()
            if not value:
                raise ValueError(f"{name} must not be empty.")
            object.__setattr__(self, name, value)
        object.__setattr__(self, "safe_margin_mm", float(self.safe_margin_mm))
        object.__setattr__(
            self, "glue_strip_width_mm", float(self.glue_strip_width_mm)
        )
        object.__setattr__(
            self, "date_window_span_deg", float(self.date_window_span_deg)
        )
        object.__setattr__(
            self, "date_window_gap_deg", float(self.date_window_gap_deg)
        )
        object.__setattr__(self, "date_window_count", 3)
        for name in (
            "date_window_inner_radius_fraction",
            "date_window_outer_radius_fraction",
            "hour_circle_radius_fraction",
            "hour_numeral_radius_fraction",
            "hour_tick_inner_radius_fraction",
            "hour_tick_outer_radius_fraction",
        ):
            object.__setattr__(self, name, float(getattr(self, name)))

    def resolve(self, overlays):
        """Return paired fixed furniture around resolved horizon curves."""
        if not isinstance(overlays, PolarHorizonPairOverlay):
            raise TypeError("overlays must be a PolarHorizonPairOverlay value.")
        south, north = overlays.faces
        if south.page_size_mm != north.page_size_mm:
            raise ValueError("Paired pouch faces require one common page size.")
        if not np.isclose(
            south.disk_radius_mm, north.disk_radius_mm, atol=1.0e-12
        ):
            raise ValueError("Paired pouch faces require one disk radius.")
        width, height = south.page_size_mm
        radius = south.disk_radius_mm
        fold_y = height - self.safe_margin_mm - 2.0 * radius
        center = (width / 2.0, fold_y + radius)
        if fold_y < self.safe_margin_mm:
            raise ValueError("The complete disk does not fit above the fold.")
        if center[0] - radius < self.safe_margin_mm:
            raise ValueError("The complete disk does not fit the pouch width.")
        if center[0] + radius > width - self.safe_margin_mm:
            raise ValueError("The complete disk does not fit the pouch width.")
        if radius - south.cut_clearance_mm <= (
            radius * self.date_window_inner_radius_fraction
        ):
            raise ValueError("Cut clearance leaves no radial date window.")
        if not np.isclose(
            south.cut_clearance_mm, north.cut_clearance_mm, atol=1.0e-12
        ):
            raise ValueError("Paired pouch faces require one cut clearance.")
        resolved = tuple(
            self._resolve_face(face, center=center, fold_y=fold_y)
            for face in overlays.faces
        )
        return PolarPouchPairFurniture(south=resolved[0], north=resolved[1])

    def _resolve_face(self, overlay, *, center, fold_y):
        offset = np.asarray(center) - np.asarray(overlay.disk_center_mm)
        horizon = tuple(
            tuple(
                (
                    float(point[0] + offset[0]),
                    float(point[1] + offset[1]),
                )
                for point in segment
            )
            for segment in overlay.horizon_segments_mm
        )
        radius = overlay.disk_radius_mm
        windows = _date_windows(
            center,
            radius,
            count=self.date_window_count,
            span_deg=self.date_window_span_deg,
            gap_deg=self.date_window_gap_deg,
            inner_fraction=self.date_window_inner_radius_fraction,
            outer_fraction=self.date_window_outer_radius_fraction,
            cut_clearance_mm=overlay.cut_clearance_mm,
        )
        hours = _hour_marks(
            overlay.face,
            center,
            radius,
            numeral_fraction=self.hour_numeral_radius_fraction,
            tick_inner_fraction=self.hour_tick_inner_radius_fraction,
            tick_outer_fraction=self.hour_tick_outer_radius_fraction,
        )
        return PolarPouchFaceFurniture(
            face=overlay.face,
            page_size_mm=overlay.page_size_mm,
            safe_margin_mm=self.safe_margin_mm,
            fold_y_mm=fold_y,
            disk_center_mm=center,
            disk_radius_mm=radius,
            horizon_segments_mm=horizon,
            date_windows=windows,
            hour_circle_radius_mm=(
                radius * self.hour_circle_radius_fraction
            ),
            hour_marks=hours,
            labels=_fixed_labels(
                overlay.face,
                center,
                radius,
                south_title=self.south_title,
                horizon_label=self.horizon_label,
            ),
            glue_strips=_glue_strips(
                overlay.page_size_mm,
                fold_y,
                safe_margin_mm=self.safe_margin_mm,
                width_mm=self.glue_strip_width_mm,
            ),
        )


def _date_windows(
    center,
    radius,
    *,
    count,
    span_deg,
    gap_deg,
    inner_fraction,
    outer_fraction,
    cut_clearance_mm,
):
    total = count * span_deg + (count - 1) * gap_deg
    start = 270.0 - total / 2.0
    outer_radius = min(
        radius * outer_fraction,
        radius - float(cut_clearance_mm),
    )
    return tuple(
        PolarPouchDateWindow(
            index=index + 1,
            center_mm=center,
            inner_radius_mm=radius * inner_fraction,
            outer_radius_mm=outer_radius,
            start_angle_deg=start + index * (span_deg + gap_deg),
            end_angle_deg=(
                start + index * (span_deg + gap_deg) + span_deg
            ),
        )
        for index in range(count)
    )


def _hour_marks(
    face,
    center,
    radius,
    *,
    numeral_fraction,
    tick_inner_fraction,
    tick_outer_fraction,
):
    angles = (
        tuple(345.0 - 15.0 * index for index in range(len(_HOURS)))
        if face == "south"
        else tuple(195.0 + 15.0 * index for index in range(len(_HOURS)))
    )
    return tuple(
        PolarPouchHourMark(
            hour=hour,
            angle_deg=angle,
            numeral_position_mm=_radial_point(
                center, radius * numeral_fraction, angle
            ),
            numeral_rotation_deg=_upright_tangent_rotation(angle),
            tick_start_mm=_radial_point(
                center, radius * tick_inner_fraction, angle
            ),
            tick_end_mm=_radial_point(
                center, radius * tick_outer_fraction, angle
            ),
        )
        for hour, angle in zip(_HOURS, angles, strict=True)
    )


def _fixed_labels(face, center, radius, *, south_title, horizon_label):
    center_x, center_y = center
    if face == "south":
        values = (
            ("cardinal", "E", (center_x - 0.86 * radius, center_y - 4.0)),
            ("cardinal", "W", (center_x + 0.86 * radius, center_y - 4.0)),
            ("cardinal", "S", (center_x, center_y - 0.36 * radius)),
            (
                "horizon",
                horizon_label,
                (center_x + 0.45 * radius, center_y - 0.36 * radius),
            ),
            ("title", south_title, (center_x, center_y - radius + 12.0)),
        )
    else:
        values = (
            ("cardinal", "W", (center_x - 0.86 * radius, center_y + 4.0)),
            ("cardinal", "E", (center_x + 0.86 * radius, center_y + 4.0)),
            ("cardinal", "N", (center_x, center_y + 0.36 * radius)),
            (
                "horizon",
                horizon_label,
                (center_x + 0.45 * radius, center_y + 0.36 * radius),
            ),
        )
    return tuple(
        PolarPouchLabel(role=role, text=text, position_mm=position)
        for role, text, position in values
    )


def _glue_strips(page_size, fold_y, *, safe_margin_mm, width_mm):
    page_width, page_height = page_size
    return (
        PolarPouchGlueStrip(
            side="left",
            lower_left_mm=(safe_margin_mm, fold_y),
            upper_right_mm=(safe_margin_mm + width_mm, page_height),
        ),
        PolarPouchGlueStrip(
            side="right",
            lower_left_mm=(page_width - safe_margin_mm - width_mm, fold_y),
            upper_right_mm=(page_width - safe_margin_mm, page_height),
        ),
    )


def _radial_point(center, radius, angle_deg):
    angle = np.deg2rad(float(angle_deg))
    return (
        float(center[0]) + float(radius) * np.cos(angle),
        float(center[1]) + float(radius) * np.sin(angle),
    )


def _upright_tangent_rotation(angle_deg):
    return (float(angle_deg) + 270.0) % 360.0 - 180.0
