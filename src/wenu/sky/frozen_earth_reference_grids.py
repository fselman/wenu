"""Observer-independent reference geometry for frozen-Earth charts."""

from __future__ import annotations

import numpy as np

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import CoordinateSpec
from wenu.geometry.spherical import SphericalCurves, SphericalGrid
from wenu.sky.coordinate_grids import CoordinatesGrid, EquatorialGrid
from wenu.sky.realization import LayerRealizationContext


def _fixed_ecliptic_spec(value):
    if not isinstance(value, CoordinateSpec):
        raise TypeError("product_coordinate_spec must be a CoordinateSpec.")
    if (
        value.frame != "barycentric-mean-ecliptic"
        or value.origin != "frozen-earth"
    ):
        raise ValueError(
            "frozen-Earth references require the fixed ecliptic product frame."
        )
    return value


class FrozenEarthEquatorialGrid(EquatorialGrid):
    """FK5 grid transformed directly into fixed mean-ecliptic axes."""

    layer_name = "coordinates_grid"

    def __init__(self, observer, *, product_coordinate_spec, **options):
        self.product_coordinate_spec = _fixed_ecliptic_spec(
            product_coordinate_spec
        )
        super().__init__(observer, **options)

    def _coordinate_spec(self):
        return self.product_coordinate_spec

    def _grid_metadata(self):
        return {
            "coordinate_system": "equatorial",
            "output_coordinate_system": "barycentric-mean-ecliptic",
            "reference_model": "fixed-frame FK5 to mean ecliptic",
        }

    def _make_curves(
        self,
        *,
        longitude_deg,
        latitude_deg,
        names,
        closed,
        styles,
        observer=None,
    ):
        del observer
        native = SphericalCurves(
            lon_deg=tuple(
                np.asarray(value, dtype=float) for value in longitude_deg
            ),
            lat_deg=tuple(
                np.asarray(value, dtype=float) for value in latitude_deg
            ),
            coordinate_spec=self._native_coordinate_spec(),
            names=names,
            closed=closed,
            metadata={
                **self._grid_metadata(),
                "styles": tuple(
                    {} if style is None else dict(style)
                    for style in styles
                ),
            },
        )
        return CoordinateService().transform(
            native,
            self.product_coordinate_spec,
        )

    def spherical_geometry(self, observer):
        del observer
        geometry = self.grid(ra=self.ra, dec=self.dec)
        components = dict(geometry.components)
        if self.include_equator:
            components["reference"] = self.equator()
        return SphericalGrid(
            components=components,
            coordinate_spec=self.product_coordinate_spec,
            metadata=self._grid_metadata(),
        )


class FrozenEarthEclipticReference(CoordinatesGrid):
    """The latitude-zero ecliptic in the frozen product frame."""

    layer_name = "coordinates_grid"
    coordinate_system = "ecliptic"

    def __init__(self):
        super().__init__(observer=None)

    def _native_coordinate_spec(self):
        raise TypeError(
            "frozen-Earth ecliptic reference has no observer-native frame."
        )

    def spherical_geometry(self, observer):
        del observer
        raise TypeError(
            "frozen-Earth ecliptic reference requires a realization context."
        )

    def realize(self, context, observer, **geometry_options):
        del observer
        if geometry_options:
            raise TypeError(
                "frozen-Earth ecliptic reference accepts no geometry options."
            )
        if not isinstance(context, LayerRealizationContext):
            raise TypeError("context must be a LayerRealizationContext.")
        spec = _fixed_ecliptic_spec(context.product_coordinate_spec)
        longitude = np.linspace(0.0, 360.0, 721, endpoint=False)
        curves = SphericalCurves(
            lon_deg=(longitude,),
            lat_deg=(np.zeros_like(longitude),),
            coordinate_spec=spec,
            closed=np.asarray((True,)),
            names=np.asarray(("ecliptic",), dtype=object),
            metadata={
                "coordinate_system": "ecliptic",
                "output_coordinate_system": "barycentric-mean-ecliptic",
                "reference_model": "fixed product-frame latitude zero",
                "styles": ({},),
            },
        )
        return SphericalGrid(
            components={"reference": curves},
            coordinate_spec=spec,
            metadata=dict(curves.metadata),
        )
