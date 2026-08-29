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
- `coordinate_transformation_audit_09a2afd.md` for the as-is coordinate
  evidence that motivates that target;
- `public_interface_audit_v0.9.5.md` for public examples, tools, coordinate
  system, frame, equinox, or epoch interface work;
- `celestial_scene_dependency_audit_49d1.md` for celestial-background,
  moving-object, observer-local, product-frame, planet, Moon, or scene-reuse
  dependency work;
- `layer_realization_context_49d2.md` for the optional pre-projection layer
  context, compatibility dispatch, or controlled-provider integration point;
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

When several rendering solutions work, choose the simplest one that preserves
the established visual hierarchy and scientific meaning.

## Communication

Before an architectural change, explain its reasoning, tradeoffs, and expected
benefit. If the implementation does not clearly support a requested change,
inspect further and ask for clarification when the choice would materially
alter the result. Never guess.
