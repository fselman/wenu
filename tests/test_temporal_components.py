"""Shared temporal-component policy for tracks and physical phase sequences."""

import pytest

from wenu.sky.mercury import MERCURY_BODY
from wenu.sky.moon import MOON_BODY
from wenu.sky.solar_system_disk_sequences import (
    ObservedSolarSystemDiskSequenceRequest,
)
from wenu.sky.venus import VENUS_POINT
from wenu.sky.venus_disk_sequence import (
    observed_solar_system_disk_sequence_layers,
)
from wenu.temporal_components import TemporalComponentPolicy


def sequence(descriptor):
    return ObservedSolarSystemDiskSequenceRequest(
        descriptor=descriptor,
        start_instant="2026-09-06T00:00:00Z",
        start_time_scale="utc",
        step_days=2.0,
        n_steps=3,
        display_name=descriptor.display_name,
        physical_radius_km=descriptor.physical_radius_km,
        radius_model=descriptor.radius_model,
    )


@pytest.mark.parametrize(
    ("cadence", "expected"),
    (("none", ()), ("start", (0,)), ("major", (0, 1, 2, 3))),
)
def test_start_inclusive_cadence_selection_is_shared(cadence, expected):
    assert TemporalComponentPolicy.indices(cadence, 4) == expected


@pytest.mark.parametrize("descriptor", (VENUS_POINT, MERCURY_BODY, MOON_BODY))
def test_phase_bodies_use_common_start_only_component_policy(descriptor):
    policy = TemporalComponentPolicy(
        path=False, ticks=False, symbols="start", labels="start"
    )

    layers = observed_solar_system_disk_sequence_layers(
        sequence(descriptor), temporal_components=policy
    )

    assert tuple(layer.component_role for layer in layers) == (
        "illuminated", "limb", "terminator", "labels",
    )
    assert all(layer.sample_indices == (0,) for layer in layers)
    assert len({id(layer.disk_realization) for layer in layers}) == 1


def test_phase_symbols_and_labels_can_be_suppressed_independently():
    labels_only = TemporalComponentPolicy(
        path=False, ticks=False, symbols="none", labels="major"
    )
    symbols_only = TemporalComponentPolicy(
        path=False, ticks=False, symbols="major", labels="none"
    )

    label_layers = observed_solar_system_disk_sequence_layers(
        sequence(VENUS_POINT), temporal_components=labels_only
    )
    symbol_layers = observed_solar_system_disk_sequence_layers(
        sequence(VENUS_POINT), temporal_components=symbols_only
    )

    assert tuple(layer.component_role for layer in label_layers) == ("labels",)
    assert tuple(layer.component_role for layer in symbol_layers) == (
        "illuminated", "limb", "terminator",
    )
    assert all(layer.sample_indices == (0, 1, 2, 3) for layer in symbol_layers)
