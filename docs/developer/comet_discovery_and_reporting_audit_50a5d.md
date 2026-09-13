# Comet discovery, acquisition, and moving-object reporting audit (Milestone 50A.5D)

**Status:** Accepted by Fernando on 2026-09-13, including the observed-angular-rate addition

**Base:** `c4c6a9c35fe9f2f91e0d1071b550628f4f5345e5`

## Purpose

50A.5C proved that the drawable-comet runtime is descriptor- and resource-
driven by installing and drawing both 2P/Encke and 161P/Hartley-IRAS. It
deliberately stopped before live discovery, automatic comet acquisition,
photometric claims, or sidecar reports. This audit defines those missing
responsibilities without changing runtime behavior.

The requested user experience is:

1. `wenu_retrieve_comets START STOP` lists known comets whose perihelion falls
   in the interval and whose perihelion distance is inside a declared bound;
2. a chart command may name an uninstalled comet exactly and let the existing
   data policy acquire a verified bounded resource before chart construction;
3. every chart containing a natural moving body writes a concise report for
   the major epochs already realized for that chart.

Artificial satellites remain outside this milestone because their catalogue,
time-validity, propagation, and reference-frame contracts are different.

## As-is findings

### Discovery and installed resources are separate

`MinorBodyResourceCollection` resolves exact aliases only inside an installed
resource collection. `tools/install_comet_resource.py` publishes a comet only
from already accepted frozen evidence. `minor_body_acquisition.py` implements
automatic preflight only for positive permanent asteroid numbers. Therefore a
missing directory such as `~/.cache/wenu/minor_bodies/10p-tempel-2` correctly
fails today; no current owner is authorized to discover or download it.

### The reusable temporal result already exists

`SolarSystemTrackRealization` evaluates each target once per sample and returns
one immutable `SolarSystemTrackResult`. Path, ticks, symbols, and labels are
views over that result. It retains exact sample instants, exact major-sample
indices, apparent directions, sample observers, source binding, and
provenance. A report must consume this result and must not repeat an ephemeris
calculation.

Observed Venus, Mercury, and Moon phase sequences use the same temporal-
component selection vocabulary but retain their separate physical-disk
realizers. Reporting may consume their completed results; it may not merge
their physical models into the track realizer.

### Export is the correct publication boundary

`ChartRequestGeneration` owns all products from one immutable request, while
`ChartExportResult` retains the completed rendering and resolved layer
options. Report construction belongs after scientific realization and before
request-scoped resources close. Serialization is export-adjacent and renderer-
neutral. PNG, PDF, SVG, and Matplotlib must not acquire report policy.

## Authoritative provider boundaries

Discovery uses the NASA/JPL SBDB Query API. The query freezes the returned
field names, API version, request parameters, retrieval instant, and raw
response digest. Candidate fields include `spkid`, `full_name`, `kind`,
`pdes`, `name`, `prefix`, `class`, `q`, `tp`, `tp_cal`, `e`, `i`, `per`,
`moid`, `t_jup`, `orbit_id`, and their available uncertainties.

Exact-object resolution uses the NASA/JPL SBDB API and Horizons API. Horizons
record numbers are provider identifiers that may change and are never inferred
from the designation. Acquisition records the exact resolved record, NAIF/SPK
target, orbit solution, coverage, segment centre, frame, type, and SHA-256.

The accepted Encke and 161P fixtures remain independent numerical oracles.
Automatic acquisition is a provider-trusted operational path; it does not
claim that every discovered comet has received a new independent numerical
validation.

## 50A.5D.1 — `wenu_retrieve_comets`

Add the console entry point:

```text
wenu_retrieve_comets START STOP
    [--max-perihelion-distance AU]
    [--observer-location NAME]
    [--format table|json]
    [--output PATH]
```

The default selection is deterministic:

- comet solutions whose perihelion instant `tp` lies within the closed input
  interval;
- perihelion distance `q <= 5 au`, configurable by the explicit option;
- one row per exact returned solution, sorted by perihelion time and then
  canonical designation;
- input civil dates are parsed as UTC boundaries and compared after explicit
  conversion to the provider's TDB perihelion scale;
- missing values remain `unknown`; they are never replaced by zero.

The human table contains canonical designation and name, comet class, UTC
perihelion date, perihelion distance, eccentricity, period when meaningful,
inclination, Earth MOID when available, orbit solution, and retrieval time.
JSON retains the same values with units, time scales, provider identity, raw
request parameters, and provenance.

“Approaches the inner Solar System” means only the declared `tp` and `q`
filter. It is not a visibility forecast. It makes no claim about altitude,
solar elongation, sky brightness, weather, coma activity, or detectability.

### Magnitude policy

Without an observer, the table may show the provider's comet photometric
parameters (`M1`, `M2`, `K1`, `K2`) when available, but must label them as
model parameters rather than an expected apparent magnitude.

With `--observer-location`, a separately identified Horizons observer query
may report the minimum model apparent magnitude and its epoch across a
declared sampling cadence. The value is labelled `model magnitude`, retains
the Horizons quantity and model provenance, and is `unknown` if the provider
does not supply it. Wenu does not synthesize a magnitude from missing model
parameters and does not rank unknown magnitudes as bright.

Discovery is an explicit network command. It never runs during import,
library chart construction, or offline policy.

## 50A.5D.2 — Generic comet preflight

Extend the existing `MovingObjectDataPolicy` boundary from numbered asteroids
to exact comet selections. This is not a comet-specific rendering path.

Resolution order is:

1. normalize the lossless IAU/MPC comet selection, preserving `P`, `D`, `I`,
   `C`, `X`, `A`, fragments, slashes, spaces, and exact names;
2. reuse an installed exact alias if its manifest covers every required chart,
   center, and track instant;
3. under `offline`, fail with the exact missing identity or coverage interval;
4. under `acquire-if-missing` or `refresh`, query exact SBDB identity and stop
   on zero or multiple matches rather than guessing;
5. bind the exact Horizons record and current orbit solution, request a bounded
   type-21 SPK, and validate target, solar centre `10`, ICRF frame `1`, segment
   type, coverage, receipt, and digest;
6. publish a manifest-backed content-addressed resource atomically under the
   existing cache lock; then render from the verified local resource only.

Name resolution is exact and case-folded after whitespace normalization.
`10P`, `10P/Tempel 2`, and exact installed/provider aliases may resolve to one
identity, but `Tempel` must not select among candidates. A permanent comet
number is always paired with its designation class; it is never interpreted as
an asteroid number. Provider ambiguity, fragment ambiguity, changed target,
changed solution, malformed SPK, incomplete coverage, or digest mismatch is a
hard failure.

The first acceptance specimen is `10P/Tempel 2`, chosen only to prove that an
uninstalled exact name can traverse the generic path. No `10P` conditional,
constant, parser exception, or resource layout is permitted in production.

## 50A.5D.3 — Moving-object report sidecars

Every CLI chart containing a natural moving-object point, track, or observed
disk sequence writes one report pair beside the chart:

```text
<chart-stem>-moving-objects.txt
<chart-stem>-moving-objects.json
```

One pair belongs to the immutable chart request, not separately to PNG, PDF,
and SVG products. Existing `ChartRequestGeneration.outputs` continues to mean
graphical outputs; a new explicit `reports` field exposes sidecars without
silently changing that compatibility tuple.

The text file is concise and human-readable. The JSON file is the complete
machine-readable record. Both contain:

- chart observer, chart observation instant, center selection and independent
  `--center-on-date` when present;
- exact body identity, class, designation/name, provider target, solution,
  resource digest, coverage, and correction policy;
- for each selected major epoch: UTC and provider time scale, apparent ICRS
  right ascension/declination, altitude/azimuth for that epoch's observer,
  observer distance, one-way light time, and provenance;
- predicted instantaneous topocentric apparent angular motion relative to the
  sidereal sky, with signed eastward and northward components in mas/s:
  coordinate rate `dRA/dt` (without the cosine factor), tangent-plane rate
  `mu_RA* = cos(dec) dRA/dt`, declination rate `mu_Dec = dDec/dt`, and total
  sky-plane speed `sqrt(mu_RA*^2 + mu_Dec^2)`;
- for comets: symbolic tail position angle and whether its source was exact
  provider `PsAng` or the calculated antisolar fallback;
- model magnitude only when an authoritative realized provider value exists,
  with its model/source label; otherwise `unknown`;
- phase and illuminated fraction for resolved Venus, Mercury, or Moon samples
  when already present in the completed disk result.

Tracks report their start and exact major anchors using the retained major-
sample indices. A standalone moving point reports the chart evaluation epoch.
Sequences use the same `none`, `start`, and `major` temporal selection contract
already used for symbols and labels. Multiple bodies append independent
sections in deterministic request order.

No report calculation may call a state source, Horizons, SBDB, a projection,
or a renderer. If a requested field was not retained by the completed
scientific realization, the implementation must first extend that immutable
result type or report `unknown`; it must not reevaluate the body.

The rates are observing predictions at each reported epoch, not orbital angular
velocities and not secants across the user-selected track cadence. Their
scientific owner must evaluate and retain an instantaneous derivative as part
of the same observer-bound apparent-direction realization. The implementation
must declare its derivative method and interval, demonstrate numerical
convergence, and compare the result with an independent Horizons apparent-rate
quantity before acceptance. The report serializer only formats the retained
values.

Signs are positive eastward in right ascension and northward in declination.
The raw coordinate rate `dRA/dt` becomes ill-conditioned at the celestial
poles; the report must retain the well-behaved tangent-plane components and
emit `unknown` plus a warning for the raw rate when the adopted pole guard is
crossed. The text report must also warn that telescope-control systems differ:
some request `dRA/dt`, others request `mu_RA*`, and neither value is an
Alt/Az motor rate or a field-rotation rate. The observer must verify the
driver's convention before applying differential tracking.

## Ownership changes

- a new provider-neutral discovery module owns query construction, typed rows,
  sorting, units, time-scale identity, and serialization inputs;
- `wenu/cli/comets.py` owns only command parsing, provider invocation, and
  table/JSON output for `wenu_retrieve_comets`;
- `minor_body_acquisition.py` generalizes verified preflight and publication;
  `cli/chart.py` invokes it before chart construction under the existing data
  policy;
- scientific result types retain reportable values at the point those values
  are first calculated;
- a new renderer-neutral moving-object report module owns aggregation and
  deterministic text/JSON serialization;
- request generation publishes one report pair after realization and before
  request-scoped ephemeris resources close;
- coordinate service, projections, preparation, Matplotlib renderer, semantic
  SVG, and physical page/export owners remain unchanged.

## Bounded implementation order

1. **50A.5D.1:** frozen SBDB query fixture, typed discovery result, table/JSON
   CLI, offline parser tests, and one deliberate live smoke test;
2. **50A.5D.2:** exact generic comet preflight, atomic cache publication,
   warm-cache offline reuse, and a 10P/Tempel 2 chart acceptance;
3. **50A.5D.3:** immutable report model, one-report-per-request publication,
   then comet, planet, Moon, asteroid, multiple-body, and all-product tests.

Each slice receives focused review before the next. A successful discovery
query does not pre-authorize acquisition, and successful acquisition does not
pre-authorize the report writer.

## Test structure

- extend `tests/test_minor_body_acquisition.py` for shared data-policy, lock,
  cache, coverage, and failure behavior;
- add `tests/test_comet_discovery.py` because provider query parsing and
  discovery serialization are a new public boundary;
- add `tests/test_moving_object_report.py` because the immutable report and
  sidecar formats are a new durable output contract;
- extend existing CLI, request-generation, track, disk-sequence, semantic, and
  documentation tests only for their established owners;
- keep network tests opt-in and use frozen raw responses for the routine suite;
- test one failure once at its owner. Downstream files assert propagation only
  when that propagation is itself a public contract.

## Acceptance gates

Before any slice closes, require:

1. deterministic frozen-response reproduction and `git diff --check`;
2. exact ambiguity, offline, coverage, corruption, and provider-drift failures;
3. proof that warm-cache chart rendering performs no network access;
4. proof that one scientific realization supplies drawing and report values;
5. 10P/Tempel 2 exact-name and designation equivalence without special code;
6. human review of discovery table, chart, text report, and JSON report;
7. PNG/PDF/SVG parity and unchanged legacy graphical-output enumeration;
8. focused tests followed by the complete Mac suite.

## Stop conditions

Stop for review if JPL cannot provide a unique exact identity, if the required
interval exceeds trustworthy SPK coverage, if a photometric value cannot be
identified as a provider model output, if sidecar production would require a
second astronomical realization, or if report generation changes chart
geometry or graphical bytes.

This audit changes no runtime code, network behavior, chart output, or public
command. Fernando accepted it on 2026-09-13 with the observed-angular-rate
addition, authorizing only 50A.5D.1.

Fernando subsequently approved a bounded 50A.5D.1A implementation on
2026-09-13: deterministic SBDB discovery, typed rows, and table/JSON output.
The optional observer-dependent Horizons magnitude query requires an agreed
sampling cadence and remains deferred to 50A.5D.1B. This split does not
authorize 50A.5D.2 acquisition or 50A.5D.3 reports.
