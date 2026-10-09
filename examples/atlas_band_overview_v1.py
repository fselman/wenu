"""Geometry-only atlas review specimen; not the future atlas CLI.

Read an already resolved band JSON. Canonical Wenu polar geometry,
MatplotlibRenderer and ExportOptions own projection, clipping, drawing and
export. No catalogue, observer or placement is invoked by the plotter.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from wenu.atlas_design import AtlasBandTiling
from wenu.charts.polar_planisphere import PolarPlanisphereChart
from wenu.charts.regional import ExportOptions
from wenu.geometry.projected import ProjectedCurve, ProjectedPoints, ProjectedPolygon
from wenu.rendering.matplotlib import MatplotlibRenderer


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


def _draw_face(ax, atlas, face, *, footprints):
    renderer = MatplotlibRenderer(ax)
    renderer.apply_viewport(face.viewport)
    renderer.set_clip_boundary(face.boundary, style={"color": "#284b63", "linewidth": 1})
    renderer.set_axes_frame_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    highlight = atlas.primary_sheet_id(atlas.seed_ra_deg, 0)
    label_x, label_y, labels, ids = [], [], [], []
    for sheet, ra0, ra1, lower, upper in visible_regions(atlas, face):
        selected = sheet.sheet_id == highlight
        renderer.draw(primary_outline(face, ra0, ra1, lower, upper), style={
            "facecolor": "#d0e9d8" if selected else
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
                  label_style={"fontsize": 7, "ha": "center", "va": "center",
                               "color": "#183b56", "zorder": 4})
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


def plot_overview(design_path, output_prefix, *, footprints=False):
    """Read/revalidate resolved JSON and write versioned PNG, PDF and SVG."""
    atlas = AtlasBandTiling.read_json(design_path)
    prefix = Path(output_prefix)
    destinations = [prefix.with_suffix(suffix) for suffix in (".png", ".pdf", ".svg")]
    if any(path.exists() for path in destinations):
        raise FileExistsError("Choose a new versioned output prefix; existing products are preserved.")
    figure, axes = plt.subplots(1, 2, figsize=(14, 8), facecolor="white")
    figure.subplots_adjust(left=0.03, right=0.97, top=0.86, bottom=0.13, wspace=0.06)
    field = atlas.geometry.sheets[0].field_width_deg
    page = atlas.geometry.page
    paper = "B4" if (page.width_mm, page.height_mm) == (353, 250) else f"{page.width_mm:g} × {page.height_mm:g} mm"
    figure.suptitle(f"Atlas {paper} · campo horizontal {field:g}° · {len(atlas.geometry.sheets)} hojas",
                   fontsize=18, color="#183b56", y=0.965)
    figure.text(0.5, 0.91, f"Áreas principales numeradas · ICRS · solapamiento mínimo {atlas.overlap_deg:g}°",
                ha="center", fontsize=11, color="#527089")
    try:
        for ax, pole in zip(axes, ("north", "south"), strict=True):
            _draw_face(ax, atlas, overview_face(atlas.geometry.overview, pole), footprints=footprints)
        highlighted = next(sheet.number for sheet in atlas.geometry.sheets
                           if sheet.sheet_id == atlas.primary_sheet_id(atlas.seed_ra_deg, 0))
        region_hint = " (cerca de Orión)" if atlas.seed_ra_deg == 82.5 else ""
        figure.text(0.5, 0.075, f"Verde: hoja {highlighted}, centro semilla RA {atlas.seed_ra_deg / 15:g} h, Dec 0°{region_hint}.",
                    ha="center", fontsize=10, color="#276749")
        figure.text(0.5, 0.041, f"Ocre: ecuador, límites de banda compartida ±{atlas.geometry.overview.shared_band_width_deg / 2:g}° y meridiano RA {atlas.geometry.overview.join_ra_deg / 15:g} h.",
                    ha="center", fontsize=9, color="#806025")
        figure.text(0.5, 0.012, "Prototipo geométrico: discos separados; sin catálogos. " +
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
    args = parser.parse_args()
    for path in plot_overview(args.design, args.output_prefix, footprints=args.footprints):
        print(path)


if __name__ == "__main__":
    main()
