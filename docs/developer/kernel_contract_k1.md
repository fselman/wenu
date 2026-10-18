# K1: public kernel and provider contract

**Revision:** 1, 2026-10-17. **Status:** accepted K2 implementation target
(PR #236); final usable SDK freeze remains K5.
**As-is base:** main `3359e9ebb430de68e68cdee8bfc40ddd6d3da692`.
**Proposed contract identifier:** `wenu.kernel/1.0`.

**Current candidate extension:** Cartesian state variant, explicit optional
velocity and `StateQuery.require_velocity`. Existing `StateProvider` methods
remain unchanged. This additive extension is reviewed before the K5 freeze.

The [K2 implementation](../../packages/wenu_kernel/README.md) remains a declared
native-state subset. The current candidate adds SI Cartesian full-model states
alongside accepted direction/certificate/canonical-planning behavior. Other records/
services in this specification are targets, not available imports. Observation,
Gaia and production routing remain pending. No astronomical transformation
changes; the coordinate guide remains current. Canonical time input is validated
rather than implicitly normalized.

The [roadmap](kernel_roadmap_v0.9.5.md) remains the sequencing authority.
This document specifies K1's proposed names, semantics, capabilities, errors
and conformance gates. Acceptance fixes the K2 implementation target; K5
freezes the usable SDK after all existing consumers have migrated. An amendment
between K1 and K5 is explicit and reviewed, not a silent interface change.

## 1. Guarantees and ownership

Every merged revision must leave existing Wenu functionality usable. Keep
public commands/APIs, accepted appearance and scientific meaning through
compatibility adapters until replacements pass their gates. Scientific
corrections, notably stellar proper motion, are accepted separately from
structural equivalence. Saved-sky formats retain readers or an explicit
versioned migration path; old bytes are not silently reinterpreted.

| Responsibility | Owner | Must not depend on |
|---|---|---|
| Identity, query admission, registry, immutable results, reuse | `wenu_kernel` | Concrete providers, Wenu products, plotting, catalogue acquisition |
| Catalogue decoding, native state/model and validity certificates | Domain provider package | Other concrete providers or products |
| Time-scale conversion | Admitted time service | Implicit clock, guessed calendar/scale or observer location |
| Origin/observer, light time, apparent corrections, frame transformation | Observation service and admitted numerical backends | Projection, paper size or appearance |
| Projection and paper/pixel tolerance conversion | Geometry/product layer | Provider implementation details |
| Charts, reports and atlases | Product layer | Private provider state or alternate position routes |

The core contracts and conformance kit use the Python standard library.
Astropy, Skyfield, NumPy and SGP4 may be numerical implementation dependencies
of adapters/services; importing the kernel SDK cannot import them or every
provider. Existing `wenu.__init__` is a compatibility facade, not the SDK.

## 2. Typed time and reference meaning

`TimePoint(jd1, jd2, scale)` is a finite two-part Julian date. Proposed core
scales are `tai`, `tt`, `tdb`, `tcb`; the day is not stored as a single large
float or a Python datetime. The constructor uses a normalized integer-valued
`jd1` and fractional `jd2` in [-0.5, 0.5), with an explicit precision contract
tested in K2. Booleans, NaN and infinity are invalid. Negative astronomical
years/year zero are represented through continuous dates, not datetime hacks.

UTC civil/calendar input and UT1 Earth-rotation interpretation enter through
adapters with leap-second/EOP/Delta-T provenance. They are not relabelled TT.
`TimeService.convert(time, target_scale)` performs only an admitted conversion,
returns its policy/resource identity, and fails when unavailable. Core v1 does
not silently download a table, extrapolate ancient EOP or implement its own
relativistic conversion. Near-modern string adapters remain for old APIs;
general historical calendar interpretation belongs to K4, not this contract.

`TimeSpan(start, stop)` is a closed interval on one declared converted time
basis, start <= stop. Unbounded coverage is an explicit separate value;
missing coverage never means infinity. A catalogue epoch, evaluation time,
reception time, emission time and equinox remain different fields.

`ReferenceSpec` declares frame ID, origin ID, position status, representation,
units, optional equinox and correction-policy identity. Frame/origin IDs must
be registered and supported, not arbitrary labels accepted by string equality.
ICRS has no equinox; projection alignment is not a reference frame. Current
`icrf` Cartesian and `icrs` angular labels are translated only through an
explicitly admitted adapter, never by relabelling values.

Native providers return the frame/origin/status advertised by their descriptor;
the kernel never forces TEME satellites or centre-relative planetary states
into fictitious barycentric ICRS states. Cartesian output uses metres and
metres/second; angular output uses radians. Adapters convert existing AU/day,
km and degree values explicitly while preserving their original provenance.

## 3. Identity, catalogue and model records

All records below are immutable, transitively through nested data.

| Proposed value | Required fields/semantics |
|---|---|
| `ObjectKey` | Namespaced stable Wenu ID; not a mutable display name or bare release-dependent Gaia ID |
| `ExternalId` | Catalogue, edition, identifier and optional physical component; Gaia IDs remain decimal strings |
| `ProviderKey` | Registered provider ID, software version and supported contract version |
| `ResourceRef` | Logical resource ID, edition, SHA-256, coverage/policy identity and provenance; filename alone is insufficient |
| `ModelRef` | Namespaced model ID/version, configuration digest and declared dependencies |
| `CatalogueRef` | Provider, exact resource set and membership/identity digest |
| `ObjectRecord` | ObjectKey, external IDs, semantic type, source reference epoch(s), model capabilities and provenance |
| `CatalogueSnapshot` | CatalogueRef plus deterministic immutable ordered object records |
| `ProviderDescriptor` | ProviderKey, admitted catalogues/models, capability/reference matrix and resource ownership policy |

Catalogue enumeration and astrometric evaluation are separate operations.
Membership is explicit and stable for a snapshot. Display labels, visual
photometry, morphology and scientific classification retain their domain
ownership. Optional typed domain services may expose them through versioned
interfaces; adding a galaxy property must not add arbitrary renderer fields
to the kernel state schema. No mutable free-form dictionaries in core records.

Duplicate object keys and unresolved aliases fail. Distinct physical components
stay distinct; alias resolution cannot silently choose the first match.
Changing catalogue edition, Gaia cross-match, membership or model makes a new
identified snapshot, not an in-place edit of an old result.

## 4. Capabilities: uniform envelope, meaningful state variants

| Capability | State returned | Required admission |
|---|---|---|
| `native_direction` | Unit direction with native reference meaning | Direction known, distance not implied |
| `epoch_direction` | Direction evaluated at a requested epoch | Declared motion model and its coverage; absent motion is not zero |
| `cartesian_state` | Position plus optional velocity | Registered frame/origin; explicit velocity availability |
| `direction_reuse_bound` | Bound for reusing a native direction | Model-valid angular certificate in that same reference meaning |
| `canonical_direction_reuse` | Deterministic original-anchor schedule | Pure optional planner plus `direction_reuse_bound`; model/resource coverage |
| `cartesian_reuse_bound` | Position and, if requested, velocity bounds | Metric/unit-specific certificate |
| `batch_evaluation` | Ordered independent object/time samples | Same science/error semantics as scalar evaluation |

These are proposed v1 names, not current methods on `Stars` or `SkyLayer`.
Capabilities are advertised per model/object subset/reference, not assumed for
every member of a provider. `supports(query)` cannot access a remote provider,
propagate, mutate state or claim physical accuracy from missing inputs.

| Existing family | Initial adapter behavior | Must not claim |
|---|---|---|
| Current Hipparcos direction route | Native catalogue direction and source epoch | Propagation merely because `position(instant)` accepts an argument |
| Gaia-enriched stellar subset | Admit epoch-direction model per usable solution; keep unmatched stars via explicit alternative | Six-dimensional state from missing distance/radial velocity; Gaia G as V |
| Galaxies/deep-sky fixed directions | Explicit constant-direction model; morphology remains domain geometry | Newly measured/proper-motion-propagated positions at every date |
| Existing planetary/minor-body source | Resource-bound geometric Cartesian states; reuse current light-time/appearance services above it | New body, disk, brightness or coverage capability from registration alone |
| Satellite SGP4 source | Explicit TEME state from the immutable element snapshot | ICRS, visibility or ancient extrapolation by relabelling |
| Grids, reference planes and constellation figures | Geometry services consume state/reference contracts where needed | Fabricated physical objects or moving IAU boundaries |

A constant-direction model may be exact relative to that declared model over
its admitted coverage, while physical motion uncertainty remains unknown.
This is different from treating an unknown stellar proper motion as measured
zero. Selection of a degraded/fixed stellar model is explicit policy/provenance.

## 5. Query and result envelopes

The following Python is a signature specification, not executable Wenu API.
Records are specified by the tables/text; no implementation is introduced.

```python
from __future__ import annotations
from typing import Literal, Protocol

class StateProvider(Protocol):
    def describe(self) -> ProviderDescriptor: ...
    def catalogue(self, reference: CatalogueRef) -> CatalogueSnapshot: ...
    def supports(self, query: StateQuery) -> CapabilityDecision: ...
    def evaluate(self, query: StateQuery) -> StateBatch: ...
    def certify(self, query: StateQuery, anchor: StateBatch) -> ReuseCertificate: ...
    def close(self) -> None: ...

class CanonicalDirectionProvider(StateProvider, Protocol):
    def plan_reuse(self, query: StateQuery) -> DirectionReusePlan: ...

class TimeService(Protocol):
    def convert(self, time: TimePoint, target_scale: Literal["tai", "tt", "tdb", "tcb"]) -> TimeConversion: ...

class Kernel(Protocol):
    def register(self, provider: StateProvider, *, ownership: Literal["owned", "borrowed"]) -> ProviderKey: ...
    def unregister(self, provider: ProviderKey) -> None: ...
    def open_session(self, policy: SessionPolicy) -> KernelSession: ...
    def close(self) -> None: ...

class KernelSession(Protocol):
    def catalogue(self, reference: CatalogueRef) -> CatalogueSnapshot: ...
    def evaluate(self, query: StateQuery) -> StateBatch: ...
    def close(self) -> None: ...

class ObservationService(Protocol):
    def realize(self, session: KernelSession,
                request: RealizationQuery) -> RealizedBatch: ...
```

`ownership` accepts exactly `owned` or `borrowed`; no implicit additional
ownership modes are admitted. Non-certifying providers retain
the uniform protocol: `certify` raises `UnsupportedCapability`, while full-model
evaluation remains available. Session/kernel close are idempotent and support
context managers with deterministic cleanup. No automatic finalizer is required
for correctness.

`StateQuery` fields:

| Field | Proposed meaning |
|---|---|
| `catalogue` | Exact CatalogueRef; provider binding is explicit, not a last-loaded global default |
| `model` | Exact admitted ModelRef |
| `objects` | Nonempty ordered tuple of unique ObjectKey values, all in the snapshot |
| `times` | Nonempty ordered tuple of unique TimePoint values, converted with explicit policy |
| `reference` | Supported native ReferenceSpec; unsupported transforms belong to observation |
| `accuracy` | AccuracyRequest described below |
| `evaluation_policy` | `full_model` or `bounded_reuse` |
| `coverage` | Optional TimeSpan for certification, containing every requested sample |
| `require_velocity` | Optional bool, default false; request an available Cartesian velocity without requiring a numerical bound. Direction queries reject true. A velocity bound also requires velocity. |

A mixed catalogue/source request is explicitly partitioned above this single-
provider query, never broadcast to all installed providers. Batch logical order
is time-major, then requested object order. Output contains exactly one record
per requested pair; it cannot silently omit failures, reorder IDs or create
duplicate rows. Pure metadata selection does not trigger epoch evaluation.

`StateBatch` preserves the original query, immutable ordered state records,
model/resource identity, actual anchor times and numerical-error evidence.
Each logical state row is a tagged union:

- `DirectionState`: finite normalized three-component unit vector, no implicit
  distance or radial velocity, explicit status/reference and source epoch.
- `CartesianState`: finite three-component position and optional three-component
  velocity, explicit availability, centre/frame/time and SI units.

The Cartesian subset uses `ReferenceSpec.representation="cartesian"` and
`units="m,m/s"`, with named `position_m` and optional `velocity_m_s` tuples.
`velocity_available` distinguishes absence from a known zero vector. Missing
velocity has `velocity_m_s=None` and `velocity_evidence=None`; no zero velocity
is inferred. `position_evidence` and `velocity_evidence` retain separate
measurement/model/numerical channels. Cartesian accuracy uses
`metric="euclidean_norm"` with independent position/velocity bounds in m/m/s;
statistical or unknown channels cannot certify deterministic bounds.

A provider's metadata-only `supports` must refuse required velocity when absent.
An accepted request returning no required velocity fails `InvalidProviderResult`.
Source epochs may be empty for non-direction `ObjectRecord` values; a Cartesian
row then carries explicit `source_epoch=None`, meaning no epoch is declared.
A declared epoch must be preserved, while direction sources still require it.
No ephemeris resource-start date is fabricated as a catalogue reference epoch.

Each single-reference query returns exactly the matching state variant. Native
frame/origin/units must be explicitly admitted; the kernel performs no frame,
origin or unit relabelling/conversion. Cartesian temporal reuse/certificates
remain unsupported in this slice; identical full-query caching is unchanged.

The logical row schema does not require scalar numerical evaluation or one
mutable Python object per source. K2 may use vectorized internal buffers and
immutable column views, but must expose the same ordered typed semantics.
Published data must own immutable storage or a provably immutable backing;
`dataclass(frozen=True)` or NumPy `writeable=False` with an external writable
alias alone is insufficient. No result changes after provider/session closure.

V1 batch failure is atomic: any failed row raises a typed error and no partial
result/cache publication occurs. A later partial-results mode requires a new
explicit capability, not silently changing success semantics. Empty catalogue
selection is allowed as metadata; an empty numerical query is invalid.

## 6. Tolerance, uncertainty and certificates

`AccuracyRequest` contains optional positive finite `angular_rad`,
`position_m`, `velocity_m_s` bounds and a registered error-metric ID.
For `bounded_reuse`, supply every bound required by the requested capability;
incompatible metrics or an unqualified apparent-angle request on a native
Cartesian query fail. No mixing of angular, positional and velocity units.

`full_model` disables cache-level temporal reuse/interpolation; interpolation
that defines the admitted ephemeris model itself remains allowed. It may reuse
a result for the identical complete scientific query. Its numerical error is the admitted
backend's declared error/limit, not mathematical zero. If an explicit accuracy
bound cannot be certified, fail `AccuracyUnavailable`; absence of a requested
bound means evaluate and report the backend's actual error status, not certify
an unrequested physical accuracy.

`bounded_reuse` first checks a matching certificate. If none qualifies, perform
full-model evaluation under the requested bounds; optionally create a new
certificate. A provider without a reuse certificate can still serve queries
whose full evaluation meets those bounds. No hidden tolerance relaxation.

`UncertaintyEvidence` has separate channels for measurement/covariance,
physical-model uncertainty and numerical approximation bounds. Each carries
units, meaning and `bounded`, `statistical` or `not_evaluated` status. Statistical
covariance/one-sigma values are not deterministic worst-case bounds. Unsupported
covariance propagation remains explicit; unknown is not zero.

`ReuseCertificate` fields and invariants:

| Field | Required meaning |
|---|---|
| `anchor_identity` | Exact computed state(s), anchor epoch(s), model and resources |
| `objects` | Explicit covered object subset, not the whole provider by assumption |
| `reference` | Same frame/origin/status/representation meaning as the covered query |
| `validity` | Closed admitted interval on a declared time basis, intersected with resource/model coverage |
| `metric` | Angular separation of unit directions, Euclidean position/velocity norm, or another registered metric |
| `maximum_error` | Conservative numerical bound valid everywhere in the interval, including anchor's prior approximation error |
| `method` | Namespaced bound model/version and configuration/resource identity |
| `identity` | Digest of the complete certificate meaning, not an object memory address |

Providers supply and justify certificates; the kernel verifies identity,
coverage and numeric admission. A constant interval-wide worst-case bound
keeps the core independent of the physical equations. Providers may generate
shorter intervals for tighter bounds. Unknown acceleration or proper motion
does not justify an infinite interval. Validity cannot exceed source coverage.

The short-time stellar estimate is motion times the difference from the
computed anchor, not from the catalogue epoch. Certification must also bound
perspective/changing angular motion where relevant; no guessed acceleration
term counts as proof. If a bound is unavailable, evaluate the admitted model.

For reuse chains, retain the original certified anchor or compose all numerical
bounds conservatively. Never reset error to zero on a cache hit. A loose entry
cannot serve a tighter request; a tighter one may serve a loose request when
all scientific identities match. Tracks require whole-interval evidence,
not only endpoint agreement. Boundary equality is admitted with outward-safe
rounding; floating-point rounding must not turn an invalid request valid.

## 7. Determinism, cache identity and selective invalidation

The current direction subset exposes `SessionPolicy.reproducibility` values
`reproducible` (default) and explicitly selected `interactive_bounded`.
Only the latter may use the current warmness-dependent certificate set.
`StateBatch.reuse_certificates` carries certificate records; a reused row's
`certificate_id` identifies its certificate, while `time` is requested and
`anchor_time` remains the original full-model epoch. Its numerical evidence
reports the interval-wide bound, including the original anchor error.
Certificates currently cover one object at one original anchor; multi-object
queries batch missing objects for evaluation and reassemble exact time-major order.

The optional `canonical_direction_reuse` capability adds
`CanonicalDirectionProvider.plan_reuse(query) -> DirectionReusePlan`; it is
not a new mandatory method on existing providers. Advertising it requires a
planner plus `direction_reuse_bound`. A planner may inspect admitted immutable
metadata, but cannot propagate, acquire resources, use cache/request history
or mutate scientific/session state. Its schedule depends only on the exact
admitted model, resources, query and declared policy; independent provider
conformance must establish cold/warm and request-order equivalence.

`AnchorSelection(object_key, requested_time, anchor_time)` records each logical
row's choice. `DirectionReusePlan(query, anchors, method, identity)` preserves
exact time-major row order and identifies the planner version/configuration/
resources. The kernel verifies query/identity/resource binding and every
anchor's model/resource coverage before propagation. The plan is returned in
`StateBatch.reuse_plan`; sample/anchor/source epochs retain their distinct meanings.

Reproducible mode follows only this declared schedule. The session-local
canonical cache keys complete catalogue/model/reference, object, actual anchor
and requested accuracy; it never substitutes an arbitrary still-valid anchor.
Missing anchors batch by anchor time. Certificates are validated against the
selected original full-model states, must bound requested samples/intervals,
and publish atomically with the new canonical cache entries. No rows of a
failed batch are committed. Explicitly unavailable plans/bounds use full-model
fallback; invalid plans/certificates and backend failures remain typed failures.
In this bounded implementation, one unavailable/insufficient planned row falls
back for the complete query and discards all newly staged canonical anchors.

For this subset, optional `StateQuery.coverage` on a `bounded_reuse` request
explicitly asks for whole-interval certification. Full evaluation of samples
alone cannot satisfy it: unavailable or insufficient interval bounds fail
`AccuracyUnavailable`. Model/resource interval violations fail `OutsideCoverage`.
Without explicit interval certification, a non-certifying provider may still
serve the requested sample through full evaluation at the requested tolerance.
Session-local anchor/certificate digest encodings are versioned internal
identities; they do not admit a new persistent format before K5.

Session policy freezes provider/resource/model bindings, time-conversion
policy, fallback policy and reproducibility mode. Registration does not change
an already open session's interpretation. No implicit model/provider fallback.

Cache identity includes contract/schema version, catalogue membership/source
digest, provider/software/model/resource identities, object/time selection,
reference meaning, time conversion and relevant approximation policy. It does
not include paper size, dpi, colour or labels. Tolerance and certificate
admission are checked even if an implementation indexes accurate entries for
reuse by looser queries. Python's randomized `hash()` is not a persistent ID.

For reproducible output, certificate anchors, interval partition and candidate
selection are deterministic functions of admitted model/policy, independent of
cache warmness and request order. Choose candidates by a frozen total order
(bound, canonical anchor time, identity); the candidate set cannot depend on
which arbitrary requests happened previously. If this cannot be guaranteed,
use full-model evaluation for reproducible mode. A separately explicit
interactive bounded mode may vary within its certified bound and records the
actual anchor. Reproducible products do not silently enter that mode.

| Event | Invalidated | Preserved |
|---|---|---|
| New stellar epoch outside some certificates | Affected star states and their dependent geometry | Other stars with valid certificates; galaxy/orbit providers |
| New observer or reception time | Affected observation results and downstream geometry | Native physical-state cache, subject to its own validity |
| New projection or paper scale | Projection/preparation; maybe a tighter state request | Existing scientifically valid physical states |
| New appearance | Affected rendering/furniture | Physical/observed geometry |
| New catalogue/model/resource | Its states and declared dependents | Unrelated providers |

Derived dependencies use identities: star-connected constellation endpoints
refresh when their stars change; IAU official boundaries retain their defining
frame. No blanket invalidation of the loaded sky for an unrelated domain edit.

Optional common-epoch snapshots retain native source solutions, velocity/model,
uncertainty and ancestry. They are derived caches, not replacements of Gaia's
reference epoch or a new realization of ICRS.

## 8. Observer realization boundary

`RealizationQuery` names catalogue/model/object bindings, reception TimePoint,
observer or explicitly barycentric origin, target frame/status, admitted
correction/EOP/refraction policies and requested output accuracy. It has no
projection or renderer. `RealizedBatch` records requested reception time,
evaluated emission times where relevant, native-state identities, correction
chain, distance availability, numerical/physical uncertainty and coordinate meaning.

The observation service can issue several native state queries to a session,
including retarded emission times and observer/Earth states, but cannot mutate
the catalogue or register a different backend mid-query. Existing light-time
and apparent-correction owners remain numerical authorities during adaptation.
Do not call `observe()` again on an already astrometric light-time solution.

Origin translation requires sufficient distance/state information. Direction-
only input cannot silently obtain finite distance/parallax. An explicitly
admitted infinite-distance approximation must appear in the selected model,
capability/accuracy limits and provenance. A native angular certificate alone
does not bound the apparent direction after origin translation.

The realization service allocates/composes its native-state, transformation,
light-time and approximation budgets to meet the requested output bound, or
fails `AccuracyUnavailable`. Observer parallax, aberration, Earth rotation and
precession/nutation have their own validity rules; the stellar proper-motion
interval does not certify them. Ancient native stellar charts can operate
without loading modern terrestrial EOP or short-span planetary kernels;
unsupported observer reconstructions fail separately.

## 9. Registry, resource lifetime and atomicity

Application assembly explicitly instantiates/loads allowed providers. Discovery
may inspect package entry-point metadata without importing every provider;
installation alone does not grant automatic registration or network access.
Version/capability validation precedes publication of a registration. Duplicate
keys, missing optional dependencies or incompatible contracts fail atomically.

Opening a session captures immutable bindings. Unregistering an in-use provider
raises `ProviderBusy`; no active session loses its backing source. Owned
providers close once at successful unregister or kernel closure after sessions
end; borrowed providers remain caller-owned.
Kernel close with active sessions fails `ProviderBusy` rather than invalidating
live results. Close after successful cleanup is idempotent. A failed open or
evaluation rolls back every allocation/temporary binding it owns, preserving
the original typed failure and reporting any cleanup failure explicitly.

K2 is synchronous; no thread-safe/concurrent evaluation capability is implied.
Existing atlas workers recreate sessions from exact serializable bindings, not
pickled locks/open handles/global singletons. Thread/process extensions require
explicit capability and isolation evidence, not an undocumented provider trait.

Evaluate/certify may read admitted local immutable resources through the session;
they cannot perform network acquisition, refresh catalogues or overwrite source
files. Resource installation/acquisition is separate explicit maintenance.
Rendering does not acquire Gaia data. A corrupt present resource fails closed.

## 10. Stable failures

All errors derive from proposed `KernelError` with immutable `code`, `message`,
`provider`, optional `object_key`, `time` and `resource` context. Codes and
structured meanings are stable; prose is not parsed. Adapters preserve the
original cause and relevant scientific context without exposing credentials.

| Error / code | Trigger |
|---|---|
| `InvalidQuery` / `invalid_query` | Malformed units/time/selection, duplicate rows, empty numerical query |
| `UnknownObject` / `unknown_object` | Object absent from the bound catalogue |
| `AmbiguousIdentity` / `ambiguous_identity` | Unresolved alias/component or provider binding |
| `UnsupportedCapability` / `unsupported_capability` | Requested operation/meaning not admitted |
| `IncompatibleContract` / `incompatible_contract` | Provider/core contract-version mismatch |
| `MissingResource` / `missing_resource` | Required local resource absent |
| `ResourceMismatch` / `resource_mismatch` | Bytes/digest/model/reference identity mismatch |
| `OutsideCoverage` / `outside_coverage` | Requested time/interval outside declared resource/model domain |
| `TimeConversionUnavailable` / `time_conversion_unavailable` | Required conversion authority/data absent |
| `AccuracyUnavailable` / `accuracy_unavailable` | Requested bound cannot be established |
| `ProviderEvaluationError` / `provider_evaluation_error` | Numerical/backend failure, including nonconvergence |
| `InvalidProviderResult` / `invalid_provider_result` | Wrong IDs/order/time/frame/status, nonfinite payload or invalid certificate |
| `ProviderBusy` / `provider_busy` | Unregister/close conflicts with active sessions |
| `ClosedSession` / `closed_session` | Numerical/catalogue use after close |

No failure becomes an empty sky, unknown value zero, stale success, unannounced
alternative model or partially published cache entry. Metadata enumeration of
zero matching objects is a distinct successful operation.

## 11. Versioning, persistence and compatibility

Proposed contract `wenu.kernel/1.0` versions semantics, units, error codes,
batch ordering, ownership, time identity and accuracy interpretation as well
as names/signatures. Providers declare an accepted contract-version range.
Unknown required fields/capabilities fail. A minor version may add opt-in
capabilities; changes to existing meaning/defaults require a major version or
an explicit negotiated contract, not an incidental software patch.

Core v1 persistence is not a new universal catalogue file format. Existing
snapshot formats retain their schemas/digest rules. A new persistent state or
certificate envelope needs a separately versioned canonical encoding accepted
before K5: finite values, exact two-part times, immutable source/resource/model
identity, explicit null/status, deterministic order and round-trip validation.
Never hash an in-memory repr or pickle as a cross-version scientific identity.
K2 may keep caches session-local until that encoding is accepted. No hidden
disk-cache compatibility promise follows from this signature specification.

| Existing contract | Migration obligation |
|---|---|
| `CoordinateSpec`, `ObservationContext` | Preserve public constructors/meaning; adapt to typed time/reference and retain epoch/equinox distinctions |
| `PositionProvider.position(instant)` | Wrap existing native positions honestly; accepting an argument is not an epoch-propagation capability |
| `EphemerisStateRequest/State/Resource*` and `EphemerisStateSource` | Preserve target/centre/provider IDs, resource chains, coverage, units and backend behavior through explicit adapters |
| `LayerRealizationContext` | Translate request context to session/realization without losing instant/reference policy; retire ignored-context fallback only after parity |
| Solar-System direction realizers | Reuse existing astrometric/apparent algorithms and resource-coherence checks; no second light-time authority |
| `CelestialSphere` and current layers | Compatible facades consume session results; do not own a competing state cache or direct provider bypass |
| Native snapshots / atlas workers | Preserve reading and design/source binding; do not relabel legacy unpropagated directions as Gaia epoch states |
| Existing CLI, Python examples and reports | Same public behavior during structural slices; explicitly accepted astrometric corrections separately |

These source interfaces were checked at the exact base in `coordinates.py`,
`positions.py`, `ephemeris.py`, `sky/realization.py` and
`solar_system_directions.py`. New names in this document are proposed SDK names,
not imports falsely attributed to existing Wenu.

## 12. Conformance and independently testable modules

The conformance kit depends on core contracts and synthetic providers only.
It imports neither Wenu products nor another installed astronomical package.
Each domain adds its numerical science oracles; these are not duplicated inside
the core. A provider change preserving contract runs its own tests/conformance;
unrelated provider or graphics suites are not a prerequisite after isolation
is accepted. Shared contract changes require an explicit affected-consumer plan.

| Gate | Fault/evidence | Owning milestone |
|---|---|---|
| SDK import isolation | No Astropy/Skyfield/NumPy/plotting/concrete-provider import side effects | K2 |
| Provider isolation | Star-only install/test works with other providers absent | K2 fake, K6 real |
| Time semantics | Equivalent admitted scales, negative/year-zero dates, precision limits and conversion failure; no label-only conversion | K2 foundation, K4 chronology |
| Query integrity | Exact ID/time product order; unsupported fields/capabilities; atomic row failure | K2 |
| Immutable results | Mutate source buffer/nested metadata after publication; result unchanged after close | K2 |
| Selective reuse | Mixed rates, inside/outside/equal interval endpoints, stricter tolerance, retained anchor error and whole-interval coverage | K2 fake, K4 real |
| Reproducibility | Cold/warm and permuted-request order yield the contracted same results/identities | K2 |
| Independent invalidation | Advancing stars does not invoke galaxy provider; observer change preserves native states | K2/K3 |
| Lifecycle/rollback | Register/open/evaluate/close failures restore all owned state; borrowed resources stay open | K2/K3 |
| Scientific adapter parity | Existing ephemeris/coordinate outputs and failures preserved under unit/time conversion | K3 |
| All consumers | Instrumented-provider evidence and prohibited bypass checks for every roadmap consumer | K3/K5 |
| Observer accuracy | Separate apparent/native budgets, distance absence and single light-time solution | K3/K4 |
| Gaia propagation | Native epoch/component matching, missing-data policies, covariance/model limits and ancient specimens | K4 |

These are required future tests, not passes claimed by this document. Keep
existing numerical, visual, print and public-path evidence while migrating.
Final integration receipts are still required for cross-cutting runtime slices
until module isolation is demonstrated. Documentation-only K1 requires only
its documentation/integrity gate.

## 13. K1 acceptance and bounded K2 entry

The [as-is audit](kernel_migration_audit_v1.md) and its pinned source/test and
functionality inventory are prerequisites to K2. Test reorganization is a
continuous deliverable of every implementation slice. Each slice supplies
owner/conformance/immediate-seam selection and preserves the protected faults
of relocated tests. K3–K5 must reconcile all current consumers; K6–K8 cannot
close a package without isolated installation, collection and execution of its
own tests with unrelated providers absent. Release composition remains a
separate responsibility. Follow the [testing policy](testing_policy.md) for
shared-contract impact and retained integration requirements.

K1 review must accept or explicitly amend: names/fields, native state variants,
time basis/precision, reference and unit policy, accuracy/certificate semantics,
determinism, error codes, lifetime and adapter obligations. The persistence
encoding remains a named later freeze prerequisite, not an undocumented choice.
No numerical tolerance, ancient accuracy, full covariance support, backend
coverage or provider permission is admitted merely by accepting the API.

The accepted K2 foundation supplies records, registration/session admission and
direction certificates without production rerouting. The current bounded slice
adds optional canonical planning with synthetic providers; it does not close all
K2 gates. Time services and the
distributable conformance kit remain explicit work before the K5 SDK freeze.
No Gaia acquisition, scientific-provider extraction, product rewrite or new
satellite science is part of K1. Wenu must continue to run after every merge.
