"""Renderer-neutral scientific Solar-System trajectory realization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timezone
from math import isfinite
from types import SimpleNamespace

import numpy as np
from astropy.time import Time, TimeDelta

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.geometry.spherical import SphericalCurves
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.solar_system_points import SolarSystemPointDescriptor
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_directions import (
    ApparentDirection,
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)


def _text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty.")
    return normalized


def _positive_days(value, *, name):
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a number of days.") from error
    if not isfinite(normalized) or normalized <= 0.0:
        raise ValueError(f"{name} must be positive and finite.")
    return normalized


def _isot(value):
    precise = value.copy()
    precise.precision = 9
    return precise.isot


@dataclass(frozen=True)
class SolarSystemTrackRequest:
    """Scientific sampling request for one Solar-System body path."""

    descriptor: SolarSystemPointDescriptor
    start_instant: str
    start_time_scale: str
    sample_step_days: float
    tick_step_days: float
    tick_count: int

    def __post_init__(self):
        if not isinstance(self.descriptor, SolarSystemPointDescriptor):
            raise TypeError(
                "descriptor must be a SolarSystemPointDescriptor."
            )
        start_instant = _text(
            self.start_instant,
            name="start_instant",
        )
        start_time_scale = _text(
            self.start_time_scale,
            name="start_time_scale",
        ).lower()
        try:
            start = Time(start_instant, scale=start_time_scale)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "start_instant must be valid in start_time_scale."
            ) from error
        object.__setattr__(self, "start_instant", _isot(start))
        object.__setattr__(
            self,
            "start_time_scale",
            start.scale,
        )
        object.__setattr__(
            self,
            "sample_step_days",
            _positive_days(
                self.sample_step_days,
                name="sample_step_days",
            ),
        )
        object.__setattr__(
            self,
            "tick_step_days",
            _positive_days(
                self.tick_step_days,
                name="tick_step_days",
            ),
        )
        if isinstance(self.tick_count, bool) or not isinstance(
            self.tick_count,
            int,
        ):
            raise TypeError("tick_count must be an integer.")
        if self.tick_count < 1:
            raise ValueError("tick_count must be positive.")

    @property
    def duration_days(self):
        """Closed track interval in days."""
        return self.tick_step_days * self.tick_count

    @property
    def tick_offsets_days(self):
        """Offsets of the start and every exact major-time anchor."""
        return tuple(
            index * self.tick_step_days
            for index in range(self.tick_count + 1)
        )

    @property
    def sample_offsets_days(self):
        """Sorted regular samples plus exact major-time anchors."""
        duration = self.duration_days
        offsets = [0.0]
        index = 1
        while index * self.sample_step_days < duration:
            offsets.append(index * self.sample_step_days)
            index += 1
        offsets.append(duration)
        offsets.extend(self.tick_offsets_days)
        offsets.sort()

        unique = []
        tolerance = 1.0e-12
        for offset in offsets:
            if not unique or abs(offset - unique[-1]) > tolerance:
                unique.append(offset)
        return tuple(unique)


@dataclass(frozen=True)
class SolarSystemTrackResult:
    """One fixed-product-frame curve with retained per-sample evidence."""

    request: SolarSystemTrackRequest
    geometry: SphericalCurves
    sample_instants: tuple[str, ...]
    sample_time_scale: str
    tick_sample_indices: tuple[int, ...]
    apparent_directions: tuple[ApparentDirection, ...]
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.request, SolarSystemTrackRequest):
            raise TypeError(
                "request must be a SolarSystemTrackRequest."
            )
        if not isinstance(self.geometry, SphericalCurves):
            raise TypeError("geometry must be a SphericalCurves.")
        if len(self.geometry) != 1:
            raise ValueError("geometry must contain exactly one curve.")
        sample_count = len(self.geometry.lon_deg[0])
        sample_instants = tuple(
            _text(value, name="sample instant")
            for value in self.sample_instants
        )
        if len(sample_instants) != sample_count:
            raise ValueError(
                "sample_instants must contain one value per curve vertex."
            )
        object.__setattr__(self, "sample_instants", sample_instants)
        object.__setattr__(
            self,
            "sample_time_scale",
            _text(
                self.sample_time_scale,
                name="sample_time_scale",
            ).lower(),
        )
        directions = tuple(self.apparent_directions)
        if len(directions) != sample_count or not all(
            isinstance(value, ApparentDirection)
            for value in directions
        ):
            raise TypeError(
                "apparent_directions must contain one ApparentDirection "
                "per curve vertex."
            )
        object.__setattr__(self, "apparent_directions", directions)
        indices = tuple(self.tick_sample_indices)
        if len(indices) != self.request.tick_count + 1:
            raise ValueError(
                "tick_sample_indices must include start and every tick."
            )
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or value >= sample_count
            for value in indices
        ):
            raise ValueError(
                "tick_sample_indices must identify valid curve vertices."
            )
        if tuple(sorted(indices)) != indices or len(set(indices)) != len(
            indices
        ):
            raise ValueError(
                "tick_sample_indices must be strictly increasing."
            )
        object.__setattr__(self, "tick_sample_indices", indices)
        object.__setattr__(
            self,
            "provenance",
            tuple(
                _text(value, name="provenance entry")
                for value in self.provenance
            ),
        )


class SolarSystemTrackRealizer:
    """Evaluate scalar apparent directions and assemble one spherical curve."""

    def __init__(
        self,
        *,
        source_factory=SkyfieldEphemerisStateSource.from_observer,
        sample_observer_factory=None,
        observer_state_factory=skyfield_observer_barycentric_state,
        astrometric_realizer=None,
        apparent_realizer=None,
        coordinate_service=None,
    ):
        self.source_factory = source_factory
        self.sample_observer_factory = (
            _observer_at_time
            if sample_observer_factory is None
            else sample_observer_factory
        )
        self.observer_state_factory = observer_state_factory
        self.astrometric_realizer = (
            AstrometricDirectionRealizer()
            if astrometric_realizer is None
            else astrometric_realizer
        )
        self.apparent_realizer = (
            SkyfieldApparentDirectionRealizer()
            if apparent_realizer is None else apparent_realizer
        )
        self.coordinate_service = (
            CoordinateService()
            if coordinate_service is None else coordinate_service
        )

    def curve(self, request, *, context, observer):
        """Return one track transformed into the context's fixed product frame."""
        if not isinstance(request, SolarSystemTrackRequest):
            raise TypeError(
                "request must be a SolarSystemTrackRequest."
            )
        if not isinstance(context, LayerRealizationContext):
            raise TypeError(
                "context must be a LayerRealizationContext."
            )
        if context.observation is None:
            raise ValueError(
                "a Solar-System track requires an observation context."
            )

        source = self.source_factory(observer)
        start = Time(
            request.start_instant,
            scale=request.start_time_scale,
        )
        sample_times = tuple(
            start + TimeDelta(offset, format="jd")
            for offset in request.sample_offsets_days
        )
        apparent_directions = []
        for sample_time in sample_times:
            sample_observer = self.sample_observer_factory(
                observer,
                sample_time,
            )
            observer_state = self.observer_state_factory(
                sample_observer,
                source=source,
            )
            direction_request = AstrometricDirectionRequest(
                target=request.descriptor.target,
                centre=request.descriptor.centre,
                reception_instant=_isot(sample_time),
                reception_time_scale=sample_time.scale,
            )
            astrometric = self.astrometric_realizer.direction(
                source,
                direction_request,
                observer_state,
            )
            apparent_directions.append(
                self.apparent_realizer.direction(
                    astrometric,
                    observer=sample_observer,
                    source=source,
                    policy=request.descriptor.correction_policy,
                )
            )

        apparent_directions = tuple(apparent_directions)
        native = _native_curve(
            request,
            apparent_directions,
            sample_times,
            source,
        )
        geometry = self.coordinate_service.transform(
            native,
            context.product_coordinate_spec,
            context.observation,
        )
        tick_indices = tuple(
            _offset_index(
                request.sample_offsets_days,
                offset,
            )
            for offset in request.tick_offsets_days
        )
        return SolarSystemTrackResult(
            request=request,
            geometry=geometry,
            sample_instants=tuple(_isot(value) for value in sample_times),
            sample_time_scale=start.scale,
            tick_sample_indices=tick_indices,
            apparent_directions=apparent_directions,
            provenance=(
                "scalar apparent directions evaluated at every sample instant",
                "assembled once as SphericalCurves before product transformation",
                "chart product frame held fixed across the complete track",
            ),
        )


def _native_curve(request, directions, sample_times, source):
    first = directions[0].geometry.coordinate_spec
    for direction in directions:
        spec = direction.geometry.coordinate_spec
        if (
            spec.frame != "icrs"
            or spec.origin != "observer"
            or spec.position_status is not PositionStatus.APPARENT
            or spec.provider != first.provider
            or spec.model != first.model
            or spec.corrections != first.corrections
        ):
            raise ValueError(
                "all samples must share one apparent ICRS direction policy."
            )
    sample_instants = tuple(_isot(value) for value in sample_times)
    coordinate_spec = CoordinateSpec(
        frame="icrs",
        origin="observer",
        position_status=PositionStatus.APPARENT,
        provider=first.provider,
        model=first.model,
        provenance=(
            *first.provenance,
            f"track start: {sample_instants[0]} {sample_times[0].scale}",
            f"track end: {sample_instants[-1]} {sample_times[-1].scale}",
            "per-vertex reception instants retained in geometry metadata",
        ),
        corrections=first.corrections,
    )
    return SphericalCurves(
        lon_deg=(
            np.asarray(
                [
                    direction.geometry.lon_deg[0]
                    for direction in directions
                ],
                dtype=float,
            ),
        ),
        lat_deg=(
            np.asarray(
                [
                    direction.geometry.lat_deg[0]
                    for direction in directions
                ],
                dtype=float,
            ),
        ),
        coordinate_spec=coordinate_spec,
        closed=np.asarray((False,)),
        ids=np.asarray(
            (f"{request.descriptor.entity_key}.track",),
            dtype=object,
        ),
        labels=np.asarray((request.descriptor.display_name,), dtype=object),
        names=np.asarray((request.descriptor.display_name,), dtype=object),
        metadata={
            "semantic_entity_key": request.descriptor.entity_key,
            "semantic_entity_display_name": request.descriptor.display_name,
            "sample_instants": sample_instants,
            "sample_time_scale": sample_times[0].scale,
            "tick_offsets_days": request.tick_offsets_days,
            "ephemeris_sha256": source.resource.sha256,
        },
    )


def _offset_index(offsets, target):
    differences = tuple(abs(value - target) for value in offsets)
    index = int(np.argmin(differences))
    if differences[index] > 1.0e-12:
        raise RuntimeError("exact tick instant is absent from curve samples.")
    return index


def _observer_at_time(observer, instant):
    try:
        utc_datetime = instant.utc.to_datetime(timezone=timezone.utc)
        skyfield_time = observer.timescale.from_datetime(utc_datetime)
        values = {
            name: getattr(observer, name)
            for name in (
                "ephemeris",
                "timescale",
                "skyfield",
                "lat_deg",
                "lon_deg",
                "elevation_m",
                "location_name",
            )
        }
    except AttributeError as error:
        raise TypeError(
            "observer must expose ephemeris, timescale, skyfield, and site "
            "identity."
        ) from error
    return SimpleNamespace(
        **values,
        t=skyfield_time,
        t_astropy=instant,
        utc_datetime=utc_datetime,
    )
