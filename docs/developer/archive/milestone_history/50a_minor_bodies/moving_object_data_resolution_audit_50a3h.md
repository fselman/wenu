# Moving-object data resolution audit (Milestone 50A.3H)

**Status:** Accepted by Fernando

**Base:** `e30f27d`

**Date:** 2026-09-12

**Runtime effect:** None

**Acceptance:** Fernando accepted decisions D50A3H-1 through D50A3H-9 on
2026-09-12 after the focused macOS documentation gate passed all 104 tests in
4.19 seconds. This authorizes the bounded 50A.3I numbered-asteroid CLI
preflight implementation; it does not authorize comet or satellite runtime
behavior.

## 1. Purpose

Wenu can draw or center on any numbered asteroid already represented by a
verified local manifest and bounded Horizons SPK. The scientific and rendering
path is accepted, but the user must currently run an acquisition tool before
the ordinary chart command. Fernando requires the ordinary CLI to resolve a
requested moving object without a separate manual download step.

This audit defines that convenience without moving network, mutable catalog,
or acquisition responsibility into `CelestialSphere.draw_chart()` or any
renderer. One CLI invocation may orchestrate a preflight acquisition and then
perform an ordinary offline render. The resulting chart must remain exactly
reproducible from the frozen resource manifest.

50A.3H changes no runtime behavior. It precedes, but does not redefine, 50A.4
comet numerical validation.

## 2. Evidence from planetarium practice

Sources were reviewed on 2026-09-12.

| Source | Material finding |
| --- | --- |
| [Stellarium `ssystem_minor.ini`](https://github.com/Stellarium/stellarium/blob/master/data/ssystem_minor.ini) | Stellarium distributes asteroid and comet identities, epochs, orbital elements, photometric fields, references, and object classes as compact records and propagates them locally. It does not distribute one sampled ephemeris for every object. |
| [Stellarium Solar System Editor](https://stellarium.org/doc/23.0/classSolarSystemEditor.html) | Its editor imports MPC one-line comet elements into the installed Solar-System record format; data update and sky calculation are separate responsibilities. |
| [SkySafari Solar System help](https://userguide.skysafariastronomy.com/app-specific/settings-help/display-options-help/solar-system-help) | SkySafari periodically downloads MPC asteroid/comet orbit data and CelesTrak satellite data, then uses those local data offline. It explicitly warns that artificial-satellite orbits require frequent refresh. |
| [Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html) and [SBDB API](https://ssd-api.jpl.nasa.gov/doc/sbdb.html) | JPL separates object/solution metadata from generated ephemerides and supports bounded small-body SPK production. Responses and orbit solutions are mutable service results that must be frozen for reproducibility. |
| [MPC documentation](https://docs.minorplanetcenter.net/) | MPC is the designation and observation authority and publishes asteroid/comet orbital data suitable for catalog import. |

The useful practice is a local catalog plus local calculation and controlled
updates. Wenu should adopt that usability pattern, not another program's
accuracy claims or a silent two-body propagator.

## 3. Required separation

One shell command does not imply one architectural phase:

```text
CLI request
    -> parse requested identity, time interval, and data policy
    -> resolve local immutable resource or acquire into a staging area
    -> validate, fingerprint, and atomically publish manifest/resource
    -> construct the ordinary ChartRequest with resolved local resources
    -> run the unchanged offline astronomical and rendering pipeline
```

The preflight resolver may use the network when policy permits. Chart request
generation, state evaluation, direction realization, projection, preparation,
rendering, and export may not. Library callers that bypass the CLI continue to
receive an offline, fail-closed interface.

## 4. Decisions

### D50A3H-1 — One-command acquisition: Adapt

The installed `wenu_chart` CLI may acquire a missing moving-object resource in
a preflight phase and continue the same invocation after successful
validation. This supersedes the 50A.0 requirement that acquisition always be a
separate user operation, but preserves its scientific boundary: no chart or
renderer performs network I/O.

The CLI must state when it acquires data and where the immutable resource was
stored. A failed lookup, ambiguous identity, unavailable service, invalid
response, digest mismatch, or insufficient coverage aborts before chart
construction; none may produce a substitute position.

### D50A3H-2 — Explicit data policy with a convenient default: Adopt

Add a data policy with three values:

- `acquire-if-missing`: use an adequate verified local resource; otherwise
  acquire, validate, store, and use one. This is the interactive CLI default.
- `offline`: prohibit network access and fail with an actionable acquisition
  message if no adequate local resource exists.
- `refresh`: acquire a current provider solution even when an adequate cached
  resource exists, publish it immutably, and use it for this invocation.

The eventual public spelling should be `--data-policy` and the corresponding
TOML value should live under a data/resource section, not under chart geometry
or object content. Environment-dependent network availability is not a hidden
fourth policy.

`acquire-if-missing` does not mean “use the newest solution.” It means “reuse a
verified resource whose identity and requested time coverage are adequate.”
Users requiring a new solution choose `refresh`; reproducible jobs choose
`offline` and retain the manifest.

### D50A3H-3 — Content-addressed immutable cache: Adopt

Acquisition writes to a temporary staging directory, validates the complete
response and SPK, computes digests, and only then publishes an immutable
resource. A small mutable index may point from normalized provider identity to
candidate manifests, but must never overwrite a resource referenced by an
existing manifest.

Concurrent processes must use a per-identity acquisition lock and atomic
publication. An interrupted acquisition leaves no valid index entry. Cache
cleanup is an explicit data-management operation and must not occur during
rendering.

### D50A3H-4 — Identity resolution: Adopt

Resolution retains separate fields for Wenu key, object class, permanent
number, periodic-comet number, primary and provisional designation, official
name, aliases, provider command, SPK ID, and orbit solution. Exact normalized
identifiers may resolve automatically. Fuzzy search may suggest candidates but
must not select one for scientific acquisition.

The resolver checks the local index first. If network policy permits and the
identity is absent, it queries an authoritative identity service, rejects
ambiguity, freezes the response and service/schema version, and only then
requests the ephemeris resource.

### D50A3H-5 — First implementation remains Horizons SPK: Adopt

The smallest implementation after acceptance generalizes the existing
numbered-asteroid acquisition path into a reusable preflight service. It uses
SBDB/Horizons to identify the selected solution and acquire a bounded SPK,
then reuses `MinorBodyResourceCollection` and
`MinorBodyResourceSession`. It does not first introduce a new orbital
integrator.

Default coverage must be derived deterministically from every requested point,
track, sequence, and center epoch plus a documented margin. The acquired
interval and provider solution, not the margin rule alone, remain recorded in
the manifest.

### D50A3H-6 — Broad orbital catalog and propagator: Defer

A compact MPC/SBDB-derived catalog is the scalable route to hundreds of
thousands of offline objects. It requires a separately validated provider
that declares perturbations, reference system, epoch/time scale, integrator,
comet non-gravitational support, accuracy interval, and update provenance.

Until that provider passes asteroid and comet comparisons, Wenu must not use a
Keplerian element calculation as a silent fallback. A future catalog provider
may coexist with Horizons SPKs through the existing typed state-source seam;
provider selection and claimed accuracy must remain visible.

### D50A3H-7 — Comets use the same preflight boundary: Adopt

After 50A.4 validates comet nucleus directions and non-gravitational model
provenance, the same resolver may acquire comet SPKs by exact comet identity.
It must preserve the chosen apparition and orbit solution and must not discard
or reapply provider-modeled non-gravitational terms. Nucleus position remains
separate from coma, tail, photocenter, and visibility.

### D50A3H-8 — Artificial satellites are a separate provider program: Adopt

Artificial satellites may later share identity lookup, data-policy vocabulary,
cache publication, observed-direction collections, clipping, projection, and
rendering. They may not reuse minor-body dynamics. Their provider requires
fresh TLE/OMM data, SGP4/SDP4-compatible propagation, TEME transformations,
Earth orientation and time handling, topocentric observer geometry, status
and decay semantics, and much shorter freshness rules.

CelesTrak or another declared source may populate the local catalog, but
“latest available” is not a reproducibility guarantee. Every satellite chart
must retain the exact element-set epoch, source, retrieval time, digest, and
propagator version. Satellite implementation is not authorized by 50A.3H.

### D50A3H-9 — Reproducibility receipt: Adopt

Every automatically acquired render must be reproducible without network from
its output provenance. At minimum retain:

- normalized object and provider identities;
- solution identifier and source/schema versions;
- retrieval time and exact query parameters;
- requested and actual coverage;
- every local filename and SHA-256 digest;
- dependency ephemeris identity;
- selected data policy and whether acquisition occurred;
- Wenu version and state-provider implementation/version.

The ordinary semantic/output metadata may reference this receipt; it must not
embed a mutable cache path as though that path were scientific identity.

## 5. First implementation slice after acceptance

50A.3I should implement only numbered-asteroid CLI preflight acquisition:

1. introduce the typed `offline`, `acquire-if-missing`, and `refresh` policy;
2. derive required coverage from the resolved center, point, and track epochs;
3. extract the existing acquisition script's reusable network and publication
   logic without importing CLI code into the library;
4. acquire an exact numbered asteroid on cache miss;
5. validate and atomically publish the existing manifest/SPK format;
6. hand the resulting directory to the unchanged request/render lifecycle;
7. keep explicit `--minor-body-resource-directory` authoritative and offline;
8. prove that a warm-cache invocation performs no network access and produces
   the same scientific resource identity as the acquiring invocation.

The implementation must not add comets, an orbital-element propagator,
satellites, fuzzy object selection, background catalog sweeps, magnitude
selection, eviction, GUI progress, or renderer changes.

## 6. Acceptance evidence for 50A.3I

- contract tests for policy parsing and precedence;
- a fake-service acquisition test covering identity, coverage, validation,
  atomic publication, and deterministic failures without real network;
- a warm-cache test that rejects any attempted network call;
- a public CLI composition test showing that a missing numbered asteroid is
  acquired before request construction;
- exact manifest and digest assertions rather than a second numerical orbit
  oracle;
- retained 50A.2/50A.3D numerical, resource, CLI, and full-suite gates;
- one Mac cold-cache chart followed by the same chart in `offline` mode, with
  identical resolved resource identity and accepted visible output.

The closest existing owners are `tests/test_minor_body_resources.py` for
manifest/session behavior and `tests/test_wenu_chart_cli.py` for public CLI
composition. Acquisition transport and atomic cache publication constitute a
new durable boundary only if they cannot be tested clearly by extending those
files; no milestone-named test file is justified.

## 7. Stop conditions

Stop before implementation if the provider cannot resolve an identity
unambiguously, the requested interval cannot be represented by the current SPK
service, redistribution or service terms prohibit the intended cache behavior,
the existing manifest cannot retain the required receipt, or automatic
acquisition would require credentials not ordinarily configured for the CLI.

Stop before claiming general offline coverage until an orbital-catalog
provider has its own scientific audit and numerical validation. Stop before
satellite work until its separate dynamics, time, frame, freshness, and data-
source contract is accepted.

## 8. Documentation review

The coordinate-system guide was reviewed. Its separation of provider-native
state, apparent-place realization, product frame, and satellite TEME/SGP4
physics remains correct. After acceptance it should record the new CLI
preflight versus offline-render boundary. User guides and TOML documentation
must not change until 50A.3I installs behavior.
