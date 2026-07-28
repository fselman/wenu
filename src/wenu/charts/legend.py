"""Configurable informational legends for static sky charts."""

from __future__ import annotations

from astropy import units as u
from astropy.coordinates import FK5, SkyCoord
from astropy.time import Time
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


def draw_chart_legend(
    ax,
    chart,
    sky,
    style,
    *,
    context_lines=None,
):
    """Draw the symbol key, chart center, and optional context lines."""
    config = style.legend
    if not config.visible:
        return None

    deep = style.deep_sky
    iso = style.isophotes
    handles = []
    if getattr(sky, "open_clusters", None) is not None:
        handles.append(Line2D([], [], color=deep.open_cluster_color,
                              marker="o", fillstyle="none",
                              linestyle="None", label="Open cluster"))
    if getattr(sky, "globular_clusters", None) is not None:
        handles.append(Line2D([], [], color=deep.globular_cluster_color,
                              marker="o", linestyle="None",
                              label="Globular cluster"))
    if getattr(sky, "planetary_nebulae", None) is not None:
        handles.append(Line2D([], [], color=deep.planetary_nebula_color,
                              marker="+", linestyle="None",
                              label="Planetary nebula"))
    if getattr(sky, "supernova_remnants", None) is not None:
        handles.append(Line2D([], [], color=deep.supernova_remnant_color,
                              marker="o", fillstyle="none",
                              linestyle="None", label="Supernova remnant"))
    if getattr(sky, "galaxies", None) is not None:
        handles.append(Patch(facecolor=deep.galaxy_face_color or "none",
                             edgecolor=deep.galaxy_edge_color,
                             label="Galaxy"))
    if getattr(sky, "milky_way_isophotes", None) is not None:
        handles.append(Patch(facecolor=iso.milky_way_color,
                             edgecolor=iso.milky_way_contour_color or "none",
                             alpha=iso.milky_way_alpha,
                             label="Milky Way"))

    horizontal = SkyCoord(
        az=float(chart.center_az_deg) * u.deg,
        alt=float(chart.center_alt_deg) * u.deg,
        frame=sky.observer.altaz_frame,
    )
    center = horizontal.transform_to(FK5(equinox=Time("J2000")))
    ra = center.ra.to_string(unit=u.hour, sep="hms", precision=0)
    dec = center.dec.to_string(
        unit=u.deg,
        sep="°′″",
        precision=0,
        alwayssign=True,
    )
    title_lines = [
        f"Center: RA {ra}, Dec {dec}",
        "Equatorial grid: FK5, J2000.0",
    ]
    if context_lines is not None:
        title_lines.extend(str(line) for line in context_lines)
    title = "\n".join(title_lines)
    legend = ax.legend(
        handles=handles,
        loc=config.location,
        fontsize=config.fontsize,
        title=title,
        title_fontsize=config.title_fontsize,
        frameon=config.frame,
        facecolor=config.facecolor,
        edgecolor=config.edgecolor,
        framealpha=config.alpha,
        ncols=config.columns,
    )
    legend.set_zorder(100)
    return legend
