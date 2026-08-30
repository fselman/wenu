"""First renderer-neutral moving-body layer: apparent Venus."""

from __future__ import annotations

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
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)


class VenusLayer(SkyLayer):
    """Realize one apparent Venus direction before ordinary projection."""

    layer_name = "venus"

    def __init__(
        self,
        *,
        source_factory=SkyfieldEphemerisStateSource.from_observer,
        observer_state_factory=skyfield_observer_barycentric_state,
        astrometric_realizer=None,
        apparent_realizer=None,
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
        self.coordinate_service = (
            CoordinateService()
            if coordinate_service is None else coordinate_service
        )

    def spherical_geometry(self, observer):
        raise TypeError(
            "Venus requires a typed LayerRealizationContext."
        )

    def realize(self, context, observer, **geometry_options):
        selected = geometry_options.pop("selected", None)
        if selected is not None and frozenset(selected) != {"venus"}:
            raise ValueError("Venus selection must contain only venus.")
        if geometry_options:
            raise TypeError("Venus accepts no geometry options.")
        if not isinstance(context, LayerRealizationContext):
            raise TypeError(
                "context must be a LayerRealizationContext."
            )
        if context.observation is None:
            raise ValueError("Venus requires an observation context.")
        if (
            context.evaluation_instant is None
            or context.evaluation_time_scale is None
        ):
            raise ValueError(
                "Venus requires an evaluation instant and time scale."
            )

        source = self.source_factory(observer)
        observer_state = self.observer_state_factory(
            observer,
            source=source,
        )
        request = AstrometricDirectionRequest(
            target="venus",
            centre="solar system barycenter",
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
        )
        native = apparent.geometry
        identified = SphericalPoints(
            native.lon_deg,
            native.lat_deg,
            coordinate_spec=native.coordinate_spec,
            ids=np.asarray(("venus",), dtype=object),
            labels=np.asarray(("Venus",), dtype=object),
            names=np.asarray(("Venus",), dtype=object),
            metadata={
                **native.metadata,
                "semantic_entity_keys": np.asarray(
                    ("venus",), dtype=object
                ),
                "semantic_entity_display_names": np.asarray(
                    ("Venus",), dtype=object
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
