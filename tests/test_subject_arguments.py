"""Shared constellation-subject command-line contracts."""

import argparse

import pytest

from wenu import (
    ChartConstellationSubjectOptions,
    add_constellation_subject_arguments,
    chart_constellation_subject,
    parse_constellation_list,
)


def parser(**defaults):
    return add_constellation_subject_arguments(
        argparse.ArgumentParser(), **defaults
    )


def test_arbitrary_iau_list_is_normalized_once_for_the_view():
    arguments = parser().parse_args([
        "--constellations", "sgr, Sco,oph,Ser"
    ])
    subject = chart_constellation_subject(arguments)

    assert subject == ChartConstellationSubjectOptions(
        constellations=("Sgr", "Sco", "Oph", "Ser")
    )
    assert subject.view_arguments() == {
        "constellations": ("Sgr", "Sco", "Oph", "Ser"),
        "group": None,
    }


def test_public_constellation_list_parser_reuses_iau_normalization():
    assert parse_constellation_list("sco, SGR") == ("Sco", "Sgr")


def test_packaged_group_remains_an_optional_alias_form():
    arguments = parser(
        default_constellations=("Cru", "Cen")
    ).parse_args(["--group", "summer-triangle"])

    assert chart_constellation_subject(arguments) == (
        ChartConstellationSubjectOptions(group="summer-triangle")
    )


def test_subject_forms_are_mutually_exclusive_and_diagnostic():
    value = parser()
    with pytest.raises(SystemExit):
        value.parse_args([
            "--constellations", "Cru,Cen", "--group", "summer-triangle"
        ])
    with pytest.raises(SystemExit):
        value.parse_args(["--constellations", "Cru,NotIAU"])


def test_subject_requires_exactly_one_form():
    with pytest.raises(ValueError, match="either constellations"):
        chart_constellation_subject(parser().parse_args([]))
    with pytest.raises(ValueError, match="mutually exclusive"):
        parser(
            default_constellations=("Cru",),
            default_group="summer-triangle",
        )


def test_optional_subject_can_represent_an_unmasked_planisphere():
    arguments = parser().parse_args([])

    assert chart_constellation_subject(
        arguments, required=False
    ) is None
