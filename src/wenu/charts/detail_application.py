"""Apply resolved chart detail to a populated celestial sphere."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from .context import BoundaryKind
from .detail import ResolvedDetail
from .style_components import StellarMagnitudeSizing
from wenu.rendering.preparation import configured_magnitude_sizes


_SIZE_OPTIONS = {
    "open_clusters": "minimum_open_cluster_size_arcmin",
    "globular_clusters": "minimum_globular_cluster_size_arcmin",
    "planetary_nebulae": "minimum_planetary_nebula_size_arcmin",
    "supernova_remnants": "minimum_supernova_remnant_size_arcmin",
}

_SELECTION_OPTIONS = {
    "nonstellar": "nonstellar_objects",
    "galaxies": "galaxies",
    "open_clusters": "open_clusters",
    "globular_clusters": "globular_clusters",
    "planetary_nebulae": "planetary_nebulae",
    "supernova_remnants": "supernova_remnants",
    "constellation_labels": "constellation_labels",
    "venus": "solar_system_objects",
    "moon": "solar_system_objects",
}


def configured_stellar_symbol_sizes(
    magnitudes,
    stars,
    *,
    limiting_magnitude=None,
):
    """Return ordinary areas, bright-star areas, and the bright mask."""
    values = np.asarray(magnitudes, dtype=float)
    sizing = stars.magnitude_sizing
    bright = (
        stars.draw_bright_symbols
        & (values <= stars.bright_magnitude_limit)
    )
    ordinary = configured_magnitude_sizes(
        values * stars.ordinary_magnitude_scale
        + stars.ordinary_magnitude_offset,
        sizing,
        limiting_magnitude=limiting_magnitude,
    ) * stars.area_scale
    ordinary = np.where(bright, 0.0, ordinary)
    highlighted = configured_magnitude_sizes(
        values * stars.bright_magnitude_scale
        + stars.bright_magnitude_offset,
        sizing,
        limiting_magnitude=limiting_magnitude,
    ) * stars.area_scale * stars.bright_symbol_area_scale
    return ordinary, highlighted, bright

_SAMPLED_OUTLINE_LAYERS = frozenset(
    {
        "nonstellar",
        "galaxies",
        "globular_clusters",
        "supernova_remnants",
    }
)


@dataclass(frozen=True)
class _LabelFormatter:
    """Value-semantic renderer adapter for curated object labels."""

    overrides: tuple[tuple[str, str | None], ...]

    def __call__(self, value):
        return dict(self.overrides).get(str(value).casefold(), value)


def _merge_mapping(base, overlay):
    merged = dict(base)
    for key, value in overlay.items():
        if (
            key in merged
            and isinstance(merged[key], Mapping)
            and isinstance(value, Mapping)
        ):
            merged[key] = _merge_mapping(merged[key], value)
        else:
            merged[key] = value
    return merged


def merge_layer_options(*sources):
    """Deep-merge layer options from left to right."""
    merged = {}
    for source in sources:
        if source is not None:
            merged = _merge_mapping(merged, source)
    return merged


_LAYER_OPTION_ALIASES = {
    "milky_way_isophotes": ("milky_way",),
}

_GRID_DETAIL_LAYER_NAMES = {
    "altaz": "altaz_grid",
    "equatorial": "equatorial_grid",
    "ecliptic": "ecliptic_grid",
    "galactic": "galactic_grid",
}


def _layer_option_names(layer):
    name = getattr(layer, "layer_name", None)
    if name is None:
        return ()
    aliases = list(_LAYER_OPTION_ALIASES.get(name, ()))
    grid_name = _GRID_DETAIL_LAYER_NAMES.get(
        getattr(layer, "coordinate_system", None)
    )
    if name == "coordinates_grid" and grid_name is not None:
        aliases.append(grid_name)
    return (name, *aliases)


def _is_hashable(value):
    try:
        hash(value)
    except TypeError:
        return False
    return True


def merge_sky_layer_options(sky, *sources):
    """Merge semantic, registered-name, and object-keyed layer options.

    Source precedence remains left-to-right. Within one source, semantic
    aliases are applied first, the registered layer name second, and the
    layer object last.
    """
    sources = tuple(source for source in sources if source is not None)
    merged = {}
    consumed = set()
    for layer in sky.layers:
        names = _layer_option_names(layer)
        registered_name = names[0] if names else None
        aliases = names[1:]
        resolved = {}
        found = False
        layer_is_hashable = _is_hashable(layer)
        for source in sources:
            for name in (*aliases, registered_name):
                if name is not None and name in source:
                    resolved = _merge_mapping(resolved, source[name])
                    consumed.add(name)
                    found = True
            if layer_is_hashable and layer in source:
                resolved = _merge_mapping(resolved, source[layer])
                consumed.add(layer)
                found = True
        if found:
            if layer_is_hashable:
                merged[layer] = resolved
            for name in names:
                merged[name] = resolved
    for source in sources:
        for key, value in source.items():
            if key not in consumed:
                merged[key] = _merge_mapping(
                    merged.get(key, {}),
                    value,
                )
    return merged


def _style_layer_options(
    style,
    sky,
    *,
    horizon_altitude_deg=None,
):
    resolved = (
        style.as_publication_style()
        if callable(getattr(style, "as_publication_style", None))
        else style
    )
    factory = getattr(resolved, "layer_options", None)
    if not callable(factory):
        return {}
    if horizon_altitude_deg is None:
        return factory(sky)
    return factory(
        sky,
        horizon_altitude_deg=horizon_altitude_deg,
    )


def composition_horizon_altitude(composition):
    """Return the single resolved layer-clipping altitude for a chart."""
    context = getattr(composition, "context", None)
    configured = getattr(context, "horizon_altitude_deg", None)
    if configured is not None:
        return float(configured)
    boundary_kind = getattr(context, "boundary_kind", None)
    if boundary_kind == BoundaryKind.RECTANGULAR:
        return -90.0
    return None


@dataclass(frozen=True)
class DetailApplication:
    """Result of applying a resolved detail policy to a sky."""

    layer_options: dict[Any, dict[str, Any]]
    reloaded_layers: tuple[str, ...] = ()


_DETAIL_LAYER_NAMES = {
    "nonstellar": "nonstellar_objects",
    "milky_way_isophotes": "milky_way",
    "magellanic_cloud_isophotes": "magellanic_clouds",
}

_REQUEST_GEOMETRY_LAYERS = frozenset({"horizon"})
_DEFAULT_DISABLED_LAYERS = frozenset({"venus", "moon"})


def _detail_layer_name(layer):
    """Return the semantic content-policy name for a registered layer."""
    layer_name = getattr(layer, "layer_name", None)
    if layer_name == "coordinates_grid":
        coordinate_system = getattr(layer, "coordinate_system", None)
        return _GRID_DETAIL_LAYER_NAMES.get(
            coordinate_system,
            "coordinate_grids",
        )
    return _DETAIL_LAYER_NAMES.get(layer_name, layer_name)


def apply_resolved_detail(
    sky,
    detail: ResolvedDetail,
    *,
    base_layer_options=None,
    explicit_layer_options=None,
    reload_catalogues=True,
) -> DetailApplication:
    """Apply catalogue limits and return effective layer options.

    Precedence is:

    1. style/base options;
    2. resolved detail;
    3. explicit call-site options.

    This function never adds or removes registered layers. Disabled layers
    remain in the sky and are skipped by the canonical rendering pipeline.
    """
    # Kept as a compatibility argument while catalogue selection moves from
    # persistent layer mutation to render-local geometry options.
    del reload_catalogues

    label_overrides = {}
    for family, identifier, label in getattr(
        detail, "content_label_overrides", ()
    ):
        label_overrides.setdefault(family, {})[
            identifier.casefold()
        ] = label

    resolved_options = {}
    for layer in sky.layers:
        name = getattr(layer, "layer_name", None)
        if not name:
            continue
        configured = {
            "enabled": (
                True
                if name in _REQUEST_GEOMETRY_LAYERS
                else (
                    False
                    if (
                        name in _DEFAULT_DISABLED_LAYERS
                        and detail.enabled_layers is None
                    )
                    else detail.layer_enabled(_detail_layer_name(layer))
                )
            ),
        }
        detail_name = _detail_layer_name(layer)
        if detail_name in _GRID_DETAIL_LAYER_NAMES.values():
            configured["render"] = {
                "draw_labels": detail_name in detail.grid_label_layers,
            }
        geometry = {}
        if name == "stars":
            if detail.star_magnitude_limit is not None:
                geometry["magnitude_limit"] = float(
                    detail.star_magnitude_limit
                )
            if detail.constellation_star_mode is not None:
                geometry["include_ids"] = detail.extra_star_ids
                geometry["include_constellation_vertices"] = (
                    detail.constellation_star_mode != "none"
                )
        elif name == "galaxies" and detail.galaxy_magnitude_limit is not None:
            geometry["magnitude_limit"] = float(
                detail.galaxy_magnitude_limit
            )
        detail_field = _SIZE_OPTIONS.get(name)
        if detail_field is not None:
            minimum = getattr(detail, detail_field)
            if minimum is not None:
                geometry["minimum_size_arcmin"] = float(minimum)
        if (
            name in _SAMPLED_OUTLINE_LAYERS
            and detail.extended_object_samples is not None
        ):
            geometry["samples"] = detail.extended_object_samples
        selection_field = _SELECTION_OPTIONS.get(name)
        if selection_field is not None:
            selected = getattr(
                detail.content_selection,
                selection_field,
            )
            if selected is not None:
                geometry["selected"] = selected
        overrides = label_overrides.get(detail_name)
        if overrides:
            configured["render"] = {
                **configured.get("render", {}),
                "label_formatter": _LabelFormatter(
                    tuple(sorted(overrides.items()))
                ),
            }
        selection = detail.content_selection
        if name == "constellation_lines":
            selected = selection.constellation_lines
            if selected is not None:
                geometry["selected"] = selected
        elif name == "constellation_boundaries":
            selected = selection.constellation_boundaries
            if selected is not None:
                geometry["selected"] = selected
        elif name == "milky_way_isophotes":
            levels = selection.milky_way_levels
            if levels is not None:
                geometry["levels"] = levels
        elif name == "magellanic_cloud_isophotes":
            field = f"{getattr(layer, 'cloud', '')}_levels"
            levels = getattr(selection, field, None)
            if levels is not None:
                geometry["levels"] = levels
        if geometry:
            configured["geometry"] = geometry
        resolved_options[
            layer if _is_hashable(layer) else name
        ] = configured

    return DetailApplication(
        layer_options=merge_sky_layer_options(
            sky,
            base_layer_options,
            resolved_options,
            explicit_layer_options,
        ),
        reloaded_layers=(),
    )


def composition_layer_options(
    composition,
    sky,
    *,
    layer_options=None,
    reload_catalogues=True,
):
    """Return rendering options for a resolved chart composition."""
    base = _style_layer_options(
        composition.style,
        sky,
        horizon_altitude_deg=composition_horizon_altitude(
            composition
        ),
    )
    stars = getattr(composition.style, "stars", None)
    sizing = getattr(stars, "magnitude_sizing", None)
    if (
        getattr(sky, "stars", None) is not None
        and sizing is not None
        and (
            sizing != StellarMagnitudeSizing()
            or stars.draw_bright_symbols
        )
    ):
        limit = (
            composition.detail.star_magnitude_limit
            if sizing.reference == "limiting_magnitude"
            else None
        )
        if sizing.reference == "limiting_magnitude" and limit is None:
            raise ValueError(
                "Normalized stellar sizing requires a magnitude limit."
            )
        publication = composition.style.as_publication_style()

        def render_stars(spherical, projected):
            ordinary_sizes, bright_sizes, _ = (
                configured_stellar_symbol_sizes(
                    spherical.metadata["magnitude"],
                    stars,
                    limiting_magnitude=limit,
                )
            )
            return publication._star_render_options(
                spherical,
                projected,
                star_sizes=ordinary_sizes,
                bright_star_sizes=bright_sizes,
            )

        base = merge_sky_layer_options(
            sky,
            base,
            {"stars": {"render": render_stars}},
        )
    return apply_resolved_detail(
        sky,
        composition.detail,
        base_layer_options=base,
        explicit_layer_options=layer_options,
        reload_catalogues=reload_catalogues,
    )
