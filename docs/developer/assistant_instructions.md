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

For the active v0.9 migration, read and follow:

- `current_architecture_v0.8.md` as the implemented baseline;
- `target_architecture_v0.9.md` as the proposed target;
- `wenu_migration_0.8_to_0.9.md` as the active roadmap;
- `target_architecture_v0.8.md` as the implemented architecture;
- `wenu_migration_0.7_to_0.8.md` as the completed roadmap;
- `implementation_reference.md` as the current API reference;
- `source_tree.md` as the current responsibility map;
- `coordinate_transformation_audit_09a2afd.md` for coordinate, frame, time,
  observer, astrometry, planet, or satellite work;
- `post_v0.9_architecture_roadmap.md` for accepted future coordinate, SVG,
  temporal-sequence, animation, planet, or satellite direction.

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

## Git and Mac patch handoff

Assume development occurs on the active branch; never guess its name or base
commit. Do not commit or push on the user's behalf unless explicitly asked.

Every modification handed to the user must be delivered as a ZIP containing
one same-named folder with exactly the handoff files needed to apply it:

- `README.md`;
- one `.patch` file.

The ZIP layout must ensure that double-clicking it in macOS Finder creates the
same-named subdirectory rather than placing loose files in `Downloads`.

The README must state the exact base commit and present commands in this
order:

1. verify clean status, branch, and commit;
2. run `git apply --check` and only then the separate `git apply` command;
3. compile every changed Python file when compilation is relevant;
4. run the limited or focused test set when one is relevant;
5. run the general test suite;
6. inspect `git status`, the diff, diff stat, and `git diff --check`, stage
   every intended file explicitly, then inspect the cached diff and run
   `git diff --cached --check`;
7. commit, push, and verify the final status and log to close the milestone.

Keep inspection practical for long patches. Before staging, run:

```bash
git status --short
git diff --name-status
git diff --stat
git diff --check
```

Verify that only the intended files appear, that the change sizes are
plausible, and that `git diff --check` is silent. Inspect substantive code one
file at a time with `git diff -- path/to/file`; use `q` to leave the pager.

After staging every intended file explicitly, run:

```bash
git status --short
git diff --cached --name-status
git diff --cached --stat
git diff --cached --check
git diff --quiet
echo $?
```

The first status column must show the intended staged `M` or `A` entries,
`git diff --cached --check` must be silent, and the final result must be `0`,
proving that no unstaged changes remain. `git diff --cached` remains available
for full inspection of exactly what the next commit will contain, but a
handoff must not require rereading a very long undifferentiated diff when the
name, status, size, whitespace, and substantive-file checks are sufficient.

Do not combine the apply check and application into one shell command. Keep
the limited and general test commands separate so their results can be
reported independently. Omit compilation or limited-test sections only when
they are genuinely irrelevant, and state that explicitly in the README.

Use `$HOME/Downloads/<folder>/<patch>.patch`. Safari/Finder may already have
expanded the ZIP; do not require an unnecessary manual unzip step.
In every patch handoff, also give Fernando the complete macOS path beginning
with `/Users/fselman/Downloads/`; never leave `/path/to`, `/full/path`, or only
the patch filename for him to resolve.

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
