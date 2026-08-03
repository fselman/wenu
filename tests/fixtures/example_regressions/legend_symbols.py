"""Render a visual comparison of chart and legend symbols."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle

from wenu import AtlasChartStyle, legend_symbol_descriptors
from wenu.charts.legend import _legend_handle, _legend_handler_map
from wenu.rendering.symbols import DEFAULT_SYMBOLS


OUTPUT = Path("output/legend-symbols")


def active_sky():
    """Return a minimal registry with every legend-bearing layer active."""
    active = object()
    return SimpleNamespace(
        open_clusters=active,
        globular_clusters=active,
        planetary_nebulae=active,
        supernova_remnants=active,
        galaxies=active,
        milky_way_isophotes=active,
    )


def chart_marker(descriptor):
    """Resolve the marker used by the corresponding chart layer."""
    if descriptor.symbol_name is not None:
        return DEFAULT_SYMBOLS[descriptor.symbol_name]
    return descriptor.marker


def draw_reference(filename=None, *, dpi=200):
    """Draw chart symbols beside their automatically generated legend."""
    style = AtlasChartStyle()
    publication = style.as_publication_style()
    descriptors = legend_symbol_descriptors(active_sky(), style)

    figure, ax = plt.subplots(figsize=(10.0, 6.0))
    figure.patch.set_facecolor("white")
    ax.set_facecolor(publication.sky_color)
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(-0.75, len(descriptors) - 0.25)
    ax.invert_yaxis()
    ax.axis("off")

    for row, descriptor in enumerate(descriptors):
        if descriptor.key == "galaxy":
            patch = Ellipse(
                (1.45, row),
                width=0.9,
                height=0.38,
                facecolor=descriptor.face_color,
                edgecolor=descriptor.edge_color,
                alpha=descriptor.alpha,
                linewidth=descriptor.linewidth,
            )
            ax.add_patch(patch)
        elif descriptor.kind == "patch":
            patch = Rectangle(
                (1.0, row - 0.22),
                0.9,
                0.44,
                facecolor=descriptor.face_color,
                edgecolor=descriptor.edge_color,
                alpha=descriptor.alpha,
                linewidth=descriptor.linewidth,
            )
            ax.add_patch(patch)
        else:
            ax.plot(
                [1.45],
                [row],
                marker=chart_marker(descriptor),
                markersize=13.0,
                markerfacecolor=descriptor.face_color,
                markeredgecolor=descriptor.edge_color,
                markeredgewidth=descriptor.linewidth,
                linestyle="None",
                alpha=descriptor.alpha,
            )
        ax.text(
            2.25,
            row,
            descriptor.label,
            va="center",
            color=publication.foreground_color,
            fontsize=11,
        )

    handles = [_legend_handle(item) for item in descriptors]
    legend = ax.legend(
        handles=handles,
        handler_map=_legend_handler_map(),
        title="Generated chart legend",
        loc="center right",
        frameon=True,
        fontsize=10,
        title_fontsize=11,
    )
    legend.set_zorder(100)
    ax.text(
        1.0,
        -0.55,
        "Symbols drawn by chart layers",
        color=publication.foreground_color,
        fontsize=12,
        weight="bold",
    )
    ax.set_title(
        "Canonical chart and legend symbols",
        color=publication.foreground_color,
        fontsize=15,
        pad=12,
    )

    if filename is not None:
        destination = Path(filename)
        destination.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(
            destination,
            dpi=dpi,
            bbox_inches="tight",
            facecolor=figure.get_facecolor(),
        )
    return figure, ax, descriptors, handles


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / "canonical-legend-symbols.png"
    figure, _, _, _ = draw_reference(destination)
    plt.close(figure)
    print(destination)


if __name__ == "__main__":
    main()
