"""Skyfield adapter for one already-resolved JPL SPK resource."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re

from astropy.time import Time
from skyfield.errors import EphemerisRangeError

from wenu.ephemeris import (
    EphemerisResourceIdentity,
    EphemerisState,
    EphemerisStateRequest,
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
    start = min(starts)
    end = max(ends)
    if not start < end:
        raise ValueError("kernel coverage must have a positive interval.")
    return start, end


def _sha256(path):
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _model_from_filename(filename):
    match = re.fullmatch(r"de(\d+)[a-z]*\.bsp", filename, flags=re.IGNORECASE)
    if match is None:
        raise ValueError(
            "model must be supplied when the kernel filename is not a "
            "DE-series BSP name."
        )
    return f"DE{match.group(1)}"


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
        _model_from_filename(path.name)
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
        ),
    )


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
        try:
            provider_id = self._kernel.decode(key)
            vector = self._kernel[provider_id]
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

        astropy_time = Time(request.instant, scale=request.time_scale)
        time = self._timescale.from_astropy(astropy_time)
        tdb = float(time.tdb)
        start, end = self._coverage_jd
        if not start <= tdb <= end:
            raise EphemerisCoverageError(
                f"requested TDB JD {tdb:.8f} is outside kernel coverage "
                f"{start:.8f} through {end:.8f}."
            )

        target, target_id = self._body(request.target, role="target")
        centre, centre_id = self._body(request.centre, role="centre")
        try:
            state = (target - centre).at(time)
        except EphemerisRangeError as error:
            raise EphemerisCoverageError(
                "requested target-centre state is outside segment coverage."
            ) from error

        return EphemerisState(
            request=request,
            position=tuple(state.position.au),
            velocity=tuple(state.velocity.au_per_d),
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
