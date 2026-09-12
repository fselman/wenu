"""Explicit chart-center grammar and namespace resolution contracts."""

import argparse

import pytest

from wenu.charts.center_arguments import (
    parse_degree_angle,
    parse_icrs_ra,
    resolve_named_center,
)


def test_explicit_angles_require_units_and_preserve_coordinate_semantics():
    assert parse_icrs_ra("02h20m35s") == pytest.approx(35.1458333333)
    assert parse_icrs_ra("35.145833deg") == pytest.approx(35.145833)
    assert parse_degree_angle("-15deg") == pytest.approx(-15.0)

    with pytest.raises(argparse.ArgumentTypeError):
        parse_icrs_ra("35.145833")
    with pytest.raises(argparse.ArgumentTypeError):
        parse_degree_angle("-15")


def test_unqualified_unique_constellation_resolves_offline():
    center = resolve_named_center("Vir")

    assert center.kind == "constellation"
    assert center.value.constellations == ("Vir",)


@pytest.mark.parametrize(
    ("specification", "kind", "identity"),
    (
        ("constellation:Vir", "constellation", "Vir"),
        ("group:summer-triangle", "group", "Cyg"),
        ("planet:Venus", "planet", "venus"),
        ("asteroid:Ceres", "asteroid", "ceres"),
        ("target:Centaurus A", "target", "centaurus-a"),
        ("galaxy:Centaurus A", "galaxy", "centaurus-a"),
        ("cluster:M13", "cluster", "m13"),
        ("nebula:M57", "nebula", "m57"),
    ),
)
def test_qualified_namespaces_resolve_expected_identity(
    specification, kind, identity
):
    center = resolve_named_center(specification)
    value = center.value
    resolved_identity = (
        value.constellations[0]
        if center.is_constellation else value.selection_key
        if hasattr(value, "selection_key") else value.key
    )

    assert center.kind == kind
    assert resolved_identity == identity


def test_namespace_qualifier_validates_target_family():
    with pytest.raises(ValueError, match="not a packaged cluster"):
        resolve_named_center("cluster:Centaurus A")


def test_unknown_namespace_and_unknown_identifier_are_rejected():
    with pytest.raises(ValueError, match="unknown center namespace"):
        resolve_named_center("catalogue:M31")
    with pytest.raises(ValueError, match="unknown center identifier"):
        resolve_named_center("Not A Packaged Object")


def test_earth_is_not_a_geocentric_chart_center():
    with pytest.raises(ValueError, match="observer origin"):
        resolve_named_center("planet:Earth")
