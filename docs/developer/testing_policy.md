# Testing policy and module independence

**Current policy consolidated:** 2026-10-17. The kernel isolation rules below
are release acceptance requirements, not a claim that current Wenu satisfies them.

## Current development

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

## Required target after the kernel is frozen

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
operational checks are retained or replaced explicitly; scientific and product
test files are unchanged. See the [cleanup ledger](documentation_cleanup_v1.json).
