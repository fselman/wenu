"""Request-owned registration of one drawable Solar-System track."""
from __future__ import annotations
from astropy.time import Time
from wenu.sky.solar_system_track_layer import SolarSystemTrackLayer


def _selected_point_replaces_start_label(request):
    """Return whether one selected point identifies the same track instant."""
    track = request.solar_system_track
    selected = set(request.content.solar_system_objects or ())
    if track.descriptor.selection_key not in selected:
        return False
    observation = Time(request.observer.time, scale="utc")
    start = Time(track.start_instant, scale=track.start_time_scale)
    return abs((observation.tai - start.tai).to_value("second")) < 1.0e-6

def _coincident_start_label(descriptor):
    """Return the display label for a selected point at the track start."""
    number = getattr(descriptor, "iau_number", None)
    if getattr(descriptor, "body_class", None) == "asteroid" and number:
        display_name = descriptor.display_name
        numbered = f"({number})"
        return (
            numbered
            if display_name == numbered
            else f"{display_name} {numbered}"
        )
    return (
        getattr(descriptor, "canonical_designation", None)
        or descriptor.display_name
    )


def configure_chart_request_track(sky, request, *, source_resolver=None):
    """Replace any prior request track with the request's selected track."""
    for point in getattr(sky, "solar_system_bodies", {}).values():
        point.request_draw_label = True
    for layer in tuple(sky.layers):
        if getattr(layer, "layer_name", None) == "solar_system_track":
            sky.remove(layer)
    if request.solar_system_track is None:
        return None
    options = {}
    if source_resolver is not None:
        from wenu.sky.solar_system_tracks import SolarSystemTrackRealizer

        options["realizer"] = SolarSystemTrackRealizer(
            source_resolver=source_resolver
        )
    replaces_start = _selected_point_replaces_start_label(request)
    descriptor = request.solar_system_track.descriptor
    if replaces_start:
        point = getattr(sky, "solar_system_bodies", {}).get(
            descriptor.selection_key
        )
        if point is not None:
            point.request_draw_label = False
    start_label_text = None
    if replaces_start:
        start_label_text = _coincident_start_label(descriptor)
    layer = SolarSystemTrackLayer(
        request.solar_system_track,
        label_ticks=request.solar_system_track_tick_labels,
        label_start=True,
        start_label_text=start_label_text,
        **options,
    )
    sky.add(layer)
    return layer
