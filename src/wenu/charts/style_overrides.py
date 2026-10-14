"""Render-local visual overrides applied after style and mode resolution."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from typing import Mapping

from .style_components import StellarMagnitudeSizing


@dataclass(frozen=True)
class ChartStyleOverrides:
    """Optional caller values with precedence over resolved mode defaults."""

    constellation_linewidth: float | None = None
    constellation_line_color: str | None = None
    constellation_label_color: str | None = None
    constellation_label_offsets: Mapping[
        str, tuple[float, float]
    ] | None = None
    boundary_linewidth: float | None = None
    boundary_color: str | None = None
    draw_coordinate_labels: bool | None = None
    ecliptic_linewidth: float | None = None
    coordinate_label_fontsize: float | None = None
    stellar_magnitude_sizing: StellarMagnitudeSizing | None = None
    star_size_scale: float | None = None
    sky_color: str | None = None
    equatorial_reference_linewidth: float | None = None
    constellation_line_gap_points: float | None = None
    star_label_placement: str | None = None
    labels_orientation: str | None = None
    grid_label_band: bool | None = None
    grid_label_band_fill_color: str | None = None
    grid_label_band_frame_color: str | None = None
    grid_label_band_linewidth: float | None = None

    def __post_init__(self):
        if self.star_size_scale is not None:
            value = self.star_size_scale
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0 or not isfinite(value * value):
                raise ValueError("star_size_scale must be finite and positive.")
        if self.labels_orientation not in {None, "chart", "upright", "up-away-from-cp"}:
            raise ValueError("unsupported labels_orientation")
        if self.star_label_placement not in {None, "fixed", "auto"}:
            raise ValueError("star_label_placement must be fixed or auto")
        if self.constellation_label_offsets is not None:
            offsets = {}
            for label, value in self.constellation_label_offsets.items():
                try:
                    dx, dy = value
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        "constellation label offsets must contain pairs."
                    ) from error
                pair = (float(dx), float(dy))
                if not all(isfinite(component) for component in pair):
                    raise ValueError(
                        "constellation label offsets must be finite."
                    )
                offsets[str(label)] = pair
            object.__setattr__(self, "constellation_label_offsets", offsets)
        if (
            self.stellar_magnitude_sizing is not None
            and not isinstance(
                self.stellar_magnitude_sizing,
                StellarMagnitudeSizing,
            )
        ):
            raise TypeError(
                "stellar_magnitude_sizing must be StellarMagnitudeSizing."
            )
        for name in (
            "grid_label_band_linewidth",
            "constellation_linewidth",
            "constellation_line_gap_points",
            "boundary_linewidth",
            "equatorial_reference_linewidth",
            "ecliptic_linewidth",
            "coordinate_label_fontsize",
        ):
            value = getattr(self, name)
            if value is None:
                continue
            if not isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")
        for name in (
            "grid_label_band_fill_color",
            "grid_label_band_frame_color",
            "constellation_line_color",
            "constellation_label_color",
            "boundary_color",
            "sky_color",
        ):
            value = getattr(self, name)
            if value is not None and not str(value).strip():
                raise ValueError(f"{name} cannot be empty.")

    def apply(self, style):
        """Return ``style`` with non-``None`` grid values replaced."""
        grids = getattr(style, "grids", None)
        if grids is None:
            raise TypeError("style overrides require a composed chart style.")
        changes = {
            name: getattr(self, name)
            for name in (
                "constellation_linewidth",
                "constellation_line_gap_points",
                "constellation_line_color",
                "constellation_label_color",
                "constellation_label_offsets",
                "boundary_linewidth",
                "boundary_color",
                "draw_coordinate_labels",
                "equatorial_reference_linewidth",
                "ecliptic_linewidth",
                "coordinate_label_fontsize",
            )
            if getattr(self, name) is not None
        }
        resolved = style if not changes else replace(
            style, grids=replace(grids, **changes)
        )
        if self.star_label_placement is not None:
            resolved = replace(resolved, stars=replace(
                resolved.stars, label_placement=self.star_label_placement,
            ))
        band_changes = {name: getattr(self, name) for name in (
            "grid_label_band", "grid_label_band_fill_color",
            "grid_label_band_frame_color", "grid_label_band_linewidth",
        ) if getattr(self, name) is not None}
        if band_changes:
            resolved = replace(resolved, canvas=replace(resolved.canvas, **band_changes))
        if self.labels_orientation is not None:
            resolved = replace(resolved, canvas=replace(
                resolved.canvas, labels_orientation=self.labels_orientation,
            ))
        if self.sky_color is not None:
            canvas = getattr(resolved, "canvas", None)
            if canvas is None:
                raise TypeError(
                    "sky color overrides require a composed canvas style."
                )
            resolved = replace(
                resolved,
                canvas=replace(canvas, sky_color=str(self.sky_color)),
            )
        if self.star_size_scale is not None:
            stars = resolved.stars
            area_factor = self.star_size_scale ** 2
            resolved = replace(resolved, stars=replace(stars,
                area_scale=stars.area_scale * area_factor,
                variable_symbol_size=stars.variable_symbol_size * area_factor,
                multiple_symbol_size=stars.multiple_symbol_size * area_factor))
        sizing = self.stellar_magnitude_sizing or resolved.stars.magnitude_sizing
        if sizing.algorithm != "legacy":
            # Physical diameter policies supersede preset/family area factors
            # and historical polar magnitude remapping. Explicit diameter
            # multiplication remains available and is recorded after resolution.
            return replace(resolved, stars=replace(resolved.stars,
                magnitude_sizing=sizing, area_scale=(self.star_size_scale if self.star_size_scale is not None else resolved.stars.diameter_scale)**2,
                ordinary_magnitude_scale=1.0, ordinary_magnitude_offset=0.0,
                bright_magnitude_scale=1.0, bright_magnitude_offset=0.0,
                draw_bright_symbols=False))
        if self.stellar_magnitude_sizing is None:
            return resolved
        stars = getattr(resolved, "stars", None)
        if stars is None:
            raise TypeError("stellar sizing requires a composed chart style.")
        return replace(
            resolved,
            stars=replace(
                stars,
                magnitude_sizing=self.stellar_magnitude_sizing,
            ),
        )


def add_magnitude_sizing_arguments(parser):
    """Shared appearance switches; selection remains a separate detail option."""
    parser.add_argument("--mag-algorithm", choices=("legacy", "linear", "asinh", "quadratic"))
    parser.add_argument("--mag-a", type=float, help="Diameter growth coefficient, mm.")
    parser.add_argument("--mag-b", type=float, help="Asinh transition interval, magnitudes.")
    parser.add_argument("--mag-dmin", type=float, help="Minimum diameter, mm, before explicit star-size scaling.")
    parser.add_argument("--mag-size-reference", type=float, help="Magnitude assigned the minimum diameter.")


def magnitude_sizing_from_arguments(arguments, base=None):
    """Build one typed policy, rejecting parameters without an algorithm."""
    values = {field: getattr(arguments, option, None) for field, option in (
        ("algorithm", "mag_algorithm"), ("a_mm", "mag_a"), ("b_mag", "mag_b"),
        ("dmin_mm", "mag_dmin"), ("size_reference_magnitude", "mag_size_reference"))}
    supplied = {key: value for key, value in values.items() if value is not None}
    if not supplied:
        return base
    if values["algorithm"] is None and base is None:
        raise ValueError("Magnitude sizing parameters require --mag-algorithm.")
    policy = replace(base or StellarMagnitudeSizing(), **supplied)
    if policy.algorithm == "legacy" and any(key != "algorithm" for key in supplied):
        raise ValueError("Diameter parameters require linear, asinh or quadratic sizing.")
    return policy
