"""Polar-only stellar magnitude-scale semantics and physical placement."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.detail_application import configured_stellar_symbol_sizes
from wenu.charts.style_components import StellarStyle


_BRIGHT_INTERVALS = (
    (-1.5, -1.0),
    (-1.0, -0.5),
    (-0.5, 0.0),
    (0.0, 0.5),
)
_ORDINARY_INTERVALS = (
    (0.5, 1.0),
    (1.0, 2.0),
    (2.0, 3.0),
    (3.0, 4.0),
    (4.0, 5.0),
)


@dataclass(frozen=True)
class PolarMagnitudeScaleEntry:
    """One polar legend interval realized by the chart's stellar size law."""

    lower_magnitude: float
    upper_magnitude: float
    representative_magnitude: float
    label: str
    symbol: str
    marker_area_points2: float


@dataclass(frozen=True)
class PolarMagnitudeScale:
    """Resolved polar-only magnitude semantics shared by disks and pouch."""

    title: str
    limiting_magnitude: float
    bright_cutoff_magnitude: float
    bright_entries: tuple[PolarMagnitudeScaleEntry, ...]
    ordinary_entries: tuple[PolarMagnitudeScaleEntry, ...]

    @property
    def entries(self):
        return self.bright_entries + self.ordinary_entries

    def manifest_record(self):
        """Return JSON-ready semantics for reproducible physical exports."""
        return {
            "title": self.title,
            "limiting_magnitude": self.limiting_magnitude,
            "bright_cutoff_magnitude": self.bright_cutoff_magnitude,
            "entries": [
                {
                    "lower_magnitude": entry.lower_magnitude,
                    "upper_magnitude": entry.upper_magnitude,
                    "representative_magnitude": (
                        entry.representative_magnitude
                    ),
                    "label": entry.label,
                    "symbol": entry.symbol,
                    "marker_area_points2": entry.marker_area_points2,
                }
                for entry in self.entries
            ],
        }


@dataclass(frozen=True)
class PolarMagnitudeScalePlacement:
    """Physical placement of the shared scale on one product face."""

    title_position_mm: tuple[float, float]
    bright_center_mm: tuple[float, float]
    ordinary_center_mm: tuple[float, float]
    entry_spacing_mm: float
    label_offset_mm: float = -4.5

    def __post_init__(self):
        values = np.asarray(
            (
                *self.title_position_mm,
                *self.bright_center_mm,
                *self.ordinary_center_mm,
                self.entry_spacing_mm,
                self.label_offset_mm,
            ),
            dtype=float,
        )
        if not np.all(np.isfinite(values)):
            raise ValueError("Magnitude-scale placement must be finite.")
        if self.entry_spacing_mm <= 0.0:
            raise ValueError("entry_spacing_mm must be positive.")


@dataclass(frozen=True)
class PolarMagnitudeScaleRequest:
    """Resolve the fixed classroom intervals through one stellar style."""

    title: str = "Magnitud"
    bright_cutoff_magnitude: float = 0.5

    def __post_init__(self):
        title = str(self.title).strip()
        cutoff = float(self.bright_cutoff_magnitude)
        if not title:
            raise ValueError("title must not be empty.")
        if not np.isfinite(cutoff):
            raise ValueError("bright_cutoff_magnitude must be finite.")
        if cutoff != 0.5:
            raise ValueError("The classroom polar scale uses a 0.5 cutoff.")
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "bright_cutoff_magnitude", cutoff)

    def resolve(self, stars, *, limiting_magnitude):
        """Return scale entries sized by the resolved polar stellar style."""
        if not isinstance(stars, StellarStyle):
            raise TypeError("stars must be a StellarStyle value.")
        limit = float(limiting_magnitude)
        if not np.isfinite(limit) or limit != 5.0:
            raise ValueError("The classroom polar scale requires limit 5.0.")
        if not stars.draw_bright_symbols:
            raise ValueError("The polar scale requires bright-star symbols.")
        if not np.isclose(
            stars.bright_magnitude_limit,
            self.bright_cutoff_magnitude,
            atol=1.0e-12,
        ):
            raise ValueError("Stellar style and magnitude-scale cutoff differ.")
        return PolarMagnitudeScale(
            title=self.title,
            limiting_magnitude=limit,
            bright_cutoff_magnitude=self.bright_cutoff_magnitude,
            bright_entries=_entries(_BRIGHT_INTERVALS, stars, "five_point"),
            ordinary_entries=_entries(_ORDINARY_INTERVALS, stars, "round"),
        )


def default_polar_magnitude_scale():
    """Resolve the packaged polar scale for physical product furniture."""
    from wenu.charts.polar_planisphere_style import (
        polar_planisphere_chart_style,
    )
    from wenu.configuration import (
        translate_geometry_detail_defaults,
        translate_style_mode_defaults,
    )

    styles = translate_style_mode_defaults()
    stars = polar_planisphere_chart_style(
        styles.atlas,
        styles.polar_planisphere_palette,
    ).stars
    limit = (
        translate_geometry_detail_defaults()
        .polar_planisphere_policy
        .star_magnitude_limit
    )
    return PolarMagnitudeScaleRequest().resolve(
        stars,
        limiting_magnitude=limit,
    )


def _entries(intervals, stars, symbol):
    entries = []
    for lower, upper in intervals:
        representative = (lower + upper) / 2.0
        ordinary, bright, mask = configured_stellar_symbol_sizes(
            (representative,),
            stars,
        )
        is_bright = symbol == "five_point"
        if bool(mask[0]) is not is_bright:
            raise ValueError("Magnitude interval does not match symbol cutoff.")
        area = bright[0] if is_bright else ordinary[0]
        entries.append(
            PolarMagnitudeScaleEntry(
                lower_magnitude=lower,
                upper_magnitude=upper,
                representative_magnitude=representative,
                label=f"{lower:.1f}..{upper:.1f}",
                symbol=symbol,
                marker_area_points2=float(area),
            )
        )
    return tuple(entries)
