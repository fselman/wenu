# Mercury disk-sequence generalization audit — Milestone 49I.3C.3.3

**Status:** Scientifically and architecturally accepted

**Audit date:** 2026-09-01

**Acceptance date:** 2026-09-01

**As-is baseline:** `3a713fb`

## 1. Purpose

This audit defines the smallest scientifically independent path from the
accepted frozen-Earth Venus sequence to Mercury. It changes no runtime type,
constant, public command, geometry, style, chart, renderer, or output.

The intended first Mercury product is the same kind of constructed diagram as
49I.3C.3.2B: Earth's heliocentric position is frozen at the sequence start,
Mercury advances at exact major epochs, and the fixed Sun and resolved Mercury
disks are expressed in fixed J2000 mean-ecliptic axes. It is not apparent sky.

Venus success supplies an architecture, not Mercury evidence. Mercury requires
its own body identity, radius authority, provider evidence, installed-kernel
comparison, sampling decision, phase/orientation checks, semantic identity, and
visual acceptance.

## 2. As-is findings

The following accepted owners are already body-neutral after a request exists:

- `FrozenEarthDiskSequenceRequest` and
  `FrozenEarthDiskSequenceRealizer.sequence()` accept a typed point descriptor,
  display name, physical radius, and radius model;
- `SolarSystemDiskGeometryRealizer` consumes the resulting disk-state protocol
  rather than requiring Venus;
- fixed product-frame transformation, projection, per-centre magnification,
  renderer, and PNG/PDF/SVG export contain no Mercury-specific science.

The visible path is not yet body-neutral:

- `chart_disk_sequence_options()` always installs `VENUS_POINT`,
  `VENUS_MEAN_RADIUS_KM`, and `VENUS_RADIUS_MODEL`;
- the CLI permits only `--planet-disk-sequence venus`;
- drawable realization, layer names, style lookup, cleanup, and semantic paths
  are Venus-named;
- both drawable sequence display requests reject every target except Venus;
- no deterministic or installed-DE440 Mercury evidence exists.

Therefore Mercury must not be enabled by widening one CLI `choices` tuple.

## 3. Mercury body identity and radius

The physical body identity is Mercury, NAIF body code `199`. The accepted
proposed spherical radius is the JPL Solar System Dynamics mean radius
`2439.4 km` with quoted uncertainty `0.1 km`: the radius of an equal-volume
sphere. The separate JPL equatorial radius `2440.53 km` must not be substituted
silently.

Authorities:

- [JPL Planetary Physical Parameters](https://ssd.jpl.nasa.gov/planets/phys_par.html)
  for mean/equatorial radius values, definitions, and the cited IAU/IAG 2015
  cartographic-elements report;
- [NAIF integer ID codes](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/naif_ids.html)
  for Mercury body code `199` and the body-versus-barycentre distinction.

Mercury and its barycentre coincide because Mercury has no satellite, but NAIF
explicitly warns that body and barycentre identifiers are not interchangeable.
The physical radius belongs to body `199`. The DE440 SPK adapter may resolve a
state through Mercury barycentre code `1` or body code `199`, depending on the
installed kernel's segment/name mapping; validation must record the actual
`provider_target_id` and explain its role instead of rewriting it as the
physical-body identifier.

## 4. Bounded implementation sequence

### 49I.3C.3.3A — Output-neutral Mercury state and numerical validation

Add one Mercury point descriptor and the accepted mean-radius constant/model.
Construct a frozen-Earth Mercury request through the existing generic sequence
realizer. Add no CLI choice, drawable layer, style, semantic output, or chart.

An installed-DE440 validator must refuse to download a missing kernel and must
compare Wenu against an independent direct-Skyfield calculation at every exact
sample. It must record:

- model, filename, SHA-256, coverage, and actual provider target/centre IDs;
- the one frozen Earth heliocentric ICRF vector;
- every same-epoch Mercury heliocentric ICRF vector;
- frozen-Earth-to-Mercury vector, distance, fixed-ecliptic longitude/latitude,
  angular diameter, phase angle, illuminated fraction, and bright-limb angle;
- fixed Sun direction and sequence identity;
- maximum residuals and explicit tolerances.

The validator must use the same accepted equations as the Venus frozen model
but independent direct vectors and the Mercury radius. It must include samples
on both sides of at least one conjunction-like thin-phase geometry and samples
spanning materially different Mercury-Sun and frozen-Earth-Mercury distances.
Undefined exact alignment is an explicit diagnostic, not a value to suppress.

### 49I.3C.3.3B — Drawable frozen-Earth Mercury sequence

Only after 49I.3C.3.3A scientific acceptance, extract or generalize the
Venus-named drawable orchestration so one body descriptor supplies target,
display name, physical radius, radius model, semantic root, and style identity.
Do not copy the Venus projection, preparation, renderer, or export path.

Enable `--planet-disk-sequence mercury` only for
`--disk-sequence-model frozen-earth-ecliptic` in this slice. Preserve the
restricted scene, fixed Sun, product-frame ecliptic, optional fixed-frame
equatorial grid, exact start-inclusive cadence, one common Mercury
magnification, and optional date labels.

Mercury semantic components must be rooted at
`sky/solar_system/planets/mercury/frozen_earth_sequence`. Venus paths and
existing Venus output must remain unchanged. The title and labels require
English and Spanish review; no literal Venus title may survive a Mercury
request.

## 5. Required deterministic contracts

The first runtime slice must prove:

- the Mercury descriptor has stable target, selection, display, and entity
  identity independent of Venus;
- the adopted radius is positive, immutable, source-labeled, and not the
  equatorial radius;
- generic frozen sequence state retains Mercury target identity through every
  direction, appearance, geometry, distance, and provenance record;
- the physical angular diameter changes only with the retained physical
  distance and radius;
- geometric status, origin `frozen-earth`, unit `au`, exact instant, and fixed
  J2000 mean-ecliptic axes remain explicit;
- existing Venus sequence tests remain unchanged and green.

The drawable slice must additionally prove request conflict rejection,
Mercury-only semantic paths, independent component styles, per-centre
magnification, fixed-Sun non-magnification, PNG/PDF/SVG parity, localized
titles, and rejection of forbidden scene content.

## 6. Human visual acceptance

Before 49I.3C.3.3B can close, Fernando must inspect a calibration spanning
enough exact epochs to show Mercury's faster orbital motion, varying distance,
angular size, phase, and bright-limb orientation. The final cadence,
magnification, field, and label policy are selected after 49I.3C.3.3A reports
the numerical sequence; this audit does not pre-accept them.

Visual review must compare Venus and Mercury hierarchy without requiring them
in the same chart. It must confirm that the construction is clearly labelled
as frozen-Earth geometry, the fixed Sun dominates appropriately, thin phases
remain legible, grids retain their scientific meaning, and no disk is clipped
or mistaken for a symbolic magnitude marker.

## 7. Explicit non-goals

49I.3C.3.3 does not authorize observed/topocentric Mercury sequences, one
resolved Mercury disk, symbolic Mercury, Mercury tracks, photometric magnitude,
surface markings, rotational orientation, multiple planets in one request,
adaptive cadence, animation, planisphere/all-sky output, physical solar disks,
or a 3D visualizer.

The coordinate-system guide was reviewed for this audit. Section 13.2.31 adds
the Mercury identity, barycentre, radius, and validation distinction; no
implemented coordinate transformation changes.

## 8. Stop conditions

Stop and re-audit if implementation would:

- treat the JPL equatorial radius as the accepted mean spherical radius;
- claim provider target ID `1` is NAIF physical-body ID `199`;
- reuse Venus constants, display names, semantic roots, or literal titles;
- pass frozen geometric states through the apparent-direction chain;
- duplicate disk geometry, projection, magnification, renderer, or exporter;
- enable observed Mercury without its own topocentric numerical validation;
- discard full vectors, distances, exact instants, or provenance;
- select numerical tolerances from desired test outcomes rather than the
  independent comparison.

## 9. Acceptance

Fernando scientifically and architecturally accepted the two-slice boundary,
JPL equal-volume mean-radius authority, physical-body versus provider-
barycentre identity distinction, frozen-only first drawable scope, and
explicit non-goals on 2026-09-01. Merging this audit authorizes only separately
reviewed 49I.3C.3.3A work; it does not pre-accept Mercury runtime values,
tolerances, public output, or visual design.

Audit preparation verification passed all 68 current-documentation tests.
