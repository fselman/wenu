"""Observed multi-epoch physical Solar-System disk sequences."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timezone
from math import isfinite
from operator import index
from types import SimpleNamespace

from astropy.time import Time, TimeDelta

from wenu.sky.solar_system_points import SolarSystemPointDescriptor
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_appearance import (
    SolarSystemApparentDisk,
    SolarSystemAppearanceRealizer,
)
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)
from wenu.solar_system_disk_geometry import (
    SolarSystemDiskGeometry,
    SolarSystemDiskGeometryRealizer,
)


def _text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty.")
    return normalized


def _positive(value, *, name):
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a number.") from error
    if not isfinite(normalized) or normalized <= 0.0:
        raise ValueError(f"{name} must be positive and finite.")
    return normalized


def _nonnegative_integer(value, *, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer.")
    try:
        normalized = index(value)
    except TypeError as error:
        raise TypeError(f"{name} must be an integer.") from error
    if normalized < 0:
        raise ValueError(f"{name} cannot be negative.")
    return normalized


def _isot(value):
    precise = value.copy()
    precise.precision = 9
    return precise.isot


@dataclass(frozen=True)
class ObservedSolarSystemDiskSequenceRequest:
    """Exact major instants for one observed resolved-body sequence."""

    descriptor: SolarSystemPointDescriptor
    start_instant: str
    start_time_scale: str
    step_days: float
    n_steps: int
    display_name: str
    physical_radius_km: float
    radius_model: str

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
        object.__setattr__(self, "start_time_scale", start.scale)
        object.__setattr__(
            self,
            "step_days",
            _positive(self.step_days, name="step_days"),
        )
        object.__setattr__(
            self,
            "n_steps",
            _nonnegative_integer(self.n_steps, name="n_steps"),
        )
        object.__setattr__(
            self,
            "display_name",
            _text(self.display_name, name="display_name"),
        )
        object.__setattr__(
            self,
            "physical_radius_km",
            _positive(
                self.physical_radius_km,
                name="physical_radius_km",
            ),
        )
        object.__setattr__(
            self,
            "radius_model",
            _text(self.radius_model, name="radius_model"),
        )

    @property
    def sample_count(self):
        """The start sample plus one sample per requested interval."""
        return self.n_steps + 1

    @property
    def sample_offsets_days(self):
        """Exact major-step offsets, including the start."""
        return tuple(
            sample * self.step_days
            for sample in range(self.sample_count)
        )


@dataclass(frozen=True)
class ObservedSolarSystemDiskSequence:
    """Observed physical disks with full retained per-epoch evidence."""

    request: ObservedSolarSystemDiskSequenceRequest
    sample_instants: tuple[str, ...]
    sample_time_scale: str
    appearances: tuple[SolarSystemApparentDisk, ...]
    geometries: tuple[SolarSystemDiskGeometry, ...]
    distances: tuple[float, ...]
    distance_origin: str = "observer"
    distance_unit: str = "au"
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(
            self.request,
            ObservedSolarSystemDiskSequenceRequest,
        ):
            raise TypeError(
                "request must be an "
                "ObservedSolarSystemDiskSequenceRequest."
            )
        instants = tuple(
            _text(value, name="sample instant")
            for value in self.sample_instants
        )
        appearances = tuple(self.appearances)
        geometries = tuple(self.geometries)
        distances = tuple(
            _positive(value, name="distance")
            for value in self.distances
        )
        count = self.request.sample_count
        if not (
            len(instants)
            == len(appearances)
            == len(geometries)
            == len(distances)
            == count
        ):
            raise ValueError(
                "sequence evidence must contain n_steps + 1 samples."
            )
        if not all(
            isinstance(value, SolarSystemApparentDisk)
            for value in appearances
        ):
            raise TypeError(
                "appearances must contain SolarSystemApparentDisk values."
            )
        if not all(
            isinstance(value, SolarSystemDiskGeometry)
            for value in geometries
        ):
            raise TypeError(
                "geometries must contain SolarSystemDiskGeometry values."
            )
        for appearance, geometry, distance in zip(
            appearances,
            geometries,
            distances,
        ):
            if geometry.appearance is not appearance:
                raise ValueError(
                    "each geometry must retain its exact appearance state."
                )
            if appearance.target != self.request.descriptor.target:
                raise ValueError(
                    "every appearance must realize the requested target."
                )
            expected_distance = (
                appearance.apparent_direction.astrometric.distance_au
            )
            tolerance = 1.0e-14 * max(1.0, expected_distance)
            if abs(distance - expected_distance) > tolerance:
                raise ValueError(
                    "distance must equal the accepted astrometric distance."
                )
        object.__setattr__(self, "sample_instants", instants)
        object.__setattr__(
            self,
            "sample_time_scale",
            _text(
                self.sample_time_scale,
                name="sample_time_scale",
            ).lower(),
        )
        object.__setattr__(self, "appearances", appearances)
        object.__setattr__(self, "geometries", geometries)
        object.__setattr__(self, "distances", distances)
        object.__setattr__(
            self,
            "distance_origin",
            _text(self.distance_origin, name="distance_origin").lower(),
        )
        object.__setattr__(
            self,
            "distance_unit",
            _text(self.distance_unit, name="distance_unit").lower(),
        )
        if self.distance_origin != "observer":
            raise ValueError(
                "observed sequence distance_origin must be observer."
            )
        if self.distance_unit != "au":
            raise ValueError(
                "observed sequence distance_unit must be au."
            )
        object.__setattr__(
            self,
            "provenance",
            tuple(
                _text(value, name="provenance entry")
                for value in self.provenance
            ),
        )


class ObservedSolarSystemDiskSequenceRealizer:
    """Realize every observed disk independently at its exact instant."""

    def __init__(
        self,
        *,
        source_factory=SkyfieldEphemerisStateSource.from_observer,
        sample_observer_factory=None,
        observer_state_factory=skyfield_observer_barycentric_state,
        astrometric_realizer=None,
        apparent_realizer=None,
        appearance_realizer=None,
        disk_realizer=None,
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
        self.appearance_realizer = (
            SolarSystemAppearanceRealizer()
            if appearance_realizer is None else appearance_realizer
        )
        self.disk_realizer = (
            SolarSystemDiskGeometryRealizer()
            if disk_realizer is None else disk_realizer
        )

    def sequence(self, request, *, observer):
        """Return independently realized physical disks at all major instants."""
        if not isinstance(
            request,
            ObservedSolarSystemDiskSequenceRequest,
        ):
            raise TypeError(
                "request must be an "
                "ObservedSolarSystemDiskSequenceRequest."
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
        appearances = []
        geometries = []
        distances = []
        for sample_time in sample_times:
            sample_observer = self.sample_observer_factory(
                observer,
                sample_time,
            )
            observer_state = self.observer_state_factory(
                sample_observer,
                source=source,
            )
            target_request = AstrometricDirectionRequest(
                target=request.descriptor.target,
                centre=request.descriptor.centre,
                reception_instant=_isot(sample_time),
                reception_time_scale=sample_time.scale,
            )
            sun_request = AstrometricDirectionRequest(
                target="sun",
                centre=request.descriptor.centre,
                reception_instant=_isot(sample_time),
                reception_time_scale=sample_time.scale,
            )
            target_astrometric = self.astrometric_realizer.direction(
                source,
                target_request,
                observer_state,
            )
            sun_astrometric = self.astrometric_realizer.direction(
                source,
                sun_request,
                observer_state,
            )
            target_apparent = self.apparent_realizer.direction(
                target_astrometric,
                observer=sample_observer,
                source=source,
                policy=request.descriptor.correction_policy,
            )
            sun_apparent = self.apparent_realizer.direction(
                sun_astrometric,
                observer=sample_observer,
                source=source,
                policy=ApparentCorrectionPolicy(),
            )
            appearance = self.appearance_realizer.appearance(
                source,
                target_apparent,
                sun_apparent,
                display_name=request.display_name,
                physical_radius_km=request.physical_radius_km,
                radius_model=request.radius_model,
            )
            appearances.append(appearance)
            geometries.append(self.disk_realizer.geometry(appearance))
            distances.append(
                appearance.apparent_direction.astrometric.distance_au
            )

        return ObservedSolarSystemDiskSequence(
            request=request,
            sample_instants=tuple(_isot(value) for value in sample_times),
            sample_time_scale=start.scale,
            appearances=tuple(appearances),
            geometries=tuple(geometries),
            distances=tuple(distances),
            provenance=(
                "topocentric observer independently evaluated at every sample",
                "apparent target and Sun directions independently evaluated",
                "physical appearance independently evaluated at every sample",
                "full observer-target distances retained without 2D inference",
                f"ephemeris model: {source.resource.model}",
                f"ephemeris sha256: {source.resource.sha256}",
            ),
        )


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
