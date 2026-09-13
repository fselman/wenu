"""Typed resolution of point-object chart centres."""

from __future__ import annotations

from dataclasses import dataclass
from functools import singledispatch

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import (
    PositionStatus,
    observation_context,
    observer_altaz_spec,
)
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.solar_system_bodies import SolarSystemBodyDescriptor
from wenu.sky.solar_system_points import SolarSystemPointLayer

from .target_resolver import ResolvedTarget


@dataclass(frozen=True)
class ObjectCenter:
    """One apparent observer-horizontal point with retained identity."""

    geometry: SphericalPoints
    key: str
    display_name: str
    provenance: tuple[str, ...]

    def __post_init__(self):
        if len(self.geometry.lon_deg) != 1:
            raise ValueError(
                "an object center must contain exactly one point."
            )

    @property
    def altitude_deg(self):
        return float(self.geometry.lat_deg[0])

    @property
    def azimuth_deg(self):
        return float(self.geometry.lon_deg[0])


def _product_spec(observer):
    return observer_altaz_spec(
        observer,
        position_status=PositionStatus.APPARENT,
        provider="wenu object-center resolver",
    )


@singledispatch
def get_object_center(subject, observer, **options):
    """Return the apparent chart center for one typed point subject."""
    del observer, options
    raise TypeError(
        f"unsupported chart-center subject: {type(subject).__name__}."
    )


@get_object_center.register
def _(subject: ResolvedTarget, observer, **options):
    """Resolve a fixed catalogue or explicit ICRS target."""
    del options
    geometry = CoordinateService().transform_skycoord(
        subject.coordinate,
        _product_spec(observer),
        observation_context(observer),
    )
    return ObjectCenter(
        geometry=geometry,
        key=subject.key,
        display_name=subject.display_name,
        provenance=(subject.provenance,),
    )


@get_object_center.register
def _(subject: SolarSystemBodyDescriptor, observer, **options):
    """Resolve a descriptor-driven apparent Solar-System point."""
    source_resolver = options.pop("source_resolver", None)
    reference_equinox = options.pop("reference_equinox", "J2000")
    if options:
        raise TypeError(
            "unknown object-center option: " + ", ".join(sorted(options))
        )
    observation = observation_context(observer)
    context = LayerRealizationContext(
        product_coordinate_spec=_product_spec(observer),
        observation=observation,
        evaluation_instant=observation.instant,
        evaluation_time_scale=observation.time_scale,
        reference_equinox=str(reference_equinox),
    )
    geometry = SolarSystemPointLayer(
        subject,
        source_resolver=source_resolver,
    ).realize(context, observer, selected={subject.selection_key})
    if len(geometry.lon_deg) > 1:
        geometry = SphericalPoints(
            lon_deg=geometry.lon_deg[:1],
            lat_deg=geometry.lat_deg[:1],
            coordinate_spec=geometry.coordinate_spec,
            ids=None if geometry.ids is None else geometry.ids[:1],
            labels=None if geometry.labels is None else geometry.labels[:1],
            names=None if geometry.names is None else geometry.names[:1],
            metadata=dict(geometry.metadata),
        )
    return ObjectCenter(
        geometry=geometry,
        key=subject.selection_key,
        display_name=subject.display_name,
        provenance=tuple(geometry.coordinate_spec.provenance),
    )
