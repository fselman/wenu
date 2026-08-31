"""Request-owned registration of one drawable Solar-System track."""
from __future__ import annotations
from wenu.sky.solar_system_track_layer import SolarSystemTrackLayer

def configure_chart_request_track(sky, request):
    """Replace any prior request track with the request's selected track."""
    for layer in tuple(sky.layers):
        if getattr(layer, "layer_name", None) == "solar_system_track":
            sky.remove(layer)
    if request.solar_system_track is None:
        return None
    layer = SolarSystemTrackLayer(\n        request.solar_system_track,\n        label_ticks=request.solar_system_track_tick_labels,\n    )
    sky.add(layer)
    return layer
