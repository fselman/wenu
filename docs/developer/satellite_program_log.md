# Wenu artificial-satellite program log

This document preserves the chronological 50S development record: candidate
boundaries, verification evidence, accepted milestones, and authorized next
steps. It is not the pedagogical satellite guide. Scientific concepts,
acronyms, formulae, principles, and module relationships belong in
[satellite_guide.md](satellite_guide.md).

## 17. Milestone evolution

- **50S.0:** maintain this literature, provider-policy, scientific, and
  architecture guide; no runtime behavior.
- **50S.1:** provider-neutral identity, observer, FoV, interval, candidate, and
  crossing-result contracts; no propagation yet.
- **50S.2A:** accepted audit of SatChecker endpoints, time and coordinate semantics,
  candidate envelope, async policy, exact cache, failures, and redistribution.
- **50S.2B:** accepted cached circular-field adapter, candidate-only
  normalization, provider-sampled evidence, explicit progress, and exact cache.
- **50S.3A:** accepted audit of honest human-readable/JSON reports and FoV charts from
  provider-sampled candidate evidence, with no invented exact crossing events.
- **50S.3B:** accepted deterministic reports plus drawable sampled-track and
  sample-point layers through the shared renderer/export path; provider
  illumination remains separate evidence.
- **50S.4A:** audit direct dependency, OMM/snapshot, SGP4/TEME,
  Earth-orientation/topocentric validation, and specimen contracts.
- **50S.4B:** canonical OMM elements and a tiny immutable synthetic snapshot.
- **50S.4C:** Vallado-validated SGP4 and typed geometric TEME state.
- **50S.4D:** independently validated no-download topocentric transformation.
- **50S.4E:** network-free propagated-specimen builder and 50S.4 closure.
- **50S.5:** complete local catalogue scan and adaptive exact-crossing oracle.
- **50S.6:** conservative plane, radial-shell, phase/reachable-arc,
  occultation, and coarse-state filters; add HEALPix/time indexing only if
  measured larger-snapshot workloads justify it; prove zero false negatives.
- **50S.7:** independent Sun/penumbra/umbra and observer-night geometry.
- **50S.8:** empirically validated object, family, and population brightness
  models with explicit `unknown` and separate glint limitations.
- **50S.9:** instrument-specific trail signal and detector contamination.
- **50S.10:** statistical products versus night time, season, observer,
  pointing, FoV, and exposure duration; close the program after numerical,
  performance, report, and visual acceptance.

Fernando accepted 50S.2B on 2026-09-15 after 45 provider/domain tests, 168
expanded focused tests, all 2,457 tests, and the bounded live provider check
passed. Fernando accepted 50S.3A on 2026-09-15; only the bounded 50S.3B implementation is authorized next.

At every milestone, revise this living guide to match accepted science and
implemented ownership. When 50S foundation work is merged, decide explicitly
whether this guide remains separate or is integrated into
`coordinate_system_guide_v0.9.5.md`; do not merge documents mechanically.


## 18. 50S.3 sampled-evidence presentation boundary

The 50S.3A admission review found reusable coordinate, projection,
preparation, renderer, semantic SVG, and export paths, but no existing
satellite report owner. `SolarSystemTrackResult` is not reusable as a data
type because it means ephemeris realization, while SatChecker supplies ordered
provider samples.

Every 50S.3 product must therefore identify its content as **SatChecker sampled
candidate evidence — not verified crossings**. Human-readable reports, JSON,
and charts consume the same already-normalized SUCCESS result. Two or more
samples may form one open polyline in supplied order; a singleton remains a
point. No interpolation, propagation, entry, exit, closest approach, continuous
containment, illumination calculation, magnitude, or detector consequence may
be inferred.

Chart geometry declares geometric topocentric-direction ICRS and follows
`CelestialSphere.draw_chart()`. Semantic identity uses the full NORAD
catalogue identifier rather than provider order or display name. Provider
illumination, if present, remains separately attributed evidence and cannot
change track admission or style.

Fernando accepted 50S.3A on 2026-09-15 after all 126 focused documentation
tests and the candidate diff check passed. The audit itself changes no runtime
behavior. Acceptance authorizes only bounded renderer-neutral reports and a
drawable sampled-candidate layer in 50S.3B.


## 19. Accepted 50S.3B implementation

`satellite_presentations.py` now provides one deterministic presentation
model over a terminal normalized SatChecker response. Text and JSON share the
same document, retain query and receipt provenance, sort candidates by full
NORAD catalogue identifier, preserve supplied samples in temporal order, and
state that the product is not a verified crossing report.

`sky/satellite_candidate_layer.py` supplies two cooperating ordinary layers.
The track layer returns an open curve for two or more samples and a point for a
singleton. The samples layer returns only supplied points and may expose their
exact normalized UTC instants as labels. Both assemble multi-instant geometric
topocentric-direction ICRS evidence with per-sample time metadata, then use the
accepted fixed chart-product transformation convention and canonical
`CelestialSphere.draw_chart()` pipeline.

Stable semantic identity is based on the full NORAD catalogue identifier.
Names remain display labels. Provider illumination is retained only in
metadata/report evidence and does not control geometry or style. There is no
entry, exit, closest approach, interpolation, propagation, network, cache-read,
retry, CLI, local catalogue, brightness, or detector behavior.

The candidate focused gate passed 90 tests, including actual Matplotlib
PNG/PDF/SVG serialization through the canonical chart pipeline. Fernando then
accepted the regenerated network-free specimen on 2026-09-15: the explicit
closed circular FoV annotation, red ordered sample path, four UTC annotations,
candidate-only title, and PNG/PDF/SVG products were correct. The final expanded focused gate passed all 217 tests, and the complete
plugin-disabled suite passed all 2,473 tests in 83.98 seconds. Fernando accepted 50S.3B on 2026-09-15. This closes SatChecker sampled
candidate reporting and drawing; only the documentation-only 50S.4A audit is authorized next.


## 20. 50S.4 snapshot and propagation admission review

The 50S.4A review separates five responsibilities that cannot share one
acceptance boundary: contract audit, immutable snapshot/domain, SGP4/TEME
propagation, Earth-orientation/topocentric transformation, and developer
specimen construction.

Wenu will declare `sgp4>=2.25,<3` directly rather than relying on Skyfield's
transitive dependency. The adapter will use explicit WGS-72 OMM
initialization, split Julian dates, typed geometric TEME position/velocity,
and explicit status codes. It will be a wrapper around the upstream
Vallado-compatible implementation, not a copied propagator.

The first installed snapshot will be a tiny hand-authored synthetic OMM/GP
collection spanning LEO, MEO, and geosynchronous-like geometry. It is
non-operational and avoids redistributing live provider data. Full integer
NORAD identity, UTC epoch, TEME/Earth/SGP4 declarations, exact canonical
content, SHA-256 identity, provenance, and validation remain mandatory.

Topocentric work will follow Astropy's documented TEME-to-ITRS and
observer-subtraction chain with automatic IERS download disabled. Results
retain EOP identity and fail outside available coverage. A separate numerical
stage must settle the name and convention of an instantaneous geometric
topocentric vector expressed in celestial axes; it must not be called
geometric ICRS merely because the axes are ICRS-oriented.

The developer builder will emit **propagated sampled specimens — not verified
crossings**. It cannot create `SatelliteCrossingResult` or claim completeness;
those belong to 50S.5.

Fernando accepted the documentation-only 50S.4A audit on 2026-09-15 after
the focused gate passed all 128 tests and the branch diff check was clean.
50S.4A changed no runtime, dependency, or package data. It is now closed, and
only 50S.4B immutable OMM element and snapshot work is authorized next.


### Accepted 50S.4B immutable OMM snapshot

The dedicated 50S.4B branch implements only the element/snapshot boundary
authorized by 50S.4A. `SatelliteElementRecord` retains all required OMM mean
elements, full six-digit synthetic NORAD identity, canonical UTC epoch,
`EARTH`/`TEME`/`UTC`/`SGP4` declarations, source-record digest, and
provenance. Invalid, incomplete, unknown-field, non-finite, wrong-frame, or
wrong-theory input fails closed.

`SatelliteElementSnapshot` and its manifest enforce exact canonical JSON
bytes, content and per-record SHA-256 identities, record count, ascending full
NORAD ordering, duplicate rejection, immutable lookup, and installed-resource
loading. The first snapshot contains only three hand-authored, non-operational
LEO-like, MEO-like, and geosynchronous-like specimens. It copies no live
CelesTrak, Space-Track, SatChecker, or tracked-object record.

The branch declares `sgp4>=2.25,<3` directly so installation owns its future
propagation dependency. It deliberately constructs no propagator and produces
no TEME state, terrestrial/topocentric transformation, field intersection, or
crossing result. Those remain gated by 50S.4C and later milestones.

At production commit `d3cb597`, all 158 expanded focused tests and all 2,483
complete-suite tests passed. The wheel was then installed into an isolated
virtual environment and the snapshot loaded from `site-packages` with exact
digest
`b6ab95df3eb180b07694b1b9bafd47c2805b6cc7ebea8636490beec03cd71457`,
record count three, and ordered identifiers 900001–900003. The first two
wheel-import attempts exposed unrelated environment issues—missing
dependencies in a no-dependency environment and a broken inherited
`spiceypy` shared library—before the package-local resource check isolated
the intended boundary. Neither failure involved the snapshot. Fernando
accepted 50S.4B on 2026-09-15. The immutable snapshot boundary is closed, and
only 50S.4C validated SGP4/TEME propagation is authorized next.


### Accepted 50S.4C SGP4 and geometric TEME state

The 50S.4C adapter is deliberately narrow: canonical OMM record → explicit
WGS-72 Vallado-compatible `Satrec` → immutable successful geometric TEME
state, or an explicit `SatellitePropagationError`. It retains split Julian
dates, element age, upstream version/backend, operation mode, source/snapshot
identity, and units. It does not silently accept NaNs or non-zero statuses.

The published Vallado verification vectors for near-Earth satellite 5 and
deep-space satellite 4632 are pinned as wrapper oracles. A published decaying
case verifies terminal error propagation. Scalar and accelerated-array routes
agree within the declared sub-millimetre position tolerance.

The 50S.4C preflight caught that the original synthetic identifiers
900001–900003 cannot be represented by upstream `Satrec`, whose current
maximum is 339999. The corrected installed snapshot uses 300001–300003,
preserving six-digit identity while remaining valid for the actual propagator.
All record digests and the snapshot digest changed accordingly; Wenu never
substitutes an internal ID.

Every result remains geocentric geometric TEME. No Earth rotation, polar
motion, ITRS state, observer subtraction, range, AltAz, celestial direction,
FoV test, or drawing occurs in this milestone.

At production commit `e0d7c78`, all 167 expanded focused tests and all 2,492
complete-suite tests passed. An isolated installed wheel loaded the corrected
snapshot from `site-packages` and propagated identifiers 300001, 300002, and
300003 at 2026-09-15T00:10:00Z. Each result reported TEME, WGS-72, status zero,
and finite position and velocity. Fernando scientifically and architecturally
accepted 50S.4C on 2026-09-15. The SGP4/TEME boundary is closed, and only
50S.4D Earth-orientation and topocentric state work is authorized next.


### Accepted 50S.4D local topocentric state

The candidate local path is:

```text
canonical OMM record
    -> WGS-72 SGP4 geometric TEME state
    -> explicit installed IERS-A TEME-to-ITRS transform
    -> WGS-84 observer subtraction in Cartesian ITRS
    -> range plus vacuum geometric AltAz
    -> optional topocentric geometric direction in GCRS axes
```

Every result retains the full source TEME state, observer, satellite and
observer ITRS vectors, topocentric vector/velocity, range, angular directions,
exact IERS-A SHA-256 and coverage, interpolated UT1−UTC and polar motion,
software versions, coordinate identity, provenance, and warnings. Automatic
IERS download and degraded accuracy are disabled; out-of-coverage instants fail
closed.

The GCRS-axis longitude/latitude are not an ICRS position, formal geocentric
GCRS coordinate, astrometric place, apparent place, or observed direction.
They are the instantaneous observer-subtracted geometric vector expressed in
celestial axes. Refraction, field intersection, exact visits, illumination,
brightness, detector effects, reporting, drawing, and specimen generation are
not part of 50S.4D. Fernando scientifically and architecturally accepted this
boundary on 2026-09-15. Only the bounded 50S.4E propagated-specimen builder is
authorized next.

### Accepted 50S.4E propagated specimen builder

The candidate `tools/build_50s4_satellite_specimens.py` tool loads the
installed three-record synthetic snapshot and evaluates an explicit ordered
UTC grid for the La Ligua observer by default. Its one JSON product records
snapshot and record digests, evaluation grid, observer, exact IERS-A identity
and sampled values, SGP4 identity, WGS-72 policy, Wenu version, TEME states,
topocentric states, and query inputs.

The product is explicitly labelled **propagated sampled specimens — not
verified crossings**. It is deterministic for identical installed resources
and arguments, performs no network access, and writes only below the required
caller-selected output directory. It contains no `SatelliteCrossingResult`,
entry/exit, closest approach, completeness claim, production tolerance, chart,
or field-search behavior. Focused, full-suite, generated-product, diff, and
Fernando acceptance gates remain pending.

#### Accepted 50S.4E verification result

The dedicated, expanded, and documentation Mac gates passed 10, 99, and 134
tests. The complete plugin-disabled suite passed all 2,522 tests in 105.38
seconds.
The inspected generated product had SHA-256
`16137e9380404dca03789532ab029c4159755c69dd2ab0ca5990a82cd9c42374`
and preserved the exact snapshot, observer, grid, IERS-A, propagator, and
software identities. Its three default synthetic tracks were below the La
Ligua horizon, so the product correctly made no visibility or crossing claim.
The branch and diff checks were clean. Fernando scientifically and architecturally
accepted 50S.4E on 2026-09-15. This closes 50S.4 and authorizes only bounded
50S.5 complete local FoV-crossing oracle work.

50S.6 acceleration and every later satellite milestone remain unauthorized.


## 21. Accepted 50S.5A complete local crossing-oracle audit

The first local oracle is restricted to a fixed closed circular field whose
centre and the accepted 50S.4D trajectory are both topocentric geometric
directions expressed in GCRS axes. Provider apparent ICRS, AltAz, projected
coordinates, and mixed position statuses are rejected rather than compared
numerically.

Every valid record in the selected immutable snapshot is scanned. Completeness
means validated numerical completeness under explicit time and angular
tolerances. Endpoint and midpoint state, topocentric Cartesian motion,
instantaneous angular rate, curvature evidence, and successive refinement form
an operationally conservative envelope. A possible-contact interval
subdivides; a singular or non-converged interval fails closed. A fixed grid,
endpoint signs alone, unconstrained interpolation, and measured
catalogue-wide speed maximum are not completeness evidence.

Bracket-preserving roots establish entry and exit. Bounded minimum refinement
detects tangency without requiring a sign change. Query endpoints are
inclusive, boundary touch counts, disconnected visits stay separate, and
uncertain refinement raises an explicit convergence error. Analytic
trajectory oracles remain independent of SGP4/Astropy composition tests.

This documentation-only review adds no solver. Fernando scientifically and
architecturally accepted it on 2026-09-15. Acceptance authorizes only bounded
50S.5B; 50S.6 and later behavior remain unauthorized.

## 22. Accepted 50S.5B complete local crossing oracle

The accepted `LocalSatelliteCrossingOracle` scans every record in the selected
immutable snapshot and composes the accepted SGP4/TEME and installed-IERS-A
observer chain. It compares only fixed-field and trajectory unit vectors in
GCRS axes. No horizon, orbital-plane, phase, HEALPix, or population filter may
remove an interval or record.

Adaptive subdivision uses endpoint/midpoint separation, topocentric angular
rate, curvature evidence, bounded roots and minima, and recursive
time-and-angular tolerance connectivity. A tangent is retained as one
zero-duration boundary event; disconnected visits remain separate. Failure or
resource exhaustion is explicit and fail closed. This is validated numerical
completeness, not formal interval arithmetic, and it authorizes no runtime 50S.6 work.

Fernando scientifically and architecturally accepted 50S.5B on 2026-09-15.
Only a documentation-first 50S.6 conservative-acceleration audit is authorized
next.

## 23. Accepted 50S.6A conservative crossing acceleration audit

The accepted exhaustive oracle remains the scientific reference. Acceleration
may reject a record only when a complete topocentric field-cone and bounded
orbital-shell envelope, including tolerance and model margins, proves that no
contact is reachable. Uncertainty means retain and solve exactly.

The first proposed implementation stage is the cone/shell selector. Nominal
orbital-plane distance, endpoint sampling, mean anomaly alone, or a fixed
sampling grid cannot establish absence. Horizon and Earth occultation do not
belong in the current geometric query predicate. Phase, coarse vectorized
states, and HEALPix/time indexing require later separate admission and measured
benefit. Fernando scientifically and architecturally accepted 50S.6A on 2026-09-15.
Only bounded 50S.6B implementation of the first cone/orbital-shell selector is
authorized; all later acceleration stages and satellite behavior remain
unauthorized.

## 24. Accepted 50S.6B cone-shell selector

The first selector is intentionally narrow. It supports only the installed
three-record synthetic snapshot and query intervals up to 60 seconds. It
constructs one whole-interval reachable angular cap from an accepted initial
topocentric state and a deliberately inflated orbital-shell speed bound.

A record is rejected only when the cap is strictly disjoint from the closed
field after tolerance and numerical margins. Retain and indeterminate both
mean “send to the exact oracle.” The selector does not use altitude or
occultation, does not sample a nominal track to infer absence, and does not
return crossings or make a performance claim. Fernando scientifically and
architecturally accepted this bounded selector on 2026-09-16. Only a
50S.6C documentation-first coordination and admission audit is authorized next.

## 25. Accepted 50S.6C coordination and admission audit

The proposed accelerated route does not create a second crossing solver.
Exhaustive and accelerated searches must share one exact record operation;
the exhaustive route invokes it for every record, and acceleration may omit
only records carrying a validated conservative reject decision. Retain and
indeterminate both mean exact solve.

Fernando scientifically and architecturally accepted this audit on 2026-09-16.
Only bounded 50S.6D coordination in the existing admitted domain is authorized
next.

Complete ordered decision coverage, invariant checking, fallback, exact-result
equivalence, and fail-closed behavior precede optimization. A selector error or
unsupported query cannot become an empty result. The installed synthetic
three-record snapshot remains a composition fixture, not evidence of useful
speed or broader catalogue validity.

Widening the selector requires immutable regime-covering fixtures and
zero-false-negative comparison with the independent exhaustive oracle.
Performance claims require predeclared representative workloads, repeated cold
and warm measurements, evaluation counts, timing distributions, and material
total-wall-time benefit. This documentation-only candidate authorizes no
runtime coordinator or broader acceleration.


## 26. Accepted 50S.6D bounded accelerated coordinator

The exhaustive crossing oracle remains the default and independently callable.
The accepted coordinator validates the complete ordered result of the accepted
cone-shell selector and calls the same exact record solver for every retain or
indeterminate decision. Only a validated reject may omit exact work.

`solve(query)` returns ordinary exact crossing results.
`solve_with_evidence(query)` additionally returns separate immutable
selection and evaluation accounting. Selector failure falls back to the
complete exhaustive route by default or fails closed under explicit policy;
invalid coverage and rejection outside the installed three-record, 60-second
domain always fail closed.

This accepted implementation makes no useful-speed claim and adds no broader catalogue
domain, default acceleration, new filter, visibility semantics, CLI, report,
or drawing behavior.


Fernando scientifically and architecturally accepted 50S.6D on 2026-09-16.
Broader-domain activation, benchmarking claims, default acceleration, new
filter stages, and later satellite behavior remain unauthorized.


## Accepted 50S.6E multi-FoV and delivery sequence

The proposed primary workload is one observer with any non-empty number of
different FoVs and independently bounded intervals. The centre of every field
must satisfy a configurable airmass limit throughout its complete interval.
The initial policy uses geometric vacuum AltAz and plane-parallel `X = sec(z)`
above the horizon, with `X_max = 2` by default (exactly 30 degrees minimum
centre altitude in this model). Only the centre is checked; the FoV radius does
not enter airmass admission. This is an FoV admission condition, not a
satellite horizon or occultation filter;
it imposes no civil-date or inferred-twilight boundary. Ten FoVs are the
ordinary benchmark and proposed internal chunk, never a hard-coded public
maximum. Disjoint, overlapping, and identical intervals are separate evidence
cases; identical intervals are a maximum-reuse research case.

A bounded 50S.6F implementation would precede representative-scale admission,
generic JSON/ECSV/VOTable reports, and exact binocular/regional/stereographic
tracks in 50S.6G. Direct Paranal or ELT compatibility requires the separate
50S.6H interface audit. 50S.7 then treats Sunlight, solar Earthshine,
Moonlight, and Lunar-Earthshine as separate geometric components; 50S.8 adds
component-resolved flux or magnitude distributions. Fernando scientifically and architecturally accepted 50S.6E on 2026-09-16.
No multi-FoV runtime or later milestone is implemented or automatically
authorized. Only bounded 50S.6F is authorized next.


## Accepted 50S.6F bounded batch implementation

The accepted Python API accepts an immutable ordered non-empty tuple of
complete single-field queries. All fields must share one observer and immutable
snapshot; field identifiers are unique, intervals and exact-solver tolerances
remain independent, and the installed synthetic 60-second domain remains the
only admitted runtime. The field-centre airmass ceiling is configurable and
defaults to 2. The radius is not part of admission.

Validation is atomic and precedes all crossing work. One typed exception
retains every rejected field and reason in input order, preparing a later 50S.6G
file/CLI adapter to write a validation file and resubmit the valid subset
without adding that behavior now. Valid fields are processed in execution-only
chunks of 10 by default and results retain input order. The candidate composes
50S.6D independently per field; it does not yet claim useful acceleration or
shared propagation/topocentric-state reuse. Fernando scientifically and
architecturally accepted 50S.6F on 2026-09-17 after 2,577 plugin-disabled tests
passed. Only a separately bounded 50S.6G audit is authorized next.


## Accepted 50S.6G delivery sequence

The candidate delivery audit separates external immutable snapshot loading,
policy-governed representative acquisition/evidence, canonical reports,
CLI/file workflow, exact drawable evidence, binocular/regional charts, and
stereographic planispheres into separately accepted slices.

Direct Python and CLI requests fail atomically. An invalid JSON request file
solves no FoV but may atomically produce a second validation-output JSON that
marks every failed FoV and embeds the ordered valid subset. Explicitly feeding
that file to a second call revalidates and calculates only the valid subset.

JSON is the canonical nested exchange; ECSV and VOTable encode the same logical
model for scientific interoperability. Exact chart tracks require certified
samples between exact entry and exit and reuse the ordinary Wenu chart path.
They remain geometric crossings; illumination, brightness, detector effects,
and observatory scheduling remain later milestones.
Fernando scientifically and architecturally accepted this sequence on
2026-09-17 after all 145 plugin-disabled current-documentation tests passed in
4.36 seconds. Only bounded 50S.6G.1A external immutable snapshot loading is
authorized next.


## Accepted 50S.6G.1A external snapshot loading

The accepted Python seam loads one explicitly selected local immutable
snapshot directory and returns the same `SatelliteElementSnapshot` used by the
installed synthetic route. The directory name is operational only; the
validated manifest and canonical records digest retain scientific identity.

The directory and both required files must be real non-symlink filesystem
objects. Every manifest, canonical JSON, digest, full-NORAD, ordering, OMM,
epoch, provenance, warning, and count check is shared with the installed
loader. This slice neither obtains nor publishes data and does not broaden the
three-record, 60-second crossing domain.

Fernando scientifically and architecturally accepted 50S.6G.1A on 2026-09-17
after the 164-test focused gate and all 2,583 plugin-disabled tests passed.
Only a separately bounded 50S.6G.1B audit is authorized next.


## Accepted 50S.6G.1B representative snapshot preflight

The candidate audit makes policy a frozen reproducibility input. Wenu first
records the exact official CelesTrak policy bytes and digest; a later
acquisition requires explicit acknowledgement of that digest before a single
fixed Active-group CSV request. Network failure, redirect, changed policy, or
invalid data stops without retry and publishes nothing.

CelesTrak Active is a large representative population, not a complete census
of payloads, rocket bodies, debris, analyst, restricted, or lost objects. Raw
response and policy bytes remain local. A deterministic medium tier is derived
offline from the same parent response, while the installed synthetic snapshot
remains the fast oracle. Exact equality and resource evidence are bound to the
canonical snapshot digest; ordinary runtime defaults do not change.

Fernando scientifically and architecturally accepted 50S.6G.1B on 2026-09-17
after all 147 plugin-disabled current-documentation tests passed in 4.54
seconds. Only bounded 50S.6G.1B.1 fake-transport implementation is authorized
next; policy-digest approval for live acquisition remains separate.

### Offline 50S.6G.1B.1 builder

The implemented builder freezes exact policy bytes and requires their SHA-256
as the acquisition acknowledgement before invoking an injected GP transport.
It accepts only the fixed Active CSV header, preserves full NORAD identifiers,
adds only the four documented OMM constants, sorts by full NORAD identity, and
publishes only after typed-record and explicit-directory validation succeed.
The included developer command consumes local response files only. No live
transport, representative admission, or evidence matrix is implemented.

Fernando accepted 50S.6G.1B.1 on 2026-09-17 after 175 focused tests and all
2,594 plugin-disabled tests passed. No live provider access was exercised or
authorized by that acceptance.

A future provider may be audited only if it is public, reliable, and genuinely
independent in observation or orbit determination, rather than a mirror of
CelesTrak or Space-Track. It must have stable machine-readable access, explicit
policy and provenance, complete identifiers, and an auditable OMM-compatible
mapping. Introduce it first as a separate validation oracle, never as silent
fallback, automatic merge, or replacement of the authorized provider.

Fernando accepted the exact `non-HTTP 200` policy-clause compatibility
correction on 2026-09-17 after 10 focused tests and all 2,595 plugin-disabled
tests passed. The frozen 14,643-byte response has SHA-256
`67bf0faa7e026a7cd49799069db9d3355f2a867894133afd39e130d6185724aa`. The acceptance covers the parser and receipt only; it does not
approve a GP request or the digest acknowledgement required before one.

The first external Active snapshot contains 16,559 records. Its retained raw
response SHA-256 is `e54730e14b2097444c5e20bba6dd13d3e2d92f956797d49256ddb1a70ffe5014`; its canonical-record SHA-256 is
`e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`. CelesTrak's suffix-free six-fractional-digit `EPOCH` is UTC
by the provider contract and is stored with explicit `Z`; the captured HTTP
media type remains `text/plain; charset=UTF-8`. Fernando accepted this repair
and snapshot on 2026-09-17 after 15 focused and 2,600 complete plugin-disabled
tests. No second provider request or 50S.6G.1B.2 work was authorized.


## Accepted 50S.6G.1B.2A external admission

The validated Active snapshot is not an ordinary runtime default. The
accepted admission boundary requires its exact canonical-record SHA-256 plus
validated manifest identity through one explicit evidence-only token shared by
the conservative selector, accelerated coordinator, and multi-FoV batch.
Logical `snapshot_id`, directory name, raw-response digest, or policy digest
alone cannot authorize scientific use. Unsupported records remain
indeterminate or fail closed and must reach the accepted exact path where
required. Fernando scientifically and architecturally accepted this boundary
on 2026-09-17 after all 150 plugin-disabled current-documentation tests passed
in 3.84 seconds. Only bounded 50S.6G.1B.2B implementation is authorized next.


## Accepted 50S.6G.1B.2B admission

External evidence now requires an explicit immutable token created after exact
canonical-digest and manifest-identity comparison. The accepted CelesTrak
identity constant is inert: it neither locates nor loads the external
directory. The same token is checked by the conservative selector, accelerated
coordinator, and multi-FoV batch before their respective external work.

Missing, forged, mismatched, or substituted admission fails closed. Existing
synthetic defaults remain unchanged, and unsupported element or query domains
remain indeterminate or fail through their accepted paths. No external
snapshot is packaged, discovered, or enabled globally.


Fernando scientifically and architecturally accepted 50S.6G.1B.2B on
2026-09-17 after 51 focused runtime tests, 151 current-documentation tests,
and all 2,611 plugin-disabled tests passed; the complete suite took 215.89
seconds. `git diff --check` and the working tree were clean. Only bounded
50S.6G.1B.2C deterministic medium-specimen work is authorized next; 50S.6G.1B.2D
matrix execution and later delivery remain separately unauthorized.


## Accepted 50S.6G.1B.2C medium specimen

The proposed 256-record default is a deterministic coverage specimen, not a
population-frequency sample. It covers declared mean-motion, inclination,
eccentricity, BSTAR, signed-age, and NORAD-width bins independently, taking two
digest-ranked representatives from every non-empty bin before deterministic
fill. It remains an external non-default product bound to the exact admitted
parent and a complete selection receipt.


Fernando scientifically and architecturally accepted 50S.6G.1B.2C on
2026-09-17 after all 153 plugin-disabled current-documentation tests passed in
4.58 seconds; `git diff --check` and the working tree were clean. Only bounded
fake-data implementation is authorized next. The first real medium selection,
50S.6G.1B.2D matrix execution, and later delivery remain separately
unauthorized.

### Candidate 50S.6G.1B.2C medium specimen

The candidate `satellites/snapshot_evidence.py` service creates a
deterministic coverage specimen from one explicitly admitted parent. It checks
the acquisition report and captured provider bytes, selects two digest-ranked
representatives per nonempty independent bin, fills deterministically, and
publishes canonical records plus a path-free receipt beneath the subset digest.
It is not a statistical sample or completeness claim.

The developer `select-medium` command is offline. The 2026-09-17 fake-data
gate passed 30 plugin-disabled tests in 5.99 seconds. No external medium
snapshot is packaged, discovered, or selected automatically; the first real
medium selection and 50S.6G.1B.2D remain unauthorized.

### Accepted 50S.6G.1B.2C implementation

Fernando scientifically and architecturally accepted the fake-data medium
selector on 2026-09-17 at `1d9d4e4`. The complete plugin-disabled suite
passed 2,622 tests in 225.75 seconds; 185 focused tests passed in 9.03 seconds.
No real medium snapshot has been produced. The first real offline selection
requires separate authorization, and 50S.6G.1B.2D remains unauthorized.

### Candidate real medium specimen

The external specimen contains 256 records with canonical-record SHA-256
`2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`.
Its canonical selection receipt has SHA-256
`1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`.
It derives from the accepted 16,559-record parent
`e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`
using age reference `2026-09-17T15:52:23.000000Z`.

The specimen has 48 mandatory representatives, 208 deterministic fill records,
and no empty bin. It remains an external deterministic coverage specimen—not a
statistical sample, complete catalogue, packaged default, or population claim.
The parent bytes were unchanged and the operation made no provider request.
Acceptance and 50S.6G.1B.2D authorization remain separate decisions.

### Accepted real 50S.6G.1B.2C specimen

Fernando accepted exact external specimen
`2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`
with receipt
`1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`
on 2026-09-17 at `c4cd009`; 157 plugin-disabled documentation tests passed
in 4.66 seconds. It remains external, immutable, and non-statistical.
50S.6G.1B.2D remains separately unauthorized.

### Candidate 50S.6G.1B.2D equivalence matrix

The documentation-only candidate defines 10 deterministic same-observer La Ligua fields on
one UTC night, with different centres and intervals plus a shared-interval
research control. The accepted 256-record specimen is explicitly admitted to
both exhaustive and accelerated services. Success requires identical ordered
crossing results, complete conservative-selection evidence, no fallback, and
no rejected satellite with an exhaustive crossing.

Resource measurements are descriptive evidence, not a speed claim. The matrix
is not executed by this audit and creates no chart, track, report route, or
runtime default.

### Accepted 50S.6G.1B.2D audit

Fernando accepted the strict equivalence-matrix audit on 2026-09-17 at
`6e7a8b9`; 159 plugin-disabled documentation tests passed in 10.75 seconds.
Only fake-data harness implementation is authorized next. The accepted real
256-record specimen must not be executed, and no speed or downstream delivery
claim is authorized.

### Candidate 50S.6G.1B.2D fake-data implementation

The candidate `satellites/crossing_matrix.py` implementation enforces exact
Python-result equality, canonical-byte and digest equality, complete
reject/retain/indeterminate evidence, forbidden exhaustive fallback, isolated
resource observations, and atomic evidence publication with manifest
revalidation. Candidate commit `19520f3` passed 2634 plugin-disabled
full-suite tests in 230.25 seconds on 2026-09-17.

This verification used fake data only. The accepted real 256-record specimen
was not read, the real ten-field matrix was not executed, and no speed or
capacity claim was made. Fernando's scientific and architectural acceptance
is required before any separately authorized real-matrix execution.

### Accepted 50S.6G.1B.2D fake-data implementation

Fernando scientifically and architecturally accepted the bounded fake-data
matrix implementation on 2026-09-17. Its recorded evidence is 2634
plugin-disabled full-suite tests in 230.25 seconds at `19520f3`, followed by
161 plugin-disabled current-documentation tests in 3.32 seconds at
`3ef6a4d`. The accepted closure neither reads the real 256-record specimen
nor executes the real ten-field matrix. Only a separately bounded
real-execution audit is authorized next.

### Candidate real-execution readiness audit

The accepted fake-data matrix core at `9bdf301` is not yet ready for the
first real run. The exact ten-field La Ligua fixture, production whole-interval
airmass certifier, isolated subprocess worker, and explicit offline developer
command remain to be implemented and proven with fake data. This audit did not
read the accepted real 256-record specimen or execute either route. Only the
bounded production-path implementation may proceed next; the real matrix and
all performance conclusions remain unauthorized.

### Accepted real-execution readiness audit

Fernando scientifically and architecturally accepted the not-ready finding on
2026-09-17 after 163 plugin-disabled current-documentation tests passed in
3.80 seconds at `054ac39`. Only the bounded fake-data production-path
implementation may proceed next. The accepted real 256-record specimen must
remain untouched and the real ten-field matrix must not be executed.\n

### Candidate offline equivalence-matrix execution path

The candidate `run-equivalence-matrix` developer command is explicit and
offline. It requires the snapshot and output directories, all three accepted
digests, and an exact operator acknowledgement. Before any route process
starts it validates the complete accepted selection receipt, constructs the
digest-frozen La Ligua fields, and atomically certifies their centre-only
airmass. Each route/query/repetition then runs in a fresh subprocess. The
fixture contains only 15- and 60-second intervals and its tests use fake data
and bounded subprocess doubles. The command performs no discovery, download,
refresh, fallback, concurrency, or cache reuse.\n

Candidate verification on Fernando's Mac completed at executable commit
`81f9031`: the 14-test focused matrix gate passed in 9.35 seconds, the
210-test immediate-boundary and documentation gate passed in 60.26 seconds,
and all 2,645 plugin-disabled tests passed in 243.71 seconds. `git diff
--check 5cd60fd...HEAD` and the working tree were clean. No accepted real
specimen was accessed and no real matrix was executed. The candidate still
requires Fernando's scientific and architectural acceptance.\n

### Accepted production-path implementation

Fernando scientifically and architecturally accepted the bounded fake-data
production-path implementation on 2026-09-18. The executable evidence remains
14 focused tests in 9.35 seconds, 210 immediate-boundary tests in 60.26
seconds, and all 2,645 plugin-disabled tests in 243.71 seconds at `81f9031`.
After documentation-only evidence recording, 164 current-documentation tests
passed in 3.94 seconds at `602eed7`; the whitespace check and working tree
were clean.

Preserve the exact accepted-medium and receipt constraints, digest-frozen
ten-field La Ligua fixture with only 15- and 60-second intervals, production
whole-interval airmass certifier, canonical fresh-subprocess worker/executor,
explicit offline command, and shortened fake-data test practice. This
acceptance does not authorize accessing the accepted real specimen, executing
the real matrix, publishing real evidence, making a performance claim, or
advancing later delivery. Any real execution requires a separate explicit
authorization.\n

### Candidate first real equivalence run

Candidate 50S.6G.1B.2D.1 proposes exactly one operator-started use of
`run-equivalence-matrix` with explicit absolute snapshot and output paths,
all three accepted digests, and the exact acknowledgement. The output root
must be new, empty, external, and have at least 2 GiB free. The run allows no
network, discovery, refresh, substitution, retry, resume, changed fixture, or
changed policy. A successful evidence directory remains external and
unaccepted until a separate review.\n

### Accepted first-real-execution authorization

Fernando scientifically and architecturally accepted 50S.6G.1B.2D.1 on
2026-09-18 after all 165 plugin-disabled current-documentation tests passed in
5.07 seconds at `af8044a`; the whitespace check and working tree were clean.

This acceptance authorizes exactly one operator-started offline execution
against the exact accepted 256-record medium, using the three frozen digests,
exact acknowledgement, accepted ten-field 15/60-second fixture, one new empty
external output root with at least 2 GiB free, the existing 3600-second
per-subprocess timeout, and no retry or resume. It does not itself start the
run. The exact absolute Mac paths must be resolved before the command is
issued. Failure or interruption authorizes no restart. Successful evidence
remains external and unaccepted pending an independent review; no performance
claim or later 50S.6G delivery is authorized.\n

### Candidate equivalence-run progress display

The offline matrix command candidate displays a terminal bar with completed
workers over the policy-derived total, integer percentage, field, route, and
phase. Under the accepted default it advances from 0/80 to 80/80. The display
is parent-only stderr text and is not scientific evidence. A running worker may
leave the same line visible for a long time; completion advances only after
that fresh subprocess returns successfully.

## Candidate equivalence-run progress verification

Candidate `b0b4432` passed 180 focused plugin-disabled tests in 5.44 seconds and the full 2647-test plugin-disabled suite in 239.53 seconds on 2026-09-18; the diff check was clean. The progress display remains parent-only and outside canonical evidence. The real specimen was not accessed, the run has not started, and renewed authorization remains pending.

## Accepted equivalence-run progress display

Fernando scientifically and architecturally accepted candidate `96b9ba0` on 2026-09-18 after the recorded focused, full-suite, final-documentation, and diff verification. The display remains parent-only and outside canonical evidence. The real specimen has not been accessed, the run has not started, and execution still requires post-merge renewed authorization.

## Renewed single real equivalence run

After progress-display merge `9c4b808`, Fernando explicitly renewed authorization on 2026-09-18 for exactly one real matrix run. It must use the accepted immutable specimen, exact fixture and 10 fields, only 15/60-second intervals, both routes, one warm-up and three measurements, at most 80 fresh subprocesses, a new empty external output root, and no retry or resume. Progress is operational stderr only; successful artifacts remain unaccepted candidate evidence.

## Accepted renewed single real run

Fernando scientifically and architecturally accepted candidate `dd71e01` on 2026-09-18 after 169 plugin-disabled documentation tests passed in 4.29 seconds and repository checks were clean. The run remains unstarted and unconsumed; merge and repeated external preflight are required before execution.

## Candidate first real equivalence evidence

The consumed one-run authorization produced candidate report `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258` from `9d93113` on 2026-09-18. Ten fields, both 15/60-second intervals, 60 measured observations, all decision classes, and exact route equality passed with no fallback. All fields had zero crossings, so positive crossing remains synthetic-only evidence. The observed acceleration is descriptive for the exact specimen and 2017 Intel Mac, not a general speed claim.

## Accepted first real equivalence evidence

Fernando scientifically and architecturally accepted report `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258` at `186e255` on 2026-09-18 after 171 documentation tests passed in 4.46 seconds. This closes the first real run as exact empty-result equivalence and conservative partition evidence. All fields had zero crossings; observed timing is descriptive only, and no rerun or parallelization is authorized.


## Candidate bounded 50S.6G.1B closure

At integrated baseline `b010a6c`, the representative-snapshot foundation is
implemented and its accepted real matrix demonstrates exact empty-result
equivalence and complete conservative partitions. All ten real fields had zero
crossings; positive-crossing behavior remains synthetic evidence.

The candidate closure expressly defers a full-snapshot matrix, wider FoV-count
matrix, comprehensive real crossing geometries, and universal performance,
capacity, concurrency, or reuse claims. The consumed real-run authority is not
renewed. No provider request, artifact refresh, rerun, report, CLI, track,
chart, illumination, or brightness work is authorized.

Pending Fernando's separate scientific and architectural acceptance,
50S.6G.1B remains open. Acceptance would authorize only a separate
documentation audit of 50S.6G.2A canonical exact-crossing reports and
deterministic JSON, not implementation.


## Accepted bounded 50S.6G.1B closure

Fernando scientifically and architecturally accepted the bounded closure on
2026-09-19 at `c62a451`, after all 173 plugin-disabled documentation tests
passed in 3.82 seconds and repository checks were clean. The representative
foundation is closed with exact empty-result equivalence and conservative
partition integrity; every real field had zero crossings. Deferred scale and
performance evidence remains explicitly unclaimed.

Only a bounded 50S.6G.2A documentation audit is authorized next. No report,
JSON Schema, encoder, round trip, CLI, track, or chart implementation is
authorized.


## Candidate 50S.6G.2A canonical exact-crossing report

The candidate report is a versioned immutable account of geometric exact local
crossings, explicitly not a visibility forecast. It preserves complete
observer, snapshot, policy, field, airmass, crossing, tolerance, provenance,
warning, and implementation identity. Zero crossings are explicit valid field
results. Creation time is supplied once, and canonical JSON plus a report
digest make repeated serialization deterministic.

Schema version 1 requires illumination, apparent magnitude, detector effect,
and exact-track samples to be null because those quantities are not evaluated.
The candidate remains separate from SatChecker sampled-candidate evidence.
Implementation is unauthorized pending Fernando's acceptance.


## Accepted 50S.6G.2A exact-report audit

Fernando scientifically and architecturally accepted the canonical
exact-crossing report and deterministic JSON audit on 2026-09-19 at candidate
commit `835ddfe`, after 175 plugin-disabled current-documentation tests passed
in 3.27 seconds; the diff check and working tree were clean.

Only the bounded immutable logical model, packaged Draft 2020-12 JSON Schema,
pure deterministic encoder/decoder, and focused exact-report tests are
authorized next. ECSV/VOTable, CLI/files, tracks, charts, illumination,
magnitude, detector effects, provider access, another real run, and unrelated
refactoring remain unauthorized.


## Candidate 50S.6G.2A exact-report implementation

The bounded candidate adds the dedicated immutable exact-local report model,
packaged closed Draft 2020-12 schema, deterministic JSON and report identity,
strict typed decoder, and focused synthetic tests. The first focused gate
passed 15 tests in 9.38 seconds at `f5f58b5`; after typed reconstruction was
added, the same 15 tests passed in 2.31 seconds at `f8d2e51`. The immediate
satellite boundary gate then passed 99 tests in 119.54 seconds.

A later decoder-isolation refinement loads the packaged schema once so each
decode/re-encode operation performs no filesystem access. At executable commit
`a65e5ac`, the combined focused and documentation gate passed 195 tests in
5.46 seconds; `git diff --check 378d2dd...HEAD` passed; and the complete
plugin-disabled suite passed 2,676 tests in 234.08 seconds. The working tree
was clean and synchronized.

The candidate remains pending Fernando's scientific and architectural
acceptance. No later 50S.6G work or new scientific execution is authorized.


## Accepted 50S.6G.2A exact-report implementation

Fernando scientifically and architecturally accepted the bounded 50S.6G.2A
implementation on 2026-09-19. The executable candidate at `a65e5ac` passed
all 2,676 plugin-disabled tests in 234.08 seconds; the final pre-acceptance
documentation gate at `8af0d14` passed 179 tests in 5.05 seconds; diff and
working-tree checks were clean.

This acceptance closes only the immutable JSON logical-report slice. It does
not authorize ECSV/VOTable, CLI/file publication, atomic writing, exact tracks,
charts, illumination, magnitude, detector effects, provider access, scheduling
integration, or another scientific execution.


## Candidate 50S.6G.2B tabular interoperability audit

After accepted 50S.6G.2A and merge commit `57c8bec`, the next bounded
documentation audit defines lossless in-memory ECSV and IVOA VOTable 1.5
encodings. The as-is review found existing repository ECSV precedent for units
and types, no existing VOTable production convention, and no authority to make
format bytes the scientific identity.

The candidate therefore retains canonical JSON identity and requires one
shared reusable format-neutral projection with thin ECSV/VOTable adapters.
It preserves validated zero-crossing fields, order, units, masks, coordinate
and UTC metadata, stable joins, provenance, and null future science. It
separates portable logical round-trip identity from same-encoder byte
determinism.

This entry records a candidate audit, not acceptance. No implementation,
filesystem publication, CLI, tracks, visibility science, provider access, or
new execution is authorized.


## Verified candidate 50S.6G.2B audit

At `ef14bc1`, all 181 plugin-disabled documentation tests passed in 4.88
seconds. The diff check against accepted program base `57c8bec` passed, and
the branch was clean and synchronized.

This verification establishes that the lossless ECSV/VOTable audit, reusable
shared projection rule, thin-adapter boundary, active-document index, and
bounded exclusions agree across current documentation. It is not scientific
or architectural acceptance and authorizes no implementation.

## Accepted 50S.6G.2B tabular interoperability audit

Fernando scientifically and architecturally accepted the documentation-only
audit on 2026-09-19 at `ef14bc1`. All 181 plugin-disabled
current-documentation tests passed in 4.88 seconds; the diff check against
`57c8bec` passed, and the branch was clean and synchronized.

Only bounded in-memory implementation is authorized next: one shared reusable
format-neutral projection, thin ECSV and VOTable 1.5 adapters, strict
validation, and lossless reconstruction preserving canonical JSON and
`report_identity_sha256`. Filesystem publication, CLI, tracks, charts,
visibility science, provider access, and new execution remain unauthorized.


### Candidate 50S.6G.2B in-memory tabular interoperability

At `3bbd82f`, the candidate adds one private reusable schema-derived tabular
projection and thin deterministic ECSV and VOTable 1.5/BINARY2 adapters for
the accepted exact local crossing report. Canonical JSON and
`report_identity_sha256` remain authoritative. The accepted Astropy 7.1.0
workaround uses explicit adjacent Boolean `__is_null` VOTable FIELDs only
for nullable Unicode values; it does not reinterpret an unmarked empty string.

The combined plugin-disabled report/documentation gate passed 208 tests in
6.68 seconds, and the complete plugin-disabled suite passed all 2,689 tests in
215.15 seconds. The diff check against `142ae70` passed, and the Mac branch
was clean and synchronized. This is candidate verification, not scientific or
architectural acceptance or merge authority. 50S.6G.2C and all filesystem,
CLI, publication, track, chart, visibility, provider, and new-execution work
remain unauthorized.


### Accepted complete 50S.6G.2B in-memory interoperability

Fernando scientifically and architecturally accepted the complete bounded
50S.6G.2B implementation on 2026-09-19. Executable commit `3bbd82f` passed
208 focused tests in 6.68 seconds and all 2,689 plugin-disabled tests in
215.15 seconds. Documentation evidence commit `ece80c7` passed all 186
current-documentation tests in 4.60 seconds; diff checks and the clean,
synchronized Mac working tree passed.

The accepted product provides deterministic lossless in-memory ECSV and
VOTable 1.5/BINARY2 carriers through one shared schema-derived projection.
Canonical JSON and `report_identity_sha256` remain authoritative, and
nullable Unicode VOTable fields use explicit `__is_null` companions required
by Astropy 7.1.0 behavior. This acceptance authorizes no later milestone;
50S.6G.2C, filesystem/CLI publication, tracks, charts, visibility science,
provider access, another real run, and unrelated refactoring remain
unauthorized.

## 2026-09-19 — Candidate 50S.6G.2C CLI/file-protocol audit

A documentation-only candidate defines one offline CLI/filesystem adapter for
direct atomic calculation and the digest-bound two-call JSON workflow. It
preserves every invalid FoV explicitly, calculates only a revalidated embedded
valid subset on the second call, and reuses the accepted canonical JSON,
ECSV, and VOTable report encoders for an atomic no-clobber bundle. This is a
candidate audit, not acceptance, and it authorizes no implementation or later
track/chart work.

## 2026-09-19 — Accepted 50S.6G.2C audit

Fernando scientifically and architecturally accepted the CLI and two-call
file-protocol audit at `bcac404`. Verification comprised 188 plugin-disabled
current-documentation tests in 5.29 seconds, a clean diff check, and a clean,
synchronized Mac working tree. Only the bounded offline implementation is
authorized next; no track, chart, provider, new science, visibility,
illumination, or brightness work is authorized.

## 2026-09-19 — Verified candidate 50S.6G.2C implementation

At `e08ebf5`, 235 immediate tests passed in 7.63 seconds and all 2,709
plugin-disabled repository tests passed in 237.35 seconds. CLI help, diff, and
clean synchronized-tree checks also passed. The implementation remains a
candidate awaiting Fernando's separate scientific and architectural
acceptance.

## 2026-09-19 — Accepted 50S.6G.2C implementation

Fernando scientifically and architecturally accepted the bounded offline
CLI/file protocol. Executable evidence is 235 immediate tests and 2,709 full
plugin-disabled tests at `e08ebf5`; final documentation evidence is 191 tests
at `f2bb49c`. Only a documentation-first 50S.6G.3A audit is authorized next.

## 2026-09-19 — Candidate 50S.6G.3A exact-local-track audit

A documentation-only candidate defines immutable exact track evidence for one accepted connected visit and an output-neutral evidence-only layer. It reuses the accepted snapshot, SGP4/TEME, and geometric topocentric route; retains exact entry, closest-approach, and exit anchors; and uses deterministic adaptive sampling with explicit fail-closed limits. SatChecker candidate tracks, accepted reports/CLI, charts, planispheres, providers, visibility, illumination, and brightness remain unchanged and unauthorized.

## 2026-09-19 — Accepted 50S.6G.3A audit

Fernando scientifically and architecturally accepted the documentation-only audit at `ce54971`. Verification comprised 193 plugin-disabled current-documentation tests in 5.73 seconds plus clean diff and synchronized-tree checks. Only the bounded exact connected-visit evidence and output-neutral layer implementation is authorized next; 50S.6G.3B and later work remain unauthorized.

## 2026-09-19 — Candidate 50S.6G.3A implementation

At `98a756d`, the candidate adds immutable exact local track evidence, accepted-route composition, deterministic anchored adaptive sampling, fail-closed limits, exact-visit identity, and evidence-only path/event layers. Fernando authorized the implementation-preflight representation correction: a timeless collection specification with evidence-level UTC and per-sample UTC instants. The focused plugin-disabled gate passed 69 tests in 75.58 seconds; full verification and separate acceptance remain pending.

## 2026-09-19 — Verified candidate 50S.6G.3A implementation

At `f0a4164`, all 2,728 plugin-disabled repository tests passed in 222.01 seconds. The 195-test documentation gate passed in 5.86 seconds, and diff plus clean synchronized-tree checks passed. This is candidate verification only; implementation acceptance, merge, and 50S.6G.3B remain unauthorized.

## 2026-09-19 — Accepted complete 50S.6G.3A implementation

Fernando scientifically and architecturally accepted the bounded implementation and authorized merge. Evidence comprises 69 focused tests, 2,728 complete plugin-disabled tests, 195 and 196 documentation tests, clean diff checks, and a clean synchronized Mac tree. Only a documentation-first 50S.6G.3B audit is authorized next.

## 2026-09-19 — Candidate 50S.6G.3B chart-integration audit

A documentation-only candidate defines how accepted exact connected-visit evidence may enter ordinary binocular and regional stereographic horizontal chart requests. It preserves one fixed product frame, existing projection/clipping/render/export owners, explicit request lifecycle cleanup, stable semantics, and bounded provenance. It authorizes no implementation or planisphere/later science work.

## 2026-09-19 — Accepted 50S.6G.3B audit

Fernando scientifically and architecturally accepted the documentation-only chart-integration audit at `ef58180`. Verification comprised 198 plugin-disabled documentation tests in 5.30 seconds plus clean diff and synchronized-tree checks. Only the bounded binocular/regional implementation and specimens are authorized next.

## 2026-09-19 — Candidate 50S.6G.3B implementation

The bounded candidate adds explicit already-realized exact-track display requests, strict regional/binocular admission, fixed-frame path/event views, independent labels, request-owned cleanup, narrow style roles, bounded provenance, semantic SVG hierarchy, focused tests, and deterministic PNG/PDF/SVG specimens. The first focused gates passed 119 and 136 plugin-disabled tests. Fernando found and rejected two deliberately distorted boundary-crossing specimen shapes; the accepted visual direction is a physically plausible nearly straight short pass, with canonical clipping demonstrated separately by tests. Complete verification and separate implementation acceptance remain pending.

## 2026-09-19 — Verified candidate 50S.6G.3B implementation

At `6580f88`, the 314-test immediate gate passed in 7.71 seconds and all 2,741 plugin-disabled tests passed in 228.97 seconds. The physically propagated 65-sample exact visit generated regional and binocular PNG, PDF, and semantic SVG through the ordinary route. Fernando judged the binocular field consistent and the revised 20 by 16 degree regional context much better. Exact-head, diff, and clean synchronized-tree checks passed. This is candidate verification only; implementation acceptance, merge, and 50S.6G.4A/B remain unauthorized.

## 2026-09-19 — Accepted complete 50S.6G.3B implementation

Fernando scientifically and architecturally accepted the bounded implementation and explicitly authorized merge and cleanup. PR 172 merged `ff2e225` into `program/50s-crossing-foundation` at `05d4029`. Evidence comprises 314 immediate tests, all 2,741 plugin-disabled tests, 199 final documentation tests, physical regional/binocular PNG/PDF/semantic-SVG review, and clean diff, exact-head, and synchronized-tree checks. Only a documentation-first 50S.6G.4A planisphere audit is authorized next; runtime planisphere/later science remains unauthorized.

## 2026-09-19 — Candidate 50S.6G.4A stereographic planisphere audit

A documentation-only candidate defines an event-specific exact-track overlay
for Wenu's paired physical stereographic polar planisphere. It distinguishes
that product from the ordinary horizontal full-sky planisphere, preserves
geometric topocentric fixed-axis meaning, resolves north/south overlap and cap
clipping, keeps the physical horizon and masks outside satellite admission,
and requires paired lifecycle cleanup, bounded non-recurrence provenance, and
physical PNG/PDF/semantic-SVG evidence. It authorizes no implementation or
later satellite science.

## 2026-09-19 — Accepted 50S.6G.4A stereographic planisphere audit

Fernando scientifically and architecturally accepted the documentation-only
audit at `c1d9015`. Verification comprised 200 plugin-disabled documentation
tests in 5.29 seconds plus exact-head, upstream, diff, and clean-tree checks.
Only the bounded 50S.6G.4B paired stereographic-planisphere implementation and
required physical north/south specimens are authorized next.

## 2026-09-20 — Corrective 50S.6G.4A AltAz planisphere audit

Fernando rejected the unmerged candidate at 7a00b15 because it placed exact
tracks on paired equatorial polar-planisphere faces. The required product is
the ordinary ChartRequest planisphere: one zenith-centred FullSkyChart in
horizontal AltAz with stereographic projection and a horizon boundary.

A documentation-only corrective candidate now supersedes the paired-polar
50S.6G.4B authority while preserving accepted 3A evidence and 3B ordinary-chart
work. It proposes only widening exact-track family admission to planisphere and
requires fixed AltAz realization, horizon-boundary evidence, lifecycle and
state isolation, bounded semantics/provenance, unchanged empty output, and one
physical La Ligua PNG/PDF/semantic-SVG specimen. No implementation is
authorized before Fernando's separate acceptance.

## 2026-09-20 — Accepted corrective 50S.6G.4A audit

Fernando scientifically and architecturally accepted the corrective AltAz
planisphere audit at 80855938. Verification comprised 201 plugin-disabled
current-documentation tests in 6.14 seconds plus clean diff, exact-head,
upstream, and working-tree checks. Only the bounded corrected 50S.6G.4B
ordinary planisphere implementation and its focused and physical acceptance
evidence are authorized next.

## 2026-09-20 — Verified candidate 50S.6G.4B implementation

Executable candidate `91eafff5` widened exact-track admission only to the
ordinary AltAz stereographic planisphere and added focused plus physical review
evidence. The focused gate passed 252 tests in 7.08 seconds and the full
plugin-disabled suite passed 2,744 tests in 220.63 seconds. A 65-sample
physically propagated La Ligua visit produced non-empty PNG, PDF, and semantic
SVG with track digest
`3f526de147caae6832c7a56330d460948c4b8963c7cdbf753618682e70d4248a`.

Fernando reviewed the horizon-bounded chart and noted that its test-only title
was too long; the manifest already carries the chart and event times, so this
was non-blocking. Exact-head, upstream, diff, and clean-tree checks passed.
The candidate awaits separate scientific and architectural acceptance; no
merge or later work is authorized.

## 2026-09-20 — Accepted complete 50S.6G.4B implementation

Fernando scientifically and architecturally accepted the corrected ordinary
AltAz stereographic planisphere implementation and explicitly authorized
merge. PR 176 merged final candidate `6bc623b` into
`program/50s-crossing-foundation` at `f0730d8`.

Evidence comprises 252 focused tests in 7.08 seconds, all 2,744 plugin-disabled
tests in 220.63 seconds, 202 final documentation tests in 5.19 seconds, the
physically propagated 65-sample La Ligua PNG/PDF/semantic-SVG specimen, and
clean diff, exact-head, upstream, and working-tree checks. The test-only long
title was non-blocking because the manifest retains the chart and event times.

This closes 50S.6G delivery. Only a documentation-first 50S.6H Paranal, ELT,
and general observatory-planning adapter audit is authorized next. Adapter
runtime, observatory writes, scheduling decisions, illumination, brightness,
and all 50S.7+ behavior remain unauthorized.
## Accepted 50S.6H observatory-planning adapter audit

On 2026-09-20, work began from accepted 50S.6G base
`e37298db29af84bd92443287ae1574cf471b76e8` on a documentation-only audit of
Paranal, ELT, and general observatory-planning adapters.

Official ESO material establishes that Paranal Phase 2 uses OBs in p2 and that
the p2 API immediately mutates ESO database state. ESO currently plans ELT
telescope first light for 2029 and scientific first light for December 2030;
the audit therefore does not infer an ELT operations API from Paranal.

Fernando scientifically and architecturally accepted the audit on 2026-09-20.
It authorizes next only an offline general JSON advisory
that intersects caller-supplied planned UTC intervals with accepted exact
crossing intervals. Paranal remains non-writing context and ELT remains a
reserved unsupported profile. Facility access or writes, scheduling decisions, ELT operational mapping, and
50S.7+ work remain unauthorized.
## Accepted 50S.6H offline planning-advisory implementation

After acceptance and merge of the audit at `4923cf3`, the bounded feature
candidate added the frozen general planning context, half-open overlap
projection, strict canonical JSON advisory, typed stable failures, public
exports, and focused tests.

The implementation remains offline and observatory-neutral. Paranal and ELT
profiles, facility network access or writes, scheduling decisions, and 50S.7+
science remain excluded. Fernando accepted the complete implementation on
2026-09-20.
The candidate validation tool owns reproducible offline positive and zero-row
JSON specimens plus a digest manifest. It uses packaged synthetic data and
performs no facility access.
## Accepted complete 50S.6H implementation evidence

Revision `32dce675e82ab9bdd806455a0c3e423a3e6f67b3` passed 226 focused and
documentation tests in 8.86 seconds and all 2,769 plugin-disabled tests in
217.10 seconds. Offline review produced one two-second positive row and one
endpoint-touch zero-row advisory from source report identity
`36899d514813784058a2ab887244b6dafbc371c78dec1111f0cc85dfdabaeba7`.
Their advisory identities begin `2e413ca5` and `a2a83fbf`, respectively;
the manifest declares no network access.

Diff, exact-head, upstream, and clean-tree checks passed. Fernando accepted
the verified implementation on 2026-09-20. After merge, only a
documentation-first 50S.7 illumination and night-geometry audit is authorized
next; facility integration and 50S.7+ runtime remain unauthorized.

## 2026-09-20 — Candidate 50S.7A illumination and night-geometry audit

Work began from accepted 50S.6H merge
`2659b46ea9194a9d2e0e7cdad311a5fc68d51b4c`. The documentation-only candidate
defines Sunlight, solar Earthshine, Moonlight, and Lunar-Earthshine as four
independent incident components; separates finite-source shadow and observer
twilight geometry from 50S.8 apparent brightness; and records fidelity,
identity, failure, event-search, and validation gates.

The current Caddy et al. moonlit-satellite preprint is treated as motivating
observational evidence, not a frozen numerical standard. The proposed first
implementation is only direct finite-Sun/WGS-84 vacuum occultation plus
geometric observer-night state. The audit remains a candidate and authorizes
no runtime, merge, branch deletion, or later work.

## 2026-09-20 — Accepted 50S.7A illumination and night-geometry audit

Fernando scientifically and architecturally accepted the complete
documentation-only audit at `fdf7e005a41a5a4d45200f841e914815d37da870`. The final
206 plugin-disabled current-documentation tests passed in 5.87 seconds, and
diff, exact-head, upstream, and clean-working-tree checks passed.

After merge, only bounded 50S.7B direct-Sun and observer-night geometry is
authorized: finite uniform-Sun/WGS-84 vacuum occultation, typed shadow state,
geometric twilight, provenance, and focused offline validation. 50S.7C and
later radiometry, reflected-source fields, brightness, detector, visibility,
facility, scheduling, and unrelated work remain unauthorized. PR merge and
branch deletion require separate explicit authorization.
## Candidate 50S.7B direct-Sun and observer-night geometry

The feature branch implements the bounded accepted slice with immutable
finite-Sun/WGS-84 vacuum occultation, typed shadow class, geometric observer
twilight, same-instant ITRS composition, complete input/model provenance, and
fail-closed bounded adaptive quadrature. The focused 24-test illumination gate
passed in 4.86 seconds on Fernando's Mac at revision `5ffae3a`.

An offline installed-DE440 binary Skyfield and selected SPICE classification
validator plus complete repository/documentation gates remain pending. The
candidate is not yet accepted. 50S.7C transitions and all radiometric,
reflected-source, brightness, detector, facility, visibility, and scheduling
work remain unauthorized.
### Candidate 50S.7B independent validation

At `51b935f`, all 24 illumination tests passed in 5.58 seconds. The offline
validator reported SPICE agreement for sunlit, penumbra, umbra, and antumbra,
then used installed DE440 `de440s.bsp` SHA-256
`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`
to obtain 20 Skyfield full-light and 5 full-shadow matches. Complete and final
repository gates remain pending; the candidate is unaccepted.

### Complete candidate 50S.7B gate

Executable revision `086e7da1` passed 291 expanded tests in 18.81 seconds,
208 current-documentation tests in 6.47 seconds, the clean branch diff, and all
2,796 plugin-disabled repository tests in 233.66 seconds. Exact upstream and a
clean working tree were confirmed. Combined with the SPICE/Skyfield receipt,
the bounded implementation is ready for Fernando's separate scientific and
architectural review. Merge, branch deletion, 50S.7C, and later work remain
unauthorized.

## Accepted 50S.7B direct-Sun and observer-night geometry

Fernando scientifically and architecturally accepted the verified candidate
at `054ac53a` on 2026-09-21. The final 208-test documentation gate passed in
4.19 seconds; the earlier 24 focused, SPICE/Skyfield, 291 expanded, 2,796
complete, diff, upstream, and clean-tree evidence remains accepted.

PR 181 merge and branch deletion require separate explicit instructions. After
merge only a documentation-first 50S.7C shadow-transition audit is authorized;
transition implementation and all later light, brightness, detector,
visibility, facility, and scheduling work remain unauthorized.

## 2026-09-21 — Candidate 50S.7C shadow-transition audit

Work began from accepted 50S.7B merge
`f9aa2dd7e7d197f015b0df7667c1fd5804e99428` on branch
`docs/50s7c-shadow-transition-audit`. The documentation-only candidate
defines observer-independent directed shadow events, continuous
finite-Sun/WGS-84 contact margins, certified UTC brackets, complete bounded
interval search, deterministic identity, fail-closed budgets, and independent
SPICE/Orekit event evidence.

The as-is review rejects visible-fraction quadrature, fixed-cadence sign scans,
chart interpolation, and the 50S.5 empirical motion envelope as contact-
completeness oracles. It keeps the future solver in the existing illumination
owner and proposes only a minimal shared geocentric ITRS seam in the
topocentric owner.

The audit adds no runtime and remains unaccepted. Transition implementation,
50S.7D+ light models, brightness, visibility, detector, facility, and
scheduling work remain unauthorized.

## 2026-09-21 — Accepted 50S.7C shadow-transition audit

Fernando scientifically and architecturally accepted exact candidate
`030a632243349c34a1455743ae9bf40ced39e755`. The complete
current-documentation gate passed 210 plugin-disabled tests in 5.81 seconds;
the branch diff, exact upstream, and clean-tree checks passed.

After merge, only the bounded 50S.7C implementation is authorized:
observer-independent continuous contact geometry, complete bounded search for
one selected record and admitted closed interval, directed events, certified
brackets, deterministic identity, terminal failure, the minimal shared
geocentric ITRS seam, focused tests, and offline independent event validation.

PR 182 merge and branch deletion remain separately authorized operations.
50S.7D+, report/chart/planning integration, brightness, visibility, detector,
facility, scheduling, and unrelated work remain unauthorized.

## 2026-09-21 — Candidate 50S.7C shadow-transition implementation

The feature branch `feature/50s7c-shadow-transitions` implements the accepted
bounded slice. Runtime commits add the shared geocentric ITRS seam, continuous
finite-Sun/WGS-84 contact geometry, immutable query/policy/result contracts,
complete bounded recursive search, six directed adjacent kinds, certified
brackets, deterministic identity, and stable fail-closed limits.

At executable `69375fab`, 58 focused illumination/topocentric tests passed in
16.67 seconds. The offline no-download validator used SpiceyPy 6.0.3, CSPICE
N0067, and installed DE440 SHA-256
`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`.
SPICE `gfoclt` reproduced four directed full-shadow contacts with 277 Wenu
evaluations and four annular contacts with 717 evaluations. Skyfield matched
20 full-light and 5 full-shadow states.

Documentation and complete repository gates remain pending. The candidate is
unaccepted; merge, branch deletion, 50S.7D+, output integration, radiometry,
brightness, visibility, detector, facility, and scheduling remain
unauthorized.

### Complete candidate 50S.7C gate

Exact candidate `bf877404` passed 311 expanded implementation/dependency
tests in 21.47 seconds, 212 current-documentation tests in 7.01 seconds, the
clean branch diff, and all 2,816 plugin-disabled repository tests in 218.58
seconds. Exact local/upstream equality and a clean working tree were confirmed.
The earlier no-download SPICE `gfoclt` full/annular event receipt and Skyfield
binary-side receipt remain part of the candidate evidence.

The bounded implementation is ready for Fernando's separate scientific and
architectural review. Merge, branch deletion, 50S.7D+, output integration,
radiometry, brightness, visibility, detector, facility, scheduling, and
unrelated work remain unauthorized.

## 2026-09-21 — Accepted 50S.7C shadow-transition implementation

Fernando scientifically and architecturally accepted exact branch head
`eaeab6085b52bfed6136d37f3010c2f353e59f53`. Executable `bf877404`,
the no-download SPICE/Skyfield receipt, 311 expanded tests in 21.47 seconds,
212 documentation tests in 7.01 seconds, all 2,816 plugin-disabled repository
tests in 218.58 seconds, the clean diff, exact upstream, and clean tree are
accepted evidence. The final timing clarification passed 212 documentation
tests in 4.72 seconds.

PR 183 merge and branch deletion remain separate explicit operations. 50S.7D+,
output integration, radiometry, reflected fields, brightness, visibility,
detector, facility, scheduling, and unrelated work remain unauthorized.
