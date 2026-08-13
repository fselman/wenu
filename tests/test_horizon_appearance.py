"""Semantic horizon-reference and mask appearance contracts."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from wenu import ChartStyle, PublicationStyle
from wenu.charts.atlas_modes import atlas_chart_style
from wenu.charts.binocular import BinocularChart
from wenu.charts.cartoon_modes import cartoon_chart_style
from wenu.charts.style_components import GridStyle, MaskStyle
from wenu.charts.styles import resolved_outside_mask_style
from wenu.charts.regional import RegionalChart
from wenu.sky.horizon import HorizonReference


def test_publication_style_configures_semantic_horizon_explicitly():
    horizon = HorizonReference()
    sky = SimpleNamespace(
        horizon_reference=horizon,
        layers=(horizon,),
        stars=None,
        nonstellar=None,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=None,
        points=None,
    )
    style = PublicationStyle(
        horizon_color="purple",
        horizon_linewidth=1.25,
        horizon_linestyle=":",
        horizon_alpha=0.6,
        horizon_zorder=8.0,
    )

    assert style.layer_options(sky)[horizon]["render"]["style"] == {
        "color": "purple",
        "linewidth": 1.25,
        "linestyle": ":",
        "alpha": 0.6,
        "zorder": 8.0,
    }


def test_composed_style_preserves_horizon_and_mask_appearance():
    style = ChartStyle(
        grids=GridStyle(
            horizon_color="purple",
            horizon_linewidth=1.25,
            horizon_linestyle=":",
            horizon_alpha=0.6,
            horizon_zorder=8.0,
        ),
        mask=MaskStyle(color="navy", alpha=0.2, zorder=12.0),
    )
    publication = style.as_publication_style()

    assert publication.horizon_reference_style() == {
        "color": "purple",
        "linewidth": 1.25,
        "linestyle": ":",
        "alpha": 0.6,
        "zorder": 8.0,
    }
    assert resolved_outside_mask_style(style) == {
        "facecolor": "navy",
        "edgecolor": "none",
        "alpha": 0.2,
        "zorder": 12.0,
    }


@pytest.mark.parametrize(
    "style",
    (
        atlas_chart_style("print"),
        atlas_chart_style("presentation"),
        cartoon_chart_style("print"),
        cartoon_chart_style("presentation"),
    ),
)
def test_output_styles_resolve_semantic_horizon_appearance(style):
    options = style.as_publication_style().horizon_reference_style()

    assert options["color"] == style.grids.horizon_color
    assert options["linewidth"] == pytest.approx(
        style.grids.horizon_linewidth
    )
    assert options["linestyle"] == style.grids.horizon_linestyle
    assert options["alpha"] == pytest.approx(style.grids.horizon_alpha)
    assert options["zorder"] == pytest.approx(style.grids.horizon_zorder)


def test_horizon_alpha_is_validated():
    with pytest.raises(ValueError, match="horizon_alpha"):
        PublicationStyle(horizon_alpha=1.1).horizon_reference_style()


def test_binocular_mask_uses_resolved_composed_style(monkeypatch):
    calls = {}
    style = replace(
        ChartStyle(),
        mask=MaskStyle(color="navy", alpha=0.2, zorder=12.0),
    )

    class Renderer:
        def set_clip_boundary(self, boundary, *, style):
            pass

        def set_axes_frame_visible(self, visible):
            pass

    chart = BinocularChart(center_alt_deg=30.0, center_az_deg=120.0)
    monkeypatch.setattr(
        RegionalChart,
        "render",
        lambda self, *args, **kwargs: calls.update(kwargs) or "result",
    )
    sky = SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_cloud_isophotes={},
        galaxies=None,
        open_clusters=None,
        planetary_nebulae=None,
        supernova_remnants=None,
        globular_clusters=None,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=None,
        points=None,
        horizon_reference=None,
        layers=(),
    )

    assert chart.render(
        sky,
        Renderer(),
        observer=object(),
        style=style,
        horizon_mask=True,
    ) == "result"
    assert calls["mask_style"] == resolved_outside_mask_style(style)
    assert calls["horizon_mask"] is True
