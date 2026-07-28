from types import SimpleNamespace

from wenu import cartoon_chart_style


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


def test_label_placement_survives_publication_style_conversion():
    composed = cartoon_chart_style("presentation")
    publication = composed.as_publication_style()
    assert publication.constellation_label_offset == (0.18, 0.14)
    assert publication.constellation_label_ha == "left"
    assert publication.constellation_label_va == "bottom"


def test_publication_layer_options_use_composed_label_placement():
    sky = fake_sky()
    publication = cartoon_chart_style(
        "presentation"
    ).as_publication_style()
    render = publication.layer_options(
        sky
    )[sky.constellation_labels]["render"]
    assert render["label_offset"]["__default__"] == (0.18, 0.14)
    assert render["label_style"]["ha"] == "left"
    assert render["label_style"]["va"] == "bottom"


def test_print_and_presentation_share_label_clearance():
    printed = cartoon_chart_style("print").as_publication_style()
    presented = cartoon_chart_style(
        "presentation"
    ).as_publication_style()
    assert printed.constellation_label_offset == (0.18, 0.14)
    assert (
        printed.constellation_label_offset
        == presented.constellation_label_offset
    )
