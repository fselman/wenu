"""Current style contracts contracts."""

# Contracts consolidated from test_milestone39a_composed_styles.py.
"""Milestone 39A tests for composed, output-neutral styles."""

from dataclasses import replace
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from wenu import ChartStyle, PublicationStyle
from wenu.charts.style_components import (
    CanvasStyle,
    DeepSkyStyle,
    GridStyle,
    IsophoteStyle,
    MaskStyle,
    StellarStyle,
)


def stellar_metadata():
    return SimpleNamespace(
        metadata={
            "magnitude": np.asarray((1.0, 2.0, 3.0)),
            "is_variable": np.asarray((True, False, True)),
            "is_multiple": np.asarray((False, True, True)),
        }
    )


def test_default_composed_style_exactly_matches_publication_defaults():
    assert ChartStyle().as_publication_style() == PublicationStyle()


def test_sections_are_focused_immutable_values():
    style = ChartStyle()
    assert isinstance(style.canvas, CanvasStyle)
    assert isinstance(style.stars, StellarStyle)
    assert isinstance(style.isophotes, IsophoteStyle)
    assert isinstance(style.deep_sky, DeepSkyStyle)
    assert isinstance(style.grids, GridStyle)
    assert isinstance(style.mask, MaskStyle)

    changed = replace(
        style,
        canvas=replace(style.canvas, sky_color="white"),
        stars=replace(style.stars, color="black", area_scale=0.5),
    )
    assert style.canvas.sky_color == "midnightblue"
    assert changed.canvas.sky_color == "white"
    assert changed.stars.color == "black"
    assert changed.stars.area_scale == 0.5


def test_custom_sections_map_to_the_flat_compatibility_layer():
    style = ChartStyle(
        canvas=CanvasStyle(
            sky_color="white",
            foreground_color="black",
            label_fontsize=8.0,
        ),
        stars=StellarStyle(
            color="black",
            area_scale=0.75,
            draw_variable_symbols=False,
            draw_multiple_symbols=False,
        ),
        grids=GridStyle(
            boundary_color="gray",
            equatorial_color="gray",
            ecliptic_color="gray",
            galactic_color="gray",
        ),
    ).as_publication_style()
    assert style.sky_color == "white"
    assert style.foreground_color == "black"
    assert style.star_color == "black"
    assert style.star_area_scale == 0.75
    assert style.label_fontsize == 8.0
    assert style.draw_variable_star_symbols is False
    assert style.draw_multiple_star_symbols is False
    assert style.boundary_color == "gray"


def test_default_star_rendering_is_output_equivalent():
    spherical = stellar_metadata()
    old = PublicationStyle()._star_render_options(spherical, None)
    new = ChartStyle().as_publication_style()._star_render_options(
        spherical,
        None,
    )
    assert old["point_overlays"] == new["point_overlays"] == []
    assert old["style"]["c"] == new["style"]["c"]
    assert old["style"]["zorder"] == new["style"]["zorder"]
    assert np.array_equal(old["style"]["s"], new["style"]["s"])


def test_constellation_boundaries_are_strokes_without_polygon_fill():
    boundary_layer = object()
    sky = SimpleNamespace(
        stars=None,
        nonstellar=None,
        galaxies=None,
        milky_way_isophotes=None,
        globular_clusters=None,
        open_clusters=None,
        supernova_remnants=None,
        planetary_nebulae=None,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=boundary_layer,
        points=None,
        layers=(),
    )
    style = PublicationStyle(boundary_color="#123456")

    boundary_style = style.layer_options(sky)[boundary_layer][
        "render"
    ]["style"]

    assert boundary_style["edgecolor"] == "#123456"
    assert boundary_style["facecolor"] == "none"
    assert "color" not in boundary_style


def test_chart_style_implements_the_existing_style_protocol():
    style = ChartStyle(mask=MaskStyle(alpha=0.42, zorder=21.0))
    assert style.outside_mask_style() == (
        style.as_publication_style().outside_mask_style()
    )

    figure, ax = plt.subplots()
    try:
        returned = style.configure_axes(ax, title="Test")
        assert returned is ax
        assert ax.get_facecolor() == (
            0.09803921568627451,
            0.09803921568627451,
            0.4392156862745098,
            1.0,
        )
        assert ax.get_title() == "Test"
    finally:
        plt.close(figure)


def test_top_level_chart_style_export_is_available():
    from wenu import ChartStyle as ExportedChartStyle

    assert ExportedChartStyle is ChartStyle

# Contracts consolidated from test_milestone39b_atlas_style.py.
"""Milestone 39B tests for the white atlas preset."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import AtlasChartStyle, ChartStyle


def test_atlas_style_is_a_composed_chart_style():
    style = AtlasChartStyle()
    assert isinstance(style, ChartStyle)
    assert style.canvas.sky_color == "white"
    assert style.stars.color == "#151515"


def test_atlas_stellar_classification_overlays_are_disabled():
    style = AtlasChartStyle()
    assert style.stars.draw_variable_symbols is False
    assert style.stars.draw_multiple_symbols is False
    flat = style.as_publication_style()
    assert flat.draw_variable_star_symbols is False
    assert flat.draw_multiple_star_symbols is False


def test_atlas_palette_matches_the_agreed_visual_roles():
    style = AtlasChartStyle()
    assert style.isophotes.milky_way_color == "#b9d3da"
    assert style.deep_sky.open_cluster_color == "#d2b321"
    assert style.deep_sky.globular_cluster_color == "#c5a000"
    assert style.deep_sky.planetary_nebula_color == "#6f8e4d"
    assert style.deep_sky.galaxy_edge_color == "#b43b37"
    assert style.grids.boundary_linestyle == ":"


def test_atlas_structural_styles_reach_publication_adapter():
    flat = AtlasChartStyle().as_publication_style()
    assert flat.constellation_line_color == "#686868"
    assert flat.constellation_linewidth == 0.35
    assert flat.constellation_label_color == "#5b5b5b"
    assert flat.boundary_color == "#777777"
    assert flat.boundary_linestyle == ":"
    assert flat.grid_linewidth == 0.45
    assert flat.ecliptic_linestyle == "--"


def test_atlas_axes_use_a_white_plotting_field():
    figure, ax = plt.subplots()
    try:
        AtlasChartStyle().configure_axes(ax, title="Atlas")
        assert ax.get_facecolor() == (1.0, 1.0, 1.0, 1.0)
        assert ax.get_title() == "Atlas"
    finally:
        plt.close(figure)


def test_atlas_style_is_exported_at_package_top_level():
    from wenu import AtlasChartStyle as ExportedAtlasChartStyle

    assert ExportedAtlasChartStyle is AtlasChartStyle

# Contracts consolidated from test_milestone40g_cartoon_visual_style.py.
from dataclasses import fields

from wenu import CartoonChartStyle
from wenu.charts.detail import CartoonDetailPolicy


def test_cartoon_style_uses_an_original_light_classroom_palette():
    style = CartoonChartStyle()
    assert style.canvas.sky_color == "#fffdf7"
    assert style.canvas.foreground_color == "#172238"
    assert style.stars.color == "#172238"
    assert style.grids.constellation_line_color == "#304f78"


def test_constellation_structure_is_visually_prominent():
    style = CartoonChartStyle()
    assert style.grids.constellation_linewidth >= 1.0
    assert style.grids.constellation_line_alpha >= 0.9
    assert style.grids.constellation_label_alpha == 1.0
    assert style.canvas.label_fontsize >= 12.0


def test_stellar_classification_overlays_are_off():
    style = CartoonChartStyle()
    assert style.stars.draw_variable_symbols is False
    assert style.stars.draw_multiple_symbols is False


def test_default_cartoon_legend_and_coordinate_labels_are_quiet():
    style = CartoonChartStyle()
    assert style.legend.visible is False
    assert style.grids.draw_coordinate_labels is False


def test_publication_style_receives_cartoon_visual_values():
    composed = CartoonChartStyle()
    publication = composed.as_publication_style()
    assert publication.sky_color == composed.canvas.sky_color
    assert publication.star_color == composed.stars.color
    assert (
        publication.constellation_line_color
        == composed.grids.constellation_line_color
    )
    assert (
        publication.constellation_linewidth
        == composed.grids.constellation_linewidth
    )
    assert publication.draw_variable_star_symbols is False
    assert publication.draw_multiple_star_symbols is False


def test_visual_style_does_not_own_chart_type_mode_or_content_policy():
    names = {item.name for item in fields(CartoonChartStyle)}
    forbidden = {
        "projection",
        "viewport",
        "angular_width_deg",
        "width_inches",
        "height_inches",
        "dpi",
        "enabled_layers",
        "magnitude_limit",
        "constellation_star_mode",
        "extra_star_ids",
    }
    assert names.isdisjoint(forbidden)


def test_cartoon_content_policy_remains_a_separate_object():
    style = CartoonChartStyle()
    detail = CartoonDetailPolicy().resolve(object(), object())
    assert style.grids.constellation_linewidth > 0
    assert detail.enabled_layers == frozenset(
        {"stars", "constellation_lines", "constellation_labels"}
    )
    assert detail.constellation_star_mode == "selected"

# Contracts consolidated from test_milestone40h_cartoon_preset.py.
import ast
from dataclasses import fields, replace
from pathlib import Path

from wenu import (
    CartoonChartPreset,
    CartoonChartStyle,
    CartoonDetailPolicy,
    PresentationMode,
    RegionalChart,
    compose_chart,
)


def m40h_cartoon_preset_regional_chart():
    return RegionalChart(
        center_alt_deg=45.0,
        center_az_deg=190.0,
        field_width_deg=45.0,
        field_height_deg=30.0,
    )


def test_default_preset_bundles_only_cartoon_style_and_detail():
    preset = CartoonChartPreset()
    assert isinstance(preset.style, CartoonChartStyle)
    assert isinstance(preset.detail, CartoonDetailPolicy)
    assert preset.components() == (preset.style, preset.detail)


def test_preset_expansion_matches_explicit_composition():
    chart = m40h_cartoon_preset_regional_chart()
    mode = PresentationMode(width_inches=10.0)
    preset = CartoonChartPreset()
    convenient = preset.compose(chart, mode=mode)
    explicit = compose_chart(
        chart,
        style=preset.style,
        mode=mode,
        detail=preset.detail,
    )
    assert convenient == explicit


def test_chart_type_and_mode_remain_independently_replaceable():
    chart = m40h_cartoon_preset_regional_chart()
    preset = CartoonChartPreset()
    narrow = preset.compose(
        chart,
        mode=PresentationMode(width_inches=8.0),
    )
    wide = preset.compose(
        chart,
        mode=PresentationMode(width_inches=14.0),
    )
    assert narrow.context == wide.context == chart.chart_context
    assert narrow.style == wide.style
    assert narrow.style is not preset.style
    assert narrow.style_name == wide.style_name == "cartoon"
    assert narrow.mode.width_inches == 8.0
    assert wide.mode.width_inches == 14.0


def test_preset_accepts_custom_style_and_detail_components():
    style = replace(
        CartoonChartStyle(),
        canvas=replace(
            CartoonChartStyle().canvas,
            sky_color="white",
        ),
    )
    detail = CartoonDetailPolicy(
        bright_star_magnitude_limit=2.0,
        extra_star_ids=frozenset({11767}),
    )
    preset = CartoonChartPreset(style=style, detail=detail)
    composition = preset.compose(m40h_cartoon_preset_regional_chart())
    assert composition.style.canvas.sky_color == "white"
    assert composition.detail.star_magnitude_limit == 2.0
    assert composition.detail.extra_star_ids == frozenset({11767})


def test_preset_does_not_own_chart_geometry_or_output_mode():
    names = {item.name for item in fields(CartoonChartPreset)}
    assert names == {"style", "detail"}


def imported_modules(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    return tuple(imported)


def test_cartoon_preset_has_no_render_backend_dependency():
    import wenu.charts.cartoon as module

    imports = imported_modules(Path(module.__file__))
    assert "matplotlib" not in imports
    assert not any(name.startswith("matplotlib.") for name in imports)

# Contracts consolidated from test_milestone41b_cartoon_composition.py.
from types import SimpleNamespace

import pytest

from wenu import (
    BoundaryKind,
    ChartContext,
    ChartMode,
    DetailOverrides,
    PresentationMode,
    PrintMode,
    ResolvedDetail,
    cartoon_output_mode,
    compose_cartoon_chart,
)
from wenu.geometry.viewport import Viewport


def m41b_cartoon_composition_chart():
    return SimpleNamespace(
        chart_context=ChartContext(
            viewport=Viewport(-2.0, 2.0, -1.0, 1.0),
            angular_width_deg=60.0,
            angular_height_deg=30.0,
            tangent_longitude_deg=180.0,
            tangent_latitude_deg=-30.0,
            boundary_kind=BoundaryKind.RECTANGULAR,
        )
    )


def test_named_modes_resolve_to_chart_mode_objects():
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        assert isinstance(cartoon_output_mode("print"), PrintMode)
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        assert isinstance(
            cartoon_output_mode("presentation"),
            PresentationMode,
        )


def test_existing_chart_mode_passes_through():
    mode = ChartMode(width_inches=9.0)
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        assert cartoon_output_mode(mode) is mode


def test_unknown_named_mode_is_rejected():
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        with pytest.raises(ValueError, match="print or presentation"):
            cartoon_output_mode("night")


def test_print_composition_keeps_concerns_separate():
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        composition = compose_cartoon_chart(m41b_cartoon_composition_chart(), mode="print")
    assert composition.context.angular_width_deg == pytest.approx(60.0)
    assert composition.style.canvas.sky_color == "white"
    assert composition.mode.dpi == 300
    assert composition.detail.enabled_layers == frozenset(
        {"stars", "constellation_lines", "constellation_labels"}
    )


def test_presentation_changes_style_and_output_not_content():
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        printed = compose_cartoon_chart(m41b_cartoon_composition_chart(), mode="print")
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        presented = compose_cartoon_chart(m41b_cartoon_composition_chart(), mode="presentation")
    assert presented.style.canvas.sky_color == "#1677A6"
    assert (
        presented.style.grids.constellation_line_color == "#FFE066"
    )
    assert presented.mode.dpi == 160
    assert presented.mode.font_scale > printed.mode.font_scale
    assert presented.detail == printed.detail
    assert presented.context == printed.context


def test_explicit_detail_policy_is_supported():
    fixed = SimpleNamespace(
        resolve=lambda context, mode: ResolvedDetail(
            star_magnitude_limit=2.0,
            enabled_layers=frozenset({"stars"}),
        )
    )
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        composition = compose_cartoon_chart(
            m41b_cartoon_composition_chart(),
            detail_policy=fixed,
        )
    assert composition.detail.star_magnitude_limit == pytest.approx(2.0)
    assert composition.detail.enabled_layers == frozenset({"stars"})


def test_detail_overrides_apply_without_touching_style():
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        composition = compose_cartoon_chart(
            m41b_cartoon_composition_chart(),
            mode="presentation",
            detail_overrides=DetailOverrides(
                star_magnitude_limit=0.5,
            ),
        )
    assert composition.detail.star_magnitude_limit == pytest.approx(0.5)
    assert composition.style.canvas.sky_color == "#1677A6"

# Contracts consolidated from test_milestone41g_regional_horizon_milky_way.py.
from pathlib import Path
from types import SimpleNamespace

from wenu.charts.context import BoundaryKind
from wenu.charts.detail_application import composition_layer_options


class RecordingStyle:
    def __init__(self):
        self.horizon_altitude_deg = "not called"

    def layer_options(self, sky, *, horizon_altitude_deg=None):
        self.horizon_altitude_deg = horizon_altitude_deg
        return {}


class EmptySky:
    layers = ()


class EmptyDetail:
    star_magnitude_limit = None
    galaxy_magnitude_limit = None
    constellation_star_mode = None
    extra_star_ids = frozenset()

    def layer_enabled(self, name):
        return True


def composition(boundary_kind):
    style = RecordingStyle()
    value = SimpleNamespace(
        style=style,
        detail=EmptyDetail(),
        context=SimpleNamespace(boundary_kind=boundary_kind),
    )
    return value, style


def test_rectangular_regional_composition_disables_horizon_clipping():
    value, style = composition(BoundaryKind.RECTANGULAR)
    composition_layer_options(
        value,
        EmptySky(),
        reload_catalogues=False,
    )
    assert style.horizon_altitude_deg == -90.0


def test_non_rectangular_chart_retains_style_horizon_default():
    value, style = composition(BoundaryKind.CIRCULAR)
    composition_layer_options(
        value,
        EmptySky(),
        reload_catalogues=False,
    )
    assert style.horizon_altitude_deg is None


def test_cartoon_example_enables_milky_way_only_in_presentation():
    namespace = {}
    source = Path("tests/fixtures/example_regressions/cartoon_modes_explicit_labels.py").read_text()
    exec(compile(source, "cartoon_modes_explicit_labels.py", "exec"), namespace)
    assert "milky_way" not in namespace["content_layers"]("print")
    assert "milky_way" in namespace["content_layers"]("presentation")


def test_cartoon_example_uses_canonical_polygon_projection():
    source = Path("tests/fixtures/example_regressions/cartoon_modes_explicit_labels.py").read_text()
    assert "clip_polygons_to_projection_cap" not in source
    assert 'milky_way_options["prepare"]' not in source
    assert "horizon_altitude_deg=-90.0" not in source

# Contracts consolidated from test_milestone43b_atlas_composition_contracts.py.
"""Milestone 43B contracts for the canonical atlas control plane."""

import numpy as np
import pytest

from wenu import (
    AtlasChartStyle,
    CelestialSphere,
    FixedDetailPolicy,
    PresentationMode,
    PrintMode,
    RegionalChart,
    ResolvedDetail,
    compose_chart,
)
from wenu.geometry.projected import ProjectedPoints
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.sky_layer import SkyLayer


def m43b_atlas_composition_contracts_regional_chart():
    return RegionalChart(
        center_alt_deg=35.0,
        center_az_deg=210.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )


@pytest.mark.parametrize("requested", (None, "print", "paper", PrintMode()))
def test_print_mode_has_one_stable_identity(requested):
    composition = compose_chart(
        m43b_atlas_composition_contracts_regional_chart(),
        style="atlas",
        mode=requested,
    )
    assert composition.style_name == "atlas"
    assert composition.mode_name == "print"
    assert isinstance(composition.style, AtlasChartStyle)


@pytest.mark.parametrize(
    "requested",
    ("presentation", PresentationMode()),
)
def test_presentation_mode_has_one_stable_identity(requested):
    composition = compose_chart(
        m43b_atlas_composition_contracts_regional_chart(),
        style="atlas",
        mode=requested,
    )
    assert composition.style_name == "atlas"
    assert composition.mode_name == "presentation"
    assert isinstance(composition.style, AtlasChartStyle)


def test_direct_atlas_style_construction_remains_supported():
    style = AtlasChartStyle()
    composition = compose_chart(m43b_atlas_composition_contracts_regional_chart(), style=style)
    assert composition.style is style
    assert composition.style_name == "atlas"


def test_unknown_style_and_mode_names_are_rejected():
    chart = m43b_atlas_composition_contracts_regional_chart()
    with pytest.raises(ValueError, match="Unknown chart style"):
        compose_chart(chart, style="special-style")
    with pytest.raises(ValueError, match="Unknown chart mode"):
        compose_chart(chart, style="atlas", mode="slides")


def test_mode_resolution_changes_no_chart_geometry_or_content():
    chart = m43b_atlas_composition_contracts_regional_chart()
    detail = FixedDetailPolicy(
        ResolvedDetail(
            star_magnitude_limit=7.0,
            enabled_layers=frozenset({"stars", "open_clusters"}),
        )
    )
    printed = compose_chart(
        chart,
        style="atlas",
        mode="print",
        detail=detail,
    )
    presented = compose_chart(
        chart,
        style="atlas",
        mode="presentation",
        detail=detail,
    )

    assert printed.context == presented.context == chart.chart_context
    assert printed.context.viewport == chart.viewport
    assert printed.context.clip_boundary is None
    assert printed.detail == presented.detail
    assert printed.style != presented.style
    assert printed.mode != presented.mode


class SpyLayer(SkyLayer):
    layer_name = "open_clusters"

    def __init__(self):
        self.received = None
        self.output = SphericalPoints(
            lon_deg=np.asarray([20.0]),
            lat_deg=np.asarray([30.0]),
        )

    def spherical_geometry(self, observer, **options):
        self.received = (observer, options)
        return self.output


class IdentityProjection:
    def project_geometry(self, spherical):
        return ProjectedPoints(
            x=spherical.lon_deg,
            y=spherical.lat_deg,
        )


class RecordingRenderer:
    def __init__(self):
        self.viewport = None

    def apply_viewport(self, viewport):
        self.viewport = viewport

    def draw(self, projected, **options):
        return (projected, options)


def test_resolved_detail_configures_layer_but_layer_produces_geometry():
    observer = object()
    sky = CelestialSphere(observer)
    layer = SpyLayer()
    sky.add(layer)
    composition = compose_chart(
        m43b_atlas_composition_contracts_regional_chart(),
        style="atlas",
        detail=FixedDetailPolicy(
            ResolvedDetail(
                enabled_layers=frozenset({"open_clusters"}),
                minimum_open_cluster_size_arcmin=12.0,
            )
        ),
    )
    application = composition.layer_options(
        sky,
        reload_catalogues=False,
    )

    result = sky.draw_chart(
        projection=IdentityProjection(),
        renderer=RecordingRenderer(),
        viewport=composition.context.viewport,
        layer_options=application.layer_options,
    )

    assert layer.received == (
        observer,
        {"minimum_size_arcmin": 12.0},
    )
    assert result.layers[0].spherical is layer.output

# Contracts consolidated from test_milestone43g_canonical_cartoon_style.py.
"""Milestone 43G contracts for cartoon style on the canonical pipeline."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time

from wenu import (
    CartoonChartStyle,
    CartoonDetailPolicy,
    CircumpolarChart,
    DetailOverrides,
    FixedDetailPolicy,
    FullSkyChart,
    RegionalChart,
    ResolvedDetail,
    cartoon_chart_style,
    compose_cartoon_chart,
    compose_chart,
)


def charts():
    observer = SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-08-02T00:00:00"),
            location=EarthLocation(
                lat=-32.44 * u.deg,
                lon=-71.23 * u.deg,
            ),
        )
    )
    return (
        RegionalChart(
            center_alt_deg=35.0,
            center_az_deg=210.0,
            field_width_deg=30.0,
            field_height_deg=20.0,
        ),
        FullSkyChart(),
        CircumpolarChart(
            observer=observer,
            pole="south",
            limiting_declination_deg=-30.0,
        ),
    )


@pytest.mark.parametrize("chart", charts())
@pytest.mark.parametrize("mode", ("print", "presentation"))
def test_named_cartoon_style_uses_canonical_composition(chart, mode):
    composition = compose_chart(chart, style="cartoon", mode=mode)

    assert composition.style_name == "cartoon"
    assert composition.mode_name == mode
    assert isinstance(composition.style, CartoonChartStyle)
    assert composition.detail == CartoonDetailPolicy().resolve(
        composition.context,
        composition.mode,
    )
    assert composition.detail.enabled_layers == frozenset(
        {"stars", "constellation_lines", "constellation_labels"}
    )
    assert composition.detail.constellation_star_mode == "selected"


@pytest.mark.parametrize("chart", charts())
def test_cartoon_mode_changes_no_chart_geometry_or_content(chart):
    printed = compose_chart(chart, style="cartoon", mode="print")
    presented = compose_chart(
        chart,
        style="cartoon",
        mode="presentation",
    )

    assert_same_geometry(printed.context, presented.context)
    assert_same_geometry(presented.context, chart.chart_context)
    assert printed.detail == presented.detail
    assert printed.style.canvas.sky_color == "white"
    assert presented.style.canvas.sky_color == "#1677A6"


def assert_same_geometry(left, right):
    """Compare contexts without ambiguous NumPy array equality."""
    assert replace(left, clip_boundary=None) == replace(
        right,
        clip_boundary=None,
    )
    left_boundary = left.clip_boundary
    right_boundary = right.clip_boundary
    if left_boundary is None or right_boundary is None:
        assert left_boundary is right_boundary is None
        return
    assert left_boundary.closed == right_boundary.closed
    assert left_boundary.name == right_boundary.name
    np.testing.assert_allclose(left_boundary.x, right_boundary.x)
    np.testing.assert_allclose(left_boundary.y, right_boundary.y)


def test_explicit_detail_policy_replaces_cartoon_recommendation():
    detail = FixedDetailPolicy(
        ResolvedDetail(
            star_magnitude_limit=4.0,
            enabled_layers=frozenset({"stars", "milky_way"}),
        )
    )
    composition = compose_chart(
        charts()[0],
        style="cartoon",
        detail=detail,
    )

    assert composition.detail.star_magnitude_limit == 4.0
    assert composition.detail.enabled_layers == frozenset(
        {"stars", "milky_way"}
    )


def test_optional_milky_way_is_render_local():
    chart = charts()[0]
    with_milky_way = compose_chart(
        chart,
        style="cartoon",
        detail_overrides=DetailOverrides(
            enabled_layers=frozenset(
                {
                    "stars",
                    "constellation_lines",
                    "constellation_labels",
                    "milky_way",
                }
            )
        ),
    )
    default_again = compose_chart(chart, style="cartoon")

    assert with_milky_way.detail.layer_enabled("milky_way")
    assert not default_again.detail.layer_enabled("milky_way")


def test_explicit_constellation_label_controls_remain_supported():
    style = cartoon_chart_style(
        "print",
        constellation_label_positions={"Sco": "ur"},
        constellation_label_offsets={"Sco": (0.1, -0.2)},
    )
    composition = compose_chart(
        charts()[0],
        style=style,
        detail=CartoonDetailPolicy(),
    )

    assert composition.style_name == "cartoon"
    assert composition.style.grids.constellation_label_offsets["Sco"] == (
        pytest.approx(0.34),
        pytest.approx(0.0),
    )


def test_legacy_wrapper_is_not_adapted_twice():
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        legacy = compose_cartoon_chart(
            charts()[0],
            mode="presentation",
        )
    canonical = compose_chart(
        charts()[0],
        style="cartoon",
        mode="presentation",
    )

    assert legacy.style.stars.area_scale == canonical.style.stars.area_scale
    assert legacy.style.canvas.label_fontsize == (
        canonical.style.canvas.label_fontsize
    )
    assert legacy.style.output_mode_name == "presentation"

# Contracts consolidated from test_milestone44fb3_cartoon_palette_and_boundary.py.
"""Milestone 44F.B.3 trichromatic cartoon products."""

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import pytest

from wenu import FullSkyChart, cartoon_chart_style, compose_chart
from wenu.charts.cartoon_modes import (
    CARTOON_PRESENTATION_PALETTE,
    CARTOON_PRINT_PALETTE,
)


YELLOW = "#FFE066"
BLUE = "#1677A6"


def test_presentation_palette_retains_base_colors_and_distinct_grids():
    colors = set(vars(CARTOON_PRESENTATION_PALETTE).values())
    assert {
        BLUE,
        YELLOW,
        "#FFFFFF",
    } <= colors
    assert len({
        CARTOON_PRESENTATION_PALETTE.equatorial_grid,
        CARTOON_PRESENTATION_PALETTE.ecliptic_grid,
        CARTOON_PRESENTATION_PALETTE.galactic_grid,
    }) == 3


def test_print_palette_adds_semantic_grid_colors():
    assert set(vars(CARTOON_PRINT_PALETTE).values()) == {
        "white",
        "#000000",
        "#707070",
        "black",
        "orange",
        "blue",
    }


def test_presentation_uses_yellow_except_semantic_coordinate_grids():
    style = cartoon_chart_style("presentation")

    assert style.stars.color == YELLOW
    assert style.canvas.foreground_color == YELLOW
    assert style.grids.constellation_line_color == YELLOW
    assert style.grids.constellation_label_color == YELLOW
    assert style.grids.boundary_color == YELLOW
    assert style.grids.equatorial_color == "#FFFFFF"
    assert style.grids.ecliptic_color == "#FFA500"
    assert style.grids.galactic_color == "#66CCFF"
    assert style.isophotes.milky_way_color == YELLOW
    assert style.isophotes.milky_way_alpha == pytest.approx(0.0)
    assert style.isophotes.milky_way_contour_color == YELLOW
    assert style.isophotes.milky_way_contour_linestyle == ":"
    assert style.isophotes.lmc_alpha == pytest.approx(0.0)
    assert style.isophotes.lmc_edge_color == YELLOW
    assert style.isophotes.lmc_linestyle == ":"
    assert style.isophotes.smc_alpha == pytest.approx(0.0)
    assert style.isophotes.smc_edge_color == YELLOW
    assert style.isophotes.smc_linestyle == ":"
    assert style.deep_sky.galaxy_edge_color == YELLOW
    assert style.legend.facecolor == BLUE
    assert style.legend.edgecolor == YELLOW
    assert style.legend.text_color == YELLOW
    assert style.canvas.footer_color == "#FFFFFF"


def test_print_uses_black_for_structure_and_footer():
    style = cartoon_chart_style("print")

    assert style.canvas.sky_color == "white"
    assert style.stars.color == "#000000"
    assert style.canvas.foreground_color == "#000000"
    assert style.grids.constellation_line_color == "#000000"
    assert style.grids.boundary_color == "#000000"
    assert style.isophotes.milky_way_alpha == pytest.approx(0.0)
    assert style.isophotes.milky_way_contour_color == "#000000"
    assert style.isophotes.lmc_edge_color == "#000000"
    assert style.isophotes.smc_edge_color == "#000000"
    assert style.legend.facecolor == "white"
    assert style.legend.edgecolor == "#000000"
    assert style.legend.text_color == "#000000"
    assert style.canvas.footer_color == "#000000"


@pytest.mark.parametrize(
    ("mode", "color"),
    [("presentation", YELLOW), ("print", "#000000")],
)
def test_cartoon_title_frame_and_circular_boundary_share_structure_color(
    mode,
    color,
):
    style = cartoon_chart_style(mode)
    figure, ax = plt.subplots()
    style.configure_axes(ax, title="Context")

    assert ax.title.get_color() == color
    assert {spine.get_edgecolor() for spine in ax.spines.values()} == {
        to_rgba(color),
    }
    assert style.chart_boundary_style()["edgecolor"] == color
    assert style.chart_boundary_style()["linewidth"] == pytest.approx(
        style.grids.constellation_linewidth
    )
    plt.close(figure)


def test_planisphere_keeps_horizon_geometry_independent_of_style():
    chart = FullSkyChart(horizon_altitude_deg=0.0)
    printed = cartoon_chart_style("print").chart_boundary_style()
    presented = cartoon_chart_style("presentation").chart_boundary_style()

    assert chart.horizon_altitude_deg == pytest.approx(0.0)
    assert chart.horizon.name == "horizon"
    assert chart.horizon.closed is True
    assert printed["edgecolor"] == "#000000"
    assert presented["edgecolor"] == YELLOW


def test_canonical_cartoon_composition_keeps_mode_context_methods():
    composition = compose_chart(
        FullSkyChart(),
        style="cartoon",
        mode="presentation",
    )
    figure, ax = plt.subplots()

    composition.style.configure_axes(ax, title="Context")

    assert ax.title.get_color() == YELLOW
    assert {spine.get_edgecolor() for spine in ax.spines.values()} == {
        to_rgba(YELLOW),
    }
    assert composition.style.chart_boundary_style()["edgecolor"] == YELLOW
    plt.close(figure)

# Contracts consolidated from test_milestone44g1_circumpolar_boundary_style.py.
"""Milestone 44G.1 circumpolar boundary-style ownership."""

from wenu import CircumpolarChart, cartoon_chart_style
from wenu.charts.presets import AtlasChartStyle


class Delegate:
    def __init__(self):
        self.options = None

    def render(self, *args, **kwargs):
        self.options = kwargs
        return "rendered"


def chart_with_delegate(monkeypatch):
    delegate = Delegate()
    monkeypatch.setattr(
        CircumpolarChart,
        "binocular_chart",
        property(lambda self: delegate),
    )
    return CircumpolarChart(object(), -69.75), delegate


def test_atlas_boundary_uses_resolved_grid_appearance(monkeypatch):
    chart, delegate = chart_with_delegate(monkeypatch)
    style = AtlasChartStyle()

    result = chart.render(
        object(),
        object(),
        style=style,
        coordinate_label_anchor=object(),
    )

    boundary = delegate.options["boundary_style"]
    assert result == "rendered"
    assert boundary["edgecolor"] == style.grids.boundary_color
    assert boundary["linewidth"] == style.grids.boundary_linewidth
    assert boundary["linestyle"] == style.grids.boundary_linestyle
    assert boundary["alpha"] == style.grids.boundary_alpha
    assert boundary["facecolor"] == "none"


def test_cartoon_boundary_uses_mode_specific_contract(monkeypatch):
    chart, delegate = chart_with_delegate(monkeypatch)
    style = cartoon_chart_style("presentation")

    chart.render(
        object(),
        object(),
        style=style,
        coordinate_label_anchor=object(),
    )

    boundary = delegate.options["boundary_style"]
    assert boundary["edgecolor"] == "#FFE066"
    assert boundary["linewidth"] == style.grids.constellation_linewidth


def test_explicit_boundary_style_retains_precedence(monkeypatch):
    chart, delegate = chart_with_delegate(monkeypatch)
    explicit = {"edgecolor": "magenta", "linewidth": 3.0}

    chart.render(
        object(),
        object(),
        style=AtlasChartStyle(),
        boundary_style=explicit,
        coordinate_label_anchor=object(),
    )

    assert delegate.options["boundary_style"] is explicit

# Contracts consolidated from test_milestone44g2_atlas_title_circular_frame.py.
"""Atlas presentation context and circular frame regression tests."""

import matplotlib.pyplot as plt

from wenu import CircumpolarChart, MatplotlibRenderer, Observer, compose_chart


def m44g2_atlas_title_circular_frame_chart():
    return CircumpolarChart(
        Observer(location="La Ligua", time="2026-08-15 21:00"),
        limiting_declination_deg=-69.75,
        pole="south",
    )


def test_atlas_presentation_title_uses_foreground_palette():
    composition = compose_chart(
        m44g2_atlas_title_circular_frame_chart(), style="atlas", mode="presentation"
    )
    figure, ax = plt.subplots()
    composition.style.configure_axes(ax, title="Circumpolar")

    assert ax.title.get_color() == composition.style.canvas.foreground_color
    plt.close(figure)


def test_circular_renderer_suppresses_rectangular_axes_frame():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)

    renderer.set_axes_frame_visible(False)

    assert all(not spine.get_visible() for spine in ax.spines.values())
    plt.close(figure)

# Contracts consolidated from test_milestone44h1_binocular_boundary_contract.py.
"""Milestone 44H.1 binocular aperture appearance contracts."""

from wenu import BinocularChart, cartoon_chart_style
from wenu.charts.presets import AtlasChartStyle


class Renderer:
    def __init__(self):
        self.boundary_style = None

    def set_clip_boundary(self, boundary, *, style=None):
        self.boundary_style = style

    def set_axes_frame_visible(self, visible):
        self.frame_visible = visible


class Sky:
    stars = None
    nonstellar = None
    milky_way_isophotes = None
    magellanic_cloud_isophotes = {}
    galaxies = None
    globular_clusters = None
    open_clusters = None
    supernova_remnants = None
    planetary_nebulae = None
    constellation_lines = None
    constellation_labels = None
    constellation_boundaries = None
    points = None
    layers = ()

    def draw_chart(self, **kwargs):
        return "rendered"


def test_atlas_binocular_boundary_uses_resolved_grid_appearance():
    renderer = Renderer()
    style = AtlasChartStyle()

    result = BinocularChart(45.0, 180.0).render(
        Sky(), renderer, style=style
    )

    assert result == "rendered"
    assert (
        renderer.boundary_style["edgecolor"]
        == style.grids.boundary_color
    )
    assert (
        renderer.boundary_style["linewidth"]
        == style.grids.boundary_linewidth
    )
    assert renderer.frame_visible is False


def test_cartoon_binocular_boundary_uses_mode_palette():
    renderer = Renderer()
    style = cartoon_chart_style("presentation")

    BinocularChart(45.0, 180.0).render(Sky(), renderer, style=style)

    assert renderer.boundary_style["edgecolor"] == "#FFE066"
    assert renderer.boundary_style["linewidth"] == (
        style.grids.constellation_linewidth
    )


def test_explicit_binocular_boundary_style_retains_precedence():
    renderer = Renderer()
    explicit = {"edgecolor": "magenta", "linewidth": 3.0}

    BinocularChart(45.0, 180.0).render(
        Sky(),
        renderer,
        style=AtlasChartStyle(),
        boundary_style=explicit,
    )

    assert renderer.boundary_style == explicit

# Contracts consolidated from test_milestone44h11_circular_transparency.py.
"""Milestone 44H.1.1 circular-background transparency contracts."""

import matplotlib.pyplot as plt

from wenu import BinocularChart, MatplotlibRenderer, compose_chart
from wenu.charts.export_workflow import _composition_export_options
from wenu.charts.regional import ExportOptions
from wenu.geometry.projected import ProjectedCurve


def circle():
    return ProjectedCurve(
        x=[-1.0, 0.0, 1.0, 0.0],
        y=[0.0, 1.0, 0.0, -1.0],
        closed=True,
    )


def test_circular_background_uses_transparent_canvas(tmp_path):
    figure, axes = plt.subplots(figsize=(2.0, 2.0), dpi=50)
    renderer = MatplotlibRenderer(axes)
    axes.set_xlim(-1.2, 1.2)
    axes.set_ylim(-1.2, 1.2)
    axes.set_aspect("equal")
    axes.set_xticks([])
    axes.set_yticks([])

    background = renderer.set_circular_background(
        circle(),
        color="#123456",
    )
    renderer.set_clip_boundary(
        circle(),
        style={"facecolor": "none", "edgecolor": "black"},
    )
    output = tmp_path / "circular.png"
    ExportOptions(
        dpi=50,
        bbox_inches=None,
        transparent=True,
        facecolor="none",
    ).save(figure, output)

    image = plt.imread(output)
    assert image[0, 0, 3] == 0.0
    center = image[image.shape[0] // 2, image.shape[1] // 2]
    assert center[3] == 1.0
    assert background.get_facecolor()[3] == 1.0
    plt.close(figure)


def test_circular_composition_defaults_to_transparent_export():
    composition = compose_chart(
        BinocularChart(45.0, 180.0),
        style="cartoon",
        mode="presentation",
    )

    options = _composition_export_options(composition)

    assert options.transparent is True
    assert options.facecolor == "none"
