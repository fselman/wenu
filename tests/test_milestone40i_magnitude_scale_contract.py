from pathlib import Path

import numpy as np
import pytest

from wenu import (
    StellarMagnitudeEntry,
    StellarMagnitudeScale,
    integer_magnitude_range,
    stellar_magnitude_scale,
)
from wenu.rendering.preparation import magnitude_sizes


def test_integer_range_is_inclusive_and_supports_negative_magnitudes():
    assert integer_magnitude_range(-1.46, 6.3) == (
        -1,
        0,
        1,
        2,
        3,
        4,
        5,
        6,
    )


def test_integer_range_uses_ceil_and_floor():
    assert integer_magnitude_range(0.2, 4.9) == (1, 2, 3, 4)
    assert integer_magnitude_range(2.2, 2.8) == ()


def test_reversed_or_nonfinite_limits_are_rejected():
    with pytest.raises(ValueError):
        integer_magnitude_range(6.0, -1.0)
    with pytest.raises(ValueError):
        integer_magnitude_range(np.nan, 6.0)
    with pytest.raises(ValueError):
        integer_magnitude_range(-1.0, np.inf)


def test_scale_uses_exact_chart_magnitude_area_law():
    scale = stellar_magnitude_scale(
        -1.46,
        4.8,
        area_scale=2.25,
        color="black",
        alpha=0.8,
    )
    expected = magnitude_sizes(scale.magnitudes) * 2.25
    assert isinstance(scale, StellarMagnitudeScale)
    assert all(
        isinstance(item, StellarMagnitudeEntry)
        for item in scale.entries
    )
    assert scale.areas == pytest.approx(tuple(expected))
    assert scale.color == "black"
    assert scale.alpha == pytest.approx(0.8)


def test_brighter_entries_have_larger_areas():
    scale = stellar_magnitude_scale(-1.0, 6.0)
    assert all(
        first > second
        for first, second in zip(scale.areas, scale.areas[1:])
    )


def test_empty_integer_range_produces_empty_scale():
    scale = stellar_magnitude_scale(2.2, 2.8)
    assert scale.entries == ()
    assert scale.magnitudes == ()
    assert scale.areas == ()


def test_invalid_area_scale_is_rejected():
    with pytest.raises(ValueError):
        stellar_magnitude_scale(0.0, 5.0, area_scale=0.0)
    with pytest.raises(ValueError):
        stellar_magnitude_scale(0.0, 5.0, area_scale=np.nan)


def test_contract_module_has_no_matplotlib_dependency():
    import wenu.charts.magnitude_legend as module

    source = Path(module.__file__).read_text().lower()
    assert "matplotlib" not in source
