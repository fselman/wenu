"""Request-owned resolved Venus disk layers sharing one scientific state."""

from __future__ import annotations

from dataclasses import dataclass

from wenu.coordinate_service import CoordinateService
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.sky_layer import SkyLayer
from wenu.sky.venus import VENUS_POINT
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_appearance import (
    SolarSystemAppearanceRealizer,
    VENUS_MEAN_RADIUS_KM,
)
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)
from wenu.solar_system_disk_geometry import (
    SolarSystemDiskGeometry,
    SolarSystemDiskGeometryRealizer,
)


VENUS_RADIUS_MODEL = (
    "JPL Planetary Physical Parameters mean radius 6051.8 km"
)


@dataclass(frozen=True)
class TransformedSolarSystemDiskGeometry:
    """Physical disk components transformed into one chart product frame."""

    physical: SolarSystemDiskGeometry
    centre: object
    limb: object
    terminator: object
    illuminated_face: object


class VenusDiskRealization:
    """Realize one Venus appearance and share it across component layers."""

    def __init__(
        self,
        *,
        source_factory=SkyfieldEphemerisStateSource.from_observer,
        observer_state_factory=skyfield_observer_barycentric_state,
        astrometric_realizer=None,
        apparent_realizer=None,
        appearance_realizer=None,
        disk_realizer=None,
        coordinate_service=None,
    ):
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

    def realize(self, context, observer):
        if not isinstance(context, LayerRealizationContext):
            raise TypeError(
                "context must be a LayerRealizationContext."
            )
        if context.observation is None:
            raise ValueError(
                "resolved Venus requires an observation context."
            )
        if (
            context.evaluation_instant is None
            or context.evaluation_time_scale is None
        ):
            raise ValueError(
                "resolved Venus requires an evaluation instant and "
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
        venus_request = AstrometricDirectionRequest(
            target=VENUS_POINT.target,
            centre=VENUS_POINT.centre,
            reception_instant=context.evaluation_instant,
            reception_time_scale=context.evaluation_time_scale,
        )
        sun_request = AstrometricDirectionRequest(
            target="sun",
            centre=VENUS_POINT.centre,
            reception_instant=context.evaluation_instant,
            reception_time_scale=context.evaluation_time_scale,
        )
        venus_astrometric = self.astrometric_realizer.direction(
            source,
            venus_request,
            observer_state,
        )
        sun_astrometric = self.astrometric_realizer.direction(
            source,
            sun_request,
            observer_state,
        )
        venus_apparent = self.apparent_realizer.direction(
            venus_astrometric,
            observer=observer,
            source=source,
            policy=VENUS_POINT.correction_policy,
        )
        sun_apparent = self.apparent_realizer.direction(
            sun_astrometric,
            observer=observer,
            source=source,
            policy=ApparentCorrectionPolicy(),
        )
        appearance = self.appearance_realizer.appearance(
            source,
            venus_apparent,
            sun_apparent,
            display_name=VENUS_POINT.display_name,
            physical_radius_km=VENUS_MEAN_RADIUS_KM,
            radius_model=VENUS_RADIUS_MODEL,
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


class VenusDiskComponentLayer(SkyLayer):
    """Expose one independently styled component of a shared Venus disk."""

    component = None
    layer_name = None

    def __init__(self, realization):
        if not isinstance(realization, VenusDiskRealization):
            raise TypeError(
                "realization must be a VenusDiskRealization."
            )
        self.disk_realization = realization

    def spherical_geometry(self, observer):
        del observer
        raise TypeError(
            "resolved Venus requires a typed LayerRealizationContext."
        )

    def realize(self, context, observer, **geometry_options):
        if geometry_options:
            raise TypeError(
                "resolved Venus components accept no geometry options."
            )
        result = self.disk_realization.realize(context, observer)
        return getattr(result, self.component)


class VenusDiskIlluminatedLayer(VenusDiskComponentLayer):
    """Illuminated Venus face polygon."""

    component = "illuminated_face"
    layer_name = "venus_disk_illuminated"


class VenusDiskLimbLayer(VenusDiskComponentLayer):
    """Closed physical Venus limb."""

    component = "limb"
    layer_name = "venus_disk_limb"


class VenusDiskTerminatorLayer(VenusDiskComponentLayer):
    """Visible Venus day-night terminator."""

    component = "terminator"
    layer_name = "venus_disk_terminator"


def venus_disk_layers():
    """Return ordered face, limb, and terminator layers sharing one state."""
    realization = VenusDiskRealization()
    return (
        VenusDiskIlluminatedLayer(realization),
        VenusDiskLimbLayer(realization),
        VenusDiskTerminatorLayer(realization),
    )
