"""Ordinary observer-bound geometrical chart views."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .product_options import ChartProductOptions
from .request import (
    ChartFrameRequest,
    ChartRequest,
    ChartSubjectRequest,
)
from .request_chart import prepare_chart_request
from .request_resolver import resolve_chart_request
from .view_defaults import chart_view_defaults


@dataclass(frozen=True)
class ChartView:
    """Observer-bound chart geometry with resolved subject provenance."""

    sky: object
    observer: object
    _prepared: object = field(repr=False)
    configuration: object | None = field(default=None, repr=False)

    @property
    def chart(self):
        """Return the canonical prepared chart geometry."""
        return self._prepared.chart

    @property
    def family(self):
        """Return the canonical chart-family identity."""
        return self._prepared.resolved.request.family

    @property
    def projection_name(self):
        """Return the resolved planar-projection identity."""
        return self._prepared.resolved.request.projection

    @property
    def coordinate_frame(self):
        """Return the resolved spherical coordinate-frame identity."""
        return self._prepared.resolved.request.coordinate_frame

    @property
    def mask(self):
        """Return whether region masking belongs to this view geometry."""
        return self._prepared.resolved.request.mask

    @property
    def target(self):
        """Return resolved target provenance, when applicable."""
        return self._prepared.resolved.target

    @property
    def constellations(self):
        """Return resolved constellation provenance, when applicable."""
        return self._prepared.resolved.constellations

    @property
    def frame(self):
        """Return the effective resolved geometrical frame."""
        return self._prepared.resolved.frame


def get_chart_view(
    sky,
    observer,
    *,
    family,
    target=None,
    ra_deg=None,
    dec_deg=None,
    constellations=None,
    group=None,
    display_name=None,
    field_diameter_deg=None,
    field_width_deg=None,
    field_height_deg=None,
    position_angle_deg=None,
    pole=None,
    limiting_declination_deg=None,
    projection=None,
    coordinate_frame=None,
    mask=None,
    configuration=None,
):
    """Resolve and prepare one observer-bound geometrical chart view."""
    if configuration is not None:
        from wenu.configuration import ConfigurationDefaults

        if not isinstance(configuration, ConfigurationDefaults):
            raise TypeError(
                "configuration must be a ConfigurationDefaults value."
            )
    defaults = chart_view_defaults(
        family,
        group=(
            group is not None
            or constellations is not None and len(constellations) > 1
        ),
        configuration=configuration,
    )
    projection_name = str(
        defaults.projection if projection is None else projection
    ).strip().lower()
    coordinate_frame_name = str(
        defaults.coordinate_frame
        if coordinate_frame is None else coordinate_frame
    ).strip().lower()
    profile = getattr(sky, "load_profile", None)
    if profile is None:
        raise ValueError("sky must declare a load profile.")
    if observer is None:
        raise TypeError("observer is required for a chart view.")
    if field_diameter_deg is None:
        field_diameter_deg = defaults.field_diameter_deg
    if field_width_deg is None and field_height_deg is None:
        field_width_deg = defaults.field_width_deg
        field_height_deg = defaults.field_height_deg
    if position_angle_deg is None:
        position_angle_deg = defaults.position_angle_deg
    if pole is None:
        pole = defaults.pole or "south"
    if limiting_declination_deg is None:
        limiting_declination_deg = defaults.limiting_declination_deg
    if mask is None:
        mask = defaults.mask

    request = ChartRequest(
        observer=_observer_request(observer),
        family=family,
        projection=projection_name,
        coordinate_frame=coordinate_frame_name,
        subject=ChartSubjectRequest(
            target=target,
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            constellations=constellations,
            group=group,
            display_name=display_name,
        ),
        frame=ChartFrameRequest(
            field_diameter_deg=field_diameter_deg,
            field_width_deg=field_width_deg,
            field_height_deg=field_height_deg,
            position_angle_deg=position_angle_deg,
            pole=pole,
            limiting_declination_deg=limiting_declination_deg,
        ),
        mask=mask,
        product=ChartProductOptions(output=Path(".")),
    )
    resolved = resolve_chart_request(request, profile)
    prepared = prepare_chart_request(
        sky, resolved, observer=observer
    )
    return ChartView(
        sky=sky,
        observer=observer,
        _prepared=prepared,
        configuration=configuration,
    )


def _observer_request(observer):
    from .request import ChartObserverRequest

    required = ("utc_datetime", "lat_deg", "lon_deg", "elevation_m")
    missing = [name for name in required if not hasattr(observer, name)]
    if missing:
        raise TypeError(
            "observer must provide scientific location and instant: "
            + ", ".join(missing)
        )

    return ChartObserverRequest(
        time=observer.utc_datetime,
        lat_deg=observer.lat_deg,
        lon_deg=observer.lon_deg,
        elevation_m=observer.elevation_m,
        timezone_name=getattr(observer, "timezone_name", None),
    )
