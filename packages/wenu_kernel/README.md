# Wenu kernel: native direction and Cartesian states

This separately installable project implements a bounded native-state subset of K2.
It is not the K5 frozen SDK. Existing Wenu continues to use its current code;
the accepted native stellar adapter uses its existing source-epoch subset.
The SDK extension itself adds no numerical backend. Wenu now supplies a
source-bound static galaxy direction consumer outside this package.

## Implemented scope

- Immutable, recursively typed identity/catalogue/model/reference/time and
  direction-state records, with defensive copies of accepted list inputs.
- Explicit registration of application-admitted references and provider instances.
- Synchronous registry/session lifetime, fixed bindings, owned/borrowed closing,
  busy guards and atomic session admission.
- One-catalogue direction queries, time-major ordered results, exact-query
  session-local caching only after every row validates, and explicit numerical
  accuracy admission. Unknown physical uncertainty remains unknown.
- Provider-supplied angular certificates and selective temporal reuse under an
  explicitly chosen interactive session policy, with atomic publication of both
  exact and certificate caches. Reuse never turns into a new computed anchor.
- Optional provider-planned canonical anchors for reproducible reuse, with pure
  planning, strict envelope admission and atomic per-object anchor caching.
- SI Cartesian full-model states with explicit optional velocity and independent
  position/velocity uncertainty channels; the same session and ordered-batch API.
- Standard-library tests with constructed native/static/moving direction and
  Cartesian providers. These are not Gaia fixtures or science oracles.

`TimePoint` requires canonical integer-valued `jd1` and `jd2` in [-0.5, 0.5).
It rejects noncanonical input instead of silently losing precision while
normalizing. It never adds the large and small date parts for identity or
interval comparison. Native state queries still require matching scales.
Explicit conversion is provided separately by `wenu_kernel.time.TimeService`.
`TimeSpan` is closed. Unbounded model coverage is an explicit value with a scale.
All model and bound resource coverages must admit each requested sample.

Reference registration is an explicit application allowlist, not a transform
engine. Direction output uses radians; Cartesian positions/velocities use SI.
Native/epoch/static direction, Cartesian state, batch evaluation and optional angular
reuse/planning capabilities are implemented. Catalogue/model references retain resource and
membership digests. `StateBatch.query` carries that immutable provenance;
rows carry source epochs and actual anchors. A provider is responsible for
returning deterministic results from its admitted immutable sources.

Cartesian temporal reuse, relativistic/civil-time adapters, observation services, real state-provider adapters,
Gaia and persistent envelopes remain later slices. Requests outside the
implemented subset fail explicitly. `StateProvider.certify` now returns the
typed `ReuseCertificate` in `wenu_kernel.reuse`.
Native-state value records remain in `wenu_kernel.records`; time-specific records
belong to `wenu_kernel.time`. The reuse module exports the
certificate type plus `make_certificate` for its content identity and admission.
Records do not import session, hashing or provider services.
The reusable standard-library provider gate is shipped in
`wenu_kernel.conformance`; provider-specific fault/science checks remain with
their owner. See [provider conformance](#provider-conformance).

## Provider conformance

The optional `wenu_kernel.conformance` module ships in this wheel, uses only
the standard library and SDK, and imports no repository tests, concrete
providers, numerical backends or product code. It is not imported automatically
by the runtime facade. A provider package installs the SDK plus its own code
and owns its offline fixtures and numerical/science oracles.

Create a `ProviderCase(provider, query, probe, activity, mutate_buffers,
reuse_query=None)` factory. Every call creates a fresh open provider with the
same immutable bindings. `query` is a supported full-model query with at least
two distinct times; `probe` includes an additional time but the same catalogue, model,
reference and ordered object selection. Use multiple objects whenever the
admitted subset permits. The suite reverses both query axes to check ordering.

`activity()` returns `ProviderActivity(evaluations, certifications, closes)`
from honest owner instrumentation. Count all numerical work, including hidden
propagation inside metadata/planning calls; inspection must have no effects.
`mutate_buffers()` changes actual provider-owned source/result buffers that
could alias published data. If the implementation has no mutable buffers,
document that fact with its owner tests rather than inventing a fake mutation.
The harness proves its evaluation hook observes work; it cannot prove an
owner's instrumentation or a no-op mutation hook is truthful.

An advertised `direction_reuse_bound` requires a supported multi-time
`bounded_reuse` query with an explicit angular tolerance. Ordinary providers
omit `reuse_query` and must explicitly refuse certification. Canonical providers
must supply a query that actually exercises planning and certificates without
fallback. There are no skipped tests hiding an unexercised advertised capability.

Run one factory/suite for **each admitted catalogue/model/reference/subset**;
one sampled case does not certify an entire multi-model descriptor. Each suite
owns eight checks: pure/stable metadata, ordered full-model results and exact
cache, cold/warm/request-order equivalence, immutable publication and owned
closing, borrowed closing, invalid selection/scale admission, optional direction
certification/refusal and optional canonical planning/reproducibility. Cartesian
position-only and velocity-bearing cases use the same full-model checks.

`provider_suite(factory, name="StellarModelContract")` constructs a normal
`unittest.TestSuite` without instantiating a provider during discovery. It can
be composed with the provider's own science tests:

```python
from wenu_kernel.conformance import provider_suite

def load_tests(loader, tests, pattern):
    # make_offline_case is defined by this provider's test fixtures.
    tests.addTests(provider_suite(make_offline_case, name="StellarModelContract"))
    return tests
```

Alternatively mix `ProviderConformance` with `unittest.TestCase` and implement
`make_case()`. Do not import another package's tests or Wenu's synthetic fixtures.
Provider construction failures before returning a case remain factory-owned;
after return, the harness cleans up failed admission and request-owned sessions.
Cleanup failures are reported by unittest alongside the original failure.

The kit checks contracts on supplied samples. It does **not** prove physical
accuracy, conservative bounds throughout an interval, real resource integrity,
acquisition permission, concurrency or all production consumers. Those proofs,
provider-specific backend/failure/uncertainty cases and isolated installation
belong to that provider's gate. Shared SDK failures stay in the SDK owner suite.
Time-adapter tests remain owned by the explicit time service/adapter boundary.

The SDK gate runs this kit against six constructed state-provider cases and
deliberately faulty providers. A separate `-I -S` consumer uses only SDK imports
and its own constructed provider, with repository fixtures absent. Existing
synthetic fault/recovery tests retain their original test IDs and assertions.
No current Wenu production path is rerouted by shipping this test module.

## Explicit time conversion

`wenu_kernel.time.TimeService` is independent of state sessions. Construct it
with explicit `adapters=(adapter, ...)` and an exact
`admissions=(adapter.describe(), ...)` allowlist. Each borrowed, handle-free
`TimeAdapter` supplies `describe()` and `convert(time, target_scale)` for one
directed scale pair. Descriptors and caller lists are snapshotted at assembly;
there is no mutable registry, automatic discovery, conversion chain, fallback,
resource acquisition or implicit conversion inside a state query.

`TimeConversionAdmission` records source/target scales, source-scale validity,
exact model/resource identity, maximum numerical error in seconds, provenance
and contract version. Resource dependencies also declare source-scale coverage;
adapters are responsible for validating their actual local bytes before admission.
`TimeConversion` returns the original `source`, converted `target`, admitted
`model`, `numerical_error_s` and exact provenance. The service rejects malformed
outputs, altered model/resource/policy identities and out-of-domain inputs.
An optional `maximum_error_s` on `convert` accepts equality and rejects any
larger reported bound. Same-scale conversion is exact identity with a distinct
resource-free model and zero introduced error; it requires no adapter.

The numerical bound covers only this conversion's introduced approximation,
including output rounding. It does not measure input-date uncertainty, physical
clock realization uncertainty or any previously accumulated conversion error.
A caller composing conversions must retain receipts and compose their bounds;
an angular state budget cannot be inferred from a time error alone. K3 adapters
must carry the conversion receipt into product provenance rather than dropping it
when making a native-scale query. Session policy remains `same_scale_only`.

`wenu_kernel.time_adapters.TaiTtAdapter(validity)` is an optional standard-library
implementation of TT(TAI) = TAI + 32.184 seconds, in either directed sense.
The caller supplies a finite `TimeSpan` on its source scale. The adapter uses
an exact rational offset and outward-rounded binary64 error bounds without
forming a large floating Julian date. It returns TT(TAI), not TT(BIPM).
The [USNO definition](https://aa.usno.navy.mil/faq/TT) was checked 2026-10-18;
no external library implementation was copied or acquired. A chosen algebraic
domain does not establish a historical atomic-clock realization. Negative-JD
tests protect numerical representation, not ancient TAI science.

TDB/TCB conversion requires a separately admitted numerical authority; none is
supplied here. UTC/UT1, leap seconds, EOP, Delta-T and historical calendar input
remain outside core `TimePoint`. Importing the SDK or time service loads no
astronomy/graphics backend. State-provider conformance is a separate shipped gate.

## Cartesian state meaning

`CartesianState.position_m` is a finite three-component position.
`velocity_m_s` is a finite three-component velocity or explicit `None`;
`velocity_available` distinguishes a known zero vector from absence.
`position_evidence` and optional `velocity_evidence` carry separate measurement,
physical-model and numerical channels. Missing velocity has no velocity evidence.

Use a native `ReferenceSpec` with representation `cartesian`, units `m,m/s`,
and an explicitly admitted frame/origin/status. The kernel performs no frame,
origin or unit conversion. A TEME/Earth state is never relabelled barycentric
ICRF. Adapters convert source units explicitly; frame/origin transformations
remain owned by admitted realization services.

Cartesian queries use `AccuracyRequest(metric="euclidean_norm")`, with optional
independent `position_m` and `velocity_m_s` bounds. `require_velocity=True`
requests velocity without requiring a numerical bound; a velocity error bound
also requires velocity. Metadata-only `supports` must refuse unavailable velocity.
An accepted request that omits it fails closed. Unknown/statistical uncertainty
cannot satisfy a deterministic bound; absent physical uncertainty is not zero.

An ephemeris source need not have a catalogue reference epoch. Non-direction
object records may declare `source_epochs=()`; their Cartesian rows then use
`source_epoch=None`. Declared epochs must be retained. Resource coverage start
is not a replacement. Native/epoch direction sources still require source epochs.

### Static direction admission

An explicit `static_direction` capability describes directions invariant with
evaluation time in the admitted reference/model and coverage. Its object records
may have `source_epochs=()` and its `DirectionState.source_epoch` may be `None`.
A declared source epoch must still be retained and match catalogue provenance.
`time` remains the requested evaluation instant; `anchor_time` remains the actual
computed anchor. Neither is a substitute measurement date.

Static and native/epoch direction capabilities require distinct model admissions.
Object records may advertise multiple models, but any native/epoch direction
capability retains its source-epoch requirement. The session permits a null
direction source epoch only under an explicit static admission. A nullable value
record alone does not authorize a model. No galaxy-specific code enters the SDK.

Constancy is exact only relative to the selected model; missing physical
uncertainty remains unknown. Coverage, source bindings, units, reference, scale
and numerical accuracy checks are unchanged. Static models receive no automatic
temporal reuse or infinite coverage. Reuse still requires the existing explicit
capabilities and validated certificates; null and declared source epochs have
distinct anchor identities. The portable kit checks constant vectors across its
supplied static-model query/probe times; providers own wider scientific evidence.

This slice implements full-model Cartesian queries and identical-query caching.
Cartesian temporal reuse fails explicitly. Each query returns only the state
variant matching its native reference, in exact time-major order. Accepted
list buffers are copied into immutable tuples. All rows validate before any
cache entry is published.

## Angular reuse and reproducibility

`SessionPolicy.reproducibility="reproducible"` remains the default. A
`bounded_reuse` query follows a provider's canonical schedule when its model
advertises `canonical_direction_reuse`. Otherwise it evaluates the full model
(or reuses an identical complete query). Arbitrary warm-cache anchors never
define reproducible output.

The optional `CanonicalDirectionProvider` protocol in `wenu_kernel.providers`
adds `plan_reuse(query) -> DirectionReusePlan`. It is not required of existing
providers. Advertising the capability requires this operation plus angular
certification. Planning may inspect already admitted immutable metadata; it
must not propagate, acquire resources, consult cache history or mutate scientific
state. A provider's science/conformance gate must demonstrate that its declared
schedule depends only on the exact model, query and policy.

The plan contains time-major `AnchorSelection` records and planner method/
resource identity. `make_reuse_plan` constructs its content identity. The kernel
validates every anchor and the complete plan before evaluating missing objects
in batches by anchor time. `StateBatch.reuse_plan` records the schedule. Canonical
cache keys include source/model/reference, object, anchor and requested accuracy.
Changing cells chooses the planned new anchor even if an old certificate is
still within tolerance. Certificates are checked against original computed
states and required intervals; new anchors publish only after all rows succeed.
Unavailable plans or insufficient admitted bounds fall back to full evaluation;
malformed envelopes or backend failures do not become fallback successes.
For this slice, one unavailable/insufficient planned row falls back for the
complete query; all newly staged canonical anchors are discarded.

An explicitly chosen `interactive_bounded` session may reuse certified native
directions. Every such query needs positive `AccuracyRequest.angular_rad`;
paper/pixel conversion remains above the kernel. The provider supplies the
motion/error model and closed validity interval. The kernel checks source,
model, membership, reference, method resources, original anchor identity,
whole-interval coverage and total numerical bound. It does not multiply proper
motion or assume that missing motion is zero.

Certificates currently cover one object at one original full-model anchor.
Interactive queries batch missing objects per requested time; canonical queries
batch by anchor time. Both preserve exact
time-major output order. Certificate selection uses bound, anchor time and
identity as a total order over available entries. Interactive results may
depend on the available anchor set, always within their reported bound.

`StateBatch.reuse_certificates` lists immutable certificates. Reused rows carry
their `certificate_id`; `time` is the request, `anchor_time` remains the
computed anchor, and `source_epoch` remains the catalogue epoch. Their numerical
channel reports the certificate's total interval bound, including prior error.
Measurement/model uncertainty stays separate. No reuse chain resets that error.

An optional `StateQuery.coverage` explicitly requests certification over the
whole interval; endpoints alone being evaluated does not satisfy it. Insufficient
interval bounds fail `AccuracyUnavailable`. Without that request, an unavailable
certificate falls back to full evaluation under the requested sample tolerance.
Malformed certificates fail closed. Only fully validated batches and certificates
enter caches, and neither cache crosses sessions. Internal versioned digest
encodings use exact binary float values and are not a persistent format promise.

## Ownership and failure behavior

Registration transfers ownership only on success. Failed registration leaves
the provider caller-owned. Session opening reads immutable catalogues and
publishes its leases only after all bindings validate; it allocates no provider
session handles. Evaluation publishes no partial batch or partial cache entry.
The core does not promise to roll back a provider's prohibited side effects.

Owned providers close at successful unregister or kernel closure. Borrowed
providers never close through the kernel. Close with active sessions fails.
A provider close failure remains registered and is explicit/retryable; earlier
successful closes in a multi-provider kernel shutdown remain completed.
Session/kernel close is idempotent after successful cleanup. Published values
remain usable after all owners close. K2 is synchronous, without reentrant or
thread-safe provider callbacks.

## Independent gate

From the repository root, without installing the existing Wenu project:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/packages/wenu_kernel/src" python -m unittest discover -s packages/wenu_kernel/tests -v
```

The same gate works against an installed wheel with `PYTHONPATH` unset.
The isolation test also imports the SDK with `-I -S`, disabling site packages.
Root Wenu pytest discovery is restricted to its existing `tests` owner;
this package has its own gate and no runtime dependencies.
The [selection manifest](test_selection_v1.json) records scope and exclusions.
These new tests protect a new enduring owner; no legacy test is moved, removed
or replaced by this foundation. Later provider extractions must record their
old/new test mapping and retain their actual science oracles.
