# Testing policy and module independence

**Current policy consolidated:** 2026-10-18. The kernel isolation rules below
are release acceptance requirements, not a claim that current Wenu satisfies them.

## Current development

The new `packages/wenu_kernel` project has an explicit standard-library owner
gate, shared synthetic-provider checks and an installed-wheel isolation gate;
see its [selection manifest](../../packages/wenu_kernel/test_selection_v1.json).
Root `pytest` defaults to the existing `tests` directory, so adding an
independent project does not silently enlarge the legacy full suite. Explicit
test paths remain supported. No legacy numerical/visual test is removed.
The K2 foundation changes no existing runtime dependency or product import;
its review gate is the isolated core plus affected documentation/inventory.
This scoped exception does not waive full integration for K3 production routing.

The direction-reuse candidate extends the same isolated owner gate. Its tests
cover provider-supplied total bounds, closed interval/one-ULP boundaries,
whole-interval requests, retained original error/anchor, tighter tolerances,
corrupt envelopes, atomic cache publication, mixed-rate updates and explicit
reproducible full-model fallback. They use constructed circular-motion fixtures,
not scientific accuracy evidence for Gaia or any real catalogue. No legacy test
is moved or removed; the existing missing-tolerance case now expects
`InvalidQuery` because bounded reuse is an implemented policy requiring a bound.

Run the smallest owner suite plus directly affected contract/seam tests.
Use `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; add no ambient plugin dependency.
During iteration, do not run unrelated scientific, projection or rendering
tests merely because they are in the repository.

A final production integration candidate still requires one complete suite
until the corresponding independent-module contract gates have been accepted.
Reuse a receipt when executable code, scientific fixtures, dependencies,
configuration, packaging and non-documentation tests are unchanged. Record
exact tested and delivered revisions and prove equivalence of relevant content.

Documentation-only cleanup, including documentation-contract tests, uses the
affected documentation and integrity gates. It does not rerun the scientific
or graphical suite when those owners and their test collection are unchanged.
The accepted `ea8dc505`/`6708f54a` receipt remains production evidence, not a
claim about a future changed production tree.

## Continuous migration and independent-module gates

Test reorganization starts with each implementation slice, not after the
freeze. The [as-is audit and functionality ledger](kernel_migration_audit_v1.md)
and [pinned file inventory](kernel_migration_inventory_v1.json) are the starting
point. Maintain them as owners migrate; a new source, command or test must not
silently escape the ledger. Baseline hashes remain historical evidence.

Classify tests on three independent axes: enduring owner, boundary level
(unit, provider conformance, immediate seam, installed product/release) and
cost/evidence (numerical, integration, visual, slow). Markers alone do not
provide dependency isolation. Pure validation tests must not require graphics
or another provider merely to collect. Keep domain fixtures with their owner;
share contract fixtures through the core conformance kit and use explicit
helpers rather than importing another test module.

For each owner extraction, record old-to-new test node IDs, protected faults,
independent oracle/resource provenance and fixture/import changes. Preserve
assertions or justify their replacement. Do not reduce a parametrized render
matrix until its actual interactions and measured cost are understood. Keep
representative real public paths and meaningful cross-option interactions.

Selection must follow semantic dependency direction, not only textual imports
or changed filenames. Each isolated package publishes an executable gate and
a selection manifest: changed owner, affected contracts/consumers, required
suites, excluded suites and rationale. A shared SDK semantic change, backend
upgrade, common fixture/resource schema, build change or unknown ownership
requires impact review and the corresponding consumer seams. A test cannot
be skipped merely because its file is outside the changed directory.

Prove installation, import, collection and execution with unrelated providers
absent. Until that owner's independent gate has been demonstrated and accepted,
the existing final production integration requirement remains in force.
Profile selected gates with `--durations`, separating collection, cold source
loading and warm work. No speed target is inferred from static file counts.

An internal change in package A, preserving the accepted public contract,
requires package A's tests and its kernel conformance tests. It must not
require running or installing package B, C, or product/rendering suites.
These are executable isolation gates, not a convention based on folder names.

| Change | Required owning verification | Unrelated suites |
|---|---|---|
| Documentation | Links, syntax, inventory and archival integrity | None |
| New appearance preset | Preset resource and shared loader contract | No astrometry/orbit tests |
| Star-provider implementation | Stellar physics plus kernel conformance | No galaxy/asteroid/satellite suites |
| Galaxy-provider implementation | Galaxy state plus kernel conformance | No stellar or moving-body suites |
| Projection | Geometry/projection contract and its immediate consumer | No catalogue acquisition/propagation suites |
| Atlas composition | Atlas/chart public contract and book outputs | No provider internal suites |
| Kernel contract or shared dependency change | Explicit affected-consumer matrix and integration evidence | Expand only for actual impact |

Release-level composition checks may test installed combinations. They are
owned by the integration/release layer and are not a hidden prerequisite for
every independently compatible package change. Cross-domain integration
remains necessary when the shared contract itself changes; that is a separately
reviewed kernel version change, not ordinary package maintenance.

## Faults the contract gates must detect

- Core importing concrete providers or graphics; one provider importing another.
- Importing/loading stars requiring planet, galaxy or satellite dependencies.
- In-place mutation of snapshots, metadata or cached state.
- A changed observer invalidating unrelated physical catalogue states.
- Updating stars reevaluating the unchanged galaxy provider.
- Stale dependent star-connected constellation geometry after propagation.
- Provider unload/resource-close failure leaking state into another request.
- A provider returning an unsupported frame/status/time combination or hiding
  absent parallax, velocity, coverage or uncertainty as zero.
- A product bypassing the kernel to call an old position source.

Use synthetic/fake providers with call counts and fault injection for these
barriers. Keep independent numerical science oracles in their owning packages.
Keep cold-start, order-independence, public-path, offline-resource and
scientific fault coverage; speed is not a reason to replace them with mocks.

## Documentation checks

Tests protect navigable active links, valid Python examples, public imports,
complete source ownership, current CLI/configuration documentation and the
exact preservation of archived editions. Do not require historical acceptance
sentences, elapsed times or obsolete plans to remain in active guides.

The old 238-test documentation diary is preserved byte-for-byte in the
[baseline archive](archive/pre_kernel_20261017/tests/test_current_documentation.py.txt).
Its historical assertions are not collected as a current test suite. Current
operational checks are retained or replaced explicitly. The subsequent audit
repairs stale user-guide/fixed-sky documentation tests and preserves their
original editions in its inventory; scientific and product test files remain
unchanged. See the [cleanup ledger](documentation_cleanup_v1.json).
