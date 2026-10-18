# Wenu assistant instructions

**Current procedure:** consolidated 2026-10-17. The previous full edition and
its chronological authorizations are preserved in the
[baseline archive](archive/pre_kernel_20261017/docs/developer/assistant_instructions.md).
User instructions take precedence; history is evidence, not a current task queue.

## Before work

1. Use GitHub `fselman/wenu` as source of truth. Establish branch and exact SHA;
   inspect the implementation and tests rather than reconstructing from memory.
2. Read [the developer index](README.md), [current architecture](current_architecture_v0.9.md),
   [source map](source_tree.md), [API reference](implementation_reference.md),
   [scientific contracts](scientific_contracts.md), [testing policy](testing_policy.md)
   and the [active roadmap](kernel_roadmap_v0.9.5.md). Read relevant scientific
   guide sections; archive material only for necessary detail/provenance.
3. Perform the as-is assessment and implement the smallest authorized milestone.
4. Before creating/updating a remote task branch, confirm Fernando's Mac is
   clean and synchronized with the exact agreed base. Uncommitted local work
   is invisible until Fernando reports or publishes it.

## Architecture

Preserve the canonical catalogue/provider → spherical → domain guard →
projection → projected → preparation → renderer → furniture/export flow.
`CelestialSphere.draw_chart()` remains the current core until an explicitly
accepted migration changes ownership. No alternate scientific/render pipeline.

Keep chart type, content/detail, style, mode and furniture independent.
Styles/modes do not alter geometry. Avoid mutable cross-request state.
Projection alignment is not an astronomical frame transform. Preserve public
APIs and accepted atlas-print appearance unless the bounded task changes them.

The standalone K2 foundation is a separate candidate under `packages/wenu_kernel`.
Native stellar realization is accepted through PR #247. Public native stellar
positions and constellation endpoints extend that adapter; other kernel
routing, Gaia DR3 and astronomical package extraction remain planned. Run the
core's explicit independent gate only when its implementation/contracts change;
root pytest discovery intentionally remains scoped to the existing `tests` owner.
Every existing functionality must use the kernel before kernel closure, with
temporary adapters allowed. Extract one independently installable package at
a time after that closure. Do not silently reclassify old snapshots as kernel states.

## Scientific and provider work

Preserve the [current scientific invariants and unresolved limits](scientific_contracts.md).
Review/update the coordinate guide whenever meaning, ownership or provenance
changes; otherwise record that it remains current. Validate scientific,
visual, print and classroom results separately where relevant.

Before choosing an automated provider route, batching, concurrency, retry,
cache or redistribution behavior, check current primary-source API/terms,
fair-use/licensing rules and record date/URLs. Treat limits as hard constraints.
Prefer explicit supported batching, deduplication, validated caching and small
queries; respect throttling/backoff. Do not evade restrictions or invent
permissions. When a policy is unclear or unreachable, keep acquisition
conservative and unresolved. A passing test does not establish permission.
Acquisition stays outside deterministic rendering and numerical test execution.

Frozen real provider fixtures must be exact captured bytes with provenance;
constructed fixtures must be labelled synthetic. Do not claim an unrun
oracle, download, scientific model or external execution as accepted evidence.
Paused Moonlight and consumed external run authorities remain paused/consumed.

## Code placement and tests

Organize code by enduring responsibility, dependency direction, lifecycle,
provenance and failure boundary. Extend an existing owner when those match;
add a module/package only when a real boundary requires it. Do not split by
milestone number, first object, CLI flag or file size. No domain dumping into
`utils`, copied body-specific orchestration or automatic top-level exports.

Use [focused owner and contract gates](testing_policy.md); do not repeatedly
run unrelated suites. A composition of tested services needs seam/failure and
isolation evidence, not duplicated lower-level proofs. Retain independent
numerical oracles, cold-start/public-path coverage and meaningful markers.

After final edits, execute the closest tests in the current environment.
Verify new imported names/signatures/fields against actual definitions.
If Wenu cannot run here, compile/inspect explicitly, state the limitation and
give the smallest complete Mac command. Fix a focused failure and rerun that
same gate before broadening. Never call written/unexecuted tests passing.
Fault injection must demonstrably change its baseline.

Use `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. Add tests to the existing owner file;
new files require an enduring responsibility, not a milestone name. State
the protected fault and closest existing test before adding coverage.
Final production integration and documentation-only exceptions follow the
testing policy. Future independent-module gates become effective only when
their isolation has been demonstrated and accepted.

## Documentation

Keep one current source for each responsibility; replace stale status rather
than appending candidate/accepted diaries. Move completed/superseded material
to `archive`, preserve provenance and update active links in the same change.
Keep incomplete scientific contracts discoverable in `scientific_contracts.md`.
Keep the roadmap separate from as-built implementation claims.

Documentation preflight checks the developer-root allowlist, active indexes,
relative Markdown links/anchors, source inventory and archives as one unit.
Inspect affected documentation tests before moving/rewording files. Test
operational contracts and integrity, not historical acceptance phrases in
current documents. Verify resulting remote contents, not merely intended edits.
Do not hand a known-broken documentation branch to Fernando.

## Delivery

Use a dedicated GitHub branch after an authorized bounded milestone; commit
verified work and open/update a PR. No direct `main` writes, force pushes,
merges or branch deletion without the corresponding explicit user instruction.
When a merge is authorized and its gates pass, do not request permission again.

Use the GitHub connector for repository inspection/delivery. Never ask Fernando
to copy/edit source files or run file-editing commands on the assistant's behalf.
If direct GitHub access fails, stop and explain; only then use a requested or
necessary versioned ZIP fallback. A ZIP must contain one named patch folder,
manifest, exact base, checksums and an idempotent apply script that verifies
base/clean state, preserves uncommitted work and fails on mismatch. Do not
create nested Finder-dependent patch paths or ask for manual file merging.

Give Mac commands completely, copy/paste ready, one group at a time, then wait
for the result. Confirm exact branch/SHA, clean state and upstream equality.
Do not delete an old branch merely because a new task starts.

Downloadable outputs require explicit `_v1`, `_v2`, etc. names, incremented
when contents change; commands must reference exact filenames. Preserve
review pairs and avoid overwrite. Temporary scripts, patch artifacts,
generated charts and unrelated notebooks do not belong in the repository.
Ordinary examples express requests; they do not implement catalogue joins,
projection, renderer dispatch, legends or repeated saving.
