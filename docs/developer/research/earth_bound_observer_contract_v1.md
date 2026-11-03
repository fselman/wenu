# Earth-bound observer: site, event and output contract

Version 1 · 2026-11-03 · K4b.08 selected definition; candidate for review

## Selection and boundary

Fernando selected this contract-definition task with “Proceed” on 2026-11-03,
then confirmed clean synchronized Mac main
`cd5c9b76c6fc25df6adb26b2a086aabf44e5e581`. It is a bounded definition under
the existing K4b.08 parent, not a new runtime milestone or authorization to
activate the parent backlog. This document defines required semantics and
identifies decisions needed to select a later implementation. Accepted site/time choices are identified below; the remaining scientific
choices are review proposals, not already adopted policies.

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
bounded implementation design. The spatial-composition choice remains open.

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

**Unresolved implementation choice:** qualify a named nominal Newtonian
site-displacement composition, including TDB-compatible spatial scaling and
its omitted relativistic terms, or select a more complete geocentric/barycentric
transformation. The modern APCO result does not qualify either over ±13000.
This document does not authorize a new relativistic engine or weaken existing
state-reference guards. State translation must have one owner and occur once.

For a constant terrestrial site, mathematical differentiation gives
v_site(TT)=d(Mᵀ)/dTT · r_site. A constant nominal angular speed times r_site
does not automatically implement that derivative. R1 exposes no rate contract;
its retained piecewise Delta-T jumps need explicit handling. R3 exposes no
matrix derivative. Before aberration, select and qualify a site-velocity policy,
including time-rate/spatial conversion to the Earth PV convention. Either a
consistent derivative or a separately named spin-only approximation needs
its own assumptions/error disclosure and join refusal/handling. No numerical
differencing, smoothing across R1 joins or omitted pole-rate term is silently
authorized. Position-only geometric output must not advertise observer velocity.

## Output capabilities and correction ownership

Output meaning is mandatory, independent of display axes or chart style.
Candidate capabilities below describe distinct quantities, not fallback stages.

| Quantity | Necessary inputs and meaning | Must not imply |
|---|---|---|
| Nominal orientation-only local direction | Admitted source direction and exact-event R3 matrix/local axes; source origin/status retained | Topocentric parallax, aberration, distance or an apparent observation |
| Simultaneous geometric topocentric direction/range | Compatible finite source/Earth/site positions at one admitted event; subtract observer position once and normalize | Light-time range, apparent place or refraction |
| Vacuum apparent direction | Explicit admitted correction policy and required source/Earth/Sun/site PV; identified intermediate stages | Atmospheric or measured ancient accuracy |
| Refracted direction | Separately selected atmosphere/wavelength model and domain | A default part of vacuum output; not selected here |

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

## Immutable result, reporting and refusal

The future service returns an immutable result binding site/assumption identity,
exact requested and actual events, time conversions, R1/R3 identities and
matrices, source/resource hashes, spatial composition and correction policy.
Carry frame, physical origin, position status, distance/velocity capabilities,
applied/omitted operations, output units and singular/unavailable statuses.
Reports must distinguish a nominal horizon from an apparent vacuum direction.
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
   finite domains. Select the separate spatial-composition policy; existing
   native states do not decide it.
3. Select geometric versus apparent first output; apparent requires a qualified
   velocity policy, including R1 joins. Do not claim it from position matrices.
4. Agree capability-aware modern measured-parallax/missing-input treatment
   before population-preserving chart adoption.
5. Select exact finite events/resources and independent numerical references
   for the first implementation gate. No supported observer interval is granted
   merely by the accepted R3 orientation target.

Later runtime tests must cover independent ellipsoid/local-triad geometry,
longitude sign, poles/zenith/nadir/wrap/horizon cases, site velocity/reference
composition, exact time/event/resource binding, Earth-centre/EMB confusion,
distance-dependent capabilities, correction duplication/omission, wrong domains,
accuracy refusal and request isolation. Modern reference agreement must be
compared under matching policies; remote tests establish numerical composition,
not historical physical accuracy. Product adoption separately needs actual
Python/CLI/serial/spawn and visual horizon receipts, including a qualified
Nineveh-era and future example. None is claimed executed by this contract.

## Primary references checked 2026-11-03

- [IERS Conventions (2010), Chapter 5, Eq. 5.1](https://iers-conventions.obspm.fr/content/chapter5/icc5.pdf): terrestrial/geocentric axes and pole/rotation/origin separation. Wenu uses the inverse-direction convention M above; R3 is a named nominal extension, not measured ancient ITRF/GCRS realization.
- [IAU 2006 Resolution B3](https://iauarchive.eso.org/static/resolutions/IAU2006_Resol3.pdf): defining TCB/TDB relation, distinct from the TT/TDB realization.
- [ERFA `dtdb.c`, SOFA-derived implementation notes](https://github.com/liberfa/erfa/blob/master/src/dtdb.c): its stated nanosecond comparison covers 1950–2050 relative to DE405 time ephemerides. This is not a ±13000-year accuracy claim or selection of an extrapolated model.
- [Accepted orientation definition and component ledger](nominal_earth_orientation_meridian_contract_v1.md), [scientific limits](../scientific_contracts.md#planned-ancient-and-future-earth-bound-observers) and [roadmap](../kernel_roadmap_v0.9.5.md#k4b08-earth-bound-observers-at-ancient-and-future-epochs) retain the project-specific assumptions and acceptance boundaries.
