"""Apply resolved chart detail to a populated celestial sphere."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .context import BoundaryKind
from .detail import ResolvedDetail


_SIZE_OPTIONS = {
    "open_clusters": "minimum_open_cluster_size_arcmin",
    "globular_clusters": "minimum_globular_cluster_size_arcmin",
    "planetary_nebulae": "minimum_planetary_nebula_size_arcmin",
    "supernova_remnants": "minimum_supernova_remnant_size_arcmin",
}


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


def _layer_option_names(layer):
    name = getattr(layer, "layer_name", None)
    if name is None:
        return ()
    return (name, *_LAYER_OPTION_ALIASES.get(name, ()))


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


def _composition_horizon_altitude(composition):
    context = getattr(composition, "context", None)
    boundary_kind = getattr(context, "boundary_kind", None)
    if boundary_kind == BoundaryKind.RECTANGULAR:
        return -90.0
    return None


def _refresh_magnitude_limit(layer, value):
    if layer is None or value is None:
        return False
    value = float(value)
    current = getattr(layer, "magnitude_limit", None)
    if current is not None and float(current) == value:
        return False
    layer.magnitude_limit = value
    loader = getattr(layer, "load", None)
    if not callable(loader):
        raise TypeError(
            f"{type(layer).__name__} has no load() method for applying "
            "a catalogue magnitude limit."
        )
    loader()
    return True


def _constellation_star_ids(sky, mode):
    if mode in (None, "none"):
        return frozenset()
    lines = getattr(sky, "constellation_lines", None)
    if lines is None:
        return frozenset()
    if mode in {"selected", "all"}:
        return lines.star_ids
    if mode == "visible":
        # Visibility clipping occurs after spherical geometry is created.
        # At this stage, use every resolvable vertex in the loaded figures;
        # the normal projection/viewport pipeline removes off-chart points.
        return lines.resolvable_star_ids
    raise ValueError(f"Unsupported constellation-star mode: {mode}")


def _refresh_star_selection(sky, detail):
    stars = getattr(sky, "stars", None)
    if stars is None or detail.constellation_star_mode is None:
        return False
    identifiers = _constellation_star_ids(
        sky,
        detail.constellation_star_mode,
    ).union(detail.extra_star_ids)
    configure = getattr(stars, "configure_selection", None)
    if not callable(configure):
        raise TypeError(
            "The stellar layer does not support configure_selection()."
        )
    return bool(configure(include_ids=identifiers, reload=True))


@dataclass(frozen=True)
class DetailApplication:
    """Result of applying a resolved detail policy to a sky."""

    layer_options: dict[Any, dict[str, Any]]
    reloaded_layers: tuple[str, ...] = ()


_DETAIL_LAYER_NAMES = {
    "milky_way_isophotes": "milky_way",
}


def _detail_layer_name(layer_name):
    """Return the semantic content-policy name for a registered layer."""
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
    reloaded = []
    if reload_catalogues:
        stars_reloaded = _refresh_magnitude_limit(
            getattr(sky, "stars", None),
            detail.star_magnitude_limit,
        )
        selection_reloaded = _refresh_star_selection(sky, detail)
        if stars_reloaded or selection_reloaded:
            reloaded.append("stars")
        if _refresh_magnitude_limit(
            getattr(sky, "galaxies", None),
            detail.galaxy_magnitude_limit,
        ):
            reloaded.append("galaxies")

    resolved_options = {}
    for layer in sky.layers:
        name = getattr(layer, "layer_name", None)
        if not name:
            continue
        configured = {
            "enabled": detail.layer_enabled(
                _detail_layer_name(name)
            ),
        }
        detail_field = _SIZE_OPTIONS.get(name)
        if detail_field is not None:
            minimum = getattr(detail, detail_field)
            if minimum is not None:
                configured["geometry"] = {
                    "minimum_size_arcmin": float(minimum),
                }
        resolved_options[name] = configured

    return DetailApplication(
        layer_options=merge_sky_layer_options(
            sky,
            base_layer_options,
            resolved_options,
            explicit_layer_options,
        ),
        reloaded_layers=tuple(reloaded),
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
        horizon_altitude_deg=_composition_horizon_altitude(
            composition
        ),
    )
    return apply_resolved_detail(
        sky,
        composition.detail,
        base_layer_options=base,
        explicit_layer_options=layer_options,
        reload_catalogues=reload_catalogues,
    )
