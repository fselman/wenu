"""Typed paint-order vocabulary and compatibility contracts."""

from dataclasses import FrozenInstanceError

import pytest

from wenu.rendering import layers
from wenu.rendering.paint_roles import (
    EXTENDED_SKY_BAND,
    LABELS,
    LABEL_BAND,
    PAINT_BANDS,
    PAINT_ROLES,
    STARS,
    STAR_BAND,
    paint_role_for_zorder,
)


def test_paint_roles_are_unique_and_strictly_ordered():
    values = [role.zorder for role in PAINT_ROLES]
    names = [role.name for role in PAINT_ROLES]

    assert values == sorted(values)
    assert len(values) == len(set(values))
    assert len(names) == len(set(names))


def test_existing_numeric_layer_constants_remain_compatible():
    assert layers.MILKY_WAY == 1.0
    assert layers.CONSTELLATIONS == 4.0
    assert layers.STARS == 5.0
    assert layers.LABELS == 7.0
    assert layers.GALAXY_LABELS == layers.LABELS


def test_exact_zorder_resolves_to_typed_role():
    assert paint_role_for_zorder(layers.STARS) is STARS
    assert paint_role_for_zorder(layers.LABELS) is LABELS
    assert paint_role_for_zorder(3.25) is None
    assert paint_role_for_zorder(None) is None


def test_paint_roles_are_immutable_and_have_svg_tokens():
    assert STARS.svg_token == "stars"
    with pytest.raises(FrozenInstanceError):
        STARS.zorder = 99.0


def test_paint_bands_are_ordered_and_roles_reference_them():
    assert [band.rank for band in PAINT_BANDS] == list(range(9))
    assert paint_role_for_zorder(layers.MILKY_WAY).band is EXTENDED_SKY_BAND
    assert STARS.band is STAR_BAND
    assert LABELS.band is LABEL_BAND
    assert LABEL_BAND.svg_token == "labels"
