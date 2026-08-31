"""Renderer-neutral semantic identity for chart layers."""

from __future__ import annotations

from dataclasses import dataclass
import re

from wenu.chart_document import EditPolicy


_SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_SAFE_PATH_COMPONENT = _SAFE_NAME


def semantic_key(
    value,
    *,
    field: str,
    numeric_prefix: str | None = None,
) -> str:
    """Return one safe stable key supplied by a semantic data source."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string.")
    key = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if key[:1].isdigit() and numeric_prefix is not None:
        if _SAFE_NAME.fullmatch(numeric_prefix) is None:
            raise ValueError(
                f"{field} numeric prefix {numeric_prefix!r} is not safe."
            )
        key = f"{numeric_prefix}_{key}"
    if _SAFE_NAME.fullmatch(key) is None:
        raise ValueError(f"{field} {value!r} has no safe semantic key.")
    return key


def _path_display_name(value: str) -> str:
    words = value.replace("_", " ").split()
    return " ".join(
        word if word in {"and", "of"} else word.capitalize()
        for word in words
    )


@dataclass(frozen=True)
class SemanticLayerContract:
    """Sky-owned hierarchy and presentation metadata for one layer."""

    path: tuple[str, ...]
    display_name: str
    presentation_order: int
    style_role: str


@dataclass(frozen=True)
class SemanticComponentContract:
    """Semantic identity for one renderer-declared part of a sky layer."""

    path_component: str
    display_name: str
    style_role_suffix: str
    edit_policy: EditPolicy


_GRID_COMPONENT_CONTRACTS = {
    "lines": SemanticComponentContract(
        "lines", "lines", "lines", EditPolicy.STYLE
    ),
    "labels": SemanticComponentContract(
        "labels", "labels", "labels", EditPolicy.LAYOUT
    ),
}


_NONSTELLAR_CATEGORY_CONTRACTS = {
    "galaxies": SemanticLayerContract(
        ("sky", "galaxies"), "Galaxies", 10, "galaxies"
    ),
    "open_clusters": SemanticLayerContract(
        ("sky", "deep_sky_objects", "open_clusters"),
        "Open clusters",
        30,
        "open_clusters",
    ),
    "globular_clusters": SemanticLayerContract(
        ("sky", "deep_sky_objects", "globular_clusters"),
        "Globular clusters",
        31,
        "globular_clusters",
    ),
    "planetary_nebulae": SemanticLayerContract(
        ("sky", "deep_sky_objects", "planetary_nebulae"),
        "Planetary nebulae",
        32,
        "planetary_nebulae",
    ),
    "supernova_remnants": SemanticLayerContract(
        ("sky", "deep_sky_objects", "supernova_remnants"),
        "Supernova remnants",
        33,
        "supernova_remnants",
    ),
    "nebulae": SemanticLayerContract(
        ("sky", "deep_sky_objects", "nebulae"),
        "Nebulae",
        34,
        "nebulae",
    ),
    "other_objects": SemanticLayerContract(
        ("sky", "deep_sky_objects", "other_objects"),
        "Other objects",
        35,
        "nonstellar",
    ),
}


_LAYER_CONTRACTS = {
    "venus_disk_illuminated": SemanticLayerContract(
        ("sky", "solar_system", "planets", "venus", "disk", "illuminated"),
        "Venus illuminated face",
        38,
        "planet_disk_illuminated",
    ),
    "venus_disk_terminator": SemanticLayerContract(
        ("sky", "solar_system", "planets", "venus", "disk", "terminator"),
        "Venus terminator",
        38,
        "planet_disk_terminator",
    ),
    "venus_disk_limb": SemanticLayerContract(
        ("sky", "solar_system", "planets", "venus", "disk", "limb"),
        "Venus limb",
        38,
        "planet_disk_limb",
    ),
    "solar_system_track": SemanticLayerContract(
        ("sky", "solar_system", "planets", "venus", "track"),
        "Venus track",
        38,
        "planet_track",
    ),
    "moon": SemanticLayerContract(
        ("sky", "solar_system", "natural_satellites", "moon"),
        "Moon",
        39,
        "moon",
    ),
    "venus": SemanticLayerContract(
        ("sky", "solar_system", "planets", "venus"),
        "Venus",
        39,
        "planet",
    ),
    "galaxies": SemanticLayerContract(
        ("sky", "galaxies"), "Galaxies", 10, "galaxies"
    ),
    "milky_way_isophotes": SemanticLayerContract(
        ("sky", "milky_way_and_magellanic_clouds", "milky_way"),
        "Milky Way",
        20,
        "milky_way",
    ),
    "magellanic_cloud_isophotes": SemanticLayerContract(
        ("sky", "milky_way_and_magellanic_clouds", "magellanic_clouds"),
        "Magellanic Clouds",
        21,
        "magellanic_clouds",
    ),
    "nonstellar": SemanticLayerContract(
        ("sky", "deep_sky_objects", "other_objects"),
        "Other objects",
        29,
        "nonstellar",
    ),
    "open_clusters": SemanticLayerContract(
        ("sky", "deep_sky_objects", "open_clusters"),
        "Open clusters",
        30,
        "open_clusters",
    ),
    "globular_clusters": SemanticLayerContract(
        ("sky", "deep_sky_objects", "globular_clusters"),
        "Globular clusters",
        31,
        "globular_clusters",
    ),
    "planetary_nebulae": SemanticLayerContract(
        ("sky", "deep_sky_objects", "planetary_nebulae"),
        "Planetary nebulae",
        32,
        "planetary_nebulae",
    ),
    "supernova_remnants": SemanticLayerContract(
        ("sky", "deep_sky_objects", "supernova_remnants"),
        "Supernova remnants",
        33,
        "supernova_remnants",
    ),
    "stars": SemanticLayerContract(
        ("sky", "stars", "symbols"), "Star symbols", 40, "stars"
    ),
    "constellation_lines": SemanticLayerContract(
        ("sky", "constellations", "lines"),
        "Constellation lines",
        50,
        "constellation_lines",
    ),
    "constellation_boundaries": SemanticLayerContract(
        ("sky", "constellations", "boundaries"),
        "Constellation boundaries",
        51,
        "constellation_boundaries",
    ),
    "constellation_labels": SemanticLayerContract(
        ("sky", "constellations", "labels"),
        "Constellation labels",
        52,
        "constellation_labels",
    ),
    "equatorial_grid": SemanticLayerContract(
        ("sky", "grids", "equatorial"),
        "Equatorial grid",
        70,
        "equatorial_grid",
    ),
    "ecliptic_grid": SemanticLayerContract(
        ("sky", "grids", "ecliptic"),
        "Ecliptic grid",
        71,
        "ecliptic_grid",
    ),
    "galactic_grid": SemanticLayerContract(
        ("sky", "grids", "galactic"),
        "Galactic grid",
        72,
        "galactic_grid",
    ),
    "altaz_grid": SemanticLayerContract(
        ("sky", "grids", "horizontal"),
        "Horizontal grid",
        73,
        "horizontal_grid",
    ),
    "celestial_points": SemanticLayerContract(
        ("sky", "grids", "reference_points"),
        "Celestial reference points",
        74,
        "celestial_points",
    ),
    "horizon": SemanticLayerContract(
        ("chart", "masks_and_boundary", "horizon"),
        "Horizon",
        80,
        "horizon",
    ),
}


@dataclass(frozen=True)
class SemanticLayerIdentity:
    """Stable public identity carried from a sky layer to an export."""

    name: str
    svg_id: str
    edit_policy: EditPolicy = EditPolicy.STYLE
    semantic_path: tuple[str, ...] = ()
    display_name: str = ""
    presentation_order: int | None = None
    style_role: str = ""
    component_contracts: tuple[
        tuple[str, SemanticComponentContract], ...
    ] = ()
    path_display_names: tuple[str, ...] = ()
    entity_category_contracts: tuple[
        tuple[str, SemanticLayerContract], ...
    ] = ()

    def __post_init__(self):
        path = self.semantic_path or (self.name,)
        if not path or any(
            not isinstance(item, str)
            or _SAFE_PATH_COMPONENT.fullmatch(item) is None
            for item in path
        ):
            raise ValueError(
                "semantic_path must contain safe non-empty components."
            )
        object.__setattr__(self, "semantic_path", tuple(path))
        if not self.display_name:
            object.__setattr__(
                self,
                "display_name",
                self.name.replace("_", " ").title(),
            )
        if not self.style_role:
            object.__setattr__(self, "style_role", self.name)
        if self.path_display_names:
            if len(self.path_display_names) != len(path):
                raise ValueError(
                    "path_display_names must align with semantic_path."
                )
        else:
            inferred = tuple(
                _path_display_name(item) for item in path
            )
            object.__setattr__(
                self,
                "path_display_names",
                (*inferred[:-1], self.display_name),
            )

    def component_identity(self, component: str):
        """Return a declared child identity for one renderer output part."""
        contracts = dict(self.component_contracts)
        contract = contracts.get(component)
        if contract is None:
            return self
        return SemanticLayerIdentity(
            name=f"{self.name}_{contract.path_component}",
            svg_id=f"{self.svg_id}-{contract.path_component.replace('_', '-')}",
            edit_policy=contract.edit_policy,
            semantic_path=(*self.semantic_path, contract.path_component),
            display_name=f"{self.display_name} {contract.display_name}",
            presentation_order=self.presentation_order,
            style_role=f"{self.style_role}_{contract.style_role_suffix}",
            path_display_names=(
                *self.path_display_names,
                f"{self.display_name} {contract.display_name}",
            ),
        )

    def category_identity(self, category: str):
        """Return the shared astronomical branch for one entity category."""
        category = semantic_key(
            category,
            field="semantic entity category",
        )
        contract = dict(self.entity_category_contracts).get(category)
        if contract is None:
            return self
        return SemanticLayerIdentity(
            name=self.name,
            svg_id=(
                "wenu-layer-"
                f"{contract.path[-1].replace('_', '-')}"
            ),
            edit_policy=self.edit_policy,
            semantic_path=contract.path,
            display_name=contract.display_name,
            presentation_order=contract.presentation_order,
            style_role=contract.style_role,
        )

    def entity_identity(self, key: str, display_name: str):
        """Return a concise child identity declared by the source data."""
        key = semantic_key(
            key,
            field="semantic entity key",
            numeric_prefix="catalog",
        )
        if not isinstance(display_name, str) or not display_name:
            raise ValueError(
                "semantic entity display name must be a non-empty string."
            )
        return SemanticLayerIdentity(
            name=self.name,
            svg_id=f"{self.svg_id}-{key.replace('_', '-')}",
            edit_policy=self.edit_policy,
            semantic_path=(*self.semantic_path, key),
            display_name=display_name,
            presentation_order=self.presentation_order,
            style_role=self.style_role,
            path_display_names=(*self.path_display_names, display_name),
        )

    @property
    def semantic_path_text(self) -> str:
        return "/".join(self.semantic_path)

    @property
    def parent_path(self) -> tuple[str, ...]:
        return self.semantic_path[:-1]


def semantic_layer_identity(layer) -> SemanticLayerIdentity | None:
    """Resolve stable identity without using labels or drawing order."""
    name = getattr(layer, "layer_name", None)
    if name == "coordinates_grid":
        coordinate_system = getattr(layer, "coordinate_system", None)
        if coordinate_system:
            name = f"{coordinate_system}_grid"
    if name is None:
        return None
    if not isinstance(name, str) or not name:
        raise ValueError("layer_name must be a non-empty string or None.")
    if _SAFE_NAME.fullmatch(name) is None:
        raise ValueError(
            f"Layer name {name!r} is not a safe semantic name."
        )
    configured_policy = getattr(layer, "semantic_edit_policy", None)
    if configured_policy is None:
        edit_policy = (
            EditPolicy.LAYOUT
            if name.endswith("_labels")
            else EditPolicy.STYLE
        )
    else:
        try:
            edit_policy = EditPolicy(configured_policy)
        except ValueError as error:
            raise ValueError(
                f"Unsupported semantic edit policy: {configured_policy!r}."
            ) from error
    contract = _LAYER_CONTRACTS.get(name)
    svg_id = f"wenu-layer-{name.replace('_', '-')}"
    if name == "magellanic_cloud_isophotes":
        cloud_key = semantic_key(
            getattr(layer, "cloud", ""),
            field="Magellanic Cloud key",
        )
        cloud_names = {
            "lmc": "Large Magellanic Cloud",
            "smc": "Small Magellanic Cloud",
        }
        if cloud_key not in cloud_names:
            raise ValueError(
                f"Unsupported Magellanic Cloud key: {cloud_key!r}."
            )
        contract = SemanticLayerContract(
            (
                "sky",
                "milky_way_and_magellanic_clouds",
                cloud_key,
            ),
            cloud_names[cloud_key],
            _LAYER_CONTRACTS[name].presentation_order,
            f"{cloud_key}_isophotes",
        )
        svg_id = f"{cloud_key}-isophotes"
    if name in {
        "constellation_lines",
        "constellation_boundaries",
        "constellation_labels",
    }:
        component = name.removeprefix("constellation_")
        default_system = (
            "iau" if name == "constellation_boundaries" else "western"
        )
        source_system = getattr(
            layer,
            "semantic_system_key",
            getattr(
                layer,
                "system",
                getattr(layer, "boundaries_name", default_system),
            ),
        )
        system_key = semantic_key(
            source_system,
            field="constellation system key",
        )
        combined_key = f"{component}_{system_key}"
        component_title = component.replace("_", " ").title()
        system_title = str(source_system).replace("_", " ").title()
        contract = SemanticLayerContract(
            ("sky", "constellations", combined_key),
            f"{component_title}-{system_title}",
            _LAYER_CONTRACTS[name].presentation_order,
            f"{name}_{system_key}",
        )
        svg_id = f"{system_key.replace('_', '-')}-{component}"
    options = {} if contract is None else {
        "semantic_path": contract.path,
        "display_name": contract.display_name,
        "presentation_order": contract.presentation_order,
        "style_role": contract.style_role,
        "component_contracts": (
            tuple(_GRID_COMPONENT_CONTRACTS.items())
            if name.endswith("_grid") or name == "solar_system_track"
            else ()
        ),
        "entity_category_contracts": (
            tuple(_NONSTELLAR_CATEGORY_CONTRACTS.items())
            if name == "nonstellar"
            else ()
        ),
    }
    return SemanticLayerIdentity(
        name=name,
        svg_id=svg_id,
        edit_policy=edit_policy,
        **options,
    )
