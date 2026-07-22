"""A small renderer-side helper rather than giving Viewport knowledge of Matplotlib"""

from __future__ import annotations

from wenu.viewport import Viewport


def apply_viewport(
    ax,
    viewport: Viewport,
    *,
    equal_aspect: bool = True,
) -> None:
    """
    Apply projected viewport bounds to a Matplotlib axis.

    Parameters
    ----------
    ax
        Matplotlib axis to configure.

    viewport
        Visible region in projected Cartesian coordinates.

    equal_aspect
        Preserve equal scale in the x and y directions.
    """
    ax.set_xlim(viewport.xlim)
    ax.set_ylim(viewport.ylim)

    if equal_aspect:
        ax.set_aspect(
            "equal",
            adjustable="box",
        )


