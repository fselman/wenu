"""Synchronous native-state sessions and certified angular direction reuse."""

from dataclasses import replace

from .errors import (
    AccuracyUnavailable, ClosedSession, IncompatibleContract, InvalidProviderResult,
    KernelError, OutsideCoverage, ProviderBusy, ProviderEvaluationError,
    ResourceMismatch, UnknownObject, UnsupportedCapability, InvalidQuery,
)
from .records import (
    CONTRACT, CapabilityDecision, CatalogueRef, CatalogueSnapshot, DirectionState, CartesianState,
    ProviderDescriptor, ProviderKey, ReferenceSpec, SessionPolicy, StateBatch,
    StateQuery, exact,
)
from .reuse import validate_certificate, qualifies, validate_reuse_plan


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
            reference = admission.reference
            direction = (reference.representation, reference.units) == ("direction", "rad")
            cartesian = (reference.representation, reference.units) == ("cartesian", "m,m/s")
            if not direction and not cartesian:
                raise UnsupportedCapability("unsupported native representation/units")
            if not set(admission.capabilities) <= {
                "native_direction", "epoch_direction", "batch_evaluation", "direction_reuse_bound",
                "canonical_direction_reuse", "cartesian_state",
            }:
                raise UnsupportedCapability("capability is outside this implementation slice")
            direction_caps = {"native_direction", "epoch_direction", "direction_reuse_bound", "canonical_direction_reuse"}
            if ((direction and "cartesian_state" in admission.capabilities)
                    or (cartesian and (set(admission.capabilities) & direction_caps
                                       or "cartesian_state" not in admission.capabilities))):
                raise UnsupportedCapability("capabilities do not match the native representation")
            if "canonical_direction_reuse" in admission.capabilities and (
                "direction_reuse_bound" not in admission.capabilities
                or not callable(getattr(provider, "plan_reuse", None))
            ):
                raise UnsupportedCapability("canonical reuse requires a planner and direction bounds")
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
        self._reuse = {}
        self._canonical = {}
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
        if query.evaluation_policy == "full_model" and query.coverage is not None:
            raise UnsupportedCapability("interval certification requires bounded_reuse")
        if query.reference.representation == "direction":
            if query.evaluation_policy == "bounded_reuse" and query.accuracy.angular_rad is None:
                raise InvalidQuery("bounded angular reuse requires a positive angular bound")
            if (query.accuracy.position_m is not None or query.accuracy.velocity_m_s is not None
                    or query.accuracy.metric != "angular_separation" or query.require_velocity):
                raise UnsupportedCapability("direction query requires angular accuracy meaning")
        elif query.reference.representation == "cartesian":
            if query.evaluation_policy != "full_model":
                raise UnsupportedCapability("Cartesian temporal reuse is not implemented")
            if query.accuracy.angular_rad is not None or query.accuracy.metric != "euclidean_norm":
                raise UnsupportedCapability("Cartesian query requires SI Euclidean error meaning")
        else:
            raise UnsupportedCapability("unsupported state representation")
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
        required = {"cartesian_state"} if query.reference.representation == "cartesian" else {"native_direction", "epoch_direction"}
        if not set(admission.capabilities) & required:
            raise UnsupportedCapability("model lacks the requested state capability")
        coverage_points = query.times + ((query.coverage.start, query.coverage.stop) if query.coverage else ())
        for time in coverage_points:
            if not admission.coverage.contains(time) or any(
                not r.coverage.contains(time) for r in query.catalogue.resources
            ):
                raise OutsideCoverage("query is outside model/resource coverage", time=time)
        if query in self._cache:
            return self._cache[query]
        if query.evaluation_policy == "bounded_reuse":
            if (self.policy.reproducibility == "reproducible"
                    and "canonical_direction_reuse" in admission.capabilities):
                result = self._evaluate_canonical(query, records, instance, descriptor, admission)
                if result is not None:
                    return result
            return self._evaluate_bounded(query, records, instance, descriptor, admission)
        batch = self._evaluate_full(query, records, instance, descriptor)
        self._cache[query] = batch
        return batch

    def _evaluate_full(self, query, records, instance, descriptor):
        """Validate a complete backend batch without publishing any cache entry."""
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
            expected_type = CartesianState if query.reference.representation == "cartesian" else DirectionState
            if (type(row) is not expected_type or row.reference != query.reference
                    or row.anchor_time != row.time):
                raise InvalidProviderResult("state provenance/reference/anchor mismatch")
            source_epochs = records[row.object_key].source_epochs
            if ((row.source_epoch is None and source_epochs)
                    or (row.source_epoch is not None and row.source_epoch not in source_epochs)):
                raise InvalidProviderResult("state source epoch does not match catalogue provenance")
            if type(row) is CartesianState:
                self._validate_cartesian(row, query)
                continue
            if row.certificate_id is not None:
                raise InvalidProviderResult("full-model state cannot be a reused direction")
            numerical = row.evidence.numerical
            if numerical.status != "not_evaluated" and (
                numerical.units != "rad" or numerical.meaning != "angular_separation"
            ):
                raise InvalidProviderResult("numerical evidence has incompatible angular meaning")
            bound = query.accuracy.angular_rad
            if bound is not None and (numerical.status != "bounded" or numerical.value > bound):
                raise AccuracyUnavailable("provider cannot certify the requested numerical bound")
        if batch.reuse_certificates or batch.reuse_plan is not None:
            raise InvalidProviderResult("full-model provider output cannot contain reuse certificates")
        return batch

    @staticmethod
    def _validate_cartesian(row, query):
        needs_velocity = query.require_velocity or query.accuracy.velocity_m_s is not None
        if needs_velocity and not row.velocity_available:
            raise InvalidProviderResult("provider accepted required velocity but returned none")
        channels = [(row.position_evidence, query.accuracy.position_m, "m")]
        if row.velocity_available:
            channels.append((row.velocity_evidence, query.accuracy.velocity_m_s, "m/s"))
        for evidence, bound, units in channels:
            numerical = evidence.numerical
            if numerical.status != "not_evaluated" and (
                numerical.units != units or numerical.meaning != "euclidean_norm"
            ):
                raise InvalidProviderResult("Cartesian numerical evidence has incompatible units/metric")
            if bound is not None and (numerical.status != "bounded" or numerical.value > bound):
                raise AccuracyUnavailable("provider cannot certify requested Cartesian numerical bound")

    def _evaluate_canonical(self, query, records, instance, descriptor, admission):
        """Evaluate only provider-chosen anchors; cache history never chooses one.

        A provider that cannot supply the requested bound falls back to full
        evaluation. Invalid envelopes and backend errors fail closed. Neither
        path publishes a partial canonical cache.
        """
        try:
            plan = invoke(instance, "plan_reuse", query, provider_key=descriptor.key)
        except (UnsupportedCapability, AccuracyUnavailable):
            return None
        validate_reuse_plan(plan, query, admission)
        anchors, missing, staged = {}, {}, {}
        for selection in plan.anchors:
            key = (query.catalogue, query.model, query.reference, selection.object_key,
                   selection.anchor_time, query.accuracy)
            anchor = self._canonical.get(key)
            if anchor is not None:
                anchors[selection.anchor_time, selection.object_key] = anchor
            else:
                objects = missing.setdefault(selection.anchor_time, [])
                if selection.object_key not in objects:
                    objects.append(selection.object_key)
        for time, objects in missing.items():
            full = replace(query, objects=tuple(objects), times=(time,),
                           evaluation_policy="full_model", coverage=None)
            try:
                batch = self._evaluate_full(full, records, instance, descriptor)
            except (UnsupportedCapability, AccuracyUnavailable):
                return None
            for row in batch.states:
                scalar = replace(full, objects=(row.object_key,))
                anchor = StateBatch(scalar, (row,))
                anchors[time, row.object_key] = anchor
                key = (query.catalogue, query.model, query.reference, row.object_key, time, query.accuracy)
                staged[key] = anchor
        states, certificates = [], {}
        for selection in plan.anchors:
            anchor = anchors[selection.anchor_time, selection.object_key]
            request = replace(query, objects=(selection.object_key,), times=(selection.requested_time,))
            try:
                cert = invoke(instance, "certify", request, anchor, provider_key=descriptor.key)
            except (UnsupportedCapability, AccuracyUnavailable):
                return None
            validate_certificate(cert, anchor, admission)
            if not qualifies(cert, query, selection.requested_time):
                return None
            row = anchor.states[0]
            numerical = replace(row.evidence.numerical, value=cert.maximum_error)
            states.append(replace(row, time=selection.requested_time, certificate_id=cert.identity,
                                  evidence=replace(row.evidence, numerical=numerical)))
            certificates[cert.identity] = cert
        result = StateBatch(query, tuple(states), tuple(certificates[k] for k in sorted(certificates)), plan)
        self._canonical.update(staged)
        self._cache[query] = result
        return result

    @staticmethod
    def _reuse_key(query, obj):
        return query.catalogue, query.model, query.reference, obj

    def _evaluate_bounded(self, query, records, instance, descriptor, admission):
        # A warmness-dependent candidate set cannot define reproducible output.
        # Reproducible mode always falls back to the admitted full model here.
        interactive = self.policy.reproducibility == "interactive_bounded"
        results, certificates, staged_cache, staged_reuse = {}, {}, {}, []
        for time in query.times:
            missing = []
            for obj in query.objects:
                candidates = self._reuse.get(self._reuse_key(query, obj), {}).values() if interactive else ()
                candidates = [(anchor, cert) for anchor, cert in candidates if qualifies(cert, query, time)]
                if not candidates:
                    missing.append(obj)
                    continue
                anchor, cert = min(candidates, key=lambda pair: (
                    pair[1].maximum_error, pair[0].states[0].anchor_time.jd1,
                    pair[0].states[0].anchor_time.jd2, pair[1].identity))
                row = anchor.states[0]
                numerical = replace(row.evidence.numerical, value=cert.maximum_error)
                results[time, obj] = replace(row, time=time, certificate_id=cert.identity,
                                            evidence=replace(row.evidence, numerical=numerical))
                certificates[cert.identity] = cert
            if not missing:
                continue
            # One backend batch per time for all missing objects, not one
            # propagation call per star. Reuse never becomes a new anchor.
            full = replace(query, objects=tuple(missing), times=(time,),
                           evaluation_policy="full_model", coverage=None)
            batch = self._cache.get(full)
            if batch is None:
                batch = self._evaluate_full(full, records, instance, descriptor)
                staged_cache[full] = batch
            for row in batch.states:
                results[time, row.object_key] = row
                cert = None
                if "direction_reuse_bound" in admission.capabilities:
                    scalar = replace(full, objects=(row.object_key,))
                    anchor = StateBatch(scalar, (row,))
                    request = replace(query, objects=(row.object_key,), times=(time,))
                    try:
                        cert = invoke(instance, "certify", request, anchor, provider_key=descriptor.key)
                    except (UnsupportedCapability, AccuracyUnavailable) as exc:
                        if query.coverage is not None:
                            raise AccuracyUnavailable("whole-interval certification is unavailable") from exc
                    else:
                        validate_certificate(cert, anchor, admission)
                        certificates[cert.identity] = cert
                        staged_reuse.append((self._reuse_key(query, row.object_key), anchor, cert))
                if query.coverage is not None and (cert is None or not qualifies(cert, query, time)):
                    raise AccuracyUnavailable("certificate does not bound the whole requested interval")
        states = tuple(results[time, obj] for time in query.times for obj in query.objects)
        result = StateBatch(query, states, tuple(certificates[key] for key in sorted(certificates)))
        # All rows/certificates must succeed before either cache is changed.
        self._cache.update(staged_cache)
        for key, anchor, cert in staged_reuse:
            self._reuse.setdefault(key, {})[cert.identity] = anchor, cert
        self._cache[query] = result
        return result

    def close(self):
        if self._closed:
            return
        for key in self._bindings:
            self._kernel._busy[key] -= 1
        self._cache.clear()
        self._reuse.clear()
        self._canonical.clear()
        self._bindings.clear()
        self._snapshots.clear()
        self._closed = True

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, *exc):
        self.close()
