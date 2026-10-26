# Current scientific contracts and paused work

## K4b.06 native stellar integration candidate

The explicit Python native atlas-sheet opt-in uses only previously admitted
full Gaia, angular Gaia and nominal-TCB Hip2 models. Source/model/event ownership
belongs to stars and their adapter. Lines and labels consume stellar positions;
they do not gain independent astrometry or epoch policy. Source identity,
photometry, names and constellation membership remain fixed. Retained source
membership and propagated label-anchor directions have separate meanings.

Model order is caller-supplied. Only declared missing-input availability selects
a later supplied model; an SDK/domain/integrity/numerical refusal aborts without
substituting another model or original static coordinates. Available geometry
carries its common TCB event; gaps carry explicit reasons. Physical accuracy and
unresolved Hip2 conventions/covariance remain unknown. The implementation does
not close #326/#333 or K4b.06, adopt improved sources, transform historical
observers, change native defaults or qualify all other sky layers.
The bounded native-sheet slice passed 59 Mac runtime and 36 documentation cases,
actual cold/restored source workloads and Fernando's visual review in PR #346,
merged at `ab8a7e9a`. These receipts preserve the physical-accuracy limits above.

## K4b.05 qualification status

The [current post-comparison review](kernel_migration_audit_v1.md#k4b05-qualification-review-after-reference-comparisons-2026-10-26)
supersedes the earlier comparison-pending matrix. Independent nominal numerical
checks, the [finite perspective comparison](kernel_migration_audit_v1.md#k4b05-finite-perspective-comparison-2026-10-25),
and the bounded ESA/literature assessment executions are complete. Detailed ESA
agreement is inconclusive; Kaler's Dipper gives qualitative agreement only.

These receipts do not establish physical ancient-position accuracy or a physical
lookback interval. Numerical reuse bounds, conditional formal covariance,
hypothetical convention/RV sensitivities and visual agreement remain separate.
Source issues #326/#333 stay open; no conversion, covariance repair, prior,
binary veto or new model is admitted. Full/angle model differences can be large
for particular stars and epochs, so no universal angular-only accuracy follows.

Fernando accepted these limits for nominal historical reconstructions on
2026-10-26 after 36 Mac documentation tests passed in 3.65 s at `a8c0dd08`.
K4b.05 is closed for that bounded intended use. Physical-accuracy guarantees,
verified Hip2 native time/covariance and optimal per-star source selection are
not established. #326/#333 and pending sibling scope remain open; K4b.06
consumer/atlas adoption remains separate. This status update changes no existing
capability, uncertainty, time/frame or refusal contract.

## Hipparcos-2 time-convention qualification

The accepted nominal-TCB fallback retains the original null source epoch scale.
The [time-convention assessment](kernel_migration_audit_v1.md#k4b05-hipparcos-2-time-convention-assessment-2026-10-24)
separates reference-epoch event assignment from proper-motion rate conversion.
Its synthetic TDB/TCB calculations are sensitivity examples, not evidence of
the 2007 catalogue's time scale, a TT conversion or physical uncertainty bounds.
The accessible source review does not establish both native conventions.
Issue #326 remains open; production inputs, model identities and unknown
convention errors remain unchanged. No new conversion or consumer adoption
is admitted.

## Hipparcos-2 covariance qualification limits

The maintenance-only standard-solution reconstruction uses the corrected CDS
encoding and a separately declared published-error normalization. Its matrix
is not a production uncertainty record. Numerical positive definiteness and a
small solve residual do not establish consistency with quoted formal errors.
Printed precision is disclosed; discrepancies are neither removed by rescaling
nor assigned a universal empirical acceptance threshold.

The primary recipe's source-covariance normalization is kept separate from its
catalogue-combination weighting choice. Nonstandard solutions need their own
evidence and, where applicable, complete annex matrices; a leading normal block
does not supply the full marginal covariance. No catalogue merge or new
association policy is introduced.

[Issue #333](https://github.com/fselman/wenu/issues/333) tracks large diagonal
discrepancies, including but not limited to records with stored F2 exactly 99.
The follow-up [precision assessment](kernel_migration_audit_v1.md#k4b05-hipparcos-2-source-precision-investigation-2026-10-23)
finds that ordinary two-decimal precision does not explain large mismatches in
the tested exploratory enclosures. This does not validate the other rows or
establish the meaning of F2=99. Clipping/saturation remains a hypothesis.
Hip2 covariance/position-error
propagation, physical accuracy and epoch-scale qualification (#326) remain
unadmitted. See the
[qualification interface](implementation_reference.md#hipparcos-2-covariance-qualification-report).

## Offline angular measurement errors

K4b.05's maintenance report validates Gaia error/correlation fields and the
correlation eigenspectrum, then propagates the position/PM marginal through
the normalized angular model. Output formal axes are local linearized standard
deviations conditional on that model, not total errors, hard confidence bounds
or physical lookback certificates. Even a positive-semidefinite matrix does not
establish that a long extrapolation remains in the linear regime.

The source normal triad is held fixed for parameter differentials; the motion
vector differential includes its normal component. Alpha-star errors are local
tangent increments, never differentials of alpha*cos(delta). Parallax and
pseudocolour are marginalized, not conditioned to exact nominal values.
The target basis is a transported tangent plane; covariance axes are not a
new celestial reference frame. Source/model/SDK uncertainty records remain unknown
where previously unknown, with native TCB and separate TT frame labels intact.

Missing-RV sensitivity is explicitly around a hypothetical zero-RV anchor,
with reciprocal positive source parallax as a distance proxy only. It supplies
neither a missing RV measurement nor its probability distribution. Full RV
covariance independence, Hip2 weight reconstruction, binaries/systemic motion,
nonlinear uncertainty coverage and ancient physical accuracy remain unqualified.
The [report interface](implementation_reference.md#offline-gaia-conditional-uncertainty-report)
preserves missing/invalid per-HIP statuses and immutable source identities.

## Long-term mean axes (K4b.04)

Explicit long-term frame orientation uses corrected Vondrak/Capitaine/Wallace
2011/2012 through ERFA, with frame bias, a finite caller TT domain inside
J2000 +/-200000 Julian years, and a separately explicit TT equinox. Native
source/motion state epochs remain unchanged on their original axis (TCB for
Gaia/Hip2 motion); frame orientation is not propagation or implicit TT/TCB
conversion. Derived views retain original SDK batches and source uncertainty.
The first-order-bias matrix is only near orthogonal; normalized direction
application is not a new state/error/reuse admission. Model identity binds the
actual matrix/backend and exact TT input/domain.

Published qualitative historical/remote accuracy and measured modern inter-model
differences are not certified physical bounds. Physical and total implementation
orientation errors remain unknown; requested guaranteed physical accuracy refuses.
No nutation/Earth rotation/polar motion/observer translation, ancient EOP/Delta-T,
new light-time/aberration, source rewrite, chart default or issue #326 resolution.
See the [API](implementation_reference.md#explicit-long-term-frame-orientation).

## Historical date semantics (K4b.03)

Explicit proleptic calendar and year-numbering labels are coordinate input,
not a physical historical time realization. Astronomical year 0 is 1 BCE;
BCE/CE labels require positive years. No calendar reform or civil time scale
is inferred. Native TCB requests use a separately admitted conversion receipt;
missing TT/TAI-to-TCB authority refuses rather than relabels. Unknown input-date
uncertainty remains unknown, separately from source-coordinate calendar rounding
and conversion numerical error. Converting the nominal event does not convert
an uncertainty interval or certify angular/physical accuracy. Keep the historical
receipt alongside native query results. No UTC/UT1/Delta-T, ancient observer,
precession or issue #326 resolution is admitted by this input boundary.
See the [API contract](implementation_reference.md#historical-calendar-input-and-nominal-tcb-epochs).

**Baseline:** `6708f54a` (2026-10-17). These invariants survive documentation
cleanup and the future kernel migration. Archived audits retain detailed
proofs and source receipts; moving them does not revoke a compatibility promise.

Open clusters retain mean Dias motions in the curated table. The original Hunt
photometric derivatives omit the published motion fields; the source-bound
astrometry companion now recovers them for the existing 509 Hunt-centred rows
(502 with radial velocities), preserving four Dias-only rows as unadopted.
Offline enrichment leaves the selected catalogue and default charts unchanged.
The ReadMe declares densest-point ICRS centres at epoch 2016.0 and mean cluster
motions, with RA motion multiplied by cos(dec). Errors of means, dispersions,
distance percentiles and masks retain their separate meanings. The raw cluster ReadMe has no explicit epoch-scale/origin declarations; the
qualification below records inherited conventions separately. Cluster-mean
covariance and centre-model accuracy remain unknown. Default chart cluster positions are not
propagated. A source lookup must not claim zero motion, date accuracy or a
fabricated measurement epoch. Public/native cluster centres and observer
transformation inputs now use the accepted SDK `catalogue_lookup` capability.
Qualified source epochs are retained; unqualified labels remain text, with no
invented scale or numerical epoch. Returned positions control geometry/cache
identity, and failures propagate. Source fields/units/masks are bound into an
immutable derived identity without adopting a cross-source motion solution. See the
[source and motion audit](kernel_migration_audit_v1.md#open-cluster-motion-and-lookup-audit-2026-10-18).

The separate [source qualification and propagation contract](kernel_migration_audit_v1.md#cluster-propagation-qualification-and-model-contract)
records documented inheritance rather than altering the original v1 facts. It
resolves Hunt's Gaia time/origin conventions and the four Dias RA-motion
conventions, while retaining unproved centre-epoch lineage and uncertainty gaps.
A future physical provider must distinguish full and explicitly reduced models,
source/nominal accuracy and computational reuse. A motion-derived update interval
alone is not an absolute sky-accuracy guarantee. Default lookup remains unchanged.

The explicit nominal cluster provider now implements that contract's first
numerical subset: qualified immutable input solutions, Astropy spherical
differentials and SI rectilinear motion in explicit TCB coordinate time. A finite
caller-declared model domain is mandatory and is not physical validity. Measurement,
centre/model and input-conversion errors remain unevaluated. Numerical direction
bounds and conservative reuse certificates are now verified against the admitted
binary64 SI rectilinear model. Requests below the direction numerical floor and velocity output on the direction
admission are refused; the explicit Cartesian admission now retains SI PV. This computational bound is not an absolute sky-accuracy
guarantee. Missing RV/epoch solutions remain visible
and unavailable. The model deliberately omits an additional light-time correction;
it is not a full relativistic stellar propagation or ancient cluster reconstruction.
No default chart or saved-sky source-lookup semantics change. Explicit native
Python chart calls may supply the admitted motion catalogue and a TCB evaluation
context. Returned states retain source/evaluation/anchor times and unknown physical
errors; neighbouring static layers are not relabelled as propagated. Restored
source snapshots inherit this route without storing evaluated model states.
Observer-dependent motion is refused until its realization contract is admitted. See the
[implemented API](implementation_reference.md#nominal-cluster-motion-provider).

## Diffuse contour metadata limits

K3.16 preserves original diffuse source properties and byte/geometry identity.
Milky Way source frame/epoch declarations remain absent; existing ICRS/degree
chart encoding is a compatibility policy. Cloud products explicitly declare
ICRS/degree axes, but Gaia DR3 derivation does not establish a morphology epoch,
distance or physical origin. No motion or morphology evolution is introduced.
New v6 saved skies preserve the envelope; v1–v5 retain explicit legacy gaps.
See the [single runtime/format contract](implementation_reference.md#diffuse-contour-source-admission-and-saved-skies).

## Object-independent positional astrometry

The shared `astrometric_state` core now owns complete-SI-input rectilinear
direction/Cartesian propagation and direction numerical/reuse certification. Cluster source ingestion supplies
qualified inputs and explicit model/reference/error meaning through its adapter.
One numerical provider may contain different object semantic types; numerical
work never branches on star/cluster/PN/SNR type. Existing cluster results and
identities are preserved. The explicit full-input stellar adapter now also uses
that same engine; ordinary stellar consumers retain their source lookup.

Fernando's approved 2026-10-19 clarification supersedes the proposed universal
1,000-year proper-motion-only limit. Known position/reference epoch plus both
proper-motion components can admit angular propagation without distance or radial
velocity. Tens of thousands of years may be useful for chart purposes, but no
universal accuracy or safe duration is asserted. State the angular model, source
uncertainties and neglected effects; assess suitability against the requested
angular tolerance. Unknown model errors stay unknown, not zero. Optional explicit
caller bounds are allowed, but missing distance/RV alone must not cause a fixed
short PM-only cutoff. Do not describe this reduced model as complete space motion.

Distance enables distance-dependent observer parallax; radial velocity enables
perspective/full-space-motion treatment when combined with the other required
inputs. These are separate capabilities, not prerequisites for angular PM-only
propagation. The initial approximately 200-year no-measured-PM proposal remains
pending separate reduced-model acceptance; it is not an implemented accuracy
guarantee. The explicit measured-PM angular model below is now implemented;
no-PM approximation remains unimplemented. Unknown motions/RV are never recorded
as measured zero.
Reduced models require explicit approximation/error semantics and their own
acceptance. Expansion, internal dynamics and morphology evolution are excluded.
Stars, clusters, PNs and SNRs retain object-specific source/centre qualification;
in particular expansion velocity or displaced compact-object motion cannot be
silently used as systemic centre motion. Observer realization remains separate.

## Explicit measured-PM angular approximation

The [angular adapter/core contract](implementation_reference.md#explicit-proper-motion-angular-model)
implements the selected measured-PM part of K4b.02/AX.13. It uses declared source
position/epoch and both mu-alpha-star/mu-delta components to admit a unit
source vector `u0` and transverse angular derivative `w` per second. Its nominal
model is `normalize(u0 + dt*w)`, evaluated against the original source epoch;
it is not constant angular speed or repeated extrapolation from previous results.
No distance/RV is inferred or changed in the source. A measured zero PM remains
a measurement; a missing PM stays unavailable. Supplied negative/null parallax,
RV, uncertainty/correlation and quality/component fields remain original facts.

This mathematical approximation omits radial perspective, observer parallax,
light-time changes, binaries and Galactic dynamics. It does not reconstruct a
full physical trajectory. The separately typed angular row has no SI position/
velocity fields and cannot admit Cartesian/observer-PV capabilities. The same
generic affine/cone owner evaluates direction and numerical reuse; object family
does not dispatch numerical work. Its direction rounding/certificate bound is
relative only to admitted binary64 angular coefficients, not source-conversion,
measurement, neglected perspective, age/date uncertainty or physical accuracy.
Those errors remain unknown. Finite caller-declared TCB coverage has no universal
short PM cutoff and is not a physical-validity promise. Constructed tests span
short intervals and +/-50,000 Julian years without claiming real-star accuracy.

Primary reference reviewed 2026-10-22: ESA [DR3 astrometric transformations,
section 4.1.7](https://gea.esac.esa.int/archive/documentation/GDR3/Data_processing/chap_cu3ast/sec_cu3ast_intro/ssec_cu3ast_intro_tansforms.html),
especially its normal triad and normalized-direction relation (equations 4.12
and 4.14). Omitting its radial term gives this declared approximation; it does
not establish that an unknown radial velocity is measured zero. The ESA full
six-dimensional reversible propagation/covariance treatment is distinct; this
angular approximation has no propagated total covariance or external physical
accuracy certification. Existing complete-input stellar/cluster results remain
unchanged. Source-position/no-PM approximations, unresolved Hip2 qualification,
observer/product adoption and historical precession/calendar work stay pending.

## Explicit stellar full-input nominal model

The [stellar adapter](implementation_reference.md#explicit-full-input-stellar-motion)
reads the validated immutable multi-edition snapshot; accepting published identity
and input availability does not turn every Gaia row into a complete motion model.
Only linked five-/six-parameter DR3 rows with position, both proper motions,
positive parallax and measured RV supply the first nominal SI model. The caller
explicitly selects reciprocal-positive-parallax distance and a spectroscopic RV
proxy. Neither is a certified distance/systemic-velocity inference. No zero-point,
binary, companion, perspective-RV calibration or missing-measurement correction
is silently applied. Hip2/original records and all original HIP objects remain
visible; unresolved source conventions and missing full inputs yield unavailable
reasons, never fabricated zero values or independently chosen identities.

Source frame/origin/TCB epoch/units/RA-motion conventions are consumed from the
snapshot metadata. The adapter performs source-to-SI conversion once; the shared
core supplies the existing nominal rectilinear direction/Cartesian model, with
no additional stellar light-time correction. Initial spherical conversion,
measurement/correlations and physical errors remain unbounded/unevaluated; the
core's angular numerical/reuse certificate applies only to its admitted binary64
SI trajectory. Supplied covariance evidence is retained but not propagated.
A finite caller-declared TCB domain is required; no physical-validity date range,
absolute accuracy or historical observer/precession guarantee follows. Quality
and component flags remain evidence and do not veto published links.

Primary source review, 2026-10-22: ESA [DR3 contents](https://www.cosmos.esa.int/web/gaia/dr3)
and [gaia_source data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html)
declare the Julian-year TCB reference epoch, mu-alpha-star proper motion and
spectroscopic barycentric RV. The six-parameter astrometric solution adds
pseudocolour, not RV. These conventions qualify the input interpretation, not
this nominal model's physical accuracy. The first adapter has no acquisition,
observer or product adoption. Reduced-input algorithms remain K4b.02/AX.13;
current star/figure/label/chart/saved-sky behaviour remains unchanged.

## Cluster observer realization contract

**Observer contract, 2026-10-19; nominal finite observer service implemented,
explicit Python chart/saved adoption implemented.** The service below is independent of object type.
PR #261 supplies native chart motion; the explicit reception-context path now
adds observed Python chart/saved motion through the shared finite observer service;
default lookup, accepted native direction/reuse semantics and saved source
snapshots do not change. This contract does not freeze a new Python signature.

### As-is assessment and ownership

`cluster_state.ClusterMotionCatalogue` retains qualified SI
position/velocity and source TCB epochs, and `ClusterMotionProvider` now supplies explicit direction or Cartesian
admissions to the shared engine. The separate SDK already admits `cartesian_state` with
SI `CartesianState` records and explicit velocity availability. No SDK change is
needed for this output. Cartesian publication has its own provider/
admission/reference/model identity, rather than adding a Cartesian flag to the
existing direction admission. That explicit Cartesian output is now implemented:
SI position and velocity preserve distance, source/evaluation times and separate
unknown error channels. No Cartesian accuracy bound or temporal reuse is admitted;
the angular cone certificate remains direction-only. The resource-free TCB/TDB
convention subset is implemented in `astrometric_coordinates`. The observation
owner now supplies reception preparation and the separately admitted nominal
finite-range realizer below. Product adoption remains open.

`OpenClusters.spherical_geometry` currently queries lookup directions and then
uses `sky.observed_cache.catalogue_point_altaz`. That helper passes RA/Dec through
`CoordinateService`; its `SkyCoord` has no distance or velocity. It cannot carry
the admitted cluster Cartesian state or certify finite-distance parallax.
`CoordinateService` owns frame transformations, not epoch propagation. Existing
Solar-System realization solves retarded geometric ephemeris states and has
different timing/units/target semantics; its light-time solver and mandatory
emission-time result are not a catalogue-astrometry adapter.

| Responsibility | Required owner and retained evidence |
|---|---|
| Source admission | Existing cluster metadata/catalogue; same 513 IDs and unavailable-row reasons, original source digests, distance estimator/RV/centre policies |
| Nominal Cartesian evaluation | Cluster provider through the SDK; explicit TCB time/domain, SI position and velocity, original source epoch, model/resource identity, separate error channels |
| Reception/time conversion | Explicit time service/backend admission; original reception instant and every converted instant, split JD/scale, model/resource/coverage and conversion receipt |
| Observer realization | Observation service using admitted backend; observer/site and Earth state, ephemeris/EOP identities, correction policy, coverage and backend versions |
| Projection and output | Existing spherical/domain/projection/preparation/render pipeline; no propagation, time conversion, parallax or apparent corrections in chart style/furniture |

### State and time admission

The Cartesian handoff must consume actual kernel-returned states, not read the
provider's private input rows or rebuild positions from RA/Dec. Preserve selected
order/duplicates and stable object identity. Missing RV/epoch, unknown identity,
wrong source digest, unsupported frame/origin/model, out-of-domain time and a
failed kernel query refuse the complete selected request; no direction-only or
lookup fallback is implicit. Source catalogues remain immutable inputs.

Keep source reference epoch, Cartesian evaluation time and observation reception
time separate. The first nominal observed model evaluates the catalogue model
at the reception event expressed explicitly in its admitted TCB convention.
It must not run a second `apply_space_motion`/proper-motion update downstream.
No implicit UTC/TT/TDB/TCB relabelling or hidden session conversion is allowed.
`astrometric_coordinates.TcbTdbAdapter` now supplies an explicitly registered
TCB/TDB pair to the unchanged SDK TimeService. It preserves split dates and
conversion receipts over a caller-admitted finite source interval. It does not
convert civil time or TT to a barycentric reception event. The separate
`ErfaReceptionBackend` now does that explicit preparation for ISO UTC strings or
TT TimePoints using digest-verified local leap/final IERS-B tables and a
caller-admitted installed backend identity. It preserves UTC, TAI, TT, UT1, TDB
and TCB events, site, model/resources and the explicit SDK TDB/TCB receipt.
TT/TDB is an approximate ERFA DTDB model. Total numerical/time-realization error
remains unknown; therefore it is not misrepresented as a bounded SDK TT/TDB
adapter. Only the separately exact TDB/TCB conversion uses SDK TimeService.
Record conversion numerical error separately from reception-date uncertainty.
An unknown conversion/physical error cannot become a zero bound.

An observer ephemeris time-scale label alone does not prove that its position,
velocity and coordinate scaling are compatible with the nominal cluster state.
The chosen backend must document and test the common spatial/time convention,
including any TCB/TDB-compatible scaling, before subtraction or translation.
The convention transformation is now explicit: IAU 2006 B3 defines the linear
TCB/TDB relation; IERS Conventions (2010) section 1.2 gives
`x_TDB = (1-L_B) x_TCB`. Velocity is unchanged because time and length share
the factor. The generic batch converter retains original SDK states, model/source
bindings and unknown evidence; operation-only rounding bounds are separate.
It does not establish that a particular ephemeris/backend supplies these
coordinates. The input-context backend now explicitly uses ERFA EPV00 Earth
PV and APCO observer PV, with BCRS axes, TDB-compatible au/au-day converted to
SI by the fixed IAU au and SI speed of light. It is an analytic approximation,
not a DE440 or DE405 SPK. No Skyfield resource is substituted. The caller
chooses a finite TT domain, constrained by actual leap expiry and final EOP
coverage and a conservative 1950--2050 model interval. EOP extrapolation and
predicted data are refused. No total time/PV accuracy bound is inferred.
Model-domain coverage, ephemeris coverage, time-adapter coverage and Earth
orientation coverage are checked independently and intersected for observation.
Modern observer data do not inherit the nominal model's long date domain.

### Apply corrections exactly once

The initial model retains the admitted catalogue policy
`light_time=no-additional-correction`. Its transported density-mode/core-mean
solution is nominal catalogue astrometry, not a qualified geometric emission
worldline. Do not feed it into the Solar-System retarded-time solver, apply
`observe()` again or manufacture a light-time/emission timestamp. A future
retarded cluster model requires a separately qualified source/model contract.

The observation service must retain finite distance through the parallax owner.
Use one admitted finite-distance backend path, or an independently admitted
translation plus subsequent correction path; never subtract the observer and
then submit that topocentric vector as barycentric ICRS for a second subtraction.
Choose and record exactly one owner each for observer displacement/parallax,
annual/diurnal aberration, admitted gravitational deflection, frame orientation,
Earth rotation/polar motion and local horizontal conversion. Perspective motion
is already in nominal Cartesian propagation. Refraction remains vacuum for the
first model, matching the current observation contract. Unsupported corrections
are explicit omissions/refusals, not unnamed precision guarantees.

The new reception context only prepares nominal Earth/observer PV and time/EOP
inputs. It applies no target propagation, parallax, light time, aberration,
deflection or refraction. The separate realizer consumes its integrity-bound
frozen ERFA context; backend model version 2 identifies this prepared handoff.
Its WGS84 ellipsoid-height policy is -1000..10000 m, with explicit geodetic
latitude and east-positive longitude. It does not infer an ellipsoidal height
from the legacy Observer elevation. No global IERS/ephemeris configuration or
leap-table update is performed. The actual ERFA leap table must match the
admitted bytes before and after each preparation; a changed global table refuses.

The implemented `realize_astrometric_batch` takes a complete actual SDK batch
for exactly the reception TCB event plus `NominalObservationAdmission`, binding
its full source admission and reception model to the no-additional-correction
light-time policy and `solar-monopole-aberration-vacuum/1`. It converts nominal
TCB-compatible position into the observer's TDB convention and subtracts the
observer exactly once. It retains geometric range and direction, then uses
finite-source ERFA LD with the Sun at reception, ERFA AB with the observer's
combined barycentric velocity, the final-CIP BPN matrix and vacuum ATIOQ.
APCO's diurnal-aberration field must be zero: diurnal velocity was already
included in AB. No `pmpx`, `atciq`, `observe()` or second space motion is used.

The solar limiter is the conventional ERFA solar limiter
`1e-6/max(1,solar_range_au**2)` applied to finite-source LD. Solar reception
position, neglected deflector retardation, planetary deflection and multipoles
are explicit model limits. Solar occultation/visibility is not modelled.
Singular observer/source or Sun/source geometry refuses the complete batch.
Astropy's finite-distance ICRS-to-AltAz path provides a separate composition
comparison; its theoretical CIP differs from this service's final dX/dY.
Independent analytic parallax/range and Lorentz-boost checks remain required;
a same-backend comparison alone does not establish physical accuracy.
No Skyfield SPK resource is substituted for this analytic ERFA model.

### Results, errors, caching and failure

Results must preserve the original Cartesian states and their source/evaluation
times, original reception time and conversions, reference/model/resource IDs,
observer/site, EOP/ephemeris identities, backend versions and applied/omitted
correction policies. The output spherical specification states its actual
observer origin, reception instant/scale and admitted apparent/observed status;
it is not relabelled barycentric astrometry. Range and unavailable emission-time
evidence remain explicit. No existing snapshot is reclassified as an epoch state.

Measurement, centre/physical-model, input conversion, time conversion, observer
resources and numerical-realization errors retain separate meanings. Unknown
channels stay unknown. The current angular certificate bounds only the admitted
native direction; it does not bound range, velocity or translated apparent
directions. Therefore initial observed motion uses full Cartesian evaluation
and full observer realization. The SDK may reuse exact source queries; this
realizer has no observer cache and recomputes corrections even on exact repeats. No temporal
reuse or absolute apparent-accuracy request is admitted without its own proof.

Observation keys must bind returned Cartesian state identity/content/time and
all observer/time/resource/correction inputs above. Lookup and motion results
cannot share a key merely because their normalized RA/Dec agree. A changed site
or EOP/ephemeris/backend invalidates observation, not unrelated provider states.
Validate current provider/time/resource admission before serving a warm cache;
failure cannot be concealed by a previous result. Publish only complete batches.
No global mutable model/backend configuration, implicit downloads, silent
resource substitutions or fallback beyond coverage are permitted. Offline IERS
selection must also reject degraded/out-of-range use rather than merely disable
downloads. Owned/borrowed resource lifetimes follow the existing request owner.

The [acceptance matrix](testing_policy.md#cluster-observer-contract-and-implementation-gates)
and [ordered implementation](kernel_roadmap_v0.9.5.md#cluster-observer-implementation-order)
define the remaining gates. Explicit observed Python chart/saved consumers now
use the accepted nominal service with full Cartesian evaluation and no fallback.
The prepared receipt owns site/event/resources; context fields must agree, and
geometry retains receipt identity and degree units before canonical projection.
Unmigrated layers refuse this context. No observer state is persisted in v5;
Ordinary horizontal CLI/TOML selection now composes this service for selected
clusters only; other layers retain their existing scientific routes. It requires
explicit local resources/code identity, independent finite TT/TCB domains and
qualified WGS84 height. Lookup pre-culling cannot decide propagated membership.
Total physical-error qualification remains pending.

Primary backend documentation checked 2026-10-19:
[ICRS](https://docs.astropy.org/en/stable/api/astropy.coordinates.ICRS.html),
[AltAz](https://docs.astropy.org/en/stable/api/astropy.coordinates.AltAz.html),
[time conversions](https://docs.astropy.org/en/stable/time/index.html), and
[offline IERS policy](https://docs.astropy.org/en/stable/utils/iers.html).
These are backend capabilities/policy references, not a dependency upgrade,
captured numerical oracle, redistribution authorization or proof of the open
spatial-convention admission. Existing deterministic tests acquire no data.

## Hipparcos-2 angular fallback and nominal TCB convention

Fernando explicitly authorized TCB as a nominal model convention on 2026-10-22,
deferring qualification of the original epoch/time-rate convention to
[issue #326](https://github.com/fselman/wenu/issues/326). He confirmed that
J1991.25 is the intended source epoch; the earlier 1991.5 text was a typo.
The earlier prerequisite block is superseded by this policy agreement.

The separate `admit_stellar_hipparcos2_motion` admission requires the explicit
`nominal-tcb-deferred-qualification` epoch policy. The source-declared Julian
epoch value is used on the nominal TCB axis. This is neither a verified source
TCB declaration nor a TT-to-TCB conversion. Captured source metadata retains
its null scale and source bytes/weights/solution/component flags unchanged.
Time-convention, measurement, conversion, covariance and physical errors remain
not evaluated. Later qualification/conversion needs a distinct admitted identity.

Qualified Gaia angular inputs take precedence based on position/both PM and
solution code, independently of parallax/RV or the earlier inventory preference.
Otherwise finite Hip2 radian positions and mu-alpha-star/mu-delta in mas per
Julian year supply separately typed angular coefficients to the existing affine
engine. This nominal tangent approximation omits perspective, acceleration,
binary/orbit/systemic and observer-parallax effects. Nonstandard/photocentre
flags remain evidence, not new component identities or an orbit solution.
No distance, RV, physical velocity or Cartesian/observer PV is fabricated.
All original HIP records and unavailable reasons remain; the 263 original lookup
entries are preserved. Existing Gaia APIs, coefficients and bindings remain
unchanged. No default/chart/observer/saved-sky consumer adoption is added.

Primary review, 2026-10-22:
[CDS I/311](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/I/311?format=html&tex=true),
[NASA HIPNEWCAT](https://heasarc.gsfc.nasa.gov/W3Browse/all/hipnewcat.html) and
[ESA I/311 datamodel](https://gea.esac.esa.int/archive/documentation/GDR1/datamodel/Ch4/hipparcos_newreduction.html)
were read for ICRS/J1991.25 and angular units. The
[2007 author paper](https://arxiv.org/pdf/0708.1752) uses mu-alpha-star; the
[2009 author paper](https://doi.org/10.1051/0004-6361/200811382) defines the
cos(delta) convention in primary indexed text (full PDF not read).
[ESA 1997](https://www.cosmos.esa.int/documents/532822/552851/vol1_all.pdf)
provides TT in primary indexed text, not direct proof of the 2007 declaration.
The [2007 book](https://link.springer.com/book/10.1007/978-1-4020-6342-8)
astrometry chapter remained inaccessible. This is an evidence gap, not evidence
that the 2007 product uses a different scale. The ticket distinguishes an epoch
offset from the time-rate difference and tracks independent catalogue checks.

## Coordinates, time and resources

Frame, origin, position status, catalogue epoch, equinox, evaluation instant
and time scale are different fields. ICRS has no equinox-of-date parameter.
Changing metadata is not propagation or a transformation. A direction without
distance is not a known Cartesian position and cannot support arbitrary
origin translations. `SphericalFrame` is projection alignment only.

Physical state, observer-dependent astrometric/apparent realization and
display geometry must have separate identities. Solve light time once in its
owner; do not apply `observe()` again to an already astrometric solution.
Common frame/centre/time units and exact resource coverage are mandatory.
Provider/cache identities include model, resource digest, policy and relevant
scientific inputs. No silent download, extrapolation, resource substitution or
relabelled coordinate fallback is permitted.

The [coordinate guide](coordinate_system_guide_v0.9.5.md) retains equations,
calendars, frame vocabulary and current implementation limits. The
[roadmap](kernel_roadmap_v0.9.5.md) defines the proposed broader state contract.

## Native stellar lookup during migration

Catalogue facts must be read from validated metadata at ingestion, preserved
in Wenu's standard catalogue envelope and mirrored in the runtime record.
Require reference epoch/time scale, frame/origin, units, edition, source identity
and provenance; preserve original fields and reject missing/conflicting claims.
Do not insert catalogue-specific defaults in a consumer. The current stellar
implementation follows this boundary; the metadata audit in the migration
audit records remaining providers that do not yet satisfy it.

The first K3 adapter exposes finite native Hipparcos directions at source epoch
J1991.25(TT), JD 2448349.0625. It does not propagate to a requested epoch.
ICRS axes do not precess; source epoch is not an equinox. Its kernel reference
status `native-catalogue` is explicit lookup semantics, not apparent place.
Unbounded lookup coverage is not physical validity. No zero proper motions,
distance, velocity or angular accuracy is inferred from missing information.
Measurement, model and numerical uncertainty are explicitly unevaluated.
Finite invalid latitude is refused; missing-coordinate legacy rows remain
outside kernel states and retain NaNs/metadata for existing downstream filters.

Native realization, `Stars.position(instant)`, explicit HIP positions and native
constellation endpoints use this lookup. `position` still ignores instant for
compatibility, but now declares the correct source epoch J1991.25, not the old
incorrect J2000.0 default. Source RA degrees are authoritative when present;
hours-only constructed inputs retain the hours × 15 conversion. This is a
coordinate-encoding/metadata correction, not motion propagation. Native labels
are accepted through K3.07. Accepted K3.08 feeds returned directions into
the existing Skyfield no-deflectors star/figure observation method and Astropy
label method. It preserves their distinct correction policies and accepted
source-hour encoding for unchanged inputs. No correction or motion step is added
by the kernel adapter; kernel refusal cannot be hidden by a warm observer cache.
No historical-epoch or Gaia accuracy claim follows from this adapter.

## Catalogue identity and curation

Nonstellar angular encodings use declared source units when available; the
normalizer converts them to its canonical degrees/arcminutes before geometry.
Incompatible declared units fail before replacing a loaded catalogue. Original
table metadata and unconsumed fields remain available, with independent metadata
copies on geometry. Unitless compatibility inputs are not evidence of source
units, frame or epoch. These preserved facts do not yet constitute complete
scientific admission. `NonStellarCatalogueMetadata` validates and mirrors
declared facts and input-byte identity, reporting absent facts explicitly. Strict
admission refuses missing frame/origin/edition/provenance/units required by the model;
legacy chart interpretation is explicitly `legacy-unverified-catalogue-encoding`.
An unknown measurement epoch is never replaced by an equinox or release date.
The SDK capability `static_direction` admits optional source epochs only for
explicitly static models. It retains source provenance, required evaluation and
anchor times, explicit coverage and separate unknown physical uncertainty.
Native/epoch direction models still require source epochs. No temporal reuse or
infinite validity follows from constancy alone. Galaxy centre routing is now
implemented through the declared static chart model; physical metadata closure
remains open. Its missing origin is explicit in the SDK reference, and all source
facts remain preserved. Shape axes/PA remain domain metadata; only centres enter
the kernel, while the existing geometry/observer/projection owners build outlines.

Galaxy chart directions use the explicit `static-direction` model, independent
of requested epoch over the intended tens-of-thousands-of-years chart use.
Measurement epoch/scale are optional provenance for that model and must not block
its admission. Other providers retain source-epoch requirements unless explicitly
assigned another admitted model. This is a chart model, not an exact law of zero
physical motion or an asserted astrometric error bound. ICRS orientation and
observer-dependent realization remain separate from updating catalogue positions.
Snapshot v5 derives headers from the record; v1-v4 restoration does not turn old
J2000 stamps into source facts. These changes do not establish source frame
precision, a motion model or provider accuracy, or close kernel routing.

An aggregate catalogue does not acquire a common reference epoch merely by
combining rows. Open-cluster positions retain their declared row epoch and
coordinate source; uniformly known selections expose that epoch, whereas mixed,
masked or unknown selections expose no scalar epoch. Frame orientation (such as
ICRS/J2000) is not evidence of measurement epoch. Original row values and masks
survive saved-sky admission; legacy collection-level stamps cannot overwrite them.

Scientific source snapshots, selected atlas membership, astrometry, naming,
component identity and appearance are independent. A new Gaia match must not
silently change catalogue membership, visual magnitude, label or component.
Preserve original IDs, values, source edition and selection criteria.
Unresolved matches remain explicit; a nearest angular neighbour alone is not
a reliable component identification across different epochs.

Star designation review cells and the research dossier remain unchanged.
Shared-star contextual naming and accepted curated names remain in force;
historical blank cells are not a requirement to stop normal label rendering.

## Stellar membership and enrichment contract

K4a.01 defines the logical record `wenu-stellar-enrichment/1` and its
[machine-readable contract and baseline census](data/stellar_enrichment_contract_v1.json).
The logical source contract now has a K4a.04 local snapshot codec. This does not
admit a Gaia physical model/provider or change the saved-sky format. K4a.02 must
qualify current primary source conventions, API/terms and acquisition/matching
policies before any source request; K4a.03–05 admit matches and actual data.

### Retained population and identity

The acquisition target population is the complete original `Stars.source_catalog`,
before magnitude, constellation, viewport, horizon or latest-chart selection.
At the pinned baseline it contains 118,218 unique ordered HIP rows, including
263 rows lacking a coordinate pair and one lacking visual magnitude. The
5.5-magnitude default selects 2,851 rows. The 23,447 multiple-flag and 23,898
variable-flag rows are catalogue classifications, not counts of physical
components or confirmed variable systems. The census is bound to the preserved
Hipparcos source digest and tested separately from the last rendered field.

The retained identity is `(catalogue, edition, identifier, component)`; HIP
identifiers remain the existing public chart/constellation keys. Decimal IDs are
serialized as strings, never floating-point numbers. Component is explicitly
null until supported by component evidence. A HIP entry, CCDM designation,
Wikidata label and Gaia source need not describe the same resolved component.
Null does not mean primary, single star, photocentre or barycentre. Preserve all
original multiple/variable classifications, component measurements and naming
records. Do not split, merge, rename or replace a baseline row through a join.

Each retained row has zero or more edition-qualified candidate counterparts.
Several candidates do not expand chart membership. A foreign source shared by
multiple baseline rows is a conflict requiring explicit evidence/review, not
permission to collapse HIP rows. Cross-release source IDs never imply identity.
Component associations and adopted solutions remain separate from display names.
At most one solution per established component may be adopted by an explicit
policy; adoption does not automatically enable its use by current consumers.

Current chart selection remains the existing magnitude cut OR explicit IDs OR
enabled constellation vertices, followed by the existing detail/visibility rules.
These selections do not define acquisition membership. An explicitly requested
HIP absent from the source, or a missing constellation endpoint, is an unresolved
source obligation: report it without inventing a star or coordinate. Gaia
non-detections, ambiguity, unusable solutions and missing fields never delete a
retained row. Existing lookup remains available; propagated fallback capability
requires its own K4b admission.

### Logical snapshot and row schema

The following names are required logical fields for the future codec. This
contract does not prescribe a container/transport, provider column spelling,
query strategy or numerical matching threshold. Changes of meaning require a
schema version; a Gaia release changes the edition adapter and source metadata,
not the kernel or product API. Unknown top-level extension fields must be
namespaced and preserved; unsupported schema versions must be refused.

| Record / field | Meaning and admission rule |
|---|---|
| Snapshot `schema` | Exact version `wenu-stellar-enrichment/1` |
| `membership_source`, `membership_digest` | Original catalogue/edition, source bytes, ordered retained identities; independent of foreign matches |
| `edition_adapters` | Versioned decoding maps and evidence for each foreign release, including original column names, units, masks and conventions |
| `resources` | Exact source payload digests, provenance and row locators; source facts do not come from filenames |
| `policy_versions` | Explicit matching, component and usability policies, distinct from acquisition receipts |
| `rows` | Exactly one record per retained baseline identity, in original order |
| `coverage_report` | Counts partitioned by match status, missing inputs, ambiguous components and absent requested IDs; not a physical-accuracy certificate |
| Row `identity` | Retained catalogue/edition/identifier/component tuple |
| Row `original` | Unmodified original source fields, missing masks and naming/photometry/component lineage |
| Row `match_status` | One of the six states below; never inferred from non-null numeric values |
| Row `candidates` | Zero or more foreign identities and their source-bound matching evidence |
| Row `adopted_solution` | Null or an explicit reference to an admitted candidate solution; valid only for `adopted` status |
| Row `foreign_photometry` | Separate measurements with passband, source/release, value, unit, error and missingness |

`not_searched` means no matching attempt; `unmatched` means a documented search
found none; `ambiguous` means identity is unresolved; `component_conflict` means
the proposed association has unresolved component/cardinality evidence;
`identified_unusable` means identity is established but astrometry fails the
declared usability policy; `adopted` means an explicit decision accepts a
particular source solution. The first five statuses require a null adopted
solution. An adopted solution must identify its candidate and policy decision;
it cannot silently become a blended or averaged solution. Candidate rejection
reasons survive publication. Search completeness and usability remain separate.

| Candidate solution / evidence | Required content |
|---|---|
| Identity | Foreign catalogue, release, decimal source ID and established component or explicit unknown |
| Reference | Frame, origin, epoch value/format/time scale and spatial convention, each bound to primary source evidence |
| Parameters | Original position, both proper motions, parallax and radial velocity when supplied; names, values, units and masks preserved |
| Uncertainty | Supplied parameter errors and correlations; any derived covariance has explicit parameter order, units, derivation and source lineage |
| Quality | Original solution type and quality fields; versioned usability result/reasons |
| Match evidence | Source resource/row, method, comparison epoch/frame, separation with units, criteria, component evidence, decision/reason and policy version |

Comparison coordinates/epochs used in matching are derived evidence and cannot
overwrite source reference epochs or original values. A separation alone is
insufficient evidence for adoption. Unknown uncertainties/correlations are null
or masked, never a zero-error or independent-error assumption. Missing PM, RV or
distance is not zero; non-positive parallax is preserved without being turned
into a physical distance. A mixed row must retain the separate source and epoch
of each input; a foreign RV must not inherit another solution's epoch/scale.
Preserve PM cosine-declination conventions explicitly at the edition boundary.
The subset retains sufficient source fields to revisit future model admission;
K4a.01 does not choose a propagation or distance-estimation model.

### Photometry, compatibility and acceptance

`Stars.magnitude` remains the existing Hipparcos visual magnitude used for
selection and symbol sizing. Original V values and missingness remain exact.
Foreign G/BP/RP or other bands are separately identified measurements, with no
implicit substitution or colour conversion. Existing contextual naming, curated
labels, legacy IDs, topology and unknown source facts are preserved. Gaia
enrichment must be opt-in at an explicitly admitted consumer boundary; current
native/observed routes and saved-sky v6 do not consume this design record.

The [stellar-enrichment-contract gate](testing_policy.md#stellar-enrichment-contract-gate)
checks the exact full population/photometry census and existing explicit-ID,
vertex and naming selection behavior. The protected faults are population
truncation to the last chart, photometric substitution, or loss of a faint
explicit/vertex row. No fabricated Gaia fixture is presented as a real match.
Current coordinate conventions and numerical implementations are unchanged;
the coordinate guide remains current. Full source/model qualification,
redistribution/publication, propagation and historical accuracy remain open; the
published-association retention policy below is now accepted.

## Offline Gaia candidate evidence

K4a.03 now supplies the [offline audit](implementation_reference.md#offline-gaia-candidate-audit).
Fernando selected it after reporting the completed raw acquisition and integrity
check, and explicitly chose the exact HIP-key pivot from the original 1997
catalogue through Hipparcos-2 to Gaia. This is entry linkage, not a new positional
match between the Hipparcos editions. Preserve each edition's provenance and
specific multiple/component/shared-source conflicts. Do not label every linked
row ambiguous merely because the edition differs.

The acquisition receipt is user-run evidence, not an independently rerun real
catalogue validation here. The terms review below remains deferred; neither it
nor redistribution is declared cleared. The old policy-only text describes that
review's delivery, not the current absence of raw downloaded data.

Common-epoch separations are explicitly nominal angular PM-only consistency
diagnostics, not match criteria, a covariance statistic or a physical propagation
capability. Missing inputs stay null; no RUWE/parallax/RV filter removes a HIP row.
Fernando subsequently explicitly accepted the published best-neighbour associations.
The v2 audit retains the `gaiadr3.hipparcos2_best_neighbour` source ID per exact HIP
key and preserves neighbourhood alternatives separately. No additional threshold,
flag decoding, component review or 1997-motion check is required to retain a
published association. Missing best rows stay unassociated; contradictory best
rows are an integrity error, not a new identity decision. Unusable or uncertain
astrometry does not erase an accepted association; physical/model admission is
separate. Diagnostics are optional, off by default, and cannot veto links.
No 2007 position/PM acquisition or repeat of the published crossmatch is required.

## Kervella supplemental association contract

Fernando selected K4a.03S1 after reviewing the magnitude distribution of HIP rows
without published associations. The [published supplement](implementation_reference.md#kervella-published-association-supplement)
uses only Table A.1's explicitly published `HIP`/`GaiaEDR3` association; it does not
repeat Kervella's positional/magnitude/parallax matching. Preserve the accepted
99,525 primary links. Existing-link disagreements are evidence, not automatic
replacement. Missing Kervella entries or missing EDR3 IDs remain unassociated;
DR2-only IDs cannot become DR3 by numerical equality. Every original HIP entry,
V magnitude, name and component/variability field remains intact.

Record the published EDR3 identity and its resource/row/provenance. The source
profile's primary ESA EDR3/DR3 shared-source-list statement is an explicit bridge,
not an assumption that Gaia IDs persist between all releases. Do not adopt the
paper's corrected parallaxes, calibrated PMs, long-term motions, PM anomalies,
component RVs or physical propagation merely because its identity link is retained.
Source parameter acquisition and K4b model admission remain separate.

Use the captured current table count (116,017), not the paper's 116,343 PMa
sample count, as the parser contract. Record that source-version discrepancy
without inventing a reconciliation. The much larger candidate companion tables
are excluded to prevent confusing a companion's source ID with its HIP parent.
Current attribution/usage evidence and access limits are recorded in the source
profile. The existing deferred Gaia redistribution review remains deferred; the
assessment introduces no broad commercial/redistribution clearance.

## Astrometric input coverage and fallback

Fernando selected K4a.03S2 on 2026-10-22 after accepting the Kervella v3 report:
117,211 published links, 1,007 without an association. Hipparcos-2 is the agreed
fallback input for absent or incomplete Gaia astrometry. An accepted identity is
preserved even when its Gaia fields cannot support motion. Availability is not
model/quality admission; five- and six-parameter solutions, position-only,
incomplete and unknown codes remain distinct. Missing PM/RV is never zero;
non-positive parallax is retained without inversion. No universal RUWE threshold
or companion/component substitution is introduced.

[Explicit capture and offline coverage](implementation_reference.md#astrometric-input-acquisition-and-coverage)
retain original membership, names and visual photometry and bind new inputs to
the original cache and published ledger. Hip2 has fewer rows than original Wenu:
missing/incomplete Hip2 entries remain visible with original 1997 lookup. Hip2
special solution types and full original records/weights remain evidence, without
pretending that every entry is a standard single-star solution. The captured CDS
ReadMe's undeclared epoch scale and RA differential convention must qualify before
propagation. Runtime source selection, uncertainty/covariance admission, K4a.04
publication and K4b propagation remain separate; current charts are unchanged.
The earlier policy review below is historical scope, not a prohibition on this
newly selected bounded acquisition. Its deferred redistribution review remains open.

## Local enrichment source admission

K4a.04 preserves the accepted original population and published identity links in
an immutable local source snapshot. The [codec and publication contract](implementation_reference.md#local-stellar-enrichment-snapshot)
validates original membership/order/visual magnitude, complete loaded original
columns/designations, exact foreign IDs and references, source units/epochs,
uncertainties/correlations/raw Hip2 weights and fallback evidence before publication.
Published identity uses `match_status=identified`; this explicitly separates
association acceptance from `adopted_solution`, which stays null. Missing inputs
and unknown Hip2 time-scale/RA differential declarations remain unknown. No
coordinate conversion, covariance construction, distance inversion, source quality
threshold, component/barycentre inference or new matching occurs.

Snapshot byte identity and detached immutable source reads qualify transport and
source availability only. The full original/captured raw resources stay in their
existing external caches and are identified by digests; the normalized snapshot
preserves parsed values plus native Hip2 record text and source metadata. It is
not a byte copy of every raw response. Local publication does not clear deferred
external redistribution review or activate K4b. Default charts/native lookup,
visual photometry, designation policy and saved-sky v6 remain unchanged.

## Gaia DR3 acquisition and matching policy review

K4a.02 delivers the [dated policy proposal and source audit](data/gaia_dr3_acquisition_policy_v1.json),
reviewed on 2026-10-21 against K4a.01 and main `d447565d`. It does not download
catalogue rows, execute TAP jobs, select a client dependency or implement a
matcher. The proposed rules below require policy acceptance. Permission and
service-preflight gaps remain explicit; K4a.02 is not closed merely by publishing
this review. K4a.03 actual cross-identification and K4a.04 subset publication
remain separate. Current coordinate mathematics and the coordinate guide are
unchanged.

### Primary-source findings and permission boundary

ESA's [indexed Gaia licence page](https://www.cosmos.esa.int/web/gaia-users/license)
states CC BY-NC 3.0 IGO and refers commercial use to the
[ESDC terms](https://www.cosmos.esa.int/web/esdc/terms-and-conditions).
The Gaia@AIP table metadata independently displays that licence. Direct ESA
licence, terms and programmatic-help fetches returned HTTP 451 during this audit;
the indexed excerpts are evidence of a restriction, not a complete terms review.
Do not infer commercial rights from public access, an older permissive summary,
an alternate mirror, or the software licence. Intended use, redistribution and
complete current terms must be recorded before authorizing acquisition or
publication. Commercial Wenu/book/chart use is not cleared by this task.
No provider contact or permission request was sent.

The [ESA DR3 release page](https://www.cosmos.esa.int/web/gaia/data-release-3)
requires release-specific credits/citations. Future receipts must preserve the
then-current ESA/Gaia/DPAC acknowledgement and relevant catalogue/crossmatch
citations. Data attribution must accompany a distributed subset and its
applicable products; it must not imply ESA endorsement. No Gaia rows or full
provider document copies are redistributed in this PR.

The [primary Astroquery Gaia documentation](https://astroquery.readthedocs.io/en/latest/gaia/gaia.html)
documents asynchronous TAP jobs, uploads/joins and local result retrieval. It
describes a 2,000-row synchronous result limit and server-side result quotas;
these are not evidence of current capacity for Fernando's selected endpoint or
account. No live endpoint/capability or quota probe was run. Exact service rules
must be captured before execution. AIP documentation is scientific/schema
evidence here, not authorization to switch acquisition providers automatically.

### Proposed bounded acquisition

Prefer the ESA Archive TAP/ADQL asynchronous route, conditional on successful
terms/capability admission. Use supported bounded ID joins/uploads, with no
whole-catalogue mirror, per-star query loop, spectra or epoch-photometry fetch.
Renderers/tests remain offline. No acquisition runs on import or chart creation.
The first pass targets the complete retained Hipparcos population, independently
of the last chart and V limit, as required by K4a.01.

1. Record the original ordered HIP population/digest. Sort and deduplicate the
   request identities separately without changing membership order.
2. Fetch the corresponding best-neighbour and complete neighbourhood evidence
   in bounded HIP batches. Keep all candidates and flag/score fields.
3. Deduplicate the union of returned DR3 source IDs and retrieve explicit source
   columns only. The JSON proposal lists identity/reference, astrometry,
   uncertainties/correlations, six-parameter auxiliary fields, quality, RV and
   separately named foreign-photometry groups. Verify each field/type/unit on the
   selected endpoint before submission; missing columns stop schema admission.
4. Reconcile locally using the retained population as the left side. A missing
   provider crossmatch remains a retained unresolved row. Count requested IDs,
   returned candidates, shared sources and unmatched/ambiguous cases explicitly.

Proposed **Wenu workload stop caps**, not provider limits or permission:

| Item | Proposed cap / behavior |
|---|---|
| Pilot | At most 100 HIP IDs; inspect schema, cardinality and response status before the full population |
| Batch | At most 5,000 HIP IDs or candidate Gaia IDs per job |
| Concurrency | One active job; no parallel accounts/endpoints |
| Run envelope | At most 128 new jobs, 1,000,000 returned rows and 500 MiB of transport bytes; separately cap expanded payload bytes at 500 MiB |
| Polling | Wait 10, 20, 40, then 60 seconds between polls; at most 40 polls and 30 minutes per job, whichever limit comes first |
| Transient errors | At most two attempts for idempotent requests, at least 60 seconds apart; honor longer `Retry-After` and stop/resume if it exceeds the current run's wait budget |
| Job creation uncertainty | Persist job identity/URL; reconcile an ambiguous POST before any new submission |
| Server or local limit | Stop with an incomplete receipt; never publish a truncated subset as complete |

Use the stricter verified provider limit whenever it is below a proposed local
cap. Lack of readable service rules is an unresolved preflight, not permission
to assume that one job is allowed. Provider refusal, quota errors, authentication
failure and unknown submission state stop the run. No infinite retry, automatic
mirror fallback, silent batch widening or account rotation. Pilot/full batch
submissions and any replacement jobs all count against the run envelope.

Cache by exact endpoint/release/query, membership/batch digest, field schema and
policy version. Preserve raw response bytes before normalization, digest both
raw/expanded representations, and record HTTP/TAP status, job identity, times,
counts and client version. Check result `QUERY_STATUS`, including overflow and
trailing errors, rather than trusting HTTP success. An incomplete/failed batch
cannot become a successful empty match. Validate local cache identity before
reuse. Clean up only this task's own completed jobs after verified local receipt;
never remove unrelated user jobs or infer indefinite server retention.

### Proposed identification and quality rules

The published [best-neighbour](https://gaia.aip.de/metadata/gaiadr3/hipparcos2_best_neighbour/)
and [neighbourhood](https://gaia.aip.de/metadata/gaiadr3/hipparcos2_neighbourhood/)
tables concern **Hipparcos-2**, whereas Wenu retains ESA 1997 I/239. The
[I/311 source description](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/I/311?format=html&tex=true)
identifies the new reduction's HIP key. The exact HIP key is the agreed entry-linkage pivot to the published Gaia
crossmatch. It does not replace original photometry or resolve specific flagged
component/photocentre conflicts. Preserve the intermediate edition
and missing Hipparcos-2 entries in the evidence. Do not substitute a DR2 table
description for DR3 flag decoding.

Fernando's association-retention instruction supersedes the earlier proposed
manual identity-acceptance gate. Trust the published best-neighbour association
through exact HIP keys; preserve full neighbourhood evidence without promoting
alternatives. Do not independently identify by distance, require a common-epoch
check or reject published links for flags/components/quality. Those facts remain
annotations and later astrometric-model admission inputs. No ambiguous-best-row
selection or new positional recovery search is authorized. The frozen JSON
acquisition proposal is retained byte-for-byte because its digest identifies the
completed cache; its earlier proposed identity gates are superseded by this rule.

First-pass `unmatched` means no counterpart in this admitted crossmatch, not
proof of physical absence from Gaia. Any subsequent positional recovery search
needs its own bounded domain, epoch/PM treatment and acceptance criteria; it is
not silently enabled by a missing row.

Retain all candidate solution types and diagnostics; evaluate identity separately
from numerical usability. Preserve original errors, correlations and all supplied
six-parameter auxiliary correlations. Unknown covariance is not diagonal/zero
covariance. Unknown solution codes/units/conventions cannot be adopted. Validate
finite supplied values, coordinate ranges, masks and covariance consistency
before any later model use. Acquisition never imposes a universal RUWE 1.4 cut,
positive-parallax cut or complete-RV requirement that deletes membership.
RUWE, duplication, excess-noise, multi-peak and non-single-star diagnostics are
retained for explicit model-specific review. No parallax zero-point, RV, binary
or colour correction is selected here.

Missing PM/RV/distance remains unknown; non-positive parallax remains a measured
value without naive inversion. Do not borrow an unqualified other-component RV.
Existing Hipparcos source-native lookup and V photometry remain available for
all retained rows. Neither this fallback nor a unique Gaia candidate grants
propagated accuracy; K4b admits those capabilities. Photometry remains governed
by K4a.01, with Gaia bands separate from the original V values.

Acceptance for this review is documentation/tooling integrity and source-policy
review, not a live network test. Full current terms, intended-use permission,
endpoint/flag metadata and service limits remain unresolved execution gates.
The source audit records what was read directly versus indexed or unavailable.

## Fixed celestial scenes and local time

`celestial_anchor_time`, frame `simulation_time`, and `catalogue reference epoch`
have separate owners. A fixed celestial scene and a rotating local horizon
must retain that distinction during kernel routing. Preserve the circumpolar
orientation reference, observer-time complete-render baseline and canonical
fixed-sky reference sequence as distinct products; none is evidence of stellar
proper-motion propagation. Graphical tolerance is separate from angular state tolerance.
Native-state reuse and observation-time updates need separate scientific keys.

## Natural moving bodies

Preserve descriptor-driven IDs and capabilities, the distinction between a
physical body and a provider barycentre ID, explicit manifest-backed minor-body
resources, validity intervals and deterministic closing of request-owned sessions.
Keep symbolic point, resolved disk, photometry and track capabilities distinct.
Display magnification acts after projection about the physical centre.
Track samples preserve their own evaluation instants while chart axes stay fixed.

Comet discovery/model magnitude depends on the stated geometry, model and
resource; it is not automatically a validated visual magnitude. Preserve the
accepted bounded sampling/workload, explicit Horizons transport, cache and
failure behavior. Automatic asteroid-name and provisional/unnumbered selection
remain unfinished; do not describe generic selection as complete.

## Artificial satellites

Preserve immutable digest-bound OMM/TLE snapshots, SGP4/WGS-72 and split-JD
evaluation, geometric TEME versus Earth-fixed/topocentric states, EOP policy,
and independent Vallado/topocentric numerical evidence.

Scalar and array propagation use existing Cartesian kernel transport for returned
geocentric TEME PV. The original split UTC JD remains the SGP4 time argument;
explicit installed-leap TAI labels serve only SDK identity/admission. Exact
finite request coverage is not orbital prediction validity. Complete supplied
record identity, optional snapshot receipt and original element epoch/age remain
explicit; uncertainty/covariance is not evaluated, not zero. No temporal reuse
certificate, freshness cutoff, frame relabelling or new physical model is added.
The original nonzero SGP4 status API and the existing EOP/observer/refraction
refusals remain authoritative. Direct constructed records/states retain their
legacy meaning without new captured-source qualification.

Sampled SatChecker candidates are not exact local connected visits. A
conservative selector cannot discard an exact crossing; fallbacks and
completeness claims must retain their accepted bounded domains. A zero-crossing
field is a valid result, not evidence for untested positive cases or capacity.

Exact/accelerated migration retains the existing independent complete-scan
reference and zero-false-negative invariant within admitted domains, including
explicit indeterminate-to-exact behavior and selector-failure policy. Batch
admission uses current whole-interval altitude/EOP service values before solving.
Solved tracks preserve exact event anchors and bounded midpoint/maximum-step
sampling tests; these do not become a global continuous-error certificate.
Synthetic positive-duration and fresh-process equivalence cases protect service
composition, not new physical accuracy, production capacity or external-source
qualification. Historical production receipts remain pinned historical evidence.

Sampled-provider presentations retain immutable supplied records and their
source-inferred coordinate convention; shared coordinate/geometry services
consume returned values without acquiring or propagating data. Per-sample
UTC/UT1, exact response identity and nullable provider illumination are evidence,
not a new physical-model or covariance qualification. A sampled open polyline
or singleton does not establish continuous containment, entry/exit times or
absence between samples. Existing audited provider constraints and unresolved
redistribution permissions remain unchanged; no current service permission is
inferred from synthetic tests or old receipts.

Exact reports retain canonical JSON identity, strict decoding, ECSV/VOTable
losslessness, explicit nullable Unicode handling, atomic no-clobber file
publication and the distinction between geometric crossing and visibility.
Tracks consume accepted solved evidence through the existing chart pipeline.
The planning advisory does not write to observatory systems. Report and tabular
consumers preserve already solved scientific values without propagation or
coordinate reevaluation. Null future-science fields remain not evaluated;
Unicode text, array order, UTC labels and source/report identities survive all
three interchange forms. CLI validated-subset files are revalidated against
current services and do not certify continued external-resource validity.
Planning overlap remains half-open and does not establish visibility or an
operational action. Synthetic altitude admission and single-instant CLI specimens
verify composition only, not new observation accuracy or crossing completeness.

Direct-Sun geometry, twilight, finite-Sun/WGS-84 shadow transitions and bounded
direct solar irradiance are implemented. Preserve the IAU nominal 1361 W/m²
at 1 au, inverse-square scaling and accepted visible-disk fraction. A nominal
constant does not mean zero physical uncertainty.

Known Skyfield Sun sources for illumination/shadow consumers use the accepted
Cartesian adapter, preserving simultaneous geometric Earth-to-Sun ICRF meaning,
exact source/request/resource identity and existing ITRS/EOP orientation. No
light-time or apparent correction is added to this geometric input. Custom
injected protocols retain their declared meaning. Satellite states retain the
accepted SGP4 transport; typed propagation failures include kernel refusal.
Original finite-disk quadrature, WGS-84 limb/contact geometry and continuous
transition domains/tolerances remain unchanged. Synthetic returned-value seams
verify composition, not new physical accuracy or orbital prediction validity.

The external TSIS-1 HSRS v2 product retains its exact digest, 25,281 native
0.1-nm samples over 202–2730 nm, 1-nm FWHM, pointwise uncertainties and exact
endpoint integration. Edition facts are now read from the validated packaged
metadata record and mirrored in the existing public identity/constants; their
values and external byte admission are unchanged. The source access date remains
historical and redistribution remains not established. Only the declaration is
packaged, not the spectrum. Radiometry consumes accepted geometry without
re-evaluating physical states. No interpolation, extrapolation or normalization to the
bolometric nominal constant; integrated physical uncertainty remains not evaluated.

Numerical Moonlight, reflected-light fields, spacecraft surface/BRDF response,
observer brightness and detector contamination remain incomplete. The accepted
LIME v1.4.2 offline inspection is evidence, not admission of a runtime lunar
model. The independent DE440/SPICE Phase-B comparison still has unresolved
case states, signed phase, frame/load-order and EOP/uncertainty gates. No new
acquisition, LIME execution or numerical Moonlight follows from this cleanup.
Consumed one-run external execution authorities remain consumed.

## Where detailed records live

| Detail | Record |
|---|---|
| Scene dependencies and layer context | [49D history](archive/milestone_history/49d_scene/) |
| Ephemeris and astrometric/apparent contracts | [49E history](archive/milestone_history/49e_ephemeris/) |
| Natural bodies and appearance | [49I history](archive/milestone_history/49i_solar_system/) |
| Minor-body resources and comet photometry | [50A history](archive/milestone_history/50a_minor_bodies/) |
| Satellite audits, protocols and program log | [Pre-kernel document archive](archive/pre_kernel_20261017/INDEX.md) |
| Satellite scientific teaching | [Current satellite guide](satellite_guide.md) |

Before changing a domain, consult its exact accepted scientific contract and
actual implementation. Historical next-step instructions are not current
authorization. The single forward priority is the kernel roadmap.

## Shared ICRS epoch defaults

K3.09 removes the shared automatic J2000.0 measurement stamp. ICRS axes have no
equinox and imply no observation or catalogue measurement epoch. A missing epoch
remains None; an explicitly qualified source epoch remains unchanged. This is a
metadata correction, not a coordinate transformation or propagation. Defining
FK4/FK5/ecliptic equinoxes retain their existing role and values. Nonstellar
physical admission still requires its declared model's source facts; removal of
a shared default cannot turn an unverified source into a qualified provider.

## Catalogue lookup and physical admission

Approved by Fernando on 2026-10-19: baseline catalogue lookup and physical
motion/parallax admission have distinct requirements. Lookup preserves recorded
positions, identity, units, edition, provenance and source-byte binding. Missing
epoch/frame/origin facts remain explicit and unverified chart interpretation
remains labelled; lookup cannot fabricate physical qualification. Requiring an
unknown physical measurement epoch must not block a preserved catalogue lookup.
Strict physical admission retains the selected model's qualified input requirements.
PN nebular centres, SNR radio centroids and associated compact/central stars remain
distinct. Baseline acceptance with explicit compatibility limits does not recover
missing facts, certify arbitrary-date accuracy or automatically close K5.

## Galaxy routing under catalogue-lookup admission

K3.10 retains the accepted static galaxy chart model. Source-bound lookup
validation does not qualify absent physical frame/origin facts; legacy records
and output remain labelled accordingly. A declared date with no admitted scale
remains source text, with SDK source_epoch None, rather than blocking a static
lookup or inventing a time scale. A genuinely qualified source epoch remains
unchanged. Kernel-returned centres control public/native/label/observed geometry
and warm-cache identity. Shape dimensions/PA, observer frame transformations and
numerical precision/uncertainty claims are unchanged. No galaxy motion is added.

## Generic nonstellar lookup and named target centres

K3.12 is lookup migration only. Messier/Caldwell membership and aliases remain
independent source declarations; one catalogue's coordinate is not substituted
from another object family. Source-bound metadata and explicit missing physical
facts survive cold/restored routes. Generic catalogue points and named target
centres consume returned kernel directions before the retained observation chain;
refusal propagates even after observed caches are warm. A copied target record
is not proof of an original source frame, epoch, origin or measurement error.
Explicit user coordinates remain constructed references. No motion, expansion,
parallax algorithm or physical time-validity guarantee is added.

## Globular-cluster baseline lookup

K3.13 changes centre routing only. Catalogue lookup preserves original Harris
source facts and 
