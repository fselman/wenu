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
from wenu.charts.reference_furniture import _reference_layer_options
from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
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


def test_reference_policy_uses_one_shared_tangent_procedure():
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


def test_polar_reference_overlay_contains_grid_planes_points_and_poles():
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
