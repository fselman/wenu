# Exact comet name resolution audit (Milestone 50A.5D.2A)

**Status:** Accepted by Fernando on 2026-09-13

**Base:** `32e1fe2cf86ff9e29d64869c0904a9e5cbd0614e`

## Decision requested

Authorize only an exact, typed comet-identity resolver that can reuse an
installed alias or resolve one uninstalled comet against NASA/JPL SBDB. This
slice does not acquire an SPK, publish a cache entry, build a chart, evaluate
magnitude, or authorize the remaining 50A.5D.2 acquisition work.

## As-is assessment

`MinorBodyResourceCollection` already normalizes case and surrounding/internal
whitespace, derives exact aliases from verified manifests, resolves `2P`,
`2P/Encke`, and `Encke` to one installed comet, and keeps `2P` distinct
from asteroid `2`. That installed-resource authority remains unchanged.

`minor_body_acquisition.py` accepts only positive permanent asteroid numbers.
Its SBDB/Horizons identity parsing, cache locking, atomic publication, and
type-21 validation are asteroid-specific today. The accepted discovery command
returns a set selected by perihelion constraints; it is not an exact-identity
resolver.

The missing seam is therefore provider-backed exact comet identity before any
acquisition begins.

## Bounded public contract

The candidate implementation adds a library boundary equivalent to:

```python
resolve_comet_identity(
    selection,
    *,
    installed_collection=None,
    fetch=provider_fetch,
) -> ResolvedCometIdentity
```

This is not initially a new public console command. The later generic preflight
will call it before requesting Horizons data.

The immutable result retains:

- the original selection and its normalized comparison form;
- canonical comet designation, primary designation, prefix, permanent number
  when present, fragment when present, and official name when present;
- exact accepted aliases;
- SBDB SPK-ID, orbit class, orbit solution ID, provider identity/version,
  exact request parameters, retrieval instant, and raw-response SHA-256;
- whether resolution came from an installed verified manifest or a live
  provider response.

The result carries identity and provenance only. It carries no open kernel,
ephemeris state, apparent direction, magnitude estimate, cache path, or
rendering object.

## Normalization and exactness

Comparison is Unicode-string case-folded after trimming and collapsing
whitespace. Normalization does not discard or reinterpret `P`, `D`, `I`,
`C`, `X`, or `A`; slashes; fragment suffixes; permanent numbers; or the
words in an official name.

Examples:

- `10P`, `10p`, and `  10P  ` have the same comparison form;
- `10P/Tempel 2` may resolve to the same identity as `10P`;
- an exact installed or provider alias such as `Tempel 2` may resolve;
- `Tempel` is not an exact alias and must never select a candidate;
- `10` is not `10P` and must never be interpreted as that comet;
- `73P` and `73P-B` are different selections unless the provider identity
  explicitly proves an exact alias relationship.

The resolver never uses substring, prefix, fuzzy, popularity, nearest-name, or
first-result matching.

## Resolution order

1. Validate and normalize the non-empty selection.
2. If an installed `MinorBodyResourceCollection` resolves an exact alias,
   return identity derived from that verified manifest without network access.
3. Otherwise issue one deliberate exact SBDB identity request.
4. Validate the API signature, fixed response schema, and every returned
   candidate before matching.
5. Construct each candidate's complete exact alias set from provider fields.
6. Return only when exactly one candidate contains the normalized selection in
   its exact alias set.
7. Fail closed when there are zero exact matches or more than one exact match.

A broad provider search may return suggestions, but suggestions are evidence
for an error, not permission to guess. Error text distinguishes no exact match
from ambiguous exact identity and includes the normalized requested selection
without selecting a preferred candidate.

## Provider and installed-resource boundary

An installed result remains authoritative for its manifest identity and
solution. The provider path does not silently replace an installed solution.
Conversely, provider resolution does not create an installed resource and does
not imply that suitable SPK coverage exists.

The provider request is explicit and injectable for deterministic offline
tests. Importing Wenu, constructing a chart, and using `offline` policy never
invoke it accidentally. Network and provider failures propagate as actionable
resolution failures without partial publication.

## Failure behavior

Resolution fails before acquisition for:

- empty or non-string selection;
- invalid UTF-8/JSON, missing signature, or changed schema;
- malformed candidate identity or a non-comet candidate;
- missing canonical designation or SPK-ID;
- zero exact aliases matching the request;
- more than one exact candidate matching the request;
- ambiguous fragment identity;
- collision between installed aliases;
- an attempted bare asteroid number such as `10`.

No failure falls back to the first provider row.

## Ownership

A small identity module owns provider query construction, typed candidate
parsing, alias construction, exact matching, and provenance. It may reuse
normalization shared with `minor_body_resources.py`, but it does not take
ownership of installed manifest validation.

`MinorBodyResourceCollection` remains the authority for installed aliases.
`minor_body_acquisition.py` remains asteroid-only in this slice.
`comet_discovery.py` remains responsible for interval-set discovery, not
single-object identity.

## Test placement

A new `tests/test_minor_body_identity.py` is justified as the durable home for
provider-backed exact minor-body identity resolution. The closest existing
files do not own that seam:

- `tests/test_minor_body_resources.py` owns installed manifest resolution;
- `tests/test_comet_discovery.py` owns perihelion-filtered set discovery;
- `tests/test_minor_body_acquisition.py` owns policy, cache, and acquisition.

The new tests use a frozen provider response and cover exact numbered,
numbered-plus-name, official-name, case/whitespace, ambiguous, fragment,
bare-number, schema-drift, and no-network-installed paths. They do not repeat
SPK, orbital propagation, chart, or renderer tests.

## Acceptance specimen and gates

The first uninstalled specimen is `10P/Tempel 2`. It proves the generic path
only; production code may contain no `10P` conditional, constant, parser
exception, fixture lookup, or resource-layout special case.

Acceptance requires:

1. Fernando accepts this exactness and failure contract;
2. focused deterministic identity and documentation tests pass;
3. a deliberate live SBDB resolution maps `10P` and
   `10P/Tempel 2` to the same identity;
4. `Tempel` and bare `10` fail without selecting an object;
5. `git diff --check` and the complete Mac test suite pass;
6. review confirms no acquisition, cache, SPK, chart, coordinate, magnitude,
   report, or renderer behavior changed.

Acceptance of 50A.5D.2A authorizes only the identity resolver. A separate
50A.5D.2B review is required before generic comet acquisition.

## Acceptance

Fernando accepted this audit on 2026-09-13 and authorized only the exact,
typed 50A.5D.2A comet-identity resolver described here. The authorization does
not include generic comet acquisition, Horizons SPK requests, cache
publication, chart integration, observer-dependent magnitude, or reports.
Those remain subject to their separately reviewed milestones.
