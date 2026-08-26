"""Renderer-neutral semantic identity for chart layers."""

from __future__ import annotations

from dataclasses import dataclass
import re

from wenu.chart_document import EditPolicy


_SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_SAFE_PATH_COMPONENT = _SAFE_NAME


@dataclass(frozen=True)
class SemanticLayerContract:
    """Sky-owned hierarchy and presentation metadata for one layer."""

    path: tuple[str, ...]
    display_name: str
    presentation_order: int
    style_role: str


_LAYER_CONTRACTS = {
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
    options = {} if contract is None else {
        "semantic_path": contract.path,
        "display_name": contract.display_name,
        "presentation_order": contract.presentation_order,
        "style_role": contract.style_role,
    }
    return SemanticLayerIdentity(
        name=name,
        svg_id=f"wenu-layer-{name.replace('_', '-')}",
        edit_policy=edit_policy,
        **options,
    )
