"""Shared renderer-neutral orchestration for symbolic Solar-System points."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from wenu.coordinate_service import CoordinateService
from wenu.antisolar import (
    angular_separation_deg,
    antisolar_position_angle_deg,
    antisolar_reference_direction,
    MINIMUM_ANTISOLAR_SEPARATION_DEG,
)
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
class EphemerisSourceBinding:
    """Target-state source paired with its observer/apparent source."""

    target_source: object
    observer_source: object


def skyfield_source_binding(descriptor, observer):
    """Resolve the ordinary one-source Skyfield binding."""
    del descriptor
    source = SkyfieldEphemerisStateSource.from_observer(observer)
    return EphemerisSourceBinding(source, source)


def _primary_resource_sha256(resource):
    digest = getattr(resource, "sha256", None)
    if digest is None:
        digest = resource.primary.sha256
    return digest


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
        source_factory=None,
        source_resolver=None,
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
        if source_factory is not None and source_resolver is not None:
            raise ValueError(
                "supply source_factory or source_resolver, not both."
            )
        self.source_factory = source_factory
        self.source_resolver = source_resolver
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

        if self.source_resolver is not None:
            binding = self.source_resolver(self.descriptor, observer)
        elif self.source_factory is not None:
            source = self.source_factory(observer)
            binding = EphemerisSourceBinding(source, source)
        else:
            binding = skyfield_source_binding(self.descriptor, observer)
        if not isinstance(binding, EphemerisSourceBinding):
            raise TypeError(
                "source_resolver must return an EphemerisSourceBinding."
            )
        source = binding.target_source
        observer_source = binding.observer_source
        observer_state = self.observer_state_factory(
            observer,
            source=observer_source,
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
            source=observer_source,
            policy=self.descriptor.correction_policy,
        )
        native = apparent.geometry
        is_comet = getattr(self.descriptor, "body_class", None) == "comet"
        lon_deg = np.asarray(native.lon_deg)
        lat_deg = np.asarray(native.lat_deg)
        entity_keys = (self.descriptor.entity_key,)
        display_names = (self.descriptor.display_name,)
        labels = (
            getattr(self.descriptor, "astronomical_symbol", None)
            or getattr(self.descriptor, "canonical_designation", None)
            or self.descriptor.display_name,
        )
        orientation_metadata = {}
        if is_comet:
            sun_request = AstrometricDirectionRequest(
                target="sun",
                centre=self.descriptor.centre,
                reception_instant=context.evaluation_instant,
                reception_time_scale=context.evaluation_time_scale,
            )
            sun_astrometric = self.astrometric_realizer.direction(
                observer_source,
                sun_request,
                observer_state,
            )
            sun_apparent = self.apparent_realizer.direction(
                sun_astrometric,
                observer=observer,
                source=observer_source,
                policy=self.descriptor.correction_policy,
            ).geometry
            comet_direction = (float(lon_deg[0]), float(lat_deg[0]))
            sun_direction = (
                float(sun_apparent.lon_deg[0]),
                float(sun_apparent.lat_deg[0]),
            )
            separation = angular_separation_deg(
                comet_direction, sun_direction
            )
            tail_suppressed = (
                separation < MINIMUM_ANTISOLAR_SEPARATION_DEG
                or separation
                > 180.0 - MINIMUM_ANTISOLAR_SEPARATION_DEG
            )
            if not tail_suppressed:
                reference = antisolar_reference_direction(
                    comet_direction, sun_direction
                )
                lon_deg = np.asarray((comet_direction[0], reference[0]))
                lat_deg = np.asarray((comet_direction[1], reference[1]))
                entity_keys = (
                    self.descriptor.entity_key,
                    f"{self.descriptor.entity_key}__antisolar_reference",
                )
                display_names = (self.descriptor.display_name, None)
                labels = (labels[0], None)
            orientation_metadata = {
                "comet_tail_suppressed": tail_suppressed,
                "apparent_sun_comet_separation_deg": separation,
                "comet_symbol_orientation_reference_index": (
                    None if tail_suppressed else 1
                ),
                "antisolar_position_angle_deg": (
                    None if tail_suppressed else antisolar_position_angle_deg(
                        comet_direction, sun_direction
                    )
                ),
                "sun_apparent_icrf_deg": sun_direction,
            }
        identified = SphericalPoints(
            lon_deg,
            lat_deg,
            coordinate_spec=native.coordinate_spec,
            ids=np.asarray(entity_keys, dtype=object),
            labels=np.asarray(labels, dtype=object),
            names=np.asarray(display_names, dtype=object),
            metadata={
                **native.metadata,
                "semantic_entity_keys": np.asarray(
                    entity_keys,
                    dtype=object,
                ),
                "semantic_entity_display_names": np.asarray(
                    display_names,
                    dtype=object,
                ),
                "ephemeris_sha256": _primary_resource_sha256(
                    source.resource
                ),
                "apparent_provenance": tuple(
                    native.coordinate_spec.provenance
                ),
                **orientation_metadata,
            },
        )
        return self.coordinate_service.transform(
            identified,
            context.product_coordinate_spec,
            context.observation,
        )
