"""Canonical single-save export of paired physical polar pages."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np

from wenu.charts.composition import compose_chart
from wenu.coordinate_service import CoordinateService
from wenu.coordinates import CoordinateSpec, observer_celestial_spec
from wenu.geometry.spherical import SphericalPoints
from wenu.charts.detail import DetailOverrides
from wenu.charts.export_workflow import ChartExportResult
from wenu.charts.furniture import (
    ChartFurnitureOptions,
    PoleAnnotations,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
)
from wenu.charts.modes import PrintMode
from wenu.charts.polar_calendar_furniture import PolarCalendarPairFurniture
from wenu.charts.polar_page_furniture import PolarPagePairFurniture
from wenu.charts.polar_page_rendering import (
    draw_polar_page_furniture,
    polar_disk_axes_bounds,
)
from wenu.charts.polar_planisphere_pair import PolarPlanispherePair
from wenu.charts.regional import ExportOptions
from wenu.rendering.matplotlib import MatplotlibRenderer


MM_PER_INCH = 25.4


@dataclass(frozen=True)
class PolarPagePairExportResult:
    """Inspectable canonical exports for the two physical disk pages."""

    south: ChartExportResult
    north: ChartExportResult

    @property
    def faces(self):
        return self.south, self.north


def export_polar_planisphere_pages(
    pair,
    calendar,
    pages,
    sky,
    observer,
    *,
    south_path,
    north_path,
    dpi=300,
):
    """Export one actual-size A4 page per face through the canonical saver."""
    if not isinstance(pair, PolarPlanispherePair):
        raise TypeError("pair must be a PolarPlanispherePair value.")
    if not isinstance(calendar, PolarCalendarPairFurniture):
        raise TypeError("calendar must be a PolarCalendarPairFurniture value.")
    if not isinstance(pages, PolarPagePairFurniture):
        raise TypeError("pages must be a PolarPagePairFurniture value.")
    if int(dpi) <= 0:
        raise ValueError("dpi must be positive.")
    south = _export_face(
        pair.south,
        calendar.south,
        pages.south,
        sky,
        observer,
        south_path,
        dpi=int(dpi),
    )
    north = _export_face(
        pair.north,
        calendar.north,
        pages.north,
        sky,
        observer,
        north_path,
        dpi=int(dpi),
    )
    return PolarPagePairExportResult(south=south, north=north)


def _export_face(
    chart,
    calendar_face,
    page_face,
    sky,
    observer,
    destination,
    *,
    dpi,
):
    mode = PrintMode(
        width_inches=page_face.page_width_mm / MM_PER_INCH,
        height_inches=page_face.page_height_mm / MM_PER_INCH,
        dpi=dpi,
    )
    composition = compose_chart(
        chart,
        style="atlas",
        mode=mode,
        detail_overrides=DetailOverrides(
            enabled_layer_additions=frozenset({"equatorial_grid"}),
        ),
        furniture=ChartFurnitureOptions(
            references=_polar_reference_annotations(chart, observer),
            poles=PoleAnnotations(
                celestial="both",
                ecliptic="both",
                galactic="both",
                labels=True,
            ),
        ),
    )
    figure = plt.figure(
        figsize=(mode.width_inches, mode.height_inches),
        facecolor=composition.style.canvas.sky_color,
    )
    ax = figure.add_axes(polar_disk_axes_bounds(page_face))
    composition.style.configure_axes(ax)
    renderer = MatplotlibRenderer(ax)
    decorator = partial(
        draw_polar_page_furniture,
        calendar_face=calendar_face,
        page_face=page_face,
    )
    options = ExportOptions(
        dpi=dpi,
        bbox_inches=None,
        transparent=False,
        facecolor=composition.style.canvas.sky_color,
        metadata={
            "Title": page_face.product_identifier,
            "Creator": "Wenu",
            "Subject": f"Source revision {page_face.source_revision}",
        },
        padding=0.0,
    )
    try:
        return chart.export(
            sky,
            renderer,
            destination,
            observer=observer,
            composition=composition,
            export_options=options,
            additional_furniture=decorator,
        )
    finally:
        plt.close(figure)


def _projected_anchor(chart, observer, *, frame, angle_deg):
    if frame == "equatorial":
        right_ascension_deg, declination_deg = float(angle_deg), 0.0
    else:
        point = CoordinateService().transform(
            SphericalPoints(
                lon_deg=np.asarray((float(angle_deg),)),
                lat_deg=np.asarray((0.0,)),
                coordinate_spec=CoordinateSpec(
                    frame="barycentric-true-ecliptic",
                    origin="solar-system-barycenter",
                    equinox=str(observer.t_astropy),
                    provider="wenu polar reference anchor",
                ),
            ),
            observer_celestial_spec(
                observer,
                "icrs",
                model="Astropy ecliptic to ICRS",
            ),
        )
        right_ascension_deg = float(point.lon_deg[0])
        declination_deg = float(point.lat_deg[0])
    x, y = chart.projection.project_spherical(
        np.asarray((right_ascension_deg,)),
        np.asarray((declination_deg,)),
    )
    return float(x[0]), float(y[0])


def _polar_reference_annotations(chart, observer):
    from wenu.configuration import load_packaged_defaults

    values = load_packaged_defaults()["grids_references"][
        "polar_planisphere_label_anchors"
    ][chart.pole]

    def labeled(text, anchor):
        return ReferencePlaneAnnotation(
            state="labeled", label=text, anchor=anchor
        )

    return ReferenceAnnotations(
        celestial_equator=labeled(
            "Celestial equator",
            _projected_anchor(
                chart,
                observer,
                frame="equatorial",
                angle_deg=values["equatorial_right_ascension_deg"],
            ),
        ),
        ecliptic=labeled(
            "Ecliptic",
            _projected_anchor(
                chart,
                observer,
                frame="ecliptic",
                angle_deg=values["ecliptic_longitude_deg"],
            ),
        ),
        galactic_plane=ReferencePlaneAnnotation(
            state="labeled", label="Galactic plane"
        ),
    )
