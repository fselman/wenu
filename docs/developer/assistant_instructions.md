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

For the v0.6 migration, read and follow:

- `current_architecture_v0.5.md` as the implemented baseline;
- `target_architecture_v0.6.md` as the proposed target;
- `wenu_migration_0.5_to_0.6.md` as the active roadmap;
- `implementation_reference.md` for current public and internal APIs;
- `source_tree.md` for package responsibilities;
- `target_architecture_v0.5.md`, `current_architecture_v0.4.md`, and
  `wenu_migration_0.4_to_0.5.md` as completed migration history.

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

When handing changes to the user on macOS, provide a ZIP containing one
same-named folder with:

- `README.md`;
- one `.patch` file.

The README must state the exact base commit and give commands to:

1. verify clean status, branch, and commit;
2. run `git apply --check` before `git apply`;
3. inspect status, diff, diff stat, and `git diff --check`;
4. compile changed Python files;
5. run focused, related, and full tests;
6. stage each intended file explicitly;
7. inspect the cached diff and run `git diff --cached --check`;
8. commit, push, and verify final status and log.

Use `$HOME/Downloads/<folder>/<patch>.patch`. Safari/Finder may already have
expanded the ZIP; do not require an unnecessary manual unzip step.

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
