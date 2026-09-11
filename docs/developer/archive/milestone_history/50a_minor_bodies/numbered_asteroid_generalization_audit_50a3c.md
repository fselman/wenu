# Numbered-asteroid generalization audit (Milestone 50A.3C)

**Status:** Accepted by Fernando on 2026-09-11

**Base:** `5b4e44f5b730aaf11b8c32330cf51cf327ae779b`

## 1. Question and bounded recommendation

50A.3B proved the complete visible path with one compiled `(1) Ceres`
descriptor and one accepted compiled Horizons solution. That path is not yet a
generic numbered-asteroid interface: the CLI accepts only `ceres`, the built-in
Solar-System catalog owns the only drawable asteroid descriptor, and
`minor_body_resources.py` owns a closed Ceres provider specification.

50A.3C recommends one separately reviewed 50A.3D implementation that makes a
**permanent minor-planet number** the public selection key for an explicitly
installed asteroid resource. `(79989)`, a small unnamed main-belt asteroid
selected by Fernando, is the acceptance specimen. It must exercise the same
generic path as every other supported numbered asteroid; no code may branch on
`79989`.

This audit changes no runtime behavior. Ceres remains the only currently
drawable asteroid until 50A.3D is implemented, numerically accepted, and
visually accepted.

The nomenclature decisions follow the IAU Minor Planet Center's current
[designation documentation](https://docs.minorplanetcenter.net/mpc-ops-docs/designations/)
and [List API contract](https://docs.minorplanetcenter.net/mpc-ops-docs/apis/list/),
which keep permanent number, provisional designation, optional name, object
groups, and dual status distinct. Acquisition continues to use the
[NASA/JPL Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html).

## 2. Identity is not dynamical classification

One positive permanent minor-planet number is unique within the minor-planet
namespace. Main-belt, Apollo, Amor, Aten, Atira, Trojan, Centaur, and
trans-Neptunian labels are classifications, not distinct number spaces. A
number therefore selects identity but does not establish class, provider
target, orbital model, validity, brightness, or suitability for display.

The manifest-backed identity for one numbered asteroid must keep these fields
separate:

- permanent minor-planet number;
- primary provisional designation and any aliases;
- optional proper name;
- stable Wenu entity and selection keys;
- object class and separately sourced classifications;
- exact Horizons command and returned SPK target;
- orbit-solution identifier, date, epoch, reference system, quality evidence,
  provenance, digest, segment identity, and coverage.

The SPK target must be consumed from the provider response and checked against
the manifest. Wenu must not derive it arithmetically from the minor-planet
number. An integer alone must not be accepted as evidence that an object is an
asteroid rather than a cometary or dual-status body.

Comet identifiers remain outside this slice. A periodic-comet number such as
`67P` is not minor planet `(67)`. Dual-status objects require a later explicit
identity policy and must not be admitted accidentally through the numbered-
asteroid route.

## 3. Public selection contract

50A.3D should accept decimal permanent minor-planet numbers through the
existing class-aware options:

```text
--asteroid 79989
--asteroid-track 79989
--minor-body-resource-directory PATH
```

The same route must support `--asteroid 1` and `--asteroid-track 1`. The
existing `ceres` spelling remains a compatibility alias for number `1`; it
must resolve to the same identity rather than create a second Ceres
descriptor.

Parsing accepts only an unsigned positive decimal integer or an explicitly
retained alias. It rejects zero, signs, decimals, empty input, comet forms,
provisional designations, arbitrary names, and comma lists in 50A.3D. A
syntactically valid number is not a promise that its resource is installed.

Rendering remains explicit and offline. If the selected number is absent from
the supplied manifest, Wenu must fail before producing output with an
actionable message. It must not query Horizons, SBDB, MPC, or any other
network service; search a global cache; substitute an osculating-element
propagator; or fall back to Ceres.

## 4. Acquisition and manifest contract

Acquisition remains a tool boundary outside chart generation. The 50A.3D tool
should accept one or more permanent minor-planet numbers, use the unambiguous
terminated Horizons small-body command, and write an explicit collection
manifest plus one bounded SPK per resolved object. It must refuse ambiguous or
non-asteroid results and refuse to overwrite an existing evidence set without
an explicit future replacement policy.

The collection manifest, not a Python module named for each asteroid, becomes
the source for request-owned numbered-asteroid descriptors and
`MinorBodySolutionIdentity` values. Each record must contain structured
identity and solution fields rather than require chart code to rediscover them
by parsing a human-readable Horizons result. The original result text remains
retained as provenance and as a cross-check.

The loader must reject duplicate permanent numbers, aliases that resolve to
different numbers, missing required identity, a class mismatch, an invalid or
unsupported solution, a filename escaping the resource directory, digest
mismatch, target mismatch, unsupported centre/frame/type, and insufficient
coverage. It opens each selected SPK at most once per chart build and closes
every opened resource exactly once.

The accepted 50A.2 directory remains readable for the existing `ceres`
compatibility route. Migration to the structured collection format must be
explicit and tested; existing Ceres commands must not stop working merely
because 50A.3D generalizes selection.

## 5. Request-owned descriptor boundary

The built-in catalog remains the authority for planets, the Moon, and other
packaged bodies. Installed numbered asteroids are request-owned extensions
resolved from the explicit manifest before chart realization. They receive an
ordinary `SolarSystemBodyDescriptor` with `SYMBOLIC_POINT` and
`APPARENT_TRACK` capabilities and `minor_body_spk` as the ephemeris-source
key.

The request must carry the resolved descriptor identity used by point and
track selection. It must not mutate the process-global built-in catalog or a
reusable celestial sphere. Request generation registers only the selected
point and track layers for that request and restores reusable-sphere state
afterward. A point and track for the same number share one descriptor and one
opened provider.

The existing target-source versus observer-source split remains unchanged:
the asteroid SPK supplies the target state; DE440/Skyfield supplies the
observer state and apparent correction. The ordinary astrometric direction,
fixed product frame, projection, preparation, semantic SVG, renderer, and
export paths remain the sole paths.

## 6. Display and semantic identity

Display text follows the accepted number-on-the-right convention:

- named object: `Ceres (1)`;
- unnamed object: `(79989)`.

The optional name must never be synthesized from a number or provisional
designation. The canonical identity retains the permanent number even if a
proper name is assigned later. A resource refresh may add or change display
metadata, but it must not silently change the selected permanent identity.

Semantic paths must be stable and number-based, for example:

```text
sky/solar_system/minor_bodies/asteroids/79989
sky/solar_system/minor_bodies/asteroids/79989/track
```

The hollow diamond, asteroid color, shared track, tick, and start-label rules
accepted in 50A.3B apply without per-object styling. The point and track carry
no magnitude, diameter, detectability, or angular-size claim.

## 7. `(79989)` numerical acceptance specimen

The 50A.3D acquisition evidence must first resolve the permanent number,
primary provisional designation, absence of a proper name, asteroid class,
Horizons command, returned SPK target, and orbit-solution provenance. Those
values must be frozen from the authoritative responses; they are not guessed
in this audit.

At no fewer than three epochs spanning the installed coverage, the existing
50A.2 validator pattern must compare the installed SPK route with frozen
direct-Horizons evidence for:

- Cartesian barycentric position and velocity;
- topocentric and geocentric astrometric right ascension and declination;
- topocentric and geocentric apparent right ascension and declination;
- distance, light time, and topocentric parallax.

The comparison must retain the actual provider solution, planetary ephemeris,
SPK digest and segment identity. Tolerances are adopted only after inspecting
the measured residuals. Existing Ceres and Apophis evidence remains the
independent regression oracle and is not copied into a new lower-level test.

After numerical acceptance, Fernando must inspect one regional PNG and its
semantic SVG containing the `(79989)` point and dated track. This visual check
tests generic identity, label, semantic path, and shared appearance, not
scientific detectability.

## 8. Tests and ownership

50A.3D should extend existing stable owners:

- chart-argument tests protect numeric syntax, the `ceres` alias, and class-
  aware rejection;
- request and resource tests protect manifest-derived descriptor identity,
  duplicate/mismatch failures, offline behavior, lifecycle, and coexistence
  with Ceres;
- existing body, point, track, semantic, and configuration tests protect only
  the new request-owned registration seam;
- the numerical validator owns the new `(79989)` authoritative comparison;
- documentation tests protect the public contract and ownership map.

Do not create a test file merely for 50A.3C or 50A.3D. Do not repeat CSPICE
interpolation, light-time, apparent-place, projection, renderer, or exporter
tests whose inputs and fault models are unchanged. Run focused tests and the
complete suite with ambient pytest plugins disabled.

## 9. User documentation, examples, and diagrams

This audit changes no installed behavior, so no user-guide example or
architecture diagram changes in 50A.3C. The coordinate-system guide is
reviewed: the provider, TDB/ICRF, light-time, apparent-place, and fixed-product-
frame explanations remain current.

50A.3D must replace Ceres-only user wording with the generic numbered-asteroid
contract, document acquisition separately from offline rendering, retain a
Ceres compatibility example, and add the accepted `(79989)` command. The
focused minor-body diagram must show manifest-derived request identity rather
than a compiled Ceres-only specification.

## 10. Deferred work and stop conditions

50A.3D does not admit provisional-only asteroids, names other than retained
aliases, comets, dual-status objects, automatic discovery, catalog sweeps,
field-of-view intersection, exposure-window searches, brightness selection,
photometry, uncertainty envelopes, occultations, or artificial satellites.

Stop and re-audit if implementation would:

- infer identity, class, provider target, solution, name, or validity from the
  integer alone;
- perform network access during chart creation;
- mutate a global catalog or reusable sphere with request-specific bodies;
- add an asteroid-specific direction, projection, preparation, renderer,
  semantic-export, or file-export path;
- weaken the explicit SPK/DE440 resource chain or accepted 50A.2 oracle;
- confuse minor-planet numbers with periodic-comet numbers.

Fernando accepted this audit on 2026-09-11. That acceptance authorizes only the
bounded 50A.3D generic numbered-asteroid implementation and `(79989)`
validation. Comet numerical validation remains 50A.4 after that follow-up
closes.
