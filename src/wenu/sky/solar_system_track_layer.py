"""Scientific Solar-System track layer."""

from __future__ import annotations

from wenu.sky.sky_layer import SkyLayer
from wenu.sky.solar_system_tracks import (
    SolarSystemTrackRealizer,
    SolarSystemTrackRequest,
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
