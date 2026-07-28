from dataclasses import fields

from wenu import CartoonChartStyle
from wenu.charts.detail import CartoonDetailPolicy


def test_cartoon_style_uses_an_original_light_classroom_palette():
    style = CartoonChartStyle()
    assert style.canvas.sky_color == "#fffdf7"
    assert style.canvas.foreground_color == "#172238"
    assert style.stars.color == "#172238"
    assert style.grids.constellation_line_color == "#304f78"


def test_constellation_structure_is_visually_prominent():
    style = CartoonChartStyle()
    assert style.grids.constellation_linewidth >= 1.0
    assert style.grids.constellation_line_alpha >= 0.9
    assert style.grids.constellation_label_alpha == 1.0
    assert style.canvas.label_fontsize >= 12.0


def test_stellar_classification_overlays_are_off():
    style = CartoonChartStyle()
    assert style.stars.draw_variable_symbols is False
    assert style.stars.draw_multiple_symbols is False


def test_default_cartoon_legend_and_coordinate_labels_are_quiet():
    style = CartoonChartStyle()
    assert style.legend.visible is False
    assert style.grids.draw_coordinate_labels is False


def test_publication_style_receives_cartoon_visual_values():
    composed = CartoonChartStyle()
    publication = composed.as_publication_style()
    assert publication.sky_color == composed.canvas.sky_color
    assert publication.star_color == composed.stars.color
    assert (
        publication.constellation_line_color
        == composed.grids.constellation_line_color
    )
    assert (
        publication.constellation_linewidth
        == composed.grids.constellation_linewidth
    )
    assert publication.draw_variable_star_symbols is False
    assert publication.draw_multiple_star_symbols is False


def test_visual_style_does_not_own_chart_type_mode_or_content_policy():
    names = {item.name for item in fields(CartoonChartStyle)}
    forbidden = {
        "projection",
        "viewport",
        "angular_width_deg",
        "width_inches",
        "height_inches",
        "dpi",
        "enabled_layers",
        "magnitude_limit",
        "constellation_star_mode",
        "extra_star_ids",
    }
    assert names.isdisjoint(forbidden)


def test_cartoon_content_policy_remains_a_separate_object():
    style = CartoonChartStyle()
    detail = CartoonDetailPolicy().resolve(object(), object())
    assert style.grids.constellation_linewidth > 0
    assert detail.enabled_layers == frozenset(
        {"stars", "constellation_lines", "constellation_labels"}
    )
    assert detail.constellation_star_mode == "selected"
