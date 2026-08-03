"""Visual verification of independent object and stellar legends."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.legend_handler import HandlerPatch
from matplotlib.patches import Ellipse

from wenu import (
    StellarMagnitudeLegendStyle,
    draw_styled_stellar_magnitude_legend,
)
from wenu.rendering.preparation import magnitude_sizes


OUTPUT = Path("output/stellar-magnitude-legend")


class Viewport:
    x_min = -1.0
    x_max = 1.0
    y_min = -0.65
    y_max = 0.65


def _legend_ellipse(
    legend,
    orig_handle,
    xdescent,
    ydescent,
    width,
    height,
    fontsize,
):
    """Create the canonical filled elliptical galaxy legend handle."""
    return Ellipse(
        (xdescent + width / 2.0, ydescent + height / 2.0),
        width=width,
        height=height * 0.55,
        facecolor=orig_handle.get_facecolor(),
        edgecolor=orig_handle.get_edgecolor(),
        linewidth=orig_handle.get_linewidth(),
        alpha=orig_handle.get_alpha(),
    )


def draw_reference(filename=None, *, dpi=200):
    """Draw a compact chart reference with two separate legends."""
    magnitudes = np.asarray(
        [-1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    )
    # Leave the upper-left legend area unobstructed.  In the earlier
    # reference the plotted -1 magnitude star touched the legend frame
    # and could be mistaken for an overlapping legend marker.
    x = np.linspace(-0.55, 0.82, magnitudes.size)
    y = 0.16 * np.sin(
        np.linspace(0.0, 2.0 * np.pi, magnitudes.size)
    )
    area_scale = 2.0

    spherical = SimpleNamespace(
        metadata={"magnitude": magnitudes}
    )
    projected = SimpleNamespace(x=x, y=y)

    figure, ax = plt.subplots(figsize=(9.0, 5.5))
    figure.patch.set_facecolor("white")
    ax.set_facecolor("#eef3f5")
    ax.set_xlim(Viewport.x_min, Viewport.x_max)
    ax.set_ylim(Viewport.y_min, Viewport.y_max)
    ax.set_aspect("equal")

    ax.scatter(
        x,
        y,
        s=magnitude_sizes(magnitudes) * area_scale,
        c="black",
        linewidths=0,
        zorder=10,
    )
    for px, py, magnitude in zip(x, y, magnitudes):
        ax.text(
            px,
            py - 0.10,
            f"{int(magnitude):+d}"
            if magnitude < 0
            else str(int(magnitude)),
            ha="center",
            va="top",
            fontsize=8,
            color="#555555",
        )

    galaxy = Ellipse(
        (0.0, -0.35),
        width=0.18,
        height=0.08,
        facecolor="#b33b32",
        edgecolor="#7d211c",
        alpha=0.65,
        label="Galaxy",
    )
    ax.add_patch(galaxy)
    object_legend = ax.legend(
        handles=[galaxy],
        title="Objects",
        loc="upper right",
        frameon=True,
        handler_map={
            Ellipse: HandlerPatch(patch_func=_legend_ellipse),
        },
    )

    result = draw_styled_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        Viewport(),
        effective_limit=5.0,
        area_scale=area_scale,
        color="black",
        legend_style=StellarMagnitudeLegendStyle(
            location="upper left",
            title="Stars",
            font_size=9,
            title_font_size=10,
        ),
    )

    ax.set_title("Independent chart legends")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(
        0.0,
        0.48,
        "The legend markers use the same areas as the plotted stars",
        ha="center",
        fontsize=10,
        color="#555555",
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
    return figure, ax, object_legend, result


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / "stellar-magnitude-legend.png"
    figure, _, _, _ = draw_reference(destination)
    plt.close(figure)
    print(destination)


if __name__ == "__main__":
    main()
