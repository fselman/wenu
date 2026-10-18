"""Synchronous registry and immutable, direction-only full-model sessions."""

from .errors import (
    AccuracyUnavailable, ClosedSession, IncompatibleContract, InvalidProviderResult,
    KernelError, OutsideCoverage, ProviderBusy, ProviderEvaluationError,
    ResourceMismatch, UnknownObject, UnsupportedCapability, InvalidQuery,
)
from .records import (
    CONTRACT, CapabilityDecision, CatalogueRef, CatalogueSnapshot, DirectionState,
    ProviderDescriptor, ProviderKey, ReferenceSpec, SessionPolicy, StateBatch,
    StateQuery, exact,
)


def invoke(provider, operation, *args, provider_key=None):
    try:
        return getattr(provider, operation)(*args)
    except KernelError:
        raise
    except Exception as exc:
        raise ProviderEvaluationError("provider " + operation + " failed", provider=provider_key) from exc


class Kernel:
    """Application assembly explicitly admits references and provider instances.

    Ownership transfers only after successful registration. Failed close leaves
    that registration available for explicit cleanup/retry. No finalizer, global
    registry, network acquisition or concurrency capability is provided.
    """

    def __init__(self, *, references):
        references = tuple(references)
        for reference in references:
            exact(reference, ReferenceSpec)
        self._references = frozenset(references)
        self._providers = {}
        self._busy = {}
        self._closed = False

    def _check(self):
        if self._closed:
            raise ClosedSession("kernel is closed")

    def register(self, provider, *, ownership):
        self._check()
        if ownership not in ("owned", "borrowed"):
            raise InvalidQuery("ownership must be owned or borrowed")
        for name in ("describe", "catalogue", "supports", "evaluate", "certify", "close"):
            if not callable(getattr(provider, name, None)):
                raise UnsupportedCapability("incomplete provider protocol")
        descriptor = invoke(provider, "describe")
        if type(descriptor) is not ProviderDescriptor:
            raise InvalidProviderResult("provider descriptor has the wrong type")
        if descriptor.key.contract_version != CONTRACT:
            raise IncompatibleContract("provider contract version not supported", provider=descriptor.key)
        if any(d.key.provider_id == descriptor.key.provider_id or p is provider
               for p, d, _ in self._providers.values()):
            raise ResourceMismatch("provider already registered", provider=descriptor.key)
        for admission in descriptor.admissions:
            if admission.reference not in self._references:
                raise UnsupportedCapability("reference has not been admitted by application assembly")
            if (admission.reference.representation, admission.reference.units) != ("direction", "rad"):
                raise UnsupportedCapability("only direction states are implemented in this slice")
            if not set(admission.capabilities) <= {"native_direction", "epoch_direction", "batch_evaluation"}:
                raise UnsupportedCapability("capability is outside this implementation slice")
            if not set(admission.model.dependencies) <= set(admission.catalogue.resources):
                raise ResourceMismatch("model resources are not bound by its catalogue")
        self._providers[descriptor.key] = provider, descriptor, ownership
        self._busy[descriptor.key] = 0
        return descriptor.key

    def unregister(self, provider):
        self._check()
        exact(provider, ProviderKey)
        if provider not in self._providers:
            raise ResourceMismatch("provider is not registered", provider=provider)
        if self._busy[provider]:
            raise ProviderBusy("provider has active sessions", provider=provider)
        instance, _, ownership = self._providers[provider]
        if ownership == "owned":
            invoke(instance, "close", provider_key=provider)
        del self._providers[provider]
        del self._busy[provider]

    def open_session(self, policy):
        self._check()
        exact(policy, SessionPolicy)
        bindings = {}
        snapshots = {}
        # No counters or published session state change until every binding and
        # catalogue validates. Providers own no per-session handles in this slice.
        for reference in policy.catalogues:
            key = reference.provider
            if key not in self._providers:
                raise ResourceMismatch("session provider is not registered", provider=key)
            instance, descriptor, _ = self._providers[key]
            if reference not in descriptor.catalogues:
                raise ResourceMismatch("catalogue is not advertised", provider=key)
            snapshot = invoke(instance, "catalogue", reference, provider_key=key)
            if type(snapshot) is not CatalogueSnapshot or snapshot.reference != reference:
                raise InvalidProviderResult("catalogue response does not match its binding", provider=key)
            records = {r.key: r for r in snapshot.objects}
            for admission in descriptor.admissions:
                if admission.catalogue == reference:
                    if not set(admission.objects) <= records.keys():
                        raise InvalidProviderResult("admission contains unknown objects", provider=key)
                    for obj in admission.objects:
                        if not set(admission.capabilities) <= set(records[obj].capabilities):
                            raise InvalidProviderResult("object lacks advertised capabilities", provider=key)
            bindings[key] = instance, descriptor
            snapshots[reference] = snapshot
        session = KernelSession(self, policy, bindings, snapshots)
        for key in bindings:
            self._busy[key] += 1
        return session

    def close(self):
        if self._closed:
            return
        if any(self._busy.values()):
            raise ProviderBusy("kernel has active sessions")
        for key in tuple(self._providers):
            self.unregister(key)
        self._closed = True

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, *exc):
        self.close()


class KernelSession:
    def __init__(self, kernel, policy, bindings, snapshots):
        self._kernel = kernel
        self._policy = policy
        self._bindings = bindings
        self._snapshots = snapshots
        self._cache = {}
        self._closed = False

    @property
    def policy(self):
        return self._policy

    def _check(self):
        if self._closed:
            raise ClosedSession("session is closed")

    def catalogue(self, reference):
        self._check()
        exact(reference, CatalogueRef)
        if reference not in self._snapshots:
            raise ResourceMismatch("catalogue is not bound by this session")
        return self._snapshots[reference]

    def evaluate(self, query):
        self._check()
        exact(query, StateQuery)
        snapshot = self.catalogue(query.catalogue)
        if query.evaluation_policy != "full_model" or query.coverage is not None:
            raise UnsupportedCapability("certification/temporal reuse is not implemented in this slice")
        if (query.accuracy.position_m is not None or query.accuracy.velocity_m_s is not None
                or query.accuracy.metric != "angular_separation"):
            raise UnsupportedCapability("direction query requires angular accuracy meaning")
        records = {r.key: r for r in snapshot.objects}
        for obj in query.objects:
            if obj not in records:
                raise UnknownObject("object is absent from this catalogue", object_key=obj)
        instance, descriptor = self._bindings[query.catalogue.provider]
        admissions = [a for a in descriptor.admissions if a.catalogue == query.catalogue
                      and a.model == query.model and a.reference == query.reference
                      and set(query.objects) <= set(a.objects)]
        if len(admissions) != 1:
            raise UnsupportedCapability("query must match exactly one advertised model/reference/subset")
        admission = admissions[0]
        if not set(admission.capabilities) & {"native_direction", "epoch_direction"}:
            raise UnsupportedCapability("model has no direction capability")
        for time in query.times:
            if not admission.coverage.contains(time) or any(
                not r.coverage.contains(time) for r in query.catalogue.resources
            ):
                raise OutsideCoverage("query is outside model/resource coverage", time=time)
        if query in self._cache:
            return self._cache[query]
        decision = invoke(instance, "supports", query, provider_key=descriptor.key)
        if type(decision) is not CapabilityDecision:
            raise InvalidProviderResult("supports returned an invalid decision")
        if not decision.supported:
            raise UnsupportedCapability(decision.reason, provider=descriptor.key)
        batch = invoke(instance, "evaluate", query, provider_key=descriptor.key)
        if type(batch) is not StateBatch or batch.query != query:
            raise InvalidProviderResult("batch does not preserve the requested scientific query")
        expected = tuple((time, obj) for time in query.times for obj in query.objects)
        if tuple((r.time, r.object_key) for r in batch.states) != expected:
            raise InvalidProviderResult("rows must match time-major requested order exactly")
        for row in batch.states:
            if (type(row) is not DirectionState or row.reference != query.reference
                    or row.anchor_time != row.time
                    or row.source_epoch not in records[row.object_key].source_epochs):
                raise InvalidProviderResult("state provenance/reference/anchor mismatch")
            numerical = row.evidence.numerical
            if numerical.status != "not_evaluated" and (
                numerical.units != "rad" or numerical.meaning != "angular_separation"
            ):
                raise InvalidProviderResult("numerical evidence has incompatible angular meaning")
            bound = query.accuracy.angular_rad
            if bound is not None and (numerical.status != "bounded" or numerical.value > bound):
                raise AccuracyUnavailable("provider cannot certify the requested numerical bound")
        # Publication follows complete response validation. A failed evaluation
        # never poisons the cache; no cache crosses sessions or providers.
        self._cache[query] = batch
        return batch

    def close(self):
        if self._closed:
            return
        for key in self._bindings:
            self._kernel._busy[key] -= 1
        self._cache.clear()
        self._bindings.clear()
        self._snapshots.clear()
        self._closed = True

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, *exc):
        self.close()
