"""Celestial reference points as spherical domain geometry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import astropy.units as u
import numpy as np
from astropy.coordinates import (
    BarycentricMeanEcliptic,
    Galactic,
    ICRS,
    SkyCoord,
    get_sun,
)

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import (
    CoordinateSpec,
    ICRS_ASTROMETRIC_SPEC,
    PositionStatus,
    observation_context,
    observer_altaz_spec,
)
from wenu.sky.geometrical_object import GeometricalObject
from wenu.geometry.spherical import SphericalPoints


@dataclass
class _CelestialPoint:
    coord: SkyCoord
    label: str | None = None
    marker: str = "x"
    size: float = 30.0
    color: Any = "white"
    zorder: float | None = None
    style: dict[str, Any] = field(default_factory=dict)


class CelestialPoints(GeometricalObject):
    """Geometrically significant points stored in their native frames."""

    layer_name = "celestial_points"

    def __init__(self, obs):
        self.obs = obs
        self._points: list[_CelestialPoint] = []

    def clear(self):
        self._points.clear()
        return self

    def __len__(self):
        return len(self._points)

    def _append_point(
        self,
        coord,
        label=None,
        marker="x",
        size=30.0,
        color="white",
        zorder=None,
        **style,
    ):
        self._points.append(
            _CelestialPoint(
                coord=coord,
                label=label,
                marker=marker,
                size=float(size),
                color=color,
                zorder=zorder,
                style=dict(style),
            )
        )
        return self

    def add_equatorial_point(
        self,
        ra_deg,
        dec_deg,
        label=None,
        marker="x",
        size=30.0,
        color="white",
        zorder=None,
        **style,
    ):
        return self._append_point(
            coord=SkyCoord(
                ra=float(ra_deg) * u.deg,
                dec=float(dec_deg) * u.deg,
                frame=ICRS(),
            ),
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    def add_galactic_point(
        self,
        lon_deg,
        lat_deg,
        label=None,
        marker="x",
        size=30.0,
        color="white",
        zorder=None,
        **style,
    ):
        return self._append_point(
            coord=SkyCoord(
                l=float(lon_deg) * u.deg,
                b=float(lat_deg) * u.deg,
                frame=Galactic(),
            ),
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    def add_ecliptic_point(
        self,
        lon_deg,
        lat_deg,
        label=None,
        marker="x",
        size=30.0,
        color="white",
        zorder=None,
        frame=None,
        **style,
    ):
        frame = (
            BarycentricMeanEcliptic(equinox=self.obs.t_astropy)
            if frame is None
            else frame
        )
        return self._append_point(
            coord=SkyCoord(
                lon=float(lon_deg) * u.deg,
                lat=float(lat_deg) * u.deg,
                frame=frame,
            ),
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    def add_equatorial_pole(
        self,
        pole="visible",
        label=None,
        marker="+",
        size=50.0,
        color="white",
        zorder=None,
        **style,
    ):
        pole = self._resolve_pole(pole)
        if label is None:
            label = "NCP" if pole == "north" else "SCP"
        return self.add_equatorial_point(
            ra_deg=0.0,
            dec_deg=90.0 if pole == "north" else -90.0,
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    def add_galactic_center(
        self,
        label="GC",
        marker="+",
        size=50.0,
        color="yellow",
        zorder=None,
        **style,
    ):
        return self.add_galactic_point(
            0.0, 0.0, label, marker, size, color, zorder, **style
        )

    def add_galactic_anticenter(
        self,
        label="GAC",
        marker="+",
        size=50.0,
        color="yellow",
        zorder=None,
        **style,
    ):
        return self.add_galactic_point(
            180.0, 0.0, label, marker, size, color, zorder, **style
        )

    def add_galactic_pole(
        self,
        pole="visible",
        label=None,
        marker="x",
        size=45.0,
        color="yellow",
        zorder=None,
        **style,
    ):
        pole = self._resolve_pole(pole)
        if label is None:
            label = "NGP" if pole == "north" else "SGP"
        return self.add_galactic_point(
            0.0,
            90.0 if pole == "north" else -90.0,
            label,
            marker,
            size,
            color,
            zorder,
            **style,
        )

    def add_ecliptic_pole(
        self,
        pole="visible",
        label=None,
        marker="x",
        size=45.0,
        color="cyan",
        zorder=None,
        **style,
    ):
        pole = self._resolve_pole(pole)
        if label is None:
            label = "NEP" if pole == "north" else "SEP"
        return self.add_ecliptic_point(
            0.0,
            90.0 if pole == "north" else -90.0,
            label,
            marker,
            size,
            color,
            zorder,
            **style,
        )

    def add_ecliptic_cardinal_points(
        self,
        marker="o",
        size=28.0,
        color="cyan",
        zorder=None,
        frame=None,
        labels=True,
        **style,
    ):
        for lon_deg, label in (
            (0.0, "♈"),
            (90.0, "♋"),
            (180.0, "♎"),
            (270.0, "♑"),
        ):
            self.add_ecliptic_point(
                lon_deg,
                0.0,
                label if labels else "",
                marker,
                size,
                color,
                zorder,
                frame=frame,
                **style,
            )
        return self

    def add_ecliptic_keypoints(self, **kwargs):
        return self.add_ecliptic_cardinal_points(**kwargs)

    def add_antisolar_point(
        self,
        label="AS",
        marker="+",
        size=50.0,
        color="orange",
        zorder=None,
        **style,
    ):
        sun = self._to_icrs(get_sun(self.obs.t_astropy))
        coord = SkyCoord(
            ra=(sun.lon_deg[0] + 180.0) % 360.0 * u.deg,
            dec=-sun.lat_deg[0] * u.deg,
            frame=self.obs.icrs_frame,
        )
        return self._append_point(
            coord,
            label,
            marker,
            size,
            color,
            zorder,
            **style,
        )

    def spherical_geometry(self, observer) -> SphericalPoints:
        """Return all points as one observer-dependent Alt/Az collection."""
        resolved_observer = self.obs if observer is None else observer

        if not self._points:
            return SphericalPoints(
                lon_deg=np.asarray([], dtype=float),
                lat_deg=np.asarray([], dtype=float),
                coordinate_spec=observer_altaz_spec(
                    resolved_observer, provider="wenu celestial points"
                ),
                labels=np.asarray([], dtype=object),
                metadata=self._style_metadata(),
            )

        icrs = [self._to_icrs(point.coord) for point in self._points]
        native = SphericalPoints(
            lon_deg=np.asarray([value.lon_deg[0] for value in icrs]),
            lat_deg=np.asarray([value.lat_deg[0] for value in icrs]),
            coordinate_spec=ICRS_ASTROMETRIC_SPEC,
            labels=[point.label for point in self._points],
            metadata=self._style_metadata(),
        )
        return CoordinateService().transform(
            native,
            observer_altaz_spec(
                resolved_observer, provider="wenu celestial points"
            ),
            observation=observation_context(resolved_observer),
        )

    @staticmethod
    def _native_spec(coord):
        frame = coord.frame
        name = frame.name
        common = {
            "position_status": PositionStatus.ASTROMETRIC,
            "provider": "wenu celestial point",
        }
        if name == "icrs":
            return ICRS_ASTROMETRIC_SPEC
        if name == "galactic":
            return CoordinateSpec(
                frame="galactic", origin="galactic-center", **common
            )
        if name == "fk5":
            return CoordinateSpec(
                frame="fk5",
                origin="solar-system-barycenter",
                equinox=str(frame.equinox),
                **common,
            )
        if name in {
            "barycentricmeanecliptic",
            "barycentrictrueecliptic",
        }:
            kind = (
                "barycentric-mean-ecliptic"
                if name == "barycentricmeanecliptic"
                else "barycentric-true-ecliptic"
            )
            return CoordinateSpec(
                frame=kind,
                origin="solar-system-barycenter",
                equinox=str(frame.equinox),
                **common,
            )
        if name == "gcrs":
            return CoordinateSpec(
                frame="gcrs",
                origin="earth-center",
                instant=str(frame.obstime.isot),
                time_scale=str(frame.obstime.scale),
                **common,
            )
        raise ValueError(
            f"Unsupported celestial-point frame: {name!r}."
        )

    @classmethod
    def _to_icrs(cls, coord):
        spherical = coord.spherical
        native = SphericalPoints(
            lon_deg=np.asarray([spherical.lon.to_value(u.deg)]),
            lat_deg=np.asarray([spherical.lat.to_value(u.deg)]),
            coordinate_spec=cls._native_spec(coord),
        )
        return CoordinateService().transform(
            native, ICRS_ASTROMETRIC_SPEC
        )

    def _style_metadata(self):
        return {
            "marker": np.asarray(
                [point.marker for point in self._points],
                dtype=object,
            ),
            "size": np.asarray(
                [point.size for point in self._points],
                dtype=float,
            ),
            "color": np.asarray(
                [point.color for point in self._points],
                dtype=object,
            ),
            "zorder": np.asarray(
                [point.zorder for point in self._points],
                dtype=object,
            ),
            "style": tuple(
                dict(point.style) for point in self._points
            ),
        }

    def _resolve_pole(self, pole):
        pole = pole.lower()
        if pole == "visible":
            return "north" if self.obs.lat_deg >= 0.0 else "south"
        if pole not in {"north", "south"}:
            raise ValueError(
                "pole must be 'north', 'south', or 'visible'"
            )
        return pole