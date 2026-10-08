"""Scope coordinate-boundary label anchoring to coordinate grids."""
from wenu.charts.boundaries import apply_coordinate_label_anchor


def test_supported_chart_owners_enable_band_and_preserve_track_anchor():
    import matplotlib.pyplot as plt
    from wenu.charts.full_sky import FullSkyChart
    from wenu.charts.regional import RegionalChart
    from wenu.charts.binocular import BinocularChart
    from wenu.charts.styles import PublicationStyle
    from wenu.rendering.matplotlib import MatplotlibRenderer
    from wenu.charts.boundaries import ExteriorGridLabelAnchor

    class Style(PublicationStyle):
        def layer_options(self, sky, **kwargs):
            return {}

    class Sky:
        def draw_chart(self, **kwargs):
            self.options = kwargs["layer_options"]
            return "result"

    charts = [FullSkyChart(), RegionalChart(center_alt_deg=45, center_az_deg=180,
                                          field_width_deg=30, field_height_deg=20),
              BinocularChart(center_alt_deg=45, center_az_deg=180)]
    for enabled in (True, False):
        for chart in charts:
            fig, ax = plt.subplots()
            renderer, sky = MatplotlibRenderer(ax), Sky()
            fixed = object()
            assert chart.render(sky, renderer, style=Style(grid_label_band=enabled), layer_options={
                "equatorial_grid": {"render": {"label_anchor": object()}},
                "solar_system_track": {"render": {"label_anchor": fixed}},
            }) == "result"
            assert (renderer._grid_label_band is not None) == enabled
            assert sky.options["solar_system_track"]["render"]["label_anchor"] is fixed
            if not isinstance(chart, FullSkyChart):
                assert isinstance(sky.options["equatorial_grid"]["render"]["label_anchor"], ExteriorGridLabelAnchor) == enabled
            plt.close(fig)


def test_exterior_anchor_uses_real_crossings_and_skips_non_crossing_curves():
    import matplotlib.pyplot as plt
    import numpy as np
    from wenu.charts.boundaries import ExteriorGridLabelAnchor, circular_boundary
    from wenu.geometry.projected import ProjectedCurve

    fig, ax = plt.subplots()
    boundary = circular_boundary(1)
    delegate = lambda curve, ax: (0.0, .95)
    anchor = ExteriorGridLabelAnchor(delegate, boundary, circular=True)
    crossing = anchor(ProjectedCurve([0, 0], [-2, 2]), ax)
    np.testing.assert_allclose((crossing.x, crossing.y), (0, 1))
    assert crossing.exterior_direction == (0, 1)
    assert crossing.rotation_deg == 0
    assert anchor(ProjectedCurve([0, 0], [-.5, .5]), ax) is None
    rectangle = ProjectedCurve([-1, 1, 1, -1], [-1, -1, 1, 1], closed=True)
    crossing = ExteriorGridLabelAnchor(delegate, rectangle)(ProjectedCurve([0, 0], [-2, 2]), ax)
    np.testing.assert_allclose((crossing.x, crossing.y), (0, 1))
    assert crossing.exterior_direction == (0, 1)
    plt.close(fig)

def test_coordinate_anchor_replaces_grid_anchor_only():
    old_grid_anchor = object()
    track_anchor = object()
    boundary_anchor = object()
    class Layer:
        pass
    grid = Layer()
    grid.layer_name = "coordinates_grid"
    grid.coordinate_system = "equatorial"
    track = Layer()
    track.layer_name = "solar_system_track"
    track.coordinate_system = None
    options = {
        "equatorial_grid": {
            "render": {"label_anchor": old_grid_anchor}
        },
        "solar_system_track": {
            "render": {"label_anchor": track_anchor}
        },
        grid: {"render": {"label_anchor": old_grid_anchor}},
        track: {"render": {"label_anchor": track_anchor}},
    }
    resolved = apply_coordinate_label_anchor(options, boundary_anchor)
    assert resolved["equatorial_grid"]["render"]["label_anchor"] is boundary_anchor
    assert resolved[grid]["render"]["label_anchor"] is boundary_anchor
    assert resolved["solar_system_track"]["render"]["label_anchor"] is track_anchor
    assert resolved[track]["render"]["label_anchor"] is track_anchor
    horizon_anchor = object()
    options["altaz_grid"] = {"render": {"label_anchor": old_grid_anchor}}
    resolved = apply_coordinate_label_anchor(options, boundary_anchor, altaz_anchor=horizon_anchor)
    assert resolved["altaz_grid"]["render"]["label_anchor"] is horizon_anchor
    assert resolved[grid]["render"]["label_anchor"] is boundary_anchor
    assert resolved[track]["render"]["label_anchor"] is track_anchor
