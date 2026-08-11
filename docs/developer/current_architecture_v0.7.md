# Wenu current architecture v0.7

**Status:** Implemented baseline for the v0.8 migration
**Baseline commit:** `b72eef8`
**Date:** 2026-08-05

Wenu v0.7 implements independently selectable equatorial, ecliptic, and
Galactic coordinate-grid layers. It does not implement an observer-local
AltAz grid, although horizontal coordinates are already the canonical
spherical geometry used by projection and rendering. The horizon remains
chart-owned boundary geometry and is not optional reference content.

The canonical flow, ownership boundaries, declarative examples, render-local
detail policy, style ownership, and packaged-example parity documented by
`target_architecture_v0.7.md` remain in force.

The permanent test suite is organized by these current responsibilities rather
than by completed milestone history. Fast unit, integration, visual, and full
commands are recorded in `source_tree.md`; the full suite remains the release
authority and atlas print remains the visual reference baseline.

The v0.8 migration now provides one immutable canonical load profile and one
maximal-sphere factory. It loads complete reusable astronomical content for an
observer and returns the existing `CelestialSphere`; chart geometry,
coordinate-grid spacing, detail, presentation, and export remain downstream
request concerns.

Stellar AltAz realization is cached per loaded `Stars` layer using observer
location, instant, ephemeris identity, data directory, catalogue identity,
and source revision. Render-local magnitude and identifier selections mask
that immutable maximal realization, and constellation figures reuse it.
Vectorized point catalogues use the same key identity: open-cluster and
planetary-nebula selections index immutable maximal AltAz center arrays.
Milky Way and Magellanic Cloud level selections likewise index immutable
maximal observed ring arrays. Official constellation boundaries cache their
complete sampled B1875 realization; the native source revision and sampling
step are part of the cache identity, while the requested constellation set
remains render-local.
Extended-object layers cache complete observed outline catalogues at each
requested geometry quality. Sample count and minimum displayed angular size
belong to the cache identity; magnitude and identifier subsets are applied
afterward. Galaxies, Messier-style objects, globular clusters, and supernova
remnants share this policy through `NonStellar`.

Milestone 46C.7A adds an immutable public chart-request graph. It separates
the scientific observer and instant, subject identity, optional framing,
content, detail, furniture, product, language, title, and output. It is a
declarative contract only: resolution and generation continue to be added
incrementally over the canonical sphere and chart pipeline.

Milestone 46C.7B adds an offline packaged target cross-identification
resolver. A resolved target preserves its display identity and ICRS center
while separately naming every catalogue family and identifier required to
draw it. Unknown and ambiguous aliases raise explicit user-facing errors;
explicit coordinates retain user provenance and need no packaged component.

Milestone 46C.7C adds the corresponding offline constellation-subject
resolver. It accepts arbitrary IAU abbreviation sets and packaged teaching
groups, and resolves their public region identities into the distinct line,
boundary, and label identifiers required internally. In particular, a public
`Ser` request consistently expands to `Ser1`/`Ser2` figures and
`SerCap`/`SerCau` labels while retaining one official boundary identity.
Teaching-group framing and curated legacy-example content are packaged data,
not example-script globals.

Milestone 46C.7D adds one request-resolution boundary before construction.
It resolves targets or constellation subjects, unions the central target and
packaged group content into an immutable render-local selection, and rejects
detail ceilings that exceed the chosen maximal-sphere load profile. The
original request remains unchanged; no chart, renderer, or export work occurs
in this phase.
