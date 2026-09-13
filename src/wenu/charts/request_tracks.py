"""Request-owned registration of one drawable Solar-System track."""
from __future__ import annotations
from astropy.time import Time
from wenu.sky.solar_system_track_layer import SolarSystemTrackLayer


def _selected_point_replaces_start_label(request, track):
    """Return whether one selected point identifies the same track instant."""
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


def configure_chart_request_tracks(sky, request, *, source_resolver=None):
    """Replace prior tracks with the request's immutable track collection."""
    for point in getattr(sky, "solar_system_bodies", {}).values():
        point.request_draw_label = True
    for layer in tuple(sky.layers):
        if getattr(layer, "layer_name", None) == "solar_system_track":
            sky.remove(layer)
    tracks = tuple(request.solar_system_tracks)
    if not tracks:
        return ()
    options = {}
    if source_resolver is not None:
        from wenu.sky.solar_system_tracks import SolarSystemTrackRealizer

        options["realizer"] = SolarSystemTrackRealizer(
            source_resolver=source_resolver
        )
    layers = []
    for track in tracks:
        replaces_start = _selected_point_replaces_start_label(request, track)
        descriptor = track.descriptor
        if replaces_start:
            point = getattr(sky, "solar_system_bodies", {}).get(
                descriptor.selection_key
            )
            if point is not None:
                point.request_draw_label = False
        layer = SolarSystemTrackLayer(
            track,
            label_ticks=request.solar_system_track_tick_labels,
            label_start=True,
            start_label_text=(
                _coincident_start_label(descriptor)
                if replaces_start else None
            ),
            **options,
        )
        sky.add(layer)
        layers.append(layer)
    return tuple(layers)


def configure_chart_request_track(sky, request, *, source_resolver=None):
    """Compatibility wrapper for callers expecting zero or one layer."""
    layers = configure_chart_request_tracks(
        sky, request, source_resolver=source_resolver
    )
    return None if not layers else layers[0] if len(layers) == 1 else layers
