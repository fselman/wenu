"""Request-time semantic observer-horizon configuration."""

from __future__ import annotations

from wenu.sky.horizon import HorizonReference

from .request import ChartRequest


def configure_chart_request_horizon(sky, request):
    """Replace the request-time horizon with the selected reference."""
    if not isinstance(request, ChartRequest):
        raise TypeError("request must be a ChartRequest.")
    if not hasattr(sky, "layers") or not callable(
        getattr(sky, "remove", None)
    ):
        raise TypeError("sky must provide registered layers and remove().")

    for layer in tuple(sky.layers):
        if isinstance(layer, HorizonReference):
            sky.remove(layer)
    if hasattr(sky, "horizon_reference"):
        sky.horizon_reference = None

    if not request.horizon or request.family == "planisphere":
        return None

    add = getattr(sky, "add_horizon_reference", None)
    if not callable(add):
        raise TypeError("sky must provide add_horizon_reference().")
    return add()
