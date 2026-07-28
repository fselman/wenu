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


def test_cartoon_labels_move_clear_of_constellation_figures():
    sky = fake_sky()
    style = cartoon_chart_style("presentation")
    render = style.layer_options(sky)[sky.constellation_labels]["render"]
    assert render["label_offset"] == (0.18, 0.14)
    assert render["label_style"]["ha"] == "left"
    assert render["label_style"]["va"] == "bottom"


def test_cartoon_label_clearance_is_part_of_reusable_style():
    printed = cartoon_chart_style("print")
    presented = cartoon_chart_style("presentation")
    assert printed.constellation_label_offset == (0.18, 0.14)
    assert presented.constellation_label_offset == (0.18, 0.14)


def test_presentation_palette_remains_unchanged():
    style = cartoon_chart_style("presentation")
    assert style.canvas.sky_color == "#1677A6"
    assert style.canvas.foreground_color == "#F7FBFD"
    assert style.grids.constellation_line_color == "#FFE066"
    assert style.grids.constellation_label_color == "#FFF0A6"
