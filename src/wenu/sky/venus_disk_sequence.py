"""Drawable observed Venus disk sequence in one fixed chart frame."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from wenu.coordinate_service import CoordinateService
from wenu.geometry.spherical import SphericalCurves, SphericalPoints, SphericalPolygons
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.sky_layer import SkyLayer
from wenu.sky.solar_system_disk_sequences import (
    ObservedSolarSystemDiskSequence,
    ObservedSolarSystemDiskSequenceRealizer,
    ObservedSolarSystemDiskSequenceRequest,
)


@dataclass(frozen=True)
class TransformedObservedDiskSequence:
    """Independent physical samples transformed into one product frame."""

    physical: ObservedSolarSystemDiskSequence
    centres: SphericalPoints
    limbs: SphericalCurves
    terminators: SphericalCurves
    illuminated_faces: SphericalPolygons


@dataclass(frozen=True)
class _TransformedDiskSample:
    centre: SphericalPoints
    limb: SphericalCurves
    terminator: SphericalCurves
    illuminated_face: SphericalPolygons


def _metadata(sequence):
    return {
        "sample_instants": sequence.sample_instants,
        "sample_time_scale": sequence.sample_time_scale,
        "distances": sequence.distances,
        "distance_origin": sequence.distance_origin,
        "distance_unit": sequence.distance_unit,
        "provenance": sequence.provenance,
    }


def _sample_ids(sequence):
    return np.asarray(
        tuple(
            f"venus_{instant[:10].replace('-', '_')}"
            for instant in sequence.sample_instants
        ),
        dtype=object,
    )


def _combine(sequence, transformed):
    if not transformed:
        raise ValueError("an observed disk sequence requires at least one sample.")
    spec = transformed[0].centre.coordinate_spec
    ids = _sample_ids(sequence)
    labels = np.asarray(
        tuple(value[:10] for value in sequence.sample_instants),
        dtype=object,
    )
    metadata = _metadata(sequence)
    return TransformedObservedDiskSequence(
        physical=sequence,
        centres=SphericalPoints(
            np.asarray(tuple(item.centre.lon_deg[0] for item in transformed)),
            np.asarray(tuple(item.centre.lat_deg[0] for item in transformed)),
            coordinate_spec=spec,
            ids=ids,
            labels=labels,
            names=labels,
            metadata=metadata,
        ),
        limbs=SphericalCurves(
            tuple(item.limb.lon_deg[0] for item in transformed),
            tuple(item.limb.lat_deg[0] for item in transformed),
            coordinate_spec=spec,
            closed=np.ones(len(transformed), dtype=bool),
            ids=ids,
            names=labels,
            metadata=metadata,
        ),
        terminators=SphericalCurves(
            tuple(item.terminator.lon_deg[0] for item in transformed),
            tuple(item.terminator.lat_deg[0] for item in transformed),
            coordinate_spec=spec,
            ids=ids,
            names=labels,
            metadata=metadata,
        ),
        illuminated_faces=SphericalPolygons(
            tuple(item.illuminated_face.lon_deg[0] for item in transformed),
            tuple(item.illuminated_face.lat_deg[0] for item in transformed),
            coordinate_spec=spec,
            ids=ids,
            names=labels,
            metadata=metadata,
        ),
    )


class ObservedVenusDiskSequenceRealization:
    """Share one independently sampled sequence across display components."""

    def __init__(self, request, *, sequence_realizer=None, coordinate_service=None):
        if not isinstance(request, ObservedSolarSystemDiskSequenceRequest):
            raise TypeError(
                "request must be an ObservedSolarSystemDiskSequenceRequest."
            )
        self.request = request
        self.sequence_realizer = (
            sequence_realizer or ObservedSolarSystemDiskSequenceRealizer()
        )
        self.coordinate_service = coordinate_service or CoordinateService()
        self._context = self._observer = self._transformed = None

    @property
    def transformed(self):
        if self._transformed is None:
            raise RuntimeError("observed Venus disk sequence has not been realized.")
        return self._transformed

    def realize(self, context, observer):
        if not isinstance(context, LayerRealizationContext):
            raise TypeError("context must be a LayerRealizationContext.")
        if context.observation is None:
            raise ValueError(
                "observed Venus disk sequence requires an observation context."
            )
        if (
            self._transformed is not None
            and self._context == context
            and self._observer is observer
        ):
            return self._transformed
        sequence = self.sequence_realizer.sequence(self.request, observer=observer)
        target = context.product_coordinate_spec
        observation = context.observation
        samples = []
        for geometry in sequence.geometries:
            samples.append(_TransformedDiskSample(
                centre=self.coordinate_service.transform(
                    geometry.centre, target, observation
                ),
                limb=self.coordinate_service.transform(
                    geometry.limb, target, observation
                ),
                terminator=self.coordinate_service.transform(
                    geometry.terminator, target, observation
                ),
                illuminated_face=self.coordinate_service.transform(
                    geometry.illuminated_face, target, observation
                ),
            ))
        self._transformed = _combine(sequence, tuple(samples))
        self._context, self._observer = context, observer
        return self._transformed


class ObservedVenusDiskSequenceLayer(SkyLayer):
    component = None
    layer_name = None

    def __init__(self, realization, *, magnification=1.0):
        if not isinstance(realization, ObservedVenusDiskSequenceRealization):
            raise TypeError(
                "realization must be an "
                "ObservedVenusDiskSequenceRealization."
            )
        magnification = float(magnification)
        if not isfinite(magnification) or not 1.0 <= magnification <= 1000.0:
            raise ValueError("magnification must be finite and between 1 and 1000.")
        self.disk_realization = realization
        self.magnification = magnification

    def spherical_geometry(self, observer):
        del observer
        raise TypeError(
            "observed Venus disk sequence requires a typed "
            "LayerRealizationContext."
        )

    def realize(self, context, observer, **geometry_options):
        if geometry_options:
            raise TypeError("observed Venus disk sequence accepts no geometry options.")
        return getattr(self.disk_realization.realize(context, observer), self.component)


class ObservedVenusDiskSequenceIlluminatedLayer(ObservedVenusDiskSequenceLayer):
    component = "illuminated_faces"
    layer_name = "venus_disk_sequence_illuminated"


class ObservedVenusDiskSequenceLimbLayer(ObservedVenusDiskSequenceLayer):
    component = "limbs"
    layer_name = "venus_disk_sequence_limb"


class ObservedVenusDiskSequenceTerminatorLayer(ObservedVenusDiskSequenceLayer):
    component = "terminators"
    layer_name = "venus_disk_sequence_terminator"


class ObservedVenusDiskSequenceLabelsLayer(ObservedVenusDiskSequenceLayer):
    component = "centres"
    layer_name = "venus_disk_sequence_labels"


def observed_venus_disk_sequence_layers(
    request,
    *,
    magnification=1.0,
    label_dates=False,
):
    """Return ordered component layers sharing one observed sequence."""
    realization = ObservedVenusDiskSequenceRealization(request)
    layers = [
        ObservedVenusDiskSequenceIlluminatedLayer(
            realization, magnification=magnification
        ),
        ObservedVenusDiskSequenceLimbLayer(realization, magnification=magnification),
        ObservedVenusDiskSequenceTerminatorLayer(
            realization, magnification=magnification
        ),
    ]
    if label_dates:
        layers.append(
            ObservedVenusDiskSequenceLabelsLayer(
                realization, magnification=magnification
            )
        )
    return tuple(layers)
