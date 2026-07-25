# src/wenu/sky/celestial_sphere.py

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from wenu.chart import (
        ChartRenderingResult,
        LayerRenderingResult,
        )

from wenu.objects.stars import Stars
from wenu.renderers.stars import StarsRenderingAdapter
from wenu.renderers.celestial_points import (
        CelestialPointsRenderingAdapter,
        )
from wenu.renderers.constellation_boundaries import (
        ConstellationBoundaryRenderingAdapter,
        )
from wenu.renderers.coordinate_grids import (
        CoordinatesGridRenderingAdapter,
        )
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
        self.point_renderer = None
        self.constellations = None
        self.constellation_boundaries = None
        self.constellation_boundary_renderer = None
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


    def draw_chart(
        self,
        *,
        projection,
        renderer,
        viewport=None,
        layer_options=None,
    ) -> ChartRenderingResult:
        """Render every registered SkyLayer through the generic pipeline."""
        if not callable(getattr(projection, "project_geometry", None)):
            raise TypeError(
                "projection must provide project_geometry()."
            )
        if not callable(getattr(renderer, "draw", None)):
            raise TypeError("renderer must provide draw().")

        if viewport is not None:
            apply = getattr(renderer, "apply_viewport", None)
            if not callable(apply):
                raise TypeError(
                    "renderer must provide apply_viewport() when a "
                    "viewport is supplied."
                )
            apply(viewport)

        options = {} if layer_options is None else layer_options
        rendered_layers = []
        for layer in self._layers:
            spherical = layer.spherical_geometry(self.observer)
            projected = projection.project_geometry(spherical)
            render_options = self._layer_render_options(
                layer,
                options,
            )
            artists = renderer.draw(
                projected,
                **render_options,
            )
            rendered_layers.append(
                LayerRenderingResult(
                    layer=layer,
                    spherical=spherical,
                    projected=projected,
                    artists=artists,
                )
            )

        return ChartRenderingResult(
            projection=projection,
            renderer=renderer,
            viewport=viewport,
            layers=tuple(rendered_layers),
        )

    @staticmethod
    def _layer_render_options(layer, options):
        # Object-specific configuration takes precedence over the shared
        # layer name. Identity comparison also supports unhashable layers.
        for key, value in options.items():
            if key is layer:
                return dict(value)
        name = getattr(layer, "layer_name", None)
        if name in options:
            return dict(options[name])
        return {}

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
        self.point_renderer = CelestialPointsRenderingAdapter(
            points=self.points,
            observer=self.observer,
        )
        self.add(self.points)
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
            stars=self.stars,
            star_renderer=self.star_renderer,
            observer=self.observer,
            system=system,
            lines_file=lines_file,
            selected=selected,
        )

        self.constellation_lines = self.constellations.lines
        self.add(self.constellation_lines)

        if self.constellation_boundaries is not None:
            self.constellations.set_boundaries(
                self.constellation_boundaries,
                renderer=self.constellation_boundary_renderer,
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
        renderer_names = {
            "color",
            "linewidth",
            "alpha",
            "zorder",
            "horizon_altitude",
        }
        renderer_kwargs = {
            name: kwargs.pop(name)
            for name in tuple(kwargs)
            if name in renderer_names
        }

        boundary_layer = ConstellationBoundaries(
            observer=self.observer,
            boundaries=boundaries,
            filename=filename,
            constellations=constellations,
            **kwargs,
        )

        self.constellation_boundaries = boundary_layer
        self.constellation_boundary_renderer = (
            ConstellationBoundaryRenderingAdapter(
                boundaries=boundary_layer,
                observer=self.observer,
                **renderer_kwargs,
            )
        )
        self.add(boundary_layer)

        if self.constellations is None:
            raise RuntimeError(
                "Call add_constellations() before "
                "add_constellation_boundaries()."
            )

        self.constellations.set_boundaries(
            boundary_layer,
            renderer=self.constellation_boundary_renderer,
        )

        return boundary_layer

# ----------------------------
# Coordinate-grid layer helpers
# ----------------------------

    def add_equatorial_grid(
        self,
        *,
        ra=None,
        dec=None,
        include_equator=False,
        frame="fk5",
        equinox="of_date",
        samples=721,
    ):
        layer = EquatorialGrid(
            observer=self.observer,
            frame=frame,
            equinox=equinox,
            samples=samples,
            ra=ra,
            dec=dec,
            include_equator=include_equator,
        )
        self.add(layer)
        return layer

    def add_ecliptic_grid(
        self,
        *,
        longitude=None,
        latitude=None,
        include_ecliptic=False,
        equinox="of_date",
        samples=721,
    ):
        layer = EclipticGrid(
            observer=self.observer,
            equinox=equinox,
            samples=samples,
            longitude=longitude,
            latitude=latitude,
            include_ecliptic=include_ecliptic,
        )
        self.add(layer)
        return layer

    def add_galactic_grid(
        self,
        *,
        longitude=None,
        latitude=None,
        include_plane=False,
        samples=721,
    ):
        layer = GalacticGrid(
            observer=self.observer,
            samples=samples,
            longitude=longitude,
            latitude=latitude,
            include_plane=include_plane,
        )
        self.add(layer)
        return layer

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

        geometry = grid.equator()

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_curves(
            ax=ax,
            projection=projection,
            geometry=geometry,
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

        geometry = grid.parallel(
            declination_deg=declination_deg,
        )

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_curves(
            ax=ax,
            projection=projection,
            geometry=geometry,
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

        geometry = grid.meridian(
            right_ascension_deg=right_ascension_deg,
        )

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_curves(
            ax=ax,
            projection=projection,
            geometry=geometry,
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

        geometry = grid.grid(
            ra=ra,
            dec=dec,
            meridian_style=resolved_meridian_style,
            parallel_style=resolved_parallel_style,
        )

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_grid(
            ax=ax,
            projection=projection,
            geometry=geometry,
            min_altitude=min_altitude,
        )

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

        geometry = grid.ecliptic()

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_curves(
            ax=ax,
            projection=projection,
            geometry=geometry,
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

        geometry = grid.parallel(
            latitude_deg=latitude_deg,
        )

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_curves(
            ax=ax,
            projection=projection,
            geometry=geometry,
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

        geometry = grid.meridian(
            longitude_deg=longitude_deg,
        )

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_curves(
            ax=ax,
            projection=projection,
            geometry=geometry,
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

        geometry = grid.grid(
            longitude=longitude,
            latitude=latitude,
            meridian_style=resolved_meridian_style,
            parallel_style=resolved_parallel_style,
        )

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_grid(
            ax=ax,
            projection=projection,
            geometry=geometry,
            min_altitude=min_altitude,
        )

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

        geometry = grid.galactic_plane()

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_curves(
            ax=ax,
            projection=projection,
            geometry=geometry,
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

        geometry = grid.parallel(
            latitude_deg=latitude_deg,
        )

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_curves(
            ax=ax,
            projection=projection,
            geometry=geometry,
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

        geometry = grid.meridian(
            longitude_deg=longitude_deg,
        )

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_curves(
            ax=ax,
            projection=projection,
            geometry=geometry,
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

        geometry = grid.grid(
            longitude=longitude,
            latitude=latitude,
            meridian_style=resolved_meridian_style,
            parallel_style=resolved_parallel_style,
        )

        renderer = CoordinatesGridRenderingAdapter(
            observer=self.observer,
        )
        return renderer.draw_grid(
            ax=ax,
            projection=projection,
            geometry=geometry,
            min_altitude=min_altitude,
        )

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

        if self.point_renderer is not None:
            artists["points"] = self.point_renderer.draw(
                ax=ax,
                projection=projection,
            )

        return artists


