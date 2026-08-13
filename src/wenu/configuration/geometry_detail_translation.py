"""Translate validated TOML values into geometry and detail contracts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
from types import MappingProxyType
from typing import Any, Mapping

from wenu.charts.detail import (
    AdaptiveDetailPolicy,
    CartoonDetailPolicy,
    FieldDetailLevel,
    FixedDetailPolicy,
    ResolvedDetail,
)
from wenu.charts.style_components import StellarMagnitudeSizing
from wenu.charts.view_defaults import ChartViewDefaults

from .validation import (
    ConfigurationError,
    load_packaged_defaults,
    validate_configuration,
)


_VIEW_CONTRACTS = {
    "all_sky": ("all_sky", "complete-sphere"),
    "planisphere": ("planisphere", "visible-hemisphere"),
    "regional_single": ("regional", "constellation-geometry"),
    "regional_group": ("regional", "packaged-group"),
    "circumpolar": ("circumpolar", "declination-limit"),
    "binocular": ("binocular", "fixed-diameter"),
}


@dataclass(frozen=True)
class GeometryDetailDefaults:
    """Existing immutable geometry and detail contracts translated from TOML."""

    view_defaults: Mapping[str, ChartViewDefaults]
    neutral_detail: ResolvedDetail
    default_content_layers: frozenset[str]
    cartoon_content_layers: frozenset[str]
    cartoon_policy: CartoonDetailPolicy
    adaptive_policy: AdaptiveDetailPolicy
    family_atlas_policies: Mapping[str, AdaptiveDetailPolicy]
    binocular_globular_policy: FixedDetailPolicy
    binocular_other_policy: FixedDetailPolicy
    binocular_stellar_sizing: StellarMagnitudeSizing


def _optional(value):
    return None if value == "none" else value


def _views(configuration: Mapping[str, Any]):
    translated = {}
    for name, table in configuration["families"].items():
        family, framing = _VIEW_CONTRACTS[name]
        if name in {"regional_single", "regional_group"} and (
            table["width"] != "none" or table["height"] != "none"
        ):
            raise ConfigurationError(
                f"families.{name}.width: explicit width and height cannot "
                "translate until Milestone 46D.4 adds them to the runtime "
                "view-default contract"
            )
        key = name.replace("_", "-") if name.startswith("regional_") else name
        translated[key] = ChartViewDefaults(
            family=family,
            framing=framing,
            projection=table["projection"],
            coordinate_frame=table["coordinate_frame"],
            position_angle_deg=table["position_angle"],
            mask=table["mask"],
            field_diameter_deg=(
                table["field_diameter"] if name == "binocular" else None
            ),
            pole=table["pole"] if name == "circumpolar" else None,
            limiting_declination_deg=(
                table["limiting_declination"]
                if name == "circumpolar"
                else None
            ),
        )
    return MappingProxyType(translated)


def _resolved_detail(table: Mapping[str, Any]) -> ResolvedDetail:
    return ResolvedDetail(
        star_magnitude_limit=_optional(table["star_magnitude_limit"]),
        galaxy_magnitude_limit=_optional(table["galaxy_magnitude_limit"]),
        minimum_open_cluster_size_arcmin=_optional(
            table["open_cluster_minimum_size"]
        ),
        minimum_globular_cluster_size_arcmin=_optional(
            table["globular_cluster_minimum_size"]
        ),
        minimum_planetary_nebula_size_arcmin=_optional(
            table["planetary_nebula_minimum_size"]
        ),
        minimum_supernova_remnant_size_arcmin=_optional(
            table["supernova_remnant_minimum_size"]
        ),
        extended_object_samples=_optional(table["extended_samples"]),
        label_density=table["label_density"],
        enabled_layers=(
            None
            if table["enabled_layers"] == "none"
            else frozenset(table["enabled_layers"])
        ),
        grid_label_layers=frozenset(table["grid_label_layers"]),
        constellation_star_mode=_optional(
            table["constellation_star_mode"]
        ),
        extra_star_ids=frozenset(table["extra_stars"]),
    )


def _adaptive(
    table: Mapping[str, Any],
    *,
    default_content_layers: frozenset[str],
) -> AdaptiveDetailPolicy:
    levels = tuple(
        FieldDetailLevel(
            level["span"],
            level["stars"],
            level["galaxies"],
            level["open_clusters"],
            level["globular_clusters"],
            level["planetary_nebulae"],
            level["supernova_remnants"],
            level["label_density"],
        )
        for level in table["levels"]
    )
    return AdaptiveDetailPolicy(
        levels=levels,
        reference_width_inches=table["reference_width"],
        output_magnitude_adjustment_per_octave=(
            table["magnitude_adjustment_per_octave"]
        ),
        maximum_output_magnitude_adjustment=table["maximum_adjustment"],
        adapt_enabled_layers=table["adapt_layers"],
        default_content_layers=default_content_layers,
    )


def translate_geometry_detail_defaults(
    configuration: Mapping[str, Any] | None = None,
) -> GeometryDetailDefaults:
    """Translate validated values into immutable geometry/detail contracts."""
    values = (
        load_packaged_defaults()
        if configuration is None
        else validate_configuration(configuration)
    )
    detail = values["detail"]
    content = detail["content"]
    default_content_layers = frozenset(content["default_layers"])
    cartoon_content_layers = frozenset(content["cartoon_layers"])
    cartoon = detail["cartoon"]
    adaptive = _adaptive(
        detail["adaptive"],
        default_content_layers=default_content_layers,
    )
    canonical = detail["canonical"]
    family_policies = MappingProxyType({
        name: replace(
            adaptive,
            star_magnitude_limit=canonical[f"{name}_star_limit"],
        )
        for name in ("all_sky", "planisphere", "regional", "circumpolar")
    })
    binocular_common = {
        "star_magnitude_limit": canonical["binocular_star_limit"],
        "galaxy_magnitude_limit": canonical["binocular_galaxy_limit"],
    }
    sizing = detail["binocular_stellar_sizing"]
    return GeometryDetailDefaults(
        view_defaults=_views(values),
        neutral_detail=_resolved_detail(detail["neutral"]),
        default_content_layers=default_content_layers,
        cartoon_content_layers=cartoon_content_layers,
        cartoon_policy=CartoonDetailPolicy(
            constellation_star_mode=cartoon["star_mode"],
            bright_star_magnitude_limit=cartoon["bright_limit"],
            extra_star_ids=frozenset(cartoon["extra_stars"]),
            include_deep_sky=cartoon["deep_sky"],
            label_named_stars=cartoon["named_star_labels"],
            default_content_layers=default_content_layers,
            cartoon_content_layers=cartoon_content_layers,
        ),
        adaptive_policy=adaptive,
        family_atlas_policies=family_policies,
        binocular_globular_policy=FixedDetailPolicy(ResolvedDetail(
            **binocular_common,
            extended_object_samples=canonical["binocular_globular_samples"],
        )),
        binocular_other_policy=FixedDetailPolicy(ResolvedDetail(
            **binocular_common,
            extended_object_samples=canonical["binocular_other_samples"],
        )),
        binocular_stellar_sizing=StellarMagnitudeSizing(
            reference=sizing["reference"],
            scale=sizing["scale"],
            exponent=sizing["exponent"],
            minimum_area=sizing["minimum_area"],
            maximum_area=sizing["maximum_area"],
        ),
    )


@lru_cache(maxsize=1)
def packaged_geometry_detail_defaults() -> GeometryDetailDefaults:
    """Return immutable packaged geometry/detail authority once per process."""
    return translate_geometry_detail_defaults()
