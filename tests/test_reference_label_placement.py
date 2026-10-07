"""Current reference label placement contracts."""

# Contracts consolidated from test_milestone45e_reference_label_tangents.py.
"""Milestone 45E tangent-aligned celestial-reference labels."""

from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import (
    AltAz,
    BarycentricMeanEcliptic,
    EarthLocation,
    Galactic,
    ICRS,
)
from astropy.time import Time

from wenu import (
    BinocularChart,
    ChartFurnitureOptions,
    CircumpolarChart,
    DetailOverrides,
    FullSkyChart,
    PoleAnnotations,
    PolarPlanisphereChart,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
    RegionalChart,
    build_celestial_reference_sky,
    compose_chart,
)
from wenu.charts.reference_furniture import (
    _reference_layer_options,
    polar_declination_tick_geometry,
)
from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPoints,
)
from wenu.rendering import (
    CurveLabelPlacement,
    MatplotlibRenderer,
    tangent_label_placement,
)


def test_generic_tangent_placement_normalizes_readable_angles():
    rising = ProjectedCurve(
        np.asarray([-1.0, 0.0, 1.0]),
        np.asarray([-1.0, 0.0, 1.0]),
    )
    falling_backwards = ProjectedCurve(
        np.asarray([1.0, 0.0, -1.0]),
        np.asarray([-1.0, 0.0, 1.0]),
    )

    assert tangent_label_placement(rising, (0.0, 0.0)).rotation_deg == 45.0
    assert tangent_label_placement(
        falling_backwards, (0.0, 0.0)
    ).rotation_deg == -45.0


def test_tangent_does_not_bridge_disconnected_segments():
    curve = ProjectedCurve(
        np.asarray([-2.0, -1.0, np.nan, 1.0, 2.0]),
        np.asarray([0.0, 0.0, np.nan, 1.0, 2.0]),
    )

    placement = tangent_label_placement(curve, (-1.0, 0.0))

    assert placement.rotation_deg == 0.0


@pytest.mark.parametrize(
    ("position", "expected"),
    (
        ((0.0, 1.0), 0.0),
        ((0.0, -1.0), -180.0),
        ((1.0, 0.0), -90.0),
        ((-1.0, 0.0), 90.0),
    ),
)
def test_polar_tangent_orientation_points_typographic_down_to_pole(
    position,
    expected,
):
    x, y = position
    tangent = np.asarray((-1.0, 0.0, 1.0))
    curve = ProjectedCurve(
        x + tangent * (-y),
        y + tangent * x,
    )

    placement = tangent_label_placement(
        curve,
        position,
        down_toward=(0.0, 0.0),
    )

    assert placement.rotation_deg == pytest.approx(expected)


def test_automatic_reference_anchors_prefer_safe_outer_regions():
    from wenu.charts.context import BoundaryKind
    from wenu.charts.reference_furniture import BoundaryAwareReferenceAnchor
    from wenu.geometry.viewport import Viewport

    rectangular = SimpleNamespace(
        viewport=Viewport(-1.0, 1.0, -1.0, 1.0),
        boundary_kind=BoundaryKind.RECTANGULAR,
        clip_boundary=None,
    )
    curve = ProjectedCurve(
        np.linspace(-0.8, 0.8, 17),
        np.zeros(17),
    )
    x, y = BoundaryAwareReferenceAnchor(rectangular)(curve)

    assert abs(x) >= 0.59
    assert y == 0.0


def test_repeated_and_isolated_samples_have_stable_fallbacks():
    repeated = ProjectedCurve(
        np.asarray([0.0, 0.0, 1.0]),
        np.asarray([0.0, 0.0, 0.0]),
    )
    isolated = ProjectedCurve(
        np.asarray([np.nan, 0.0, np.nan]),
        np.asarray([np.nan, 0.0, np.nan]),
    )

    assert tangent_label_placement(
        repeated, (0.0, 0.0)
    ).rotation_deg == 0.0
    assert tangent_label_placement(
        isolated, (0.0, 0.0)
    ).rotation_deg is None


def test_renderer_applies_generic_placement_without_reference_semantics():
    curve = ProjectedCurve(
        np.asarray([-1.0, 0.0, 1.0]),
        np.asarray([-1.0, 0.0, 1.0]),
        name="generic",
    )
    grid = ProjectedGrid(
        {"curves": ProjectedCurves([curve])}
    )
    figure, ax = plt.subplots()
    try:
        artists = MatplotlibRenderer(ax).draw(
            grid,
            draw_labels=True,
            label_style={"fontsize": 10.0},
            label_anchor=lambda curve, ax: CurveLabelPlacement(
                0.0,
                0.0,
                45.0,
                0.75,
                horizontal_alignment="left",
                vertical_alignment="bottom",
            ),
        )
        text = next(
            artist
            for artist in artists
            if callable(getattr(artist, "get_text", None))
            and artist.get_text()
        )
        assert text.get_text() == "generic"
        assert text.get_rotation() == pytest.approx(45.0)
        assert text.get_rotation_mode() == "anchor"
        assert text.get_horizontalalignment() == "left"
        assert text.get_verticalalignment() == "bottom"
        displacement = (
            text.get_transform().transform((0.0, 0.0))
            - ax.transData.transform((0.0, 0.0))
        )
        assert np.hypot(*displacement) == pytest.approx(
            0.75 * 10.0 * figure.dpi / 72.0
        )
    finally:
        plt.close(figure)


def test_renderer_resolves_callable_point_label_rotation():
    points = ProjectedPoints(
        x=np.asarray((0.0,)),
        y=np.asarray((-1.0,)),
        labels=np.asarray(("label",), dtype=object),
    )
    figure, ax = plt.subplots()
    try:
        artists = MatplotlibRenderer(ax).draw(
            points,
            style={"s": 0.0},
            draw_labels=True,
            label_style={
                "rotation": lambda x, y: -180.0,
                "rotation_mode": "anchor",
            },
        )
        text = next(
            artist
            for artist in artists
            if callable(getattr(artist, "get_text", None))
        )
        assert text.get_rotation() == pytest.approx(180.0)
        assert text.get_rotation_mode() == "anchor"
    finally:
        plt.close(figure)


@pytest.mark.parametrize("dpi", [100, 300])
@pytest.mark.parametrize("polar", [False, True])
def test_joint_labels_separate_companions_area_and_curve_while_tracks_stay_fixed(dpi, polar):
    from wenu.charts.boundaries import circular_boundary
    from wenu.geometry.projected import ProjectedPolygon
    from wenu.rendering.label_placement import rotation_with_down_toward

    fig, ax = plt.subplots(figsize=(7, 7), dpi=dpi)
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_aspect("equal")
    renderer = MatplotlibRenderer(ax)
    renderer.set_clip_boundary(circular_boundary(2), style={"facecolor": "none", "edgecolor": "black"})
    def rotation(x, y):
        return rotation_with_down_toward(np.degrees(np.arctan2(y, x)) + 90, (x, y), (0, 0))
    orientation = rotation if polar else 0.0
    renderer.draw(ProjectedPoints([0, .5, .5001], [.8, .6, .6001], labels=["Deneb", "Albireo", "β² Cyg"]),
                  style={"s": [100, 16, 4], "color": "black"}, draw_labels=True,
                  label_style={"fontsize": 5.25, "color": "black", "placement": "auto", "rotation": orientation})
    region = ProjectedPolygon([-0.4, .4, .4, -.4], [.4, .4, 1.4, 1.4])
    renderer.draw(ProjectedPoints([0], [.8], labels=["Cyg"], metadata={"label_regions": ((region,),)}),
                  draw_markers=False, draw_labels=True,
                  label_style={"fontsize": 6.375, "color": "gray", "ha": "center", "va": "center", "placement": "region", "rotation": orientation})
    curve = ProjectedCurve(np.linspace(-1.5, 1.5, 101), .12 * np.linspace(-1.5, 1.5, 101)**2 - .8, name="plane")
    class Anchor:
        def __call__(self, curve, ax=None):
            return tangent_label_placement(curve, (0, -.8), normal_offset_em=.75)
        def candidates(self, curve, ax=None):
            return [tangent_label_placement(curve, (x, y), normal_offset_em=.75)
                    for x, y in zip(curve.x[::5], curve.y[::5])]
    renderer.draw(ProjectedGrid({"curve": ProjectedCurves([curve])}), draw_labels=True,
                  label_anchor=Anchor(), label_style={"fontsize": 6, "color": "blue"},
                  label_formatter=lambda name: "Plano galáctico")
    renderer.draw(ProjectedPoints([0, .06, -.06], [-.74, -.73, -.75]), style={"s": 36, "color": "black"})
    date = ax.text(-1.0, 1.2, "15 oct", rotation=37)
    date_before = date.get_position(), date.get_rotation()
    renderer.finalize_graphics()
    backend = fig.canvas.get_renderer()
    boxes = [text.get_window_extent(backend) for text in ax.texts]
    assert all(not a.overlaps(b) for i, a in enumerate(boxes) for b in boxes[i + 1:])
    assert renderer.unresolved_label_collisions == ()
    assert (date.get_position(), date.get_rotation()) == date_before
    area = next(text for text in ax.texts if text.get_text() == "Cyg")
    box = area.get_window_extent(backend)
    centre = ax.transData.inverted().transform(((box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2))
    assert -.4 < centre[0] < .4 and .4 < centre[1] < 1.4
    for text in ax.texts[:4]:
        assert text.get_rotation() == pytest.approx(rotation(*text.get_position()) % 360 if polar else 0)
    plane = next(text for text in ax.texts if text.get_text() == "Plano galáctico")
    x, y = plane.get_position()
    assert y == pytest.approx(.12 * x**2 - .8)
    expected = tangent_label_placement(curve, (x, y), normal_offset_em=.75)
    assert plane.get_rotation() == pytest.approx(expected.rotation_deg % 360)
    assert plane.get_color() == "blue" and plane.get_fontsize() == 6
    before = [(text.get_position(), text.get_rotation()) for text in ax.texts]
    renderer.finalize_graphics()
    for text, (position, angle) in zip(ax.texts, before):
        np.testing.assert_allclose(text.get_position(), position, atol=1e-12)
        assert text.get_rotation() == pytest.approx(angle)
    plt.close(fig)


@pytest.mark.parametrize("polar", [False, True])
@pytest.mark.parametrize("policy", ["chart", "upright", "up-away-from-cp"])
def test_object_orientation_scope_and_deferred_render_isolation(polar, policy):
    from wenu.charts.label_placement import apply_object_label_orientation

    stars, constellations, body, track, grid = (object() for _ in range(5))
    sky = SimpleNamespace(stars=stars, constellation_labels=constellations,
                          solar_system_bodies={"planet": body})
    style = SimpleNamespace(labels_orientation=policy)
    render = {"label_style": {"fontsize": 7.0, "color": "red"}}
    source = {stars: {"render": lambda spherical, projected: render},
              constellations: {"render": render}, body: {"render": render},
              track: {"render": render}, grid: {"render": render}}
    if not polar and policy == "up-away-from-cp":
        with pytest.raises(ValueError, match="require a polar-planisphere"):
            apply_object_label_orientation(source, sky=sky, style=style)
        return
    resolved = apply_object_label_orientation(source, sky=sky, style=style, polar=polar)
    assert resolved[track] is source[track]
    assert resolved[grid] is source[grid]
    assert "rotation" not in render["label_style"]
    for layer in (stars, constellations, body):
        configured = resolved[layer]["render"]
        configured = configured(None, None) if callable(configured) else configured
        labels = configured["label_style"]
        assert labels["fontsize"] == 7.0
        assert labels["color"] == "red"
        if polar and policy != "upright":
            assert labels["rotation"](0.0, -1.0) == pytest.approx(-180.0)
        else:
            assert labels["rotation"] == 0.0


@pytest.mark.parametrize(("chart", "polar"), [
    (FullSkyChart(), False),
    (RegionalChart(center_alt_deg=45.0, center_az_deg=180.0,
                   field_width_deg=30.0, field_height_deg=20.0), False),
    (PolarPlanisphereChart(pole="north"), True),
    (PolarPlanisphereChart(pole="south", flip_ew=True), True),
])
@pytest.mark.parametrize("policy", ["chart", "upright"])
def test_chart_render_routes_apply_object_label_orientation(chart, polar, policy):
    from wenu import CelestialSphere, PublicationStyle

    layer = object()
    class Sky(CelestialSphere):
        def __init__(self):
            super().__init__(object())
            self.stars = layer

        def draw_chart(self, **kwargs):
            return kwargs["layer_options"]

    class Renderer:
        def set_clip_boundary(self, *args, **kwargs):
            pass

    result = chart.render(
        Sky(), Renderer(), observer=object(),
        style=PublicationStyle(labels_orientation=policy),
        layer_options={layer: {"render": {"label_style": {"fontsize": 7.0}}}},
    )
    rotation = result[layer]["render"]["label_style"]["rotation"]
    if polar and policy == "chart":
        assert rotation(1.0, 0.0) == pytest.approx(-90.0)
    else:
        assert rotation == 0.0


@pytest.mark.parametrize("policy", ["upright", "up-away-from-cp"])
def test_auto_placement_retains_final_orientation_and_fixed_track_dates(policy):
    from wenu.charts.label_placement import apply_object_label_orientation

    layer = object()
    options = apply_object_label_orientation(
        {layer: {"render": {"label_style": {"fontsize": 7.0, "color": "red",
                                             "placement": "auto"}}}},
        sky=SimpleNamespace(stars=layer),
        style=SimpleNamespace(labels_orientation=policy), polar=True,
    )[layer]["render"]
    figure, ax = plt.subplots(figsize=(4, 4))
    try:
        ax.set(xlim=(-2, 2), ylim=(-2, 2), aspect="equal")
        renderer = MatplotlibRenderer(ax)
        date = ax.text(0.0, -1.0, "15 Oct", rotation=37.0)
        before = (date.get_position(), date.get_rotation(), date.get_ha(), date.get_va())
        points = ProjectedPoints(np.asarray([0.0, 0.015]), np.asarray([-1.0, -1.01]),
                                 labels=np.asarray(["Albireo", "beta2"], dtype=object))
        artists = renderer.draw(points, style={"s": 12.0}, draw_labels=True, **options)
        figure.canvas.draw()
        renderer.finalize_label_placement()
        labels = [artist for artist in artists if hasattr(artist, "get_text")]
        assert len(labels) == 2
        assert any(np.linalg.norm(np.asarray(text.get_position()) - np.asarray((0, -1))) > 0.02
                   for text in labels)
        for text in labels:
            assert text.get_color() == "red"
            assert text.get_fontsize() == 7.0
            if policy == "upright":
                assert text.get_rotation() == 0.0
            else:
                x, y = text.get_position()
                angle = np.radians(text.get_rotation())
                up = np.asarray([-np.sin(angle), np.cos(angle)])
                np.testing.assert_allclose(up, np.asarray([x, y]) / np.hypot(x, y), atol=1e-12)
        assert (date.get_position(), date.get_rotation(), date.get_ha(), date.get_va()) == before
        final = [(text.get_position(), text.get_rotation()) for text in labels]
        renderer.finalize_label_placement()
        for text, (position, rotation) in zip(labels, final):
            np.testing.assert_allclose(text.get_position(), position, atol=1e-12)
            assert text.get_rotation() == pytest.approx(rotation, abs=1e-12)
    finally:
        plt.close(figure)


@pytest.mark.parametrize("placement", ["fixed", "auto"])
def test_reference_policy_uses_one_shared_tangent_procedure(placement):
    from wenu.charts.style_overrides import ChartStyleOverrides
    observer = SimpleNamespace(
        lat_deg=-32.0,
        icrs_frame=ICRS(),
        ecliptic_frame=BarycentricMeanEcliptic(),
        galactic_frame=Galactic(),
        altaz_frame=AltAz(
            obstime=Time("2026-08-02T00:00:00"),
            location=EarthLocation(
                lat=-32.0 * u.deg,
                lon=-71.0 * u.deg,
            ),
        ),
    )
    curve = ProjectedCurve(
        np.asarray([-1.0, 0.0, 1.0]),
        np.asarray([0.0, 0.5, 1.0]),
    )

    charts = (
        FullSkyChart(),
        RegionalChart(35.0, 210.0, 30.0, 20.0),
        CircumpolarChart(observer, -30.0),
        BinocularChart(35.0, 210.0),
    )
    for chart in charts:
        composition = compose_chart(
            chart,
            style="atlas",
            style_overrides=ChartStyleOverrides(star_label_placement=placement),
            furniture=ChartFurnitureOptions(
                references=ReferenceAnnotations(
                    ecliptic=ReferencePlaneAnnotation(
                        state="labeled",
                        label="Ecliptic",
                        anchor=(0.0, 0.0),
                    ),
                    galactic_plane=ReferencePlaneAnnotation(
                        state="labeled",
                        label="Galactic plane",
                        anchor=(0.0, 0.0),
                    ),
                )
            ),
        )
        overlay = build_celestial_reference_sky(
            SimpleNamespace(observer=observer), composition
        )
        options = _reference_layer_options(overlay, composition, chart)
        placements = [
            options[layer]["render"]["label_anchor"](curve)
            for layer in overlay.layers
        ]

        assert all(
            isinstance(item, CurveLabelPlacement) for item in placements
        )
        assert placements[0].rotation_deg == placements[1].rotation_deg
        assert placements[0].rotation_deg == pytest.approx(
            np.degrees(np.arctan2(1.0, 2.0))
        )
        assert placements[0].normal_offset_em == 0.75
        assert all(not options[layer]["render"]["label_anchor"].candidates(curve) for layer in overlay.layers)


@pytest.mark.parametrize("placement", ["fixed", "auto"])
def test_automatic_reference_labels_reserve_separated_positions(placement):
    from wenu.charts.style_overrides import ChartStyleOverrides
    observer = SimpleNamespace(
        lat_deg=-32.0,
        icrs_frame=ICRS(),
        ecliptic_frame=BarycentricMeanEcliptic(),
        galactic_frame=Galactic(),
        altaz_frame=AltAz(
            obstime=Time("2026-08-02T00:00:00"),
            location=EarthLocation(lat=-32.0 * u.deg, lon=-71.0 * u.deg),
        ),
    )
    labeled = lambda text: ReferencePlaneAnnotation(
        state="labeled", label=text
    )
    chart = PolarPlanisphereChart()
    composition = compose_chart(
        chart,
        style="atlas",
        mode="print",
        style_overrides=ChartStyleOverrides(star_label_placement=placement),
        furniture=ChartFurnitureOptions(
            references=ReferenceAnnotations(
                ecliptic=labeled("Ecliptic"),
                galactic_plane=labeled("Galactic plane"),
            )
        ),
    )
    overlay = build_celestial_reference_sky(
        SimpleNamespace(observer=observer),
        composition,
        observer=observer,
        chart=chart,
    )
    options = _reference_layer_options(overlay, composition, chart)
    curve = ProjectedCurve(
        np.linspace(-1.5, 1.5, 121),
        np.zeros(121),
    )

    placements = [
        options[layer]["render"]["label_anchor"](curve)
        for layer in overlay.layers
    ]

    assert all(isinstance(item, CurveLabelPlacement) for item in placements)
    viewport = composition.context.viewport
    separation = np.hypot(
        (placements[0].x - placements[1].x) / viewport.width,
        (placements[0].y - placements[1].y) / viewport.height,
    )
    assert separation >= 0.10 - 1.0e-12
    for layer in overlay.layers:
        candidates = options[layer]["render"]["label_anchor"].candidates(curve)
        assert bool(candidates) == (placement == "auto")
        assert all(item.normal_offset_em == .75 for item in candidates)


def test_polar_reference_policy_uses_pole_down_orientation_exclusively():
    observer = SimpleNamespace(
        lat_deg=-32.0,
        icrs_frame=ICRS(),
        ecliptic_frame=BarycentricMeanEcliptic(),
        galactic_frame=Galactic(),
        altaz_frame=AltAz(
            obstime=Time("2026-08-02T00:00:00"),
            location=EarthLocation(lat=-32.0 * u.deg, lon=-71.0 * u.deg),
        ),
    )
    annotation = ReferencePlaneAnnotation(
        state="labeled",
        label="Ecliptic",
        anchor=(0.0, -1.0),
    )
    curve = ProjectedCurve(
        np.asarray((-1.0, 0.0, 1.0)),
        np.asarray((-1.0, -1.0, -1.0)),
    )

    placements = []
    for chart in (PolarPlanisphereChart(), FullSkyChart()):
        composition = compose_chart(
            chart,
            style="atlas",
            furniture=ChartFurnitureOptions(
                references=ReferenceAnnotations(ecliptic=annotation)
            ),
        )
        overlay = build_celestial_reference_sky(
            SimpleNamespace(observer=observer),
            composition,
            observer=observer,
            chart=chart,
        )
        options = _reference_layer_options(overlay, composition, chart)
        placements.append(
            options[overlay.layers[0]]["render"]["label_anchor"](curve)
        )

    assert placements[0].rotation_deg == pytest.approx(-180.0)
    assert placements[1].rotation_deg == pytest.approx(0.0)


def test_polar_reference_overlay_contains_grid_planes_points_and_poles():
    obstime = Time("2026-08-02T00:00:00")
    observer = SimpleNamespace(
        lat_deg=-32.0,
        t_astropy=obstime,
        icrs_frame=ICRS(),
        ecliptic_frame=BarycentricMeanEcliptic(),
        galactic_frame=Galactic(),
        altaz_frame=AltAz(
            obstime=obstime,
            location=EarthLocation(lat=-32.0 * u.deg, lon=-71.0 * u.deg),
        ),
    )
    labeled = lambda text: ReferencePlaneAnnotation(
        state="labeled", label=text
    )
    chart = PolarPlanisphereChart()
    composition = compose_chart(
        chart,
        style="atlas",
        mode="print",
        detail_overrides=DetailOverrides(
            enabled_layer_additions=frozenset({"equatorial_grid"}),
        ),
        furniture=ChartFurnitureOptions(
            references=ReferenceAnnotations(
                celestial_equator=labeled("Celestial equator"),
                ecliptic=labeled("Ecliptic"),
                galactic_plane=labeled("Galactic plane"),
            ),
            poles=PoleAnnotations(ecliptic="both", galactic="both"),
        ),
    )

    overlay = build_celestial_reference_sky(
        SimpleNamespace(observer=observer),
        composition,
        observer=observer,
        chart=chart,
    )
    equatorial = [
        layer
        for layer in overlay.layers
        if getattr(layer, "coordinate_system", None) == "equatorial"
    ]

    assert len(equatorial) == 2
    assert equatorial[0].ra == (0.0, 90.0, 180.0, 270.0)
    assert equatorial[0].dec == tuple(float(v) for v in range(-80, 81, 20))
    assert equatorial[1].include_equator is True
    assert len(overlay.points) == 8
    metadata = overlay.points._style_metadata()
    assert set(metadata["marker"]) == {"x"}
    np.testing.assert_allclose(metadata["size"], [12.0] * 8)
    assert all(
        style["linewidths"] == pytest.approx(0.55)
        for style in metadata["style"]
    )
    assert [point.label for point in overlay.points._points[:4]] == [
        "", "", "", ""
    ]
    assert [point.label for point in overlay.points._points[-4:]] == [
        "♈", "♋", "♎", "♑"
    ]


@pytest.mark.parametrize(
    "projection_name", ("polar_azimuthal_equidistant", "stereographic")
)
@pytest.mark.parametrize(
    ("pole", "expected_count"), (("south", 24), ("north", 24))
)
def test_polar_declination_ticks_are_short_projected_furniture(
    projection_name,
    pole,
    expected_count,
):
    chart = PolarPlanisphereChart(
        pole=pole,
        limiting_declination_deg=20.0 if pole == "south" else -20.0,
        projection_name=projection_name,
    )

    ticks = polar_declination_tick_geometry(chart)

    assert len(ticks) == expected_count
    assert all(len(curve.x) == 2 for curve in ticks)
    assert all(len(curve.y) == 2 for curve in ticks)
    assert all(curve.closed is False for curve in ticks)
