"""Sky-owned semantic hierarchy and presentation-order contracts."""

from types import SimpleNamespace

import pytest

from wenu.sky.semantic_identity import (
    SemanticLayerIdentity,
    semantic_layer_identity,
)


def identity(name, *, coordinate_system=None):
    layer = SimpleNamespace(layer_name=name)
    if coordinate_system is not None:
        layer.coordinate_system = coordinate_system
    return semantic_layer_identity(layer)


def test_celestial_layers_follow_the_accepted_presentation_order():
    names = (
        "galaxies",
        "milky_way_isophotes",
        "magellanic_cloud_isophotes",
        "open_clusters",
        "globular_clusters",
        "planetary_nebulae",
        "supernova_remnants",
        "stars",
        "constellation_lines",
        "constellation_boundaries",
        "constellation_labels",
    )
    resolved = tuple(identity(name) for name in names)

    assert tuple(item.presentation_order for item in resolved) == (
        10, 20, 21, 30, 31, 32, 33, 40, 50, 51, 52
    )
    assert tuple(item.semantic_path for item in resolved) == (
        ("sky", "galaxies"),
        ("sky", "milky_way_and_magellanic_clouds", "milky_way"),
        (
            "sky",
            "milky_way_and_magellanic_clouds",
            "magellanic_clouds",
        ),
        ("sky", "deep_sky_objects", "open_clusters"),
        ("sky", "deep_sky_objects", "globular_clusters"),
        ("sky", "deep_sky_objects", "planetary_nebulae"),
        ("sky", "deep_sky_objects", "supernova_remnants"),
        ("sky", "stars", "symbols"),
        ("sky", "constellations", "lines_western"),
        ("sky", "constellations", "boundaries_iau"),
        ("sky", "constellations", "labels_western"),
    )


@pytest.mark.parametrize(
    ("system", "path", "order"),
    (
        ("equatorial", ("sky", "grids", "equatorial"), 70),
        ("ecliptic", ("sky", "grids", "ecliptic"), 71),
        ("galactic", ("sky", "grids", "galactic"), 72),
        ("altaz", ("sky", "grids", "horizontal"), 73),
    ),
)
def test_each_grid_propagates_its_own_semantic_path(system, path, order):
    resolved = identity("coordinates_grid", coordinate_system=system)

    assert resolved.semantic_path == path
    assert resolved.presentation_order == order


def test_chart_context_follows_sky_content_without_entering_sky_taxonomy():
    horizon = identity("horizon")

    assert horizon.semantic_path == (
        "chart", "masks_and_boundary", "horizon"
    )
    assert horizon.presentation_order == 80


def test_unknown_extension_layer_keeps_safe_generic_identity():
    resolved = identity("custom_overlay")

    assert resolved == SemanticLayerIdentity(
        name="custom_overlay",
        svg_id="wenu-layer-custom-overlay",
    )
    assert resolved.semantic_path_text == "custom_overlay"
    assert resolved.parent_path == ()
    assert resolved.presentation_order is None


@pytest.mark.parametrize(
    "path",
    (
        ("Sky", "stars"),
        ("sky", "constellation labels"),
        ("sky", ""),
    ),
)
def test_semantic_paths_reject_unsafe_components(path):
    with pytest.raises(ValueError, match="semantic_path"):
        SemanticLayerIdentity(
            name="test",
            svg_id="wenu-layer-test",
            semantic_path=path,
        )


def test_grid_identity_declares_independent_line_and_label_children():
    grid = identity("coordinates_grid", coordinate_system="equatorial")

    lines = grid.component_identity("lines")
    labels = grid.component_identity("labels")

    assert lines.semantic_path == (
        "sky", "grids", "equatorial", "lines"
    )
    assert lines.display_name == "Equatorial grid lines"
    assert lines.style_role == "equatorial_grid_lines"
    assert lines.edit_policy.value == "style"
    assert labels.semantic_path == (
        "sky", "grids", "equatorial", "labels"
    )
    assert labels.display_name == "Equatorial grid labels"
    assert labels.style_role == "equatorial_grid_labels"
    assert labels.edit_policy.value == "layout"


def test_non_grid_identity_ignores_undeclared_renderer_parts():
    galaxies = identity("galaxies")

    assert galaxies.component_identity("lines") is galaxies


def test_constellation_hierarchy_is_shallow_and_system_agnostic():
    layer = SimpleNamespace(
        layer_name="constellation_lines",
        semantic_system_key="polynesian_navigation",
    )

    resolved = semantic_layer_identity(layer)
    entity = resolved.entity_identity("manu", "Manu")

    assert resolved.semantic_path == (
        "sky", "constellations", "lines_polynesian_navigation"
    )
    assert resolved.display_name == "Lines-Polynesian Navigation"
    assert resolved.svg_id == "polynesian-navigation-lines"
    assert resolved.path_display_names == (
        "Sky", "Constellations", "Lines-Polynesian Navigation"
    )
    assert entity.semantic_path == (
        "sky",
        "constellations",
        "lines_polynesian_navigation",
        "manu",
    )
    assert entity.display_name == "Manu"
    assert entity.path_display_names[-2:] == (
        "Lines-Polynesian Navigation", "Manu"
    )
    assert entity.svg_id == "polynesian-navigation-lines-manu"
