"""Milestone 44C canonical celestial-reference annotations."""

from types import SimpleNamespace

import numpy as np
from astropy.coordinates import BarycentricMeanEcliptic, Galactic, ICRS

from wenu import (
    BinocularChart,
    BoundaryAwareReferenceAnchor,
    ChartFurnitureOptions,
    FooterOptions,
    PoleAnnotations,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
    RegionalChart,
    build_celestial_reference_sky,
    compose_chart,
)
from wenu.geometry.projected import ProjectedCurve
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


def test_reference_sky_contains_only_requested_semantic_geometry():
    composition = compose_chart(
        chart(),
        style="atlas",
        mode="presentation",
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

    assert [layer.coordinate_system for layer in overlay.layers[:2]] == [
        "ecliptic",
        "galactic",
    ]
    assert overlay.layers[0].include_ecliptic is True
    assert overlay.layers[1].include_plane is True
    assert len(overlay.points) == 5
    metadata = overlay.points._style_metadata()
    assert set(metadata["marker"]) == {"x"}


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


def test_circular_automatic_anchor_stays_inside_field_stop():
    context = BinocularChart(45.0, 180.0).chart_context
    anchor = BoundaryAwareReferenceAnchor(context)
    curve = ProjectedCurve(
        x=np.linspace(-2.0, 2.0, 73),
        y=np.zeros(73),
        name="galactic_plane",
    )

    x, y = anchor(curve)
    radius = np.nanmedian(
        np.hypot(
            context.clip_boundary.x,
            context.clip_boundary.y,
        )
    )
    assert np.hypot(x, y) <= radius

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
