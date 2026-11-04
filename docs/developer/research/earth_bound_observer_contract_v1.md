# Earth-bound observer: site, event and output contract

Version 1 · 2026-11-03 · K4b.08 selected definition; candidate for review

## Selection and boundary

Fernando selected this contract-definition task with “Proceed” on 2026-11-03,
then confirmed clean synchronized Mac main
`cd5c9b76c6fc25df6adb26b2a086aabf44e5e581`. It is a bounded definition under
the existing K4b.08 parent, not a new runtime milestone or authorization to
activate the parent backlog. This document defines required semantics and
identifies decisions needed to select a later implementation. Accepted site/time, IAU/GR, three-output and SOFA/ERFA refraction choices are
identified below; unresolved numerical and product choices remain review items.

Deliver an explicit fixed-site, exact-event observer contract before runtime,
followed separately by observer implementation and product adoption. No code,
SDK, source catalogue, ephemeris acquisition, dependency, persistent format,
CLI, worker or rendering change belongs to this task. Preserve modern catalogue
population/measurements and ordinary modern observer defaults. K4b.07/K4b.08
parents and K5 reconciliation remain open.

## As-is assessment at the exact base

| Existing owner/public seam | Available behavior | Boundary for this contract |
|---|---|---|
| [Ordinary Observer](../../../src/wenu/observer.py), `Observer` | Existing civil-time, Skyfield/Astropy and resource/cache lifecycle | Keep defaults; do not insert ancient civil-time assumptions or a second scientific pipeline |
| [Modern reception](../../../src/wenu/astrometric_observation.py), `ErfaReceptionBackend.prepare` | Explicit UTC or TT input; final-IERS-B/leap resources; WGS84 ellipsoid height; EPV00/DTDB/APCO observer PV | Domain intersects actual resources and 1950–2050; even TT is internally mapped through admitted UTC. Cannot supply this remote-epoch observer |
| Same owner, `realize_astrometric_batch` | Already evaluated full Cartesian stellar batches; displacement, solar monopole, combined aberration, final-CIP orientation, vacuum horizon | Requires the modern `ReceptionContext` and its UTC identity. Cannot accept the R3 result by relabelling it as that context |
| [Conventions](../../../src/wenu/astrometric_coordinates.py), `NominalEarthOrientation.evaluate` | Accepted opt-in R3 full matrices at one split TT event, bound to R1 split UT1 | No site, observer PV, velocity derivative, TT–TDB mapping or apparent-place realization |
| Same owner, `TcbTdbAdapter`, `convert_barycentric_batch` | Explicit linear TCB/TDB time mapping and admitted nominal-astrometric spatial scaling | No TT/TDB model. Batch converter refuses geometric ephemeris references; do not weaken that guard |
| Same owner, `HistoricalDate`, `resolve_historical_date` | Explicit proleptic calendar/year numbering/scale and retained source uncertainty; resolver targets TCB through admitted direct conversion | Retain chronology receipt. This is not an existing arbitrary ancient TT↔TCB adapter or ancient UTC resolver |
| [Companions](../../../src/wenu/ephemeris_companion.py), `load_ephemeris_companion`, `EphemerisCompanion.at` | Immutable exact-event Earth-centre/Sun geometric ICRF, TDB-compatible states | No planetary reuse, observer translation, light-time solution or implicit TT link |
| [Coordinate specification](../../../src/wenu/coordinates.py), `CoordinateSpec` | Separates frame, origin, position status, event/scale and corrections | Use these concepts; do not encode an ancient event as a modern UTC string to fit an old consumer |

Ownership stays with astronomical convention and observer services, composed
upstream of catalogue/provider → spherical geometry → domain guard → projection
→ preparation → renderer/export. Stars retain propagation and source selection;
geometry consumers retain their direct shared geometry interfaces. No physical
state query is invented for a contour, grid or constellation-boundary vertex.

The [accepted R3 receipt](../kernel_migration_audit_v1.md#accepted-nominal-earth-orientation-result)
is reused unchanged. A prepared matrix can serve many directions at its exact
event. Preparing remote events took about 13–18 minutes on the measured Mac;
that cost is disclosed, not an inserted optimization prerequisite. No endpoint
integration rerun, interpolation, persistent orientation cache or automatic
parallel optimization is selected here.

## Site record and local axes

Require a caller-supplied site identity and numeric east-positive longitude,
geodetic latitude and height, with explicit units, ellipsoid/datum, coordinate
reference epoch and uncertainty/provenance. A reference epoch may be explicitly
unknown; it must never be inferred from the requested observing epoch. Preserve
the original values alongside any canonical longitude representation. Reject
nonfinite values, booleans and incompatible coordinate kinds.

**Agreed initial site convention, 2026-11-03:** use fixed WGS84 ellipsoid
geometry, geodetic latitude and explicit ellipsoid height. Fernando accepted
this explained convention with “Agreed”. Qualify La Ligua’s existing 52 m
before treating it as ellipsoid height. A proposed −1000..10000 m numerical
height admission remains a separate unselected implementation limit; it was
not part of that agreement. Interpret height as ellipsoid height, never as an
unqualified map elevation or height above mean sea level.
Record a named fixed-coordinate assumption: longitude, latitude and ellipsoid
height are held constant in the declared nominal terrestrial axes. A supplied
modern reference epoch does not make these ancient ITRF coordinates. Plate
motion, tides, loading, terrain, vertical deflection and palaeogeography are
omitted, with unknown physical error. Other datums or site evolution need
separate admission. Registered La Ligua/Papudo locations do not bypass this
qualification; their existing elevation must not be silently reinterpreted.

For longitude λ and geodetic latitude φ, define orthonormal terrestrial local
east, north and ellipsoid-normal up vectors:

```text
east  = (-sin λ, cos λ, 0)
north = (-sin φ cos λ, -sin φ sin λ, cos φ)
up    = ( cos φ cos λ,  cos φ sin λ, sin φ)
```

These equations are the candidate Wenu convention, not a gravity-defined
vertical. At a geographic pole the supplied longitude fixes the conventional
east/north axes; disclose that dependence. For a unit terrestrial direction d,
compute E=d·east, N=d·north, U=d·up, altitude=atan2(U,hypot(E,N)) and
azimuth=atan2(E,N) modulo 2π: north zero, increasing eastward. At zenith/nadir,
azimuth is undefined; the output must carry that status rather than presenting
an arbitrary zero as a measured direction. Public numerical angles are radians;
presentation units belong to consumers. Numerical singularity tolerance and its
error treatment must be declared in the later implementation.

## Event and time contract

**Agreed time approach, 2026-11-03:** Fernando selected the ephemeris-based
TT–TDB route (review option 3) and required optional explicit CLI selection of
TT=TDB (option 1) and the full ERFA model (option 2). The
[time guide](../time_scales_guide_v1.md#agreed-wenu-time-policy) owns the
explanation and policy requirements. Option 3 is the primary/default for this
new observer route; existing modern defaults are unchanged. No silent fallback,
new implementation or supported interval follows from the selection. Exact
resources/algorithm, location treatment, accuracy and CLI syntax remain for the
bounded implementation design. The subsequently agreed IAU/GR spatial
convention and site-velocity definition are recorded below.

The observer input is one explicit split-JD TT event plus its chronology record
and the selected immutable R3 orientation result. Check exact TT identity,
coverage, policy/backend binding and R1 rotation receipt before use. UT1 must
come from that same receipt; no independent implicit Skyfield/Astropy UT1.
Keep TT, native stellar TCB and ephemeris TDB distinct throughout.

Retain original calendar/year numbering, source-scale clock uncertainty,
conversion/admission identity and numerical rounding separately. Astronomical
year zero, BCE labels, historical clock or calendar conversion must be explicit.
The remote route does not require UTC, timezone or leap seconds. Future civil
requests with unresolved leap/clock assumptions refuse until an explicit policy
is selected; existing qualified modern UTC behavior remains available unchanged.

| Required link | Contract |
|---|---|
| TT → UT1 | Existing selected R1 receipt, including Delta-T regime/extrapolation and unknown physical error |
| TT ↔ TDB | Selected ephemeris-based primary route; equality and full ERFA are explicit optional CLI requirements. Each requires finite coverage, realization/location convention, provenance and known/unknown error. No automatic equality, silent fallback or extension of modern DTDB accuracy |
| TDB ↔ TCB | Existing explicit `TcbTdbAdapter` admission and receipt; this linear definition does not supply the previous link |
| Chronology → nominal event | Retain the source receipt and uncertainty; conversion of a central value alone does not propagate an uncertainty interval |

An explicitly supplied TT/TDB pair still needs evidence connecting the same
event under a declared realization; two equal-looking JD numbers are not a
conversion. A caller-supplied common-event realization may be considered at
review, but is not automatic trust or an implemented public input schema.

Record requested reception event and every actual source event. Saved stellar
in-window reuse retains its original event and approximation receipt. A later
observer may consume that approximation only under an expressly selected
capability/output policy; it cannot claim exact simultaneous geometry. The
candidate first exact-event path requires actual stellar states at the mapped
TCB event and Earth/Sun states at the mapped TDB event. Stellar reuse windows
never authorize reuse of Earth/Sun PV or orientation at another event.

## Relative states, site position and velocity

Let M be R3's celestial-to-terrestrial matrix and r_site the ellipsoid Cartesian
site vector. The nominal geocentric celestial site displacement is Mᵀ r_site.
This is an axis rotation in the declared convention. It is not by itself the
relativistic GCRS↔BCRS transformation or permission to add unlike spatial scales.

Before any finite-distance subtraction, explicitly admit common spatial axes,
origin, coordinate scale, units and simultaneous event. Keep Earth centre
(NAIF 399) distinct from the Earth-Moon barycentre (3). Verify the actual SPK
body/centre/segment/time coverage and resource identity independently of R3's
orientation domain. Saved companions are optional inputs, not prerequisites:
the admitted existing offline provider may supply the same required states.

**Agreed spatial convention, 2026-11-03:** Fernando accepted the standard
IAU post-Newtonian geocentric/barycentric transformation and then explicitly
confirmed “OK, let us go with the IAU formulation” after the PPN discussion.
Use General Relativity with β=γ=1; adjustable PPN deviations are not selected.
Time and spatial scale conventions must remain consistent with the admitted
Earth ephemeris and stellar inputs. Any omitted terms must be explicit,
justified approximations to this definition, not an automatic geometric fallback.
The concrete retained approximation order, terms, resources and finite domain
still need implementation design and qualification. Modern APCO behavior does
not qualify a new ±13000 observer. State translation has one owner and occurs
once; existing state-reference guards remain intact.

### Site-velocity definition and existing inputs

After clarifying that JPL already supplies the Earth-centre orbital contribution,
Fernando instructed “Proceed.” This selects continued site-velocity definition
within the existing K4b.08 contract slice. It does not activate an unreviewed
numerical algorithm, new rate model, acquisition or runtime implementation.
The following derivative identities are consequences of the fixed-site,
R1/R3 and IAU conventions, not claims of an implemented derivative interface.

| Contribution | Existing input | Remaining requirement |
|---|---|---|
| Earth-centre orbital position/velocity | Existing JPL ephemeris/state adapter or exact-event companion | Consume returned geometric PV with exact event/body/centre/reference/resource checks; do not integrate a new orbit or finite-difference planetary positions |
| Fixed terrestrial site | Agreed WGS84 coordinates and explicit height convention | Zero terrestrial-coordinate velocity does not mean zero celestial velocity |
| Site motion in celestial axes | Same prepared R3 orientation and its R1 TT/UT1 receipt | Derive a consistent orientation rate; R3 currently exposes matrices, not derivatives |
| Barycentric observer state | Same admitted IAU spacetime transformation and selected TT/TDB realization | Transform position and velocity consistently, including required rates and TCB/TDB-compatible spatial conventions |

For constant r_site, the mathematical site trajectory before barycentric
composition is

```text
r_cel(TT) = M(TT)ᵀ r_site,
v_cel,TT  = d(Mᵀ)/dTT · r_site.
```

Rates here use TT coordinate seconds. The result is not yet an admitted
barycentric velocity in TDB seconds. A position rotation cannot simply be
applied to a zero terrestrial velocity; its own derivative supplies the motion.
This is the familiar state-transform distinction between a 3×3 position
rotation and a position/velocity transformation including rotation rates.

For the accepted R3 convention, M=R3(ERA) C(TT), with identity polar-motion
matrix. Derive both terms, not only nominal daily spin:

```text
dM/dTT = (dR3/dERA) (dERA/dTT) C + R3 (dC/dTT),
dERA/dTT = [2π × 1.00273781191135448 / 86400] × dUT1/dTT,
dUT1/dTT = 1 − d(ΔT)/dTT.
```

The last equality uses seconds on both scales and holds on smooth model pieces.
Do not replace it silently with unit rate or borrow an unrelated orientation
library's Earth spin. Preserve omitted polar motion/CPO/FCN rather than
introducing a measured-modern rate under the nominal ancient policy.

### Local pole/origin rate without another long transport

The accepted nonrotating-origin definition already gives the derivative of the
celestial triad at the event. If C has rows a, b, n, where n is the normalized
pole and b=n×a, then on a smooth mathematical pole history:

```text
da/dTT = −n (a · dn/dTT),
db/dTT = −n (b · dn/dTT),
dC/dTT has rows (da/dTT, db/dTT, dn/dTT).
```

Thus one prepared exact-event origin and a qualified local pole derivative
are sufficient mathematically. The definition does not require repeating the
13–18 minute origin-history integration at neighboring events just to estimate
velocity. This is a local derivative consequence, not interpolation, a new
persistent cache or a numerical acceleration result.

Differentiate the intended normalized pole model, including normalization and
its precession/nutation terms, not a piecewise staircase of binary64 output.
Whether local derivatives are analytical or evaluated by an admitted numerical
method remains a concrete implementation choice. Numerical differentiation
would need scale-aware steps, convergence/roundoff evidence, admitted stencil
support and refusal on failure; no step size or rate accuracy is selected here.
The R3 origin convergence estimate alone supplies no velocity-error bound.

### Rate discontinuities, domains and barycentric composition

R1 deliberately retains piecewise polynomial joins. Its decimal TT year also
uses the actual Gregorian calendar-year length, so its time derivative can
change at year boundaries adjacent to leap years. This is a property of the
accepted convention, not evidence of instantaneous physical changes in Earth
spin. Differentiate each admitted smooth piece with the correct year-length
factor; do not assume every decimal year is 365.25 days.

**Definition-level refusal rule:** do not advertise a unique instantaneous
velocity where the selected mathematical position/time model is discontinuous
or lacks a common two-sided derivative. Identify the offending boundary; return
no required velocity or apparent result. Position-only behavior keeps its own
existing admission. No smoothing, averaging, one-sided substitute at a model
join or constant-spin fallback is selected. Metadata-only regime changes do
not by themselves prove a mathematical discontinuity; assess the actual model.
Derivative evaluation support must also stay within admitted orientation/time/
ephemeris domains. At a finite coverage edge where the mathematical model is
smooth, an appropriately qualified one-sided numerical method may be proposed;
it must not extrapolate or be confused with defining a derivative at a kink.

Let the admitted IAU transformation express the barycentric observer position
as x_obs(t)=x_E(t)+δx_IAU(t), in a single declared barycentric coordinate scale.
Here δx_IAU is the transformed displacement under that definition, not merely
the rotated Euclidean site vector. Then, in the same time parameter t:

```text
v_obs(t) = v_E(t) + d(δx_IAU)/dt.
```

Consume JPL's returned v_E. Apply the chain rule to the same retained IAU
transformation and TT/TCG/TCB/TDB relationships used for x_obs, including
position-dependent time terms where retained. Do not append an independently
assumed local velocity or count the Earth term twice. If retained spatial terms
need additional ephemeris derivatives, such as Earth acceleration, obtain and
qualify them through the admitted ephemeris owner; position/velocity availability
alone does not prove those derivative capabilities. No hidden zero derivatives,
new resource acquisition or planetary integration is authorized here.

Bind returned velocity to its position event, site, full orientation/rotation,
time/spatial policies, ephemeris and derivative algorithm/support/units. Keep
unknown physical, numerical and rate errors separate; refuse unavailable
accuracy guarantees. Later independent tests must cover fixed-axis uniform
spin, moving-pole/origin contributions, time-rate factors, R1/calendar joins,
resource/coverage edges and derivative consistency with the composed position.
Use an independent admitted modern state-transform reference under matching
policies; its frame labels alone do not qualify the ancient nominal model.
No velocity implementation, test result or apparent-observer product is claimed
by this definition. Position-only geometric output must not advertise velocity.

## Output capabilities and correction ownership

Output meaning is mandatory, independent of display axes or chart style.
Fernando selected geometric, vacuum apparent and refracted outputs with “The
three of them” on 2026-11-03, then accepted SOFA/ERFA for refraction with
“SOFA/ERFA is OK. Proceed.” These are agreed capabilities for the new route,
not implemented products, an output default or automatic fallback stages.

| Quantity | Necessary inputs and meaning | Must not imply |
|---|---|---|
| Nominal orientation-only local direction | Admitted source direction and exact-event R3 matrix/local axes; source origin/status retained | Topocentric parallax, aberration, distance or an apparent observation |
| Simultaneous geometric topocentric direction/range | Compatible finite source/Earth/site positions at one admitted event; subtract observer position once and normalize | Light-time range, apparent place or refraction |
| Vacuum apparent direction | Explicit admitted correction policy and required source/Earth/Sun/site PV; identified intermediate stages | Atmospheric or measured ancient accuracy |
| Refracted apparent direction | Selected SOFA/ERFA atmospheric model applied to the admitted vacuum apparent direction, with explicit atmosphere/wavelength and qualified domain | A default part of vacuum output or a reconstruction of actual ancient weather |

An orientation-only local direction is an explicit approximation capability;
it must not be selected automatically when parallax/corrections were required.
For modern charts preserve all source stars and available measured parallaxes.
An angular propagation model does not mean zero source parallax. Before modern
adoption, define measured-parallax application for reduced-input stars,
nonpositive/uncertain parallax and missing-distance cases without silently
discarding stars or manufacturing positive distances. A single finite-Cartesian
input gate cannot become a new catalogue population filter. Ancient model
unavailability remains distinct from modern source availability.

For a future apparent policy, enumerate applied and omitted operations and
their order. Reuse the existing finite-source solar-monopole/combined-aberration
owners where their admitted references and domains apply; do not force remote
inputs into the modern frozen ERFA context. Annual and diurnal displacement
and aberration each occur once, not again in a downstream library. Additional
stellar light time, retarded deflectors, planetary deflection and multipoles
remain omitted unless separately selected. Existing solar-system light-time
owners retain their own contracts; this task adds no new planetary observer.
Fixed boundaries/contours/grids remain geometry, with no invented parallax.

### Selected SOFA/ERFA refraction contract

The initial model is the SOFA-derived ERFA `refco` coefficient model, with a
qualified application of its refraction convention. Optical/IR use is the
initial scientific context; selecting the library does not qualify a radio
product or a separate low-altitude ray-tracing model. Hohenkerk–Sinclair and
Bennett/Sæmundsson alternatives are not selected.

The model relates vacuum and observed zenith distances by

```text
z_vacuum − z_observed = A tan(z_observed) + B tan³(z_observed).
```

The argument is the refracted zenith distance. The forward application must
respect this implicit relation and qualify the chosen numerical application;
evaluating its right side at the vacuum angle is not the defining equation.
The atmosphere record supplies pressure at the site in hPa, temperature in °C,
relative humidity on [0,1], and wavelength in micrometres. Sea-level-corrected
pressure is not the required site pressure. Preserve original units, input
provenance, model/backend version, coefficients and the application method.
A declared atmospheric scenario can support an ancient/future calculation;
it does not recover the actual weather. No atmospheric defaults are selected.

Apply this atmospheric operation once to the vacuum result. Keep all three
quantities bound to the same site/event/source and correction identities, with
separate availability and atmospheric assumptions. Missing atmospheric inputs
must not silently become zero pressure or a vacuum result labelled refracted.
The chosen product policy must explicitly refuse or report an unavailable
requested capability. Selecting all three capabilities does not require every
source to supply every quantity or authorize dropping catalogue rows.

The existing modern `ErfaReceptionBackend` prepares zero refraction coefficients;
its frozen context admission rejects nonzero `refa`, `refb` and `diurab`.
Preserve those vacuum/integrity guards. ERFA `atioq` also performs orientation
and diurnal aberration: rerunning a complete observed-place transformation on
an already corrected vacuum direction risks duplicate operations. Define the
atmospheric seam in the existing observer owner; do not mutate a modern context
or relabel the R3 orientation as one. No wrapper or API is implemented here.

Accuracy must depend on altitude and atmospheric knowledge. ERFA `atioq` gives
conditional optical performance of about 0.05 arcsec for zenith distances below
70°, better than 30 arcsec at 85°, and better than 20 arcmin at the horizon,
assuming accurate meteorology and no gross local effects. These are backend
statements, not Wenu-certified bounds. Forward/inverse agreement is a separate
numerical diagnostic. Numerical safeguards near the horizon do not establish
physical admission. The later implementation must define finite angle/input
domains, requested-accuracy refusal and explicit low-altitude status; this
agreement chooses no universal cutoff or below-horizon ray solution.

The coefficient model omits explicit height effects apart from pressure,
latitude dependence and variable tropospheric lapse rate. WGS84 ellipsoid height
still owns site geometry; terrain, horizon depression, local vertical anomalies
and anomalous atmospheric profiles are not supplied by this model. Keep
atmospheric-input uncertainty, model discrepancy and numerical error separate
from the vacuum error channels; unknown physical errors remain unknown.

## Immutable result, reporting and refusal

The future service returns an immutable result binding site/assumption identity,
exact requested and actual events, time conversions, R1/R3 identities and
matrices, source/resource hashes, spatial composition and correction policy.
Carry frame, physical origin, position status, distance/velocity capabilities,
applied/omitted operations, output units and singular/unavailable statuses.
Reports must distinguish nominal orientation-only, geometric, vacuum apparent
and refracted quantities, including atmospheric assumptions and availability.
Do not claim a universal public record class, TOML/CLI syntax, serialization
format or SDK version in advance of implementation review.

Keep separate error channels for source measurements/motion, chronology,
TT/TDB realization, Delta-T/spin, pole/origin orientation, site, ephemeris,
spatial composition, corrections and numerical computation. Each value must
state units and interpretation (bound, standard uncertainty, diagnostic estimate
or unknown); unknown is not zero. No quadrature or independence is inferred.
R3 convergence estimates are not certified total bounds. Reject a requested
accuracy guarantee when a required bound is unavailable.

When timing/rotation uncertainties are supplied, propagation must respect the
chosen model/domain and remain separate from physical unknowns. No universal
15 arcsec/s bound, near-horizon linearization or rise/set timing accuracy is
inferred from a central direction. Horizon events require a separately selected
time-search and uncertainty contract; this exact-event task supplies none.

Refuse wrong scales/events, incompatible references, missing required inputs,
unsupported corrections, altered site/resource/backend identities, expired
coverage, nonconvergence and unqualified velocity. Optional missing quantities
stay explicitly unavailable under the requested capability. No hidden fallback,
download or mutation. Future worker transport needs explicit immutable input
admission and process-local ownership; it is not implemented by this definition.

## Review gate and later acceptance

For this documentation task, execute the complete existing `documentation`
gate on the Mac, check links/anchors and unchanged source inventory, and review
the candidate semantics. Reuse R3 evidence; do not repeat its long integrations.
The [testing policy](../testing_policy.md#earth-bound-observer-contract-definition-gate)
separates this definition gate from later runtime qualification.

Before selecting runtime scope, resolve these concrete choices together:

1. Preserve the agreed fixed WGS84/geodetic/ellipsoid-height convention;
   qualify actual site heights and review remaining numeric/local-axis details.
2. Design the selected ephemeris-based TT/TDB realization and its explicitly
   selectable equality/full-ERFA alternatives; qualify actual resources and
   finite domains. Preserve the agreed IAU/GR spatial convention; design and
   qualify the retained approximation order and terms.
3. Review/qualify the derivative-consistent site-velocity construction and its
   local numerical/rate admission, including R1/calendar joins. Preserve all
   three agreed outputs and SOFA/ERFA refraction; design the ordered correction
   policy, atmosphere inputs, numerical application and finite admission before
   runtime. Do not claim apparent capability from position matrices.
4. Agree capability-aware modern measured-parallax/missing-input treatment
   before population-preserving chart adoption.
5. Select exact finite events/resources and independent numerical references
   for the first implementation gate. No supported observer interval is granted
   merely by the accepted R3 orientation target.

Later runtime tests must cover independent ellipsoid/local-triad geometry,
longitude sign, poles/zenith/nadir/wrap/horizon cases, site velocity/reference
composition, exact time/event/resource binding, Earth-centre/EMB confusion,
distance-dependent capabilities, correction duplication/omission, wrong domains,
accuracy refusal and request isolation. Refraction acceptance additionally needs
independent coefficient/application references, correct observed-angle/sign/units,
zenith/altitude-domain cases, zero-pressure numerical limit, invalid/missing
atmosphere refusal, no duplicate corrections and unchanged vacuum results.
A zero-pressure test does not authorize missing-input fallback. Modern reference agreement must be
compared under matching policies; remote tests establish numerical composition,
not historical physical accuracy. Product adoption separately needs actual
Python/CLI/serial/spawn and visual horizon receipts, including a qualified
Nineveh-era and future example. None is claimed executed by this contract.

## Primary references checked 2026-11-03

- [IERS Conventions (2010), Chapter 5, Eq. 5.1](https://iers-conventions.obspm.fr/content/chapter5/icc5.pdf): terrestrial/geocentric axes and pole/rotation/origin separation. Wenu uses the inverse-direction convention M above; R3 is a named nominal extension, not measured ancient ITRF/GCRS realization.
- [IAU 2006 Resolution B3](https://iauarchive.eso.org/static/resolutions/IAU2006_Resol3.pdf): defining TCB/TDB relation, distinct from the TT/TDB realization.
- [ERFA `dtdb.c`, SOFA-derived implementation notes](https://github.com/liberfa/erfa/blob/master/src/dtdb.c): its stated nanosecond comparison covers 1950–2050 relative to DE405 time ephemerides. This is not a ±13000-year accuracy claim or selection of an extrapolated model.
- [Accepted orientation definition and component ledger](nominal_earth_orientation_meridian_contract_v1.md), [scientific limits](../scientific_contracts.md#planned-ancient-and-future-earth-bound-observers) and [roadmap](../kernel_roadmap_v0.9.5.md#k4b08-earth-bound-observers-at-ancient-and-future-epochs) retain the project-specific assumptions and acceptance boundaries.

- [IAU framework: Soffel et al. (2003)](https://arxiv.org/html/astro-ph/0303376v1) and [USNO Circular 179, Section 1.4](https://aa.usno.navy.mil/downloads/Circular_179_bw.pdf): adopted reference-system formulation within GR, β=γ=1; PPN extensions are separate.
- [JPL/NAIF SPK required reading](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/spk.html): ephemeris position/velocity states and resource coverage.
- [JPL/NAIF state transformation interface](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/sxform_c.html): position/velocity frame transforms. This is a reference for the state-transform distinction, not selection of SPICE Earth orientation for R3.

- [ERFA `refco.c`](https://github.com/liberfa/erfa/blob/master/src/refco.c): selected coefficient equation, observed-angle convention, atmospheric input units and model omissions.
- [ERFA `atioq.c`](https://github.com/liberfa/erfa/blob/master/src/atioq.c): atmospheric application, conditional altitude-dependent accuracy, numerical safeguards and other operations that must not be duplicated.
