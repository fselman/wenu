from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from wenu import (
    VisibleStarStatistics,
    visible_star_mask,
    visible_star_statistics,
)
from wenu.geometry.viewport import Viewport


def geometries():
    spherical = SimpleNamespace(
        metadata={
            "magnitude": np.asarray(
                [-1.4, 0.2, 3.1, 5.8, 7.0, np.nan]
            )
        }
    )
    projected = SimpleNamespace(
        x=np.asarray([4.0, 0.0, 0.4, 0.8, 0.2, 0.0]),
        y=np.asarray([0.0, 0.0, 0.3, 0.8, 0.1, 0.0]),
    )
    viewport = Viewport.centered(width=2.0, height=2.0)
    return spherical, projected, viewport


def test_statistics_exclude_bright_star_outside_viewport():
    spherical, projected, viewport = geometries()
    result = visible_star_statistics(
        spherical,
        projected,
        viewport,
        effective_limit=6.0,
    )
    assert isinstance(result, VisibleStarStatistics)
    assert result.visible_count == 3
    assert result.brightest_magnitude == pytest.approx(0.2)
    assert result.faintest_magnitude == pytest.approx(5.8)
    assert result.effective_limit == pytest.approx(6.0)


def test_effective_limit_excludes_fainter_stars():
    spherical, projected, viewport = geometries()
    result = visible_star_statistics(
        spherical,
        projected,
        viewport,
        effective_limit=3.5,
    )
    assert result.visible_count == 2
    assert result.faintest_magnitude == pytest.approx(3.1)


def test_optional_footprint_supports_circular_charts():
    spherical, projected, viewport = geometries()
    result = visible_star_statistics(
        spherical,
        projected,
        viewport,
        effective_limit=6.0,
        footprint_contains=lambda x, y: np.hypot(x, y) <= 0.6,
    )
    assert result.visible_count == 2
    assert result.brightest_magnitude == pytest.approx(0.2)
    assert result.faintest_magnitude == pytest.approx(3.1)


def test_mask_is_inclusive_at_viewport_edges():
    spherical = SimpleNamespace(
        metadata={"magnitude": np.asarray([1.0, 2.0])}
    )
    projected = SimpleNamespace(
        x=np.asarray([-1.0, 1.0]),
        y=np.asarray([-1.0, 1.0]),
    )
    viewport = Viewport.centered(width=2.0, height=2.0)
    mask = visible_star_mask(
        spherical,
        projected,
        viewport,
        effective_limit=2.0,
    )
    assert mask.tolist() == [True, True]


def test_no_visible_stars_has_explicit_empty_statistics():
    spherical, projected, viewport = geometries()
    result = visible_star_statistics(
        spherical,
        projected,
        viewport,
        effective_limit=-2.0,
    )
    assert not result.has_visible_stars
    assert result.visible_count == 0
    assert result.brightest_magnitude is None
    assert result.faintest_magnitude is None


def test_mismatched_geometry_shapes_are_rejected():
    spherical, projected, viewport = geometries()
    projected.x = projected.x[:-1]
    with pytest.raises(ValueError):
        visible_star_mask(
            spherical,
            projected,
            viewport,
            effective_limit=6.0,
        )


def test_invalid_footprint_shape_is_rejected():
    spherical, projected, viewport = geometries()
    with pytest.raises(ValueError):
        visible_star_mask(
            spherical,
            projected,
            viewport,
            effective_limit=6.0,
            footprint_contains=lambda x, y: [True],
        )


def test_statistics_module_remains_backend_independent():
    import wenu.charts.magnitude_legend as module

    source = Path(module.__file__).read_text().lower()
    assert "matplotlib" not in source
