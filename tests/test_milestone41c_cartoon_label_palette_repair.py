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


def test_presentation_uses_brighter_ocean_blue():
    style = cartoon_chart_style("presentation")
    assert style.canvas.sky_color == "#1677A6"
    assert style.grids.constellation_line_color == "#FFE066"
    assert style.grids.constellation_label_color == "#FFF0A6"


def test_print_remains_white_for_paper():
    style = cartoon_chart_style("print")
    assert style.canvas.sky_color == "white"
    assert style.stars.color == "#111111"


def test_cartoon_labels_receive_clearance_and_matching_halo():
    sky = fake_sky()
    style = cartoon_chart_style("presentation")
    render = style.layer_options(sky)[sky.constellation_labels]["render"]
    assert render["label_offset"] == (0.18, 0.14)
    assert render["label_style"]["ha"] == "left"
    assert render["label_style"]["va"] == "bottom"
    bbox = render["label_style"]["bbox"]
    assert bbox["facecolor"] == "#1677A6"
    assert bbox["edgecolor"] == "none"
    assert bbox["alpha"] == 0.78


def test_label_clearance_is_configurable():
    style = cartoon_chart_style("print")
    assert style.constellation_label_offset == (0.18, 0.14)
    assert style.constellation_label_halo_alpha == 0.78
