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

Fernando accepted 50S.6G.1B.1 on 2026-09-17 after 175 focused plugin-disabled
tests and all 2,594 plugin-disabled tests passed. The next step is not an
implicit live operation: obtain separate authorization before fetching the
policy, and require separate approval of its exact digest before GP access.

The exact direct policy URL is `https://celestrak.org/usage-policy.php`; the
50S.6G.1B.1 regression test protects it. A redirected or documentation-
subdirectory URL is not an acceptable substitute.

Fernando accepted this direct-policy-URL correction on 2026-09-17 after all
2,595 plugin-disabled tests passed. CelesTrak remains the only authorized
provider. Do not treat that acceptance as permission for a live GP request.

Fernando accepted the exact `non-HTTP 200` policy-clause compatibility
correction on 2026-09-17 after 10 focused tests and all 2,595 plugin-disabled
tests passed. The frozen 14,643-byte policy response has SHA-256
`67bf0faa7e026a7cd49799069db9d3355f2a867894133afd39e130d6185724aa`. This acceptance validates the parser correction and receipt only;
explicit approval of that exact digest remains separately required before any
GP request.

Fernando accepted the CelesTrak epoch/media-type compatibility correction and
the resulting external Active snapshot on 2026-09-17 after 15 focused tests
and all 2,600 plugin-disabled tests passed. The single direct response contains
16,559 records and has SHA-256 `e54730e14b2097444c5e20bba6dd13d3e2d92f956797d49256ddb1a70ffe5014`; its canonical records have SHA-256
`e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`. Preserve CelesTrak's declared UTC meaning while normalizing
the exact suffix-free six-fractional-digit CSV epoch to Wenu's canonical `Z`
form, and preserve the captured `text/plain; charset=UTF-8` media type. No
second provider request occurred. 50S.6G.1B.2 remains separately authorized.


## Accepted 50S.6G.1B.2A digest-admission boundary

Before external snapshot admission work, read
`satellite_snapshot_admission_audit_50s6g1b2a.md`. The candidate requires
exact canonical-record SHA-256 plus validated manifest identity, shared by the
selector, accelerated coordinator, and multi-FoV batch. Preserve the installed
synthetic default and keep external admission explicit and evidence-only. This
documentation audit changes no runtime and does not authorize medium selection,
matrix execution, chart integration, or another provider request. Fernando
scientifically and architecturally accepted it on 2026-09-17 after all 150 plugin-disabled current-documentation tests passed in 3.84 seconds. Only
bounded 50S.6G.1B.2B digest-admission implementation is authorized next.


## Accepted 50S.6G.1B.2B admission boundary

The candidate implementation in `satellites/snapshot_admission.py` owns
explicit external identity, finite policy, and opaque admission-token
contracts. Preserve exact canonical-record SHA-256 plus the complete audited
manifest identity. The selector, accelerated coordinator, and multi-FoV batch
must consume the same token before external scientific work. Keep all existing
synthetic ID defaults unchanged. Do not add medium selection, a matrix runner,
implicit discovery, network access, external package data, reports, tracks,
charts, or later 50S.6G behavior before separate acceptance.


Fernando scientifically and architecturally accepted 50S.6G.1B.2B on
2026-09-17 after 51 focused runtime tests, 151 current-documentation tests,
and all 2,611 plugin-disabled tests passed; the complete suite took 215.89
seconds. `git diff --check` and the working tree were clean. Only bounded
50S.6G.1B.2C deterministic medium-specimen work is authorized next; 50S.6G.1B.2D
matrix execution and later delivery remain separately unauthorized.


## Accepted 50S.6G.1B.2C medium-specimen boundary

Before medium-specimen work, read
`satellite_medium_specimen_audit_50s6g1b2c.md`. The candidate uses only the
explicit admitted parent, the acquisition stop instant, exact declared scalar
bins, two deterministic representatives per non-empty bin, and deterministic
fill to a default target of 256. Keep the product external, receipt-bound,
non-statistical, and non-default. This documentation audit changes no runtime
and does not authorize a real subset operation or matrix execution.


Fernando scientifically and architecturally accepted 50S.6G.1B.2C on
2026-09-17 after all 153 plugin-disabled current-documentation tests passed in
4.58 seconds; `git diff --check` and the working tree were clean. Only bounded
fake-data implementation is authorized next. The first real medium selection,
50S.6G.1B.2D matrix execution, and later delivery remain separately
unauthorized.

### Candidate 50S.6G.1B.2C boundary

Treat `satellites/snapshot_evidence.py` as the sole candidate owner of
deterministic medium selection and receipt-bound atomic publication. Preserve
exact external admission, acquisition-report and captured-response binding,
the retrieval-stop age reference, independent scalar bins, full NORAD
identifiers, canonical ordering, and the synthetic installed default. Keep
`select-medium` explicitly offline.

On 2026-09-17, 30 plugin-disabled focused tests passed in 5.99 seconds. This
candidate has not yet been scientifically and architecturally accepted. Do not
run it on the real 16,559-record parent, authorize 50S.6G.1B.2D, package an
external product, or change runtime defaults without Fernando's separate
approval.

### Accepted 50S.6G.1B.2C implementation boundary

Fernando scientifically and architecturally accepted the bounded fake-data
implementation on 2026-09-17 at `1d9d4e4`, after 2,622 plugin-disabled tests
passed in 225.75 seconds and 185 focused tests passed in 9.03 seconds. Preserve
`snapshot_evidence.py` as the deterministic medium-selection owner and keep
the command offline, explicit, digest-bound, and receipt-bound.

Acceptance does not authorize running against the real 16,559-record parent.
Require Fernando's separate approval before the first real selection.
50S.6G.1B.2D matrix execution, packaging, discovery, provider access, and
runtime-default changes remain unauthorized.

### Candidate real 50S.6G.1B.2C artifact boundary

The external specimen contains 256 records with canonical-record SHA-256
`2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`.
Its canonical selection receipt has SHA-256
`1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`.
It derives from the accepted 16,559-record parent
`e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`
using age reference `2026-09-17T15:52:23.000000Z`.

The authorized offline operation used `a5b95fd`, selected 48 mandatory and
208 fill records across 24 nonempty bins, preserved all parent bytes, and made
no provider request. Keep this product external and identity-bound. Do not
package, discover, refresh, substitute, or treat it as statistically
representative. Its candidate evidence record preceded acceptance; do not begin
50S.6G.1B.2D without separate authorization.

### Accepted real 50S.6G.1B.2C artifact

Fernando accepted only exact external subset
`2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`
and receipt
`1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`
on 2026-09-17 at `c4cd009`, after 157 plugin-disabled documentation tests
passed in 4.66 seconds. This closes 50S.6G.1B.2C.

Do not refresh, substitute, package, discover, or promote this artifact to a
runtime default. Only a separately authorized 50S.6G.1B.2D matrix audit may
proceed next; matrix execution itself is not authorized by this acceptance.

### Candidate 50S.6G.1B.2D audit boundary

Treat `satellite_equivalence_matrix_audit_50s6g1b2d.md` as a
documentation-only candidate. Preserve the exact accepted medium and receipt
digests, the 10-field same-observer/same-night contract, independent intervals,
shared-interval research control, strict canonical result equality, complete
selector partitions, forbidden fallback, isolated raw resource observations,
atomic external evidence, and all stated non-claims.

Do not implement or run the matrix, access a provider, package external data,
add concurrency or cache reuse, create tracks or charts, or claim speed without
Fernando's separate authorization.

### Accepted 50S.6G.1B.2D audit boundary

Fernando scientifically and architecturally accepted the documentation-only
audit on 2026-09-17 at `6e7a8b9`, after 159 plugin-disabled documentation
tests passed in 10.75 seconds. Only bounded fake-data implementation of
`crossing_matrix.py`, its tests, canonical evidence, isolated resource seam,
atomic publication, and offline command is authorized next.

Do not read or execute the accepted real 256-record specimen, publish real
matrix evidence, claim speed or capacity, add concurrency or cache reuse, or
begin reports, tracks, charts, illumination, or later delivery without
separate authorization.

### Candidate 50S.6G.1B.2D implementation boundary

Treat `satellites/crossing_matrix.py` at candidate commit `19520f3` as a
fake-data-tested implementation awaiting Fernando's scientific and
architectural acceptance. On 2026-09-17, 2634 plugin-disabled full-suite tests
passed in 230.25 seconds. Do not read the accepted real 256-record specimen,
execute the real ten-field matrix, claim a speedup, or advance later 50S.6G
delivery under this candidate record. Any real execution requires a separate
explicit authorization after acceptance.

### Accepted 50S.6G.1B.2D implementation boundary

Fernando scientifically and architecturally accepted the fake-data-only
50S.6G.1B.2D implementation on 2026-09-17 after 2634 plugin-disabled
full-suite tests passed in 230.25 seconds at `19520f3` and 161
plugin-disabled current-documentation tests passed in 3.32 seconds at
`3ef6a4d`. Do not read the accepted real specimen or execute the real matrix
under this acceptance. Only a separately bounded real-execution audit is
authorized next; execution and later delivery require separate explicit
authorization.

### Candidate real-execution readiness boundary

At integrated baseline `9bdf301`, do not attempt the real 50S.6G.1B.2D
matrix. The accepted core still exposes injected test seams and lacks the
frozen ten-field request fixture, production airmass certifier,
fresh-subprocess worker, and explicit offline developer command. Only bounded
production-path implementation with fake data is authorized next. Do not read,
discover, copy, hash, or otherwise access the external real specimen; do not
propagate it, execute a route, or infer performance under this audit.

### Accepted real-execution readiness boundary

Fernando scientifically and architecturally accepted the fail-closed audit on
2026-09-17 after 163 plugin-disabled current-documentation tests passed in
3.80 seconds at `054ac39`. Implement only the bounded production path using
fake data: exact receipt constraints, frozen fixture, production airmass
certifier, fresh-subprocess protocol and worker, offline command, and tests.
Do not access the accepted real specimen or execute the real matrix without a
later separate explicit authorization.\n

### Candidate production-path implementation boundary

The candidate branch implements only the accepted fake-data production path:
exact medium-receipt constraints, a digest-frozen ten-field La Ligua fixture,
the production whole-interval airmass certifier, a canonical fresh-subprocess
worker/executor, and the explicit offline `run-equivalence-matrix` developer
command. Fernando directed on 2026-09-17 that fixture durations be reduced to
15 and 60 seconds and that new tests avoid unnecessary repeated scientific
route runs. Do not access the accepted real specimen or execute the real
matrix under this candidate. Verification and separate scientific and
architectural acceptance are still required.\n

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

### Candidate first-real-execution authorization boundary

Read the candidate 50S.6G.1B.2D.1 section in
`satellite_equivalence_matrix_audit_50s6g1b2d.md`. It proposes exactly one
offline run of the accepted 256-record specimen into one new empty external
output root, with the three accepted digests, exact acknowledgement, accepted
15/60-second fixture, existing 3600-second subprocess timeout, no retry, and
separate evidence review. This documentation candidate authorizes no specimen
access or execution before Fernando's explicit acceptance.\n

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

### Candidate matrix progress boundary

The first real run remains paused. The candidate parent-process progress bar
reports completed worker count over the policy-derived total plus field, route,
and phase. It writes only to parent stderr and must not change worker protocol,
canonical evidence, timing, route order, timeout, retries, science, or
publication. Verification extends the existing fake protocol test and adds no
scientific run. Require separate acceptance, merge, and renewed one-run
authorization before accessing the real specimen.

## Candidate matrix progress verification boundary

Candidate commit `b0b4432` was verified on 2026-09-18 with 180 focused plugin-disabled tests passing in 5.44 seconds, the complete 2647-test plugin-disabled suite passing in 239.53 seconds, and a clean diff check. Do not treat this verification as acceptance, merge authority, or renewed real-run authorization. Do not access the accepted real specimen until the progress change is accepted, merged, and the one-run authorization is explicitly renewed.

## Accepted matrix progress boundary

Fernando scientifically and architecturally accepted the 50S.6G.1B.2D.2 progress display at `96b9ba0` on 2026-09-18. Do not infer merge authority or real-run authority from this acceptance. Keep the accepted real specimen untouched until Fernando separately requests the merge and then explicitly renews the one-run authorization.

## Renewed one-run matrix authority

Fernando explicitly renewed authorization on 2026-09-18 for exactly one real matrix run after progress-display merge `9c4b808`. Do not access the accepted specimen or start the command until this renewal record is merged and the external preflight is repeated. Then issue exactly one operator-started command using the accepted specimen, a new empty output root, 10 fields, only 15/60-second intervals, both routes, one warm-up plus three measured repetitions, at most 80 subprocess invocations, and no retry or resume. Failure or interruption consumes the authority. Success remains candidate evidence requiring independent review.

## Accepted renewed one-run authority

Fernando scientifically and architecturally accepted the renewed authorization record at `dd71e01` on 2026-09-18 after 169 documentation tests passed in 4.29 seconds and repository checks were clean. Do not start or consume the run before this record is merged and the external preflight is repeated. After those conditions pass, issue exactly one command and do not retry or resume it.

## Candidate first real-matrix evidence boundary

The one authorized run was consumed successfully on 2026-09-18 at `9d93113`, producing candidate report `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258`. Do not rerun, resume, refresh, or substitute the external evidence. Exact empty-result equivalence and partition integrity passed across 10 fields and 60 measured observations, but all fields had zero crossings; do not claim positive real-crossing validation or universal performance. The candidate requires Fernando's separate scientific and architectural acceptance.

## Accepted first real-matrix evidence boundary

Fernando scientifically and architecturally accepted the first real-matrix report `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258` at `186e255` on 2026-09-18. Preserve the explicit finding: exact empty-result equivalence and partition integrity passed, while all 10 fields had zero crossings. Do not claim positive real-crossing validation or universal performance, and do not rerun the matrix. Serial closure review, output-neutral refactoring, or parallelization requires a new bounded audit and explicit authorization.


## Candidate bounded 50S.6G.1B closure boundary

At integrated baseline `b010a6c`, accepted report
`d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258`
establishes exact empty-result exhaustive/accelerated equality and conservative
partition integrity for the accepted ten-field real matrix. Every field had
zero crossings. Do not claim positive real-crossing validation, a full-snapshot
matrix, broader FoV-count coverage, universal performance, concurrency, or
reuse.

The one-run authority is consumed. Do not rerun, retry, resume, refresh,
substitute, search for positive real crossings, execute the full snapshot,
parallelize, or refactor under this candidate. This documentation-only closure
changes no runtime. Until Fernando separately accepts it, 50S.6G.1B remains
open and 50S.6G.2A is unauthorized. Acceptance would authorize only a bounded
50S.6G.2A documentation audit, not report implementation.


## Accepted bounded 50S.6G.1B closure boundary

Fernando scientifically and architecturally accepted the bounded closure on
2026-09-19 at `c62a451`, after 173 plugin-disabled current-documentation
tests passed in 3.82 seconds and repository checks were clean.

Preserve the exact limitation: every real field had zero crossings, so the
accepted result is exact empty-result equivalence and conservative partition
integrity, not positive real-crossing validation or a universal scale or
performance claim. The one-run authority remains consumed.

Only the bounded 50S.6G.2A documentation audit is authorized next. Do not
implement a report model, JSON Schema, encoder, decoder, round trip, CLI,
track, chart, new execution, refactor, or parallelization without later
separate acceptance.


## Candidate 50S.6G.2A exact-report audit boundary

Read `satellite_exact_crossing_report_audit_50s6g2a.md` before any
exact-crossing report or JSON work. The candidate permits no runtime change.
Preserve exact-local scientific status separately from SatChecker sampled
candidates, explicit zero-crossing fields, caller-supplied immutable creation
time, complete retained context, semantic array order, canonical digest,
closed Draft 2020-12 schema, duplicate-key rejection, semantic validation, and
typed byte-identical round trips.

Do not implement until Fernando separately accepts the audit. ECSV/VOTable,
CLI/files, tracks, charts, illumination, magnitude, detector effects, provider
access, another real run, and unrelated refactoring remain unauthorized.


## Accepted 50S.6G.2A implementation boundary

Fernando scientifically and architecturally accepted the audit on 2026-09-19
at `835ddfe`, after 175 plugin-disabled documentation tests passed in 3.27
seconds and repository checks were clean.

Implement only the bounded immutable exact-report logical model, packaged
Draft 2020-12 JSON Schema, pure deterministic encoder/decoder, and focused
tests. Preserve every accepted status, ordering, digest, schema, semantic, and
round-trip constraint. Do not implement ECSV/VOTable, CLI/files, tracks,
charts, illumination, magnitude, detector effects, provider access, another
real run, or unrelated refactoring.


## Candidate 50S.6G.2A implementation boundary

Treat `satellite_crossing_reports.py`, its packaged version-1 schema, and
`test_satellite_crossing_reports.py` as a bounded candidate awaiting
Fernando's scientific and architectural acceptance. Preserve the distinct
exact-local product/status, explicit zero-crossing fields, caller-supplied
creation time, complete typed context, semantic array order, canonical digest,
closed schema, duplicate-key rejection, null future science, and byte-identical
round trip.

Do not add ECSV/VOTable, CLI/files, atomic publication, tracks, charts,
illumination, magnitude, detector effects, scheduling adapters, provider
access, another real run, or unrelated refactoring under this candidate.


## Accepted 50S.6G.2A implementation boundary

Fernando scientifically and architecturally accepted the bounded 50S.6G.2A
implementation on 2026-09-19. The executable candidate at `a65e5ac` passed
all 2,676 plugin-disabled tests in 234.08 seconds; the final pre-acceptance
documentation gate at `8af0d14` passed 179 tests in 5.05 seconds; diff and
working-tree checks were clean.

Preserve `satellite_crossing_reports.py` as the exact-local logical report
owner and preserve the packaged version-1 schema, deterministic identity,
strict typed decoder, zero-crossing semantics, null future science, and
byte-identical round trips. Do not begin 50S.6G.2B or later work without
separate authorization.


## Candidate 50S.6G.2B audit boundary

Treat `satellite_tabular_report_audit_50s6g2b.md` as a documentation-only
candidate. It proposes lossless in-memory ECSV and VOTable 1.5 encodings of the
accepted exact report through one shared reusable format-neutral tabular
projection and thin format adapters. Canonical JSON and
`report_identity_sha256` remain logical authority.

Do not implement 50S.6G.2B before Fernando's separate scientific and
architectural acceptance. Do not add paths, files, CLI, atomic publication,
plain CSV, tracks, charts, visibility science, provider access, another real
run, or unrelated refactoring.

## Accepted 50S.6G.2B audit boundary

Fernando scientifically and architecturally accepted the documentation-only
audit on 2026-09-19 at `ef14bc1`, after 181 plugin-disabled
current-documentation tests passed in 4.88 seconds and repository checks were
clean.

Implement only one reusable format-neutral in-memory tabular projection with
thin ECSV and VOTable 1.5 adapters, strict validation, and lossless exact-report
reconstruction preserving canonical JSON and `report_identity_sha256`.
Do not add paths, files, CLI, atomic publication, plain CSV, tracks, charts,
visibility science, provider access, another real run, or unrelated
refactoring. 50S.6G.2C and later milestones remain separately unauthorized.


## Candidate 50S.6G.2B Astropy Unicode-null correction boundary

Candidate testing on Fernando's Mac with Astropy 7.1.0 demonstrated that
Astropy deliberately discards VOTable BINARY2 null flags for `char` and
`unicodeChar` fields. Treat the amendment in
`satellite_tabular_report_audit_50s6g2b.md` as documentation-only and
unaccepted. It proposes exact adjacent Boolean `__is_null` companion FIELDs
only for nullable Unicode VOTable values, while leaving the shared logical
projection, ECSV, canonical JSON, and `report_identity_sha256` unchanged.

Do not interpret an empty string as null, write a private BINARY2 parser, or
make further runtime changes until Fernando separately accepts this bounded
amendment. Paths, files, CLI, publication, tracks, charts, visibility science,
provider access, and new execution remain unauthorized.


## Accepted 50S.6G.2B Astropy Unicode-null correction

Fernando scientifically and architecturally accepted the bounded correction on
2026-09-19 at `5038e4a`, after 184 plugin-disabled current-documentation
tests passed in 5.28 seconds and repository checks were clean. Implement only
the exact adjacent Boolean `__is_null` VOTable FIELDs for nullable Unicode
values, strict validation, and focused tests. Preserve the shared logical
projection, ECSV, canonical JSON identity, and every existing 50S.6G.2B
exclusion.


## Candidate 50S.6G.2B implementation verification boundary

Treat the in-memory ECSV/VOTable implementation at `3bbd82f` as a verified
candidate awaiting Fernando's scientific and architectural acceptance. The
combined report/documentation gate passed 208 plugin-disabled tests in 6.68
seconds, and all 2,689 plugin-disabled repository tests passed in 215.15
seconds. Repository checks and the Mac working tree were clean and
synchronized.

Preserve the single shared schema-derived projection, deterministic ECSV and
VOTable 1.5/BINARY2 adapters, strict reconstruction, canonical JSON and
`report_identity_sha256`, and accepted explicit Unicode `__is_null`
companions. Do not merge, begin 50S.6G.2C, or add paths, files, CLI,
publication, tracks, charts, visibility science, provider access, another real
run, or unrelated refactoring before separate acceptance.


## Accepted complete 50S.6G.2B implementation boundary

Fernando scientifically and architecturally accepted the complete bounded
50S.6G.2B implementation on 2026-09-19. Executable commit `3bbd82f` passed
208 focused tests in 6.68 seconds and all 2,689 plugin-disabled tests in
215.15 seconds. Documentation evidence commit `ece80c7` passed all 186
current-documentation tests in 4.60 seconds; diff checks and the clean,
synchronized Mac working tree passed.

Preserve the single shared schema-derived projection, deterministic ECSV and
VOTable 1.5/BINARY2 adapters, canonical JSON and
`report_identity_sha256`, strict reconstruction, and explicit nullable
Unicode `__is_null` companions. This acceptance authorizes no later
milestone. Do not begin 50S.6G.2C, filesystem/CLI publication, tracks, charts,
visibility science, provider access, another real run, or unrelated
refactoring without separate authorization.

## Candidate 50S.6G.2C audit boundary

Read `satellite_cli_file_protocol_audit_50s6g2c.md` before any satellite
crossing CLI, request-file, validation-output, manifest, or filesystem
publication work. The candidate specifies direct atomic calculation, one
closed initial JSON request, deterministic first-call validation output, and a
second explicit call that revalidates and calculates only the embedded valid
subset while retaining every invalid FoV as audit evidence. It also freezes
explicit paths, fixed bundle filenames, digests, no-clobber and symlink safety,
exit status, and interruption cleanup while reusing the accepted canonical
JSON/ECSV/VOTable report model.

Do not implement 50S.6G.2C before Fernando separately accepts this audit. Do
not add provider access, new execution science, tracks, charts, visibility,
illumination, brightness, detector effects, or unrelated refactoring.

## Accepted 50S.6G.2C audit boundary

Fernando scientifically and architecturally accepted the documentation-only
50S.6G.2C audit on 2026-09-19 at `bcac404`, after all 188 plugin-disabled
current-documentation tests passed in 5.29 seconds and repository checks were
clean.

Implement only the bounded offline CLI/filesystem adapter, its closed initial
request, validation output and manifest schemas, direct atomic route,
validated-subset second call, accepted JSON/ECSV/VOTable bundle composition,
path/symlink/no-clobber policy, exit status, interruption cleanup, and focused
tests. Do not add provider access, new execution science, tracks, charts,
visibility, illumination, brightness, detector effects, scheduling adapters,
or unrelated refactoring. 50S.6G.3A and later work remain unauthorized.

## Candidate 50S.6G.2C implementation boundary

Treat the CLI/file-protocol implementation as an unaccepted candidate. It may
contain only the offline adapter, packaged closed schemas, validation-only
coordinator seam, installed entry point, focused tests, and directly required
documentation. Do not add provider access, acquisition, new execution science,
tracks, charts, visibility, illumination, brightness, detector effects,
scheduling adapters, or unrelated refactoring. Do not merge or begin
50S.6G.3A before separate verification and acceptance.

## Candidate 50S.6G.2C implementation verification boundary

Treat `e08ebf5e0061dbf1e69c8cc58a55a9696e785300` as a verified candidate,
not an accepted implementation. The 235-test immediate gate passed in 7.63
seconds and all 2,709 plugin-disabled tests passed in 237.35 seconds on
Fernando's Mac; the CLI help preflight, diff check, branch synchronization, and
working-tree check were clean. Do not merge, delete branches, or begin
50S.6G.3A without Fernando's separate scientific and architectural acceptance.

## Accepted 50S.6G.2C implementation boundary

Fernando scientifically and architecturally accepted the bounded implementation
on 2026-09-19. Executable commit `e08ebf5` passed 235 immediate tests in 7.63
seconds and all 2,709 plugin-disabled tests in 237.35 seconds; documentation
commit `f2bb49c` passed 191 tests in 5.50 seconds. Preserve every accepted CLI,
protocol, identity, validation, report, path, publication, status, and
interruption contract.

Only a bounded documentation-first 50S.6G.3A exact-local-track audit is
authorized next. Do not implement tracks, layers, charts, visibility,
illumination, brightness, provider access, or new execution science without
later separate acceptance.

## Candidate 50S.6G.3A audit boundary

Read `satellite_exact_local_track_audit_50s6g3a.md` before any exact local satellite track or layer work. Treat the document as a candidate only. Do not implement until Fernando separately accepts it.

Preserve one accepted connected crossing as event truth, the accepted snapshot/SGP4/TEME/topocentric route as direction truth, mandatory exact entry/closest/exit anchors, deterministic fail-closed sampling, distinct candidate-versus-exact scientific status, and an evidence-only layer. Do not add chart integration, planisphere work, provider access, report/CLI changes, visibility, illumination, brightness, or unrelated refactoring.

## Accepted 50S.6G.3A audit boundary

Fernando scientifically and architecturally accepted the audit on 2026-09-19 at `ce549715889c135e17b87749f3860855b1b54447`; 193 plugin-disabled current-documentation tests passed in 5.73 seconds and repository checks were clean.

Implement only the exact connected-visit evidence, deterministic anchored fail-closed sampler, identity/provenance contract, output-neutral path/event views, and focused offline tests. Do not begin 50S.6G.3B charts, 50S.6G.4A/B planispheres, provider work, report/CLI changes, visibility, illumination, brightness, or unrelated refactoring. Do not merge the candidate implementation before separate verification and acceptance.

## Candidate 50S.6G.3A implementation boundary

Treat `98a756d4405ba60756e3899d9a0886029cfa8afd` as a focused-test-passing candidate, not an accepted implementation. Preserve the timeless collection `CoordinateSpec`, evidence-level UTC sample scale, per-sample UTC instants, exact event anchors, deterministic left-before-right adaptation, fail-closed limits, snapshot binding, exact-visit semantics, and evidence-only layer ownership.

The 69-test plugin-disabled focused gate passed in 75.58 seconds. Do not merge or begin 50S.6G.3B before full-suite and documentation verification plus Fernando's separate scientific and architectural acceptance. Do not add report/CLI changes, chart registration, planispheres, providers, visibility, illumination, brightness, or unrelated refactoring.

## Candidate 50S.6G.3A implementation verification boundary

Treat `f0a41648dc5565e4a8deed5d7bb6640a3df4e2d1` as a verified candidate awaiting Fernando's separate scientific and architectural implementation acceptance. The 195-test documentation gate passed in 5.86 seconds and all 2,728 plugin-disabled repository tests passed in 222.01 seconds; diff and clean synchronized-tree checks passed.

Do not merge, delete branches, or begin 50S.6G.3B. Preserve the accepted scope and implementation-preflight representation resolution without adding charts, planispheres, report/CLI changes, providers, visibility, illumination, or brightness.

## Accepted 50S.6G.3A implementation boundary

Fernando scientifically and architecturally accepted the complete bounded implementation and authorized merge on 2026-09-19. Preserve the exact-track evidence, accepted scientific composition route, anchors, sampling/failure/identity contracts, timeless collection plus explicit sample UTC, evidence-only layers, semantic family, and fixed-axis coordinate seam.

Only a documentation-first 50S.6G.3B binocular/regional chart-integration audit is authorized next. Do not implement chart integration or begin 50S.6G.4A/B planisphere work without separate acceptance. Do not add report/CLI changes, providers, visibility, illumination, brightness, detector effects, or unrelated refactoring.

## Candidate 50S.6G.3B audit boundary

Read `satellite_binocular_regional_track_audit_50s6g3b.md` before any exact satellite chart-request or regional/binocular integration work. Treat it as a candidate only; do not implement before Fernando separately accepts it.

Preserve already-realized 3A evidence as the sole track truth, matching observer/reference-instant admission, one fixed product-frame transform, request-owned installation and cleanup, independent path/event/label controls, canonical projection/clipping/render/export owners, bounded provenance summaries, and stable exact-visit semantics. Do not add planisphere/all-sky/circumpolar tracks, provider access, report/CLI changes, new execution science, visibility, illumination, brightness, detector effects, or unrelated refactoring.

## Accepted 50S.6G.3B audit boundary

Fernando scientifically and architecturally accepted the audit on 2026-09-19 at `ef58180f62b99423abbb92da56f9ef08dce8c173`; 198 plugin-disabled documentation tests passed in 5.30 seconds and repository checks were clean.

Implement only the explicit already-realized display request, strict admission, fixed-frame realization, request-owned install/cleanup, path/event/label controls, existing-owner appearance and export integration, bounded provenance, stable semantics, focused tests, and required regional/binocular PNG/PDF/semantic-SVG specimens. Do not begin 50S.6G.4A/B or add all-sky/circumpolar tracks, providers, report/CLI changes, new science, visibility, illumination, brightness, detector effects, or unrelated refactoring. Do not merge before separate verification, visual review, and acceptance.

## Candidate 50S.6G.3B implementation boundary

The current candidate implements only the accepted already-realized regional/binocular chart seam: frozen display controls, strict observer/reference admission, one fixed product-frame transform, request-owned cleanup, existing style/detail/projection/render/export composition, bounded provenance, stable exact-visit semantics, focused tests, and deterministic offline specimens.

Treat physically plausible complete-track visual specimens and canonical boundary-clipping tests as complementary evidence. Do not distort a short satellite trajectory merely to show every event marker and a leave/re-enter clipping case in one convex viewport. Do not merge or begin 50S.6G.4A/B before complete verification and Fernando's separate acceptance. Providers, reports, CLI schemas, new execution science, all-sky/circumpolar tracks, visibility, illumination, brightness, and detector effects remain out of scope.

## Candidate 50S.6G.3B implementation verification boundary

Treat executable commit `6580f88ed6e0199d3089e9319d59f6e50d294a29` as a verified candidate awaiting Fernando's separate scientific and architectural implementation acceptance. The 314-test immediate gate passed in 7.71 seconds and all 2,741 plugin-disabled repository tests passed in 228.97 seconds. The deterministic offline physical specimen produced one 65-sample propagated exact visit in regional and binocular PNG, PDF, and semantic SVG; Fernando judged the binocular field consistent and the revised 20 by 16 degree regional context much better. Diff, clean synchronized-tree, and exact-head checks passed.

The coordinate-system guide was reviewed and remains current: this specimen changes no coordinate ownership or meaning. Do not merge, delete branches, or begin 50S.6G.4A/B. Providers, reports, CLI schemas, new execution science, all-sky/circumpolar tracks, visibility, illumination, brightness, and detector effects remain unauthorized.

## Accepted 50S.6G.3B implementation boundary

Fernando scientifically and architecturally accepted the complete bounded implementation and explicitly authorized merge and branch cleanup on 2026-09-19. PR 172 merged the verified candidate into `program/50s-crossing-foundation` at `05d4029aa324eb43c6d1c4017101549a4cd68147`. Executable commit `6580f88` passed 314 immediate tests in 7.71 seconds and all 2,741 plugin-disabled tests in 228.97 seconds; documentation head `ff2e225` passed 199 current-documentation tests in 4.71 seconds. Physical regional/binocular PNG, PDF, and semantic-SVG specimens, diff checks, exact-head checks, and clean synchronized-tree checks passed.

Preserve the already-realized exact-track request boundary, strict observer/reference admission, fixed product-frame realization, request-owned cleanup, independent path/event/label controls, canonical projection/clipping/render/export ownership, bounded provenance, stable exact-visit semantics, and the separation between physical visual specimens and canonical clipping tests.

Only a documentation-first 50S.6G.4A planisphere exact-track audit is authorized next. Do not implement planisphere, all-sky, or circumpolar satellite tracks or add provider access, report/CLI changes, new execution science, visibility, illumination, brightness, detector effects, or unrelated refactoring without later separate acceptance.

## Candidate 50S.6G.4A audit boundary

Read `satellite_stereographic_planisphere_track_audit_50s6g4a.md` before any
polar-planisphere exact-track work. Treat the document as a documentation-only
candidate. It concerns only the paired physical north/south planisphere with
stereographic projection, not the ordinary horizontal full-sky planisphere.

Preserve already-realized 3A evidence, geometric topocentric fixed-axis
meaning, explicit observer/reference admission, event-specific non-recurrence,
intentional face-overlap duplication, existing declination-cap clipping,
longitude continuity, paired lifecycle cleanup, stable semantics, and bounded
provenance. The physical horizon, masks, calendar, and page furniture perform
no satellite visibility science.

Do not implement 50S.6G.4B before Fernando separately accepts this audit. Do
not add ordinary all-sky/circumpolar or equidistant-polar tracks, provider or
report/CLI changes, new execution science, visibility, illumination,
brightness, detector effects, scheduling adapters, 50S.7/50S.8 behavior, or
unrelated refactoring.

## Accepted 50S.6G.4A audit boundary

Fernando scientifically and architecturally accepted the documentation-only
audit on 2026-09-19 at `c1d9015ab18153dc84aba1360edb29fa4f46bf4e`;
all 200 plugin-disabled current-documentation tests passed in 5.29 seconds,
and exact-head, upstream, diff, and clean-tree checks passed.

Implement only the bounded 50S.6G.4B paired stereographic-planisphere
integration and its required north/south PNG, PDF, semantic-SVG, coordinate,
clipping, lifecycle, provenance, state-isolation, and unchanged-output
evidence. Do not add ordinary full-sky/circumpolar or equidistant-polar
tracks, combined-face or pouch-sheet output, provider or report/CLI changes,
new execution science, visibility, illumination, brightness, detector
effects, scheduling adapters, 50S.7/50S.8 behavior, or unrelated refactoring.
Do not merge the implementation before separate verification, physical visual
review, and Fernando's scientific and architectural acceptance.

## Corrective 50S.6G.4A AltAz planisphere boundary

The 2026-09-19 authorization of paired equatorial polar-planisphere work was
based on the wrong product identity and is superseded for 50S.6G.4B. Read
satellite_stereographic_planisphere_track_audit_50s6g4a.md before any further
planisphere satellite-track work.

The corrective candidate concerns only ChartRequest(family="planisphere"):
one zenith-centred FullSkyChart in the horizontal AltAz frame with
stereographic projection and the horizon as its boundary. It authorizes no
implementation until Fernando separately accepts it. Do not continue the
unmerged paired-polar candidate or add circumpolar, Galactic all-sky, provider,
CLI/report, visibility, illumination, brightness, detector, scheduling,
50S.7, or 50S.8 behavior.

## Accepted corrective 50S.6G.4A boundary

Fernando accepted the corrective AltAz planisphere audit on 2026-09-20 at
80855938. Only the bounded corrected 50S.6G.4B ordinary
ChartRequest(family="planisphere") integration is authorized next. Preserve the
existing fixed AltAz request path, horizon boundary, exact-track lifecycle,
semantics, provenance, renderer, and exporters. All paired-polar, circumpolar,
Galactic all-sky, provider, CLI/report, visibility, illumination, brightness,
detector, scheduling, 50S.7, and 50S.8 work remains unauthorized.

## Verified candidate 50S.6G.4B implementation boundary

Treat executable commit `91eafff5` as a verified candidate awaiting Fernando's
separate scientific and architectural acceptance. It changes only ordinary
planisphere admission and adds focused tests plus a physical La Ligua review
tool. The focused 252-test gate and all 2,744 plugin-disabled repository tests
passed; the PNG/PDF/semantic-SVG specimen retained 65 samples and passed visual
review with only a non-blocking specimen-title observation. Do not merge or
begin later satellite work before separate acceptance.

## Accepted complete 50S.6G.4B implementation boundary

Fernando scientifically and architecturally accepted the complete corrected
implementation and authorized merge on 2026-09-20. PR 176 merged final
candidate `6bc623b` at `f0730d8` after 252 focused, 2,744 complete, and 202
final documentation tests plus physical PNG/PDF/semantic-SVG review and clean
repository checks.

Preserve ordinary AltAz planisphere admission, fixed chart-reference-frame
meaning, retained sample UTC, horizon-only clipping, request-owned lifecycle,
semantics, bounded provenance, and canonical export. Only a
documentation-first 50S.6H observatory-planning adapter audit is authorized
next. Do not implement adapters or begin 50S.7+ work without later acceptance.
## Accepted 50S.6H observatory-planning adapter boundary

The documentation-only 50S.6H audit is recorded in
`satellite_observatory_planning_adapter_audit_50s6h.md`. It admits for later
acceptance only an offline, deterministic general planning-advisory JSON
projection downstream of the canonical `ExactSatelliteCrossingReport`.
Paranal vocabulary must remain advisory and non-writing; ELT remains reserved
until ESO publishes a stable operational interface.

Fernando scientifically and architecturally accepted this audit on 2026-09-20.
Only the bounded offline general planning-advisory implementation is authorized
next. Do not add facility network or credential handling, write or mutate an
observatory planning system, make scheduling decisions, translate crossings
into OB time constraints, map ELT operations, or begin 50S.7+ work.
## Accepted 50S.6H offline planning-advisory implementation boundary

The feature candidate implements only the accepted general-profile version 1
offline projection in `satellite_planning_advisories.py`. Preserve frozen
caller-owned planning inputs, exact observer and `field_id` matching,
half-open overlap, planning-unit/report ordering, zero-row validity, strict
canonical JSON, typed stable rejection codes, source report identity, snapshot
identity, and independent advisory identity.

Fernando scientifically and architecturally accepted the implementation on
2026-09-20. Preserve its offline general-profile boundary. Do not add facility
networking or credentials, implement Paranal/ELT profiles, mutate an OB, make a
scheduling decision, or add 50S.7+ runtime.
## Accepted complete 50S.6H implementation boundary

Candidate revision `32dce675` passed 226 focused/documentation and 2,769
complete plugin-disabled tests plus offline positive/zero-row specimen review,
digest, diff, exact-head, upstream, and clean-tree checks. Fernando accepted this evidence on 2026-09-20. After merge, only a
documentation-first 50S.7 illumination and night-geometry audit is authorized
next; no 50S.7 runtime or later work is authorized.

## Candidate 50S.7A illumination and night-geometry audit boundary

Read `satellite_illumination_night_geometry_audit_50s7a.md` before any
satellite illumination or night-geometry work. Treat the audit as a candidate
only; it changes no runtime and authorizes no implementation before Fernando's
separate scientific and architectural acceptance.

Preserve Sunlight, solar Earthshine, Moonlight, and Lunar-Earthshine as four
independent components. Preserve incident geometry/source fields separately
from 50S.8 spacecraft attitude, BRDF, apparent brightness, and 50S.9 detector
effects. The proposed first slice is only finite uniform-Sun/WGS-84 vacuum
occultation, typed shadow state, observer geometric twilight, provenance, and
focused offline validation. Do not implement reflected-light fields,
radiometry, brightness, visibility, detector effects, facility integration,
or scheduling from this candidate audit.

## Accepted 50S.7A illumination and night-geometry audit boundary

Fernando scientifically and architecturally accepted the documentation-only
50S.7A audit on 2026-09-20 at
`fdf7e005a41a5a4d45200f841e914815d37da870`. The final 206 plugin-disabled
current-documentation tests passed in 5.87 seconds, and diff, exact-head,
upstream, and clean-tree checks passed.

After this audit is merged, implement only the bounded 50S.7B direct-Sun and
observer-night geometry slice: immutable output-neutral geometry, finite
uniform-Sun/WGS-84 vacuum Earth occultation, typed shadow state, observer
geometric twilight, complete provenance, and focused offline validation. Do
not begin 50S.7C+, radiometry, solar Earthshine or Lunar-Earthshine fields,
Moonlight radiometry, brightness, visibility, detector effects, facility
integration, scheduling, or unrelated refactoring. Merge and branch deletion
remain separately authorized operations.
## Candidate 50S.7B implementation boundary

Treat `feature/50s7b-direct-sun-night-geometry` as an unaccepted bounded
candidate. Preserve its output-neutral `satellites/illumination.py`
composition over accepted topocentric and ephemeris owners, same-instant ITRS
vectors, uniform finite-Sun/WGS-84 vacuum occultation, converged visible-disk
fraction, typed shadow and twilight states, explicit lunar
`not_evaluated`, failures, and provenance.

Before acceptance require the offline installed-DE440/Skyfield/SPICE receipt,
focused and complete plugin-disabled suites, documentation gate, diff check,
exact head/upstream, and clean tree. Do not implement 50S.7C transition search,
radiometry, Earthshine, Moonlight radiometry, Lunar-Earthshine fields,
brightness, visibility, detector effects, facility integration, scheduling,
or unrelated refactoring. Merge and branch deletion remain separate explicit
decisions.

## Verified candidate 50S.7B review state

Treat executable revision `086e7da1` plus its documentation-only evidence
commits as a verified but unaccepted candidate. The expanded 291-test gate,
208-test documentation gate, clean diff, complete 2,796-test suite, exact
upstream/clean tree, and offline SPICE/Skyfield receipt passed. Do not merge,
delete the branch, or begin 50S.7C+ work without Fernando's separate explicit
decision.

## Accepted 50S.7B implementation boundary

Fernando scientifically and architecturally accepted exact candidate
`054ac53a1f2d50aca06c268cfc7ff5fb074c690f` on 2026-09-21. Preserve its
output-neutral direct-Sun/WGS-84 occultation, bounded adaptive convergence,
same-instant ITRS composition, geometric twilight, typed states, explicit
lunar `not_evaluated`, failures, resource identity, and provenance.

Do not merge PR 181 or delete its branch without separate explicit
instructions. After merge, only a documentation-first 50S.7C
shadow-transition audit is authorized. Do not implement transitions,
radiometry, reflected fields, brightness, visibility, detector effects,
facility integration, scheduling, or unrelated refactoring.

## Candidate 50S.7C shadow-transition audit boundary

Read `satellite_shadow_transition_audit_50s7c.md` before any satellite
shadow-contact or transition-search work. Treat it as a documentation-only
candidate. It proposes observer-independent directed events, continuous
finite-Sun/WGS-84 contact margins, certified UTC brackets, complete bounded
closed-interval search, deterministic identity, terminal failure, and
independent SPICE/Orekit event evidence.

Do not implement 50S.7C before Fernando's separate scientific and
architectural acceptance. Do not use visible-fraction quadrature, fixed-cadence
sign scans, chart samples, or the 50S.5 empirical motion envelope as a
transition-completeness oracle. Do not add radiometry, reflected fields,
brightness, visibility, detector effects, facility integration, scheduling,
or unrelated refactoring.

## Accepted 50S.7C audit boundary

Fernando scientifically and architecturally accepted the documentation-only
50S.7C audit at `030a6322` on 2026-09-21 after 210 plugin-disabled
current-documentation tests passed in 5.81 seconds and repository checks were
clean.

After merge, implement only the bounded observer-independent transition slice
defined in `satellite_shadow_transition_audit_50s7c.md`: continuous
finite-Sun/WGS-84 contact geometry, one selected immutable record and admitted
closed UTC interval, complete bounded search, directed events, certified
brackets, deterministic identity, terminal failure, the minimal shared
geocentric ITRS seam, focused tests, and offline independent event validation.

Do not begin implementation before the audit is merged. Do not attach
transitions to crossings, tracks, reports, charts, CLI, or planning advisories,
and do not add 50S.7D+ radiometry or reflected fields, brightness, visibility,
detector effects, facility integration, scheduling, or unrelated refactoring.
PR merge and branch deletion remain separate explicit decisions.

## Candidate 50S.7C implementation boundary

Treat `feature/50s7c-shadow-transitions` at executable `69375fab` plus later
documentation-only evidence as an unaccepted bounded candidate. Preserve the
single-record observer-independent query, continuous finite-Sun/WGS-84
contact margins, shared geocentric ITRS seam, complete bounded recursive
search, directed adjacent events, certified brackets, deterministic identity,
and typed terminal failures.

The 58-test focused gate and offline SPICE `gfoclt`/Skyfield receipt passed.
Before review require the current-documentation gate, expanded focused gate,
complete plugin-disabled suite, diff check, exact upstream, and clean tree.
Do not attach events to crossings, tracks, reports, charts, CLI, or planning;
do not begin 50S.7D+, radiometry, reflected fields, brightness, visibility,
detector, facility, scheduling, or unrelated refactoring. Merge and branch
deletion remain separate explicit decisions.

## Verified candidate 50S.7C review state

Treat exact candidate `bf877404` plus this documentation-only gate record as
verified but unaccepted. The 311-test expanded gate passed in 21.47 seconds,
the 212-test documentation gate passed in 7.01 seconds, the clean diff passed,
and all 2,816 plugin-disabled repository tests passed in 218.58 seconds. Exact
upstream equality, clean tree, and the independent SPICE/Skyfield receipt were
also confirmed.

Do not merge or delete the feature branch without Fernando's separate explicit
instruction. Do not begin 50S.7D+, attach transitions to outputs, or add
radiometry, reflected fields, brightness, visibility, detector, facility,
scheduling, or unrelated work before separate authorization.

## Accepted 50S.7C implementation boundary

Fernando scientifically and architecturally accepted exact branch head
`eaeab6085b52bfed6136d37f3010c2f353e59f53` on 2026-09-21. Executable
`bf877404` passed the independent SPICE/Skyfield receipt, 311 expanded
tests, 212 current-documentation tests, all 2,816 plugin-disabled repository
tests, clean diff, exact upstream, and clean-tree checks. The final
documentation-only clarification passed 212 tests in 4.72 seconds.

Preserve the single-record observer-independent query, continuous
finite-Sun/WGS-84 contact margins, shared geocentric ITRS seam, complete
bounded search, six directed adjacent events, certified brackets,
deterministic identity, complete provenance, and typed terminal failures.

Do not merge PR 183 or delete its feature branch without Fernando's separate
explicit instruction. Do not begin 50S.7D+, attach transitions to outputs, or
add radiometry, reflected fields, brightness, visibility, detector, facility,
scheduling, or unrelated work before a separately accepted bounded milestone.
## Candidate 50S.7D direct-source radiometry audit boundary

Read `satellite_direct_source_radiometry_audit_50s7d.md` before any incident
solar or lunar radiometry work. Treat it as a documentation-only candidate.
It retains both direct sources within 50S.7D but proposes only a bounded
solar-first 50S.7D.1 implementation after separate acceptance: IAU 2015
nominal bolometric normal-plane irradiance, inverse-square distance scaling,
and the accepted uniform-disk visible fraction.

Do not implement 50S.7D before Fernando's separate scientific and
architectural acceptance. Do not describe the exact nominal constant as zero
physical uncertainty, encode unknown Moonlight as zero, or add spectral
resources, lunar coefficients, attitude, surfaces, BRDF, magnitude, outputs,
visibility, detector, facility, scheduling, or unrelated behavior.

The audit authorizes no runtime. 50S.7D.2+, 50S.7E+, merge, and branch deletion
remain separate explicit decisions.

## Accepted 50S.7D audit boundary

Fernando scientifically and architecturally accepted the documentation-only
50S.7D direct-source radiometry audit on 2026-09-21 at exact candidate
`362199d04bd917741a8be88f20608967af75530e`. All 214 plugin-disabled
current-documentation tests passed in 7.00 seconds, and diff, exact-head,
upstream, and clean-tree checks passed.

After this audit is merged, implement only the bounded 50S.7D.1 direct-Sun
bolometric normal-plane irradiance slice in the existing illumination owner:
the IAU 2015 nominal `1361 W m-2` value at 1 au, inverse-square
Sun-satellite distance scaling, accepted uniform-disk visible fraction,
immutable identity and provenance, explicit physical/model uncertainty
`not_evaluated`, focused tests, and offline independent recomputation.

Do not begin implementation before the audit is merged. Do not add spectral
Sunlight, numeric Moonlight, Earth-reflected fields, component bundling,
spacecraft attitude or surfaces, BRDF, magnitude, visibility, detector,
report/chart/CLI/planning integration, facility behavior, scheduling, or
unrelated refactoring. 50S.7D.2+, 50S.7E+, PR merge, and branch deletion
remain separate explicit decisions.

## Candidate 50S.7D.1 implementation boundary

Treat executable `4b5f8e6925f88df38a2923c057f4d039328e3d2b` plus later
documentation-only evidence as an unaccepted bounded candidate. Preserve its
immutable IAU-nominal bolometric normal-plane policy/result/evaluator,
inverse-square distance scaling, accepted uniform-disk fraction composition,
complete geometry identity, numerical convergence evidence, explicit
physical/model uncertainty `not_evaluated`, typed failures, focused tests, and
offline independent recomputation.

The 86-test illumination/ephemeris gate passed. Before review require the
installed DE440/IERS no-download receipt, current-documentation and package-
boundary gates, complete plugin-disabled Mac suite, diff check, exact upstream,
and clean tree. Do not add spectral Sunlight, Moonlight, reflected fields,
component bundles, surface response, brightness, visibility, detector,
output, facility, scheduling, or unrelated refactoring. Merge and branch
deletion remain separate explicit decisions.

## Verified candidate 50S.7D.1 review state

Treat exact branch head `5bf5d52e81670f1a69af0476283195d12a3119bc` as verified but
unaccepted. The installed-resource no-download receipt produced all nine
sunlit/penumbral/umbral LEO/MEO/GEO cases with zero clear and incident
irradiance residuals; its SHA-256 is
`43037267cd841232dcffca05797a2d55dce3d90b9caf8b84fbf785b19129fc73`.
The 308-test expanded gate passed in 24.79 seconds and the complete 2,832-test
plugin-disabled suite passed in 236.81 seconds. Diff, exact upstream, and clean
tree checks passed.

Do not merge or delete the feature branch without Fernando's separate explicit
instruction. Do not begin 50S.7D.2+, reflected fields, spacecraft response,
brightness, visibility, detector, output, facility, scheduling, or unrelated
work before separate acceptance and authorization.
