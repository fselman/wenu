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
