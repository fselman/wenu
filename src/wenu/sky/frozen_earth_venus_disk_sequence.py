"""Drawable frozen-Earth Venus sequence in fixed J2000 ecliptic axes."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalPoints,
    SphericalPolygons,
)
from wenu.sky.frozen_earth_disk_sequences import (
    FrozenEarthDiskSequence,
    FrozenEarthDiskSequenceRealizer,
    FrozenEarthDiskSequenceRequest,
)
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.sky_layer import SkyLayer
from wenu.solar_system_disk_geometry import SolarSystemDiskGeometryRealizer


@dataclass(frozen=True)
class FrozenEarthVenusDiskSequenceGeometry:
    """Ordinary spherical components plus the fixed Sun direction."""

    physical: FrozenEarthDiskSequence
    centres: SphericalPoints
    limbs: SphericalCurves
    terminators: SphericalCurves
    illuminated_faces: SphericalPolygons
    sun: SphericalPoints


def _metadata(sequence):
    return {
        "sequence_model": "frozen-earth-ecliptic",
        "direction_semantics": "frozen-observer geometric; not apparent",
        "sample_instants": sequence.sample_instants,
        "distances": tuple(
            disk.direction.distance_au for disk in sequence.disks
        ),
        "distance_origin": sequence.distance_origin,
        "distance_unit": sequence.distance_unit,
        "frozen_earth_heliocentric_icrf_au": tuple(
            sequence.frozen_earth_state.position
        ),
        "provenance": sequence.provenance,
    }


def _combine(sequence, geometries):
    spec = sequence.sun_direction.coordinate_spec
    labels = np.asarray(
        tuple(value[:10] for value in sequence.sample_instants),
        dtype=object,
    )
    ids = np.asarray(
        tuple(
            f"venus_{value[:10].replace('-', '_')}"
            for value in sequence.sample_instants
        ),
        dtype=object,
    )
    metadata = _metadata(sequence)
    return FrozenEarthVenusDiskSequenceGeometry(
        physical=sequence,
        centres=SphericalPoints(
            np.asarray(tuple(item.centre.lon_deg[0] for item in geometries)),
            np.asarray(tuple(item.centre.lat_deg[0] for item in geometries)),
            coordinate_spec=spec,
            ids=ids,
            labels=labels,
            names=labels,
            metadata=metadata,
        ),
        limbs=SphericalCurves(
            tuple(item.limb.lon_deg[0] for item in geometries),
            tuple(item.limb.lat_deg[0] for item in geometries),
            coordinate_spec=spec,
            closed=np.ones(len(geometries), dtype=bool),
            ids=ids,
            names=labels,
            metadata=metadata,
        ),
        terminators=SphericalCurves(
            tuple(item.terminator.lon_deg[0] for item in geometries),
            tuple(item.terminator.lat_deg[0] for item in geometries),
            coordinate_spec=spec,
            ids=ids,
            names=labels,
            metadata=metadata,
        ),
        illuminated_faces=SphericalPolygons(
            tuple(item.illuminated_face.lon_deg[0] for item in geometries),
            tuple(item.illuminated_face.lat_deg[0] for item in geometries),
            coordinate_spec=spec,
            ids=ids,
            names=labels,
            metadata=metadata,
        ),
        sun=SphericalPoints(
            sequence.sun_direction.lon_deg.copy(),
            sequence.sun_direction.lat_deg.copy(),
            coordinate_spec=spec,
            ids=np.asarray(("sun",), dtype=object),
            labels=np.asarray(("Sun",), dtype=object),
            names=np.asarray(("Sun",), dtype=object),
            metadata={**metadata, "symbol": "six-point-star"},
        ),
    )


class FrozenEarthVenusDiskSequenceRealization:
    """Share one frozen construction across all drawable components."""

    def __init__(
        self,
        request,
        *,
        sequence_realizer=None,
        geometry_realizer=None,
    ):
        if not isinstance(request, FrozenEarthDiskSequenceRequest):
            raise TypeError("request must be a FrozenEarthDiskSequenceRequest.")
        self.request = request
        self.sequence_realizer = (
            sequence_realizer or FrozenEarthDiskSequenceRealizer()
        )
        self.geometry_realizer = (
            geometry_realizer or SolarSystemDiskGeometryRealizer()
        )
        self._context = self._observer = self._transformed = None

    @property
    def transformed(self):
        if self._transformed is None:
            raise RuntimeError(
                "frozen-Earth Venus sequence has not been realized."
            )
        return self._transformed

    def realize(self, context, observer):
        if not isinstance(context, LayerRealizationContext):
            raise TypeError("context must be a LayerRealizationContext.")
        spec = context.product_coordinate_spec
        if (
            spec.frame != "barycentric-mean-ecliptic"
            or spec.origin != "frozen-earth"
        ):
            raise ValueError(
                "frozen-Earth sequence requires the fixed ecliptic product "
                "frame."
            )
        if (
            self._transformed is not None
            and self._context == context
            and self._observer is observer
        ):
            return self._transformed
        sequence = self.sequence_realizer.sequence(self.request, observer=observer)
        geometries = tuple(
            self.geometry_realizer.geometry(disk)
            for disk in sequence.disks
        )
        self._transformed = _combine(sequence, geometries)
        self._context, self._observer = context, observer
        return self._transformed


class FrozenEarthVenusDiskSequenceLayer(SkyLayer):
    component = None
    layer_name = None

    def __init__(self, realization, *, magnification=1.0):
        if not isinstance(realization, FrozenEarthVenusDiskSequenceRealization):
            raise TypeError(
                "realization must be a "
                "FrozenEarthVenusDiskSequenceRealization."
            )
        magnification = float(magnification)
        if not isfinite(magnification) or not 1.0 <= magnification <= 1000.0:
            raise ValueError(
                "magnification must be finite and between 1 and 1000."
            )
        self.disk_realization = realization
        self.magnification = magnification

    def spherical_geometry(self, observer):
        del observer
        raise TypeError(
            "frozen-Earth sequence requires a typed "
            "LayerRealizationContext."
        )

    def realize(self, context, observer, **geometry_options):
        if geometry_options:
            raise TypeError("frozen-Earth sequence accepts no geometry options.")
        realized = self.disk_realization.realize(context, observer)
        return getattr(realized, self.component)


class FrozenEarthVenusSequenceIlluminatedLayer(FrozenEarthVenusDiskSequenceLayer):
    component = "illuminated_faces"
    layer_name = "venus_disk_sequence_frozen_illuminated"


class FrozenEarthVenusSequenceLimbLayer(FrozenEarthVenusDiskSequenceLayer):
    component = "limbs"
    layer_name = "venus_disk_sequence_frozen_limb"


class FrozenEarthVenusSequenceTerminatorLayer(FrozenEarthVenusDiskSequenceLayer):
    component = "terminators"
    layer_name = "venus_disk_sequence_frozen_terminator"


class FrozenEarthVenusSequenceLabelsLayer(FrozenEarthVenusDiskSequenceLayer):
    component = "centres"
    layer_name = "venus_disk_sequence_frozen_labels"


class FrozenEarthSunSymbolLayer(FrozenEarthVenusDiskSequenceLayer):
    component = "sun"
    layer_name = "frozen_earth_sun"


def frozen_earth_venus_disk_sequence_layers(
    request,
    *,
    magnification=1.0,
    label_dates=False,
):
    """Return the fixed-Sun symbol and shared frozen Venus components."""
    realization = FrozenEarthVenusDiskSequenceRealization(request)
    layers = [
        FrozenEarthVenusSequenceIlluminatedLayer(
            realization, magnification=magnification
        ),
        FrozenEarthVenusSequenceLimbLayer(
            realization, magnification=magnification
        ),
        FrozenEarthVenusSequenceTerminatorLayer(
            realization, magnification=magnification
        ),
    ]
    if label_dates:
        layers.append(
            FrozenEarthVenusSequenceLabelsLayer(
                realization, magnification=magnification
            )
        )
    layers.append(FrozenEarthSunSymbolLayer(realization, magnification=1.0))
    return tuple(layers)
