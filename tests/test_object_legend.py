"""Current object legend contracts."""

# Contracts consolidated from test_milestone40h_galaxy_legend_ellipse.py.
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

from wenu import AtlasChartStyle, legend_symbol_descriptors
from wenu.charts.legend import (
    _legend_handle,
    _legend_handler_map,
)


m40h_galaxy_legend_ellipse_ROOT = Path(__file__).resolve().parents[1]
m40h_galaxy_legend_ellipse_EXAMPLE = m40h_galaxy_legend_ellipse_ROOT / "tests" / "fixtures" / "example_regressions" / "legend_symbols.py"


def galaxy_descriptor():
    sky = SimpleNamespace(
        open_clusters=None,
        globular_clusters=None,
        planetary_nebulae=None,
        supernova_remnants=None,
        galaxies=object(),
        milky_way_isophotes=None,
    )
    return legend_symbol_descriptors(
        sky,
        AtlasChartStyle(),
    )[0]


def m40h_galaxy_legend_ellipse_load_example():
    spec = spec_from_file_location("legend_symbols_example", m40h_galaxy_legend_ellipse_EXAMPLE)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_galaxy_descriptor_has_a_filled_face():
    descriptor = galaxy_descriptor()
    assert descriptor.face_color not in (None, "none")
    assert descriptor.face_color == descriptor.edge_color


def test_galaxy_legend_handle_is_an_elongated_ellipse():
    handle = _legend_handle(galaxy_descriptor())
    assert isinstance(handle, Ellipse)
    assert handle.width > handle.height
    assert handle.get_fill()


def test_ellipse_has_a_dedicated_legend_handler():
    handler_map = _legend_handler_map()
    assert Ellipse in handler_map


def test_visual_reference_draws_a_galaxy_ellipse():
    module = m40h_galaxy_legend_ellipse_load_example()
    figure, ax, _, _ = module.draw_reference()
    try:
        ellipses = [
            patch
            for patch in ax.patches
            if isinstance(patch, Ellipse)
        ]
        assert len(ellipses) == 1
        assert ellipses[0].width > ellipses[0].height
        assert ellipses[0].get_fill()
    finally:
        plt.close(figure)


def test_visual_reference_can_be_saved(tmp_path):
    module = m40h_galaxy_legend_ellipse_load_example()
    destination = tmp_path / "galaxy-ellipse.png"
    figure, _, _, _ = module.draw_reference(destination, dpi=72)
    try:
        assert destination.is_file()
        assert destination.stat().st_size > 0
    finally:
        plt.close(figure)

# Contracts consolidated from test_milestone40h_legend_context_repair.py.
from inspect import signature
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import AtlasChartStyle, draw_chart_legend


def empty_sky():
    return SimpleNamespace(
        open_clusters=None,
        globular_clusters=None,
        planetary_nebulae=None,
        supernova_remnants=None,
        galaxies=None,
        milky_way_isophotes=None,
    )


def test_context_lines_parameter_is_preserved():
    assert "context_lines" in signature(draw_chart_legend).parameters


def test_context_lines_follow_resolved_or_custom_metadata():
    figure, ax = plt.subplots()
    legend = draw_chart_legend(
        ax,
        object(),
        empty_sky(),
        AtlasChartStyle(),
        title="Coordinates",
        context_lines=(
            "La Ligua, Chile",
            "2026-08-15 21:00 CLT",
        ),
    )
    assert legend.get_title().get_text().splitlines() == [
        "Coordinates",
        "La Ligua, Chile",
        "2026-08-15 21:00 CLT",
    ]
    plt.close(figure)

# Contracts consolidated from test_milestone40h_legend_metadata.py.
from types import SimpleNamespace
from dataclasses import replace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    AtlasChartStyle,
    LegendMetadata,
    chart_context_lines,
    draw_chart_legend,
    resolve_legend_metadata,
    observer_context_lines,
)


class FakeHorizontal:
    def transform_to(self, frame):
        from astropy import units as u
        from astropy.coordinates import SkyCoord

        return SkyCoord(ra=15.0 * u.deg, dec=-30.0 * u.deg, frame=frame)


class FakeObserver:
    from astropy.time import Time

    altaz_frame = object()
    t_astropy = Time("2026-08-28T00:00:00", scale="utc")
    lat_deg = -32.0
    lon_deg = -71.0
    elevation_m = 0.0


class FakeSkyCoord:
    def __init__(self, **kwargs):
        pass

    def transform_to(self, frame):
        return FakeHorizontal().transform_to(frame)



def patch_center_transform(monkeypatch, module):
    from wenu.geometry.spherical import SphericalPoints

    def transform(_service, _geometry, target_spec, observation=None):
        assert observation is not None
        return SphericalPoints(
            lon_deg=[15.0],
            lat_deg=[-30.0],
            coordinate_spec=target_spec,
        )

    monkeypatch.setattr(module.CoordinateService, "transform", transform)


def fake_chart():
    return SimpleNamespace(center_alt_deg=45.0, center_az_deg=180.0)


def fake_sky(*layers):
    return SimpleNamespace(
        observer=FakeObserver(),
        layers=layers,
        open_clusters=None,
        globular_clusters=None,
        planetary_nebulae=None,
        supernova_remnants=None,
        galaxies=None,
        milky_way_isophotes=None,
    )


def test_metadata_uses_last_registered_coordinate_grid(monkeypatch):
    import wenu.charts.legend_metadata as module

    patch_center_transform(monkeypatch, module)
    first = SimpleNamespace(
        coordinate_system="galactic",
    )
    active = SimpleNamespace(
        coordinate_system="equatorial",
        frame="fk5",
        equinox="J2050",
    )
    metadata = resolve_legend_metadata(
        fake_chart(),
        fake_sky(first, object(), active),
    )
    assert isinstance(metadata, LegendMetadata)
    assert metadata.coordinate_system == "equatorial"
    assert metadata.frame == "fk5"
    assert metadata.epoch == "J2050.0"
    assert metadata.grid_text == "Equatorial grid: FK5, J2050.0"
    assert "RA 1h00m00s" in metadata.center_text


def test_explicit_grid_overrides_registered_grid(monkeypatch):
    import wenu.charts.legend_metadata as module

    patch_center_transform(monkeypatch, module)
    registered = SimpleNamespace(
        coordinate_system="equatorial",
        frame="fk5",
        equinox="J2000",
    )
    explicit = SimpleNamespace(coordinate_system="galactic")
    metadata = resolve_legend_metadata(
        fake_chart(),
        fake_sky(registered),
        grid=explicit,
    )
    assert metadata.coordinate_system == "galactic"
    assert metadata.grid_text == "Galactic grid: IAU Galactic"


def test_icrs_has_no_fictitious_epoch(monkeypatch):
    import wenu.charts.legend_metadata as module

    patch_center_transform(monkeypatch, module)
    grid = SimpleNamespace(
        coordinate_system="equatorial",
        frame="icrs",
        equinox="J2000",
    )
    metadata = resolve_legend_metadata(
        fake_chart(),
        fake_sky(grid),
    )
    assert metadata.grid_text == "Equatorial grid: ICRS"
    assert metadata.epoch is None


def test_legend_visibility_and_location_remain_style_controlled():
    style = AtlasChartStyle()
    hidden = replace(
        style,
        legend=replace(style.legend, visible=False),
    )
    figure, ax = plt.subplots()
    assert draw_chart_legend(
        ax,
        fake_chart(),
        fake_sky(),
        hidden,
    ) is None
    plt.close(figure)


def test_legend_accepts_explicit_title_without_resolving_coordinates():
    figure, ax = plt.subplots()
    legend = draw_chart_legend(
        ax,
        fake_chart(),
        fake_sky(),
        AtlasChartStyle(),
        title="Custom metadata",
    )
    assert legend.get_title().get_text() == "Custom metadata"
    assert legend._loc == 1
    plt.close(figure)


def test_metadata_module_has_no_render_backend_dependency():
    from pathlib import Path
    import wenu.charts.legend_metadata as module

    source = Path(module.__file__).read_text().lower()
    assert "matplotlib" not in source


def test_observer_context_lines_include_location_and_local_time():
    from datetime import datetime, timezone

    observer = SimpleNamespace(
        utc_datetime=datetime(2026, 8, 16, 1, 0, tzinfo=timezone.utc),
        timezone_name="America/Santiago",
        location_name="La Ligua",
        lat_deg=-32.4524,
        lon_deg=-71.2311,
        elevation_m=52.0,
    )

    assert observer_context_lines(observer) == (
        "Location: La Ligua — 32.4524° S, 71.2311° W, 52 m",
        "Date: 2026-08-15",
        "Local time: 21:00 (UTC−04:00)",
    )

    assert observer_context_lines(
        observer,
        location=False,
        local_time=False,
        labels=False,
    ) == ("2026-08-15",)


def test_compact_chart_context_lines_are_independently_selectable(
    monkeypatch,
):
    import wenu.charts.legend_metadata as module

    patch_center_transform(monkeypatch, module)
    grid = SimpleNamespace(
        coordinate_system="equatorial",
        frame="fk5",
        equinox="J2050",
    )
    sky = fake_sky(grid)

    assert chart_context_lines(fake_chart(), sky) == (
        "RA 1h00m00s",
        "Dec -30°00′00″",
        "FK5, J2050.0",
    )
    assert chart_context_lines(
        fake_chart(), sky, center=False
    ) == ("FK5, J2050.0",)
    assert chart_context_lines(
        fake_chart(), sky, grid=False
    ) == ("RA 1h00m00s", "Dec -30°00′00″")

# Contracts consolidated from test_milestone40h_legend_symbols.py.
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

# Contracts consolidated from test_milestone40h_legend_visual.py.
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from wenu.rendering.symbols import DEFAULT_SYMBOLS


m40h_legend_visual_ROOT = Path(__file__).resolve().parents[1]
m40h_legend_visual_EXAMPLE = m40h_legend_visual_ROOT / "tests" / "fixtures" / "example_regressions" / "legend_symbols.py"


def m40h_legend_visual_load_example():
    spec = spec_from_file_location("legend_symbols_example", m40h_legend_visual_EXAMPLE)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_contains_every_supported_symbol():
    module = m40h_legend_visual_load_example()
    figure, _, descriptors, handles = module.draw_reference()
    try:
        assert [item.key for item in descriptors] == [
            "open_cluster",
            "globular_cluster",
            "planetary_nebula",
            "supernova_remnant",
            "galaxy",
            "milky_way",
        ]
        assert len(handles) == len(descriptors)
    finally:
        plt.close(figure)


def test_reference_uses_canonical_fixed_marker_paths():
    module = m40h_legend_visual_load_example()
    figure, _, descriptors, handles = module.draw_reference()
    try:
        by_key = dict(zip((item.key for item in descriptors), handles))
        assert (
            by_key["open_cluster"].get_marker()
            is DEFAULT_SYMBOLS.open_cluster
        )
        assert (
            by_key["planetary_nebula"].get_marker()
            is DEFAULT_SYMBOLS.planetary_nebula
        )
    finally:
        plt.close(figure)


def test_reference_uses_marker_and_patch_handle_families():
    module = m40h_legend_visual_load_example()
    figure, _, descriptors, handles = module.draw_reference()
    try:
        pairs = dict(zip((item.key for item in descriptors), handles))
        assert isinstance(pairs["open_cluster"], Line2D)
        assert isinstance(pairs["globular_cluster"], Line2D)
        assert isinstance(pairs["planetary_nebula"], Line2D)
        assert isinstance(pairs["supernova_remnant"], Line2D)
        assert isinstance(pairs["galaxy"], Patch)
        assert isinstance(pairs["milky_way"], Patch)
    finally:
        plt.close(figure)


def test_reference_writes_to_requested_destination(tmp_path):
    module = m40h_legend_visual_load_example()
    destination = tmp_path / "legend-reference.png"
    figure, _, _, _ = module.draw_reference(destination, dpi=72)
    try:
        assert destination.is_file()
        assert destination.stat().st_size > 0
    finally:
        plt.close(figure)


def test_default_output_keeps_repository_root_clean():
    module = m40h_legend_visual_load_example()
    assert module.OUTPUT == Path("output/legend-symbols")



def test_object_legend_preserves_descriptor_keys_when_labels_change():
    figure, ax = plt.subplots()
    sky = fake_sky()
    for name in (
        "open_clusters",
        "globular_clusters",
        "planetary_nebulae",
        "supernova_remnants",
        "galaxies",
        "milky_way_isophotes",
    ):
        setattr(sky, name, object())
    custom = {
        "open_cluster": "Amas ouverts",
        "galaxy": "Galaxias",
    }

    from wenu.charts.legend import draw_chart_legend

    legend = draw_chart_legend(
        ax,
        fake_chart(),
        sky,
        AtlasChartStyle(),
        title="Context",
        symbol_labels=custom,
    )

    assert legend._wenu_legend_entry_keys == (
        "open_cluster",
        "globular_cluster",
        "planetary_nebula",
        "supernova_remnant",
        "galaxy",
        "milky_way",
    )
    assert legend.get_texts()[0].get_text() == "Amas ouverts"
    assert legend.get_texts()[4].get_text() == "Galaxias"
    plt.close(figure)
