from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from wenu import (
    AtlasChartStyle,
    LegendSymbolDescriptor,
    legend_symbol_descriptors,
)
from wenu.charts.legend import _legend_handle
from wenu.rendering.symbols import DEFAULT_SYMBOLS


def sky_with(**active):
    names = (
        "open_clusters",
        "globular_clusters",
        "planetary_nebulae",
        "supernova_remnants",
        "galaxies",
        "milky_way_isophotes",
    )
    return SimpleNamespace(
        **{
            name: active.get(name)
            for name in names
        }
    )


def test_only_active_layers_produce_descriptors():
    descriptors = legend_symbol_descriptors(
        sky_with(
            open_clusters=object(),
            planetary_nebulae=object(),
            galaxies=object(),
        ),
        AtlasChartStyle(),
    )
    assert all(
        isinstance(item, LegendSymbolDescriptor)
        for item in descriptors
    )
    assert [item.key for item in descriptors] == [
        "open_cluster",
        "planetary_nebula",
        "galaxy",
    ]


def test_fixed_symbols_name_canonical_library_entries():
    descriptors = {
        item.key: item
        for item in legend_symbol_descriptors(
            sky_with(
                open_clusters=object(),
                planetary_nebulae=object(),
            ),
            AtlasChartStyle(),
        )
    }
    assert descriptors["open_cluster"].symbol_name == "open_cluster"
    assert (
        descriptors["planetary_nebula"].symbol_name
        == "planetary_nebula"
    )


def test_renderer_uses_exact_canonical_marker_paths():
    descriptors = legend_symbol_descriptors(
        sky_with(
            open_clusters=object(),
            planetary_nebulae=object(),
        ),
        AtlasChartStyle(),
    )
    handles = {
        descriptor.key: _legend_handle(descriptor)
        for descriptor in descriptors
    }
    assert isinstance(handles["open_cluster"], Line2D)
    assert (
        handles["open_cluster"].get_marker()
        is DEFAULT_SYMBOLS.open_cluster
    )
    assert (
        handles["planetary_nebula"].get_marker()
        is DEFAULT_SYMBOLS.planetary_nebula
    )


def test_area_objects_use_patch_descriptors_and_handles():
    descriptors = legend_symbol_descriptors(
        sky_with(
            galaxies=object(),
            milky_way_isophotes=object(),
        ),
        AtlasChartStyle(),
    )
    assert [item.kind for item in descriptors] == ["patch", "patch"]
    assert all(
        isinstance(_legend_handle(item), Patch)
        for item in descriptors
    )


def test_descriptor_colors_come_from_style():
    style = AtlasChartStyle()
    descriptors = {
        item.key: item
        for item in legend_symbol_descriptors(
            sky_with(
                open_clusters=object(),
                supernova_remnants=object(),
                galaxies=object(),
            ),
            style,
        )
    }
    assert (
        descriptors["open_cluster"].edge_color
        == style.deep_sky.open_cluster_color
    )
    assert (
        descriptors["supernova_remnant"].linewidth
        == style.deep_sky.supernova_remnant_linewidth
    )
    assert (
        descriptors["galaxy"].edge_color
        == style.deep_sky.galaxy_edge_color
    )


def test_descriptor_module_has_no_render_backend_dependency():
    import wenu.charts.legend_symbols as module

    source = Path(module.__file__).read_text().lower()
    assert "matplotlib" not in source
    assert "wenu.rendering" not in source
