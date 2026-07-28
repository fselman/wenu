from inspect import signature
from types import SimpleNamespace

import matplotlib.pyplot as plt

from wenu import (
    MatplotlibRenderer,
    cartoon_chart_style,
    compose_cartoon_chart,
)
from wenu.geometry.projected import ProjectedPoints


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


def test_manual_offsets_survive_publication_conversion():
    publication = cartoon_chart_style(
        "print",
        constellation_label_offsets={"Lyr": (0.07, 0.05)},
    ).as_publication_style()
    assert publication.constellation_label_offsets == {
        "Lyr": (0.07, 0.05)
    }


def test_label_options_contain_default_and_manual_offsets():
    sky = fake_sky()
    publication = cartoon_chart_style(
        "print",
        constellation_label_offsets={"Lyr": (0.07, 0.05)},
    ).as_publication_style()
    offsets = publication.layer_options(
        sky
    )[sky.constellation_labels]["render"]["label_offset"]
    assert offsets["__default__"] == (0.18, 0.14)
    assert offsets["Lyr"] == (0.07, 0.05)


def test_renderer_resolves_offsets_by_label_identity():
    figure, ax = plt.subplots()
    points = ProjectedPoints(
        x=[1.0, 2.0],
        y=[3.0, 4.0],
        labels=["Lyr", "Cyg"],
    )
    artists = MatplotlibRenderer(ax).draw(
        points,
        style={"s": 0.0},
        draw_labels=True,
        label_offset={
            "__default__": (0.18, 0.14),
            "Lyr": (0.07, 0.05),
        },
    )
    positions = {
        artist.get_text(): artist.get_position()
        for artist in artists
        if hasattr(artist, "get_text")
    }
    assert positions["Lyr"] == (1.07, 3.05)
    assert positions["Cyg"] == (2.18, 4.14)
    plt.close(figure)


def test_cartoon_composition_accepts_manual_offsets():
    assert (
        "constellation_label_offsets"
        in signature(compose_cartoon_chart).parameters
    )
