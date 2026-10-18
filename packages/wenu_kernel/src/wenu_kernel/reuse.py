"""Angular certificates and admission, independent of physical motion models.

Digest encodings below are versioned session-local identities, not the K5
persistent state envelope. Float hex strings retain exact binary values.
"""

from dataclasses import fields, replace
from hashlib import sha256
import json

from . import records as r
from .records import ReuseCertificate
from .errors import InvalidProviderResult, InvalidQuery, KernelError

_IDENTITY_TYPES = {
    r.TimePoint, r.TimeSpan, r.UnboundedCoverage, r.ObjectKey, r.ProviderKey,
    r.ResourceRef, r.ModelRef, r.CatalogueRef, r.ReferenceSpec, r.AccuracyRequest,
    r.StateQuery, r.DirectionState, r.StateBatch, r.UncertaintyChannel,
    r.UncertaintyEvidence,
    r.AnchorSelection,
}


def _encode(value):
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int:
        return ["integer", str(value)]
    if type(value) is float:
        return ["binary64", value.hex()]
    if type(value) is tuple:
        return [_encode(item) for item in value]
    if type(value) in _IDENTITY_TYPES:
        return [type(value).__name__, [[f.name, _encode(getattr(value, f.name))]
                                      for f in fields(value)]]
    raise InvalidQuery("unsupported value in session identity")


def _identity(schema, values):
    data = json.dumps([schema, _encode(values)], ensure_ascii=True,
                      allow_nan=False, separators=(",", ":")).encode("ascii")
    return sha256(data).hexdigest()


def direction_anchor_identity(anchor):
    """Identify one actual full-model object/time state, including its error."""
    r.exact(anchor, r.StateBatch)
    if (len(anchor.states) != 1 or len(anchor.query.objects) != 1
            or len(anchor.query.times) != 1 or anchor.reuse_certificates or anchor.reuse_plan is not None
            or anchor.query.evaluation_policy != "full_model"
            or anchor.query.coverage is not None):
        raise InvalidQuery("certificate anchors must be scalar full-model states")
    state = anchor.states[0]
    if (state.time != state.anchor_time or state.certificate_id is not None
            or state.time != anchor.query.times[0]
            or state.object_key != anchor.query.objects[0]):
        raise InvalidQuery("a reused direction cannot become a new certified anchor")
    return _identity("wenu_kernel/session-direction-anchor/2", (anchor,))


def reuse_plan_identity(plan):
    r.exact(plan, r.DirectionReusePlan)
    return _identity("wenu_kernel/session-direction-plan/1", (plan.query, plan.anchors, plan.method))


def make_reuse_plan(query: r.StateQuery, anchors: tuple[r.AnchorSelection, ...],
                    method: r.ModelRef) -> r.DirectionReusePlan:
    plan = r.DirectionReusePlan(query, anchors, method, "0" * 64)
    return replace(plan, identity=reuse_plan_identity(plan))


def validate_reuse_plan(plan, query, admission):
    if (type(plan) is not r.DirectionReusePlan or plan.query != query
            or plan.identity != reuse_plan_identity(plan)
            or not set(plan.method.dependencies) <= set(query.catalogue.resources)):
        raise InvalidProviderResult("canonical plan identity or source binding mismatch")
    expected = tuple((time, obj) for time in query.times for obj in query.objects)
    if tuple((a.requested_time, a.object_key) for a in plan.anchors) != expected:
        raise InvalidProviderResult("canonical plan must preserve exact time-major row selection")
    try:
        valid = all(admission.coverage.contains(a.anchor_time)
                    and all(resource.coverage.contains(a.anchor_time) for resource in query.catalogue.resources)
                    for a in plan.anchors)
    except KernelError as exc:
        raise InvalidProviderResult("canonical anchor uses an incompatible time basis") from exc
    if not valid:
        raise InvalidProviderResult("canonical anchor lies outside model/resource coverage")


def make_certificate(*, catalogue: r.CatalogueRef, model: r.ModelRef,
                     anchor_identity: str, objects: tuple[r.ObjectKey, ...],
                     reference: r.ReferenceSpec, validity: r.TimeSpan,
                     metric: str, maximum_error: float, method: r.ModelRef) -> ReuseCertificate:
    """Construct a typed envelope with its session-local content identity.

    Records own values only; hashing/admission depend on records, never the
    reverse. Inbound records still require full identity validation by core.
    """
    certificate = ReuseCertificate(catalogue, model, anchor_identity, objects,
                                    reference, validity, metric, maximum_error, method, "0" * 64)
    return replace(certificate, identity=certificate_identity(certificate))


def certificate_identity(certificate):
    r.exact(certificate, ReuseCertificate)
    values = tuple(getattr(certificate, f.name) for f in fields(certificate)
                   if f.name != "identity")
    return _identity("wenu_kernel/session-angular-certificate/1", values)


def validate_certificate(certificate, anchor, admission):
    """Fail closed for a provider claim with inconsistent identity or scope.

    The provider proves its physical bound. The kernel checks envelope meaning,
    whole-interval coverage and inclusion of the original approximation error.
    It never estimates proper motion, acceleration or uncertainty itself.
    """
    if type(certificate) is not ReuseCertificate:
        raise InvalidProviderResult("provider returned an invalid certificate type")
    query = anchor.query
    state = anchor.states[0]
    if (certificate.catalogue != query.catalogue or certificate.model != query.model
            or certificate.objects != query.objects or certificate.reference != query.reference
            or certificate.metric != "angular_separation"
            or certificate.anchor_identity != direction_anchor_identity(anchor)
            or certificate.identity != certificate_identity(certificate)
            or not set(certificate.method.dependencies) <= set(query.catalogue.resources)):
        raise InvalidProviderResult("certificate identity, resources or reference do not match anchor")
    numerical = state.evidence.numerical
    if (numerical.status != "bounded" or numerical.units != "rad"
            or numerical.meaning != "angular_separation"
            or certificate.maximum_error < numerical.value):
        raise InvalidProviderResult("certificate omits the original numerical bound")
    try:
        points = (certificate.validity.start, certificate.validity.stop)
        valid = certificate.validity.contains(state.anchor_time) and all(
            admission.coverage.contains(t)
            and all(resource.coverage.contains(t) for resource in query.catalogue.resources)
            for t in points)
    except KernelError as exc:
        raise InvalidProviderResult("certificate uses an incompatible time basis") from exc
    if not valid:
        raise InvalidProviderResult("certificate exceeds source/model coverage or omits anchor")


def qualifies(certificate, query, time):
    """Use exact comparisons: no epsilon widens an interval or requested bound."""
    points = (query.coverage.start, query.coverage.stop) if query.coverage else (time,)
    return (certificate.maximum_error <= query.accuracy.angular_rad
            and all(certificate.validity.contains(t) for t in points))
