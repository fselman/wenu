"""Contracts for milestone 49I.3E.3 observed multi-epoch Moon display."""

import argparse

import pytest

from wenu import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    add_chart_arguments,
)
from wenu.charts.chart_arguments import (
    chart_disk_options,
    chart_disk_sequence_options,
)
from wenu.charts.request_disks import (
    ObservedSolarSystemDiskSequenceDisplayRequest,
)
from wenu.sky.moon import MOON_BODY
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.solar_system_bodies import OBSERVED_DISK_SEQUENCE
from wenu.sky.venus import VENUS_POINT
from wenu.sky.venus_disk_sequence import (
    observed_solar_system_disk_sequence_layers,
)


def parser():
    value = argparse.ArgumentParser()
    return add_chart_arguments(value, default_output="output/reference.png")


def moon_sequence_arguments(*extra):
    return parser().parse_args([
        "--moon-disk-sequence",
        "--disk-sequence-model", "observed",
        "--disk-sequence-start", "2026-09-06T00:00:00Z",
        "--disk-sequence-step", "2d",
        "--disk-sequence-n-steps", "6",
        *extra,
    ])


def test_cli_adapts_moon_vocabulary_to_shared_observed_sequence():
    request = chart_disk_sequence_options(moon_sequence_arguments(
        "--disk-sequence-labels",
        "--moon-disk-magnification", "8",
    ))

    assert isinstance(request, ObservedSolarSystemDiskSequenceDisplayRequest)
    assert request.sequence.descriptor is MOON_BODY
    assert request.sequence.sample_count == 7
    assert request.sequence.sample_offsets_days == (
        0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0,
    )
    assert request.model == "observed"
    assert request.magnification == 8.0
    assert request.label_dates is True
    assert chart_disk_options(moon_sequence_arguments()) == ()


@pytest.mark.parametrize(
    "extra, message",
    (
        (("--disk-sequence-model", "frozen-earth-ecliptic"), "does not support"),
        (("--moon",), "both a single disk and a disk sequence"),
        (("--moon-appearance", "symbolic"), "both a single disk"),
        (("--planet-disk-sequence", "venus"), "not both"),
    ),
)
def test_moon_sequence_rejects_unsupported_models_and_representations(
    extra, message
):
    arguments = moon_sequence_arguments(*extra)
    with pytest.raises(ValueError, match=message):
        chart_disk_sequence_options(arguments)


def test_partial_sequence_controls_require_an_explicit_selector():
    arguments = parser().parse_args([
        "--disk-sequence-model", "observed",
        "--disk-sequence-start", "2026-09-06T00:00:00Z",
        "--disk-sequence-step", "2d",
        "--disk-sequence-n-steps", "6",
    ])
    with pytest.raises(ValueError, match="requires --planet-disk-sequence or"):
        chart_disk_sequence_options(arguments)


def chart_request(family, sequence):
    values = {
        "observer": ChartObserverRequest(
            location="La Ligua", time="2026-09-16T00:00:00Z"
        ),
        "family": family,
        "product": ChartProductOptions(output="output/chart.png"),
        "solar_system_disk_sequence": sequence,
    }
    if family in {"regional", "binocular"}:
        values["subject"] = ChartSubjectRequest(target="moon")
    if family == "circumpolar":
        values["frame"] = ChartFrameRequest(
            pole="south", limiting_declination_deg=-15
        )
    if family == "all_sky":
        values["projection"] = "mollweide"
        values["coordinate_frame"] = "galactic"
    return ChartRequest(**values)


@pytest.mark.parametrize(
    "family",
    ("regional", "binocular", "circumpolar", "planisphere", "all_sky"),
)
def test_moon_observed_sequence_is_authorized_in_all_chart_families(family):
    sequence = chart_disk_sequence_options(moon_sequence_arguments())

    assert sequence.supports_chart_family(family)
    assert chart_request(family, sequence).solar_system_disk_sequence is sequence


def test_moon_sequence_layers_are_generic_and_semantically_stable():
    display = chart_disk_sequence_options(moon_sequence_arguments(
        "--disk-sequence-labels"
    ))
    layers = observed_solar_system_disk_sequence_layers(
        display.sequence,
        magnification=display.magnification,
        label_dates=display.label_dates,
    )

    assert tuple(layer.layer_name for layer in layers) == (
        "moon_disk_sequence_illuminated",
        "moon_disk_sequence_limb",
        "moon_disk_sequence_terminator",
        "moon_disk_sequence_labels",
    )
    assert len({id(layer.disk_realization) for layer in layers}) == 1
    assert tuple(
        semantic_layer_identity(layer).semantic_path_text for layer in layers
    ) == (
        "sky/solar_system/natural_satellites/moon/disk_sequence/illuminated",
        "sky/solar_system/natural_satellites/moon/disk_sequence/limb",
        "sky/solar_system/natural_satellites/moon/disk_sequence/terminator",
        "sky/solar_system/natural_satellites/moon/disk_sequence/labels",
    )


def test_sequence_family_policy_does_not_expand_venus():
    assert MOON_BODY.supports(OBSERVED_DISK_SEQUENCE)
    assert MOON_BODY.supports_observed_disk_sequence_in("all_sky")
    assert VENUS_POINT.supports_observed_disk_sequence_in("regional")
    assert VENUS_POINT.supports_observed_disk_sequence_in("binocular")
    assert not VENUS_POINT.supports_observed_disk_sequence_in("planisphere")
