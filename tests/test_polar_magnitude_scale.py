"""Shared polar-only magnitude-scale semantics."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from wenu import (
    PolarMagnitudeScalePlacement,
    PolarMagnitudeScaleRequest,
    default_polar_magnitude_scale,
)
from wenu.charts.detail_application import configured_stellar_symbol_sizes
from wenu.charts.polar_planisphere_style import polar_planisphere_chart_style
from wenu.configuration import translate_style_mode_defaults


def test_default_scale_has_requested_bright_and_ordinary_intervals():
    scale = default_polar_magnitude_scale()

    assert scale.title == "Magnitud"
    assert scale.bright_cutoff_magnitude == pytest.approx(0.5)
    assert scale.limiting_magnitude == pytest.approx(5.0)
    assert tuple(
        (entry.lower_magnitude, entry.upper_magnitude)
        for entry in scale.bright_entries
    ) == ((-1.5, -1.0), (-1.0, -0.5), (-0.5, 0.0), (0.0, 0.5))
    assert tuple(
        (entry.lower_magnitude, entry.upper_magnitude)
        for entry in scale.ordinary_entries
    ) == ((0.5, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0))
    assert tuple(entry.symbol for entry in scale.entries) == (
        *(("five_point",) * 4),
        *(("round",) * 5),
    )


def test_entries_reuse_the_exact_polar_stellar_size_law():
    defaults = translate_style_mode_defaults()
    stars = polar_planisphere_chart_style(
        defaults.atlas,
        defaults.polar_planisphere_palette,
    ).stars
    scale = PolarMagnitudeScaleRequest().resolve(
        stars,
        limiting_magnitude=5.0,
    )

    magnitudes = np.asarray(
        [entry.representative_magnitude for entry in scale.entries]
    )
    ordinary, bright, bright_mask = configured_stellar_symbol_sizes(
        magnitudes,
        stars,
    )
    expected = np.where(bright_mask, bright, ordinary)
    assert tuple(entry.marker_area_points2 for entry in scale.entries) == (
        pytest.approx(expected)
    )


def test_scale_is_immutable_validated_public_and_manifest_ready():
    scale = default_polar_magnitude_scale()
    record = scale.manifest_record()

    assert record["bright_cutoff_magnitude"] == pytest.approx(0.5)
    assert len(record["entries"]) == 9
    with pytest.raises(FrozenInstanceError):
        scale.title = "Otra"
    with pytest.raises(ValueError, match="0.5 cutoff"):
        PolarMagnitudeScaleRequest(bright_cutoff_magnitude=0.18)
    with pytest.raises(ValueError, match="positive"):
        PolarMagnitudeScalePlacement(
            title_position_mm=(0.0, 0.0),
            bright_center_mm=(0.0, 0.0),
            ordinary_center_mm=(0.0, 0.0),
            entry_spacing_mm=0.0,
        )

    import wenu

    for name in (
        "PolarMagnitudeScale",
        "PolarMagnitudeScaleEntry",
        "PolarMagnitudeScalePlacement",
        "PolarMagnitudeScaleRequest",
        "PolarMagnitudeScaleRendering",
        "default_polar_magnitude_scale",
        "draw_polar_magnitude_scale",
    ):
        assert name in wenu.__all__
