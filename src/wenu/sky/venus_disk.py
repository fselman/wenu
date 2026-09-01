"""Generic request-owned resolved-body disk component layers."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from wenu.coordinate_service import CoordinateService
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.sky_layer import SkyLayer
from wenu.sky.solar_system_bodies import (
    RESOLVED_SPHERICAL_DISK,
    SolarSystemBodyDescriptor,
)
from wenu.sky.venus import VENUS_POINT, VENUS_RADIUS_MODEL
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_appearance import SolarSystemAppearanceRealizer
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)
from wenu.solar_system_disk_geometry import (
    SolarSystemDiskGeometry,
    SolarSystemDiskGeometryRealizer,
)


@dataclass(frozen=True)
class TransformedSolarSystemDiskGeometry:
    """Physical disk components transformed into one chart product frame."""

    physical: SolarSystemDiskGeometry
    centre: object
    limb: object
    terminator: object
    illuminated_face: object


class SolarSystemDiskRealization:
    """Realize one body appearance and share it across component layers."""

    def __init__(
        self,
        descriptor,
        *,
        source_factory=SkyfieldEphemerisStateSource.from_observer,
        observer_state_factory=skyfield_observer_barycentric_state,
        astrometric_realizer=None,
        apparent_realizer=None,
        appearance_realizer=None,
        disk_realizer=None,
        coordinate_service=None,
    ):
        if not isinstance(descriptor, SolarSystemBodyDescriptor):
            raise TypeError("descriptor must be a SolarSystemBodyDescriptor.")
        if not descriptor.supports(RESOLVED_SPHERICAL_DISK):
            raise ValueError(
                f"{descriptor.display_name} does not support resolved disks."
            )
        self.descriptor = descriptor
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
        self.appearance_realizer = (
            SolarSystemAppearanceRealizer()
            if appearance_realizer is None else appearance_realizer
        )
        self.disk_realizer = (
            SolarSystemDiskGeometryRealizer()
            if disk_realizer is None else disk_realizer
        )
        self.coordinate_service = (
            CoordinateService()
            if coordinate_service is None else coordinate_service
        )
        self._context = None
        self._observer = None
        self._transformed = None

    @property
    def transformed(self):
        """Return the shared transformed state after component realization."""
        if self._transformed is None:
            raise RuntimeError(
                f"{self.descriptor.display_name} disk has not been realized."
            )
        return self._transformed

    def realize(self, context, observer):
        if not isinstance(context, LayerRealizationContext):
            raise TypeError(
                "context must be a LayerRealizationContext."
            )
        if context.observation is None:
            raise ValueError(
                f"resolved {self.descriptor.display_name} requires an "
                "observation context."
            )
        if (
            context.evaluation_instant is None
            or context.evaluation_time_scale is None
        ):
            raise ValueError(
                f"resolved {self.descriptor.display_name} requires an "
                "evaluation instant and "
                "time scale."
            )
        if (
            self._transformed is not None
            and self._context == context
            and self._observer is observer
        ):
            return self._transformed

        source = self.source_factory(observer)
        observer_state = self.observer_state_factory(
            observer,
            source=source,
        )
        body_request = AstrometricDirectionRequest(
            target=self.descriptor.target,
            centre=self.descriptor.centre,
            reception_instant=context.evaluation_instant,
            reception_time_scale=context.evaluation_time_scale,
        )
        sun_request = AstrometricDirectionRequest(
            target="sun",
            centre=self.descriptor.centre,
            reception_instant=context.evaluation_instant,
            reception_time_scale=context.evaluation_time_scale,
        )
        body_astrometric = self.astrometric_realizer.direction(
            source,
            body_request,
            observer_state,
        )
        sun_astrometric = self.astrometric_realizer.direction(
            source,
            sun_request,
            observer_state,
        )
        body_apparent = self.apparent_realizer.direction(
            body_astrometric,
            observer=observer,
            source=source,
            policy=self.descriptor.correction_policy,
        )
        sun_apparent = self.apparent_realizer.direction(
            sun_astrometric,
            observer=observer,
            source=source,
            policy=ApparentCorrectionPolicy(),
        )
        appearance = self.appearance_realizer.appearance(
            source,
            body_apparent,
            sun_apparent,
            display_name=self.descriptor.display_name,
            physical_radius_km=self.descriptor.physical_radius_km,
            radius_model=self.descriptor.radius_model,
        )
        physical = self.disk_realizer.geometry(appearance)
        target = context.product_coordinate_spec
        observation = context.observation
        transformed = TransformedSolarSystemDiskGeometry(
            physical=physical,
            centre=self.coordinate_service.transform(
                physical.centre,
                target,
                observation,
            ),
            limb=self.coordinate_service.transform(
                physical.limb,
                target,
                observation,
            ),
            terminator=self.coordinate_service.transform(
                physical.terminator,
                target,
                observation,
            ),
            illuminated_face=self.coordinate_service.transform(
                physical.illuminated_face,
                target,
                observation,
            ),
        )
        self._context = context
        self._observer = observer
        self._transformed = transformed
        return transformed


class SolarSystemDiskComponentLayer(SkyLayer):
    """Expose one independently styled component of a shared body disk."""

    component = None
    layer_name = None

    def __init__(self, realization, *, magnification=1.0):
        if not isinstance(realization, SolarSystemDiskRealization):
            raise TypeError(
                "realization must be a SolarSystemDiskRealization."
            )
        magnification = float(magnification)
        if not isfinite(magnification) or not 1.0 <= magnification <= 1000.0:
            raise ValueError(
                "magnification must be finite and between 1 and 1000."
            )
        self.disk_realization = realization
        self.body_descriptor = realization.descriptor
        self.magnification = magnification
        self.component_role = self.component
        self.display_kind = "resolved_disk"
        self.layer_name = (
            f"{self.body_descriptor.entity_key}_disk_{self.component_role}"
        )

    def spherical_geometry(self, observer):
        del observer
        raise TypeError(
            f"resolved {self.body_descriptor.display_name} requires a typed "
            "LayerRealizationContext."
        )

    def realize(self, context, observer, **geometry_options):
        if geometry_options:
            raise TypeError(
                "resolved body components accept no geometry options."
            )
        result = self.disk_realization.realize(context, observer)
        return getattr(result, self.component)


class SolarSystemDiskIlluminatedLayer(SolarSystemDiskComponentLayer):
    """Illuminated Venus face polygon."""

    component = "illuminated"

    def realize(self, context, observer, **geometry_options):
        if geometry_options:
            raise TypeError(
                "resolved body components accept no geometry options."
            )
        return self.disk_realization.realize(
            context, observer
        ).illuminated_face


class SolarSystemDiskLimbLayer(SolarSystemDiskComponentLayer):
    """Closed physical Venus limb."""

    component = "limb"


class SolarSystemDiskTerminatorLayer(SolarSystemDiskComponentLayer):
    """Visible Venus day-night terminator."""

    component = "terminator"


def solar_system_disk_layers(descriptor, *, magnification=1.0):
    """Return generic face, limb, and terminator layers for one body."""
    realization = SolarSystemDiskRealization(descriptor)
    return (
        SolarSystemDiskIlluminatedLayer(
            realization, magnification=magnification
        ),
        SolarSystemDiskLimbLayer(realization, magnification=magnification),
        SolarSystemDiskTerminatorLayer(
            realization, magnification=magnification
        ),
    )


def venus_disk_layers(*, magnification=1.0):
    """Compatibility factory for the accepted Venus public output."""
    return solar_system_disk_layers(VENUS_POINT, magnification=magnification)


VenusDiskRealization = SolarSystemDiskRealization
VenusDiskComponentLayer = SolarSystemDiskComponentLayer
VenusDiskIlluminatedLayer = SolarSystemDiskIlluminatedLayer
VenusDiskLimbLayer = SolarSystemDiskLimbLayer
VenusDiskTerminatorLayer = SolarSystemDiskTerminatorLayer
