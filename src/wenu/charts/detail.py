"""Output-neutral contracts and adaptive chart-detail policies."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from math import isfinite, log, sqrt
from typing import Protocol, runtime_checkable

from .context import ChartContext
from .modes import ResolvedMode


COORDINATE_GRID_LAYERS = frozenset(
    {"equatorial_grid", "ecliptic_grid", "galactic_grid"}
)


DEFAULT_CONTENT_LAYERS = frozenset(
    {
        "stars",
        "constellation_lines",
        "constellation_labels",
        "constellation_boundaries",
        *COORDINATE_GRID_LAYERS,
        "milky_way",
        "magellanic_clouds",
        "galaxies",
        "globular_clusters",
        "open_clusters",
        "planetary_nebulae",
        "supernova_remnants",
    }
)

CARTOON_CONTENT_LAYERS = frozenset(
    {
        "stars",
        "constellation_lines",
        "constellation_labels",
    }
)

CONSTELLATION_STAR_MODES = frozenset(
    {"selected", "visible", "all", "none"}
)


@dataclass(frozen=True)
class ResolvedDetail:
    """Effective catalogue, size, labeling, and layer limits."""

    star_magnitude_limit: float | None = None
    galaxy_magnitude_limit: float | None = None
    minimum_open_cluster_size_arcmin: float | None = None
    minimum_globular_cluster_size_arcmin: float | None = None
    minimum_planetary_nebula_size_arcmin: float | None = None
    minimum_supernova_remnant_size_arcmin: float | None = None
    label_density: float = 1.0
    enabled_layers: frozenset[str] | None = None
    grid_label_layers: frozenset[str] = frozenset()
    constellation_star_mode: str | None = None
    extra_star_ids: frozenset[int] = frozenset()

    def __post_init__(self) -> None:
        numeric_names = (
            "star_magnitude_limit",
            "galaxy_magnitude_limit",
            "minimum_open_cluster_size_arcmin",
            "minimum_globular_cluster_size_arcmin",
            "minimum_planetary_nebula_size_arcmin",
            "minimum_supernova_remnant_size_arcmin",
            "label_density",
        )
        for name in numeric_names:
            value = getattr(self, name)
            if value is None:
                continue
            if not isfinite(float(value)):
                raise ValueError(f"{name} must be finite.")
            if name.startswith("minimum_") and float(value) < 0.0:
                raise ValueError(f"{name} cannot be negative.")
        if self.label_density <= 0.0:
            raise ValueError("label_density must be positive.")
        if self.enabled_layers is not None:
            normalized = frozenset(
                str(name).strip()
                for name in self.enabled_layers
                if str(name).strip()
            )
            if not normalized:
                raise ValueError("enabled_layers cannot be empty.")
            object.__setattr__(self, "enabled_layers", normalized)
        labels = frozenset(
            str(name).strip()
            for name in self.grid_label_layers
            if str(name).strip()
        )
        unknown_labels = labels - COORDINATE_GRID_LAYERS
        if unknown_labels:
            raise ValueError(
                "grid_label_layers must contain only equatorial_grid, "
                "ecliptic_grid, or galactic_grid."
            )
        object.__setattr__(self, "grid_label_layers", labels)
        if (
            self.constellation_star_mode is not None
            and self.constellation_star_mode not in CONSTELLATION_STAR_MODES
        ):
            raise ValueError(
                "constellation_star_mode must be selected, visible, all, "
                "none, or None."
            )
        object.__setattr__(
            self,
            "extra_star_ids",
            frozenset(int(value) for value in self.extra_star_ids),
        )

    def layer_enabled(self, name: str) -> bool:
        """Return whether a semantic layer is enabled."""
        if self.enabled_layers is None:
            return True
        name = str(name)
        if name in self.enabled_layers:
            return True
        if name == "coordinate_grids":
            return bool(self.enabled_layers & COORDINATE_GRID_LAYERS)
        if name in COORDINATE_GRID_LAYERS:
            return "coordinate_grids" in self.enabled_layers
        return False


@dataclass(frozen=True)
class DetailOverrides:
    """Explicit call-site overrides; ``None`` preserves policy results."""

    star_magnitude_limit: float | None = None
    galaxy_magnitude_limit: float | None = None
    minimum_open_cluster_size_arcmin: float | None = None
    minimum_globular_cluster_size_arcmin: float | None = None
    minimum_planetary_nebula_size_arcmin: float | None = None
    minimum_supernova_remnant_size_arcmin: float | None = None
    label_density: float | None = None
    enabled_layers: frozenset[str] | None = None
    grid_label_layers: frozenset[str] | None = None
    enabled_layer_additions: frozenset[str] | None = None
    disabled_layers: frozenset[str] | None = None
    constellation_star_mode: str | None = None
    extra_star_ids: frozenset[int] | None = None

    def __post_init__(self):
        for name in (
            "enabled_layers",
            "grid_label_layers",
            "enabled_layer_additions",
            "disabled_layers",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(
                    self,
                    name,
                    frozenset(
                        str(item).strip()
                        for item in value
                        if str(item).strip()
                    ),
                )


@runtime_checkable
class DetailPolicy(Protocol):
    """Protocol implemented by adaptive and special-purpose policies."""

    def resolve(
        self,
        context: ChartContext,
        mode: ResolvedMode,
    ) -> ResolvedDetail:
        """Return effective limits for ``context`` and ``mode``."""


@dataclass(frozen=True)
class FixedDetailPolicy:
    """Compatibility policy returning explicitly supplied fixed values."""

    detail: ResolvedDetail = ResolvedDetail()

    def resolve(
        self,
        context: ChartContext,
        mode: ResolvedMode,
    ) -> ResolvedDetail:
        del context, mode
        return self.detail


@dataclass(frozen=True)
class CartoonDetailPolicy:
    """Sparse educational-chart content, independent of visual style.

    The stellar catalogue is resolved as the union of constellation vertices,
    stars at or brighter than ``bright_star_magnitude_limit``, and
    ``extra_star_ids``.  Constellation identifiers are obtained later when
    the resolved detail is applied to a populated celestial sphere.
    """

    constellation_star_mode: str = "selected"
    bright_star_magnitude_limit: float = 3.0
    extra_star_ids: frozenset[int] = frozenset()
    include_deep_sky: bool = False
    label_named_stars: bool = False

    def __post_init__(self) -> None:
        if self.constellation_star_mode not in CONSTELLATION_STAR_MODES:
            raise ValueError(
                "constellation_star_mode must be selected, visible, all, "
                "or none."
            )
        if not isfinite(float(self.bright_star_magnitude_limit)):
            raise ValueError(
                "bright_star_magnitude_limit must be finite."
            )
        object.__setattr__(
            self,
            "extra_star_ids",
            frozenset(int(value) for value in self.extra_star_ids),
        )

    def resolve(
        self,
        context: ChartContext,
        mode: ResolvedMode,
    ) -> ResolvedDetail:
        del context, mode
        enabled = (
            DEFAULT_CONTENT_LAYERS
            if self.include_deep_sky
            else CARTOON_CONTENT_LAYERS
        )
        return ResolvedDetail(
            star_magnitude_limit=float(
                self.bright_star_magnitude_limit
            ),
            label_density=1.0,
            enabled_layers=enabled,
            constellation_star_mode=self.constellation_star_mode,
            extra_star_ids=self.extra_star_ids,
        )


@dataclass(frozen=True)
class FieldDetailLevel:
    """One control point in an adaptive field-size profile."""

    field_span_deg: float
    star_magnitude_limit: float
    galaxy_magnitude_limit: float
    minimum_open_cluster_size_arcmin: float
    minimum_globular_cluster_size_arcmin: float
    minimum_planetary_nebula_size_arcmin: float
    minimum_supernova_remnant_size_arcmin: float
    label_density: float

    def __post_init__(self) -> None:
        for item in fields(self):
            value = float(getattr(self, item.name))
            if not isfinite(value) or value <= 0.0:
                raise ValueError(
                    f"{item.name} must be positive and finite."
                )


DEFAULT_FIELD_DETAIL_LEVELS = (
    FieldDetailLevel(3.0, 12.0, 12.0, 0.5, 0.2, 0.1, 0.5, 1.30),
    FieldDetailLevel(6.5, 11.0, 12.0, 1.0, 0.5, 0.2, 1.0, 1.20),
    FieldDetailLevel(15.0, 9.5, 11.8, 2.0, 1.0, 0.5, 2.0, 1.05),
    FieldDetailLevel(30.0, 8.2, 11.5, 4.0, 2.0, 1.0, 4.0, 0.90),
    FieldDetailLevel(60.0, 7.2, 11.0, 8.0, 4.0, 2.0, 8.0, 0.72),
    FieldDetailLevel(100.0, 6.5, 10.5, 15.0, 8.0, 4.0, 15.0, 0.55),
    FieldDetailLevel(180.0, 6.0, 10.0, 30.0, 15.0, 8.0, 30.0, 0.40),
)


@dataclass(frozen=True)
class AdaptiveDetailPolicy:
    """Interpolate chart detail from visible field and output capacity.

    Field coverage is the primary control.  Output size makes only a small
    bounded correction, preventing a large export from silently changing the
    scientific content by several magnitudes.
    """

    levels: tuple[FieldDetailLevel, ...] = DEFAULT_FIELD_DETAIL_LEVELS
    reference_width_inches: float = 7.0
    output_magnitude_adjustment_per_octave: float = 0.20
    maximum_output_magnitude_adjustment: float = 0.50
    adapt_enabled_layers: bool = True

    def __post_init__(self) -> None:
        levels = tuple(
            sorted(self.levels, key=lambda level: level.field_span_deg)
        )
        if len(levels) < 2:
            raise ValueError("Adaptive detail requires at least two levels.")
        spans = [level.field_span_deg for level in levels]
        if len(set(spans)) != len(spans):
            raise ValueError("Field-detail spans must be unique.")
        if self.reference_width_inches <= 0.0:
            raise ValueError("reference_width_inches must be positive.")
        if self.maximum_output_magnitude_adjustment < 0.0:
            raise ValueError(
                "maximum_output_magnitude_adjustment cannot be negative."
            )
        object.__setattr__(self, "levels", levels)

    @staticmethod
    def field_span_deg(context: ChartContext) -> float:
        """Return an equivalent-square angular span for the visible field."""
        area = (
            context.visible_solid_angle_sq_deg
            if context.visible_solid_angle_sq_deg is not None
            else context.angular_area_deg2
        )
        return sqrt(float(area))

    def _bracket(self, span):
        if span <= self.levels[0].field_span_deg:
            return self.levels[0], self.levels[0], 0.0
        if span >= self.levels[-1].field_span_deg:
            return self.levels[-1], self.levels[-1], 0.0
        for lower, upper in zip(self.levels, self.levels[1:]):
            if lower.field_span_deg <= span <= upper.field_span_deg:
                fraction = (
                    log(span) - log(lower.field_span_deg)
                ) / (
                    log(upper.field_span_deg)
                    - log(lower.field_span_deg)
                )
                return lower, upper, fraction
        raise RuntimeError("Could not bracket field-detail span.")

    @staticmethod
    def _interpolate(lower, upper, fraction, name):
        start = float(getattr(lower, name))
        stop = float(getattr(upper, name))
        return start + fraction * (stop - start)

    def _output_magnitude_adjustment(self, mode):
        effective_width = (
            mode.width_inches
            / max(float(mode.font_scale), float(mode.symbol_scale))
        )
        octave = log(
            effective_width / self.reference_width_inches,
            2.0,
        )
        adjustment = (
            octave * self.output_magnitude_adjustment_per_octave
        )
        bound = self.maximum_output_magnitude_adjustment
        return max(-bound, min(bound, adjustment))

    @staticmethod
    def _enabled_layers(span):
        layers = set(DEFAULT_CONTENT_LAYERS)
        if span > 120.0:
            layers -= {
                "planetary_nebulae",
                "supernova_remnants",
                "open_clusters",
            }
        elif span > 75.0:
            layers -= {
                "planetary_nebulae",
                "supernova_remnants",
            }
        elif span > 40.0:
            layers -= {"planetary_nebulae"}
        return frozenset(layers)

    def resolve(
        self,
        context: ChartContext,
        mode: ResolvedMode,
    ) -> ResolvedDetail:
        span = self.field_span_deg(context)
        lower, upper, fraction = self._bracket(span)
        names = (
            "star_magnitude_limit",
            "galaxy_magnitude_limit",
            "minimum_open_cluster_size_arcmin",
            "minimum_globular_cluster_size_arcmin",
            "minimum_planetary_nebula_size_arcmin",
            "minimum_supernova_remnant_size_arcmin",
            "label_density",
        )
        values = {
            name: self._interpolate(
                lower,
                upper,
                fraction,
                name,
            )
            for name in names
        }
        output_adjustment = self._output_magnitude_adjustment(mode)
        values["star_magnitude_limit"] += output_adjustment
        values["galaxy_magnitude_limit"] += 0.5 * output_adjustment
        values["label_density"] *= (
            mode.width_inches / self.reference_width_inches
        ) ** 0.25
        values["enabled_layers"] = (
            self._enabled_layers(span)
            if self.adapt_enabled_layers
            else None
        )
        return ResolvedDetail(**values)


def apply_detail_overrides(
    detail: ResolvedDetail,
    overrides: DetailOverrides | None,
) -> ResolvedDetail:
    """Apply non-``None`` explicit values with deterministic precedence."""
    if overrides is None:
        return detail
    layer_fields = {"enabled_layer_additions", "disabled_layers"}
    changes = {
        item.name: getattr(overrides, item.name)
        for item in fields(overrides)
        if item.name not in layer_fields
        and getattr(overrides, item.name) is not None
    }
    resolved = replace(detail, **changes)
    additions = overrides.enabled_layer_additions
    removals = overrides.disabled_layers
    if additions is None and removals is None:
        return resolved
    enabled = set(
        DEFAULT_CONTENT_LAYERS
        if resolved.enabled_layers is None
        else resolved.enabled_layers
    )
    enabled.update(() if additions is None else additions)
    enabled.difference_update(() if removals is None else removals)
    return replace(resolved, enabled_layers=frozenset(enabled))
