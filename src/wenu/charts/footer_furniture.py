"""Matplotlib-facing rendering of canonical figure-margin footers."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version


@dataclass(frozen=True)
class ChartFooterRendering:
    """Inspectable artists and resolved text for one chart footer."""

    copyright_text: str | None
    application_text: str | None
    artists: tuple[object, ...]


def installed_wenu_version() -> str:
    """Return installed package metadata without hard-coding a release."""
    try:
        return version("wenu")
    except PackageNotFoundError:
        return "0+unknown"


def resolved_footer_text(footer, *, package_version=None):
    """Resolve independent left and right footer strings."""
    application = None
    if footer.application:
        application = footer.application_name
        if footer.include_version:
            resolved_version = (
                installed_wenu_version()
                if package_version is None
                else str(package_version)
            )
            application = f"{application} {resolved_version}"
    return footer.copyright, application


def draw_chart_footer(
    renderer,
    footer,
    mode,
    *,
    color="black",
    package_version=None,
    layout=None,
) -> ChartFooterRendering | None:
    """Draw requested credits below the axes in the figure margin."""
    copyright_text, application_text = resolved_footer_text(
        footer,
        package_version=package_version,
    )
    if copyright_text is None and application_text is None:
        return None

    ax = renderer.ax
    figure = ax.figure
    position = ax.get_position()
    bottom = max(float(position.y0), 0.065)
    top = float(position.y1)
    if bottom < top:
        ax.set_position(
            [position.x0, bottom, position.width, top - bottom]
        )

    if layout is None:
        from wenu.configuration import (
            packaged_furniture_product_export_defaults,
        )

        layout = packaged_furniture_product_export_defaults().footer_layout
    font_size = layout.font_size * float(
        getattr(mode, "font_scale", 1.0)
    )
    common = dict(
        y=layout.y,
        fontsize=font_size,
        color=str(color),
        va="bottom",
    )
    artists = []
    if copyright_text is not None:
        artists.append(
            figure.text(
                layout.left_x,
                s=copyright_text,
                ha="left",
                **common,
            )
        )
    if application_text is not None:
        artists.append(
            figure.text(
                layout.right_x,
                s=application_text,
                ha="right",
                **common,
            )
        )
    return ChartFooterRendering(
        copyright_text=copyright_text,
        application_text=application_text,
        artists=tuple(artists),
    )
