"""Current stellar symbols contracts."""

# Contracts consolidated from test_milestone38a_stellar_classification.py.
from io import BytesIO
from types import SimpleNamespace

import numpy as np
from matplotlib.path import Path as MatplotlibPath

from wenu.objects.stars import (
    Stars,
    _attach_hipparcos_semantics,
    _hipparcos_semantics,
)
from wenu.rendering.symbols import DEFAULT_SYMBOLS


def hipparcos_line(
    hip,
    *,
    variability_type="",
    variability_annex="",
    light_curve_annex="",
    ccdm_id="",
    ccdm_entries="",
    components="",
    multiple_annex="",
    theta="",
    separation="",
    delta_hp="",
):
    line = [" "] * 449

    def put(start, end, value):
        width = end - start
        text = str(value)
        line[start:end] = list(text.rjust(width))

    line[0] = "H"
    put(8, 14, hip)
    put(321, 322, variability_type)
    put(323, 324, variability_annex)
    put(325, 326, light_curve_annex)
    line[327:337] = list(str(ccdm_id).ljust(10)[:10])
    put(340, 342, ccdm_entries)
    put(343, 345, components)
    put(346, 347, multiple_annex)
    put(355, 358, theta)
    put(359, 366, separation)
    put(373, 378, delta_hp)
    return "".join(line)


def test_parser_distinguishes_variable_constant_and_colour_revision():
    payload = "\n".join(
        (
            hipparcos_line(1, variability_type="P", variability_annex="1"),
            hipparcos_line(2, variability_type="C"),
            hipparcos_line(3, variability_type="R"),
            hipparcos_line(4, variability_type="U", light_curve_annex="B"),
        )
    ).encode("ascii")
    parsed = _hipparcos_semantics(payload)
    assert parsed[1]["is_variable"] is True
    assert parsed[2]["is_variable"] is False
    assert parsed[3]["is_variable"] is False
    assert parsed[4]["is_variable"] is True
    assert parsed[1]["variability_annex"] == "1"
    assert parsed[4]["light_curve_annex"] == "B"


def test_parser_preserves_positive_multiplicity_evidence():
    payload = "\n".join(
        (
            hipparcos_line(
                10,
                ccdm_id="12345+6789",
                ccdm_entries=2,
                components=2,
                multiple_annex="C",
                theta=37,
                separation="8.608",
                delta_hp="1.14",
            ),
            hipparcos_line(11),
        )
    ).encode("ascii")
    parsed = _hipparcos_semantics(payload)
    assert parsed[10]["is_multiple"] is True
    assert parsed[10]["ccdm_id"] == "12345+6789"
    assert parsed[10]["component_count"] == 2
    assert parsed[10]["component_position_angle_deg"] == 37.0
    assert parsed[10]["component_separation_arcsec"] == 8.608
    assert parsed[10]["component_magnitude_difference"] == 1.14
    assert parsed[11]["is_multiple"] is False


def test_semantics_attach_in_source_index_order():
    import pandas as pd

    source = pd.DataFrame(
        {"magnitude": [1.0, 2.0]},
        index=[20, 10],
    )
    semantics = {
        10: {"is_variable": True, "variability_type": "P"},
        20: {"is_multiple": True, "component_count": 2},
    }
    result = _attach_hipparcos_semantics(source, semantics)
    assert result["is_variable"].tolist() == [False, True]
    assert result["is_multiple"].tolist() == [True, False]
    assert result["variability_type"].tolist() == ["", "P"]


def test_stellar_geometry_exposes_aligned_semantic_metadata():
    import pandas as pd

    stars = Stars(observer=None)
    stars.hip_df = pd.DataFrame(
        {
            "magnitude": [1.5, 2.5],
            "variability_type": ["P", ""],
            "variability_annex": ["1", ""],
            "light_curve_annex": ["A", ""],
            "is_variable": [True, False],
            "ccdm_id": ["", "12345+6789"],
            "ccdm_entry_count": [0, 2],
            "component_count": [0, 2],
            "multiple_annex": ["", "C"],
            "component_position_angle_deg": [np.nan, 45.0],
            "component_separation_arcsec": [np.nan, 2.0],
            "component_magnitude_difference": [np.nan, 1.0],
            "is_multiple": [False, True],
        },
        index=[100, 200],
    )
    stars.compute_altaz = lambda **kwargs: (
        np.asarray((30.0, 40.0)),
        np.asarray((120.0, 130.0)),
    )
    geometry = stars.spherical_geometry(SimpleNamespace())
    assert geometry.ids.tolist() == [100, 200]
    assert geometry.metadata["is_variable"].tolist() == [True, False]
    assert geometry.metadata["is_multiple"].tolist() == [False, True]
    assert geometry.metadata["multiple_annex"].tolist() == ["", "C"]


def test_symbol_library_has_independent_stellar_symbols():
    variable = DEFAULT_SYMBOLS.variable_star
    multiple = DEFAULT_SYMBOLS.multiple_star
    assert isinstance(variable, MatplotlibPath)
    assert isinstance(multiple, MatplotlibPath)
    assert variable is not multiple
    assert DEFAULT_SYMBOLS["variable_star"] is variable
    assert DEFAULT_SYMBOLS["multiple_star"] is multiple
    assert np.max(np.abs(variable.vertices)) <= 1.0
    assert np.max(np.abs(multiple.vertices)) <= 1.0


def test_stellar_geometry_supplies_defaults_for_minimal_dataframe():
    import pandas as pd

    stars = Stars(observer=None)
    stars.hip_df = pd.DataFrame(
        {"magnitude": [1.0, 2.0]},
        index=[10, 20],
    )
    stars.compute_altaz = lambda **kwargs: (
        np.asarray((30.0, 40.0)),
        np.asarray((120.0, 130.0)),
    )
    geometry = stars.spherical_geometry(SimpleNamespace())
    assert geometry.metadata["is_variable"].tolist() == [False, False]
    assert geometry.metadata["is_multiple"].tolist() == [False, False]
    assert geometry.metadata["variability_type"].tolist() == ["", ""]
    assert geometry.metadata["component_count"].tolist() == [0, 0]

# Contracts consolidated from test_milestone38b_stellar_symbol_rendering.py.
"""Milestone 38B tests for vectorized stellar symbol overlays."""

from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu.charts.styles import PublicationStyle
from wenu.geometry.projected import ProjectedPoints
from wenu.rendering import layers
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.rendering.symbols import DEFAULT_SYMBOLS


def points():
    return ProjectedPoints(
        x=np.asarray((0.0, 1.0, 2.0, np.nan)),
        y=np.asarray((0.0, 1.0, 2.0, np.nan)),
        ids=np.asarray((1, 2, 3, 4)),
    )


def test_renderer_draws_each_overlay_as_one_vectorized_collection():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    artists = renderer.draw(
        points(),
        style={"s": 5.0, "color": "white"},
        point_overlays=[
            {
                "mask": [True, False, True, True],
                "style": {
                    "marker": DEFAULT_SYMBOLS.variable_star,
                    "s": 20.0,
                    "facecolors": "none",
                    "edgecolors": "cyan",
                },
            },
            {
                "mask": [False, True, True, False],
                "style": {
                    "marker": DEFAULT_SYMBOLS.multiple_star,
                    "s": 20.0,
                    "facecolors": "none",
                    "edgecolors": "gold",
                },
            },
        ],
    )
    try:
        assert len(artists) == 3
        assert len(artists[0].get_offsets()) == 3
        assert len(artists[1].get_offsets()) == 2
        assert len(artists[2].get_offsets()) == 2
    finally:
        plt.close(figure)


def test_renderer_rejects_misaligned_overlay_mask():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    try:
        with pytest.raises(ValueError, match="must match"):
            renderer.draw(
                points(),
                point_overlays=[{"mask": [True, False]}],
            )
    finally:
        plt.close(figure)


def spherical_metadata():
    return SimpleNamespace(
        metadata={
            "magnitude": np.asarray((1.0, 2.0, 3.0)),
            "is_variable": np.asarray((True, False, True)),
            "is_multiple": np.asarray((False, True, True)),
        }
    )


def test_stellar_symbol_overlays_are_independently_optional():
    plain = PublicationStyle()._star_render_options(
        spherical_metadata(),
        None,
    )
    assert plain["point_overlays"] == []

    variable = PublicationStyle(
        draw_variable_star_symbols=True,
    )._star_render_options(spherical_metadata(), None)
    assert len(variable["point_overlays"]) == 1
    assert variable["point_overlays"][0]["mask"].tolist() == [
        True, False, True,
    ]

    multiple = PublicationStyle(
        draw_multiple_star_symbols=True,
    )._star_render_options(spherical_metadata(), None)
    assert len(multiple["point_overlays"]) == 1
    assert multiple["point_overlays"][0]["mask"].tolist() == [
        False, True, True,
    ]


def test_stellar_overlay_styles_use_named_layer_zorders():
    options = PublicationStyle(
        draw_variable_star_symbols=True,
        draw_multiple_star_symbols=True,
        variable_star_color="cyan",
        multiple_star_color="gold",
    )._star_render_options(spherical_metadata(), None)
    multiple, variable = options["point_overlays"]
    assert multiple["style"]["zorder"] == layers.MULTIPLE_STARS
    assert variable["style"]["zorder"] == layers.VARIABLE_STARS
    assert multiple["style"]["edgecolors"] == "gold"
    assert variable["style"]["edgecolors"] == "cyan"
    assert layers.STARS < layers.MULTIPLE_STARS < layers.VARIABLE_STARS


def test_base_star_scatter_remains_vectorized():
    options = PublicationStyle(
        draw_variable_star_symbols=True,
        draw_multiple_star_symbols=True,
    )._star_render_options(spherical_metadata(), None)
    assert np.asarray(options["style"]["s"]).shape == (3,)
    assert options["style"]["zorder"] == layers.STARS

# Contracts consolidated from test_milestone44h21_normalized_stellar_symbols.py.
from dataclasses import replace
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from wenu import (
    AtlasChartStyle,
    ChartStyleOverrides,
    StellarMagnitudeSizing,
    stellar_magnitude_scale,
)
from wenu.rendering.preparation import (
    configured_magnitude_sizes,
    magnitude_sizes,
)


SIZING = StellarMagnitudeSizing(
    reference="limiting_magnitude",
    scale=1.0,
    exponent=0.20,
    minimum_area=1.0,
    maximum_area=40.0,
)


def load_binocular_example():
    path = Path("examples/binocular_object.py")
    spec = importlib.util.spec_from_file_location("binocular_object", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_formula_remains_the_default():
    assert np.allclose(
        magnitude_sizes([5.0, 4.0]),
        [1.5, 1.5 * 10.0 ** 0.35],
    )


def test_limiting_magnitude_maps_to_minimum_and_bright_stars_grow():
    areas = configured_magnitude_sizes(
        [11.0, 10.0, 6.0, -1.0],
        SIZING,
        limiting_magnitude=11.0,
    )
    assert areas[0] == pytest.approx(1.0)
    assert np.all(np.diff(areas) > 0.0)
    assert areas[-1] == pytest.approx(40.0)


def test_configuration_is_validated():
    with pytest.raises(ValueError, match="reference"):
        replace(SIZING, reference="unknown")
    with pytest.raises(ValueError, match="maximum_area"):
        replace(SIZING, maximum_area=0.5)


def test_style_override_preserves_configuration_as_typed_state():
    style = ChartStyleOverrides(
        stellar_magnitude_sizing=SIZING
    ).apply(AtlasChartStyle())
    assert style.stars.magnitude_sizing is SIZING


def test_magnitude_legend_uses_the_identical_area_law():
    scale = stellar_magnitude_scale(
        6.0,
        11.0,
        magnitude_sizing=SIZING,
        limiting_magnitude=11.0,
    )
    expected = configured_magnitude_sizes(
        scale.magnitudes,
        SIZING,
        limiting_magnitude=11.0,
    )
    assert np.allclose(scale.areas, expected)


def test_binocular_example_declares_the_normalized_contract():
    binocular_object = load_binocular_example()
    source = Path("examples/binocular_object.py").read_text(encoding="utf-8")

    assert binocular_object.STAR_MAGNITUDE_LIMIT == pytest.approx(11.0)
    assert 'reference="limiting_magnitude"' in source
    assert "scale=1.0" in source
    assert "exponent=0.20" in source
    assert "minimum_area=1.0" in source
    assert "maximum_area=40.0" in source
