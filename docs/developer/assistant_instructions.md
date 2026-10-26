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
3. Perform the as-is assessment, identify the agreed roadmap submilestone ID,
   and implement only that bounded item under the roadmap-control rules below.
4. Before creating/updating a remote task branch, confirm Fernando's Mac is
   clean and synchronized with the exact agreed base. Uncommitted local work
   is invisible until Fernando reports or publishes it.

## Roadmap control: mandatory before implementation

The [active roadmap](kernel_roadmap_v0.9.5.md) is the single authoritative plan.
Follow its scope, dependencies, agreed sequence and intermediate milestone ledger
strictly. A status of pending records agreed scope; it does not authorize the
agent to activate the whole backlog. Before a task, state its existing ID,
intended result, scope limits, prerequisites and smallest acceptance gate.
A general "proceed" applies to the bounded milestone just discussed, not to
unmentioned additional milestones. If the next item/order has not been selected,
propose it explicitly rather than choosing or rewriting the order silently.

If an extra item, unlisted prerequisite, scope expansion, changed scientific
policy, new package/capability or change of agreed order is needed:

1. Stop the affected implementation. Read-only assessment may continue.
2. Discuss the concrete proposal with Fernando: why it is needed, which existing
   milestone it affects, alternatives, compatibility/scientific consequences,
   dependencies and the proposed acceptance gate.
3. Obtain Fernando's explicit agreement. Do not infer it from a prior broad
   migration approval or a passing test. Mark an unresolved proposal as proposed,
   never agreed or next.
4. Document the agreed change, its stable ID, scope, order/dependencies,
   acceptance criteria and agreement reference in the roadmap **before** starting
   the additional implementation. Update linked contracts/inventory if affected.
5. Proceed only within that newly agreed, documented boundary.

Routine implementation choices and necessary fixes that remain inside the
already agreed milestone do not create an extra milestone or require repeated
permission. They still preserve its limits and receive appropriate verification.
Do not disguise extra science or architectural work as such a choice. Further
roadmap subdivisions that alter deliverables/order follow the same discussion,
agreement and documentation rule; no hidden intermediate work queue is allowed.

Keep completed, partial, pending, optional/proposed and excluded work distinct.
Record the tested commit/PR and limitations when closing a bounded item. A
partial slice cannot close its parent, and a proposed or optional item is not a
new prerequisite for migration closure. Do not silently promote the positional
extension to a mandatory predecessor of the remaining K3 baseline migration.
Update the current-position/next-item fields after acceptance; publishing a plan
change is not itself user agreement to implement it. This roadmap/instruction
update does not itself authorize new runtime work.

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
The agreed kernel is a modular shared-service layer, including state/time/resource
services, generic coordinate/observer realization, spherical geometry/topology,
domain guards, projections and projected geometry. The separately installed
state SDK is one implemented component, not the whole target kernel. Follow the
[agreed service boundary](kernel_roadmap_v0.9.5.md#proposed-architecture).
Every consumer must use its appropriate shared service/domain interface before
closure, with temporary adapters allowed. Geometry consumers may call public
geometry services directly; do not force contours, grids or projections through
object-state queries or invent physical objects per vertex. Reuse existing
geometry/projection interfaces first. A new geometry-query protocol requires a
demonstrated need and the normal explicit scope agreement. Keep astronomical
source/model knowledge, product policy and renderer implementations outside
generic kernel services. Internal components remain independently testable;
conceptual ownership does not mandate one class/wheel or eager dependencies.
Extract one independently installable package at a time after that closure. Do not silently reclassify old snapshots as kernel states.

Revision 32 orders KG.01–KG.05 geometry-service assessment/contracts/migration
and acceptance before KG.06 completed-K audit and KG.07 demonstrated corrections,
then K3.16. Follow the roadmap's KG ledger; do not resume diffuse runtime work
or presume prior migrations compliant before those prerequisites are accepted.
Audit actual implementations and preserve prior receipts only where applicable.
This sequence agreement is not blanket execution authority for every KG item.

## Scientific and provider work

Catalogue facts (reference epoch/time scale, frame, centre, units, edition and
provenance) belong to validated source metadata, preserved in a standard Wenu
catalogue representation and mirrored in its runtime record. Consumers must
read that record. Do not duplicate catalogue-specific literals or infer missing
metadata from a name, filename or another catalogue. Validate before publication;
preserve original source fields and bind metadata to source bytes. Mathematical
definitions, supported schema identifiers and explicit model policies remain
software contracts. See the metadata audit in `kernel_migration_audit_v1.md`.

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

### Mac terminal guard

Fernando also works on the separate wenu-imaging project on Linux host
chapman3 and may paste a Wenu command block into that terminal. Every command
block intended for his Mac, including read-only diagnostics, tests, Git and
acceptance commands, must start with a Darwin check before changing directory
or executing any other operation. Use an explicit nonzero exit rather than a
Python assert, which optimization can disable:

```bash
python -c 'import platform,sys; sys.exit(0 if platform.system() == "Darwin" else "STOP: run this in your Mac terminal, not chapman3.")' &&
cd /Users/fselman/Developer/wenu &&
git status -sb
```

Chain every subsequent dependent command with `&&` (including the final
Python heredoc invocation), or use an equivalent shell structure that aborts
the entire block on guard failure. A standalone check followed by independently
executed lines is insufficient. Missing Python must also stop the block.
Retain the exact repository path and applicable branch, SHA, clean-state and
upstream checks after the platform check. Do not rely only on the visible
terminal prompt. Do not change files, install software or attempt to repair the
Linux environment when this guard refuses. Commands explicitly requested for
Linux wenu-imaging belong to that separate project and must not be relabelled
as Mac Wenu commands.

Downloadable outputs require explicit `_v1`, `_v2`, etc. names, incremented
when contents change; commands must reference exact filenames. Preserve
review pairs and avoid overwrite. Temporary scripts, patch artifacts,
generated charts and unrelated notebooks do not belong in the repository.
Ordinary examples express requests; they do not implement catalogue joins,
projection, renderer dispatch, legends or repeated saving.


## Build, test and output locations and provenance

Fernando established this convention on 2026-10-26, consistent with his parallel
wenu-imaging work. Keep Wenu work separate from wenu-imaging. Use
`~/Software/build/wenu/build/`, `~/Software/build/wenu/test/` and
`~/Software/build/wenu/output/` for new build, test and generated-output runs;
use a purpose-specific run directory within the appropriate location. Do not
create output/build/test directories directly in the Mac home directory, use
`~/wenu-output` for new work, or put generated artifacts in the repository.
The active source checkout remains `/Users/fselman/Developer/wenu`.

Every new build, test or generated-output run directory must contain a
consistently named `run-provenance.json`, created before the run starts and
updated on completion or failure. Record:

- Repository identity, branch and exact source commit SHA.
- Whether the source had uncommitted changes (and the observed status).
- Purpose, creation time with time zone, host and exact commands.
- Inputs, outputs and links to related run directories.
- Status: `running`, `passed`, `failed` or `incomplete`.
- Retention role: `disposable`, `acceptance evidence` or `active installation`.

Use JSON null or an explicit unknown value for facts that cannot be recovered;
never infer an exact branch, commit, clean state or input identity from a folder
name. Preserve source identifiers/hashes and the provenance record with retained
evidence. Failed or interrupted runs must not retain a misleading passed status.
Apply this convention to subsequent assistant commands and delivered run recipes.
It is an operational rule, not a new astronomical model or source-snapshot schema.

A merged branch alone never makes a directory safe to delete. Before cleanup,
check that it contains no unique input/data or required acceptance evidence,
supplies no selected executable or active installation, and has no active
consumers. Preserve dependencies referenced by retained runs. Existing directories
receive records only where provenance can be recovered; unknown fields remain
explicitly unknown. Inspect existing `~/wenu-output` content and retention needs
before relocation/cleanup; do not delete, overwrite or relabel those results as
a new run merely to tidy the home directory.
