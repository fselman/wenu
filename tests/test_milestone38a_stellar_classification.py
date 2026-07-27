from io import BytesIO
from types import SimpleNamespace

import numpy as np
from matplotlib.path import Path

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
    assert isinstance(variable, Path)
    assert isinstance(multiple, Path)
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
