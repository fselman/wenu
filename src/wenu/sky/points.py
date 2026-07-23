# src/wenu/sphere/points.py

from dataclasses import dataclass, field
from typing import Any, Optional

import astropy.units as u
from astropy.coordinates import SkyCoord, get_sun

from wenu.renderers import (
        layers,
        render_point,
        render_text,
        )
from wenu.geometry import radec_to_altaz


@dataclass
class _CelestialPoint:
    """
    Internal representation of one point on the celestial sphere.
    """

    coord: SkyCoord
    label: Optional[str] = None
    marker: str = "x"
    size: float = 30.0
    color: Any = "white"
    zorder: float = layers.POINTS
    style: dict = field(default_factory=dict)


class CelestialPoints:
    """
    Collection of geometrically significant points on the celestial sphere.

    Coordinates are stored as Astropy SkyCoord objects in their native
    coordinate frames. When drawn, they are transformed to ICRS, converted
    to horizontal coordinates, and passed to the projection.
    """

    def __init__(self, obs):
        """
        Parameters
        ----------
        obs
            Wenu Observer instance.
        """
        self.obs = obs
        self._points = []

    def clear(self):
        """
        Remove all points from the collection.
        """
        self._points.clear()
        return self

    def __len__(self):
        """
        Return the number of stored points.
        """
        return len(self._points)

    def _append_point(
        self,
        coord,
        label=None,
        marker="x",
        size=30.0,
        color="white",
        zorder=layers.POINTS,
        **style,
    ):
        """
        Append one SkyCoord point to the internal collection.
        """
        self._points.append(
            _CelestialPoint(
                coord=coord,
                label=label,
                marker=marker,
                size=size,
                color=color,
                zorder=zorder,
                style=style,
            )
        )

        return self

    # ------------------------------------------------------------------
    # Generic coordinate-frame methods
    # ------------------------------------------------------------------

    def add_equatorial_point(
        self,
        ra_deg,
        dec_deg,
        label=None,
        marker="x",
        size=30.0,
        color="white",
        zorder=layers.POINTS,
        **style,
    ):
        """
        Add a point specified in equatorial ICRS coordinates.

        Parameters
        ----------
        ra_deg, dec_deg
            Right ascension and declination in degrees.
        """
        coord = SkyCoord(
            ra=float(ra_deg) * u.deg,
            dec=float(dec_deg) * u.deg,
            frame=self.obs.icrs_frame,
        )

        return self._append_point(
            coord=coord,
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
        zorder=layers.POINTS,
        **style,
    ):
        """
        Add a point specified in Galactic longitude and latitude.

        Parameters
        ----------
        lon_deg, lat_deg
            Galactic longitude and latitude in degrees.
        """
        coord = SkyCoord(
            l=float(lon_deg) * u.deg,
            b=float(lat_deg) * u.deg,
            frame=self.obs.galactic_frame,
        )

        return self._append_point(
            coord=coord,
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
        zorder=layers.POINTS,
        **style,
    ):
        """
        Add a point in the ecliptic frame defined by Observer.

        Parameters
        ----------
        lon_deg, lat_deg
            Ecliptic longitude and latitude in degrees.
        """
        coord = SkyCoord(
            lon=float(lon_deg) * u.deg,
            lat=float(lat_deg) * u.deg,
            frame=self.obs.ecliptic_frame,
        )

        return self._append_point(
            coord=coord,
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    # ------------------------------------------------------------------
    # Equatorial points
    # ------------------------------------------------------------------

    def add_equatorial_pole(
        self,
        pole="visible",
        label=None,
        marker="+",
        size=50.0,
        color="white",
        zorder=layers.POINTS,
        **style,
    ):
        """
        Add the north, south, or locally visible celestial pole.
        """
        pole = self._resolve_pole(pole)

        dec_deg = 90.0 if pole == "north" else -90.0

        if label is None:
            label = "NCP" if pole == "north" else "SCP"

        return self.add_equatorial_point(
            ra_deg=0.0,
            dec_deg=dec_deg,
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    # ------------------------------------------------------------------
    # Galactic points
    # ------------------------------------------------------------------

    def add_galactic_center(
        self,
        label="GC",
        marker="+",
        size=50.0,
        color="yellow",
        zorder=layers.POINTS,
        **style,
    ):
        """
        Add the Galactic Center at l = 0 degrees, b = 0 degrees.
        """
        return self.add_galactic_point(
            lon_deg=0.0,
            lat_deg=0.0,
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    def add_galactic_anticenter(
        self,
        label="GAC",
        marker="+",
        size=50.0,
        color="yellow",
        zorder=layers.POINTS,
        **style,
    ):
        """
        Add the Galactic anticenter at l = 180 degrees, b = 0 degrees.
        """
        return self.add_galactic_point(
            lon_deg=180.0,
            lat_deg=0.0,
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    def add_galactic_pole(
        self,
        pole="visible",
        label=None,
        marker="x",
        size=45.0,
        color="yellow",
        zorder=layers.POINTS,
        **style,
    ):
        """
        Add the north, south, or locally visible Galactic pole.
        """
        pole = self._resolve_pole(pole)

        lat_deg = 90.0 if pole == "north" else -90.0

        if label is None:
            label = "NGP" if pole == "north" else "SGP"

        return self.add_galactic_point(
            lon_deg=0.0,
            lat_deg=lat_deg,
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    # ------------------------------------------------------------------
    # Ecliptic points
    # ------------------------------------------------------------------

    def add_ecliptic_pole(
        self,
        pole="visible",
        label=None,
        marker="x",
        size=45.0,
        color="cyan",
        zorder=layers.POINTS,
        **style,
    ):
        """
        Add the north, south, or locally visible ecliptic pole.
        """
        pole = self._resolve_pole(pole)

        lat_deg = 90.0 if pole == "north" else -90.0

        if label is None:
            label = "NEP" if pole == "north" else "SEP"

        return self.add_ecliptic_point(
            lon_deg=0.0,
            lat_deg=lat_deg,
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    def add_ecliptic_cardinal_points(
        self,
        marker="o",
        size=28.0,
        color="cyan",
        zorder=layers.POINTS,
        **style,
    ):
        """
        Add the four cardinal points of the ecliptic.

        Ecliptic longitudes
        -------------------
        0 degrees
            Aries.
        90 degrees
            Cancer.
        180 degrees
            Libra.
        270 degrees
            Capricorn.
        """
        cardinal_points = (
            (0.0, "♈"),
            (90.0, "♋"),
            (180.0, "♎"),
            (270.0, "♑"),
        )

        for lon_deg, label in cardinal_points:
            self.add_ecliptic_point(
                lon_deg=lon_deg,
                lat_deg=0.0,
                label=label,
                marker=marker,
                size=size,
                color=color,
                zorder=zorder,
                **style,
            )

        return self

    def add_ecliptic_keypoints(
        self,
        marker="o",
        size=28.0,
        color="cyan",
        zorder=layers.POINTS,
        **style,
    ):
        """
        Alias for add_ecliptic_cardinal_points().
        """
        return self.add_ecliptic_cardinal_points(
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    # ------------------------------------------------------------------
    # Solar-system geometry
    # ------------------------------------------------------------------

    def add_antisolar_point(
        self,
        label="AS",
        marker="+",
        size=50.0,
        color="orange",
        zorder=layers.POINTS,
        **style,
    ):
        """
        Add the point on the celestial sphere opposite the Sun.
        """
        sun = get_sun(self.obs.t_astropy).transform_to(
            self.obs.icrs_frame
        )

        antisolar_ra = (
            sun.ra + 180.0 * u.deg
        ).wrap_at(360.0 * u.deg)

        antisolar_dec = -sun.dec

        coord = SkyCoord(
            ra=antisolar_ra,
            dec=antisolar_dec,
            frame=self.obs.icrs_frame,
        )

        return self._append_point(
            coord=coord,
            label=label,
            marker=marker,
            size=size,
            color=color,
            zorder=zorder,
            **style,
        )

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, ax, projection):
        """
        Project and render all visible stored points.

        Points below the horizon are not rendered.

        Returns
        -------
        list
            Matplotlib marker and text artists created by the renderer.
        """
        artists = []

        for point in self._points:
            icrs = point.coord.transform_to(
                self.obs.icrs_frame
            )

            alt_deg, az_deg = radec_to_altaz(
                icrs.ra.deg,
                icrs.dec.deg,
                self.obs.t,
                self.obs.lat_deg,
                self.obs.lon_deg,
            )

            alt_deg = float(alt_deg)
            az_deg = float(az_deg)

            if alt_deg < 0.0:
                continue

            projected = projection.project_point(
                lon_deg=az_deg,
                lat_deg=alt_deg,
                name=point.label,
            )

            style = dict(point.style)

            label_offset = style.pop(
                "label_offset",
                (0.03, 0.03),
            )
            fontsize = style.pop(
                "fontsize",
                9,
            )

            marker_artist = render_point(
                ax,
                projected,
                marker=point.marker,
                s=point.size,
                color=point.color,
                zorder=point.zorder,
                **style,
            )

            artists.append(marker_artist)

            if point.label is not None:
                dx, dy = label_offset

                label_artist = render_text(
                    ax,
                    projected.x + dx,
                    projected.y + dy,
                    point.label,
                    fontsize=fontsize,
                    color=point.color,
                    ha="left",
                    va="bottom",
                    zorder=point.zorder,
                )

                artists.append(label_artist)

        return artists

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    def _resolve_pole(self, pole):
        """
        Resolve 'north', 'south', or 'visible' to north or south.
        """
        pole = pole.lower()

        if pole == "visible":
            return "north" if self.obs.lat_deg >= 0.0 else "south"

        if pole not in {"north", "south"}:
            raise ValueError(
                "pole must be 'north', 'south', or 'visible'"
            )

        return pole
