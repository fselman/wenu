"""Observer-latitude horizon geometry for paired polar overlays."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.coordinates import observer_altaz_spec

from wenu.charts.coordinate_frames import horizontal_to_equatorial
from wenu.charts.polar_page_furniture import PolarPagePairFurniture
from wenu.charts.polar_planisphere_pair import PolarPlanispherePair
from wenu.geometry.spherical import SphericalCurves, SphericalPoints
from wenu.sky.horizon import HorizonReference


@dataclass(frozen=True)
class PolarHorizonFaceOverlay:
    """One clipped horizon window in physical page coordinates."""

    face: str
    page_size_mm: tuple[float, float]
    disk_center_mm: tuple[float, float]
    disk_radius_mm: float
    site_latitude_deg: float
    cut_clearance_mm: float
    horizon_segments_mm: tuple[tuple[tuple[float, float], ...], ...]
    pole_position_mm: tuple[float, float]
    meridian_horizon_position_mm: tuple[float, float]

    @property
    def pole_to_horizon_mm(self):
        """Return the physical pole-to-meridian-horizon distance."""
        pole = np.asarray(self.pole_position_mm, dtype=float)
        horizon = np.asarray(self.meridian_horizon_position_mm, dtype=float)
        return float(np.linalg.norm(horizon - pole))


@dataclass(frozen=True)
class PolarHorizonPairOverlay:
    """Matched south- and north-facing observer-latitude overlays."""

    south: PolarHorizonFaceOverlay
    north: PolarHorizonFaceOverlay

    @property
    def faces(self):
        return self.south, self.north


@dataclass(frozen=True)
class PolarHorizonOverlayRequest:
    """Resolve canonical altitude-zero geometry onto both physical faces."""

    site_latitude_deg: float = -32.443342
    samples: int = 721
    cut_clearance_mm: float = 1.0

    def __post_init__(self):
        latitude = float(self.site_latitude_deg)
        clearance = float(self.cut_clearance_mm)
        if not np.isfinite(latitude) or not -90.0 < latitude < 90.0:
            raise ValueError(
                "site_latitude_deg must be finite and between -90 and 90."
            )
        if int(self.samples) < 16:
            raise ValueError("samples must be at least 16.")
        if not np.isfinite(clearance) or clearance < 0.0:
            raise ValueError(
                "cut_clearance_mm must be finite and non-negative."
            )
        object.__setattr__(self, "site_latitude_deg", latitude)
        object.__setattr__(self, "samples", int(self.samples))
        object.__setattr__(self, "cut_clearance_mm", clearance)

    def resolve(self, pair, pages, observer):
        """Return paired physical overlays for one observer and disk pair."""
        if not isinstance(pair, PolarPlanispherePair):
            raise TypeError("pair must be a PolarPlanispherePair value.")
        if not isinstance(pages, PolarPagePairFurniture):
            raise TypeError("pages must be a PolarPagePairFurniture value.")
        observer_latitude = getattr(observer, "lat_deg", None)
        if observer_latitude is None:
            raise TypeError("observer must provide lat_deg.")
        if not np.isclose(
            float(observer_latitude), self.site_latitude_deg, atol=1.0e-9
        ):
            raise ValueError(
                "observer latitude must match the horizon-overlay latitude."
            )
        horizon = HorizonReference(samples=self.samples).spherical_geometry(
            observer
        )
        equatorial = horizontal_to_equatorial(horizon, observer)
        references, zenith_ra_deg = _equatorial_references(observer)
        normalized_horizon = _relative_right_ascension(
            equatorial, zenith_ra_deg
        )
        normalized_references = (
            _wrap_degrees(references.lon_deg - zenith_ra_deg),
            references.lat_deg,
        )
        south = _resolve_face(
            face="south",
            chart=pair.south,
            page=pages.south,
            horizon=normalized_horizon,
            reference_coordinates=normalized_references,
            site_latitude_deg=self.site_latitude_deg,
            cut_clearance_mm=self.cut_clearance_mm,
        )
        north = _resolve_face(
            face="north",
            chart=pair.north,
            page=pages.north,
            horizon=normalized_horizon,
            reference_coordinates=normalized_references,
            site_latitude_deg=self.site_latitude_deg,
            cut_clearance_mm=self.cut_clearance_mm,
        )
        return PolarHorizonPairOverlay(south=south, north=north)


def _equatorial_references(observer):
    horizontal = SphericalPoints(
        lon_deg=np.asarray((0.0, 180.0, 0.0)),
        lat_deg=np.asarray((0.0, 0.0, 90.0)),
        coordinate_spec=observer_altaz_spec(
            observer, provider="wenu polar horizon reference"
        ),
        labels=np.asarray(("N", "S", "ZENITH"), dtype=object),
        metadata={"coordinate_system": "altaz"},
    )
    equatorial = horizontal_to_equatorial(horizontal, observer)
    return equatorial, float(equatorial.lon_deg[-1])


def _relative_right_ascension(curves, zenith_ra_deg):
    return SphericalCurves(
        lon_deg=tuple(
            _wrap_degrees(longitude - zenith_ra_deg)
            for longitude in curves.lon_deg
        ),
        lat_deg=tuple(latitude.copy() for latitude in curves.lat_deg),
        coordinate_spec=curves.coordinate_spec,
        closed=curves.closed.copy(),
        ids=None if curves.ids is None else curves.ids.copy(),
        labels=None if curves.labels is None else curves.labels.copy(),
        names=None if curves.names is None else curves.names.copy(),
        metadata={
            **dict(curves.metadata),
            "longitude_reference": "local_meridian",
        },
    )


def _resolve_face(
    *,
    face,
    chart,
    page,
    horizon,
    reference_coordinates,
    site_latitude_deg,
    cut_clearance_mm,
):
    projected = chart.project_equatorial_geometry(horizon)
    scale = page.disk_radius_mm / chart.boundary_radius
    center = np.asarray(page.disk_center_mm, dtype=float)
    segments = tuple(
        tuple(
            (float(x), float(y))
            for x, y in zip(
                center[0] + scale * curve.x,
                center[1] + scale * curve.y,
                strict=True,
            )
        )
        for curve in projected
    )
    longitude, latitude = reference_coordinates
    x, y = chart.projection.project_spherical(longitude[:2], latitude[:2])
    meridian_positions = tuple(
        (
            float(center[0] + scale * value_x),
            float(center[1] + scale * value_y),
        )
        for value_x, value_y in zip(x, y, strict=True)
    )
    meridian = meridian_positions[1 if face == "south" else 0]
    return PolarHorizonFaceOverlay(
        face=face,
        page_size_mm=page.page_size_mm,
        disk_center_mm=page.disk_center_mm,
        disk_radius_mm=page.disk_radius_mm,
        site_latitude_deg=site_latitude_deg,
        cut_clearance_mm=cut_clearance_mm,
        horizon_segments_mm=segments,
        pole_position_mm=page.disk_center_mm,
        meridian_horizon_position_mm=meridian,
    )


def _wrap_degrees(values):
    return (np.asarray(values, dtype=float) + 180.0) % 360.0 - 180.0