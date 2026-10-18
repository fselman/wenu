"""Immutable identity, time, catalogue, native-state and certificate vocabulary.

No time conversion, physical propagation or numerical backend lives here.
Constructor failures are InvalidQuery; providers must publish these exact
record types, never mutable subclasses or opaque numerical buffers.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, fsum, ulp
from typing import Literal

from .errors import InvalidQuery, TimeConversionUnavailable

CONTRACT = "wenu.kernel/1.0"
SCALES = ("tai", "tt", "tdb", "tcb")


def text(value):
    if type(value) is not str or not value or value.strip() != value:
        raise InvalidQuery("expected a nonempty trimmed string")


def digest(value):
    text(value)
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise InvalidQuery("expected a lowercase SHA-256 digest")


def finite(value):
    if type(value) not in (int, float):
        raise InvalidQuery("expected a finite real number, not bool")
    try:
        converted = float(value)
    except OverflowError as exc:
        raise InvalidQuery("real number exceeds supported float precision") from exc
    if not isfinite(converted):
        raise InvalidQuery("expected a finite real number")
    return converted


def exact(value, cls):
    if type(value) is not cls:
        raise InvalidQuery("expected exact record type " + cls.__name__)


def sequence(record, name, cls, *, unique=False, nonempty=False):
    values = getattr(record, name)
    if type(values) not in (tuple, list):
        raise InvalidQuery("expected tuple/list for " + name)
    values = tuple(values)
    for value in values:
        if cls is str:
            text(value)
        else:
            exact(value, cls)
    if nonempty and not values:
        raise InvalidQuery("empty " + name)
    if unique and len(set(values)) != len(values):
        raise InvalidQuery("duplicate " + name)
    object.__setattr__(record, name, values)


@dataclass(frozen=True, slots=True)
class TimePoint:
    jd1: int
    jd2: float
    scale: Literal["tai", "tt", "tdb", "tcb"]

    def __post_init__(self):
        text(self.scale)
        if type(self.jd1) is int:
            day = self.jd1
        elif type(self.jd1) is float and isfinite(self.jd1) and self.jd1.is_integer():
            day = int(self.jd1)
        else:
            raise InvalidQuery("jd1 must be an integer-valued day")
        fraction = finite(self.jd2)
        if not -0.5 <= fraction < 0.5 or self.scale not in SCALES:
            raise InvalidQuery("canonical fractional day or time scale invalid")
        object.__setattr__(self, "jd1", day)
        object.__setattr__(self, "jd2", fraction if fraction else 0.0)


@dataclass(frozen=True, slots=True)
class TimeSpan:
    start: TimePoint
    stop: TimePoint

    def __post_init__(self):
        exact(self.start, TimePoint)
        exact(self.stop, TimePoint)
        if self.start.scale != self.stop.scale or self.key(self.start) > self.key(self.stop):
            raise InvalidQuery("coverage must be ordered on one time basis")

    @staticmethod
    def key(time):
        return time.jd1, time.jd2

    def contains(self, time):
        exact(time, TimePoint)
        if time.scale != self.start.scale:
            raise TimeConversionUnavailable("explicit time conversion is required", time=time)
        return self.key(self.start) <= self.key(time) <= self.key(self.stop)


@dataclass(frozen=True, slots=True)
class UnboundedCoverage:
    """Explicit model coverage; never inferred from a missing value."""

    scale: str

    def __post_init__(self):
        text(self.scale)
        if self.scale not in SCALES:
            raise InvalidQuery("invalid coverage scale")

    def contains(self, time):
        exact(time, TimePoint)
        if time.scale != self.scale:
            raise TimeConversionUnavailable("explicit time conversion is required", time=time)
        return True


def coverage(value):
    if type(value) not in (TimeSpan, UnboundedCoverage):
        raise InvalidQuery("coverage must be explicit")


@dataclass(frozen=True, slots=True)
class ObjectKey:
    value: str

    def __post_init__(self):
        text(self.value)
        if ":" not in self.value or any(not p for p in self.value.split(":")):
            raise InvalidQuery("object key must have a namespace")


@dataclass(frozen=True, slots=True)
class ExternalId:
    catalogue: str
    edition: str
    identifier: str
    component: str | None = None

    def __post_init__(self):
        for value in (self.catalogue, self.edition, self.identifier):
            text(value)
        if self.component is not None:
            text(self.component)


@dataclass(frozen=True, slots=True)
class ProviderKey:
    provider_id: str
    software_version: str
    contract_version: str = CONTRACT

    def __post_init__(self):
        for value in (self.provider_id, self.software_version, self.contract_version):
            text(value)


@dataclass(frozen=True, slots=True)
class ResourceRef:
    resource_id: str
    edition: str
    sha256: str
    coverage: TimeSpan | UnboundedCoverage
    policy: str
    provenance: tuple[str, ...]

    def __post_init__(self):
        for value in (self.resource_id, self.edition, self.policy):
            text(value)
        digest(self.sha256)
        coverage(self.coverage)
        sequence(self, "provenance", str, nonempty=True)


@dataclass(frozen=True, slots=True)
class ModelRef:
    model_id: str
    version: str
    configuration_digest: str
    dependencies: tuple[ResourceRef, ...]

    def __post_init__(self):
        text(self.model_id)
        text(self.version)
        digest(self.configuration_digest)
        sequence(self, "dependencies", ResourceRef, unique=True)


@dataclass(frozen=True, slots=True)
class CatalogueRef:
    provider: ProviderKey
    resources: tuple[ResourceRef, ...]
    membership_digest: str

    def __post_init__(self):
        exact(self.provider, ProviderKey)
        sequence(self, "resources", ResourceRef, unique=True)
        digest(self.membership_digest)


@dataclass(frozen=True, slots=True)
class ObjectRecord:
    key: ObjectKey
    external_ids: tuple[ExternalId, ...]
    semantic_type: str
    source_epochs: tuple[TimePoint, ...]
    capabilities: tuple[str, ...]
    provenance: tuple[str, ...]

    def __post_init__(self):
        exact(self.key, ObjectKey)
        text(self.semantic_type)
        sequence(self, "external_ids", ExternalId, unique=True)
        sequence(self, "source_epochs", TimePoint, unique=True)
        sequence(self, "capabilities", str, unique=True, nonempty=True)
        sequence(self, "provenance", str, nonempty=True)
        if set(self.capabilities) & {"native_direction", "epoch_direction"} and not self.source_epochs:
            raise InvalidQuery("direction sources must declare their source epoch")


@dataclass(frozen=True, slots=True)
class CatalogueSnapshot:
    reference: CatalogueRef
    objects: tuple[ObjectRecord, ...]

    def __post_init__(self):
        exact(self.reference, CatalogueRef)
        sequence(self, "objects", ObjectRecord)
        if len({r.key for r in self.objects}) != len(self.objects):
            raise InvalidQuery("duplicate catalogue object keys")


@dataclass(frozen=True, slots=True)
class ReferenceSpec:
    frame_id: str
    origin_id: str
    status: str
    representation: str
    units: str
    correction_policy: str
    equinox: TimePoint | None = None

    def __post_init__(self):
        for value in (self.frame_id, self.origin_id, self.status, self.representation,
                      self.units, self.correction_policy):
            text(value)
        if self.equinox is not None:
            exact(self.equinox, TimePoint)
        if self.frame_id == "icrs" and self.equinox is not None:
            raise InvalidQuery("ICRS has no equinox")


@dataclass(frozen=True, slots=True)
class ModelAdmission:
    catalogue: CatalogueRef
    model: ModelRef
    reference: ReferenceSpec
    objects: tuple[ObjectKey, ...]
    capabilities: tuple[str, ...]
    coverage: TimeSpan | UnboundedCoverage

    def __post_init__(self):
        exact(self.catalogue, CatalogueRef)
        exact(self.model, ModelRef)
        exact(self.reference, ReferenceSpec)
        sequence(self, "objects", ObjectKey, unique=True)
        sequence(self, "capabilities", str, unique=True, nonempty=True)
        coverage(self.coverage)


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    key: ProviderKey
    catalogues: tuple[CatalogueRef, ...]
    admissions: tuple[ModelAdmission, ...]
    resource_policy: str

    def __post_init__(self):
        exact(self.key, ProviderKey)
        sequence(self, "catalogues", CatalogueRef, unique=True, nonempty=True)
        sequence(self, "admissions", ModelAdmission, unique=True)
        text(self.resource_policy)
        if any(c.provider != self.key for c in self.catalogues):
            raise InvalidQuery("descriptor provider binding mismatch")
        if any(a.catalogue not in self.catalogues for a in self.admissions):
            raise InvalidQuery("admission catalogue is not advertised")


@dataclass(frozen=True, slots=True)
class AccuracyRequest:
    angular_rad: float | None = None
    position_m: float | None = None
    velocity_m_s: float | None = None
    metric: str = "angular_separation"

    def __post_init__(self):
        text(self.metric)
        for name in ("angular_rad", "position_m", "velocity_m_s"):
            value = getattr(self, name)
            if value is not None:
                value = finite(value)
                if value <= 0:
                    raise InvalidQuery("accuracy bounds must be positive")
                object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class StateQuery:
    catalogue: CatalogueRef
    model: ModelRef
    objects: tuple[ObjectKey, ...]
    times: tuple[TimePoint, ...]
    reference: ReferenceSpec
    accuracy: AccuracyRequest
    evaluation_policy: str = "full_model"
    coverage: TimeSpan | None = None
    require_velocity: bool = False

    def __post_init__(self):
        for value, cls in ((self.catalogue, CatalogueRef), (self.model, ModelRef),
                           (self.reference, ReferenceSpec), (self.accuracy, AccuracyRequest)):
            exact(value, cls)
        sequence(self, "objects", ObjectKey, unique=True, nonempty=True)
        sequence(self, "times", TimePoint, unique=True, nonempty=True)
        if type(self.require_velocity) is not bool:
            raise InvalidQuery("require_velocity must be bool")
        text(self.evaluation_policy)
        if self.evaluation_policy not in ("full_model", "bounded_reuse"):
            raise InvalidQuery("unknown evaluation policy")
        if self.coverage is not None:
            exact(self.coverage, TimeSpan)
            if not all(self.coverage.contains(t) for t in self.times):
                raise InvalidQuery("query coverage omits a requested sample")


@dataclass(frozen=True, slots=True)
class CapabilityDecision:
    supported: bool
    reason: str

    def __post_init__(self):
        if type(self.supported) is not bool:
            raise InvalidQuery("supported must be bool")
        text(self.reason)


@dataclass(frozen=True, slots=True)
class UncertaintyChannel:
    status: str
    value: float | None
    units: str
    meaning: str

    def __post_init__(self):
        text(self.status)
        text(self.units)
        text(self.meaning)
        if self.status not in ("bounded", "statistical", "not_evaluated"):
            raise InvalidQuery("unknown uncertainty status")
        if self.status == "not_evaluated":
            if self.value is not None:
                raise InvalidQuery("unknown uncertainty cannot have a numeric value")
        elif self.value is None or finite(self.value) < 0:
            raise InvalidQuery("uncertainty requires a nonnegative finite value")
        else:
            object.__setattr__(self, "value", finite(self.value))


@dataclass(frozen=True, slots=True)
class UncertaintyEvidence:
    measurement: UncertaintyChannel
    physical_model: UncertaintyChannel
    numerical: UncertaintyChannel

    def __post_init__(self):
        for value in (self.measurement, self.physical_model, self.numerical):
            exact(value, UncertaintyChannel)


@dataclass(frozen=True, slots=True)
class AnchorSelection:
    object_key: ObjectKey
    requested_time: TimePoint
    anchor_time: TimePoint

    def __post_init__(self):
        exact(self.object_key, ObjectKey)
        exact(self.requested_time, TimePoint)
        exact(self.anchor_time, TimePoint)


@dataclass(frozen=True, slots=True)
class DirectionReusePlan:
    query: StateQuery
    anchors: tuple[AnchorSelection, ...]
    method: ModelRef
    identity: str

    def __post_init__(self):
        exact(self.query, StateQuery)
        exact(self.method, ModelRef)
        sequence(self, "anchors", AnchorSelection, nonempty=True)
        digest(self.identity)


@dataclass(frozen=True, slots=True)
class ReuseCertificate:
    catalogue: CatalogueRef
    model: ModelRef
    anchor_identity: str
    objects: tuple[ObjectKey, ...]
    reference: ReferenceSpec
    validity: TimeSpan
    metric: str
    maximum_error: float
    method: ModelRef
    identity: str

    def __post_init__(self):
        for value, cls in ((self.catalogue, CatalogueRef), (self.model, ModelRef),
                           (self.reference, ReferenceSpec), (self.validity, TimeSpan),
                           (self.method, ModelRef)):
            exact(value, cls)
        digest(self.anchor_identity)
        digest(self.identity)
        sequence(self, "objects", ObjectKey, unique=True, nonempty=True)
        if len(self.objects) != 1:
            raise InvalidQuery("this slice certifies one original object/time anchor")
        text(self.metric)
        value = finite(self.maximum_error)
        if value < 0:
            raise InvalidQuery("certificate error cannot be negative")
        object.__setattr__(self, "maximum_error", value)


@dataclass(frozen=True, slots=True)
class DirectionState:
    """A nullable source epoch is admitted only by a static-direction session model."""

    object_key: ObjectKey
    time: TimePoint
    source_epoch: TimePoint | None
    anchor_time: TimePoint
    reference: ReferenceSpec
    vector: tuple[float, float, float]
    evidence: UncertaintyEvidence
    certificate_id: str | None = None

    def __post_init__(self):
        for value, cls in ((self.object_key, ObjectKey), (self.time, TimePoint),
                           (self.anchor_time, TimePoint),
                           (self.reference, ReferenceSpec), (self.evidence, UncertaintyEvidence)):
            exact(value, cls)
        if self.source_epoch is not None:
            exact(self.source_epoch, TimePoint)
        if type(self.vector) not in (tuple, list) or len(self.vector) != 3:
            raise InvalidQuery("direction must have three components")
        vector = tuple(finite(x) for x in self.vector)
        if abs(fsum(x*x for x in vector) - 1.0) > 8 * ulp(1.0):
            raise InvalidQuery("direction must already be a unit vector")
        if self.reference.representation != "direction" or self.reference.units != "rad":
            raise InvalidQuery("direction requires a radian direction reference")
        object.__setattr__(self, "vector", vector)
        if self.certificate_id is not None:
            digest(self.certificate_id)


@dataclass(frozen=True, slots=True)
class CartesianState:
    object_key: ObjectKey
    time: TimePoint
    source_epoch: TimePoint | None
    anchor_time: TimePoint
    reference: ReferenceSpec
    position_m: tuple[float, float, float]
    velocity_m_s: tuple[float, float, float] | None
    position_evidence: UncertaintyEvidence
    velocity_evidence: UncertaintyEvidence | None

    def __post_init__(self):
        for value, cls in ((self.object_key, ObjectKey), (self.time, TimePoint),
                           (self.anchor_time, TimePoint), (self.reference, ReferenceSpec),
                           (self.position_evidence, UncertaintyEvidence)):
            exact(value, cls)
        if self.source_epoch is not None:
            exact(self.source_epoch, TimePoint)
        if (self.reference.representation, self.reference.units) != ("cartesian", "m,m/s"):
            raise InvalidQuery("Cartesian output requires metres and metres/second")
        for name in ("position_m", "velocity_m_s"):
            values = getattr(self, name)
            if name == "velocity_m_s" and values is None:
                continue
            if type(values) not in (tuple, list) or len(values) != 3:
                raise InvalidQuery("Cartesian vectors require three components")
            object.__setattr__(self, name, tuple(finite(v) for v in values))
        if self.velocity_m_s is None:
            if self.velocity_evidence is not None:
                raise InvalidQuery("absent velocity cannot carry numerical evidence")
        else:
            exact(self.velocity_evidence, UncertaintyEvidence)

    @property
    def velocity_available(self):
        return self.velocity_m_s is not None


@dataclass(frozen=True, slots=True)
class StateBatch:
    query: StateQuery
    states: tuple[DirectionState | CartesianState, ...]
    reuse_certificates: tuple[ReuseCertificate, ...] = ()
    reuse_plan: DirectionReusePlan | None = None

    def __post_init__(self):
        exact(self.query, StateQuery)
        if type(self.states) not in (tuple, list) or any(
            type(state) not in (DirectionState, CartesianState) for state in self.states
        ):
            raise InvalidQuery("state batch requires typed direction or Cartesian records")
        object.__setattr__(self, "states", tuple(self.states))
        sequence(self, "reuse_certificates", ReuseCertificate, unique=True)
        if self.reuse_plan is not None:
            exact(self.reuse_plan, DirectionReusePlan)


@dataclass(frozen=True, slots=True)
class SessionPolicy:
    catalogues: tuple[CatalogueRef, ...]
    time_policy: str = "same_scale_only"
    fallback_policy: str = "none"
    reproducibility: str = "reproducible"

    def __post_init__(self):
        sequence(self, "catalogues", CatalogueRef, unique=True, nonempty=True)
        for value in (self.time_policy, self.fallback_policy, self.reproducibility):
            text(value)
        if (self.time_policy != "same_scale_only" or self.fallback_policy != "none"
                or self.reproducibility not in ("reproducible", "interactive_bounded")):
            raise InvalidQuery("session policy is outside the implemented foundation")
