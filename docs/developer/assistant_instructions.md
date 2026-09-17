# AI Assistant Instructions for Wenu

This document defines the expected behavior of AI assistants contributing to
Wenu. Its purpose is to preserve architectural consistency and make every
change incremental, reviewable, reproducible, and safe to apply.

## Project purpose

Wenu is a Python library for accurate, reproducible, publication-quality
static sky charts for observing guides, books, articles, education, outreach,
and guided observation. It is not an interactive planetarium.

Prioritize astronomical correctness, clarity, simplicity, maintainability,
reproducibility, and publication-quality rendering over speculative
flexibility or real-time performance.

## Source of truth

The Git repository is always the source of truth. Never reconstruct files from
memory or previous conversations. Before proposing a modification:

1. inspect the active branch, current commit, and working tree;
2. read the current implementation and relevant tests;
3. read the active architecture and migration documents;
4. make only the smallest change required by the current milestone.

Previous conversations may explain intent but do not override the repository.

## Architectural authority

For current work, read and follow:

- `README.md` as the active developer-document index and top-level placement policy;

- `current_architecture_v0.9.md` as the implemented architecture authority;
- `post_v0.9_architecture_roadmap.md` as the active milestone roadmap;
- `archive/architecture_history/target_architecture_v0.9.md` and `archive/migration_history/wenu_migration_0.8_to_0.9.md` only as
  accepted design and completed-migration evidence;
- `implementation_reference.md` as the current API reference;
- `source_tree.md` as the current responsibility map;
- `diagrams/README.md` and its current SVGs as the human inspection view of
  ownership, process flow, and architectural change seams;
- `target_architecture_v0.9.5.md` and
  `coordinate_system_guide_v0.9.5.md` for proposed 49B/49C coordinate,
  provider, frame, time, provenance, planet, or satellite work;
- `archive/audits/coordinate_transformation_audit_09a2afd.md` for the as-is coordinate
  evidence that motivates that target;
- `archive/audits/public_interface_audit_v0.9.5.md` for public examples, tools, coordinate
  system, frame, equinox, or epoch interface work;
- `archive/milestone_history/49d_scene/celestial_scene_dependency_audit_49d1.md` for celestial-background,
  moving-object, observer-local, product-frame, planet, Moon, or scene-reuse
  dependency work;
- `archive/milestone_history/49d_scene/layer_realization_context_49d2.md` for the optional pre-projection layer
  context, compatibility dispatch, or controlled-provider integration point;
- `archive/milestone_history/49e_ephemeris/ephemeris_provider_contract_49e1.md` for ephemeris state, target/centre,
  kernel provenance, apparent-place corrections, or Sun/Moon/planet provider
  boundary work;
- `archive/milestone_history/49e_ephemeris/ephemeris_runtime_contracts_49e2.md` for the frozen ephemeris resource,
  state request, six-component state, structural source, or `TOPOCENTRIC`
  removal work;
- `archive/milestone_history/49e_ephemeris/solar_system_direction_realizer_49e4.md` and
  `archive/milestone_history/49e_ephemeris/astrometric_direction_runtime_49e5.md` for observer state, retarded emission
  time, light-time iteration, astrometric direction, or Venus-first runtime
  work;
- `archive/milestone_history/49i_solar_system/venus_vertical_slice_audit_49i1.md` for the first drawable Venus,
  ordinary realization-context handoff, planet semantic identity, or
  `--planet venus` work;
- `archive/milestone_history/49i_solar_system/ordinary_realization_context_49i1a.md` for the implemented ordinary
  request-to-layer context mapping and its output-neutral acceptance;
- `archive/milestone_history/49i_solar_system/venus_layer_49i1b.md` for the first production Venus layer, opt-in planet
  selection, symbolic appearance, semantic identity, or visual acceptance;
- `archive/milestone_history/49i_solar_system/shared_solar_system_point_layer_49i2b.md` for the shared symbolic-point
  descriptor, renderer-neutral orchestration, or Venus migration boundary;
- `archive/milestone_history/49i_solar_system/moon_layer_49i2c.md` for the first production Moon point, shared internal
  Solar-System selection, natural-satellite semantics, or visual review;
- `archive/milestone_history/49i_solar_system/solar_system_track_audit_49i2d.md` for Solar-System trajectories,
  per-sample time provenance, fixed chart-frame tracks, or projected ticks;
- `archive/milestone_history/49i_solar_system/solar_system_track_curve_49i2d1.md` for sampled track contracts, scalar
  direction evidence, exact tick anchors, or fixed-frame curve realization;
- `archive/milestone_history/49i_solar_system/drawable_venus_track_49i2d2.md` for the visible Venus track request,
  projected perpendicular ticks, two-pass date placement, style, semantic
  identity, or visual acceptance;
- `archive/milestone_history/49i_solar_system/physical_apparent_disk_audit_49i3a.md` for symbolic-versus-resolved
  Solar-System appearance, angular diameter, phase, limb orientation,
  photometry, or object-specific display magnification;
- `archive/milestone_history/49i_solar_system/venus_physical_appearance_49i3b.md` for the accepted Venus radius,
  angular-diameter, phase, illuminated-fraction, bright-limb convention,
  numerical tolerances, or output-neutral physical-appearance state;
- `satchecker_provider_contract_audit_50s2a.md` for the accepted SatChecker
  endpoint, UTC-to-UT1, coordinate, candidate-envelope, async, exact-cache,
  failure, and response-data redistribution boundary;
- `satellite_report_drawing_audit_50s3a.md` for the accepted sampled-candidate
  report, drawing, semantic-identity, shared-backend, and no-exact-crossing
  boundary;
- `satellite_snapshot_propagation_audit_50s4a.md` for the accepted direct
  `sgp4>=2.25,<3` dependency, synthetic snapshot, geometric TEME, no-download
  topocentric-validation, and propagated-specimen boundary. In 50S.4B keep
  records immutable and fail closed, load only digest-verified installed
  synthetic resources, preserve full NORAD identifiers, and add no
  propagation or transformation. Fernando accepted 50S.4B on 2026-09-15;
  only the bounded 50S.4D Earth-orientation and topocentric state chain is authorized next.
  In that wrapper use explicit WGS-72, split Julian dates, typed geocentric
  geometric TEME state, complete status/provenance, and pinned Vallado
  near-Earth/deep-space vectors; add no terrestrial or observer transform;
- `post_v0.9_architecture_roadmap.md` for active coordinate, SVG,
  temporal-sequence, animation, planet, or satellite direction;
- `archive/milestone_history/49f_svg/svg_output_audit_and_plan.md` for SVG product, font, verification,
  constellation-artwork, or 2D/3D-boundary work.
- `archive/milestone_history/49j_performance/test_architecture_and_accepted_practice_audit_49j1.md`
  for accepted fixture, marker, duplication, timing, and Mac-measurement
  evidence;
- `archive/milestone_history/49j_performance/test_practice_decisions_49j2.md`
  for the accepted test policy;
- `archive/milestone_history/49j_performance/marker_truthfulness_49j3b.md` for
  the completed marker-semantics audit and gate-membership correction;
- `archive/milestone_history/49j_performance/repository_source_index_49j3c.md`
  for the completed immutable repository-source inventory work;
- `archive/milestone_history/49j_performance/immutable_catalogue_fixture_49j3d.md`
  for the accepted immutable catalogue-summary fixture and canonical-sphere
  rejection boundary;
- `archive/milestone_history/49j_performance/cold_builder_kernel_oracles_49j3e.md`
  for the accepted cold-builder and installed-kernel oracle decision;
- `archive/milestone_history/49j_performance/calendar_layout_cost_49j3f.md`
  for the accepted calendar text-extent optimization;
- `archive/milestone_history/49j_performance/observer_time_sequence_oracle_49j3g.md`
  for the accepted cold canonical observer-time sequence decision;
- `archive/milestone_history/49j_performance/test_suite_optimization_closure_49j3h.md` for the accepted 49J.3 fault-model,
  repeated-measurement, and test-file-growth closure;
- `archive/milestone_history/49j_performance/fixed_sky_reuse_equivalence_49j5b.md`
  for the accepted exact comparison of the loaded-sphere route with the
  retained cold oracle;
- `archive/milestone_history/49j_performance/loaded_sphere_reuse_49j5a.md`
  for the accepted explicit cold-versus-loaded-sphere fixed-sky sequence seam
  and its observer lifecycle boundaries;
- `archive/milestone_history/49j_performance/performance_closure_49j6.md`
  for the accepted 49J closure evidence and transition to 50A.0;
- `archive/milestone_history/50a_minor_bodies/minor_body_scientific_provider_audit_50a0.md`
  for accepted asteroid/comet state-source, resource-chain, validity,
  uncertainty, identifier, photometry, and non-gravitational-model decisions;
- `archive/milestone_history/50a_minor_bodies/first_drawable_comet_audit_50a5a.md` for accepted 2P/Encke identity,
  explicit resource, symbolic nucleus, shared point/track, and coma/tail
  separation decisions;
- `archive/milestone_history/50a_minor_bodies/solar_system_temporal_components_audit_50a5b1.md` before changing temporal
  path, tick, symbol, label, or observed-phase component reuse;
- `archive/milestone_history/49j_performance/test_entry_and_admission_49j3a.md`
  for the completed reproducible test-entry and new-test admission
  implementation.

Documents under `docs/developer/archive/` are historical evidence, not active
architectural authority. Do not read them routinely. Consult them only when a
task requires provenance, old compatibility reasoning, or migration history.

Wenu has one canonical flow:

```text
catalogues and sky layers
    -> spherical geometry
    -> projection-domain guard
    -> projection
    -> projected geometry
    -> chart preparation
    -> renderer
    -> chart furniture and export
```

Do not create parallel sky, geometry, projection, clipping, rendering, legend,
or export pipelines. Extend the existing architecture rather than replacing
it. `CelestialSphere.draw_chart()` remains the canonical execution core.

Animation may orchestrate repeated canonical static renders and later reuse
scientifically invariant state through an approved temporal contract. It must
not introduce a second astronomical or rendering pipeline. Output formats are
export/backend concerns and must not change astronomical geometry.

## Independent chart concerns

Keep these responsibilities separate:

- chart type owns projection, framing, viewport, and final boundary;
- chart style owns appearance;
- output mode adapts appearance and output scale;
- detail policy owns astronomical selection and density;
- legend policy owns chart furniture.

Styles and modes must not change geometry. Rendering one composition must not
leak mutable selection or style state into a later render of the same sky.

Atlas print is the golden visual baseline. Preserve it unless an approved
milestone explicitly changes it. The old cartoon-specific orchestration is
deprecated but remains available until canonical replacement parity exists.

## Development workflow

Work in small, independently testable milestones. Each change must:

- compile;
- preserve existing public APIs unless the roadmap explicitly changes them;
- pass the focused gate that covers every changed responsibility and immediate
  seam, plus the full suite at the milestone handoff defined below;
- leave the project usable;
- avoid unrelated refactoring, cleanup, or formatting.

### Layered post-change verification

During implementation, run the smallest focused gate that covers every changed
responsibility and its immediate architectural, scientific, provider, or public
seams. Do not repeatedly run unrelated tests merely because they exist in the
repository. A documentation-only edit normally reruns the affected
documentation contract and integrity checks; a domain edit reruns its owning
tests plus directly affected shared-boundary tests.

Run the complete plugin-disabled suite:

- once before presenting a bounded implementation milestone for acceptance;
- after a material cross-cutting change whose effects cannot be bounded by the
  focused gates;
- before merging a milestone branch into its integration branch; and
- before merging the integration branch into `main`.

A previously passing full suite remains valid across a later documentation-only
edit only when the documentation gate and repository-integrity checks pass and
no executable code, scientific fixture, dependency, configuration, packaging,
or non-documentation test collection changed. Record the exact commit or
remote tree covered by every focused and full-suite result; never attach an
earlier result ambiguously to later production content.

Create domain markers or focused test files only when they describe an
enduring responsibility and their membership is complete and truthful. Do not
create a marker or empty future test file merely to name a branch or milestone.
Shared tests may need to be named explicitly when they protect multiple domains
and therefore do not belong exclusively to one marker.

Every medium or major milestone must review
`coordinate_system_guide_v0.9.5.md`. Update it when scientific meaning,
implementation ownership, object provenance, or the public coordinate
explanation changes; otherwise record that it was reviewed and remains
current. Automated documentation checks do not replace Fernando's scientific
and pedagogical review.

Before adding a test, answer:

1. What new contract, boundary, or fault does it protect?
2. Which existing test is closest, and why is extension or parametrization
   insufficient?
3. Does the capability change lower-level behavior, or merely compose behavior
   already tested?
4. Can the assertion inspect an existing immutable artifact without obscuring
   ownership or independence?
5. Which marker and gate describe the work actually performed?

A capability that merely composes already-tested functions does not repeat all
lower-level tests. Add evidence for the new seam, composition, boundary,
provenance, state-isolation obligation, or newly possible failure. Repeat a
lower-level or complete path only when the context changes its inputs,
invariants, tolerance, ownership, failure modes, public route, scientific
oracle, cold-state obligation, or order-independence contract.

### Test-file placement and growth

Add a test to the existing file that owns the closest stable product
responsibility, architectural boundary, public route, or scientific oracle.
Do not create a test file merely for a milestone, pull request, bug, method, or
individual scientific example. Milestone history belongs in its developer
record; tests remain organized by current architecture.

Create a new test file only when it will own at least one durable distinction:

- a new component or module with its own responsibility;
- a new architectural boundary or independently supported public route;
- a distinct scientific oracle or state-isolation obligation; or
- materially different environmental, resource, marker, or gate requirements.

Before creating the file, record the closest existing test file, why extending
or parametrizing it would obscure ownership or independence, and the stable
responsibility named by the new file. Prefer extending an existing immutable
artifact when setup, oracle, tier, and failure meaning agree. Keep tests
separate when their public routes, scientific recomputation, mutable state,
cold-state obligations, or order/isolation fault models differ.

Name test files for enduring responsibilities, such as
`test_chart_sequence.py`, never for chronological milestone identifiers. If a
file becomes unwieldy, split it by stable internal responsibilities rather than
by age or implementation history. At every major closure, review test-file
count, new files added, complete-route duplication, and whether superseded
historical phrase checks can move to bounded archive-integrity coverage. Do not
reorganize existing tests solely to reduce the number of files.

### Documentation-contract preflight

Before presenting any documentation change, inspect every existing
documentation test affected by added, removed, renamed, moved, or reworded
files.

1. If a file is added to or removed from `docs/developer/`, update and verify
   the exact top-level-file allowlist.
2. If established acceptance wording is changed, search for every exact-phrase
   assertion before committing.
3. Never write a documentation assertion from memory. Copy its exact phrase
   from the final document, then verify after whitespace normalization that the
   resulting document contains the asserted text.
4. Treat the developer-document index, resulting filesystem set, roadmap
   links, relative Markdown links, and archive paths as one consistency unit.
5. Inspect the resulting branch contents—not only the intended replacement—to
   verify that every required edit actually applied.
6. Do not present the branch for Mac testing until this static
   documentation-contract preflight is complete.

### Source-tree alignment and production-module admission

Before adding or relocating a production module, identify its durable
architectural responsibility, closest existing owner, dependency direction,
lifecycle, provenance, and failure modes.

- Extend an existing module when the new behavior has the same responsibility,
  dependencies, lifecycle, and reason to change.
- Create a new module when the behavior introduces a distinct scientific or
  provider responsibility, provenance contract, failure boundary, or
  independently testable lifecycle.
- Create a subpackage when a coherent domain requires several collaborating
  modules with a stable boundary. Do not create one merely for a milestone or
  first implementation.
- Organize production code by enduring responsibility, not milestone number,
  CLI option, first specimen, or chronological development history.
- A body-specific module is appropriate only for immutable registration data
  or genuinely body-specific science, never for copied orchestration,
  projection, rendering, or export.
- Do not place domain behavior in `utils`. File size alone neither requires
  nor justifies splitting a module.
- Keep package `__init__.py` files focused on intentional public or
  compatibility exports; adding an internal module does not by itself justify
  another top-level export.
- Before handoff, verify package-boundary tests and update `source_tree.md`
  whenever ownership or placement changes.
- Keep structural reorganization separate from behavioral implementation
  unless the accepted milestone explicitly requires both.

Every new production file proposal must name the closest existing owner and
explain why extending it would mix responsibilities or violate a dependency,
lifecycle, provenance, failure, or testing boundary.

Run Wenu tests with ambient pytest plugins disabled:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest
```

Any required plugin must be explicitly loaded, version constrained,
documented, and accepted before it becomes part of a Wenu gate.

For visual milestones, compare the mandatory regression charts named in the
active migration roadmap. Do not accept an unexplained regression.

Ordinary examples should express chart requests. They must not implement
projection, clipping, renderer dispatch, catalogue joins, legend assembly, or
repeated final saving.

## Scope and files

Modify only files required for the requested milestone. Preserve existing
coding style. Never place backup directories, generated ZIP files, temporary
scripts, intermediate data, or exported charts inside the repository. Put
temporary and patch-handoff files outside it.

Do not generate unrelated documentation, notebooks, screenshots, examples, or
test data unless the milestone requires them.

## Git and delivery workflow

The normal Wenu workflow has four broad stages:

1. Fernando and the assistant discuss and agree on the work, scope, non-goals,
   delivery mode, and acceptance criteria.
2. The assistant performs the agreed work on a dedicated GitHub branch,
   verifies it, commits it, and opens or updates a pull request.
3. After the GitHub state is approved and merged, the assistant guides Fernando
   through synchronizing the Wenu repository on his Mac.
4. Fernando runs the relevant local tests and performs the scientific, visual,
   print, or classroom inspection that requires human judgment.

### Before remote work

GitHub is authoritative for shared committed history, but Fernando's local
working tree may contain uncommitted work that a remote assistant cannot see.
Before creating or updating a remote task branch, establish the exact base
commit and ask Fernando to confirm that his Mac working tree is clean and
synchronized with that base. If it is not, stop and resolve the local state
before writing remotely.

### Direct GitHub delivery

Direct GitHub delivery is the preferred mode when the connector is available.

Once Fernando approves a bounded milestone, that approval authorizes the
assistant to create or update its dedicated branch, make the agreed changes,
run available verification, commit the verified result to that branch, and
open or update a pull request. Stay within the agreed scope and report any
material choice that requires renewed approval.

Do not merge a pull request, delete a branch, force-push, rewrite history, or
commit directly to `main` without a separate explicit request. A direct
`main` commit is reserved for a narrow, well-understood change that Fernando
specifically asks to apply that way.

Before presenting the pull request, inspect the changed filenames, diff stat,
whitespace, substantive diff, and available focused and full test results.
Record the exact base and head commits, remaining uncertainty, and acceptance
work that must occur on the Mac.

### Mac synchronization and acceptance

After a pull request is approved and merged, guide Fernando one command group at
a time. Normally verify a clean local tree, switch to `main`, and fast-forward
from GitHub:

```bash
git status
git switch main
git pull --ff-only
git status
git log -1 --oneline
```

Interpret the output before proceeding. Then provide the exact focused tests,
full tests, rendering commands, or visual inspection procedure required for the
milestone. Do not treat remote automated checks as a substitute for Fernando's
scientific or visual acceptance.

### ZIP patch fallback

Use the Finder-safe Mac ZIP handoff only when direct GitHub delivery is
unavailable or Fernando specifically requests a patch. The ZIP must contain one
same-named folder with exactly:

- `README.md`;
- one `.patch` file.

The README must identify the exact base commit and guide Fernando through:
clean-state verification; separate `git apply --check` and `git apply`
commands; relevant compilation; focused and full tests; diff and whitespace
inspection; explicit staging; cached-diff inspection; commit, push, and clean
closure.

Place temporary and handoff files outside the repository. Use
`$HOME/Downloads/<folder>/<patch>.patch`, and always provide the complete
macOS path beginning with `/Users/fselman/Downloads/`.

## Scientific and rendering standards

Astronomical correctness takes precedence over appearance. Visual
simplifications are acceptable only when they do not introduce conceptual
errors. Preserve coordinate transformations, projection-domain clipping,
chart preparation, viewport clipping, catalogue provenance, and semantic
metadata.

For Solar-System directions, preserve the explicit astrometric-to-apparent
handoff. Apparent correction must consume the accepted astrometric result and
must not silently invoke a second light-time solution. Treat apparent status,
position reference epoch, equinox, and observation instant as separate
concepts in code and documentation.

Planets, the Moon, minor bodies, and comets must converge on one typed
pre-projection and output pipeline. Allow interchangeable state providers and
body-specific physical geometry; never copy the Venus chart path into
body-specific projection, renderer, or exporter implementations.

For the Moon, do not infer correction-policy validity from Venus. Require an
installed-kernel comparison with direct Skyfield and explicit topocentric
parallax evidence before installing Moon chart content.

When several rendering solutions work, choose the simplest one that preserves
the established visual hierarchy and scientific meaning.

## Communication

Before an architectural change, explain its reasoning, tradeoffs, and expected
benefit. If the implementation does not clearly support a requested change,
inspect further and ask for clarification when the choice would materially
alter the result. Never guess.


For resolved Solar-System disks, consult
`archive/milestone_history/49i_solar_system/resolved_venus_disk_audit_49i3c.md` after the accepted 49I.3A and 49I.3B
contracts. Keep physical angular diameter immutable, sample illuminated face, limb, and
terminator as ordinary physical pre-projection semantic geometry, and apply
object-specific display magnification only after projection around the
projected physical centre. Multi-epoch disks must use independent appearance
states in one fixed chart frame. Do not use a large scatter marker or a
format-specific geometry path.


For 49I.3C.1 physical disk geometry, consult
`archive/milestone_history/49i_solar_system/venus_disk_spherical_geometry_49i3c1.md`. Preserve the 720-sample
renderer-neutral centre, limb, visible terminator, and illuminated-face
contract. Do not move post-projection magnification, chart selection, style,
or rendering policy into `solar_system_disk_geometry.py`.


For 49I.3C.2 drawable Venus disks, consult
`archive/milestone_history/49i_solar_system/drawable_venus_disk_49i3c2.md`. Preserve explicit resolved selection,
object-specific post-projection magnification about the exact projected
physical centre, independent illuminated/limb/terminator semantics, and
regional/binocular scope. Keep symbolic Venus as the default and keep
multi-epoch disk display in 49I.3C.3.


For multi-epoch resolved planet disks, consult
`archive/milestone_history/49i_solar_system/planet_disk_sequence_audit_49i3c3.md`. Keep observed topocentric sequences
scientifically distinct from frozen-Earth ecliptic constructions. Both may
share typed sequence, disk geometry, projection, preparation, renderer, and
export owners only after their different direction and appearance states are
resolved. Never label a frozen-observer geometric direction as apparent sky.


For the output-neutral observed Venus disk sequence, consult
`archive/milestone_history/49i_solar_system/observed_venus_disk_sequence_49i3c31a.md`. Preserve exact start-inclusive
major instants, independent topocentric observer and physical-appearance
realization at every epoch, and explicit observer/AU distances. Do not combine
native per-epoch geometry under a false common coordinate instant.


For the drawable observed Venus sequence, consult
`archive/milestone_history/49i_solar_system/drawable_observed_venus_sequence_49i3c31b.md`. Transform every physical
epoch independently into one fixed product frame before aggregation, preserve
observer/AU distance evidence, and magnify each projected disk only around its
own separately projected centre. Keep frozen-Earth mode and Mercury outside
this accepted slice.


For the output-neutral frozen-Earth Venus sequence, consult
`archive/milestone_history/49i_solar_system/frozen_earth_venus_sequence_49i3c32a.md`. Preserve the one start-time Earth
heliocentric vector, same-epoch planet heliocentric vectors, complete retained
ICRF evidence, frozen-earth/AU distances, geometric status, and fixed J2000
mean-ecliptic axes. Never pass this state through the apparent-direction chain.
Keep public request, Sun glyph, restricted scene, and visible output in
49I.3C.3.2B.


For the drawable frozen-Earth Venus sequence, consult
`archive/milestone_history/49i_solar_system/drawable_frozen_earth_venus_sequence_49i3c32b.md`. Preserve frozen-Earth
public request integration, restricted regional content, fixed Sun,
per-centre magnification, localized title, and product-frame
ecliptic/equatorial references. Never introduce an observer AltAz intermediate
into fixed-frame reference geometry. Keep Mercury in the independently
validated 49I.3C.3.3 milestone.


For Mercury disk-sequence work, consult
`archive/milestone_history/49i_solar_system/mercury_disk_sequence_audit_49i3c33.md`. Preserve the distinction between
NAIF physical body `199` and a kernel-resolved Mercury barycentre, use the
separately sourced mean spherical radius, validate output-neutral frozen-Earth
state before drawable integration, and generalize the Venus orchestration
without copying its projection, preparation, renderer, or exporter. Do not
enable observed Mercury, symbolic Mercury, tracks, single disks, photometry,
rotation, multiple bodies, animation, or 3D behavior under this milestone.

For drawable frozen-Earth Mercury, also consult
`archive/milestone_history/49i_solar_system/drawable_frozen_earth_mercury_sequence_49i3c33c.md`. Keep public exposure
capability-driven, reject observed Mercury, derive localized body text and
semantic identity from its descriptor, and reuse the shared fixed-Earth
layers, projection, preparation, style, renderer, and exporters.

Before registering another moving body, consult
`archive/milestone_history/49i_solar_system/moving_body_architecture_49i3c33a.md`. Add identity, relationships, physical
metadata, and capabilities through the body catalog. Do not add a body-specific
point, disk, sequence, projection, renderer, or exporter when the generic
moving-body machinery applies. Classification is metadata; capability and the
validated scientific model govern behavior.

For ordinary apparent major planets, consult
`archive/milestone_history/49i_solar_system/apparent_major_planets_49i3d1.md`. Register data and symbolic-point capability
through the catalog; preserve provider barycentre IDs separately from physical
planet IDs; reuse the shared apparent point layer; and do not infer resolved
disk, photometry, rings, track, or sequence capabilities from classification.


For resolved Moon work, consult `archive/milestone_history/49i_solar_system/resolved_moon_audit_49i3e0.md` after the
planning handoff in `archive/milestone_history/49i_solar_system/resolved_moon_plan_49i3e.md`. Preserve the JPL
equal-volume mean radius, topocentric apparent centre, independent physical
state at every sample epoch, and one fixed chart-epoch product frame. Transport
the complete sample tangent geometry into that frame; do not treat the scalar
bright-limb angle as frame-invariant. Reuse the descriptor-driven appearance,
disk geometry, observed sequence, projection, per-centre magnification,
renderer, semantics, and exporters. Do not add runtime Moon behavior under
49I.3E.0.

For the output-neutral lunar appearance state, also consult
`archive/milestone_history/49i_solar_system/lunar_physical_appearance_49i3e1.md`. Preserve the single catalog Moon
identity, Earth parent relationship, JPL equal-volume mean radius, and generic
`SolarSystemApparentDisk` realization. Require the installed-DE440 validator
and explicit parallax evidence before acceptance. Do not add resolved disk
geometry, Moon display controls, magnification, sequence requests, or visible
output under 49I.3E.1.

For the drawable resolved single-epoch Moon, also consult
`archive/milestone_history/49i_solar_system/drawable_resolved_moon_49i3e2.md`. Keep bare `--moon` resolved by default,
preserve explicit symbolic compatibility, and apply Moon magnification only
after projection about the physical centre. Authorize chart families through
the body descriptor and reuse generic disk geometry/rendering/export. Exercise
factor 1000 in automated contracts for all five families; use a calibrated,
legible factor for human visual review. Do not add a Moon sequence or any other
multi-epoch Moon behavior under 49I.3E.2.


For observed multi-epoch Moon sequences, consult
`archive/milestone_history/49i_solar_system/observed_moon_disk_sequence_49i3e3.md`. Adapt `--moon-disk-sequence` into
the generic observed request, independently realize every sample, and
transform complete tangent geometry into one chart-epoch product frame.
Preserve descriptor-owned all-five-family Moon policy, per-centre
post-projection magnification, concise SVG hierarchy labels, and rejection of
frozen-Earth lunar requests. Do not add a Moon-specific sequence realizer,
projector, renderer, exporter, interpolation, or animation path.


The resolved-Moon program 49I.3E.0 through 49I.3E.3 is closed. Treat
`archive/milestone_history/49i_solar_system/resolved_moon_plan_49i3e.md` as accepted historical planning plus closure
evidence and preserve the implemented shared single-disk and observed-sequence
paths. Parent closure authorizes no new runtime behavior. Any Frozen-Earth
lunar sequence, interpolation, animation, texture, libration, eclipse,
resolved-disk refraction, or occultation work requires a new bounded milestone.


For performance or post-v0.9 closure work, consult
`archive/roadmap_history/test_performance_and_future_program_49j_50.md` and the accepted historical
audit at
`archive/milestone_history/49j_performance/performance_and_closure_audit_49j0.md`.
Keep the reusable-sphere diagnostic
separate from a cold independent-frame oracle, report exclusive wall-time spans
separately from overlapping profiler totals, and preserve
`generate_chart_request()` as the complete-render correctness route. Do not
add caching or optimization under 49J.0.

For 49J test changes, complete the accepted-practice audit and Fernando's
Adopt/Adapt/Reject/Defer decision milestone before changing fixture scope,
markers, test reuse, or execution policy. Faster execution must retain
independent public-path and scientific fault-detection evidence.

For 50A minor-body work, follow the accepted 50A.0 audit. Milestone 50A.1 may
add only the generic state-provider/resource seam: keep acquisition outside
rendering, preserve explicit state-resource chains, and never use an
unvalidated two-body orbit as a silent production fallback. Body registration,
CLI options, and visible objects remain later separately reviewed slices.
The accepted 50A.1 and 50A.2 records are archived under
`archive/milestone_history/50a_minor_bodies/`. Preserve their explicit SPK
segment-centre composition, narrow CSPICE type-21
segment evaluator, explicit DE440 dependency, frozen direct-Horizons oracle,
and calibrated Ceres/Apophis tolerances. 50A.2 is accepted; 50A.3 is the next
separately reviewed slice for the first drawable asteroid. Follow the accepted
50A.3A audit in
`archive/milestone_history/50a_minor_bodies/first_drawable_asteroid_audit_50a3a.md`:
begin with Ceres,
require an explicit local manifest-backed resource directory, reuse the shared
point and track machinery through descriptor-aware provider resolution, and
make no photometric or implicit-network claim.
The bounded implementation is accepted and archived in
`archive/milestone_history/50a_minor_bodies/drawable_ceres_50a3b.md`. Preserve
the target-source versus observer-source split: the minor-body SPK supplies
Ceres, while DE440/Skyfield continues to supply observer state and apparent
correction. Do not add implicit acquisition, a fallback propagator, magnitude
semantics, discovery, or a second projection/render/export path. Fernando
requested and accepted a post-closure numbered-asteroid generalization audit
before comet work. Follow
`archive/milestone_history/50a_minor_bodies/numbered_asteroid_generalization_audit_50a3c.md`:
keep permanent number, optional name, provisional designation, provider target,
solution, and classification separate; keep rendering offline; derive
request-owned descriptors only from an explicit verified manifest; resolve any
manifest-declared official name and its permanent number to one descriptor;
and use `(79989)` only as a generic acceptance specimen. Do not add
object-specific branching, implicit network lookup, or fuzzy name search.
50A.3D and PR 98's explicit-center CLI contract are implemented. Preserve the
rule that center, content, constellation layers, and masks are independent.
Milestones 50A.3G and 50A.3I are accepted. Preserve their explicit CLI
semantics and automatic numbered-asteroid preflight contracts.

For 50A.4, follow `archive/milestone_history/50a_minor_bodies/comet_numerical_validation_audit_50a4.md`. Until Fernando
accepts that audit, add no comet runtime, selector, acquisition, fixture, or
validation implementation. Preserve 2P/Encke as a proposed specimen rather
than a special runtime case.

For 50A.5C, follow the accepted `archive/milestone_history/50a_minor_bodies/second_drawable_comet_audit_50a5c.md`.
Preserve 161P/Hartley-IRAS as a bounded second installed-resource specimen,
never a runtime special case. Inspect signed SBDB and Horizons identity
responses before selecting its apparition record. Characterize new numerical
and position-angle evidence before proposing tolerances. Do not add automatic
comet acquisition, fuzzy discovery, photometric claims, physical tail
morphology, or another direction, temporal, projection, rendering, semantic,
or export pipeline.

Accepted 50A.3H audits one-command moving-object data resolution and governs
the implemented 50A.3I numbered-asteroid CLI preflight. Keep
automatic network access in an installed-CLI preflight phase:
validate and atomically publish an immutable resource before constructing the
ordinary offline chart request. Never allow request generation, provider state
evaluation, direction realization, projection, rendering, or export to query a
service. Do not add a silent orbital-element fallback. Keep artificial
satellite OMM/TLE plus SGP4/TEME physics in a separate provider milestone.

For 50B publication-style work, complete the print, typography, contrast,
accessibility, cartographic, and astronomical-atlas practice review plus
Fernando's adoption decisions before installing numerical physical-output
standards. Screen review alone cannot accept a print profile; style and output
mode must not change astronomical geometry.


For accepted 50S.4D Earth-orientation and topocentric work, preserve
`satellites/topocentric.py` as the distinct Cartesian-state boundary. Select
and identify the installed IERS-A resource explicitly, disable automatic
download and degraded accuracy, fail closed outside coverage, subtract the
WGS-84 observer in ITRS before angular conversion, and retain range plus vacuum
AltAz. Call the celestial result a topocentric geometric direction expressed
in GCRS axes; never label it ICRS, a formal GCRS coordinate, astrometric,
apparent, or observed. Add no field intersection, crossing solver,
illumination, photometry, CLI, drawing, or 50S.4E specimen behavior. Fernando accepted 50S.4D on 2026-09-15; only
the bounded 50S.4E propagated-specimen builder is authorized next.

### Accepted 50S.4E boundary

The bounded 50S.4E developer specimen builder is accepted and closed. It consumes the
installed synthetic snapshot and accepted 50S.4C/50S.4D services, performs no
network access, and writes only **propagated sampled specimens — not verified
crossings** beneath a caller-selected output directory. It must not construct
`SatelliteCrossingResult`, claim a complete catalogue search, select production
crossing tolerances, or become a hidden 50S.5 crossing oracle.

Fernando scientifically and architecturally accepted 50S.4E on 2026-09-15.
This closes 50S.4. Only bounded 50S.5 complete local FoV-crossing oracle work
is authorized next; 50S.6 acceleration and all later satellite behavior remain
unauthorized.


### Accepted 50S.5A audit boundary

Follow `satellite_crossing_oracle_audit_50s5a.md` for complete-local-oracle
work. Fernando scientifically and architecturally accepted 50S.5A on
2026-09-15. Only the bounded 50S.5B local crossing-oracle implementation is
authorized next; 50S.6 acceleration and all later satellite behavior remain
unauthorized. Preserve the distinction between a fixed geometric field in
GCRS axes and provider apparent ICRS evidence. Uncertain numerical intervals
must subdivide or fail closed; they must never become silent negative results.

### Accepted 50S.5B implementation boundary

The bounded candidate implementation lives in
`satellites/crossing_oracle.py`. It may scan all selected snapshot records,
compose only the accepted SGP4/TEME and topocentric services, and return ordered
connected `SatelliteCrossingResult` values. Preserve validated numerical
completeness under declared time and angular tolerances; this is not a formal
interval-arithmetic proof. Uncertain evaluation, exhausted resources, invalid
records, propagation failure, or unavailable Earth orientation must fail
closed through `SatelliteCrossingConvergenceError` with the record identity.
Fernando scientifically and architecturally accepted 50S.5B on 2026-09-15.
Only a documentation-first 50S.6 conservative-acceleration audit is authorized
next; runtime acceleration and all later behavior remain unauthorized.

### Accepted 50S.6A acceleration-audit boundary

Follow `satellite_crossing_acceleration_audit_50s6a.md` before adding any
crossing acceleration. Preserve the independently callable exhaustive 50S.5
oracle. A filter may reject only with an explicit conservative bound; equality,
uncertainty, unsupported regimes, or arithmetic failure must retain the record
for exact solving. Horizon and Earth-occultation rejection are not compatible
with the accepted geometric query semantics. Fernando scientifically and architecturally accepted this audit on 2026-09-15.
Only bounded 50S.6B implementation of the first topocentric cone/orbital-shell
selector is authorized. No phase stage, coarse vectorized propagator,
HEALPix/time index, horizon/occultation filter, or later behavior is authorized.

### Accepted 50S.6B cone-shell selector boundary

The candidate `satellites/crossing_acceleration.py` adds only immutable
`ConeShellPolicy`, `ConeShellDecision`, `ConeShellSelection`, and
`ConservativeConeShellSelector`. It admits only
`synthetic_50s4b_v1` and intervals no longer than 60 seconds. Rejection
requires strict separation between the closed field and a whole-interval
reachable cap derived from the accepted initial topocentric state and an
outward shell-speed bound.

Every unsupported snapshot, longer interval, unsupported element regime,
insufficient range, or initial-state failure is `indeterminate` and must reach
the exact 50S.5 solver. No accelerated coordinator, phase filter, coarse-state
filter, horizon/occultation filter, index, or changed oracle result is included.
Fernando scientifically and architecturally accepted this bounded selector on
2026-09-16. Only a documentation-first 50S.6C coordination, broader-domain,
and benchmark-admission audit is authorized next.

### Accepted 50S.6C coordination-audit boundary

Follow `satellite_crossing_coordination_audit_50s6c.md` before adding an
accelerated search service. Preserve the independently callable exhaustive
50S.5 route and the accepted 50S.6B selector domain. Retain and indeterminate
records must reach one shared exact record seam; rejected records may be omitted
only with complete ordered selector evidence. Selector failure falls back to
exhaustive solving or fails closed and can never become an empty result.

This documentation-only audit authorizes no broader selector domain, benchmark
claim, default enablement, phase/coarse/indexing stage, or later satellite
behavior. Fernando scientifically and architecturally accepted 50S.6C on
2026-09-16. Only a bounded 50S.6D coordinator inside the existing three-record,
60-second domain is authorized next.


### Accepted 50S.6D accelerated-coordinator boundary

The accepted implementation extracts the existing exact per-record operation
without changing its algorithm and compose the accepted 50S.6B selector inside
the installed three-record, 60-second domain. Preserve the independently
callable exhaustive route as the default. Retain and indeterminate decisions
must reach the shared exact seam once; rejected records may be omitted only
after complete query-bound NORAD-ordered evidence validation.

Selector exceptions must fall back to exhaustive solving or fail closed.
Missing, inconsistent, duplicate, reordered, unknown, or out-of-domain reject
evidence must fail closed. Keep acceleration evidence separate from the exact
`SatelliteCrossingResult` tuple. No broader selector domain, benchmark claim,
default enablement, phase/coarse/index stage, horizon/occultation predicate,
illumination, photometry, CLI, reporting, drawing, 50S.7, or later behavior is
authorized.


Fernando scientifically and architecturally accepted 50S.6D on 2026-09-16.
Preserve the exhaustive default, shared exact-record seam, separate immutable
acceleration evidence, complete ordered-decision validation, and the installed
three-record, 60-second limit. No broader domain, benchmark claim, default
enablement, phase/coarse/index stage, horizon/occultation predicate, 50S.7, or
later behavior is authorized next without a separately accepted bounded
milestone.


## Accepted 50S.6E boundary

Before any later satellite acceleration, batching, reporting, drawing, or
illumination work, read
`satellite_multifov_interchange_audit_50s6e.md`. It proposes one observer and
any non-empty number of independently timed, field-centre airmass-bounded FoVs;
ten is a reference workload, not a hard-coded public limit. The initial policy
uses geometric vacuum AltAz and plane-parallel `X = sec(z)`, with configurable
`X_max` defaulting to 2. Only the field centre is checked, and it must satisfy
the limit throughout the complete field interval. This is field admission, not a satellite horizon or occultation filter.
Fernando scientifically and architecturally accepted 50S.6E on 2026-09-16.
Only a separately bounded 50S.6F implementation is authorized next. Generic observatory reports, exact
chart tracks, Paranal/ELT adapters, Sunlight, solar Earthshine, Moonlight,
Lunar-Earthshine, brightness, and detector effects remain later, separately
accepted milestones.


## Accepted 50S.6F implementation boundary

The accepted implementation adds only the immutable Python batch contracts in
`satellites/crossing_batch.py`, the governed field-centre altitude evaluator
in `satellites/topocentric.py`, and focused tests. Preserve one snapshot, one
observer, unique ordered FoV identifiers, independently bounded intervals, the
existing synthetic three-record snapshot, and the existing 60-second
single-field admission domain.

Validate the complete batch before solving any field. Accumulate every
field-specific validation failure in input order and raise one typed atomic
error; do not return partial crossing results. Certify centre-only geometric
vacuum airmass over the complete interval with configurable `X_max` defaulting
to 2. Process any non-empty field count in execution-only chunks defaulting to
10, preserve input order, and compose the accepted 50S.6D single-field route.
This milestone makes no useful-speed or physical-state-reuse claim. It adds no
CLI, file input, validation-output file, generic report, chart, observatory
adapter, illumination, photometry, broader catalogue, or later behavior.
Fernando scientifically and architecturally accepted 50S.6F on 2026-09-17
after 2,577 plugin-disabled tests passed. Only a separately bounded 50S.6G
audit is authorized next; no 50S.6G implementation is authorized.


## Accepted 50S.6G delivery-audit boundary

Read `satellite_delivery_audit_50s6g.md` before proposing representative
snapshot admission, exact crossing reports, multi-FoV CLI/files, exact local
track layers, or chart integration. Preserve one observer, ordered independent
FoVs, centre-only complete-interval airmass admission, atomic validation, exact
50S.5 equivalence, and illumination-independent geometric results.

Direct Python/CLI mode remains atomic. File mode may write one separate
validation-output JSON only after whole-batch validation fails; it performs no
crossing work, records every invalid field, embeds the ordered valid subset,
and requires digest-bound revalidation when explicitly supplied for a second
call. JSON is the only initial request protocol. Reports use one canonical
logical model with JSON, ECSV, and VOTable encodings. Exact tracks must reuse
the accepted propagation/topocentric services and canonical chart pipeline.
This accepted audit changes no runtime or output. Fernando scientifically and
architecturally accepted it on 2026-09-17 after all 145 plugin-disabled
current-documentation tests passed in 4.36 seconds. Only bounded 50S.6G.1A
external immutable snapshot loading is authorized next. Acquisition, broader
runtime admission, reports, CLI/files, exact tracks, chart integration, and all
later behavior remain unauthorized.


## Accepted 50S.6G.1A external snapshot boundary

The accepted implementation adds only `load_snapshot_directory(directory)` to
`satellites/snapshots.py` and its intentional package export. It accepts one
explicit caller-selected local directory, requires a real non-symlink
directory plus non-symlink regular `manifest.json` and declared records file,
and reuses the complete accepted manifest, canonical-byte, digest, OMM,
identity, ordering, epoch, and count validation.

The validated manifest, not the directory name, owns snapshot identity. The
loader performs no discovery, download, acquisition, provider access, retry,
fallback, cache write, directory publication, representative-scale admission,
crossing calculation, report, CLI, or chart behavior. The installed synthetic
snapshot and existing `load_snapshot()` remain unchanged public routes.
Fernando scientifically and architecturally accepted 50S.6G.1A on 2026-09-17
after the 164-test focused gate and all 2,583 plugin-disabled tests passed.
Only a separately bounded 50S.6G.1B representative snapshot preflight and
evidence audit is authorized next, not its implementation.


## Accepted 50S.6G.1B provider-policy and evidence boundary

Read `satellite_snapshot_preflight_audit_50s6g1b.md` before proposing any
representative satellite acquisition, external-snapshot admission, or scale
claim. The accepted audit chooses CelesTrak `GROUP=active&FORMAT=CSV` as one
explicit representative-scale population, not a complete resident-space-
object catalogue.

Policy freezing and GP acquisition are separate operations. A direct HTTP 200
policy receipt must be inspected and explicitly acknowledged by exact digest
before one direct HTTP 200 bulk GP request; redirects, retries, fallback,
polling, per-object requests, and concurrent downloads are forbidden. Raw
bytes, receipts, canonical snapshot, medium selection, and evidence remain
outside the repository and package. This audit changes no runtime. Fernando
scientifically and architecturally accepted this boundary on 2026-09-17 after
all 147 plugin-disabled current-documentation tests passed in 4.54 seconds.
Only bounded 50S.6G.1B.1 fake-transport policy-receipt and deterministic-
builder implementation is authorized next. No live CelesTrak request or
50S.6G.1B.2 work is authorized.

50S.6G.1B.1 is now implemented through a mandatory injected transport and an
offline response-file developer command. Preserve the absence of a default or
live network adapter. Exact policy-response SHA-256 acknowledgement must occur
before any GP transport call; failures remain atomic. Do not perform a live
CelesTrak request or begin representative admission/evidence without separate
Fernando authorization.
