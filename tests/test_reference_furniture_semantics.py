"""Cardinality-independent semantic contracts for celestial references."""

from types import SimpleNamespace

import pytest

from wenu.charts.reference_furniture import (
    _assign_polar_declination_tick_semantics,
)


@pytest.mark.parametrize("count", (0, 1, 7, 24, 40))
def test_declination_tick_identity_does_not_depend_on_tick_count(count):
    artists = tuple(object() for _ in range(count))
    calls = []
    renderer = SimpleNamespace(
        assign_semantic_identity=lambda items, identity: calls.append(
            (items, identity)
        )
    )

    result = _assign_polar_declination_tick_semantics(renderer, artists)

    assert result == artists
    if not artists:
        assert calls == []
        return

    assert len(calls) == 1
    assigned, identity = calls[0]
    assert assigned == artists
    assert identity.semantic_path == (
        "sky",
        "grids",
        "equatorial",
        "lines",
        "declination_tick_marks",
    )
    assert identity.display_name == "Declination tick marks"
    assert identity.style_role == "equatorial_grid_lines"
    assert identity.edit_policy.value == "style"
