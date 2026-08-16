"""Output-neutral contracts and adaptive chart-detail policies."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from math import isfinite, log, sqrt
from typing import Protocol, runtime_checkable

from .context import ChartContext
from .modes import ResolvedMode


COORDINATE_GRID_LAYERS = frozenset(
    {
        "altaz_grid",
        "equatorial_grid",
        "ecliptic_grid",
        "galactic_grid",
    }
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
        "milky_way",
        "magellanic_clouds",
        "galaxies",
        "globular_clusters",
        "open_clusters",
    }
)

POLAR_PLANISPHERE_CONTENT_LAYERS = frozenset(
    {
        "stars",
        "constellation_lines",
        "constellation_labels",
        "milky_way",
        "magellanic_clouds",
    }
)

CONSTELLATION_STAR_MODES = frozenset(
    {"selected", "visible", "all", "none"}
)


def _normalized_identifiers(values, *, field_name):
    if values is None:
        return None
    normalized = []
    for value in values:
        identifier = str(value).strip()
        if not identifier:
            raise ValueError(
                f"{field_name} cannot contain an empty identifier."
            )
        normalized.append(identifier)
    return frozenset(normalized)


def _normalized_levels(values, *, field_name, converter):
    if values is None:
        return None
    normalized = []
    for value in values:
        level = converter(value)
        if isinstance(level, str):
            level = level.strip()
            if not level:
                raise ValueError(
                    f"{field_name} cannot contain an empty level."
                )
        normalized.append(level)
    return frozenset(normalized)


@dataclass(frozen=True)
class SkyContentSelection:
    """Named astronomical content selected for one chart render.

    ``None`` preserves the registered layer's default selection. An empty
    set explicitly selects no members of that family. Catalogue identifiers
    retain their spelling; individual layers remain responsible for their
    established case-folding and alias rules.
    """

    constellation_lines: frozenset[str] | None = None
    constellation_boundaries: frozenset[str] | None = None
    constellation_labels: frozenset[str] | None = None
    nonstellar_objects: frozenset[str] | None = None
    galaxies: frozenset[str] | None = None
    open_clusters: frozenset[str] | None = None
    globular_clusters: frozenset[str] | None = None
    planetary_nebulae: frozenset[str] | None = None
    supernova_remnants: frozenset[str] | None = None
    milky_way_levels: frozenset[str] | None = None
    lmc_levels: frozenset[int] | None = None
    smc_levels: frozenset[int] | None = None

    def __post_init__(self):
        for name in (
            "constellation_lines",
            "constellation_boundaries",
            "constellation_labels",
            "nonstellar_objects",
            "galaxies",
            "open_clusters",
            "globular_clusters",
            "planetary_nebulae",
            "supernova_remnants",
        ):
            object.__setattr__(
                self,
                name,
                _normalized_identifiers(
                    getattr(self, name),
                    field_name=name,
                ),
            )
        object.__setattr__(
            self,
            "milky_way_levels",
            _normalized_levels(
                self.milky_way_levels,
                field_name="milky_way_levels",
                converter=str,
            ),
        )
        for name in ("lmc_levels", "smc_levels"):
            object.__setattr__(
                self,
                name,
                _normalized_levels(
                    getattr(self, name),
                    field_name=name,
                    converter=int,
                ),
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
    extended_object_samples: int | None = None
    label_density: float = 1.0
    enabled_layers: frozenset[str] | None = None
    grid_label_layers: frozenset[str] = frozenset()
    constellation_star_mode: str | None = None
    extra_star_ids: frozenset[int] = frozenset()
    content_selection: SkyContentSelection = SkyContentSelection()

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
        if self.extended_object_samples is not None:
            samples = int(self.extended_object_samples)
            if samples < 12:
                raise ValueError(
                    "extended_object_samples must be at least 12."
                )
            object.__setattr__(self, "extended_object_samples", samples)
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
                "grid_label_layers must contain only altaz_grid, "
                "equatorial_grid, ecliptic_grid, or galactic_grid."
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
        if not isinstance(self.content_selection, SkyContentSelection):
            raise TypeError(
                "content_selection must be a SkyContentSelection."
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
    extended_object_samples: int | None = None
    label_density: float | None = None
    enabled_layers: frozenset[str] | None = None
    grid_label_layers: frozenset[str] | None = None
    enabled_layer_additions: frozenset[str] | None = None
    disabled_layers: frozenset[str] | None = None
    constellation_star_mode: str | None = None
    extra_star_ids: frozenset[int] | None = None
    content_selection: SkyContentSelection | None = None

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
        if (
            self.content_selection is not None
            and not isinstance(
                self.content_selection,
                SkyContentSelection,
            )
        ):
            raise TypeError(
                "content_selection must be a SkyContentSelection or None."
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
class PolarPlanisphereDetailPolicy:
    """Sparse, projection-independent content for classroom star disks."""

    star_magnitude_limit: float = 5.5
    label_density: float = 1.0
    enabled_layers: frozenset[str] = POLAR_PLANISPHERE_CONTENT_LAYERS
    constellation_star_mode: str = "none"

    def __post_init__(self):
        magnitude = float(self.star_magnitude_limit)
        density = float(self.label_density)
        layers = frozenset(str(value) for value in self.enabled_layers)
        if not isfinite(magnitude):
            raise ValueError("star_magnitude_limit must be finite.")
        if not isfinite(density) or density <= 0.0:
            raise ValueError("label_density must be positive and finite.")
        if layers != POLAR_PLANISPHERE_CONTENT_LAYERS:
            raise ValueError(
                "enabled_layers must contain only the essential polar-"
                "planisphere stars, constellation lines and labels, "
                "Milky Way, and Magellanic Clouds."
            )
        if self.constellation_star_mode != "none":
            raise ValueError(
                "constellation_star_mode must be 'none' so magnitude 5.5 "
                "remains the complete stellar selection rule."
            )
        object.__setattr__(self, "star_magnitude_limit", magnitude)
        object.__setattr__(self, "label_density", density)
        object.__setattr__(self, "enabled_layers", layers)

    def resolve(
        self,
        context: ChartContext,
        mode: ResolvedMode,
    ) -> ResolvedDetail:
        """Return the same astronomical selection for either disk face."""
        del context, mode
        return ResolvedDetail(
            star_magnitude_limit=self.star_magnitude_limit,
            label_density=self.label_density,
            enabled_layers=self.enabled_layers,
            constellation_star_mode=self.constellation_star_mode,
        )


@dataclass(frozen=True)
class CartoonDetailPolicy:
    """Restrained educational-chart content, independent of visual style.

    The stellar catalogue is resolved as the union of constellation vertices,
    stars at or brighter than ``bright_star_magnitude_limit``, and
    ``extra_star_ids``.  The ordinary cartoon layer set may also include
    configured bright galaxies and large clusters; ``include_deep_sky``
    switches to the complete default layer set. Constellation identifiers are
    obtained later when the resolved detail is applied to a populated sphere.
    """

    constellation_star_mode: str = "selected"
    bright_star_magnitude_limit: float = 3.0
    extra_star_ids: frozenset[int] = frozenset()
    include_deep_sky: bool = False
    label_named_stars: bool = False
    galaxy_magnitude_limit: float = 8.0
    minimum_open_cluster_size_arcmin: float = 60.0
    minimum_globular_cluster_size_arcmin: float = 30.0
    default_content_layers: frozenset[str] = DEFAULT_CONTENT_LAYERS
    cartoon_content_layers: frozenset[str] = CARTOON_CONTENT_LAYERS

    def __post_init__(self) -> None:
        if self.constellation_star_mode not in CONSTELLATION_STAR_MODES:
            raise ValueError(
                "constellation_star_mode must be selected, visible, all, "
                "or none."
            )
        for name in (
            "bright_star_magnitude_limit",
            "galaxy_magnitude_limit",
            "minimum_open_cluster_size_arcmin",
            "minimum_globular_cluster_size_arcmin",
        ):
            value = float(getattr(self, name))
            if not isfinite(value):
                raise ValueError(f"{name} must be finite.")
            if name.startswith("minimum_") and value < 0.0:
                raise ValueError(f"{name} cannot be negative.")
        object.__setattr__(
            self,
            "extra_star_ids",
            frozenset(int(value) for value in self.extra_star_ids),
        )
        object.__setattr__(
            self,
            "default_content_layers",
            frozenset(str(value) for value in self.default_content_layers),
        )
        object.__setattr__(
            self,
            "cartoon_content_layers",
            frozenset(str(value) for value in self.cartoon_content_layers),
        )

    def resolve(
        self,
        context: ChartContext,
        mode: ResolvedMode,
    ) -> ResolvedDetail:
        del context, mode
        enabled = (
            self.default_content_layers
            if self.include_deep_sky
            else self.cartoon_content_layers
        )
        return ResolvedDetail(
            star_magnitude_limit=float(
                self.bright_star_magnitude_limit
            ),
            galaxy_magnitude_limit=float(self.galaxy_magnitude_limit),
            minimum_open_cluster_size_arcmin=float(
                self.minimum_open_cluster_size_arcmin
            ),
            minimum_globular_cluster_size_arcmin=float(
                self.minimum_globular_cluster_size_arcmin
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
    star_magnitude_limit: float | None = None
    default_content_layers: frozenset[str] = DEFAULT_CONTENT_LAYERS

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
        if (
            self.star_magnitude_limit is not None
            and not isfinite(float(self.star_magnitude_limit))
        ):
            raise ValueError("star_magnitude_limit must be finite.")
        object.__setattr__(self, "levels", levels)
        object.__setattr__(
            self,
            "default_content_layers",
            frozenset(str(value) for value in self.default_content_layers),
        )

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

    def _enabled_layers(self, span):
        layers = set(self.default_content_layers)
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
        if self.star_magnitude_limit is not None:
            values["star_magnitude_limit"] = float(
                self.star_magnitude_limit
            )
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
    *,
    default_content_layers=DEFAULT_CONTENT_LAYERS,
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
        default_content_layers
        if resolved.enabled_layers is None
        else resolved.enabled_layers
    )
    enabled.update(() if additions is None else additions)
    enabled.difference_update(() if removals is None else removals)
    return replace(resolved, enabled_layers=frozenset(enabled))
