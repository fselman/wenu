"""JSON-driven atlas review specimen; not the future atlas CLI.

Read an already resolved band JSON. Canonical Wenu polar geometry,
MatplotlibRenderer and ExportOptions own projection, clipping, drawing and
export. Optional native catalogue layers use the canonical sky pipeline.
Placement is never invoked by the plotter.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from dataclasses import replace
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox, TransformedBbox

from wenu.atlas_design import AtlasBandTiling
from wenu.charts.polar_planisphere import PolarPlanisphereChart
from wenu.charts.regional import ExportOptions
from wenu.geometry.projected import ProjectedCurve, ProjectedPoints, ProjectedPolygon
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.sky.realization import NATIVE_ICRS_SPEC
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.charts.composition import compose_chart
from wenu.charts.detail import DetailOverrides


def index_sky(star_magnitude_limit):
    """Load existing catalogue owners once, without an observer or ephemeris."""
    sky = CelestialSphere(None)
    sky.add_milky_way_isophotes()
    sky.add_stars(magnitude_limit=star_magnitude_limit)
    sky.add_constellations()
    return sky


def composed_axes(figure, overview):
    """Same-scale disks, with their inward equatorial points coincident."""
    north = overview_face(overview, "north")
    radius = north.boundary_radius
    equator_radius = north.projection.projected_radius(90)
    # Equal square panels overlap by the excess cap beyond the equator.
    # Sky-band width and this physical lens are distinct quantities.
    ratio = equator_radius / radius
    panel = min(0.94 / (1 + ratio), 0.70 * figure.get_figheight() / figure.get_figwidth())
    height = panel * figure.get_figwidth() / figure.get_figheight()
    bottom = 0.135 + (0.70 - height) / 2
    left = (1 - panel * (1 + ratio)) / 2
    axes = tuple(figure.add_axes((x, bottom, panel, height))
                 for x in (left, left + panel * ratio))
    return axes


def _join_faces(figure, axes, atlas):
    """Bisect the paper lens; retain both full contours as assembly guides.

    Each own hemisphere is entirely on its assigned side of the join, so
    clipping the lens does not remove sky coverage. This is a two-projection
    index, not pointwise registration of the whole common sky band.
    """
    for ax, pole in zip(axes, ("north", "south"), strict=True):
        # Keep this in figure coordinates: savefig changes DPI. A fixed
        # display-pixel Bbox would silently clip different sky on export.
        clip = TransformedBbox(Bbox.from_extents(
            0 if pole == "north" else 0.5, 0,
            0.5 if pole == "north" else 1, 1,
        ), figure.transFigure)
        for artist in (*ax.lines, *ax.patches, *ax.collections, *ax.texts):
            artist.set_clip_box(clip)
            artist.set_clip_on(True)
        boundary = overview_face(atlas.geometry.overview, pole).boundary
        figure.add_artist(Line2D(boundary.x, boundary.y, transform=ax.transData,
                                color="#527089", linewidth=0.65, zorder=20))


def overview_face(overview, pole):
    """Put the join meridian on the inward horizontal radius of each face."""
    north = pole == "north"
    return PolarPlanisphereChart(
        pole=pole, projection_name="stereographic", flip_ew=False,
        limiting_declination_deg=(overview.north_limit_dec_deg if north
                                  else overview.south_limit_dec_deg),
        position_angle_deg=(1 if north else -1) * (overview.join_ra_deg - 90),
    )


def visible_regions(atlas, face):
    """Exact primary-sector/cap intersections with a polar view's latitude cap."""
    by_id = {sheet.sheet_id: sheet for sheet in atlas.geometry.sheets}
    for band in atlas.bands:
        lower = max(band.dec_min_deg, face.limiting_declination_deg
                    if face.pole == "north" else -90)
        upper = min(band.dec_max_deg, face.limiting_declination_deg
                    if face.pole == "south" else 90)
        if lower >= upper:
            continue
        for index, identifier in enumerate(band.sheet_ids):
            ra0 = band.ra_origin_deg + index * band.sector_width_deg
            yield by_id[identifier], ra0, ra0 + band.sector_width_deg, lower, upper


def _samples(start, stop):
    return np.linspace(start, stop, max(2, int(np.ceil(abs(stop - start))) + 1))


def primary_outline(face, ra0, ra1, lower, upper):
    """Sample only for display; JSON's analytic validation remains authoritative."""
    ra_edge, dec_edge = _samples(ra0, ra1), _samples(lower, upper)
    if ra1 - ra0 == 360 and (lower == -90 or upper == 90):
        # A polar cap has one circular edge; drawing a sector via its pole
        # would introduce a false radial border.
        dec = lower if upper == 90 else upper
        x, y = face.projection.project_spherical(ra_edge, np.full(len(ra_edge), dec))
        return ProjectedPolygon(x, y)
    ra = np.concatenate((ra_edge, np.full(len(dec_edge), ra1),
                         ra_edge[::-1], np.full(len(dec_edge), ra0)))
    dec = np.concatenate((np.full(len(ra_edge), lower), dec_edge,
                          np.full(len(ra_edge), upper), dec_edge[::-1]))
    x, y = face.projection.project_spherical(ra, dec)
    return ProjectedPolygon(x, y)


def _draw_face(ax, atlas, face, *, footprints, sky=None, star_magnitude_limit=5.5):
    renderer = MatplotlibRenderer(ax)
    renderer.apply_viewport(face.viewport)
    renderer.set_clip_boundary(face.boundary, style={"edgecolor": "#284b63", "facecolor": "none", "linewidth": 1})
    renderer.set_axes_frame_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    if sky is not None:
        composition = compose_chart(
            face, style="atlas", mode="print",
            detail_overrides=DetailOverrides(
                star_magnitude_limit=star_magnitude_limit,
                enabled_layers=frozenset({"stars", "constellation_lines",
                                          "constellation_labels", "milky_way"}),
                constellation_star_mode="none",
            ),
        )
        style = replace(composition.style,
                        canvas=replace(composition.style.canvas, sky_color="none"))
        options = composition.layer_options(sky).layer_options
        face.render(sky, renderer, style=style, layer_options=options,
                    realization_context=LayerRealizationContext(NATIVE_ICRS_SPEC),
                    boundary_style={"edgecolor": "#284b63", "facecolor": "none", "linewidth": 1})
    highlight = atlas.primary_sheet_id(atlas.seed_ra_deg, 0)
    label_x, label_y, labels, ids = [], [], [], []
    for sheet, ra0, ra1, lower, upper in visible_regions(atlas, face):
        selected = sheet.sheet_id == highlight
        renderer.draw(primary_outline(face, ra0, ra1, lower, upper), style={
            "facecolor": "none" if sky is not None else "#d0e9d8" if selected else
                         ("#edf3f8" if sheet.number % 2 else "#ffffff"),
            "edgecolor": "#276749" if selected else "#527089",
            "linewidth": 1.2 if selected else 0.45, "zorder": 1,
        })
        # Thin rim fragments remain visible, but their number is placed only
        # where the actual centre is in this view. Every centre is in at least
        # one face; shared-band centres retain the same number in both.
        if lower <= sheet.center_dec_deg <= upper:
            x, y = face.projection.project_spherical(sheet.center_ra_deg, sheet.center_dec_deg)
            label_x.append(float(x))
            label_y.append(float(y))
            labels.append(str(sheet.number))
            ids.append(sheet.sheet_id)
    renderer.draw(ProjectedPoints(np.array(label_x), np.array(label_y),
                                 ids=np.array(ids), labels=np.array(labels)),
                  draw_markers=False, draw_labels=True,
                  label_style={"fontsize": 10 if sky is not None else 7,
                               "fontweight": "bold" if sky is not None else "normal",
                               "ha": "center", "va": "center",
                               "color": "#183b56", "zorder": 25,
                               "bbox": {"facecolor": "white", "edgecolor": "none",
                                        "alpha": 0.85, "pad": 0.6}})
    ra = _samples(0, 360)
    for dec in (-atlas.geometry.overview.shared_band_width_deg / 2, 0,
                atlas.geometry.overview.shared_band_width_deg / 2):
        if (face.pole == "north" and dec < face.limiting_declination_deg) or (
                face.pole == "south" and dec > face.limiting_declination_deg):
            continue
        x, y = face.projection.project_spherical(ra, np.full(len(ra), dec))
        renderer.draw(ProjectedCurve(x, y, closed=True), style={
            "color": "#b7791f", "linewidth": 0.8,
            "linestyle": "-" if dec == 0 else "--", "zorder": 3,
        })
    dec = _samples(face.limiting_declination_deg, face.pole_declination_deg)
    x, y = face.projection.project_spherical(np.full(len(dec), atlas.geometry.overview.join_ra_deg), dec)
    renderer.draw(ProjectedCurve(x, y), style={"color": "#b7791f", "linewidth": 0.8, "zorder": 3})
    if footprints:
        for sheet in atlas.geometry.sheets:
            boundary = np.array(sheet.boundary_samples(atlas.geometry.page, samples_per_edge=129))
            boundary = np.vstack((boundary, boundary[0]))
            # Mask the hidden hemisphere before projection to avoid an antipodal
            # chord. The circular renderer clip is the final display boundary.
            visible = boundary[:, 1] >= face.limiting_declination_deg if face.pole == "north" else boundary[:, 1] <= face.limiting_declination_deg
            safe_dec = np.where(visible, boundary[:, 1], np.nan)
            x, y = face.projection.project_spherical(boundary[:, 0], safe_dec)
            renderer.draw(ProjectedCurve(x, y), style={
                "color": "#27815b" if sheet.sheet_id == highlight else "#8b3b65",
                "linewidth": 1.3 if sheet.sheet_id == highlight else 0.35,
                "alpha": 1 if sheet.sheet_id == highlight else 0.4,
                "zorder": 2,
            })
    renderer.finalize_graphics()
    ax.set_title(f"{'Norte' if face.pole == 'north' else 'Sur'} · límite Dec {face.limiting_declination_deg:+g}°",
                 fontsize=11, pad=12, color="#183b56")


def plot_overview(design_path, output_prefix, *, footprints=False, joined=False,
                  astronomy=False, star_magnitude_limit=5.5):
    """Read/revalidate resolved JSON and write versioned PNG, PDF and SVG."""
    atlas = AtlasBandTiling.read_json(design_path)
    if not np.isfinite(star_magnitude_limit) or not 0 < star_magnitude_limit <= 11:
        raise ValueError("star_magnitude_limit must be finite and between 0 and 11.")
    prefix = Path(output_prefix)
    destinations = [prefix.with_suffix(suffix) for suffix in (".png", ".pdf", ".svg")]
    if any(path.exists() for path in destinations):
        raise FileExistsError("Choose a new versioned output prefix; existing products are preserved.")
    sky = index_sky(star_magnitude_limit) if astronomy else None
    figure = plt.figure(figsize=(14, 8), facecolor="white")
    if joined:
        axes = composed_axes(figure, atlas.geometry.overview)
    else:
        axes = figure.subplots(1, 2)
        figure.subplots_adjust(left=0.03, right=0.97, top=0.86, bottom=0.13, wspace=0.06)
    for ax in axes:
        ax.set_facecolor("none")
    field = atlas.geometry.sheets[0].field_width_deg
    page = atlas.geometry.page
    paper = "B4" if (page.width_mm, page.height_mm) == (353, 250) else f"{page.width_mm:g} × {page.height_mm:g} mm"
    figure.suptitle(f"Atlas {paper} · campo horizontal {field:g}° · {len(atlas.geometry.sheets)} hojas",
                   fontsize=18, color="#183b56", y=0.965)
    figure.text(0.5, 0.91, f"Áreas principales numeradas · ICRS · solapamiento mínimo {atlas.overlap_deg:g}°",
                ha="center", fontsize=11, color="#527089")
    try:
        for ax, pole in zip(axes, ("north", "south"), strict=True):
            _draw_face(ax, atlas, overview_face(atlas.geometry.overview, pole), footprints=footprints,
                       sky=sky, star_magnitude_limit=star_magnitude_limit)
        if joined:
            _join_faces(figure, axes, atlas)
        highlighted = next(sheet.number for sheet in atlas.geometry.sheets
                           if sheet.sheet_id == atlas.primary_sheet_id(atlas.seed_ra_deg, 0))
        region_hint = " (cerca de Orión)" if atlas.seed_ra_deg == 82.5 else ""
        figure.text(0.5, 0.075, f"Verde: hoja {highlighted}, centro semilla RA {atlas.seed_ra_deg / 15:g} h, Dec 0°{region_hint}.",
                    ha="center", fontsize=10, color="#276749")
        figure.text(0.5, 0.041, f"Ocre: ecuador, límites de banda compartida ±{atlas.geometry.overview.shared_band_width_deg / 2:g}° y meridiano RA {atlas.geometry.overview.join_ra_deg / 15:g} h.",
                    ha="center", fontsize=9, color="#806025")
        content = f"Estrellas hasta magnitud {star_magnitude_limit:g}, constelaciones y Vía Láctea. " if astronomy else "Sin catálogos. "
        layout = "Contornos unidos; banda común con dos proyecciones. " if joined else "Discos separados. "
        figure.text(0.5, 0.012, layout + content +
                    ("Magenta: huellas completas con solapamiento." if footprints else "Los bordes indican propiedad primaria, no la huella completa de cada hoja."),
                    ha="center", fontsize=9, color="#527089")
        options = ExportOptions(dpi=160, bbox_inches=None, facecolor="white",
                                metadata={"Title": prefix.name, "Creator": "Wenu"})
        return tuple(options.save(figure, path) for path in destinations)
    finally:
        plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", type=Path, help="Resolved band-tiling JSON")
    parser.add_argument("output_prefix", type=Path, help="New versioned filename without extension")
    parser.add_argument("--footprints", action="store_true", help="Overlay sampled complete rectangular footprints")
    parser.add_argument("--joined", action="store_true", help="Compose overlapping disk contours at the inward equatorial point")
    parser.add_argument("--astronomy", action="store_true", help="Add native ICRS catalogue stars, constellations and Milky Way")
    parser.add_argument("--star-magnitude-limit", type=float, default=5.5)
    args = parser.parse_args()
    for path in plot_overview(args.design, args.output_prefix, footprints=args.footprints,
                              joined=args.joined, astronomy=args.astronomy,
                              star_magnitude_limit=args.star_magnitude_limit):
        print(path)


if __name__ == "__main__":
    main()
