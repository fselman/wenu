"""Contracts for milestone 49I.3E.2 resolved single-epoch Moon display."""

import argparse
from types import SimpleNamespace

import pytest

from wenu import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    add_chart_arguments,
    chart_content_options,
)
from wenu.charts.chart_arguments import chart_disk_options
from wenu.charts.context import BoundaryKind, Viewport
from wenu.charts.detail import ResolvedDetail
from wenu.charts.detail_application import composition_layer_options
from wenu.charts.request_disks import (
    SolarSystemDiskDisplayRequest,
    configure_chart_request_disks,
)
from wenu.charts.styles import PublicationStyle
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.moon import MOON_BODY
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.venus import VENUS_POINT
from wenu.sky.venus_disk import solar_system_disk_layers
from wenu.solar_system_disk_geometry import (
    DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES,
)


def parser():
    value = argparse.ArgumentParser()
    return add_chart_arguments(
        value,
        default_output="output/reference.png",
    )


def test_bare_moon_selects_one_resolved_disk_at_physical_scale():
    arguments = parser().parse_args(["--moon"])

    assert chart_content_options(arguments).moon is False
    assert chart_disk_options(arguments) == (
        SolarSystemDiskDisplayRequest(MOON_BODY, 1.0),
    )


def test_symbolic_moon_preserves_the_compatibility_point():
    arguments = parser().parse_args(
        ["--moon", "--moon-appearance", "symbolic"]
    )

    assert chart_content_options(arguments).moon is True
    assert chart_disk_options(arguments) == ()


def test_resolved_moon_magnification_is_explicit_and_display_only():
    arguments = parser().parse_args([
        "--moon",
        "--moon-appearance", "resolved",
        "--moon-disk-magnification", "1000",
    ])

    request = chart_disk_options(arguments)[0]
    assert request.descriptor is MOON_BODY
    assert request.magnification == 1000.0


@pytest.mark.parametrize("value", ("0", "nan", "inf", "1001"))
def test_moon_magnification_obeys_the_shared_finite_envelope(value):
    arguments = parser().parse_args(
        ["--moon", "--moon-disk-magnification", value]
    )

    with pytest.raises(ValueError, match="between 1 and 1000"):
        chart_disk_options(arguments)


@pytest.mark.parametrize(
    "options",
    (
        ("--moon-appearance", "resolved"),
        ("--moon-disk-magnification", "2"),
    ),
)
def test_moon_display_controls_cannot_enable_the_moon_implicitly(options):
    with pytest.raises(ValueError, match="requires --moon"):
        chart_disk_options(parser().parse_args(options))


def test_symbolic_moon_rejects_disk_magnification():
    arguments = parser().parse_args([
        "--moon",
        "--moon-appearance", "symbolic",
        "--moon-disk-magnification", "2",
    ])

    with pytest.raises(ValueError, match="requires resolved Moon"):
        chart_disk_options(arguments)


def test_moon_uses_the_generic_disk_layers_and_stable_semantics():
    layers = solar_system_disk_layers(MOON_BODY, magnification=40)

    assert tuple(layer.layer_name for layer in layers) == (
        "moon_disk_illuminated",
        "moon_disk_limb",
        "moon_disk_terminator",
    )
    assert len({id(layer.disk_realization) for layer in layers}) == 1
    assert {layer.magnification for layer in layers} == {40.0}
    assert tuple(
        semantic_layer_identity(layer).semantic_path_text for layer in layers
    ) == (
        "sky/solar_system/natural_satellites/moon/disk/illuminated",
        "sky/solar_system/natural_satellites/moon/disk/limb",
        "sky/solar_system/natural_satellites/moon/disk/terminator",
    )
    assert DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES == 720


def request_for(family, disk):
    options = {
        "observer": ChartObserverRequest(
            location="La Ligua", time="2026-09-02 00:00"
        ),
        "family": family,
        "product": ChartProductOptions(output="output/chart.png"),
        "solar_system_disks": (disk,),
    }
    if family in {"regional", "binocular"}:
        options["subject"] = ChartSubjectRequest(target="moon")
    if family == "circumpolar":
        options["frame"] = ChartFrameRequest(
            pole="south", limiting_declination_deg=-30
        )
    if family == "all_sky":
        options["projection"] = "mollweide"
        options["coordinate_frame"] = "galactic"
    return ChartRequest(**options)


@pytest.mark.parametrize(
    "family",
    ("regional", "binocular", "circumpolar", "planisphere", "all_sky"),
)
def test_resolved_moon_is_authorized_in_all_five_chart_families(family):
    disk = SolarSystemDiskDisplayRequest(MOON_BODY)

    assert request_for(family, disk).solar_system_disks == (disk,)


@pytest.mark.parametrize("family", ("circumpolar", "planisphere", "all_sky"))
def test_descriptor_policy_does_not_expand_resolved_venus_support(family):
    disk = SolarSystemDiskDisplayRequest(VENUS_POINT)

    with pytest.raises(ValueError, match=f"Venus.*{family}"):
        request_for(family, disk)


def test_moon_disk_style_is_body_owned_not_a_venus_alias():
    publication = PublicationStyle()
    sky = CelestialSphere(None)
    configure_chart_request_disks(sky, SimpleNamespace(
        solar_system_disks=(SolarSystemDiskDisplayRequest(MOON_BODY),),
        solar_system_disk_sequence=None,
    ))
    composition = SimpleNamespace(
        style=publication,
        detail=ResolvedDetail(),
        context=SimpleNamespace(
            boundary_kind=BoundaryKind.RECTANGULAR,
            viewport=Viewport(-1.0, 1.0, -1.0, 1.0),
        ),
    )

    application = composition_layer_options(
        composition, sky, reload_catalogues=False
    )
    render = application.layer_options[
        sky.moon_disk_illuminated
    ]["render"]

    assert publication.moon_disk_face_color != publication.venus_disk_face_color
    assert render["style"]["facecolor"] == publication.moon_disk_face_color
