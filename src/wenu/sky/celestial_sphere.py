# src/wenu/sky/celestial_sphere.py

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from wenu.objects.stars import Stars
from wenu.renderers.stars import StarsRenderingAdapter
from wenu.sky.constellations import Constellations
from wenu.sky.constellation_boundaries import ConstellationBoundaries
from wenu.sky.coordinate_grids import (
        EquatorialGrid,
        EclipticGrid,
        GalacticGrid,
        )
from wenu.sky.points import CelestialPoints
from wenu.sky.sky_layer import SkyLayer


class CelestialSphere:
    """
    The apparent celestial sphere for a particular observer.

    CelestialSphere coordinates astronomical layers such as stars,
    constellations, celestial curves, and celestial points. It does not
    perform projection mathematics or catalogue loading itself.

    Parameters
    ----------
    observer
        The observer defining the observing location, time, and reference
        frame.
    """

    def __init__(self, observer) -> None:
        self.observer = observer

        self.stars =  None
        self.star_renderer = None
        self.points = None
        self.constellations = None
        self.constellation_boundaries = None
        self.constellation_lines = None
        self._layers: list[SkyLayer] = []

    @property
    def layers(self) -> tuple[SkyLayer, ...]:
        """
        Return the registered sky layers.

        A tuple is returned so callers cannot modify the internal layer list
        accidentally.
        """
        return tuple(self._layers)

    def add(self, layer: SkyLayer) -> SkyLayer:
        """
        Add a sky layer to the celestial sphere.

        Parameters
        ----------
        layer
            An instance of :class:`SkyLayer`.

        Returns
        -------
        SkyLayer
            The added layer. Returning it allows further configuration after
            registration.
        """
        if not isinstance(layer, SkyLayer):
            raise TypeError(
                f"{type(layer).__name__} cannot be added to CelestialSphere "
                "because it does not implement the SkyLayer contract."
            )

        self._layers.append(layer)
        return layer

    def extend(self, layers: Iterable[SkyLayer]) -> None:
        """
        Add several sky layers.
        """
        for layer in layers:
            self.add(layer)

    def remove(self, layer: SkyLayer) -> None:
        """
        Remove a previously registered layer.
        """
        self._layers.remove(layer)

    def clear(self) -> None:
        """
        Remove all registered layers.
        """
        self._layers.clear()

# -----------------------------
# Star methods
# ----------------------------
    def add_stars(
        self,
        catalog="hipparcos",
        magnitude_limit=5.5,
    ) -> Stars:
        self.stars = Stars(
            observer=self.observer,
            catalog=catalog,
            magnitude_limit=magnitude_limit,
        )

        self.stars.load()

        self.star_renderer = StarsRenderingAdapter(
            stars=self.stars,
            observer=self.observer,
        )
        self.add(self.stars)

        return self.stars

# -------------------------------
# Celestial keypoints annotations
# --------------------------------
    def add_points(self, **kwargs: Any) -> CelestialPoints:
        self.points = CelestialPoints(obs=self.observer)
        return self.points

# -------------------------
# Constellation methods
# --------------------------
    
    def add_constellations(
        self,
        system="western",
        lines_file=None,
        selected=None,
    ):
        if self.stars is None:
            raise RuntimeError(
                "Stars must be added before constellations."
            )

        self.constellations = Constellations(
            stars=self.star_renderer,
            system=system,
            lines_file=lines_file,
            selected=selected,
        )

        if self.constellation_boundaries is not None:
            self.constellations.set_boundaries(
                self.constellation_boundaries
            )

        return self.constellations

    def add_constellation_boundaries(
        self,
        boundaries="iau",
        filename=None,
        *,
        constellations=None,
        **kwargs,
    ):
        boundary_layer = ConstellationBoundaries(
            observer=self.observer,
            boundaries=boundaries,
            filename=filename,
            constellations=constellations,
            **kwargs,
        )

        self.constellation_boundaries = boundary_layer

        if self.constellations is None:
            raise RuntimeError(
                "Call add_constellations() before "
                "add_constellation_boundaries()."
            )

        self.constellations.set_boundaries(boundary_layer)

        return boundary_layer

# ----------------------------
# Equatorial grid methods
# ----------------------------

    def draw_equatorial(
        self,
        ax,
        projection,
        *,
        frame="fk5",
        equinox="of_date",
        samples=721,
        min_altitude=0.0,
        **style,
    ):
        """
        Draw the celestial equator.

        Parameters
        ----------
        ax
            Matplotlib axes.
        projection
            Wenu projection used to draw the curve.
        frame
            Equatorial coordinate frame: ``"icrs"`` or ``"fk5"``.
        equinox
            FK5 equinox, or ``"of_date"``.
        samples
            Number of samples around the complete equator.
        min_altitude
            Projection clipping altitude in degrees.
        **style
            Keyword arguments passed through to Matplotlib ``ax.plot``.
        """
        grid = EquatorialGrid(
            observer=self.observer,
            frame=frame,
            equinox=equinox,
            samples=samples,
        )

        curve = grid.equator()

        return curve.draw(
            ax=ax,
            projection=projection,
            min_altitude=min_altitude,
            **style,
        )

    def draw_equatorial_parallel(
        self,
        ax,
        projection,
        declination_deg,
        *,
        frame="fk5",
        equinox="of_date",
        samples=721,
        min_altitude=0.0,
        **style,
    ):
        """
        Draw a constant-declination parallel.
        """
        grid = EquatorialGrid(
            observer=self.observer,
            frame=frame,
            equinox=equinox,
            samples=samples,
        )

        curve = grid.parallel(
            declination_deg=declination_deg,
        )

        return curve.draw(
            ax=ax,
            projection=projection,
            min_altitude=min_altitude,
            **style,
        )

    def draw_equatorial_meridian(
        self,
        ax,
        projection,
        right_ascension_deg,
        *,
        frame="fk5",
        equinox="of_date",
        samples=721,
        min_altitude=0.0,
        **style,
    ):
        """
        Draw a constant-right-ascension meridian.
    
        Parameters
        ----------
        ax
            Matplotlib axes.
        projection
            Wenu projection used to draw the curve.
        right_ascension_deg
            Right ascension of the meridian, in degrees.
        frame
            Equatorial coordinate frame: ``"icrs"`` or ``"fk5"``.
        equinox
            FK5 equinox, or ``"of_date"``.
        samples
            Number of samples along the complete meridian.
        min_altitude
            Projection clipping altitude in degrees.
        **style
            Keyword arguments passed through to Matplotlib ``ax.plot``.
        """
        grid = EquatorialGrid(
            observer=self.observer,
            frame=frame,
            equinox=equinox,
            samples=samples,
        )

        curve = grid.meridian(
            right_ascension_deg=right_ascension_deg,
        )

        return curve.draw(
            ax=ax,
            projection=projection,
            min_altitude=min_altitude,
            **style,
        )

    def draw_equatorial_grid(
        self,
        ax,
        projection,
        *,
        ra=None,
        dec=None,
        frame="fk5",
        equinox="of_date",
        samples=721,
        min_altitude=0.0,
        meridian_style=None,
        parallel_style=None,
        **style,
    ):
        """
        Draw selected meridians and parallels of an equatorial grid.

        Parameters
        ----------
        ax
            Matplotlib axes.
        projection
            Wenu projection used to draw the curves.
        ra
            Iterable of right ascensions in degrees. ``None`` draws no
            meridians.
        dec
            Iterable of declinations in degrees. ``None`` draws no
            parallels.
        frame
            Equatorial coordinate frame: ``"icrs"`` or ``"fk5"``.
        equinox
            FK5 equinox, or ``"of_date"``.
        samples
            Number of samples per curve.
        min_altitude
            Projection clipping altitude in degrees.
        meridian_style
            Style applied specifically to meridians.
        parallel_style
            Style applied specifically to parallels.
        **style
            Common style applied to every curve. Specific meridian or
            parallel styles override these values.

        Returns
        -------
        list
            Matplotlib artists generated by all grid curves.
        """
        if ra is None and dec is None:
            return []

        grid = EquatorialGrid(
            observer=self.observer,
            frame=frame,
            equinox=equinox,
            samples=samples,
        )

        common_style = dict(style)

        resolved_meridian_style = {
            **common_style,
            **({} if meridian_style is None else meridian_style),
        }

        resolved_parallel_style = {
            **common_style,
            **({} if parallel_style is None else parallel_style),
        }

        curves = grid.grid(
            ra=ra,
            dec=dec,
            meridian_style=resolved_meridian_style,
            parallel_style=resolved_parallel_style,
        )

        artists = []

        for curve in curves:
            artists.extend(
                curve.draw(
                    ax=ax,
                    projection=projection,
                    min_altitude=min_altitude,
                    **curve.style,
                )
            )

        return artists

# -------------------------
# Ecliptic grid methods
# -------------------------

    def draw_ecliptic(
        self,
        ax,
        projection,
        *,
        equinox="of_date",
        samples=721,
        min_altitude=0.0,
        **style,
    ):
        """
        Draw the ecliptic.
    
        The ecliptic is the zero-latitude parallel of the selected
        ecliptic coordinate system.
        """
        grid = EclipticGrid(
            observer=self.observer,
            equinox=equinox,
            samples=samples,
        )

        curve = grid.ecliptic()

        return curve.draw(
            ax=ax,
            projection=projection,
            min_altitude=min_altitude,
            **style,
        )

    def draw_ecliptic_parallel(
        self,
        ax,
        projection,
        latitude_deg,
        *,
        equinox="of_date",
        samples=721,
        min_altitude=0.0,
        **style,
    ):
        """
        Draw a constant-ecliptic-latitude parallel.
        """
        grid = EclipticGrid(
            observer=self.observer,
            equinox=equinox,
            samples=samples,
        )

        curve = grid.parallel(
            latitude_deg=latitude_deg,
        )

        return curve.draw(
            ax=ax,
            projection=projection,
            min_altitude=min_altitude,
            **style,
        )

    def draw_ecliptic_meridian(
        self,
        ax,
        projection,
        longitude_deg,
        *,
        equinox="of_date",
        samples=721,
        min_altitude=0.0,
        **style,
    ):
        """
        Draw a constant-ecliptic-longitude meridian.
        """
        grid = EclipticGrid(
            observer=self.observer,
            equinox=equinox,
            samples=samples,
        )

        curve = grid.meridian(
            longitude_deg=longitude_deg,
        )

        return curve.draw(
            ax=ax,
            projection=projection,
            min_altitude=min_altitude,
            **style,
        )

    def draw_ecliptic_grid(
        self,
        ax,
        projection,
        *,
        longitude=None,
        latitude=None,
        equinox="of_date",
        samples=721,
        min_altitude=0.0,
        meridian_style=None,
        parallel_style=None,
        **style,
    ):
        """
        Draw selected meridians and parallels of an ecliptic grid.

        Parameters
        ----------
        longitude
            Iterable of ecliptic longitudes in degrees.
        latitude
            Iterable of ecliptic latitudes in degrees.
        """
        if longitude is None and latitude is None:
            return []

        grid = EclipticGrid(
            observer=self.observer,
            equinox=equinox,
            samples=samples,
        )

        common_style = dict(style)

        resolved_meridian_style = {
            **common_style,
            **({} if meridian_style is None else meridian_style),
        }

        resolved_parallel_style = {
            **common_style,
            **({} if parallel_style is None else parallel_style),
        }

        curves = grid.grid(
            longitude=longitude,
            latitude=latitude,
            meridian_style=resolved_meridian_style,
            parallel_style=resolved_parallel_style,
        )

        artists = []

        for curve in curves:
            artists.extend(
                curve.draw(
                    ax=ax,
                    projection=projection,
                    min_altitude=min_altitude,
                    **curve.style,
                )
            )

        return artists

# -------------------------
# Galactic methods
# -------------------------
    def draw_galactic_plane(
        self,
        ax,
        projection,
        *,
        samples=721,
        min_altitude=0.0,
        **style,
    ):
        """
        Draw the Galactic plane.

        The Galactic plane is the zero-latitude parallel of the
        Galactic coordinate system.
        """
        grid = GalacticGrid(
            observer=self.observer,
            samples=samples,
        )

        curve = grid.galactic_plane()

        return curve.draw(
            ax=ax,
            projection=projection,
            min_altitude=min_altitude,
            **style,
        )

    def draw_galactic_parallel(
        self,
        ax,
        projection,
        latitude_deg,
        *,
        samples=721,
        min_altitude=0.0,
        **style,
    ):
        """
        Draw a constant-Galactic-latitude parallel.
        """
        grid = GalacticGrid(
            observer=self.observer,
            samples=samples,
        )

        curve = grid.parallel(
            latitude_deg=latitude_deg,
        )

        return curve.draw(
            ax=ax,
            projection=projection,
            min_altitude=min_altitude,
            **style,
        )

    def draw_galactic_meridian(
        self,
        ax,
        projection,
        longitude_deg,
        *,
        samples=721,
        min_altitude=0.0,
        **style,
    ):
        """
        Draw a constant-Galactic-longitude meridian.
        """
        grid = GalacticGrid(
            observer=self.observer,
            samples=samples,
        )

        curve = grid.meridian(
            longitude_deg=longitude_deg,
        )

        return curve.draw(
            ax=ax,
            projection=projection,
            min_altitude=min_altitude,
            **style,
        )


    def draw_galactic_grid(
        self,
        ax,
        projection,
        *,
        longitude=None,
        latitude=None,
        samples=721,
        min_altitude=0.0,
        meridian_style=None,
        parallel_style=None,
        **style,
    ):
        """
        Draw selected meridians and parallels of a Galactic grid.

        Parameters
        ----------
        longitude
            Iterable of Galactic longitudes in degrees.
        latitude
            Iterable of Galactic latitudes in degrees.
        """
        if longitude is None and latitude is None:
            return []

        grid = GalacticGrid(
            observer=self.observer,
            samples=samples,
        )

        common_style = dict(style)

        resolved_meridian_style = {
            **common_style,
            **({} if meridian_style is None else meridian_style),
        }

        resolved_parallel_style = {
            **common_style,
            **({} if parallel_style is None else parallel_style),
        }

        curves = grid.grid(
            longitude=longitude,
            latitude=latitude,
            meridian_style=resolved_meridian_style,
            parallel_style=resolved_parallel_style,
        )

        artists = []

        for curve in curves:
            artists.extend(
                curve.draw(
                    ax=ax,
                    projection=projection,
                    min_altitude=min_altitude,
                    **curve.style,
                )
            )

        return artists

# -------------------------------
# General curve drawing method
# ------------------------------

    def draw(self, ax, projection):
        artists = {}

        if self.star_renderer is not None:
            artists["stars"] = self.star_renderer.draw(
                ax=ax,
                projection=projection,
            )

        if self.constellations is not None:
            artists["constellations"] = self.constellations.draw(
                ax=ax,
                projection=projection,
            )

        if self.points is not None:
            artists["points"] = self.points.draw(
                ax=ax,
                projection=projection,
            )

        return artists


