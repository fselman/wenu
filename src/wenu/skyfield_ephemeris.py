"""Skyfield adapter for one already-resolved JPL SPK resource."""

from __future__ import annotations

from contextlib import contextmanager, ExitStack
from dataclasses import dataclass
from fractions import Fraction
import re
from hashlib import sha256
from math import cos, isfinite, radians, sin
from pathlib import Path

import numpy as np
from astropy.time import Time
from skyfield.errors import EphemerisRangeError
from skyfield.positionlib import Astrometric as SkyfieldAstrometric

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.ephemeris import (
    EphemerisResourceIdentity,
    EphemerisJulianDate,
    EphemerisState,
    EphemerisStateRequest,
)
from wenu.geometry.spherical import SphericalPoints
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
    ApparentDirection,
    AstrometricDirection,
    ObserverBarycentricState,
)


class EphemerisAdapterError(ValueError):
    """Base error for deterministic installed-ephemeris failures."""


class UnsupportedEphemerisFrameError(EphemerisAdapterError):
    """The adapter cannot express states in the requested frame."""


class EphemerisTargetError(EphemerisAdapterError):
    """The resolved kernel cannot identify a requested body."""


class EphemerisCoverageError(EphemerisAdapterError):
    """The requested instant is outside usable kernel coverage."""


def _kernel_coverage(kernel):
    segments = tuple(getattr(kernel, "segments", ()))
    if not segments:
        raise ValueError("kernel must expose at least one SPK segment.")
    try:
        starts = tuple(float(segment.spk_segment.start_jd) for segment in segments)
        ends = tuple(float(segment.spk_segment.end_jd) for segment in segments)
    except (AttributeError, TypeError, ValueError) as error:
        raise TypeError(
            "kernel segments must expose finite start_jd and end_jd values."
        ) from error
    if not all(isfinite(value) for value in starts + ends):
        raise ValueError("kernel segment coverage must be finite.")
    start = max(starts)
    end = min(ends)
    if not start < end:
        raise ValueError(
            "kernel segments have no common coverage interval."
        )
    return start, end


def _sha256(path):
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_skyfield_resource_identity(kernel, *, model=None):
    """Fingerprint one already-open Skyfield kernel without opening another."""
    try:
        path = Path(kernel.path).expanduser().resolve(strict=True)
    except (AttributeError, OSError, TypeError) as error:
        raise TypeError(
            "kernel must expose the path of an existing resolved resource."
        ) from error
    coverage_start, coverage_end = _kernel_coverage(kernel)
    resolved_model = (
        "unqualified SPK model"
        if model is None
        else str(model).strip()
    )
    if not resolved_model:
        raise ValueError("model must be non-empty.")
    return EphemerisResourceIdentity(
        provider="Skyfield/JPL SPK",
        model=resolved_model,
        filename=path.name,
        sha256=_sha256(path),
        coverage_start=f"JD {coverage_start:.8f}",
        coverage_end=f"JD {coverage_end:.8f}",
        coverage_time_scale="tdb",
        provenance=(
            f"resolved path: {path}",
            f"SPK segments: {len(kernel.segments)}",
            ("physical model unqualified; filename is not model evidence"
             if model is None else "model explicitly declared by caller; not independently qualified"),
        ),
    )


@dataclass(frozen=True)
class PinnedEphemerisResource:
    """Caller-pinned local file and metadata, never inferred from its name.

    Coverage is checked against the actual conservative segment intersection.
    Model/provenance is a caller admission, not inferred physical accuracy.
    """

    path: str
    sha256: str
    model: str
    part: str
    coverage_jd: tuple[float, float]
    provenance: tuple[str, ...]

    def __post_init__(self):
        if (self.model, self.part) not in (
                ('DE440', 'full'), ('DE441', 'part-1'), ('DE441', 'part-2')):
            raise ValueError('Explicit DE440/full or DE441/part-1/part-2 required.')
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError('Explicit local SPK path required.')
        digest = self.sha256
        if (type(digest) is not str or len(digest) != 64
                or any(c not in '0123456789abcdef' for c in digest)):
            raise ValueError('Pinned SHA-256 required.')
        if (type(self.coverage_jd) not in (tuple, list) or len(self.coverage_jd) != 2
                or any(type(x) not in (int, float) or not isfinite(x)
                       for x in self.coverage_jd)
                or not self.coverage_jd[0] < self.coverage_jd[1]):
            raise ValueError('Finite increasing TDB coverage required.')
        object.__setattr__(self, 'coverage_jd', tuple(float(x) for x in self.coverage_jd))
        if (type(self.provenance) not in (tuple, list) or not self.provenance
                or any(type(x) is not str or not x.strip() for x in self.provenance)):
            raise ValueError('Explicit resource provenance required.')
        object.__setattr__(self, 'provenance', tuple(self.provenance))


def _spk_segments(kernel):
    """Qualify the actual JPL geometric paths, axes, types and segment ranges."""
    records = tuple(dict(centre=s.spk_segment.center, target=s.spk_segment.target,
        frame=s.spk_segment.frame, data_type=s.spk_segment.data_type,
        start_jd=float(s.spk_segment.start_jd), end_jd=float(s.spk_segment.end_jd))
        for s in kernel.segments)
    if (not records or any(r['frame'] != 1 or r['data_type'] not in (2, 3)
                          or not isfinite(r['start_jd']) or not isfinite(r['end_jd'])
                          or r['start_jd'] >= r['end_jd'] for r in records)
            or not {(0, 3), (3, 399), (0, 10)} <=
            {(r['centre'], r['target']) for r in records}):
        raise ValueError('SPK requires J2000/ICRF geometric 0→3→399 and 0→10 paths.')
    return records


class OfflineEphemerisResources:
    """Context-owned validated resources; no acquisition or cross-request cache."""

    def __init__(self, entries):
        self._entries = tuple(entries)
        self._closed = False

    def select(self, event):
        """DE440 first, then covered DE441 part 1, then part 2; never fallback on failure."""
        if self._closed:
            raise ValueError('Offline ephemeris context is closed.')
        if type(event) is not EphemerisJulianDate:
            raise TypeError('Explicit split-JD TDB event required.')
        exact = Fraction(event.jd1) + Fraction(event.jd2)
        for pin, source, segments in self._entries:
            if pin.coverage_jd[0] <= exact <= pin.coverage_jd[1]:
                return source, dict(model=pin.model, part=pin.part,
                    path=str(Path(pin.path).expanduser().resolve()),
                    sha256=pin.sha256, coverage_jd=list(pin.coverage_jd),
                    provenance=list(pin.provenance), segments=[dict(s) for s in segments],
                    policy='de440-then-de441-part1-then-part2/1',
                    spatial_convention='JPL TDB-compatible geometric ICRF',
                    axes_evidence='SPK frame 1; JPL DE440/DE441 metadata explicitly admitted')
        raise EphemerisCoverageError('Outside all qualified DE440/DE441 coverage.')


@contextmanager
def open_pinned_ephemerides(resources):
    """Verify all three caller-pinned files and own/close their offline handles.

    load_file opens only existing files. builtin=True prevents time-table I/O;
    no UTC/UT1/observer calculation uses the bundled tables in this native TDB path.
    """
    pins = tuple(resources)
    roles = [('DE440', 'full'), ('DE441', 'part-1'), ('DE441', 'part-2')]
    if (len(pins) != 3 or any(type(p) is not PinnedEphemerisResource for p in pins)
            or {(p.model, p.part) for p in pins} != set(roles)):
        raise ValueError('Exactly one DE440 and both DE441 parts must be pinned.')
    from skyfield.api import load_file, load
    timescale = load.timescale(builtin=True)
    owner = None
    with ExitStack() as stack:
        entries = []
        for role in roles:
            pin = next(p for p in pins if (p.model, p.part) == role)
            path = Path(pin.path).expanduser().resolve(strict=True)
            if not path.is_file():
                raise ValueError('SPK must be an existing regular file.')
            kernel = load_file(str(path))
            stack.callback(kernel.close)
            identity = resolve_skyfield_resource_identity(kernel, model=pin.model)
            if identity.sha256 != pin.sha256 or _kernel_coverage(kernel) != pin.coverage_jd:
                raise ValueError('Pinned SPK hash or coverage differs from actual file.')
            segments = _spk_segments(kernel)
            source = SkyfieldEphemerisStateSource(kernel=kernel, timescale=timescale,
                resource=identity, coverage_jd=pin.coverage_jd)
            entries.append((pin, source, segments))
        owner = OfflineEphemerisResources(entries)
        try:
            yield owner
        finally:
            owner._closed = True


class SkyfieldEphemerisStateSource:
    """Borrow an open Skyfield kernel and return geometric ICRF states."""

    def __init__(
        self,
        *,
        kernel,
        timescale,
        resource,
        coverage_jd,
    ):
        if not isinstance(resource, EphemerisResourceIdentity):
            raise TypeError("resource must be an EphemerisResourceIdentity.")
        if not callable(getattr(timescale, "from_astropy", None)):
            raise TypeError("timescale must provide from_astropy().")
        if not callable(getattr(kernel, "decode", None)):
            raise TypeError("kernel must provide decode().")
        start, end = (float(value) for value in coverage_jd)
        if not start < end:
            raise ValueError("coverage_jd must be an increasing pair.")
        self._kernel = kernel
        self._timescale = timescale
        self._coverage_jd = (start, end)
        self.resource = resource

    @classmethod
    def from_observer(cls, observer, *, model=None):
        """Borrow the kernel and timescale already owned by an Observer."""
        try:
            kernel = observer.ephemeris
            timescale = observer.timescale
        except AttributeError as error:
            raise TypeError(
                "observer must expose an open ephemeris and timescale."
            ) from error
        coverage = _kernel_coverage(kernel)
        resource = resolve_skyfield_resource_identity(kernel, model=model)
        return cls(
            kernel=kernel,
            timescale=timescale,
            resource=resource,
            coverage_jd=coverage,
        )

    def _body(self, key, *, role):
        provider_key = key
        if isinstance(key, str) and re.fullmatch(r"[+-]?\d+", key.strip()):
            provider_key = int(key)
        try:
            provider_id = self._kernel.decode(provider_key)
            vector = (
                None
                if provider_id == 0
                else self._kernel[provider_id]
            )
        except (KeyError, TypeError, ValueError) as error:
            raise EphemerisTargetError(
                f"kernel cannot resolve {role} {key!r}."
            ) from error
        return vector, str(provider_id)

    def state(self, request):
        """Evaluate one simultaneous geometric target-minus-centre state."""
        if not isinstance(request, EphemerisStateRequest):
            raise TypeError("request must be an EphemerisStateRequest.")
        if request.frame != "icrf":
            raise UnsupportedEphemerisFrameError(
                "Skyfield SPK adapter currently supports only frame='icrf'."
            )

        if type(request.instant) is EphemerisJulianDate:
            # tdb_jd preserves the low part for jplephem's split-time evaluation.
            time = self._timescale.tdb_jd(request.instant.jd1, request.instant.jd2)
            tdb = Fraction(request.instant.jd1) + Fraction(request.instant.jd2)
        else:
            astropy_time = Time(request.instant, scale=request.time_scale)
            time = self._timescale.from_astropy(astropy_time)
            tdb = float(time.tdb)
        start, end = self._coverage_jd
        if not start <= tdb <= end:
            raise EphemerisCoverageError(
                f"requested TDB JD {float(tdb):.8f} is outside kernel coverage "
                f"{start:.8f} through {end:.8f}."
            )

        target, target_id = self._body(request.target, role="target")
        centre, centre_id = self._body(request.centre, role="centre")
        try:
            target_state = None if target is None else target.at(time)
            centre_state = None if centre is None else centre.at(time)
        except EphemerisRangeError as error:
            raise EphemerisCoverageError(
                "requested target-centre state is outside segment coverage."
            ) from error

        zero = (0.0, 0.0, 0.0)
        target_position = (
            zero if target_state is None else tuple(target_state.position.au)
        )
        target_velocity = (
            zero
            if target_state is None
            else tuple(target_state.velocity.au_per_d)
        )
        centre_position = (
            zero if centre_state is None else tuple(centre_state.position.au)
        )
        centre_velocity = (
            zero
            if centre_state is None
            else tuple(centre_state.velocity.au_per_d)
        )

        return EphemerisState(
            request=request,
            position=tuple(
                target_component - centre_component
                for target_component, centre_component in zip(
                    target_position,
                    centre_position,
                )
            ),
            velocity=tuple(
                target_component - centre_component
                for target_component, centre_component in zip(
                    target_velocity,
                    centre_velocity,
                )
            ),
            position_unit="au",
            velocity_unit="au/day",
            resource=self.resource,
            provider_target_id=target_id,
            provider_centre_id=centre_id,
            provenance=(
                "simultaneous geometric target-minus-centre state",
                "Skyfield ICRF axes",
            ),
        )


def skyfield_observer_barycentric_state(observer, *, source):
    """Borrow one Observer and expose its reception-time ICRF state."""
    if not isinstance(source, SkyfieldEphemerisStateSource):
        raise TypeError("source must be a SkyfieldEphemerisStateSource.")
    try:
        if source._kernel is not observer.ephemeris:
            raise ValueError(
                "source and observer must borrow the same ephemeris."
            )
        state = observer.skyfield.at(observer.t)
        instant = observer.t_astropy
    except AttributeError as error:
        raise TypeError(
            "observer must expose skyfield, t, and t_astropy values."
        ) from error
    location_name = getattr(observer, "location_name", None)
    observer_id = (
        str(location_name)
        if location_name
        else (
            f"WGS84 {observer.lat_deg:.12g},"
            f"{observer.lon_deg:.12g},"
            f"{observer.elevation_m:.12g}m"
        )
    )
    return ObserverBarycentricState(
        observer_id=observer_id,
        centre="solar system barycenter",
        frame="icrf",
        instant=instant.isot,
        time_scale=instant.scale,
        position=tuple(state.position.au),
        velocity=tuple(state.velocity.au_per_d),
        position_unit="au",
        velocity_unit="au/day",
        resource=source.resource,
        provider_observer_id="WGS84 terrestrial site",
        provider_centre_id="0",
        provenance=(
            "Skyfield Earth plus WGS84 site at reception time",
            "Skyfield ICRF axes",
        ),
    )


class SkyfieldApparentDirectionRealizer:
    """Apply Skyfield apparent-place corrections without repeating observe()."""

    def direction(self, astrometric, *, observer, source, policy=None):
        if not isinstance(astrometric, AstrometricDirection):
            raise TypeError("astrometric must be an AstrometricDirection.")
        if not isinstance(source, SkyfieldEphemerisStateSource):
            raise TypeError("source must be a SkyfieldEphemerisStateSource.")
        if source._kernel is not getattr(observer, "ephemeris", None):
            raise ValueError(
                "source and observer must borrow the same ephemeris."
            )
        resolved_policy = (
            ApparentCorrectionPolicy() if policy is None else policy
        )
        if not isinstance(resolved_policy, ApparentCorrectionPolicy):
            raise TypeError("policy must be an ApparentCorrectionPolicy.")
        if astrometric.observer_state.resource != source.resource:
            raise ValueError(
                "astrometric result and source must use the same resource."
            )
        try:
            reception = observer.t_astropy
            centre = observer.skyfield.at(observer.t)
        except AttributeError as error:
            raise TypeError(
                "observer must expose t_astropy, skyfield, and t."
            ) from error
        requested_reception = Time(
            astrometric.request.reception_instant,
            scale=astrometric.request.reception_time_scale,
        )
        offset_days = float((reception - requested_reception).to_value("day"))
        if abs(offset_days) > 1.0e-12:
            raise ValueError(
                "observer must be evaluated at the astrometric reception instant."
            )
        self._validate_observer_state(astrometric, centre)

        lon = radians(float(astrometric.geometry.lon_deg[0]))
        lat = radians(float(astrometric.geometry.lat_deg[0]))
        distance = astrometric.distance_au
        cos_latitude = cos(lat)
        position = (
            distance * cos_latitude * cos(lon),
            distance * cos_latitude * sin(lon),
            distance * sin(lat),
        )
        try:
            target = int(astrometric.target_provider_id)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "astrometric target_provider_id must be an integer NAIF ID."
            ) from error

        skyfield_astrometric = SkyfieldAstrometric(
            position,
            astrometric.relative_velocity_au_per_day,
            observer.t,
            centre.target,
            target,
        )
        skyfield_astrometric._ephemeris = observer.ephemeris
        skyfield_astrometric.center_barycentric = centre
        skyfield_astrometric.light_time = astrometric.light_time_days
        apparent = skyfield_astrometric.apparent(
            deflectors=resolved_policy.deflector_naif_ids
        )
        ra, dec, _ = apparent.radec()
        astrometric_spec = astrometric.geometry.coordinate_spec
        corrections = {
            "one-way-light-time",
            "aberration",
            "gravitational-deflection",
        }
        if resolved_policy.earth_deflection:
            corrections.add("earth-gravitational-deflection")
        coordinate_spec = CoordinateSpec(
            frame="icrs",
            origin="observer",
            position_status=PositionStatus.APPARENT,
            instant=astrometric.geometry.coordinate_spec.instant,
            time_scale=astrometric.geometry.coordinate_spec.time_scale,
            provider=astrometric_spec.provider,
            model=astrometric_spec.model,
            provenance=(
                *astrometric_spec.provenance,
                f"apparent model: {resolved_policy.model}",
                "deflector NAIF IDs: "
                + ",".join(
                    str(value)
                    for value in resolved_policy.deflector_naif_ids
                ),
                f"observer: {astrometric.observer_state.observer_id}",
                f"target: {astrometric.request.target}",
            ),
            corrections=frozenset(corrections),
        )
        geometry = SphericalPoints(
            np.array((float(ra.hours) * 15.0,)),
            np.array((float(dec.degrees),)),
            coordinate_spec=coordinate_spec,
            ids=np.array((astrometric.request.target,), dtype=object),
        )
        return ApparentDirection(
            astrometric=astrometric,
            policy=resolved_policy,
            geometry=geometry,
            provenance=(
                "consumed accepted astrometric vector without observe()",
                "Skyfield apparent() applied deflection then aberration",
            ),
        )

    @staticmethod
    def _validate_observer_state(astrometric, centre):
        state = astrometric.observer_state
        position_residual = max(
            abs(actual - retained)
            for actual, retained in zip(centre.position.au, state.position)
        )
        velocity_residual = max(
            abs(actual - retained)
            for actual, retained in zip(
                centre.velocity.au_per_d,
                state.velocity,
            )
        )
        if position_residual > 1.0e-15 or velocity_residual > 1.0e-15:
            raise ValueError(
                "observer barycentric state does not match the astrometric result."
            )

