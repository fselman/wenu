from inspect import signature
from types import SimpleNamespace

import pytest

from wenu import cartoon_chart_style, compose_cartoon_chart
from wenu.charts.label_placement import (
    LABEL_POSITION_VECTORS,
    resolve_constellation_label_offsets,
)


class HashableLayer:
    pass


def fake_sky():
    labels = HashableLayer()
    return SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_clouds=None,
        galaxies=None,
        supernova_remnants=None,
        globular_clusters=None,
        planetary_nebulae=None,
        open_clusters=None,
        constellation_lines=None,
        constellation_labels=labels,
        constellation_boundaries=None,
        coordinate_grids=(),
        points=None,
        layers=(labels,),
    )


def test_nine_position_vocabulary_is_complete():
    assert set(LABEL_POSITION_VECTORS) == {
        "c", "ul", "u", "ur", "cl", "cr", "ll", "lc", "lr"
    }


def test_unspecified_labels_default_to_center():
    resolved = resolve_constellation_label_offsets(
        {"Cyg": "cl"},
        clearance=(0.2, 0.1),
    )
    assert resolved["__default__"] == (0.0, 0.0)
    assert resolved["Cyg"] == pytest.approx((-0.2, 0.0))


def test_manual_offset_is_added_after_discrete_position():
    resolved = resolve_constellation_label_offsets(
        {"Lyr": "ur"},
        {"Lyr": (-0.03, 0.02)},
        clearance=(0.2, 0.1),
    )
    assert resolved["Lyr"] == pytest.approx((0.17, 0.12))


def test_unknown_position_is_rejected():
    with pytest.raises(ValueError, match="sideways"):
        resolve_constellation_label_offsets({"Lyr": "sideways"})


def test_cartoon_style_emits_resolved_per_label_offsets():
    sky = fake_sky()
    style = cartoon_chart_style(
        "print",
        constellation_label_positions={
            "Cyg": "cl",
            "Lyr": "ur",
        },
        constellation_label_offsets={
            "Lyr": (-0.03, 0.02),
        },
        constellation_label_clearance=(0.2, 0.1),
    ).as_publication_style()
    render = style.layer_options(
        sky
    )[sky.constellation_labels]["render"]
    assert render["label_offset"]["__default__"] == (0.0, 0.0)
    assert render["label_offset"]["Cyg"] == pytest.approx((-0.2, 0.0))
    assert render["label_offset"]["Lyr"] == pytest.approx((0.17, 0.12))
    assert render["label_style"]["ha"] == "center"
    assert render["label_style"]["va"] == "center"


def test_composition_exposes_position_and_clearance_controls():
    parameters = signature(compose_cartoon_chart).parameters
    assert "constellation_label_positions" in parameters
    assert "constellation_label_offsets" in parameters
    assert "constellation_label_clearance" in parameters


def test_legacy_manual_offset_calls_remain_unchanged():
    style = cartoon_chart_style(
        "print",
        constellation_label_offsets={"Lyr": (0.07, 0.05)},
    ).as_publication_style()
    assert style.constellation_label_offsets == {
        "Lyr": (0.07, 0.05)
    }
