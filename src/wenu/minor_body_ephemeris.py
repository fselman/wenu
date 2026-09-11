"""Offline minor-body states from one borrowed Horizons SPK resource."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from pathlib import Path
from threading import RLock
from types import SimpleNamespace

import numpy as np
import spiceypy
from astropy.time import Time
from skyfield.constants import AU_KM
from skyfield.errors import EphemerisRangeError

from wenu.ephemeris import (
    EphemerisResourceChain,
    EphemerisResourceIdentity,
    EphemerisState,
    EphemerisStateRequest,
    EphemerisStateSource,
)
from wenu.skyfield_ephemeris import (
    EphemerisCoverageError,
    EphemerisTargetError,
    UnsupportedEphemerisFrameError,
)


class UnsupportedEphemerisTimeScaleError(ValueError):
    """The minor-body adapter requires a TDB state instant."""


class EphemerisCompositionError(ValueError):
    """A dependency returned an incompatible state for composition."""


_CSPICE_LOCK = RLock()
_J2000_JD = 2451545.0
_SECONDS_PER_DAY = 86400.0


@dataclass(frozen=True)
class SpiceMinorBodySegment:
    """One CSPICE-evaluable SPK segment without kernel-pool composition."""

    kernel: object = field(repr=False, compare=False)
    descriptor: tuple[float, ...] = field(repr=False)
    target: int
    center: int
    frame_id: int
    data_type: int
    start_jd: float
    end_jd: float

    @property
    def spk_segment(self):
        """Expose coverage names shared with Skyfield SPK segments."""
        return self

    def at(self, time):
        """Evaluate this exact segment at one Skyfield TDB instant."""
        return self.kernel._evaluate(self, float(time.tdb))


class SpiceMinorBodyKernel:
    """Explicit owner of one DAF/SPK handle evaluated through CSPICE."""

    def __init__(self, path):
        self.path = Path(path).expanduser().resolve(strict=True)
        self._closed = False
        with _CSPICE_LOCK:
            self._handle = spiceypy.dafopr(str(self.path))
            try:
                spiceypy.dafbfs(self._handle)
                segments = []
                while spiceypy.daffna():
                    descriptor = spiceypy.dafgs(5)
                    bounds, integers = spiceypy.dafus(descriptor, 2, 6)
                    target, center, frame_id, data_type, _, _ = (
                        int(value) for value in integers
                    )
                    segments.append(
                        SpiceMinorBodySegment(
                            kernel=self,
                            descriptor=tuple(float(x) for x in descriptor),
                            target=target,
                            center=center,
                            frame_id=frame_id,
                            data_type=data_type,
                            start_jd=(
                                _J2000_JD + float(bounds[0]) / _SECONDS_PER_DAY
                            ),
                            end_jd=(
                                _J2000_JD + float(bounds[1]) / _SECONDS_PER_DAY
                            ),
                        )
                    )
            except Exception:
                spiceypy.dafcls(self._handle)
                self._closed = True
                raise
        self.segments = tuple(segments)

    def _evaluate(self, segment, tdb_jd):
        if self._closed:
            raise ValueError("minor-body SPK is closed.")
        et = (tdb_jd - _J2000_JD) * _SECONDS_PER_DAY
        with _CSPICE_LOCK:
            frame_id, state, center = spiceypy.spkpvn(
                self._handle,
                np.asarray(segment.descriptor),
                et,
            )
        if int(frame_id) != segment.frame_id or int(center) != segment.center:
            raise EphemerisCompositionError(
                "CSPICE returned a different segment frame or centre."
            )
        state = np.asarray(state, dtype=float)
        if state.shape != (6,) or not np.all(np.isfinite(state)):
            raise EphemerisCompositionError(
                "CSPICE returned a malformed minor-body state."
            )
        return SimpleNamespace(
            position=SimpleNamespace(
                au=tuple(float(value) / AU_KM for value in state[:3])
            ),
            velocity=SimpleNamespace(
                au_per_d=tuple(
                    float(value) * _SECONDS_PER_DAY / AU_KM
                    for value in state[3:]
                )
            ),
        )

    def close(self):
        """Close this kernel owner's DAF handle exactly once."""
        if self._closed:
            return
        with _CSPICE_LOCK:
            spiceypy.dafcls(self._handle)
        self._closed = True

    def __enter__(self):
        if self._closed:
            raise ValueError("minor-body SPK is closed.")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def _text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty.")
    return normalized


def _optional_text(value, *, name):
    if value is None:
        return None
    return _text(value, name=name)


def _texts(value, *, name):
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of strings.")
    try:
        return tuple(_text(item, name=f"{name} entry") for item in value)
    except TypeError as error:
        raise TypeError(f"{name} must be an iterable of strings.") from error


def _text_pairs(value, *, name):
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of text pairs.")
    try:
        pairs = tuple(tuple(item) for item in value)
    except TypeError as error:
        raise TypeError(
            f"{name} must be an iterable of text pairs."
        ) from error
    if any(len(item) != 2 for item in pairs):
        raise ValueError(f"{name} entries must contain exactly two values.")
    normalized = tuple(
        (
            _text(key, name=f"{name} key"),
            _text(item, name=f"{name} value"),
        )
        for key, item in pairs
    )
    keys = tuple(key for key, _ in normalized)
    if len(keys) != len(set(keys)):
        raise ValueError(f"{name} keys must be unique.")
    return normalized


@dataclass(frozen=True)
class MinorBodySolutionIdentity:
    """Immutable identity of one acquired Horizons orbit solution."""

    provider: str
    service_version: str
    wenu_target: str
    object_class: str
    primary_designation: str
    horizons_command: str
    provider_spk_id: str
    orbit_solution_id: str
    solution_date: str
    osculating_epoch: str
    reference_system: str
    iau_number: int | None = None
    name: str | None = None
    aliases: tuple[str, ...] = ()
    model_parameters: tuple[tuple[str, str], ...] = ()
    quality_fields: tuple[tuple[str, str], ...] = ()
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        for field_name in (
            "provider",
            "service_version",
            "wenu_target",
            "primary_designation",
            "horizons_command",
            "provider_spk_id",
            "orbit_solution_id",
            "solution_date",
            "osculating_epoch",
            "reference_system",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(getattr(self, field_name), name=field_name),
            )
        object_class = _text(
            self.object_class,
            name="object_class",
        ).lower()
        if object_class not in {"asteroid", "comet"}:
            raise ValueError("object_class must be 'asteroid' or 'comet'.")
        object.__setattr__(self, "object_class", object_class)
        try:
            provider_spk_id = int(self.provider_spk_id)
        except ValueError as error:
            raise ValueError(
                "provider_spk_id must be an integer string."
            ) from error
        if provider_spk_id == 0:
            raise ValueError(
                "provider_spk_id must not identify the barycentre."
            )
        object.__setattr__(self, "provider_spk_id", str(provider_spk_id))
        if self.iau_number is not None:
            if isinstance(self.iau_number, bool) or not isinstance(
                self.iau_number,
                int,
            ):
                raise TypeError("iau_number must be an integer or None.")
            if self.iau_number <= 0:
                raise ValueError("iau_number must be positive.")
        object.__setattr__(
            self,
            "name",
            _optional_text(self.name, name="name"),
        )
        aliases = _texts(self.aliases, name="aliases")
        if len(aliases) != len(set(aliases)):
            raise ValueError("aliases must not contain duplicates.")
        object.__setattr__(self, "aliases", aliases)
        object.__setattr__(
            self,
            "model_parameters",
            _text_pairs(self.model_parameters, name="model_parameters"),
        )
        object.__setattr__(
            self,
            "quality_fields",
            _text_pairs(self.quality_fields, name="quality_fields"),
        )
        object.__setattr__(
            self,
            "provenance",
            _texts(self.provenance, name="provenance"),
        )


@dataclass(frozen=True)
class MinorBodySegmentIdentity:
    """Ordered SPK segment identity retained by the borrowed provider."""

    index: int
    target_id: int
    centre_id: int
    coverage_start_jd: float
    coverage_end_jd: float
    frame_id: int = 1
    data_type: int | None = None

    def __post_init__(self):
        for name in ("index", "target_id", "centre_id", "frame_id"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer.")
        if self.frame_id != 1:
            raise ValueError(
                "minor-body SPK segments must use ICRF/J2000 frame 1."
            )
        if self.data_type is not None and (
            isinstance(self.data_type, bool)
            or not isinstance(self.data_type, int)
        ):
            raise TypeError("data_type must be an integer or None.")
        start = float(self.coverage_start_jd)
        end = float(self.coverage_end_jd)
        if not isfinite(start) or not isfinite(end) or not start < end:
            raise ValueError("segment coverage must be finite and increasing.")
        object.__setattr__(self, "coverage_start_jd", start)
        object.__setattr__(self, "coverage_end_jd", end)


@dataclass(frozen=True, kw_only=True)
class MinorBodyEphemerisState(EphemerisState):
    """A geometric state retaining its orbit solution and SPK segment."""

    solution: MinorBodySolutionIdentity
    segment: MinorBodySegmentIdentity

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.solution, MinorBodySolutionIdentity):
            raise TypeError("solution must be a MinorBodySolutionIdentity.")
        if not isinstance(self.segment, MinorBodySegmentIdentity):
            raise TypeError("segment must be a MinorBodySegmentIdentity.")
        if self.provider_target_id != self.solution.provider_spk_id:
            raise ValueError(
                "provider_target_id must match the minor-body solution."
            )
        if int(self.provider_target_id) != self.segment.target_id:
            raise ValueError(
                "selected segment target must match the minor-body solution."
            )


def _sha256(path):
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_minor_body_resource_identity(kernel, *, target_id, model):
    try:
        path = Path(kernel.path).expanduser().resolve(strict=True)
    except (AttributeError, OSError, TypeError) as error:
        raise TypeError(
            "small_body_kernel must expose an existing resolved path."
        ) from error
    segments = tuple(
        segment
        for segment in getattr(kernel, "segments", ())
        if getattr(segment, "target", None) == target_id
    )
    if not segments:
        raise EphemerisTargetError(
            "small-body kernel does not contain the declared provider "
            f"SPK ID {target_id}."
        )
    try:
        coverage = tuple(
            (
                float(segment.spk_segment.start_jd),
                float(segment.spk_segment.end_jd),
            )
            for segment in segments
        )
    except (AttributeError, TypeError, ValueError) as error:
        raise TypeError(
            "minor-body segments must expose finite SPK coverage."
        ) from error
    if any(
        not isfinite(start) or not isfinite(end) or not start < end
        for start, end in coverage
    ):
        raise ValueError(
            "minor-body segment coverage must be finite and increasing."
        )
    return EphemerisResourceIdentity(
        provider="Skyfield/JPL Horizons SPK",
        model=_text(model, name="model"),
        filename=path.name,
        sha256=_sha256(path),
        coverage_start=f"JD {min(start for start, _ in coverage):.8f}",
        coverage_end=f"JD {max(end for _, end in coverage):.8f}",
        coverage_time_scale="tdb",
        provenance=(
            f"resolved path: {path}",
            f"target SPK ID: {target_id}",
            f"target segments: {len(segments)}",
            "exact coverage retained by ordered segment identities",
        ),
    )


class SkyfieldMinorBodyStateSource:
    """Compose one local small-body SPK with a planetary state source."""

    def __init__(
        self,
        *,
        small_body_kernel,
        planetary_source,
        timescale,
        resource,
        solution,
    ):
        if not isinstance(planetary_source, EphemerisStateSource):
            raise TypeError(
                "planetary_source must satisfy EphemerisStateSource."
            )
        if not isinstance(resource, EphemerisResourceChain):
            raise TypeError("resource must be an EphemerisResourceChain.")
        if not isinstance(solution, MinorBodySolutionIdentity):
            raise TypeError("solution must be a MinorBodySolutionIdentity.")
        if not callable(getattr(timescale, "from_astropy", None)):
            raise TypeError("timescale must provide from_astropy().")
        segments = tuple(getattr(small_body_kernel, "segments", ()))
        target_id = int(solution.provider_spk_id)
        matched = []
        for index, segment in enumerate(segments):
            if getattr(segment, "target", None) != target_id:
                continue
            try:
                raw = segment.spk_segment
                identity = MinorBodySegmentIdentity(
                    index=index,
                    target_id=int(segment.target),
                    centre_id=int(segment.center),
                    coverage_start_jd=raw.start_jd,
                    coverage_end_jd=raw.end_jd,
                    frame_id=int(getattr(segment, "frame_id", 1)),
                    data_type=getattr(segment, "data_type", None),
                )
            except (AttributeError, TypeError, ValueError) as error:
                raise TypeError(
                    "minor-body segments must expose target, centre, and "
                    "finite SPK coverage."
                ) from error
            matched.append((segment, identity))
        if not matched:
            raise EphemerisTargetError(
                "small-body kernel does not contain the declared provider "
                f"SPK ID {target_id}."
            )
        planetary_resource = getattr(planetary_source, "resource", None)
        if not isinstance(planetary_resource, EphemerisResourceIdentity):
            raise TypeError(
                "planetary_source must expose one EphemerisResourceIdentity."
            )
        if planetary_resource not in resource.dependencies:
            raise ValueError(
                "resource dependencies must include the planetary source."
            )
        self._small_body_kernel = small_body_kernel
        self._planetary_source = planetary_source
        self._timescale = timescale
        self._segments = tuple(matched)
        self.resource = resource
        self.solution = solution

    @classmethod
    def from_kernels(
        cls,
        *,
        small_body_kernel,
        planetary_source,
        timescale,
        solution,
        model,
    ):
        """Borrow resolved resources and fingerprint the small-body SPK."""
        if not isinstance(solution, MinorBodySolutionIdentity):
            raise TypeError("solution must be a MinorBodySolutionIdentity.")
        if not isinstance(planetary_source, EphemerisStateSource):
            raise TypeError(
                "planetary_source must satisfy EphemerisStateSource."
            )
        if not isinstance(
            getattr(planetary_source, "resource", None),
            EphemerisResourceIdentity,
        ):
            raise TypeError(
                "planetary_source must expose one EphemerisResourceIdentity."
            )
        primary = _resolve_minor_body_resource_identity(
            small_body_kernel,
            target_id=int(solution.provider_spk_id),
            model=model,
        )
        segment_provenance = tuple(
            (
                f"ordered segment {index}: target {segment.target}, "
                f"centre {segment.center}, "
                f"frame {getattr(segment, 'frame_id', 1)}, "
                f"type {getattr(segment, 'data_type', 'unreported')}, "
                f"JD {segment.spk_segment.start_jd:.8f} through "
                f"{segment.spk_segment.end_jd:.8f} TDB"
            )
            for index, segment in enumerate(small_body_kernel.segments)
        )
        resource = EphemerisResourceChain(
            primary=primary,
            dependencies=(planetary_source.resource,),
            provenance=(
                "primary: acquired Horizons small-body SPK",
                "dependency: resolved planetary ephemeris",
            )
            + segment_provenance,
        )
        return cls(
            small_body_kernel=small_body_kernel,
            planetary_source=planetary_source,
            timescale=timescale,
            resource=resource,
            solution=solution,
        )

    def state(self, request):
        """Return one composed geometric state at a declared TDB instant."""
        if not isinstance(request, EphemerisStateRequest):
            raise TypeError("request must be an EphemerisStateRequest.")
        if request.target != self.solution.wenu_target:
            raise EphemerisTargetError(
                "request target does not match the resolved minor-body "
                "solution."
            )
        if request.frame != "icrf":
            raise UnsupportedEphemerisFrameError(
                "minor-body SPK adapter supports only frame='icrf'."
            )
        if request.time_scale != "tdb":
            raise UnsupportedEphemerisTimeScaleError(
                "minor-body SPK adapter supports only time_scale='tdb'."
            )
        astropy_time = Time(request.instant, scale="tdb")
        time = self._timescale.from_astropy(astropy_time)
        tdb = float(time.tdb)
        selected = None
        for segment, identity in reversed(self._segments):
            if identity.coverage_start_jd <= tdb <= identity.coverage_end_jd:
                selected = (segment, identity)
                break
        if selected is None:
            raise EphemerisCoverageError(
                f"requested TDB JD {tdb:.8f} is outside minor-body segment "
                "coverage."
            )
        segment, identity = selected
        try:
            relative = segment.at(time)
        except EphemerisRangeError as error:
            raise EphemerisCoverageError(
                "requested minor-body state is outside segment coverage."
            ) from error
        centre_request = EphemerisStateRequest(
            target=str(identity.centre_id),
            centre=request.centre,
            frame="icrf",
            instant=request.instant,
            time_scale="tdb",
        )
        centre_state = self._planetary_source.state(centre_request)
        if centre_state.request != centre_request:
            raise EphemerisCompositionError(
                "planetary source returned a different state request."
            )
        if centre_state.resource not in self.resource.dependencies:
            raise EphemerisCompositionError(
                "planetary state resource is not a declared dependency."
            )
        if (
            centre_state.position_unit != "au"
            or centre_state.velocity_unit != "au/day"
        ):
            raise EphemerisCompositionError(
                "planetary state must use AU and AU/day."
            )
        position = tuple(
            float(body) + float(centre)
            for body, centre in zip(
                relative.position.au,
                centre_state.position,
            )
        )
        velocity = tuple(
            float(body) + float(centre)
            for body, centre in zip(
                relative.velocity.au_per_d,
                centre_state.velocity,
            )
        )
        return MinorBodyEphemerisState(
            request=request,
            position=position,
            velocity=velocity,
            position_unit="au",
            velocity_unit="au/day",
            resource=self.resource,
            provider_target_id=self.solution.provider_spk_id,
            provider_centre_id=centre_state.provider_centre_id,
            solution=self.solution,
            segment=identity,
            provenance=(
                "simultaneous geometric target-minus-centre state",
                "Horizons small-body segment composed with planetary state",
                f"selected ordered segment: {identity.index}",
                f"orbit solution: {self.solution.orbit_solution_id}",
                "Skyfield ICRF axes",
            ),
        )
