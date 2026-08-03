import pytest

from wenu import (
    CARTOON_PRESENTATION_PALETTE,
    CARTOON_PRINT_PALETTE,
    CartoonDetailPolicy,
    PresentationMode,
    PrintMode,
    cartoon_chart_style,
)


def test_print_cartoon_uses_white_paper_palette():
    style = cartoon_chart_style("print")
    assert style.canvas.sky_color == "white"
    assert style.stars.color == CARTOON_PRINT_PALETTE.stars
    assert (
        style.grids.constellation_line_color
        == CARTOON_PRINT_PALETTE.constellation_lines
    )
    assert not style.stars.draw_variable_symbols
    assert not style.stars.draw_multiple_symbols


def test_presentation_uses_agreed_projector_palette():
    style = cartoon_chart_style("presentation")
    assert style.canvas.sky_color == "#1677A6"
    assert style.stars.color == "#FFE066"
    assert style.grids.constellation_line_color == "#FFE066"
    assert style.grids.constellation_label_color == "#FFE066"
    assert style.canvas.foreground_color == "#FFE066"
    assert style.canvas.footer_color == "#FFFFFF"
    assert style.isophotes.milky_way_color == "#FFE066"


def test_presentation_contains_no_red_primary_chart_colors():
    palette = CARTOON_PRESENTATION_PALETTE
    values = tuple(vars(palette).values())
    assert "#ff0000" not in {value.lower() for value in values}
    assert "red" not in {value.lower() for value in values}


def test_presentation_increases_screen_readability():
    printed = cartoon_chart_style(PrintMode())
    presented = cartoon_chart_style(PresentationMode())
    assert (
        presented.canvas.label_fontsize
        > printed.canvas.label_fontsize
    )
    assert (
        presented.grids.constellation_linewidth
        > printed.grids.constellation_linewidth
    )
    assert presented.stars.area_scale > printed.stars.area_scale


def test_mode_selection_rejects_unknown_names():
    with pytest.raises(ValueError, match="print or presentation"):
        cartoon_chart_style("night")


def test_visual_mode_does_not_resolve_content():
    detail = CartoonDetailPolicy().resolve(object(), object())
    assert detail.enabled_layers == frozenset(
        {"stars", "constellation_lines", "constellation_labels"}
    )
    assert detail.constellation_star_mode == "selected"


def test_publication_styles_preserve_mode_colors():
    presented = cartoon_chart_style("presentation")
    publication = presented.as_publication_style()
    assert publication.sky_color == "#1677A6"
    assert publication.star_color == "#FFE066"
    assert publication.constellation_line_color == "#FFE066"
    assert publication.constellation_label_color == "#FFE066"
