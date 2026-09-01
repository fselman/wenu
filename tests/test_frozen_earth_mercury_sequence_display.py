"""Drawable frozen-Earth Mercury through shared moving-body machinery."""

from argparse import Namespace

import pytest

from wenu.charts.chart_arguments import (
    _SEQUENCE_BODY_KEYS,
    chart_disk_options,
    chart_disk_sequence_options,
)
from wenu.charts.drawing import _frozen_title
from wenu.charts.request_disks import (
    FrozenEarthSolarSystemDiskSequenceDisplayRequest,
)
from wenu.sky.frozen_earth_venus_disk_sequence import (
    frozen_earth_solar_system_disk_sequence_layers,
)
from wenu.sky.mercury import MERCURY_BODY
from wenu.sky.semantic_identity import semantic_layer_identity


def arguments(**values):
    defaults = {
        "planet_appearance": [],
        "planet_disk_magnification": ["mercury=200"],
        "planet_disk_sequence": "mercury",
        "disk_sequence_model": "frozen-earth-ecliptic",
        "disk_sequence_start": "2026-08-30T00:00:00Z",
        "disk_sequence_step": 2.0,
        "disk_sequence_n_steps": 3,
        "disk_sequence_labels": True,
    }
    defaults.update(values)
    return Namespace(**defaults)


def test_cli_exposes_mercury_only_for_its_catalog_capability():
    assert "mercury" in _SEQUENCE_BODY_KEYS
    value = chart_disk_sequence_options(arguments())
    assert isinstance(value, FrozenEarthSolarSystemDiskSequenceDisplayRequest)
    assert value.sequence.descriptor is MERCURY_BODY
    assert value.sequence.sample_offsets_days == (0.0, 2.0, 4.0, 6.0)
    assert value.magnification == 200.0
    assert value.label_dates is True
    assert chart_disk_options(arguments()) == ()


def test_cli_rejects_unvalidated_observed_mercury():
    with pytest.raises(
        ValueError,
        match="Mercury does not support the observed disk-sequence model",
    ):
        chart_disk_sequence_options(arguments(disk_sequence_model="observed"))


def test_shared_factory_derives_mercury_layers_and_semantics_from_descriptor():
    request = chart_disk_sequence_options(arguments())
    layers = frozen_earth_solar_system_disk_sequence_layers(
        request.sequence,
        magnification=request.magnification,
        label_dates=True,
    )
    assert tuple(layer.layer_name for layer in layers) == (
        "mercury_disk_sequence_frozen_illuminated",
        "mercury_disk_sequence_frozen_limb",
        "mercury_disk_sequence_frozen_terminator",
        "mercury_disk_sequence_frozen_labels",
        "frozen_earth_sun",
    )
    assert len({id(layer.disk_realization) for layer in layers}) == 1
    assert tuple(
        semantic_layer_identity(layer).semantic_path_text for layer in layers
    ) == (
        "sky/solar_system/planets/mercury/frozen_earth_sequence/illuminated",
        "sky/solar_system/planets/mercury/frozen_earth_sequence/limb",
        "sky/solar_system/planets/mercury/frozen_earth_sequence/terminator",
        "sky/solar_system/planets/mercury/frozen_earth_sequence/labels",
        "sky/solar_system/star/sun",
    )
    assert all(layer.magnification == 200.0 for layer in layers[:-1])
    assert layers[-1].magnification == 1.0


def test_frozen_title_uses_descriptor_localization_without_body_branching():
    assert _frozen_title("en", MERCURY_BODY) == (
        "Frozen-Earth Mercury sequence"
    )
    assert _frozen_title("es", MERCURY_BODY) == (
        "Secuencia de Mercurio desde una Tierra fija"
    )
