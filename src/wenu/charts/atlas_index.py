"""Resolved atlas index presentation through canonical chart/render/export owners.

Read an already resolved band JSON. Canonical Wenu polar geometry,
MatplotlibRenderer and ExportOptions own projection, clipping, drawing and
export. Optional native catalogue layers use the canonical sky pipeline.
Placement is never invoked by the plotter.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, replace
import os
import tempfile

from matplotlib.colors import is_color_like
from wenu.atlas_design import _keys, _number, _integer
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
from wenu.charts.detail import SkyContentSelection


SUPPORTED_INDEX_LAYERS = frozenset({"stars", "constellation_lines",
    "constellation_labels", "milky_way", "magellanic_clouds"})


@dataclass(frozen=True)
class AtlasIndexPresentation:
    """Independent version-1 index presentation; never a geometry request."""

    joined: bool = True
    footprints: bool = False
    width_mm: float = 355.6
    height_mm: float = 203.2
    layers: tuple[str, ...] = ()
    star_magnitude_limit: float = 5.5
    milky_way_levels: tuple[str, ...] = ()
    heading_size_pt: float = 18
    number_size_pt: float = 10
    text_size_pt: float = 9
    paper_color: str = "white"
    ink_color: str = "#183b56"
    border_color: str = "#527089"
    highlight_color: str = "#276749"
    guide_color: str = "#b7791f"
    footprint_color: str = "#8b3b65"
    formats: tuple[str, ...] = ("png", "pdf", "svg")
    dpi: int = 160
    transparent: bool = False

    def __post_init__(self):
        for name in ("joined", "footprints", "transparent"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be a boolean.")
        for name, lo, hi in (("width_mm", 50, 1000), ("height_mm", 50, 1000),
                ("star_magnitude_limit", -2, 11), ("heading_size_pt", 2, 72),
                ("number_size_pt", 2, 72), ("text_size_pt", 2, 72)):
            value = _number(getattr(self, name), name)
            if not lo <= value <= hi:
                raise ValueError(f"{name} must be between {lo} and {hi}.")
            object.__setattr__(self, name, value)
        for name, allowed, nonempty in (
                ("layers", SUPPORTED_INDEX_LAYERS, False),
                ("milky_way_levels", {"ol1", "ol2", "ol3", "ol4", "ol5"}, False),
                ("formats", {"png", "pdf", "svg"}, True)):
            values = getattr(self, name)
            if not isinstance(values, (list, tuple)) or any(type(v) is not str for v in values):
                raise ValueError(f"{name} must be a list of names.")
            if len(set(values)) != len(values) or not set(values) <= allowed or (nonempty and not values):
                raise ValueError(f"Invalid or duplicate {name}.")
            object.__setattr__(self, name, tuple(values))
        if ("milky_way" in self.layers) != bool(self.milky_way_levels):
            raise ValueError("Select Milky Way levels exactly when its layer is enabled.")
        for name in ("paper_color", "ink_color", "border_color", "highlight_color", "guide_color", "footprint_color"):
            color = getattr(self, name)
            if type(color) is not str or not is_color_like(color):
                raise ValueError(f"{name} must be a Matplotlib colour string.")
        _integer(self.dpi, "dpi")
        if not 72 <= self.dpi <= 1200:
            raise ValueError("dpi must be between 72 and 1200.")

    @classmethod
    def from_dict(cls, data):
        _keys(data, {"schema_version", "document_kind", "layout", "content", "typography", "colours", "export"}, "index presentation")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise ValueError("Unsupported index presentation schema.")
        if data["document_kind"] != "wenu-atlas-index-presentation":
            raise ValueError("Unsupported index presentation kind.")
        groups = {
            "layout": {"joined", "footprints", "width_mm", "height_mm"},
            "content": {"layers", "star_magnitude_limit", "milky_way_levels"},
            "typography": {"heading_size_pt", "number_size_pt", "text_size_pt"},
            "colours": {"paper_color", "ink_color", "border_color", "highlight_color", "guide_color", "footprint_color"},
            "export": {"formats", "dpi", "transparent"},
        }
        values = {}
        for group, keys in groups.items():
            _keys(data[group], keys, group)
            values.update(data[group])
        return cls(**values)


def index_sky(star_magnitude_limit, *, include_lowest_mw_isophote=False,
              magellanic_clouds=False, layers=None, milky_way_levels=None):
    """Load catalogue owners once, without an observer or ephemeris."""
    if layers is None:
        layers = {"stars", "constellation_lines", "constellation_labels", "milky_way"}
        if magellanic_clouds:
            layers.add("magellanic_clouds")
    sky = CelestialSphere(None)
    if "milky_way" in layers:
        sky.add_milky_way_isophotes(levels=milky_way_levels or (
            ("ol1", "ol2", "ol3", "ol4", "ol5") if include_lowest_mw_isophote else None))
    if "magellanic_clouds" in layers:
        sky.add_magellanic_cloud_isophotes("lmc")
        sky.add_magellanic_cloud_isophotes("smc")
    # Constellation owners need catalogue vertices even if stars are hidden.
    if set(layers) & {"stars", "constellation_lines", "constellation_labels"}:
        sky.add_stars(magnitude_limit=star_magnitude_limit)
    if set(layers) & {"constellation_lines", "constellation_labels"}:
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


def _join_faces(figure, axes, atlas, presentation=None):
    """Bisect the paper lens; retain both full contours as assembly guides.

    Each own hemisphere is entirely on its assigned side of the join, so
    clipping the lens does not remove sky coverage. This is a two-projection
    index, not pointwise registration of the whole common sky band.
    """
    presentation = presentation or AtlasIndexPresentation()
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
                                color=presentation.border_color, linewidth=0.65, zorder=20))


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


def _draw_face(ax, atlas, face, *, footprints, sky=None, star_magnitude_limit=5.5,
               include_lowest_mw_isophote=False, magellanic_clouds=False, presentation=None):
    presentation = presentation or AtlasIndexPresentation(number_size_pt=10 if sky is not None else 7)
    renderer = MatplotlibRenderer(ax)
    renderer.apply_viewport(face.viewport)
    renderer.set_clip_boundary(face.boundary, style={"edgecolor": presentation.border_color, "facecolor": "none", "linewidth": 1})
    renderer.set_axes_frame_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    if sky is not None:
        composition = compose_chart(
            face, style="atlas", mode="print",
            detail_overrides=DetailOverrides(
                star_magnitude_limit=star_magnitude_limit,
                enabled_layers=frozenset(presentation.layers) if presentation.layers else frozenset({"stars", "constellation_lines",
                                          "constellation_labels", "milky_way"}
                                          | ({"magellanic_clouds"} if magellanic_clouds else set())),
                content_selection=SkyContentSelection(
                    milky_way_levels=frozenset(presentation.milky_way_levels) if presentation.milky_way_levels else (frozenset({"ol1", "ol2", "ol3", "ol4", "ol5"})
                    if include_lowest_mw_isophote else None),
                ),
                constellation_star_mode="none",
            ),
        )
        style = replace(composition.style,
                        canvas=replace(composition.style.canvas, sky_color="none"))
        options = composition.layer_options(sky).layer_options
        face.render(sky, renderer, style=style, layer_options=options,
                    realization_context=LayerRealizationContext(NATIVE_ICRS_SPEC),
                    boundary_style={"edgecolor": presentation.border_color, "facecolor": "none", "linewidth": 1})
    highlight = atlas.primary_sheet_id(atlas.seed_ra_deg, 0)
    label_x, label_y, labels, ids = [], [], [], []
    for sheet, ra0, ra1, lower, upper in visible_regions(atlas, face):
        selected = sheet.sheet_id == highlight
        renderer.draw(primary_outline(face, ra0, ra1, lower, upper), style={
            "facecolor": "none" if sky is not None else "#d0e9d8" if selected else
                         ("#edf3f8" if sheet.number % 2 else "#ffffff"),
            "edgecolor": presentation.highlight_color if selected else presentation.border_color,
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
                  label_style={"fontsize": presentation.number_size_pt,
                               "fontweight": "bold" if sky is not None else "normal",
                               "ha": "center", "va": "center",
                               "color": presentation.ink_color, "zorder": 25,
                               "bbox": {"facecolor": presentation.paper_color, "edgecolor": "none",
                                        "alpha": 0.85, "pad": 0.6}})
    ra = _samples(0, 360)
    for dec in (-atlas.geometry.overview.shared_band_width_deg / 2, 0,
                atlas.geometry.overview.shared_band_width_deg / 2):
        if (face.pole == "north" and dec < face.limiting_declination_deg) or (
                face.pole == "south" and dec > face.limiting_declination_deg):
            continue
        x, y = face.projection.project_spherical(ra, np.full(len(ra), dec))
        renderer.draw(ProjectedCurve(x, y, closed=True), style={
            "color": presentation.guide_color, "linewidth": 0.8,
            "linestyle": "-" if dec == 0 else "--", "zorder": 3,
        })
    dec = _samples(face.limiting_declination_deg, face.pole_declination_deg)
    x, y = face.projection.project_spherical(np.full(len(dec), atlas.geometry.overview.join_ra_deg), dec)
    renderer.draw(ProjectedCurve(x, y), style={"color": presentation.guide_color, "linewidth": 0.8, "zorder": 3})
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
                "color": presentation.highlight_color if sheet.sheet_id == highlight else presentation.footprint_color,
                "linewidth": 1.3 if sheet.sheet_id == highlight else 0.35,
                "alpha": 1 if sheet.sheet_id == highlight else 0.4,
                "zorder": 2,
            })
    renderer.finalize_graphics()
    ax.set_title(f"{'Norte' if face.pole == 'north' else 'Sur'} · límite Dec {face.limiting_declination_deg:+g}°",
                 fontsize=presentation.text_size_pt + 2, pad=12, color=presentation.ink_color)


def plot_overview(design_path, output_prefix, *, footprints=False, joined=False,
                  astronomy=False, star_magnitude_limit=5.5,
                  include_lowest_mw_isophote=False, magellanic_clouds=False, presentation=None):
    """Read/revalidate resolved JSON and write versioned PNG, PDF and SVG."""
    if (include_lowest_mw_isophote or magellanic_clouds) and not astronomy:
        raise ValueError("Milky Way and Cloud options require astronomy=True.")
    if presentation is None:
        layers = ("stars", "constellation_lines", "constellation_labels", "milky_way") if astronomy else ()
        if magellanic_clouds:
            layers += ("magellanic_clouds",)
        presentation = AtlasIndexPresentation(joined=joined, footprints=footprints,
            layers=layers, star_magnitude_limit=star_magnitude_limit,
            milky_way_levels=(("ol1", "ol2", "ol3", "ol4", "ol5") if include_lowest_mw_isophote else ("ol2", "ol3", "ol4", "ol5")) if astronomy else (),
            number_size_pt=10 if astronomy else 7)
    if not isinstance(presentation, AtlasIndexPresentation):
        raise ValueError("presentation must be an AtlasIndexPresentation.")
    joined, footprints = presentation.joined, presentation.footprints
    star_magnitude_limit = presentation.star_magnitude_limit
    astronomy = bool(presentation.layers)
    include_lowest_mw_isophote = "ol1" in presentation.milky_way_levels
    magellanic_clouds = "magellanic_clouds" in presentation.layers
    atlas = AtlasBandTiling.read_json(design_path)
    if not np.isfinite(star_magnitude_limit) or not -2 <= star_magnitude_limit <= 11:
        raise ValueError("star_magnitude_limit must be finite and between 0 and 11.")
    prefix = Path(output_prefix)
    if prefix.suffix or not prefix.name or not prefix.parent.is_dir():
        raise ValueError("Output prefix must have no extension and its parent must exist.")
    destinations = [prefix.with_suffix("." + suffix) for suffix in presentation.formats]
    if any(path.exists() or path.is_symlink() for path in destinations):
        raise FileExistsError("Choose a new versioned output prefix; existing products are preserved.")
    sky = index_sky(star_magnitude_limit,
                    include_lowest_mw_isophote=include_lowest_mw_isophote,
                    magellanic_clouds=magellanic_clouds, layers=presentation.layers,
                    milky_way_levels=presentation.milky_way_levels) if astronomy else None
    figure = plt.figure(figsize=(presentation.width_mm / 25.4, presentation.height_mm / 25.4), facecolor=presentation.paper_color)
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
                   fontsize=presentation.heading_size_pt, color=presentation.ink_color, y=0.965)
    figure.text(0.5, 0.91, f"Áreas principales numeradas · ICRS · solapamiento mínimo {atlas.overlap_deg:g}°",
                ha="center", fontsize=presentation.text_size_pt + 2, color=presentation.border_color)
    try:
        for ax, pole in zip(axes, ("north", "south"), strict=True):
            _draw_face(ax, atlas, overview_face(atlas.geometry.overview, pole), footprints=footprints,
                       sky=sky, star_magnitude_limit=star_magnitude_limit,
                       include_lowest_mw_isophote=include_lowest_mw_isophote,
                       magellanic_clouds=magellanic_clouds, presentation=presentation)
        if joined:
            _join_faces(figure, axes, atlas)
            for contour in figure.artists:
                contour.set_color(presentation.border_color)
        highlighted = next(sheet.number for sheet in atlas.geometry.sheets
                           if sheet.sheet_id == atlas.primary_sheet_id(atlas.seed_ra_deg, 0))
        region_hint = " (cerca de Orión)" if atlas.seed_ra_deg == 82.5 else ""
        figure.text(0.5, 0.075, f"Hoja semilla {highlighted}, centro semilla RA {atlas.seed_ra_deg / 15:g} h, Dec 0°{region_hint}.",
                    ha="center", fontsize=presentation.text_size_pt + 1, color=presentation.highlight_color)
        figure.text(0.5, 0.041, f"Guías: ecuador, límites de banda compartida ±{atlas.geometry.overview.shared_band_width_deg / 2:g}° y meridiano RA {atlas.geometry.overview.join_ra_deg / 15:g} h.",
                    ha="center", fontsize=presentation.text_size_pt, color=presentation.guide_color)
        layer_names = {"stars": f"estrellas m ≤ {star_magnitude_limit:g}",
            "constellation_lines": "líneas de constelación", "constellation_labels": "abreviaturas",
            "milky_way": "Vía Láctea " + "/".join(level.upper() for level in presentation.milky_way_levels),
            "magellanic_clouds": "Nubes de Magallanes"}
        content = " · ".join(layer_names[layer] for layer in presentation.layers) + ". " if astronomy else "Sin catálogos. "
        layout = "Contornos unidos; banda común con dos proyecciones. " if joined else "Discos separados. "
        variant = astronomy and (include_lowest_mw_isophote or magellanic_clouds)
        legend = ("Huellas completas." if footprints else "Bordes: propiedad primaria.") if variant else (
            "Huellas completas con solapamiento." if footprints else
            "Los bordes indican propiedad primaria, no la huella completa de cada hoja.")
        figure.text(0.5, 0.012, layout + content + legend,
                    ha="center", fontsize=presentation.text_size_pt, color=presentation.border_color)
        options = ExportOptions(dpi=presentation.dpi, bbox_inches=None,
                                transparent=presentation.transparent,
                                facecolor="none" if presentation.transparent else presentation.paper_color,
                                metadata={"Title": prefix.name, "Creator": "Wenu"})
        # Render every format before publishing; preserve existing destinations.
        published = []
        with tempfile.TemporaryDirectory(prefix=".wenu-index-", dir=prefix.parent) as staging:
            staged = [Path(staging) / path.name for path in destinations]
            for path in staged:
                options.save(figure, path)
            try:
                for source, destination in zip(staged, destinations, strict=True):
                    os.link(source, destination)
                    published.append((source, destination))
            except BaseException:
                for source, destination in reversed(published):
                    if destination.exists() and os.path.samefile(source, destination):
                        destination.unlink()
                raise
        return tuple(destinations)
    finally:
        plt.close(figure)
