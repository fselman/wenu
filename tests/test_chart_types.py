import numpy as np
import pytest

from wenu import (
    BinocularChart,
    BoundaryKind,
    CircumpolarChart,
    CircularGridLabelAnchor,
    CircularLabelAnchor,
    ProjectedCurve,
)
from wenu.charts.boundaries import (
    RectangularLabelAnchor,
    apply_coordinate_label_anchor,
    circular_boundary,
)


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
    assert anchor(dec) == pytest.approx((-1.8335, 0.4825))


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
    assert anchor(ra, Axes()) == pytest.approx((0.0, -1.0))
    assert anchor(dec, Axes()) == pytest.approx((-2.0, 0.0))


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
    ):
        source = (directory / filename).read_text().lower()
        assert "matplotlib" not in source
