# TT–TDB realization: resource assessment and implementation proposal

Version 1 · 2026-11-04 · K4b.08 documentation review; proposals, not runtime

## Authority and result

Fernando selected this bounded review with “Proceed” on 2026-11-04, after
confirming clean synchronized Mac main
`7f0f7486c8cf9b19ee8a8bf1ca2ad088ee561ec5` and merged-branch/cache cleanup.
The [observer contract](earth_bound_observer_contract_v1.md) owns agreed site,
time, GR, velocity and output requirements. This review specifies a concrete
candidate and its blockers; it does not select an implementation or acquisition.

**Recommendation for review:** first qualify a prepared geocentric DE440 time
series as a small independent time-service slice, with explicitly selected
equality and full-ERFA comparison policies. Keep site-event linking separately
identified within the same observer design. Long-span primary conversion still
needs an admitted time resource or a separately selected DE441-based time
integration. A modern slice alone cannot deliver the ancient observer.
No new milestone ID, compulsory sequence, package, CLI spelling, public class,
SDK/schema revision or runtime dependency is established by this recommendation.

No binary ephemeris was downloaded or evaluated here. Resource listings/headers
are evidence about published candidates, not local-file admission or numerical
validation. Accepted R1/R3 integrations and existing modern defaults are reused
unchanged. The parent K4b.08 remains open.

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

## Long-span options requiring a decision

1. Locate and qualify a compatible prepared DE441-derived time product, including
   actual long-span coverage and construction evidence. No such product was
   established by this review.
2. Qualify an explicitly mixed time/PV model, such as DE431 time with DE441 PV.
   This is an alternative proposal, not an approved replacement or a guarantee
   that the two transformations remain equivalent at remote dates.
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

None of these alternatives receives implicit priority from this list. R3's
J−13000..J+13000 target remains an orientation target; no observer/time interval
is enlarged. Do not silently bridge DE440/DE441 or two time models at a seam.

## Proposed implementation gate and open decisions

Before runtime, agree actual resources/hashes, evaluator/lifecycle, finite source
and target coverage, numerical certification and whether the first slice is
geocentric only. Proposed deterministic geocentric comparison events are TDB
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
