"""Scientific Solar-System track layer."""

from __future__ import annotations

from dataclasses import replace

from astropy.time import Time, TimeDelta

from wenu.sky.sky_layer import SkyLayer
from wenu.sky.solar_system_points import SolarSystemPointLayer
from wenu.sky.solar_system_tracks import (
    SolarSystemTrackRealizer,
    SolarSystemTrackRequest,
    _isot,
    _observer_at_time,
)


class SolarSystemTrackLayer(SkyLayer):
    """Realize one scientific track as an ordinary spherical curve."""

    layer_name = "solar_system_track"

    def __init__(
        self, request, *, realizer=None, label_ticks=False,
        label_start=True, start_label_text=None,
    ):
        if not isinstance(request, SolarSystemTrackRequest):
            raise TypeError(
                "request must be a SolarSystemTrackRequest."
            )
        self.request = request
        if hasattr(request.descriptor, "body_class"):
            self.body_descriptor = request.descriptor
            self.display_kind = "apparent_track"
        self.realizer = (
            SolarSystemTrackRealizer()
            if realizer is None
            else realizer
        )
        self.last_result = None
        self.label_ticks = bool(label_ticks)
        self.label_start = bool(label_start)
        self.start_label_text = start_label_text

    def realize(self, context, observer, **geometry_options):
        if geometry_options:
            raise TypeError(
                "SolarSystemTrackLayer accepts no geometry options."
            )
        self.last_result = self.realizer.curve(
            self.request,
            context=context,
            observer=observer,
        )
        return self.last_result.geometry

    def spherical_geometry(self, observer):
        del observer
        raise RuntimeError(
            "SolarSystemTrackLayer requires a "
            "LayerRealizationContext."
        )


class CometTrackSymbolLayer(SkyLayer):
    """Realize one reusable comet symbol at one major track epoch."""

    layer_name = "solar_system_track_symbol"

    def __init__(
        self,
        request,
        offset_days,
        *,
        source_resolver=None,
        draw_label=False,
    ):
        if not isinstance(request, SolarSystemTrackRequest):
            raise TypeError("request must be a SolarSystemTrackRequest.")
        if getattr(request.descriptor, "body_class", None) != "comet":
            raise ValueError("CometTrackSymbolLayer requires a comet.")
        self.request = request
        self.descriptor = request.descriptor
        self.body_descriptor = request.descriptor
        self.display_kind = "symbolic_point"
        self.offset_days = float(offset_days)
        self.source_resolver = source_resolver
        self.request_draw_label = bool(draw_label)

    def realize(self, context, observer, **geometry_options):
        start = Time(
            self.request.start_instant,
            scale=self.request.start_time_scale,
        )
        instant = start + TimeDelta(self.offset_days, format="jd")
        sample_observer = _observer_at_time(observer, instant)
        resolver = self.source_resolver
        point = SolarSystemPointLayer(
            self.descriptor,
            source_resolver=(
                None
                if resolver is None
                else lambda descriptor, ignored_observer: resolver(
                    descriptor, observer
                )
            ),
        )
        sample_context = replace(
            context,
            evaluation_instant=_isot(instant),
            evaluation_time_scale=instant.scale,
        )
        return point.realize(
            sample_context,
            sample_observer,
            **geometry_options,
        )

    def spherical_geometry(self, observer):
        del observer
        raise RuntimeError(
            "CometTrackSymbolLayer requires a LayerRealizationContext."
        )
