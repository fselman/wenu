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
- `post_v0.9_architecture_roadmap.md` for active coordinate, SVG,
  temporal-sequence, animation, planet, or satellite direction;
- `archive/milestone_history/49f_svg/svg_output_audit_and_plan.md` for SVG product, font, verification,
  constellation-artwork, or 2D/3D-boundary work.

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
- pass focused and full tests;
- leave the project usable;
- avoid unrelated refactoring, cleanup, or formatting.

Every medium or major milestone must review
`coordinate_system_guide_v0.9.5.md`. Update it when scientific meaning,
implementation ownership, object provenance, or the public coordinate
explanation changes; otherwise record that it was reviewed and remains
current. Automated documentation checks do not replace Fernando's scientific
and pedagogical review.

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
`performance_and_closure_audit_49j0.md`. Keep the reusable-sphere diagnostic
separate from a cold independent-frame oracle, report exclusive wall-time spans
separately from overlapping profiler totals, and preserve
`generate_chart_request()` as the complete-render correctness route. Do not
add caching or optimization under 49J.0.
