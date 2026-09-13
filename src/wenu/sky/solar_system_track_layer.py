"""Scientific Solar-System track layer."""

from __future__ import annotations

import numpy as np

from wenu.antisolar import (
    ANTISOLAR_TANGENT_OFFSET_DEG,
    MINIMUM_ANTISOLAR_SEPARATION_DEG,
    angular_separation_deg,
    antisolar_position_angle_deg,
    offset_direction_deg,
)
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.sky_layer import SkyLayer
from wenu.sky.solar_system_points import (
    _provider_gas_tail_position_angle,
)
from wenu.sky.solar_system_tracks import (
    SolarSystemTrackRealizer,
    SolarSystemTrackRequest,
)
from wenu.solar_system_directions import AstrometricDirectionRequest


class SolarSystemTrackRealization:
    """Share one scientific track result across all display components."""

    def __init__(self, request, *, realizer=None):
        if not isinstance(request, SolarSystemTrackRequest):
            raise TypeError("request must be a SolarSystemTrackRequest.")
        self.request = request
        self.realizer = realizer or SolarSystemTrackRealizer()
        self._context = self._observer = self._result = None

    def realize(self, context, observer):
        if (
            self._result is not None
            and self._context == context
            and self._observer is observer
        ):
            return self._result
        self._result = self.realizer.curve(
            self.request, context=context, observer=observer
        )
        self._context, self._observer = context, observer
        return self._result


class SolarSystemTrackLayer(SkyLayer):
    """Realize one scientific track as an ordinary spherical curve."""

    layer_name = "solar_system_track"

    def __init__(
        self, request, *, realizer=None, realization=None,
        label_ticks=False, label_start=True, start_label_text=None,
        draw_path=True, draw_ticks=True,
    ):
        if not isinstance(request, SolarSystemTrackRequest):
            raise TypeError(
                "request must be a SolarSystemTrackRequest."
            )
        self.request = request
        if hasattr(request.descriptor, "body_class"):
            self.body_descriptor = request.descriptor
            self.display_kind = "apparent_track"
        if realizer is not None and realization is not None:
            raise ValueError("supply realizer or realization, not both.")
        self.track_realization = realization or SolarSystemTrackRealization(
            request, realizer=realizer
        )
        self.realizer = self.track_realization.realizer
        self.last_result = None
        self.label_ticks = bool(label_ticks)
        self.label_start = bool(label_start)
        self.start_label_text = start_label_text
        self.draw_path = bool(draw_path)
        self.draw_ticks = bool(draw_ticks)

    def realize(self, context, observer, **geometry_options):
        if geometry_options:
            raise TypeError(
                "SolarSystemTrackLayer accepts no geometry options."
            )
        self.last_result = self.track_realization.realize(context, observer)
        return self.last_result.geometry

    def spherical_geometry(self, observer):
        del observer
        raise RuntimeError(
            "SolarSystemTrackLayer requires a "
            "LayerRealizationContext."
        )


class SolarSystemTrackSymbolLayer(SkyLayer):
    """Place one descriptor-owned symbol from a shared track result."""

    layer_name = "solar_system_track_symbol"

    def __init__(
        self,
        realization,
        major_index,
        *,
        draw_label=False,
    ):
        if not isinstance(realization, SolarSystemTrackRealization):
            raise TypeError("realization must be a SolarSystemTrackRealization.")
        self.track_realization = realization
        self.request = realization.request
        self.major_index = int(major_index)
        if not 0 <= self.major_index <= self.request.tick_count:
            raise ValueError("major_index is outside the track major epochs.")
        self.offset_days = self.request.tick_offsets_days[self.major_index]
        self.descriptor = self.request.descriptor
        self.body_descriptor = self.descriptor
        self.display_kind = "symbolic_point"
        self.request_draw_label = bool(draw_label)

    def realize(self, context, observer, **geometry_options):
        selected = geometry_options.pop("selected", None)
        if selected is not None and self.descriptor.selection_key not in selected:
            raise ValueError("track-symbol selection must contain its body.")
        if geometry_options:
            raise TypeError("track symbol accepts no geometry options.")
        result = self.track_realization.realize(context, observer)
        sample_index = result.tick_sample_indices[self.major_index]
        instant = result.sample_instants[sample_index]
        key = f"{self.descriptor.entity_key}_{instant[:10].replace('-', '_')}"
        return SphericalPoints(
            [result.geometry.lon_deg[0][sample_index]],
            [result.geometry.lat_deg[0][sample_index]],
            coordinate_spec=result.geometry.coordinate_spec,
            ids=np.asarray((key,), dtype=object),
            labels=np.asarray((None,), dtype=object),
            names=np.asarray((self.descriptor.display_name,), dtype=object),
            metadata={
                **dict(result.geometry.metadata),
                "sample_instant": instant,
                "track_sample_index": sample_index,
            },
        )

    def spherical_geometry(self, observer):
        del observer
        raise RuntimeError(
            "SolarSystemTrackSymbolLayer requires a LayerRealizationContext."
        )


class CometTrackSymbolLayer(SolarSystemTrackSymbolLayer):
    """Specialize shared track-symbol placement with comet orientation."""

    def __init__(self, realization, major_index, **options):
        if getattr(realization.request.descriptor, "body_class", None) != "comet":
            raise ValueError("CometTrackSymbolLayer requires a comet.")
        super().__init__(realization, major_index, **options)

    def realize(self, context, observer, **geometry_options):
        primary = super().realize(context, observer, **geometry_options)
        result = self.track_realization.realize(context, observer)
        sample_index = result.tick_sample_indices[self.major_index]
        apparent = result.apparent_directions[sample_index]
        comet = (
            float(apparent.geometry.lon_deg[0]),
            float(apparent.geometry.lat_deg[0]),
        )
        binding = result.source_binding
        observer_state = apparent.astrometric.observer_state
        request = AstrometricDirectionRequest(
            target=self.descriptor.target,
            centre=self.descriptor.centre,
            reception_instant=result.sample_instants[sample_index],
            reception_time_scale=result.sample_time_scale,
        )
        angle = _provider_gas_tail_position_angle(
            binding.target_source, request, observer_state
        )
        sun = None
        separation = None
        suppressed = False
        if angle is None:
            sun_request = AstrometricDirectionRequest(
                target="sun", centre=self.descriptor.centre,
                reception_instant=request.reception_instant,
                reception_time_scale=request.reception_time_scale,
            )
            astrometric = self.track_realization.realizer.astrometric_realizer.direction(
                binding.observer_source, sun_request, observer_state
            )
            sun_geometry = self.track_realization.realizer.apparent_realizer.direction(
                astrometric,
                observer=result.sample_observers[sample_index],
                source=binding.observer_source,
                policy=self.descriptor.correction_policy,
            ).geometry
            sun = (float(sun_geometry.lon_deg[0]), float(sun_geometry.lat_deg[0]))
            separation = angular_separation_deg(comet, sun)
            suppressed = (
                separation < MINIMUM_ANTISOLAR_SEPARATION_DEG
                or separation > 180.0 - MINIMUM_ANTISOLAR_SEPARATION_DEG
            )
            if not suppressed:
                angle = antisolar_position_angle_deg(comet, sun)
        metadata = {
            **dict(primary.metadata),
            "comet_tail_suppressed": suppressed,
            "apparent_sun_comet_separation_deg": separation,
            "sun_apparent_icrf_deg": sun,
            "comet_tail_orientation_source": (
                "provider PsAng" if sun is None else "Wenu apparent Sun-comet fallback"
            ),
        }
        if suppressed:
            return SphericalPoints(
                primary.lon_deg, primary.lat_deg,
                coordinate_spec=primary.coordinate_spec,
                ids=primary.ids, labels=primary.labels, names=primary.names,
                metadata=metadata,
            )
        reference = offset_direction_deg(
            comet, angle, ANTISOLAR_TANGENT_OFFSET_DEG
        )
        native = SphericalPoints(
            [comet[0], reference[0]], [comet[1], reference[1]],
            coordinate_spec=apparent.geometry.coordinate_spec,
            ids=[primary.ids[0], f"{primary.ids[0]}__antisolar_reference"],
            labels=[None, None], names=[self.descriptor.display_name, None],
            metadata={
                **metadata,
                "comet_symbol_orientation_reference_index": 1,
                "antisolar_position_angle_deg": angle,
            },
        )
        return self.track_realization.realizer.coordinate_service.transform(
            native, context.product_coordinate_spec, context.observation
        )
