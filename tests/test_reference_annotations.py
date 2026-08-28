"""Current reference annotations contracts."""

# Contracts consolidated from test_milestone44c_celestial_references.py.
"""Milestone 44C canonical celestial-reference annotations."""

from types import SimpleNamespace

import numpy as np
import pytest
from astropy.coordinates import (
    BarycentricMeanEcliptic,
    BarycentricTrueEcliptic,
    Galactic,
    ICRS,
)
from astropy.time import Time

from wenu import (
    BinocularChart,
    BoundaryAwareReferenceAnchor,
    ChartFurnitureOptions,
    ChartStyleOverrides,
    FooterOptions,
    PoleAnnotations,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
    RegionalChart,
    build_celestial_reference_sky,
    compose_chart,
    LegendOptions,
)
from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.geometry.projected import ProjectedCurve, ProjectedPoints
from wenu.geometry.spherical import SphericalPoints
from wenu.charts.reference_furniture import _reference_layer_options


def observer():
    return SimpleNamespace(
        lat_deg=-32.0,
        icrs_frame=ICRS(),
        ecliptic_frame=BarycentricMeanEcliptic(),
        galactic_frame=Galactic(),
    )


def chart():
    return RegionalChart(35.0, 210.0, 30.0, 20.0)


def test_reference_overlay_is_opt_in():
    composition = compose_chart(chart(), style="atlas")
    sky = SimpleNamespace(observer=observer())

    assert build_celestial_reference_sky(sky, composition) is None


def test_binocular_target_marker_is_render_local_reference_furniture():
    binocular = BinocularChart(
        35.0,
        210.0,
        target_ra_deg=201.365,
        target_dec_deg=-43.019,
    )
    composition = compose_chart(
        binocular,
        style="atlas",
        furniture=ChartFurnitureOptions(),
    )
    sky = SimpleNamespace(observer=observer())

    overlay = build_celestial_reference_sky(
        sky,
        composition,
        chart=binocular,
    )

    assert overlay is not None
    assert len(overlay.points) == 1
    point = overlay.points._points[0]
    assert point.marker == "+"
    assert point.label is None
    assert point.coord.icrs.ra.deg == pytest.approx(201.365)
    assert point.coord.icrs.dec.deg == pytest.approx(-43.019)


def test_reference_sky_contains_only_requested_semantic_geometry():
    composition = compose_chart(
        chart(),
        style="atlas",
        mode="presentation",
        furniture=ChartFurnitureOptions(
            references=ReferenceAnnotations(
                celestial_equator=ReferencePlaneAnnotation(
                    state="labeled",
                    label="Celestial equator",
                ),
                ecliptic=ReferencePlaneAnnotation(
                    state="labeled",
                    label="Ecliptic",
                ),
                galactic_plane=ReferencePlaneAnnotation(
                    state="line",
                    label="Galactic plane",
                ),
            ),
            poles=PoleAnnotations(
                celestial="both",
                ecliptic="visible",
                galactic="both",
            ),
        ),
    )
    overlay = build_celestial_reference_sky(
        SimpleNamespace(observer=observer()),
        composition,
    )

    assert [layer.coordinate_system for layer in overlay.layers[:3]] == [
        "equatorial",
        "ecliptic",
        "galactic",
    ]
    assert overlay.layers[0].include_equator is True
    assert overlay.layers[1].include_ecliptic is True
    assert overlay.layers[2].include_plane is True
    assert len(overlay.points) == 5
    metadata = overlay.points._style_metadata()
    assert metadata["marker"][:2].tolist() == ["+", "+"]
    assert set(metadata["marker"][2:]) == {"x"}


def test_both_poles_use_conventional_labels():
    composition = compose_chart(
        chart(),
        style="cartoon",
        furniture=ChartFurnitureOptions(
            poles=PoleAnnotations(
                celestial="both",
                ecliptic="both",
                galactic="both",
            )
        ),
    )
    overlay = build_celestial_reference_sky(
        SimpleNamespace(observer=observer()),
        composition,
    )

    labels = [point.label for point in overlay.points._points]
    assert labels == ["NCP", "SCP", "NEP", "SEP", "NGP", "SGP"]


def test_labeled_ecliptic_keypoints_use_the_reference_ecliptic_frame():
    resolved_observer = observer()
    resolved_observer.t_astropy = Time("2026-08-16")
    composition = compose_chart(
        chart(),
        style="cartoon",
        furniture=ChartFurnitureOptions(
            references=ReferenceAnnotations(
                ecliptic_keypoints="labeled"
            ),
            poles=PoleAnnotations(labels=False),
        ),
    )

    overlay = build_celestial_reference_sky(
        SimpleNamespace(observer=resolved_observer),
        composition,
    )

    assert len(overlay.points) == 4
    expected = BarycentricTrueEcliptic(
        equinox=resolved_observer.t_astropy
    )
    assert all(
        point.coord.frame.is_equivalent_frame(expected)
        for point in overlay.points._points
    )
    assert [point.label for point in overlay.points._points] == [
        "♈", "♋", "♎", "♑"
    ]


def test_rectangular_reference_furniture_preserves_all_keypoint_altitudes():
    resolved_observer = observer()
    resolved_observer.t_astropy = Time("2026-08-16")
    subject = chart()
    composition = compose_chart(
        subject,
        style="cartoon",
        furniture=ChartFurnitureOptions(
            references=ReferenceAnnotations(
                ecliptic_keypoints="labeled"
            )
        ),
    )
    overlay = build_celestial_reference_sky(
        SimpleNamespace(observer=resolved_observer),
        composition,
    )
    options = _reference_layer_options(overlay, composition, subject)
    labels = np.asarray(["♈", "♋", "♎", "♑"], dtype=object)
    spherical = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=np.asarray([91.0, 190.0, 271.0, 10.0]),
        lat_deg=np.asarray([-1.51, -80.86, 1.50, 80.86]),
        labels=labels,
    )
    projected = ProjectedPoints(
        x=np.asarray([-0.8, -0.4, 0.4, 0.8]),
        y=np.asarray([0.0, 0.0, 0.0, 0.0]),
        labels=labels,
    )

    prepared = options[overlay.points]["prepare"](
        spherical,
        projected,
    )

    assert prepared.finite.tolist() == [True, True, True, True]
    assert prepared.labels.tolist() == ["♈", "♋", "♎", "♑"]


def test_rectangular_automatic_anchor_uses_visible_curve_segment():
    context = chart().chart_context
    anchor = BoundaryAwareReferenceAnchor(context)
    curve = ProjectedCurve(
        x=np.asarray([-10.0, -0.1, 0.0, 0.1, 10.0]),
        y=np.asarray([10.0, -0.1, 0.0, 0.1, -10.0]),
        name="ecliptic",
    )

    x, y = anchor(curve)
    assert context.viewport.contains(x, y)


def test_rectangular_anchor_avoids_legend_corners_and_chart_edges():
    context = chart().chart_context
    anchor = BoundaryAwareReferenceAnchor(
        context,
        avoid_locations=("upper right", "lower right"),
    )
    curve = ProjectedCurve(
        x=np.linspace(context.viewport.x_min, context.viewport.x_max, 101),
        y=np.linspace(context.viewport.y_min, context.viewport.y_max, 101),
        name="ecliptic",
    )

    x, y = anchor(curve)
    normalized_x = (
        (x - context.viewport.x_min) / context.viewport.width
    )
    normalized_y = (
        (y - context.viewport.y_min) / context.viewport.height
    )
    assert 0.16 <= normalized_x + 1.0e-12 <= 0.84
    assert 0.16 <= normalized_y + 1.0e-12 <= 0.84
    assert normalized_x <= 0.50


def test_circular_automatic_anchor_stays_inside_field_stop():
    context = BinocularChart(45.0, 180.0).chart_context
    radius = np.nanmedian(
        np.hypot(
            context.clip_boundary.x,
            context.clip_boundary.y,
        )
    )
    anchor = BoundaryAwareReferenceAnchor(context)
    curve = ProjectedCurve(
        x=np.linspace(-radius, radius, 73),
        y=np.zeros(73),
        name="galactic_plane",
    )

    x, y = anchor(curve)
    assert np.hypot(x, y) <= radius
    assert np.hypot(x, y) >= 0.70 * radius

    invisible = ProjectedCurve(
        x=np.asarray([-2.0, 2.0]),
        y=np.asarray([2.0, 2.0]),
        name="galactic_plane",
    )
    assert anchor(invisible) is None


def test_reference_labels_are_semantic_and_independent():
    subject = chart()
    composition = compose_chart(
        subject,
        style="atlas",
        furniture=ChartFurnitureOptions(
            references=ReferenceAnnotations(
                ecliptic=ReferencePlaneAnnotation(
                    state="labeled",
                    label="Ecliptic",
                ),
                galactic_plane=ReferencePlaneAnnotation(
                    state="line",
                    label="Galactic plane",
                ),
            )
        ),
    )
    overlay = build_celestial_reference_sky(
        SimpleNamespace(observer=observer()),
        composition,
    )
    options = _reference_layer_options(overlay, composition, subject)
    ecliptic, galactic = overlay.layers

    assert options[ecliptic]["render"]["draw_labels"] is True
    assert (
        options[ecliptic]["render"]["label_formatter"]("ecliptic")
        == "Ecliptic"
    )
    assert options[galactic]["render"]["draw_labels"] is False


def test_automatic_reference_anchor_inherits_legend_occupancy():
    subject = chart()
    composition = compose_chart(
        subject,
        style="atlas",
        furniture=ChartFurnitureOptions(
            references=ReferenceAnnotations(
                ecliptic=ReferencePlaneAnnotation(
                    state="labeled",
                    label="Ecliptic",
                )
            ),
            legends=LegendOptions(),
        ),
    )
    overlay = build_celestial_reference_sky(
        SimpleNamespace(observer=observer()),
        composition,
    )
    options = _reference_layer_options(overlay, composition, subject)
    anchor = options[overlay.layers[0]]["render"]["label_anchor"]

    assert anchor.delegate.avoid_locations == (
        "upper right",
        "lower right",
    )


def test_equator_reference_width_does_not_strengthen_equatorial_grid():
    subject = chart()
    composition = compose_chart(
        subject,
        style="cartoon",
        style_overrides=ChartStyleOverrides(
            equatorial_reference_linewidth=1.0,
        ),
        furniture=ChartFurnitureOptions(
            references=ReferenceAnnotations(
                celestial_equator=ReferencePlaneAnnotation(state="line")
            )
        ),
    )
    overlay = build_celestial_reference_sky(
        SimpleNamespace(observer=observer()),
        composition,
    )
    options = _reference_layer_options(overlay, composition, subject)

    assert options[overlay.layers[0]]["render"]["style"][
        "linewidth"
    ] == pytest.approx(1.0)
    assert composition.style.grids.coordinate_linewidth != pytest.approx(1.0)


def test_reference_anchor_labels_only_one_visible_segment():
    subject = chart()
    composition = compose_chart(
        subject,
        style="atlas",
        furniture=ChartFurnitureOptions(
            references=ReferenceAnnotations(
                ecliptic=ReferencePlaneAnnotation(
                    state="labeled",
                    label="Ecliptic",
                )
            )
        ),
    )
    overlay = build_celestial_reference_sky(
        SimpleNamespace(observer=observer()),
        composition,
    )
    options = _reference_layer_options(overlay, composition, subject)
    anchor = options[overlay.layers[0]]["render"]["label_anchor"]
    curve = ProjectedCurve(
        x=np.asarray([-0.1, 0.0, 0.1]),
        y=np.asarray([-0.1, 0.0, 0.1]),
        name="ecliptic",
    )

    assert anchor(curve) is not None
    assert anchor(curve) is None


def test_explicit_reference_anchor_is_preserved_by_composition():
    position = (0.125, -0.25)
    composition = compose_chart(
        chart(),
        style="atlas",
        furniture=ChartFurnitureOptions(
            references=ReferenceAnnotations(
                ecliptic=ReferencePlaneAnnotation(
                    state="labeled",
                    label="Ecliptic",
                    anchor=position,
                )
            )
        ),
    )

    assert composition.furniture.references.ecliptic.anchor == position


def test_footer_only_furniture_does_not_build_celestial_geometry():
    composition = compose_chart(
        chart(),
        style="atlas",
        furniture=ChartFurnitureOptions(
            footer=FooterOptions(application=True)
        ),
    )

    assert build_celestial_reference_sky(
        SimpleNamespace(observer=observer()),
        composition,
    ) is None


def test_reference_policy_module_has_no_backend_import():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    source = (
        root / "src/wenu/charts/reference_furniture.py"
    ).read_text(encoding="utf-8")
    assert "matplotlib" not in source.lower()