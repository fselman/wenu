import ast
from dataclasses import fields, replace
from pathlib import Path

from wenu import (
    CartoonChartPreset,
    CartoonChartStyle,
    CartoonDetailPolicy,
    PresentationMode,
    RegionalChart,
    compose_chart,
)


def regional_chart():
    return RegionalChart(
        center_alt_deg=45.0,
        center_az_deg=190.0,
        field_width_deg=45.0,
        field_height_deg=30.0,
    )


def test_default_preset_bundles_only_cartoon_style_and_detail():
    preset = CartoonChartPreset()
    assert isinstance(preset.style, CartoonChartStyle)
    assert isinstance(preset.detail, CartoonDetailPolicy)
    assert preset.components() == (preset.style, preset.detail)


def test_preset_expansion_matches_explicit_composition():
    chart = regional_chart()
    mode = PresentationMode(width_inches=10.0)
    preset = CartoonChartPreset()
    convenient = preset.compose(chart, mode=mode)
    explicit = compose_chart(
        chart,
        style=preset.style,
        mode=mode,
        detail=preset.detail,
    )
    assert convenient == explicit


def test_chart_type_and_mode_remain_independently_replaceable():
    chart = regional_chart()
    preset = CartoonChartPreset()
    narrow = preset.compose(
        chart,
        mode=PresentationMode(width_inches=8.0),
    )
    wide = preset.compose(
        chart,
        mode=PresentationMode(width_inches=14.0),
    )
    assert narrow.context == wide.context == chart.chart_context
    assert narrow.style is wide.style is preset.style
    assert narrow.mode.width_inches == 8.0
    assert wide.mode.width_inches == 14.0


def test_preset_accepts_custom_style_and_detail_components():
    style = replace(
        CartoonChartStyle(),
        canvas=replace(
            CartoonChartStyle().canvas,
            sky_color="white",
        ),
    )
    detail = CartoonDetailPolicy(
        bright_star_magnitude_limit=2.0,
        extra_star_ids=frozenset({11767}),
    )
    preset = CartoonChartPreset(style=style, detail=detail)
    composition = preset.compose(regional_chart())
    assert composition.style.canvas.sky_color == "white"
    assert composition.detail.star_magnitude_limit == 2.0
    assert composition.detail.extra_star_ids == frozenset({11767})


def test_preset_does_not_own_chart_geometry_or_output_mode():
    names = {item.name for item in fields(CartoonChartPreset)}
    assert names == {"style", "detail"}


def imported_modules(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    return tuple(imported)


def test_cartoon_preset_has_no_render_backend_dependency():
    import wenu.charts.cartoon as module

    imports = imported_modules(Path(module.__file__))
    assert "matplotlib" not in imports
    assert not any(name.startswith("matplotlib.") for name in imports)
