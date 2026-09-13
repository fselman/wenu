# Second drawable comet audit (Milestone 50A.5C)

**Status:** Accepted by Fernando on 2026-09-13

**Runtime effect:** None

**Acceptance specimen:** 161P/Hartley-IRAS

## 1. Purpose

Before closing Program 50A, prove that the accepted comet implementation is
descriptor- and resource-driven rather than an accidental 2P/Encke special
case. The bounded specimen is 161P/Hartley-IRAS during its 2026 return. The
Minor Planet Center solution published for that return places perihelion at
2026-11-27.52819 TT with `q = 1.2650441 au`; September and October therefore
provide a useful moving-track interval before perihelion.

Fernando accepted this identity, provenance, reuse, and visual-test boundary
on 2026-09-13. That acceptance authorizes only the bounded evidence,
characterization, generic installation, and 161P visual experiment described
here.

## 2. Scientific question

The test must answer one narrow question:

> Can a second independently validated installed comet use exactly the same
> resource, point, track, temporal-component, antisolar-symbol, projection,
> rendering, semantic, and export machinery as 2P/Encke?

Passing this test does not claim arbitrary-comet support. It proves only that
the machinery admits another explicit manifest-backed periodic comet without
object-specific runtime branching.

## 3. Identity and authority

The acquisition step must resolve `161P/Hartley-IRAS` through current NASA/JPL
SBDB and Horizons responses. No identifier may be guessed from the permanent
number. Before fixture construction, preserve and cross-check:

- canonical primary designation;
- official name and exact accepted aliases;
- Horizons apparition command record;
- NAIF SPK target identifier;
- orbit solution identifier and epoch;
- object class and all returned model parameters, including any
  non-gravitational terms;
- producer, planetary ephemeris, small-body perturber model, observation arc,
  observation counts, RMS, and validity fields when supplied;
- SPK segment type, centre, frame, time scale, coverage, filename, and
  SHA-256 digest; and
- the exact companion planetary ephemeris identity used by Wenu.

The installed descriptor is derived from the verified manifest. Runtime code
must not contain a `161P` branch, target number, solution identifier, orbital
element, name, or apparition rule.

## 4. Evidence and characterization

Deliberate tooling may acquire a raw evidence directory containing:

1. the SBDB response;
2. the bounded Horizons SPK;
3. direct Horizons barycentric or centre-relative vectors;
4. geocentric apparent and astrometric observer quantities;
5. La Ligua topocentric apparent and astrometric quantities; and
6. Horizons quantity 27, preserving `PsAng` and `PsAMV` separately.

Use at least three accepted epochs spanning September and October 2026. One
epoch should be near the reported 2026-10-02 Earth approach if authoritative
Horizons coverage supports it. Exact epochs, record identifiers, solution,
and model parameters remain evidence outcomes, not audit assumptions.

Compact fixture construction is offline and digest-bound to the raw evidence.
Characterization must precede tolerance selection. `--characterize` cannot
report acceptance or enforce a proposed tolerance. No tolerance is inherited
silently from Encke; a later acceptance decision may reuse an existing
envelope only after the measured residuals and source precision justify it.

## 5. Installed resource boundary

The current manifest-backed `MinorBodyResourceCollection` remains the sole
runtime authority. The implementation may extract a generic comet resource
installer from the Encke-named tool, with the old command retained as a thin
compatibility wrapper if useful. The generic owner must accept verified
fixture/evidence inputs and emit the same typed manifest schema for both
comets.

Installation must be content-addressed or otherwise deterministic, validate
all declared digests and coverage before publication, and fail without
partially publishing a resource. Chart construction and rendering remain
offline. Merely recognizing a syntactically valid comet designation does not
authorize acquisition or drawing.

The installed collection should resolve these exact aliases to one descriptor
when, and only when, the authoritative evidence confirms them:

```text
161P
161P/Hartley-IRAS
Hartley-IRAS
```

Case normalization may follow the accepted exact-alias policy. Fuzzy search,
partial-name matching, discovery, and substitution of another apparition are
out of scope.

## 6. Reuse contract

161P must travel through the existing generic owners:

- `MinorBodyResourceCollection` for manifest validation and resolution;
- the shared minor-body state provider for borrowed SPK state;
- the shared astrometric and apparent direction chain;
- `SolarSystemTrackRealizer` for one evaluation per scientific sample;
- the immutable `TemporalComponentPolicy` for independent path, tick, symbol,
  and date-label selection;
- the canonical reusable comet symbol and per-epoch orientation adapter;
- the existing fixed product-frame transformation, projection, preparation,
  renderer, semantic SVG, and export route.

Provider `PsAng` has precedence for the gas-tail/antisolar symbol direction at
an epoch. The apparent-Sun calculation remains the fallback when the installed
provider has no applicable angle. `PsAMV` remains a dust-tail motion-vector
diagnostic and must not replace `PsAng`. Near the accepted conjunction or
opposition exclusion, the same canonical head-only symbol used for Encke is
selected without inventing a direction.

## 7. Visual experiment

The primary acceptance product is a La Ligua regional chart covering a
161P track from approximately 2026-09-01 through 2026-10-31. The final centre,
field dimensions, cadence, and label density should be chosen after the
acquired trajectory is inspected rather than guessed in this audit.

Review at least:

1. a complete path, ticks, major-epoch symbols, and date labels;
2. major-epoch symbols and dates with path and ticks suppressed; and
3. semantic SVG for stable comet point, track, and symbol identity.

Each symbol must use its own epoch orientation. The chart need not claim that
161P is naked-eye visible or encode physical coma, brightness, dust-tail
morphology, nucleus radius, or activity. The fixed fan remains a class symbol.

An optional mixed-track chart may place 161P with a planet or installed
asteroid when a useful common field exists. It is not an acceptance condition
if the real 2026 geometry makes such a chart uninformative.

## 8. Tests

Extend responsibility-owned tests to prove:

- evidence identity and cross-response consistency;
- offline compact-fixture reconstruction;
- non-accepting characterization followed by explicit enforced tolerances;
- generic installation of Encke and 161P with no runtime object branch;
- exact alias resolution and collision rejection;
- preservation of the returned model and quality fields;
- missing, corrupt, wrong-solution, wrong-target, and out-of-coverage failure;
- provider `PsAng` precedence and apparent-Sun fallback;
- one target evaluation per track sample and one shared track realization;
- independent temporal-component selection; and
- unchanged Encke, asteroid, planet, Moon, projection, and export behavior.

Do not duplicate the already accepted generic renderer, projection, temporal
policy, canonical-symbol geometry, or planetary phase tests. Add a test only
where the second resource introduces a new failure mode.

## 9. Acceptance gates

Before 50A.5C can close, require:

- Fernando's acceptance of this audit;
- inspection of the raw SBDB and Horizons identity blocks;
- accepted numerical and position-angle characterization;
- byte-for-byte compact-fixture reproduction on the Mac;
- focused scientific, resource, CLI, temporal, and documentation tests;
- the complete Mac regression suite;
- explicit PNG and semantic-SVG review of the 161P track products; and
- confirmation that chart execution performs no network access.

## 10. Stop conditions

Stop and re-audit if implementation would:

- place `161P`, its target, solution, or orbit in runtime source;
- infer a target identifier from the designation;
- accept a changed solution or apparition without evidence review;
- apply Encke residual tolerances before characterization;
- acquire or refresh data during request construction or rendering;
- add a second comet direction, track, temporal, symbol, or export pipeline;
- recompute the target for its track symbols;
- confuse `PsAMV` with the antisolar `PsAng` direction;
- introduce fuzzy comet discovery or automatic comet preflight;
- make brightness, visibility, coma, dust-tail, or activity claims; or
- weaken any accepted Encke, asteroid, planet, or Moon contract.

Successful 50A.5C acceptance authorizes 50A.6 minor-body closure. It does not
authorize a general comet catalogue, live service, orbital-element propagator,
automatic comet acquisition, or physical comet rendering.

## 11. Implemented identity checkpoint

The first bounded implementation checkpoint deliberately stops before SPK or
table acquisition. `tools/acquire_50a5c_comet_identity.py` requests the exact
`161P` designation from SBDB and makes a non-ephemeris Horizons identity query.
It validates both service signatures and the returned numbered-comet name,
preserves both complete raw responses with digests and request URLs, and does
not guess an apparition record. Fernando must inspect those provider results
before the next acquisition step freezes a Horizons record or solution.

Fernando's inspected identity result selects Horizons record `90001107`, NAIF
target `1000042`, and solution `JPL#71` dated 2026-09-08 09:12:21. SBDB returns
the Halley-type periodic-comet classification, observation arc 1983-11-23
through 2026-09-08, and non-gravitational `A1` and `A2`. The complete Horizons
identity response additionally preserves the non-standard force-law constants
`ALN`, `NK`, `NM`, `NN`, and `R0`; they are not reconstructed from the smaller
SBDB model-parameter list.

`tools/acquire_50a5c_comet_evidence.py` binds its full SPK, vector,
geocentric, La Ligua topocentric, Sun, and `PsAng`/`PsAMV` requests to that
inspected identity. The characterization epochs are 2026-09-01, 2026-10-02,
and 2026-10-31. It copies the verified identity documents into a new immutable
evidence directory and writes nothing until every returned signature, target,
solution, table, and SPK segment has passed validation.

The offline compact-fixture checkpoint reuses the 50A.4 vector and observer
table parser through a parameterized comet identity specification. It adds the
161P Sun and quantity-27 rows to that same numerical record, with both
numerical and antisolar tolerances explicitly null. The combined validator
delegates to the accepted generic minor-body numerical validator and accepted
antisolar validator; characterization reports residuals without enforcing or
reporting candidate thresholds.
