"""Shared immutable direction-table provider; no catalogue decoding or graphics.

Native stellar, source lookup and explicit static models share registration/value/lifetime
mechanics. Source interpretation and model selection remain with domain owners.
"""
from __future__ import annotations

from hashlib import sha256
import json
from math import cos, sin, radians, degrees, atan2, hypot, sqrt, fsum, isfinite

from wenu_kernel import Kernel
from wenu_kernel.errors import ClosedSession, InvalidQuery, ResourceMismatch, UnsupportedCapability
from wenu_kernel.records import (
    AccuracyRequest, CapabilityDecision, CatalogueRef, CatalogueSnapshot,
    DirectionState, ExternalId, ModelAdmission, ModelRef, ObjectKey, ObjectRecord,
    ProviderDescriptor, ProviderKey, ReferenceSpec, ResourceRef, SessionPolicy,
    StateBatch, StateQuery, TimePoint, UnboundedCoverage, UncertaintyChannel,
    UncertaintyEvidence,
)


def _digest(value):
    return sha256(json.dumps(value, separators=(",", ":"), ensure_ascii=True,
                             allow_nan=False).encode("ascii")).hexdigest()


def _text(value):
    if type(value) is not str or not value or value.strip() != value:
        raise InvalidQuery("catalogue identifiers must be nonempty trimmed strings")
    return value


def _unit_direction(lon, lat):
    lon, lat = radians(lon % 360.0), radians(lat)
    c = cos(lat)
    vector = (c * cos(lon), c * sin(lon), sin(lat))
    norm = sqrt(fsum(value * value for value in vector))
    return tuple(value / norm for value in vector)


def catalogue_direction_angles(states, rows):
    """Decode kernel results, retaining exact source encoding when identical.

    Native catalogue geometry historically preserves input floating values.
    Keep that encoding only for the exact matching returned unit vector; a
    different vector is decoded from the kernel result. This is not failure
    recovery and never suppresses a refused or failed state query.
    """
    angles = []
    for state, (_, lon, lat) in zip(states, rows, strict=True):
        if state.vector == _unit_direction(lon, lat):
            angles.append((lon, lat))
        else:
            x, y, z = state.vector
            angles.append((degrees(atan2(y, x)) % 360.0,
                           degrees(atan2(z, hypot(x, y)))))
    return tuple(angles)


class CatalogueDirectionProvider:
    """Immutable input-table adapter; no acquisition or propagation.

    Rows are (identifier, longitude_degrees, latitude_degrees). Identity binds
    copied binary inputs/epoch, not an invented original catalogue-file digest.
    Physical and numerical uncertainty remain explicitly unknown.
    """

    def __init__(self, rows, *, namespace, source_epoch, provenance, catalogue_edition,
                 reference, capability, semantic_type, provider_id, resource_id,
                 model_id, coverage, source_identity=(), source_epochs=None):
        namespace, catalogue_edition = _text(namespace), _text(catalogue_edition)
        if capability not in ("native_direction", "static_direction", "catalogue_lookup"):
            raise UnsupportedCapability("unsupported catalogue direction model")
        if source_epoch is not None and type(source_epoch) is not TimePoint:
            raise InvalidQuery("source epoch must be an explicit TimePoint or None")
        if source_epoch is None and capability not in ("static_direction", "catalogue_lookup"):
            raise InvalidQuery("an explicit source epoch is required")
        provenance = tuple(_text(item) for item in provenance)
        if not provenance:
            raise InvalidQuery("source provenance is required")
        copied = []
        for identifier, lon, lat in rows:
            _text(identifier)
            if (type(lon) not in (int, float) or type(lat) not in (int, float)
                    or not isfinite(lon) or not isfinite(lat) or not -90 <= lat <= 90):
                raise InvalidQuery("native directions must be finite with valid latitude")
            copied.append((identifier, float(lon), float(lat)))
        self._rows = tuple(copied)
        epochs = ((source_epoch,) * len(self._rows) if source_epochs is None else tuple(source_epochs))
        if (len(epochs) != len(self._rows)
                or any(epoch is not None and type(epoch) is not TimePoint for epoch in epochs)
                or capability == "native_direction" and any(epoch is None for epoch in epochs)):
            raise InvalidQuery("source epochs must align with rows and the admitted model")
        keys = tuple(ObjectKey(namespace + ":" + row[0]) for row in self._rows)
        if len(set(keys)) != len(keys):
            raise InvalidQuery("duplicate native catalogue identifiers")
        self._lookup = dict(zip(keys, self._rows))
        self._epochs = dict(zip(keys, epochs))
        self._closed = False
        self._epoch = source_epoch
        self._scale = coverage.scale
        key = ProviderKey(provider_id, "1")
        resource_digest = _digest((namespace, catalogue_edition,
                                  None if source_epoch is None else (source_epoch.jd1, source_epoch.jd2, source_epoch.scale),
                                  provenance,
                                  [(i, lon.hex(), lat.hex()) for i, lon, lat in self._rows]))
        if source_identity:
            resource_digest = _digest((resource_digest, source_identity))
        if source_epochs is not None:
            resource_digest = _digest((resource_digest, tuple(None if epoch is None else
                (epoch.jd1, epoch.jd2, epoch.scale) for epoch in epochs)))
        resource = ResourceRef(resource_id, "1", resource_digest,
                               coverage, "immutable copied table; no acquisition", provenance)
        catalogue = CatalogueRef(key, (resource,), _digest([k.value for k in keys]))
        model = ModelRef(model_id, "1",
                         _digest(("lookup-only", resource_digest)), (resource,))
        capabilities = (capability, "batch_evaluation")
        records = tuple(ObjectRecord(k, (ExternalId(namespace, catalogue_edition, row[0]),),
                                     semantic_type, (() if epoch is None else (epoch,)), capabilities, provenance)
                        for k, row, epoch in zip(keys, self._rows, epochs))
        self._catalogue = CatalogueSnapshot(catalogue, records)
        self._admission = ModelAdmission(catalogue, model, reference,
                                        keys, capabilities, coverage)
        self._descriptor = ProviderDescriptor(key, (catalogue,), (self._admission,),
                                              "offline native lookup; no propagation")
        self._evidence = UncertaintyEvidence(*(
            UncertaintyChannel("not_evaluated", None, "rad", meaning)
            for meaning in ("catalogue measurement", "no propagation model", "angular_separation")
        ))

    def _check(self):
        if self._closed:
            raise ClosedSession("native catalogue provider is closed")

    def describe(self):
        self._check()
        return self._descriptor

    def catalogue(self, reference):
        self._check()
        if reference != self._catalogue.reference:
            raise ResourceMismatch("native catalogue binding mismatch")
        return self._catalogue

    def supports(self, query):
        self._check()
        if type(query) is not StateQuery:
            return CapabilityDecision(False, "a typed state query is required")
        admission = self._admission
        if (query.catalogue, query.model, query.reference) != (
                admission.catalogue, admission.model, admission.reference):
            return CapabilityDecision(False, "catalogue/model/native reference mismatch")
        if any(key not in self._lookup for key in query.objects):
            return CapabilityDecision(False, "unknown native object")
        if any(time.scale != self._scale for time in query.times):
            return CapabilityDecision(False, "explicit time conversion is required")
        if (query.evaluation_policy != "full_model" or query.coverage is not None
                or query.require_velocity or query.accuracy != AccuracyRequest()):
            return CapabilityDecision(False, "no accuracy bound, velocity or temporal certificate")
        return CapabilityDecision(True, "source directions only; not epoch astrometry")

    def _direction(self, key):
        _, lon, lat = self._lookup[key]
        return _unit_direction(lon, lat)

    def evaluate(self, query):
        decision = self.supports(query)
        if not decision.supported:
            raise UnsupportedCapability(decision.reason)
        return StateBatch(query, tuple(
            DirectionState(key, time, self._epochs[key], time, query.reference,
                           self._direction(key), self._evidence)
            for time in query.times for key in query.objects
        ))

    def certify(self, query, anchor):
        self._check()
        raise UnsupportedCapability("catalogue direction model does not certify temporal reuse")

    def close(self):
        self._closed = True



def catalogue_direction_states(provider, instant):
    """Evaluate one copied table in an owned kernel scope; no fallback path."""
    caller_owned = True
    try:
        descriptor = provider.describe()
        admission = descriptor.admissions[0]
        if not admission.objects:
            return ()
        with Kernel(references=(admission.reference,)) as kernel:
            kernel.register(provider, ownership="owned")
            caller_owned = False
            with kernel.open_session(SessionPolicy(descriptor.catalogues)) as session:
                return session.evaluate(StateQuery(
                    admission.catalogue, admission.model, admission.objects,
                    (instant,), admission.reference, AccuracyRequest(),
                )).states
    finally:
        if caller_owned:
            provider.close()
