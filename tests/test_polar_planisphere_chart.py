"""Single-face polar-planisphere chart geometry."""

from types import SimpleNamespace

import numpy as np
import pytest

from wenu import PolarPlanisphereChart
from wenu.charts.context import BoundaryKind
from wenu.charts.legend_plan import chart_type_name, default_chart_legend_plan
from wenu.geometry.projected import ProjectedPoints
from wenu.geometry.spherical import SphericalCurves, SphericalPoints
from wenu.projections import (
    PolarAzimuthalEquidistantProjection,
    StereographicProjection,
)


def test_default_faces_have_configurable_forty_degree_overlap():
    south = PolarPlanisphereChart()
    north = PolarPlanisphereChart(pole="north")

    assert south.limiting_declination_deg == pytest.approx(20.0)
    assert north.limiting_declination_deg == pytest.approx(-20.0)
    assert south.angular_radius_deg == pytest.approx(110.0)
    assert north.angular_radius_deg == pytest.approx(110.0)
    assert (
        south.limiting_declination_deg
        - north.limiting_declination_deg
    ) == pytest.approx(40.0)


@pytest.mark.parametrize(
    ("projection_name", "kind"),
    (
        (
            "polar_azimuthal_equidistant",
            PolarAzimuthalEquidistantProjection,
        ),
        ("stereographic", StereographicProjection),
    ),
)
@pytest.mark.parametrize("pole", ("south", "north"))
def test_both_poles_support_equidistant_and_stereographic_projection(
    projection_name,
    kind,
    pole,
):
    chart = PolarPlanisphereChart(
        pole=pole,
        projection_name=projection_name,
        position_angle_deg=17.0,
        flip_ew=False,
    )

    assert isinstance(chart.projection, kind)
    assert chart.projection_selection.coordinate_frame == "equatorial"
    projected = chart.projection.project_spherical(
        37.0, chart.limiting_declination_deg
    )
    restored = chart.projection.unproject_spherical(*projected)
    assert restored.lon_deg == pytest.approx(37.0)
    assert restored.lat_deg == pytest.approx(
        chart.limiting_declination_deg
    )


def test_projection_choice_changes_radial_law_not_disk_contract():
    equidistant = PolarPlanisphereChart()
    stereographic = PolarPlanisphereChart(projection_name="stereographic")

    assert equidistant.boundary_radius == pytest.approx(2.0 * 110.0 / 90.0)
    assert stereographic.boundary_radius == pytest.approx(
        2.0 * np.tan(np.radians(55.0))
    )
    for chart in (equidistant, stereographic):
        assert chart.boundary.closed
        assert chart.viewport.aspect_ratio == pytest.approx(1.0)
        assert chart.chart_context.boundary_kind is BoundaryKind.CIRCULAR
        assert chart.chart_context.clip_boundary.closed
        assert chart.figure_size(8.0) == pytest.approx((8.0, 8.0))
        assert chart.physical_diameter_mm == pytest.approx(195.0)


@pytest.mark.parametrize(
    "projection_name", ("polar_azimuthal_equidistant", "stereographic")
)
@pytest.mark.parametrize(
    ("pole", "outside_declination"), (("north", -30.0), ("south", 30.0))
)
def test_face_cap_removes_outside_curve_chords_before_rendering(
    projection_name,
    pole,
    outside_declination,
):
    chart = PolarPlanisphereChart(
        pole=pole,
        projection_name=projection_name,
    )
    curves = SphericalCurves(
        lon_deg=(np.asarray((20.0, 200.0)),),
        lat_deg=(np.asarray((outside_declination, outside_declination)),),
    )

    projected = chart.project_equatorial_geometry(curves)

    assert len(projected) == 0


@pytest.mark.parametrize(
    ("pole", "declinations", "finite"),
    (
        ("north", (-27.0, 27.0), (False, True)),
        ("south", (-27.0, 27.0), (True, False)),
    ),
)
def test_face_cap_suppresses_reference_points_outside_declination_limit(
    pole,
    declinations,
    finite,
):
    chart = PolarPlanisphereChart(pole=pole)
    points = SphericalPoints(
        lon_deg=np.asarray((0.0, 0.0)),
        lat_deg=np.asarray(declinations),
    )

    projected = chart.project_equatorial_geometry(points)

    assert tuple(np.isfinite(projected.x)) == finite
    assert tuple(np.isfinite(projected.y)) == finite


def test_physical_diameter_does_not_change_projection_geometry():
    small = PolarPlanisphereChart(physical_diameter_mm=180.0)
    large = PolarPlanisphereChart(physical_diameter_mm=210.0)

    assert small.boundary_radius == pytest.approx(large.boundary_radius)
    np.testing.assert_allclose(small.boundary.x, large.boundary.x)
    np.testing.assert_allclose(small.boundary.y, large.boundary.y)


def test_render_transforms_canonical_altaz_before_selected_projection(
    monkeypatch,
):
    source = SphericalPoints(lon_deg=[1.0], lat_deg=[2.0])
    equatorial = SphericalPoints(lon_deg=[30.0], lat_deg=[-40.0])
    calls = {}

    def transform(geometry, observer):
        calls["transform"] = (geometry, observer)
        return equatorial

    monkeypatch.setattr(
        "wenu.charts.polar_planisphere.horizontal_to_equatorial",
        transform,
    )

    class Renderer:
        def set_clip_boundary(self, boundary, *, style):
            calls["boundary"] = boundary

    class Sky:
        observer = None

        def draw_chart(self, **kwargs):
            calls["draw"] = kwargs
            return kwargs["project_geometry"](source)

    chart = PolarPlanisphereChart(projection_name="stereographic")
    observer = object()
    result = chart.render(Sky(), Renderer(), observer=observer)

    expected = chart.projection.project_geometry(equatorial)
    np.testing.assert_allclose(result.x, expected.x)
    np.testing.assert_allclose(result.y, expected.y)
    assert calls["transform"] == (source, observer)
    assert calls["draw"]["observer"] is observer
    assert calls["boundary"].name == "declination_20"


def test_constellation_labels_are_suppressed_before_the_date_ring():
    chart = PolarPlanisphereChart()
    radius = chart.boundary_radius
    labels = ProjectedPoints(
        x=np.asarray((0.0, radius * 0.95)),
        y=np.asarray((0.0, 0.0)),
        labels=np.asarray(("SCP", "EDGE"), dtype=object),
    )
    layer = object()
    sky = SimpleNamespace(constellation_labels=layer)
    options = chart._inset_constellation_labels(
        sky,
        {layer: {"prepare": lambda spherical, projected: projected}},
    )

    prepared = options[layer]["prepare"](object(), labels)

    assert np.isfinite(prepared.x[0])
    assert np.isnan(prepared.x[1])
    assert prepared.labels.tolist() == ["SCP", "EDGE"]
    rotation = options[layer]["render"]["label_style"]["rotation"]
    assert rotation(0.0, radius * 0.5) == pytest.approx(0.0)
    assert rotation(0.0, -radius * 0.5) == pytest.approx(-180.0)
    assert rotation(radius * 0.5, 0.0) == pytest.approx(-90.0)
    assert rotation(-radius * 0.5, 0.0) == pytest.approx(90.0)


def test_deep_sky_labels_share_the_radial_polar_orientation():
    chart = PolarPlanisphereChart()
    constellation = object()
    deep_sky_layers = {
        name: object()
        for name in (
            "nonstellar",
            "galaxies",
            "open_clusters",
            "globular_clusters",
            "planetary_nebulae",
        )
    }
    sky = SimpleNamespace(
        constellation_labels=constellation,
        **deep_sky_layers,
    )
    options = {
        layer: {"render": {"draw_labels": True}}
        for layer in (constellation, *deep_sky_layers.values())
    }

    resolved = chart._inset_constellation_labels(sky, options)

    for layer in options:
        label_style = resolved[layer]["render"]["label_style"]
        assert label_style["rotation_mode"] == "anchor"
        assert label_style["rotation"](1.0, 0.0) == pytest.approx(-90.0)


@pytest.mark.parametrize(
    "options, message",
    (
        ({"pole": "east"}, "pole"),
        ({"limiting_declination_deg": 90.0}, "limiting_declination"),
        ({"projection_name": "mollweide"}, "projection_name"),
        ({"projection_radius": 0.0}, "projection_radius"),
        ({"physical_diameter_mm": 0.0}, "physical_diameter_mm"),
        ({"boundary_samples": 8}, "boundary_samples"),
    ),
)
def test_invalid_face_geometry_is_rejected(options, message):
    with pytest.raises(ValueError, match=message):
        PolarPlanisphereChart(**options)


def test_chart_has_public_identity_and_interim_legend_defaults():
    chart = PolarPlanisphereChart()

    assert chart_type_name(chart) == "polar_planisphere"
    assert default_chart_legend_plan(chart.chart_type).chart_type == (
        "polar_planisphere"
    )
    import wenu

    assert wenu.PolarPlanisphereChart is PolarPlanisphereChart
    assert "PolarPlanisphereChart" in wenu.__all__


def test_polar_legend_fallback_does_not_copy_existing_family_authority():
    from wenu.configuration import (
        packaged_furniture_product_export_defaults,
    )

    defaults = packaged_furniture_product_export_defaults()

    assert default_chart_legend_plan("regional") is (
        defaults.furniture_by_family["regional"].legends.plan
    )
    assert default_chart_legend_plan("polar_planisphere") is not (
        defaults.furniture_by_family["circumpolar"].legends.plan
    )
