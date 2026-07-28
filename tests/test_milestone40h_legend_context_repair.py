from inspect import signature
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import AtlasChartStyle, draw_chart_legend


def empty_sky():
    return SimpleNamespace(
        open_clusters=None,
        globular_clusters=None,
        planetary_nebulae=None,
        supernova_remnants=None,
        galaxies=None,
        milky_way_isophotes=None,
    )


def test_context_lines_parameter_is_preserved():
    assert "context_lines" in signature(draw_chart_legend).parameters


def test_context_lines_follow_resolved_or_custom_metadata():
    figure, ax = plt.subplots()
    legend = draw_chart_legend(
        ax,
        object(),
        empty_sky(),
        AtlasChartStyle(),
        title="Coordinates",
        context_lines=(
            "La Ligua, Chile",
            "2026-08-15 21:00 CLT",
        ),
    )
    assert legend.get_title().get_text().splitlines() == [
        "Coordinates",
        "La Ligua, Chile",
        "2026-08-15 21:00 CLT",
    ]
    plt.close(figure)
