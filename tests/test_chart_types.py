import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu import (
    BinocularChart,
    BoundaryKind,
    CircumpolarChart,
    CircularGridLabelAnchor,
    CircularLabelAnchor,
    EllipticalGridLabelAnchor,
    MatplotlibRenderer,
    ProjectedCurve,
    RegionalChart,
)
from wenu.charts.boundaries import (
    RectangularLabelAnchor,
    apply_coordinate_label_anchor,
    circular_boundary,
)
from wenu.geometry.projected import (
    ProjectedCurves,
    ProjectedGrid,
)
from wenu.rendering.label_placement import CurveLabelPlacement


def test_circular_boundary_is_closed_and_finite():
    boundary = circular_boundary(2.5, samples=37)
    assert boundary.closed
    assert len(boundary.x) == 37
    assert np.all(boundary.finite)
    assert boundary.x[0] == pytest.approx(boundary.x[-1])
    assert boundary.y[0] == pytest.approx(boundary.y[-1])


def test_circular_anchor_uses_boundary_not_axes_shape():
    boundary = circular_boundary(2.0, samples=73)
    curve = ProjectedCurve(
        x=[0.0, 0.0, 0.0],
        y=[0.0, 1.0, 2.0],
        name="right_ascension_0",
    )
    anchor = CircularLabelAnchor(boundary, inset=0.5)
    assert anchor(curve, ax=None) == pytest.approx((0.0, 1.0))


def test_circular_grid_anchor_preserves_polar_label_conventions():
    boundary = circular_boundary(2.0, samples=73)
    ra = ProjectedCurve(
        x=[0.0, 0.0, 0.0],
        y=[0.0, 1.0, 2.0],
        name="right_ascension_0",
    )
    dec = ProjectedCurve(
        x=[1.0, -1.9, 0.0],
        y=[0.0, 0.5, 1.0],
        name="declination_-75",
    )
    anchor = CircularGridLabelAnchor(
        boundary,
        inset=0.965,
        declination_at_left=True,
    )

    assert anchor(ra) == pytest.approx((0.0, 1.93))
    placement = anchor(dec)
    assert isinstance(placement, CurveLabelPlacement)
    assert (placement.x, placement.y) == pytest.approx((-1.8335, 0.4825))
    assert placement.normal_offset_em == pytest.approx(0.65)


def test_rectangular_anchor_places_ra_at_bottom_and_dec_at_left():
    class Axes:
        def get_xlim(self):
            return (-2.0, 2.0)

        def get_ylim(self):
            return (-1.0, 1.0)

    ra = ProjectedCurve(
        x=[-1.0, 0.0, 1.0],
        y=[1.0, -1.0, 0.0],
        name="right_ascension_0",
    )
    dec = ProjectedCurve(
        x=[2.0, -2.0, 0.0],
        y=[-0.5, 0.0, 0.5],
        name="declination_0",
    )
    anchor = RectangularLabelAnchor(inset=0.0)
    ra_placement = anchor(ra, Axes())
    assert isinstance(ra_placement, CurveLabelPlacement)
    assert (ra_placement.x, ra_placement.y) == pytest.approx((0.0, -1.0))
    assert ra_placement.horizontal_alignment == "center"
    assert ra_placement.vertical_alignment == "bottom"
    placement = anchor(dec, Axes())
    assert isinstance(placement, CurveLabelPlacement)
    assert (placement.x, placement.y) == pytest.approx((-2.0, 0.0))
    assert placement.horizontal_alignment == "left"


def test_rectangular_anchor_keeps_negative_declination_label_inside_axes():
    declination = ProjectedCurve(
        x=[-2.0, 0.0, 2.0],
        y=[0.0, 0.0, 0.0],
        name="declination_-15",
    )
    grid = ProjectedGrid(
        {"declination": ProjectedCurves([declination])}
    )
    figure, ax = plt.subplots(figsize=(7.0, 7.0), dpi=160)
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(-1.0, 1.0)
    try:
        artists = MatplotlibRenderer(ax).draw(
            grid,
            draw_labels=True,
            label_style={"fontsize": 18.0},
            label_formatter=lambda name: "-15:00",
            label_anchor=RectangularLabelAnchor(),
        )
        figure.canvas.draw()
        text = next(
            artist
            for artist in artists
            if callable(getattr(artist, "get_text", None))
            and artist.get_text() == "-15:00"
        )
        renderer = figure.canvas.get_renderer()
        axes_bounds = ax.get_window_extent(renderer=renderer)
        label_bounds = text.get_window_extent(renderer=renderer)

        assert label_bounds.x0 >= axes_bounds.x0
        assert text.get_horizontalalignment() == "left"
    finally:
        plt.close(figure)


def test_rectangular_anchor_ignores_off_page_declination_samples():
    curve = ProjectedCurve(
        x=[-8.0, -6.0, -1.5, 0.0, 1.5, 6.0],
        y=[3.0, 2.0, -0.8, -0.9, -0.8, 2.0],
        name="declination_-30",
    )

    class Axes:
        @staticmethod
        def get_xlim():
            return -2.0, 2.0

        @staticmethod
        def get_ylim():
            return -1.0, 1.0

    placement = RectangularLabelAnchor()(curve, Axes())

    assert isinstance(placement, CurveLabelPlacement)
    assert (placement.x, placement.y) == pytest.approx((-1.5, -0.8))


def test_regional_chart_applies_rectangular_coordinate_label_anchor():
    layer = object()
    captured = {}

    class Style:
        def layer_options(self, sky):
            return {
                layer: {
                    "render": {
                        "label_formatter": str,
                    }
                }
            }

    class Sky:
        def draw_chart(self, **kwargs):
            captured.update(kwargs)
            return "rendered"

    chart = RegionalChart(45.0, 180.0, 30.0, 20.0)

    assert chart.render(Sky(), object(), style=Style()) == "rendered"
    anchor = captured["layer_options"][layer]["render"][
        "label_anchor"
    ]
    assert isinstance(anchor, RectangularLabelAnchor)
    assert anchor.inset == pytest.approx(0.01)


def test_elliptical_anchor_uses_one_meridian_for_latitudes_and_key_longitudes():
    boundary = ProjectedCurve(
        x=[-2.0, 0.0, 2.0, 0.0, -2.0],
        y=[0.0, 1.0, 0.0, -1.0, 0.0],
        closed=True,
        name="boundary",
    )
    latitude = ProjectedCurve(
        x=[-1.5, 0.0, 1.5],
        y=[0.5, 0.6, 0.5],
        name="galactic_latitude_30",
    )
    secondary_longitude = ProjectedCurve(
        x=[0.2, 0.2, 0.2],
        y=[-0.8, 0.0, 0.8],
        name="galactic_longitude_45",
    )
    principal_longitude = ProjectedCurve(
        x=[1.0, 1.0, 1.0],
        y=[-0.8, 0.0, 0.8],
        name="galactic_longitude_270",
    )
    anchor = EllipticalGridLabelAnchor(boundary)

    placement = anchor(latitude)
    assert isinstance(placement, CurveLabelPlacement)
    assert placement.x < 0.0
    assert placement.y == pytest.approx(0.579)
    assert anchor(secondary_longitude) is None
    placement = anchor(principal_longitude)
    assert isinstance(placement, CurveLabelPlacement)
    assert placement.x == pytest.approx(1.024)
    assert placement.y == pytest.approx(-0.035)
    assert placement.horizontal_alignment == "left"
    assert placement.vertical_alignment == "top"


def test_elliptical_anchor_places_180_label_inside_left_seam():
    boundary = ProjectedCurve(
        x=[-2.0, 0.0, 2.0, 0.0, -2.0],
        y=[0.0, 1.0, 0.0, -1.0, 0.0],
        closed=True,
        name="boundary",
    )
    seam = ProjectedCurve(
        x=[-2.0, -2.0, 2.0, 2.0],
        y=[-0.8, 0.0, 0.0, 0.8],
        name="galactic_longitude_180",
    )

    placement = EllipticalGridLabelAnchor(boundary)(seam)

    assert placement.x == pytest.approx(-1.976)
    assert placement.y == pytest.approx(-0.035)


@pytest.mark.parametrize(
    ("name", "x"),
    (
        ("galactic_longitude_90", 0.0),
        ("galactic_longitude_180", 2.0),
    ),
)
def test_elliptical_anchor_rejects_false_split_longitude_segments(name, x):
    boundary = ProjectedCurve(
        x=[-2.0, 0.0, 2.0, 0.0, -2.0],
        y=[0.0, 1.0, 0.0, -1.0, 0.0],
        closed=True,
        name="boundary",
    )
    duplicate = ProjectedCurve(
        x=[x, x, x],
        y=[-0.8, 0.0, 0.8],
        name=name,
    )

    assert EllipticalGridLabelAnchor(boundary)(duplicate) is None


def test_grid_anchor_application_does_not_mutate_input():
    layer = object()
    original_anchor = object()
    options = {
        layer: {
            "render": {
                "label_formatter": str,
                "label_anchor": original_anchor,
            }
        }
    }
    replacement = object()
    resolved = apply_coordinate_label_anchor(options, replacement)
    assert resolved[layer]["render"]["label_anchor"] is replacement
    assert options[layer]["render"]["label_anchor"] is original_anchor


def test_binocular_chart_has_circular_context_and_square_viewport():
    chart = BinocularChart(
        center_alt_deg=45.0,
        center_az_deg=120.0,
        field_diameter_deg=6.5,
    )
    assert chart.chart_context.boundary_kind is BoundaryKind.CIRCULAR
    assert chart.chart_context.clip_boundary.closed
    assert chart.viewport.aspect_ratio == pytest.approx(1.0)
    assert chart.figure_size(8.0) == pytest.approx((8.0, 8.0))
    assert chart.regional_chart.field_width_deg == pytest.approx(6.5)


def test_binocular_validation():
    with pytest.raises(ValueError, match="field_diameter_deg"):
        BinocularChart(0.0, 0.0, field_diameter_deg=0.0)


def test_circumpolar_radius_and_validation():
    chart = CircumpolarChart(
        observer=object(),
        limiting_declination_deg=-40.0,
        pole="south",
    )
    assert chart.pole_declination_deg == -90.0
    assert chart.angular_radius_deg == pytest.approx(50.0)
    with pytest.raises(ValueError, match="negative"):
        CircumpolarChart(
            observer=object(),
            limiting_declination_deg=40.0,
            pole="south",
        )


def test_circumpolar_forwards_horizon_mask_to_circular_chart(monkeypatch):
    calls = {}

    class CircularChart:
        def render(self, *args, **kwargs):
            calls.update(kwargs)
            return "result"

    monkeypatch.setattr(
        CircumpolarChart,
        "binocular_chart",
        property(lambda self: CircularChart()),
    )
    chart = CircumpolarChart(
        observer=object(),
        limiting_declination_deg=-40.0,
        pole="south",
    )

    assert chart.render(
        object(),
        object(),
        horizon_mask=True,
        boundary_style={},
        coordinate_label_anchor=object(),
    ) == "result"
    assert calls["horizon_mask"] is True


def test_chart_type_modules_do_not_import_render_backend():
    from pathlib import Path
    import wenu.charts.binocular as binocular_module

    directory = Path(binocular_module.__file__).parent
    for filename in (
        "boundaries.py",
        "binocular.py",
        "circumpolar.py",
        "polar_planisphere.py",
        "polar_planisphere_pair.py",
        "polar_calendar.py",
        "polar_calendar_furniture.py",
        "polar_planisphere_style.py",
    ):
        source = (directory / filename).read_text().lower()
        assert "matplotlib" not in source
