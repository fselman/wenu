# TT–TDB realization: resource assessment and implementation proposal

Version 1 · 2026-11-16 · K4b.08 resource assessment and geocentric contract definition

## Authority and result

Fernando selected this bounded review with “Proceed” on 2026-11-04, after
confirming clean synchronized Mac main
`7f0f7486c8cf9b19ee8a8bf1ca2ad088ee561ec5` and merged-branch/cache cleanup.
The [observer contract](earth_bound_observer_contract_v1.md) owns agreed site,
time, GR, velocity and output requirements. This review specifies a concrete
candidate and its blockers; it does not select an implementation or acquisition.

**Original recommendation (2026-11-04):** first qualify a prepared geocentric DE440t
series as a small independent time-service slice. The subsequent resource
qualifications and selected geocentric contract below supersede that sequencing
proposal. Keep site-event linking separately
identified within the same observer design. Long-span primary conversion still
needs an admitted time resource or a separately selected DE441-based time
integration. A modern slice alone cannot deliver the ancient observer.
No new milestone ID, compulsory sequence, package, CLI spelling, public class,
SDK/schema revision or runtime dependency is established by this recommendation.

No binary ephemeris was downloaded or evaluated here. Resource listings/headers
are evidence about published candidates, not local-file admission or numerical
validation. Accepted R1/R3 integrations and existing modern defaults are reused
unchanged. The parent K4b.08 remains open.

## Subsequently selected resource step

On 2026-11-04, after this review merged through #373/main `81314326`,
Fernando selected DE440t acquisition and reader qualification. See the
[roadmap scope](../kernel_roadmap_v0.9.5.md#k4b08-selected-de440t-resource-qualification)
and [resource ledger](../data/external_catalogue_ledger_v1.md#selected-de440t-time-resource-acquisition).
This supersedes the earlier lack of acquisition authority only for that bounded
resource step. Fernando subsequently reported successful Mac acquisition and
reader inspection at `473e66c6`: the actual type-2 time segment covers native
TDB JD 2287184.5..2688976.5; all 421 JPL scalar references agree within
2.168404344971009e-19 s. Exact resource/hash/reader identity and receipt belong
to the linked ledger. This is published-point reader agreement, not a certified
time-conversion/physical error or implementation of TT-input inversion.
The complete Mac documentation gate passed 36 cases in 5.25 s at `fb3d2c2c`.
The proposed geocentric converter and site/error implementation remain unselected;
the subsequent DE431t resource decision is recorded below. JPL's [BSP README](https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/README.txt),
[reference values](https://ssd.jpl.nasa.gov/ftp/eph/planets/ascii/de440t/testpo.440t)
and [reference-reader description](https://ssd.jpl.nasa.gov/ftp/eph/planets/fortran/testeph1.f)
provide the concrete scalar sign/units/target checks. They do not turn a resource
comparison into a certified conversion bound.

## As-is owners and constraints at the exact base

| Owner | Observed implementation | Consequence |
|---|---|---|
| [Conventions](../../../src/wenu/astrometric_coordinates.py), `TcbTdbAdapter` | Directed finite TCB↔TDB arithmetic through existing `TimeService` | Reuse after explicit TT↔TDB conversion; no implicit chain |
| [Kernel time service](../../../packages/wenu_kernel/src/wenu_kernel/time.py), `TimeConversionAdmission`, `TimeConversion` | Requires finite nonnegative error fields, source-scale coverage and one admitted adapter per directed pair; adapters are borrowed and handle-free | Do not insert an unknown bound or register three competing policies for the same directed pair in one service |
| [Pinned ephemerides](../../../src/wenu/skyfield_ephemeris.py), `open_pinned_ephemerides` | Exactly DE440/full plus DE441/part-1 and part-2; hashes, conservative coverage and geometric 0→3→399/0→10 paths | This is not an existing general time-series loader; preserve its role validation |
| [Modern reception](../../../src/wenu/astrometric_observation.py), `ErfaReceptionBackend.prepare` | Site-aware `erfa.dtdb`, WGS84 km inputs, final IERS, EPV00 and explicit bounded modern reception domain | Preserve this path and its unknown total error; do not relabel it as a new bounded time adapter |
| Same conventions owner, `NominalEarthOrientation.evaluate` | Exact TT/R1-UT1 matrices and model receipts; no time conversion or rate | A time-series conversion need not invoke full-history orientation; site linking must bind its own exact TT orientation |

Extend the existing convention owner for time-model selection and numerical
conversion where responsibility matches. Resource opening/verification belongs
with resource owners, upstream of immutable conversion admission. A prepared,
handle-free evaluator or other lifecycle design needs proof before borrowing it
through `TimeService`; do not smuggle an open mutable SPK into a frozen adapter.
Keep scientific model semantics out of the generic kernel, CLI and renderers.
One explicitly selected policy creates the applicable directed adapter pair;
Python and eventual CLI select that same policy, not separate numerical engines.

## Published resource findings checked 2026-11-04

| Candidate | Primary-source observation | What remains unqualified |
|---|---|---|
| JPL `de440t.bsp` and ASCII `de440t/header.440t` | JPL BSP directory lists the time variant (displayed size 145.7M). Header states JED 2287184.5..2688976.5, 32-day records, NCOEFF=1122; GROUP 1050 ends with a nonzero 13-coefficient/eight-subinterval entry | Actual binary segments, scalar sign/units/layout, exact coverage, hash, backend compatibility and numerical errors; no local presence established |
| Retained DE440/DE441 position resources | Existing accepted ledger records verified geometric state resources. Published DE441 header states JED −3100015.5..8000016.5, NCOEFF=1018 and zero final coefficient/subinterval counts | Position coverage does not confer time coverage. Do not infer a time payload from the edition or an Earth/Sun PV result |
| Long-span prepared JPL time candidate | Checked BSP directory lists `de431t.bsp`; it lists `de441.bsp` but no `de441t.bsp` | This directory observation is not proof that no DE441 time product exists anywhere. DE431 time with DE441 PV is a different model combination requiring explicit compatibility review; no automatic substitution |
| INPOP21a | IMCCE publishes `_tt.dat` TDB variants and states that included TT−TDB values are in seconds | Advertised ±100/±1000-year file ranges are not the R3 target. Actual epochs, format, terms of use and compatibility need admission; no model switch or CALCEPH dependency selected |

Header coverage is a discovery limit, not an admitted Wenu interval. Inspect
actual time segments and coefficient records before selecting precise endpoints.
The independent variable and scalar quantity must be verified separately from
position units. CALCEPH documents time IDs 1000000001 (TT−TDB) relative to
1000000000, with seconds/day selection affecting returned units. These IDs are
candidate inspection expectations, not assertions about an unopened SPK.
Never pass a time pseudo-target through a planetary position normalizer or
interpret its scalar as kilometres. Do not use filename spelling as metadata.

The existing [external ledger](../data/external_catalogue_ledger_v1.md) continues
to own verified local locations. A later authorized acquisition must preserve
source URL/date, complete bytes/SHA-256, comments/header/constants, edition,
time quantity/scale, segment descriptors and actual coverage. Store required
external inputs outside disposable builds; no download during conversion/test
execution. Provider terms and redistribution remain subject to explicit review.

## Scalar calculation and finite admission

Use seconds for offsets and seconds per second for rates. Let `t` be a split
TDB date and let `D(t)` be the admitted geocentric TT−TDB scalar in seconds.
The proposed forward mapping is

```text
TT = TDB + D(TDB)/86400       (dates in days).
```

For TT input, solve `t + D(t)/86400 = TT` inside verified TDB coverage.
Starting from the same numeric TT label can be an initial numerical guess;
it is not the selected equality approximation or a returned fallback result.
Use a bounded, bracketed root solve after establishing a monotone admitted
mapping. A Newton step may be used only with an admitted derivative and a
bracket safeguard. Do not evaluate an initial guess outside resource coverage.
Map verified endpoints to determine conservative TT-source coverage; TT and TDB
coverage cannot simply be assigned identical numeric labels. Handle gaps,
overlaps and segment precedence explicitly and record the chosen segment.
Refuse out-of-domain roots, nonfinite evaluations, inconsistent joins or failure
to converge. Do not clamp an event to an endpoint or extrapolate coefficients.

Preserve integer `jd1` and canonical fractional `jd2` in existing Wenu records;
pass two parts to backends and normalize by the existing split-date rules.
Subtract offsets and form residuals without collapsing the complete JD into
one binary64 number. Proposed initial solver diagnostic: residual ≤1 ns, subject
to feasibility tests and review. This is neither an adopted admission bound nor
an ephemeris/model accuracy claim. If `|1+dD/dt|` has admitted lower bound `m`,
residual plus evaluator-error control can inform a root-error bound divided by
`m`; a residual alone does not certify the full conversion error.

Distinguish interpolation/evaluation, root solution, split arithmetic, source
time realization, source ephemeris and physical-model error channels. Only a
justified numerical bound may populate the existing SDK fields. If it is not
available, return explicit unavailability outside that bounded admission or
propose a separately reviewed contract change; do not weaken `TimeService` or
encode unknown as zero. A backend comparison/round trip is diagnostic evidence,
not automatically a bound. Numerical rate capability is separately qualified:
for this geocentric map `dTT/dTDB = 1+dD/dt`, using consistent seconds. No rate
or site velocity follows merely from a successful scalar conversion.

## Geocentric conversion versus site-event linking

TT scales geocentric coordinate time; it is not the proper time of a clock at
the chosen observatory. A geocentric time ephemeris supplies one geocentre
mapping. The same TT hypersurface evaluated at a nonzero site displacement
generally maps to a different barycentric event. Keep those meanings explicit.

At leading order the site increment in TDB−TT is proportional to
`v_E · r_site / c²`, with consistent barycentric/geocentric axes, scale and
units. The sign is positive in TDB−TT and negative in TT−TDB. This identifies
the seam; it is not the complete selected PN formula. Park et al. Eq. 3 includes
higher-order terms; retained factors/order and displacement transformation must
be reviewed together with the already agreed IAU/GR spatial composition.
Do not append an unscaled terrestrial vector to a TDB-compatible state.

For a supplied TT site event, prepare its exact-event R3/site geometry once.
During a scalar TDB solve keep that TT-event site identity fixed and evaluate
necessary Earth PV at admitted trial TDB values. Do not recompute neighboring
full-history origins simply as a root-solver side effect. Inverse site conversion
cannot reuse a different event's matrix or pretend the site increment is
constant; an arbitrary TDB→site-TT inverse needs its own coupled admission and
cost review. The first proposed geocentric slice avoids claiming that capability.
Geocentre results must be labelled geocentric, not a completed terrestrial
observer event. No omission of the site term is silently called the primary
site-aware route. Earth acceleration/site/time rates are separate prerequisites
where differentiation of the retained terms needs them.

## Explicit alternatives with the same semantic boundary

| Policy | Proposed treatment | Limits and receipt |
|---|---|---|
| Ephemeris-based primary | Admitted prepared geocentric scalar, then separately qualified site-event transformation when requested | Bind resource/segment, input and actual output events, location mode, solver/units and model/error identities |
| Equality approximation | Explicit same-numeric-label TT↔TDB approximation with finite caller admission | Not SDK same-scale identity; report omitted relativistic/geocentric/site terms and unknown approximation error. Do not claim total zero error from exact label copying |
| Full ERFA | `dtdb` full Fairhead–Bretagnon geocentric model using zero site coordinates for a like-for-like geocentric comparison | Returns TDB−TT in seconds, opposite to `D`. A direct TT argument is permitted by ERFA notes; any solver/argument convention remains in the receipt |

ERFA also supplies an optional site term using UT1 day fraction, east-positive
longitude and cylindrical site distances in km. For a site-aware alternative,
either use that complete named ERFA convention or a separately admitted common
site transformation after a geocentric evaluation; distinguish them and never
apply both. ERFA's stated comparison with DE405 time integrations over 1950–2050
does not establish agreement with DE440, a Wenu total bound, or remote validity.
Propose that modern overlap as the first cross-model comparison domain, not a
default extrapolation. Remote ERFA or equality requests need explicit finite
nominal-use admission and unknown-error reporting before being exposed.
No automatic policy switch on resource, coverage or convergence failure.

## Long-span resource decision and unselected alternatives

**Selected 2026-11-04:** Fernando said “Aceptemos de431t”. Use DE431t as the
long-span geocentric TT−TDB resource. Bounded acquisition, actual time-segment
inspection, all-record join diagnostics and sampled DE440t overlap were
subsequently reported passed at `e9ac9d4f`; exact bytes/hash, actual native
coverage and retained receipts belong to the external ledger. At `da7a6ce1`,
Fernando also reported exact CSPICE/jplephem agreement at 274 native events
and a passed analytic synthetic value/rate/fault control. This establishes
sampled independent reader evaluation, not source-fit/physical accuracy. The
mixed-model assessment below records the limits; quantified compatibility
remains unresolved. The resource qualification and assessment were accepted
and merged through #376. DE440t remains the modern reference. This selects
the resource, not a certified interval/error, automatic seam, converter or site
transformation. See the
[roadmap decision](../kernel_roadmap_v0.9.5.md#k4b08-selected-de431t-long-span-time-resource).

The direct Mac query reported NO_MATCH for center/target 1000000000 → 1000000001
in both DE441 parts and the single SSD DE441 kernel, with a successful DE440t
control. Receipt:
`~/Software/build/wenu/test/de441-time-query-v1-u7r5hfhf/run-provenance.json`.
The single remote file was index-inspected using HTTPS ranges, not fully acquired
or checksum-admitted. The generic “starting with DE430” README does not establish
a time segment in every later kernel.

Alternatives below remain unselected except for the DE431t choice:

1. Locate and qualify a compatible prepared DE441-derived time product, including
   actual long-span coverage and construction evidence. No such product was
   established by this review.
2. Qualify an explicitly mixed time/PV model, such as DE431 time with DE441 PV.
   DE431t is now the selected time resource; compatibility qualification remains
   pending. Selection does not guarantee equivalence at remote dates.
3. Prepare a DE441-based time ephemeris by integrating the relativistic time
   equations along returned planetary trajectories. This integrates a scalar
   time relation, not new planetary orbits. Earth/Sun alone are insufficient for
   a claimed full JPL-equivalent model: select all retained gravitating bodies,
   constants, potential/vector/higher-order terms, epoch normalization and
   omissions explicitly. Park et al. Eq. 3 supplies the reference framework.
   Fix the integration constant using the IAU reference epoch and scale
   conventions, not by arbitrary zero at J2000 or matching a single ERFA value.
   Quadrature, secular cancellation, interpolation, cumulative errors and costs
   need a separately agreed qualification plan. No long integration is selected.

DE431t has explicit priority through Fernando's resource selection. R3's
J−13000..J+13000 target remains an orientation target; no observer/time interval
is enlarged. Do not silently bridge DE440/DE441 or two time models at a seam.

## DE431 time with DE441 states: compatibility assessment

**Assessed 2026-11-05; no runtime admission.** The selected resource is acquired
and readable, and independent CSPICE/jplephem sampled evaluation passed.
The existing [resource ledger](../data/external_catalogue_ledger_v1.md#selected-de431t-long-span-time-resource)
owns numerical receipts. Distinguish three separate questions:

| Question | Evidence and result |
|---|---|
| Shared coordinate-scale convention | [Folkner et al. (2014), Section II.C](https://ipnpr.jpl.nasa.gov/progress_report/42-196/196C.pdf) and [Park et al. (2021), Section 2.3](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440_and_de441.pdf) both describe TDB relative to TCB and TT relative to TCG, with the same published LB, LG and reference epoch. No scale-name mismatch is demonstrated. This does not equate their numerical ephemeris realizations |
| Realization/model compatibility | The time relation depends on Earth velocity, external potentials and other retained relativistic terms. DE431t with DE441 states is explicitly heterogeneous: reader success and common scale definitions do not reproduce a DE441-derived time integration. No uniform mixed-model error bound is established |
| Coefficient/evaluator fidelity | Independent readers agree at the 274 selected events, and every adjoining record has the reported continuity. Both readers consume the same fitted representation. No comparison to the original integrated time series or higher-fidelity same-model fit has been established |

The common constants are LB=1.550519768e−8, LG=6.969290134e−10 and
reference epoch JD 2443144.5003725 in the cited formulations. Preserve each
formula's sign and normalization conventions if implemented; this assessment
does not introduce a constant correction or re-zero the time ephemeris.
Park et al. describe revised trajectories/model terms and fitted parameters
relative to the earlier ephemerides. Consequently the observed modern
DE431t/DE440t discrepancies cannot be promoted to a DE431t/DE441 error bound,
especially outside the measured overlap.

**Historical fit concern:** [Irwin's first-hand 2017 report](https://sourceforge.net/p/timeephem/timeephem-devel/message/35729726/)
describes insufficient coefficients in original DE430t/DE431t versions and
explicit uncertainty about subsequent updates. The retained release identity,
degree, continuity and independent reader agreement do not establish whether
that original fit issue affects these bytes. Do not label the current file
defective or the issue resolved. Contacting JPL and new integration remain
unselected; neither is imposed as a prerequisite to reviewing this resource.

**Assessment outcome:** common stated scale conventions support documenting the
combination as a candidate mixed realization; they are not a scientific
accuracy certificate or authorization to expose it as a qualified converter.
A future candidate must bind both resources/models and their actual domains,
preserve unknown source-fit/physical/mixed-model errors, and select numerical
admission and site-event/rate semantics separately. Geocentric scalar evaluation
does not supply the terrestrial site term. No new fallback, seam, integration,
error-schema change or implementation milestone is activated. Bounded resource
inspection and this assessment are ready for review after the documentation
gate; parent K4b.08 remains open.

## Geocentric TT–TDB converter contract

**Selected for definition on 2026-11-16 under K4b.08.** This section defines
the geocentric conversion contract for review. The resource qualifications in
PRs #374 and #376 are prerequisites. Implementation and numerical admission
require separate acceptance.

### Resource, event and result

- Each conversion uses one explicitly selected, immutable prepared time
  resource. The long-span selection is DE431t; DE440t is the modern
  reference. Bind the selection to the ledger's exact payload SHA-256,
  direct type-2 segment (centre 1000000000, target 1000000001, frame 1),
  record layout and verified native TDB coverage. A missing file, mismatched
  identity/layout, unavailable bound or out-of-domain event produces a
  refusal. Model selection happens before conversion and has no automatic
  fallback, seam or extrapolation.
- Accept one finite event tagged TT or TDB with Wenu's canonical split JD.
  Return the corresponding event in the other scale, in the same split
  representation. Carry model/resource identity, segment and record
  identity (or an unambiguous equivalent), direction, and a finite numerical
  error bound in seconds. Keep the original input unchanged. Epoch
  differences, residuals and normalization use the split parts throughout.
- Let `t` be TDB in seconds relative to the same split reference epoch,
  and let `D(t)` be the selected record's geocentric TT−TDB in seconds.
  Define `F(t) = t + D(t)` in the same relative units. TDB→TT evaluates
  `F`; TT→TDB finds the unique admitted `t` satisfying `F(t) = TT`.
  A TT label may seed a solver after bracketing, but every polynomial
  evaluation uses a TDB argument inside its owning record.

### Coverage, joins and inversion

1. Certify the native record partition before admitting conversion. At an
   interior shared TDB boundary the later record owns the event. Each record
   includes its left endpoint and excludes a right endpoint shared with its
   successor. Include a verified terminal endpoint when it has exactly one
   owner. Precedence at a shared endpoint is distinct from positive-width
   native overlaps, which this contract refuses. A native gap remains outside
   the admitted native domain.
2. For each admitted record interval, establish a positive lower bound
   `m` on `dF/dt = 1 + dD/dt`. Map each interval into TT with its own
   one-sided endpoint values and inclusion rules. Do not assume adjacent
   images meet. A forward jump can leave a TT gap; a backward jump can
   create multiple inverse candidates. Even a small measured join jump
   does not justify welding the images or treating the resource as globally
   monotone. Preserve the TT images as a union; the outer mapped endpoints
   alone do not define inverse validity.
3. For TT input, certify membership in exactly one record image across the
   declared inverse domain before returning a root. Refuse a TT gap, multiple
   candidates or unresolved membership/uniqueness when endpoint error
   enclosures overlap the query. Exact endpoint reasoning may resolve
   equality and ownership. A record's exclusive endpoint may be used as a
   one-sided mathematical limit for bracketing purposes, never as a returned
   root for that record. No nearest-record choice or endpoint clamping.
4. Solve inside the certified record with a bounded bracketed method;
   a Newton step is admissible only when safeguarded within the bracket.
   Verify the final encoded split TDB lies in the owning interval and meets
   the certified error budget. Refuse invalid brackets, nonfinite evaluation,
   inability to encode an in-domain result within tolerance, or failure to
   converge. An inverse trial outside the admitted record is never evaluated
   against that record's polynomial.

### Error admission and SDK boundary

The numerical reference is the exact mathematical map defined by the
identified binary coefficients, declared record-time normalization and
boundary ownership. A forward bound includes argument formation, polynomial
evaluation, offset addition and output rounding; propagate argument error
through the polynomial using a bound over the admitted argument interval.
For an inverse result `t_hat`, evaluate the residual at the final encoded
output. If its computed magnitude is `r` and all residual-computation error
is bounded by `e`, the mean-value theorem gives
`|t_hat - t_root| <= (r + e)/m` on the certified monotone record.
An enclosing bracket can also bound the error if its endpoints and the
returned representation are accounted for. Use an outward-rounded upper
bound in the receipt. A residual tolerance alone, sampled independent-reader
agreement, repeatability and round trips do not establish a uniform bound.

For any later SDK adapter, bind each direction separately. The existing
[TimeService](../../../packages/wenu_kernel/src/wenu_kernel/time.py) expects
one adapter per directed pair and source-scale coverage for both admission
and model dependencies. Any TT descriptor must therefore be a documented
source-scale projection of the same pinned native TDB resource, preserving
the TDB metadata in provenance. A descriptor span can only describe
conservative outer coverage; inside it the adapter must still enforce actual
record membership and uniqueness. Populate the admission maximum and the
per-result bound only with finite justified values. Resource identity and
preparation belong before service composition, with no automatic acquisition
or policy substitution during conversion.

Original-fit error, physical accuracy and compatibility with DE441 states
remain unknown. None enters the SDK numerical-error field. This definition
admits no numerical threshold or production interval; even the proposed 1 ns
diagnostic is not an adopted budget. A polynomial derivative used internally
to prove invertibility does not admit a public rate or a displaced-site event.

### Acceptance

The present gate is review of this contract and the complete documentation
suite. A later implementation proposal must identify admitted resources and
intervals, prove error bounds for its evaluator and solver, and test both
directions against labelled analytic controls plus independent same-resource
evaluation. Include shared endpoints, both jump signs, native and mapped
gaps, overlapping TT images, unresolved endpoint membership, sign/units
faults and cancellation in split dates. The existing sampled resource
receipts are inputs to that work. The site term, public rate, model seams,
observer/CLI/chart integration and runtime changes remain separate.

## Proposed implementation gate and open decisions

Before runtime, agree evaluator/lifecycle, finite source and target admission
intervals and numerical certification under the geocentric contract above. Proposed deterministic geocentric comparison events are TDB
split dates `(2451545, 0.0)`, `(2451545, 0.25)` and `(2460000, 0.125)`, plus
actual segment/resource boundaries and deliberately inadmissible events. These
are a candidate gate, not observations or executed numerical results.

Use a direct primary interpolation reference on the same bytes, such as CALCEPH
or a qualified independent JPL-compatible evaluator; select/install that oracle
separately. A different wrapper around the same interpolator is not independent.
ERFA offers a cross-model comparison with known independence/edition limits;
agreement need not be exact and must not replace a same-resource interpolation
check. INPOP may be an additional comparison, not a hidden production source.

Protect wrong sign/seconds-versus-days, TT supplied as native TDB, whole-JD
precision loss, wrong pseudo-target, source hash/backend mutation, source/target
coverage edges, root/segment failure, finite numerical admission, direct-pair
selection/no fallback, both conversion directions and request isolation.
Use synthetic labelled scalar polynomials to test inversion/rates independently;
same-resource round trips alone cannot detect a consistently reversed sign.
Site-term and rate acceptance separately needs independent matching-policy
references, geocentre zero limit and no duplicated location contribution.
Later CLI/Python selection and chart adoption keep their own public-path gates.

**Current acceptance:** complete existing documentation gate and user review.
No new test file, source module, test-manifest selection or dependency change.
No TT/TDB numerical test, binary inspection or new physical bound is claimed.

## Primary references and observation limits

Checked 2026-11-04:

- [JPL BSP directory](https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/),
  [DE440t ASCII header](https://ssd.jpl.nasa.gov/ftp/eph/planets/ascii/de440t/header.440t)
  and [DE441 ASCII header](https://ssd.jpl.nasa.gov/ftp/eph/planets/ascii/de441/header.441).
  Text fetched directly after the web reader rejected the directory/content type;
  no binary payload fetched. Directory sizes are displayed metadata only.
- [Park et al. (2021), Section 2.3, Eq. 3](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440_and_de441.pdf):
  relativistic time transformation and source-model terms.
- [ERFA `dtdb.c`](https://github.com/liberfa/erfa/blob/master/src/dtdb.c):
  full analytical model, offset sign, site input convention and limited comparison.
- [CALCEPH reading/evaluation documentation](https://calceph.imcce.fr/docs/latest/html/c/calceph.multiple.cusage.html)
  and [NAIF time identifiers, version 4 manual, Chapter 7](https://calceph.imcce.fr/docs/4.0.0/calceph_c.pdf):
  explicit native scale, time pseudo-targets and units; not a dependency choice.
- [IMCCE INPOP21a distribution](https://ftp.imcce.fr/pub/ephem/planets/inpop21a/)
  and [INPOP format specification](https://www.imcce.fr/content/medias/recherche/equipes/asd/inpop/inpop_file_format_2_0.pdf):
  optional time arrays, scales, advertised files and conditions of use.
- [IAU 2006 Resolution B3](https://iauarchive.eso.org/static/resolutions/IAU2006_Resol3.pdf),
  also explained in the [time guide](../time_scales_guide_v1.md):
  TCB/TDB normalization is distinct from an evaluated TT/TDB realization.
