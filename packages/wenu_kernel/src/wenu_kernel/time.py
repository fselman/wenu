"""Explicit, frozen admission of offline time-conversion adapters.

This service never converts state queries implicitly or chooses a conversion
chain. Adapters are borrowed, immutable, handle-free services. Resource
acquisition and verification of local resource bytes belong to their owners.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from .errors import (
    AccuracyUnavailable, IncompatibleContract, InvalidProviderResult,
    InvalidQuery, KernelError, OutsideCoverage, ProviderEvaluationError,
    ResourceMismatch, TimeConversionUnavailable,
)
from .records import (
    CONTRACT, SCALES, ModelRef, TimePoint, TimeSpan, UnboundedCoverage,
    coverage, exact, finite, sequence, text,
)


@dataclass(frozen=True, slots=True)
class TimeConversionAdmission:
    source_scale: str
    target_scale: str
    validity: TimeSpan | UnboundedCoverage
    model: ModelRef
    maximum_error_s: float
    provenance: tuple[str, ...]
    contract_version: str = CONTRACT

    def __post_init__(self):
        for value in (self.source_scale, self.target_scale, self.contract_version):
            text(value)
        if self.source_scale not in SCALES or self.target_scale not in SCALES:
            raise InvalidQuery("unsupported conversion scale")
        if self.source_scale == self.target_scale:
            raise InvalidQuery("identity conversion is owned by TimeService")
        coverage(self.validity)
        scale = (self.validity.scale if type(self.validity) is UnboundedCoverage
                 else self.validity.start.scale)
        if scale != self.source_scale:
            raise InvalidQuery("conversion validity must use the source scale")
        exact(self.model, ModelRef)
        for resource in self.model.dependencies:
            domain = resource.coverage
            scale = domain.scale if type(domain) is UnboundedCoverage else domain.start.scale
            if scale != self.source_scale:
                raise InvalidQuery("conversion resources must declare source-scale coverage")
        value = finite(self.maximum_error_s)
        if value < 0:
            raise InvalidQuery("conversion error bound cannot be negative")
        object.__setattr__(self, "maximum_error_s", value)
        sequence(self, "provenance", str, nonempty=True)


@dataclass(frozen=True, slots=True)
class TimeConversion:
    source: TimePoint
    target: TimePoint
    model: ModelRef
    numerical_error_s: float
    provenance: tuple[str, ...]

    def __post_init__(self):
        exact(self.source, TimePoint)
        exact(self.target, TimePoint)
        exact(self.model, ModelRef)
        value = finite(self.numerical_error_s)
        if value < 0:
            raise InvalidQuery("conversion error bound cannot be negative")
        object.__setattr__(self, "numerical_error_s", value)
        sequence(self, "provenance", str, nonempty=True)


class TimeAdapter(Protocol):
    def describe(self) -> TimeConversionAdmission: ...
    def convert(self, time: TimePoint, target_scale: str) -> TimeConversion: ...


# Exact JSON bytes: {"operation":"identity","version":1}
# Identity is resource-free and introduces no numerical error.
IDENTITY_MODEL = ModelRef("wenu.time:identity", "1",
                          sha256(b'{"operation":"identity","version":1}').hexdigest(), ())
IDENTITY_PROVENANCE = ("Exact identity on the same declared continuous time scale",)


def _call(adapter, method, *args, time=None):
    try:
        return getattr(adapter, method)(*args)
    except KernelError:
        raise
    except Exception as exc:
        raise ProviderEvaluationError("time adapter failed in " + method, time=time) from exc


class TimeService:
    """One explicitly admitted adapter per directed pair; no fallback or I/O.

    The constructor snapshots descriptors and the caller's collections. No
    register/unregister, sessions, handles or implicit ownership are introduced.
    Adapters must remain deterministic for the admitted immutable resources.
    """

    def __init__(self, adapters=(), *, admissions=()):
        if type(adapters) not in (tuple, list) or type(admissions) not in (tuple, list):
            raise InvalidQuery("adapters and admissions must be tuples/lists")
        allowed = tuple(admissions)
        for admission in allowed:
            exact(admission, TimeConversionAdmission)
            if admission.contract_version != CONTRACT:
                raise IncompatibleContract("time conversion contract mismatch")
        if len(set(allowed)) != len(allowed):
            raise InvalidQuery("duplicate time conversion admission")
        bindings = {}
        for adapter in tuple(adapters):
            if not all(callable(getattr(adapter, name, None)) for name in ("describe", "convert")):
                raise IncompatibleContract("time adapter lacks a required operation")
            admission = _call(adapter, "describe")
            if type(admission) is not TimeConversionAdmission:
                raise InvalidProviderResult("invalid time adapter descriptor")
            if admission.contract_version != CONTRACT:
                raise IncompatibleContract("time adapter contract mismatch")
            if admission not in allowed:
                raise ResourceMismatch("time conversion is not explicitly admitted")
            pair = admission.source_scale, admission.target_scale
            if pair in bindings:
                raise InvalidQuery("ambiguous time adapter pair")
            bindings[pair] = adapter, admission
        if set(allowed) != {a for _, a in bindings.values()}:
            raise ResourceMismatch("admitted time conversion has no adapter")
        self._bindings = bindings

    def convert(self, time: TimePoint, target_scale: str, *, maximum_error_s=None) -> TimeConversion:
        exact(time, TimePoint)
        text(target_scale)
        if target_scale not in SCALES:
            raise InvalidQuery("unsupported target time scale")
        if maximum_error_s is not None:
            maximum_error_s = finite(maximum_error_s)
            if maximum_error_s < 0:
                raise InvalidQuery("requested time error cannot be negative")
        if time.scale == target_scale:
            return TimeConversion(time, time, IDENTITY_MODEL, 0, IDENTITY_PROVENANCE)
        pair = time.scale, target_scale
        if pair not in self._bindings:
            raise TimeConversionUnavailable("no admitted direct time conversion", time=time)
        adapter, admission = self._bindings[pair]
        if not admission.validity.contains(time) or any(
            not r.coverage.contains(time) for r in admission.model.dependencies
        ):
            raise OutsideCoverage("time is outside conversion/resource coverage", time=time)
        result = _call(adapter, "convert", time, target_scale, time=time)
        if (type(result) is not TimeConversion or result.source != time
                or result.target.scale != target_scale or result.model != admission.model
                or result.provenance != admission.provenance
                or result.numerical_error_s > admission.maximum_error_s):
            raise InvalidProviderResult("time conversion does not match its admission", time=time)
        if maximum_error_s is not None and result.numerical_error_s > maximum_error_s:
            raise AccuracyUnavailable("requested conversion bound is unavailable", time=time)
        return result
