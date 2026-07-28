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


def test_legacy_mode_retains_left_bottom_alignment():
    publication = cartoon_chart_style(
        "presentation"
    ).as_publication_style()
    assert publication.constellation_label_ha == "left"
    assert publication.constellation_label_va == "bottom"


def test_discrete_position_mode_uses_center_alignment():
    sky = fake_sky()
    publication = cartoon_chart_style(
        "presentation",
        constellation_label_positions={"Lyr": "ur"},
    ).as_publication_style()
    render = publication.layer_options(
        sky
    )[sky.constellation_labels]["render"]
    assert render["label_style"]["ha"] == "center"
    assert render["label_style"]["va"] == "center"
