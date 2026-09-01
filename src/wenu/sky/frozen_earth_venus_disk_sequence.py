"""Generic drawable frozen-Earth body sequence in fixed ecliptic axes."""

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
class FrozenEarthSolarSystemDiskSequenceGeometry:
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
            f"{sequence.request.descriptor.entity_key}_"
            f"{value[:10].replace('-', '_')}"
            for value in sequence.sample_instants
        ),
        dtype=object,
    )
    metadata = _metadata(sequence)
    return FrozenEarthSolarSystemDiskSequenceGeometry(
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


class FrozenEarthSolarSystemDiskSequenceRealization:
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
                "frozen-Earth body sequence has not been realized."
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


class FrozenEarthSolarSystemDiskSequenceLayer(SkyLayer):
    component = None
    component_role = None

    def __init__(self, realization, *, magnification=1.0):
        if not isinstance(
            realization, FrozenEarthSolarSystemDiskSequenceRealization
        ):
            raise TypeError(
                "realization must be a "
                "FrozenEarthSolarSystemDiskSequenceRealization."
            )
        magnification = float(magnification)
        if not isfinite(magnification) or not 1.0 <= magnification <= 1000.0:
            raise ValueError(
                "magnification must be finite and between 1 and 1000."
            )
        self.disk_realization = realization
        self.body_descriptor = realization.request.descriptor
        self.magnification = magnification
        self.display_kind = "frozen_earth_disk_sequence"
        if self.component_role == "sun":
            self.layer_name = "frozen_earth_sun"
        else:
            self.layer_name = (
                f"{self.body_descriptor.entity_key}_disk_sequence_frozen_"
                f"{self.component_role}"
            )

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


class FrozenEarthSolarSystemSequenceIlluminatedLayer(
    FrozenEarthSolarSystemDiskSequenceLayer
):
    component = "illuminated_faces"
    component_role = "illuminated"


class FrozenEarthSolarSystemSequenceLimbLayer(
    FrozenEarthSolarSystemDiskSequenceLayer
):
    component = "limbs"
    component_role = "limb"


class FrozenEarthSolarSystemSequenceTerminatorLayer(
    FrozenEarthSolarSystemDiskSequenceLayer
):
    component = "terminators"
    component_role = "terminator"


class FrozenEarthSolarSystemSequenceLabelsLayer(
    FrozenEarthSolarSystemDiskSequenceLayer
):
    component = "centres"
    component_role = "labels"


class FrozenEarthSunSymbolLayer(FrozenEarthSolarSystemDiskSequenceLayer):
    component = "sun"
    component_role = "sun"


def frozen_earth_solar_system_disk_sequence_layers(
    request,
    *,
    magnification=1.0,
    label_dates=False,
):
    """Return the fixed Sun and generic shared body-disk components."""
    realization = FrozenEarthSolarSystemDiskSequenceRealization(request)
    layers = [
        FrozenEarthSolarSystemSequenceIlluminatedLayer(
            realization, magnification=magnification
        ),
        FrozenEarthSolarSystemSequenceLimbLayer(
            realization, magnification=magnification
        ),
        FrozenEarthSolarSystemSequenceTerminatorLayer(
            realization, magnification=magnification
        ),
    ]
    if label_dates:
        layers.append(
            FrozenEarthSolarSystemSequenceLabelsLayer(
                realization, magnification=magnification
            )
        )
    layers.append(FrozenEarthSunSymbolLayer(realization, magnification=1.0))
    return tuple(layers)


def frozen_earth_venus_disk_sequence_layers(request, **options):
    """Compatibility factory preserving accepted Venus public output."""
    return frozen_earth_solar_system_disk_sequence_layers(request, **options)


FrozenEarthVenusDiskSequenceGeometry = FrozenEarthSolarSystemDiskSequenceGeometry
FrozenEarthVenusDiskSequenceRealization = (
    FrozenEarthSolarSystemDiskSequenceRealization
)
FrozenEarthVenusDiskSequenceLayer = FrozenEarthSolarSystemDiskSequenceLayer
FrozenEarthVenusSequenceIlluminatedLayer = (
    FrozenEarthSolarSystemSequenceIlluminatedLayer
)
FrozenEarthVenusSequenceLimbLayer = FrozenEarthSolarSystemSequenceLimbLayer
FrozenEarthVenusSequenceTerminatorLayer = (
    FrozenEarthSolarSystemSequenceTerminatorLayer
)
FrozenEarthVenusSequenceLabelsLayer = FrozenEarthSolarSystemSequenceLabelsLayer
