"""Shared renderer-neutral orchestration for symbolic Solar-System points."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from wenu.coordinate_service import CoordinateService
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.sky_layer import SkyLayer
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)


def _text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty.")
    return normalized


@dataclass(frozen=True)
class SolarSystemPointDescriptor:
    """Stable body identity and direction policy for one symbolic point."""

    target: str
    entity_key: str
    display_name: str
    selection_key: str
    centre: str = "solar system barycenter"
    correction_policy: ApparentCorrectionPolicy = field(
        default_factory=ApparentCorrectionPolicy
    )

    def __post_init__(self):
        for name in (
            "target",
            "entity_key",
            "display_name",
            "selection_key",
            "centre",
        ):
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name=name),
            )
        if not isinstance(
            self.correction_policy,
            ApparentCorrectionPolicy,
        ):
            raise TypeError(
                "correction_policy must be an ApparentCorrectionPolicy."
            )


class SolarSystemPointLayer(SkyLayer):
    """Realize one apparent body direction before ordinary projection."""

    def __init__(
        self,
        descriptor,
        *,
        source_factory=SkyfieldEphemerisStateSource.from_observer,
        observer_state_factory=skyfield_observer_barycentric_state,
        astrometric_realizer=None,
        apparent_realizer=None,
        coordinate_service=None,
    ):
        if not isinstance(descriptor, SolarSystemPointDescriptor):
            raise TypeError(
                "descriptor must be a SolarSystemPointDescriptor."
            )
        self.descriptor = descriptor
        self.layer_name = descriptor.entity_key
        if hasattr(descriptor, "body_class"):
            self.body_descriptor = descriptor
            self.display_kind = "symbolic_point"
        self.source_factory = source_factory
        self.observer_state_factory = observer_state_factory
        self.astrometric_realizer = (
            AstrometricDirectionRealizer()
            if astrometric_realizer is None else astrometric_realizer
        )
        self.apparent_realizer = (
            SkyfieldApparentDirectionRealizer()
            if apparent_realizer is None else apparent_realizer
        )
        self.coordinate_service = (
            CoordinateService()
            if coordinate_service is None else coordinate_service
        )

    def spherical_geometry(self, observer):
        del observer
        raise TypeError(
            f"{self.descriptor.display_name} requires a typed "
            "LayerRealizationContext."
        )

    def realize(self, context, observer, **geometry_options):
        selected = geometry_options.pop("selected", None)
        if (
            selected is not None
            and self.descriptor.selection_key not in frozenset(selected)
        ):
            raise ValueError(
                f"{self.descriptor.display_name} selection must contain "
                f"{self.descriptor.selection_key}."
            )
        if geometry_options:
            raise TypeError(
                f"{self.descriptor.display_name} accepts no geometry options."
            )
        if not isinstance(context, LayerRealizationContext):
            raise TypeError(
                "context must be a LayerRealizationContext."
            )
        if context.observation is None:
            raise ValueError(
                f"{self.descriptor.display_name} requires an "
                "observation context."
            )
        if (
            context.evaluation_instant is None
            or context.evaluation_time_scale is None
        ):
            raise ValueError(
                f"{self.descriptor.display_name} requires an evaluation "
                "instant and time scale."
            )

        source = self.source_factory(observer)
        observer_state = self.observer_state_factory(
            observer,
            source=source,
        )
        request = AstrometricDirectionRequest(
            target=self.descriptor.target,
            centre=self.descriptor.centre,
            reception_instant=context.evaluation_instant,
            reception_time_scale=context.evaluation_time_scale,
        )
        astrometric = self.astrometric_realizer.direction(
            source,
            request,
            observer_state,
        )
        apparent = self.apparent_realizer.direction(
            astrometric,
            observer=observer,
            source=source,
            policy=self.descriptor.correction_policy,
        )
        native = apparent.geometry
        identified = SphericalPoints(
            native.lon_deg,
            native.lat_deg,
            coordinate_spec=native.coordinate_spec,
            ids=np.asarray((self.descriptor.entity_key,), dtype=object),
            labels=np.asarray(
                (
                    getattr(
                        self.descriptor,
                        "astronomical_symbol",
                        None,
                    ) or self.descriptor.display_name,
                ),
                dtype=object,
            ),
            names=np.asarray((self.descriptor.display_name,), dtype=object),
            metadata={
                **native.metadata,
                "semantic_entity_keys": np.asarray(
                    (self.descriptor.entity_key,),
                    dtype=object,
                ),
                "semantic_entity_display_names": np.asarray(
                    (self.descriptor.display_name,),
                    dtype=object,
                ),
                "ephemeris_sha256": source.resource.sha256,
                "apparent_provenance": tuple(
                    native.coordinate_spec.provenance
                ),
            },
        )
        return self.coordinate_service.transform(
            identified,
            context.product_coordinate_spec,
            context.observation,
        )
