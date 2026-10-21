"""Adapt an existing geometric ephemeris evaluation to the Cartesian SDK.

The astronomical backend and light-time algorithm remain their existing owners.
Each request has a short-lived, borrowed registration: no cross-request state or
resource cache, temporal certificate, acquisition or ephemeris ownership.
"""

from dataclasses import replace
from hashlib import sha256
import json
from math import floor

from astropy.time import Time
from astropy import units as u

from wenu.ephemeris import (
    EphemerisResourceChain, EphemerisResourceIdentity,
    EphemerisState, EphemerisStateRequest,
)
from wenu_kernel.kernel import Kernel
from wenu_kernel.errors import ResourceMismatch, UnsupportedCapability
from wenu_kernel.records import (
    AccuracyRequest, CapabilityDecision, CartesianState, CatalogueRef,
    CatalogueSnapshot, ModelAdmission, ModelRef, ObjectKey, ObjectRecord,
    ProviderDescriptor, ProviderKey, ReferenceSpec, ResourceRef, SessionPolicy,
    StateBatch, StateQuery, TimePoint, TimeSpan, UncertaintyChannel,
    UncertaintyEvidence,
)


def _time_point(time):
    # Canonicalize the split JD without first summing a large Julian date.
    day = int(time.jd1)
    fraction = float(time.jd2) + float(time.jd1 - day)
    carry = floor(fraction + 0.5)
    return TimePoint(day + carry, fraction - carry, time.scale)


def _unknown(units):
    channel = UncertaintyChannel(
        "not_evaluated", None, units, "euclidean_norm"
    )
    return UncertaintyEvidence(channel, channel, channel)


class _EphemerisProvider:
    """One explicitly admitted target/centre/time over a borrowed backend."""

    def __init__(self, source, request):
        resource = source.resource
        if not isinstance(resource, (EphemerisResourceIdentity, EphemerisResourceChain)):
            raise TypeError("Cartesian adapter requires an ephemeris resource or chain.")
        self.source = source
        self.original_resource = resource
        self.request = request
        self.original = None
        self.key = ProviderKey("wenu:ephemeris", "1")
        self.object = ObjectKey("ephemeris:" + request.target)
        identity = json.dumps(
            [request.target, request.centre, request.frame],
            separators=(",", ":"), ensure_ascii=False,
        ).encode()
        resources = (
            (resource.primary,) + resource.dependencies
            if isinstance(resource, EphemerisResourceChain) else (resource,)
        )

        def endpoint(value):
            if value.startswith("JD "):
                return _time_point(Time(float(value[3:]), format="jd", scale="tdb"))
            return _time_point(Time(value, scale="tdb"))
        references = []
        for index, item in enumerate(resources):
            if item.coverage_time_scale != "tdb":
                raise UnsupportedCapability("ephemeris coverage requires TDB")
            domain = TimeSpan(endpoint(item.coverage_start), endpoint(item.coverage_end))
            references.append(ResourceRef(
                ("ephemeris:spk" if index == 0 else f"ephemeris:spk:{index}"),
                item.model, item.sha256, domain,
                "borrowed resolved offline resource; no acquisition",
                item.provenance or ("caller supplied ephemeris identity",),
            ))
        # Composition can be admitted only where every dependency is covered.
        # Exact segment gaps remain the existing backend's responsibility.
        coverage = TimeSpan(
            max((ref.coverage.start for ref in references), key=TimeSpan.key),
            min((ref.coverage.stop for ref in references), key=TimeSpan.key),
        )
        self.resources = tuple(references)
        self.resource = self.resources[0]
        self.catalogue_ref = CatalogueRef(
            self.key, self.resources, sha256(identity).hexdigest(),
        )
        self.model = ModelRef(
            "wenu:geometric-ephemeris", "1", sha256(identity).hexdigest(),
            self.resources,
        )
        self.reference = ReferenceSpec(
            request.frame, request.centre, "geometric", "cartesian", "m,m/s",
            "simultaneous geometric; no light-time or apparent corrections",
        )
        self.admission = ModelAdmission(
            self.catalogue_ref, self.model, self.reference, (self.object,),
            ("cartesian_state",), coverage,
        )
        self.query = StateQuery(
            self.catalogue_ref, self.model, (self.object,),
            (_time_point(Time(request.instant, scale=request.time_scale).tdb),),
            self.reference, AccuracyRequest(metric="euclidean_norm"),
            require_velocity=True,
        )

    def describe(self):
        return ProviderDescriptor(
            self.key, (self.catalogue_ref,), (self.admission,),
            "borrowed; request-scoped registration",
        )

    def catalogue(self, reference):
        if reference != self.catalogue_ref:
            raise ResourceMismatch("ephemeris catalogue mismatch")
        return CatalogueSnapshot(reference, (ObjectRecord(
            self.object, (), "ephemeris target", (), ("cartesian_state",),
            ("target and centre preserved from EphemerisStateRequest",),
        ),))

    def supports(self, query):
        return CapabilityDecision(query == self.query, "one admitted geometric request")

    def evaluate(self, query):
        if query != self.query:
            raise UnsupportedCapability("ephemeris query differs from admission")
        state = self.source.state(self.request)
        if not isinstance(state, EphemerisState) or state.request != self.request:
            raise ResourceMismatch("ephemeris returned a different request")
        if state.resource != self.original_resource:
            raise ResourceMismatch("ephemeris returned a different resource")
        if (state.position_unit, state.velocity_unit) != ("au", "au/day"):
            raise UnsupportedCapability("ephemeris adapter requires AU and AU/day")
        self.original = state
        return StateBatch(query, (CartesianState(
            self.object, query.times[0], None, query.times[0], self.reference,
            tuple(x * u.au.to(u.m) for x in state.position),
            tuple(x * (u.au / u.day).to(u.m / u.s) for x in state.velocity),
            _unknown("m"), _unknown("m/s"),
        ),))

    def certify(self, *args):
        raise UnsupportedCapability("ephemeris temporal reuse is not admitted")

    def close(self):
        # The caller owns the backend; this registration never closes it.
        pass


class KernelEphemerisStateSource:
    """Expose returned SDK states through the existing direction protocol."""

    def __init__(self, source):
        self.source = source
        self.resource = source.resource

    def apparent_gas_tail_position_angle_deg(self, *, request, observer_state):
        """Retain the source-owned optional sample alongside state transport."""
        resolve = getattr(self.source, "apparent_gas_tail_position_angle_deg", None)
        if not callable(resolve):
            return None
        return resolve(request=request, observer_state=observer_state)

    def state(self, request):
        if not isinstance(request, EphemerisStateRequest):
            raise TypeError("request must be an EphemerisStateRequest.")
        if request.frame != "icrf":
            raise UnsupportedCapability("ephemeris adapter requires ICRF")
        if self.source.resource != self.resource:
            raise ResourceMismatch("borrowed ephemeris identity changed")
        provider = _EphemerisProvider(self.source, request)
        with Kernel(references=(provider.reference,)) as kernel:
            kernel.register(provider, ownership="borrowed")
            with kernel.open_session(SessionPolicy((provider.catalogue_ref,))) as session:
                returned = session.evaluate(provider.query).states[0]
        original = provider.original
        return replace(
            original,
            position=tuple(x / u.au.to(u.m) for x in returned.position_m),
            velocity=tuple(x / (u.au / u.day).to(u.m / u.s) for x in returned.velocity_m_s),
            provenance=original.provenance + ("returned kernel Cartesian state",),
        )
