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

    sizing = binocular_object.BINOCULAR_STELLAR_SIZING
    assert sizing == SIZING
    assert binocular_object.STAR_MAGNITUDE_LIMIT == pytest.approx(11.0)
