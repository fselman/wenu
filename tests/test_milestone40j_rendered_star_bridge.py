from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import wenu.charts.legend_composition as composition
from wenu import (
    RenderedStarGeometry,
    RenderedStarsNotFoundError,
    default_chart_legend_plan,
    draw_rendered_chart_legends,
    rendered_star_geometry,
)


class Stars:
    pass


class OtherLayer:
    pass


def geometries():
    spherical = SimpleNamespace(
        metadata={"magnitude": np.asarray([-1.0, 1.0, 3.0])}
    )
    projected = SimpleNamespace(
        x=np.asarray([0.0, 0.2, 0.4]),
        y=np.asarray([0.0, 0.2, 0.4]),
    )
    return spherical, projected


def rendering_result(star_layer=None):
    star_layer = Stars() if star_layer is None else star_layer
    spherical, projected = geometries()
    viewport = SimpleNamespace(
        x_min=-1.0,
        x_max=1.0,
        y_min=-1.0,
        y_max=1.0,
    )
    return SimpleNamespace(
        viewport=viewport,
        layers=(
            SimpleNamespace(
                layer=OtherLayer(),
                spherical=object(),
                projected=object(),
            ),
            SimpleNamespace(
                layer=star_layer,
                spherical=spherical,
                projected=projected,
            ),
        ),
    ), star_layer


def test_explicit_layer_identity_extracts_rendered_geometry():
    result, layer = rendering_result()
    resolved = rendered_star_geometry(result, star_layer=layer)
    assert isinstance(resolved, RenderedStarGeometry)
    assert resolved.layer is layer
    assert resolved.spherical is result.layers[1].spherical
    assert resolved.projected is result.layers[1].projected
    assert resolved.viewport is result.viewport


def test_sky_stars_identity_is_preferred():
    result, layer = rendering_result()
    sky = SimpleNamespace(stars=layer)
    resolved = rendered_star_geometry(result, sky=sky)
    assert resolved.layer is layer


def test_class_name_fallback_supports_stored_results():
    result, layer = rendering_result()
    resolved = rendered_star_geometry(result)
    assert resolved.layer is layer


def test_missing_stars_raise_clear_error():
    result, _ = rendering_result()
    result = SimpleNamespace(
        viewport=result.viewport,
        layers=result.layers[:1],
    )
    with pytest.raises(
        RenderedStarsNotFoundError,
        match="no matching Stars",
    ):
        rendered_star_geometry(result)


def test_magnitude_metadata_is_required():
    result, layer = rendering_result()
    bad = SimpleNamespace(
        viewport=result.viewport,
        layers=(
            SimpleNamespace(
                layer=layer,
                spherical=SimpleNamespace(metadata={}),
                projected=result.layers[1].projected,
            ),
        ),
    )
    with pytest.raises(ValueError, match="magnitude"):
        rendered_star_geometry(bad, star_layer=layer)


def test_rendered_coordinator_reuses_geometry(monkeypatch):
    monkeypatch.setattr(
        composition,
        "draw_chart_legend",
        lambda ax, *args, **kwargs: ax.legend([], []),
    )
    result, layer = rendering_result()
    sky = SimpleNamespace(stars=layer)
    figure, ax = plt.subplots()
    legends = draw_rendered_chart_legends(
        ax,
        object(),
        sky,
        object(),
        default_chart_legend_plan("regional"),
        result,
        effective_limit=3.0,
    )
    assert legends.stars.statistics.visible_count == 3
    assert len(legends.artists) == 2
    plt.close(figure)


def test_disabled_stars_do_not_require_a_rendered_star_layer(monkeypatch):
    monkeypatch.setattr(
        composition,
        "draw_chart_legend",
        lambda ax, *args, **kwargs: ax.legend([], []),
    )
    result, _ = rendering_result()
    result = SimpleNamespace(
        viewport=result.viewport,
        layers=result.layers[:1],
    )
    plan = default_chart_legend_plan("regional").with_stars(
        enabled=False
    )
    figure, ax = plt.subplots()
    legends = draw_rendered_chart_legends(
        ax,
        object(),
        SimpleNamespace(stars=None),
        object(),
        plan,
        result,
        effective_limit=3.0,
    )
    assert legends.objects is not None
    assert legends.stars is None
    plt.close(figure)


def test_public_api_exports_rendered_bridge():
    from wenu import draw_rendered_chart_legends as exported

    assert exported is draw_rendered_chart_legends
