# Current scientific contracts and paused work

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
identities are preserved. Other production source adapters remain unimplemented.

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
guarantee. No reduced-input propagation algorithm is implemented by this policy
update. Unknown motions/RV are never recorded as measured zero.
Reduced models require explicit approximation/error semantics and their own
acceptance. Expansion, internal dynamics and morphology evolution are excluded.
Stars, clusters, PNs and SNRs retain object-specific source/centre qualification;
in particular expansion velocity or displaced compact-object motion cannot be
silently used as systemic centre motion. Observer realization remains separate.

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

The external TSIS-1 HSRS v2 product retains its exact digest, 25,281 native
0.1-nm samples over 202–2730 nm, 1-nm FWHM, pointwise uncertainties and exact
endpoint integration. No interpolation, extrapolation or normalization to the
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
source facts and missing physical declarations without substituting another
catalogue's position. Half-light radius remains a structural measurement; the
existing plotted diameter is twice that radius, not a motion or physical extent
evolution model. Known/unknown source epochs retain shared lookup semantics.
Native and observed shapes/labels consume returned centres; warm caches cannot
hide refusal or changed state. No proper motion, parallax, internal dynamics,
expansion or arbitrary-date physical validity claim is added.

## Planetary-nebula baseline lookup

K3.14 changes PN nebular-centre routing only. True/probable object inclusion,
curated membership/selection criteria and angular-size filters remain unchanged.
Catalogue flux/diameter fields are retained metadata; symbols keep their existing
fixed display scaling. A nebular centre is not silently replaced by an associated
central star. Returned kernel centres govern native symbols and observed inputs
and cache identity; failed admission/evaluation propagates after cache fill.
Missing physical frame/origin/epoch facts remain explicit. No proper motion,
parallax model, expansion or arbitrary-date accuracy claim is introduced; AX.15
remains separate pending work.

## Supernova-remnant baseline lookup

K3.15 changes Green radio-centre routing only. Original source coordinates,
major/minor radio diameters, morphology and radio flux remain preserved facts.
Unknown position angles retain the existing equal-area circle policy, not an
invented celestial orientation. Radio flux is not an optical visibility measure.
Signed Galactic designations remain distinct identities. Returned kernel centres
control native/observed geometry and warm-cache identity; source-admission/state
refusal propagates without falling back to raw coordinates. Unknown physical
frame/origin/epoch facts remain explicit. No associated compact-object position
or motion replaces the catalogue radio centre. Proper motion/parallax remains
AX.16; expansion and morphology evolution remain excluded.


## Existing observer resource and warm-cache boundary

Legacy observed geometry now checks the actual active EOP/leap/backend inputs
before shared cache reuse. `Observer` geometry admission binds loaded ephemeris
bytes and refuses a closed or changed admitted file descriptor. This is cache
correctness and resource lifetime, not new physical-source qualification or an
absolute-accuracy certificate. The legacy Astropy/Skyfield resource-selection and
observation policies are preserved; strict offline reception remains distinct.
Request-owned resources close on success/failure; borrowed resources retain caller
ownership. No observer resource is serialized as a native catalogue state.

## Ephemeris model identity and geometric state transport

A DE-like filename is not evidence of a physical ephemeris model. Resolved SPK
identity retains exact SHA-256 and segment coverage; absent model qualification
is explicit. Caller-declared model text is provenance, not independent validation.
K3.25 default planet/Moon point states pass through the existing Cartesian SDK
before the retained light-time/apparent chain. Measurement, physical-model and
numerical error channels remain not evaluated; unit conversion supplies no bound.
Targets such as Mars barycentre are preserved and are not replaced by the physical
planet ID. No new apparent correction, distance, motion or disk science is admitted.

## Resolved-body migration invariants

K3.26 changes default state transport and request-component reuse, preserving the
existing single/observed and frozen-Earth scientific models. The observed service
remains the single light-time authority; no light-time/apparent correction is
introduced into the frozen geometric construction. Radius/model, physical angular
diameter, phase and bright-limb angle remain independent of display magnification.
Unknown ephemeris-model qualification and error channels remain unknown. A shared
component result is an admission within one request context, revalidated against
live observer resources; a different context requires fresh admission. Numerical
parity against the retained raw route is not a new physical accuracy guarantee.

## Natural-body track migration invariants

Natural-body track sampling retains the existing geometric/light-time/apparent
chain, body versus barycentre targets, individual observer states and exact major
time anchors. State unit transport adds no correction, model or uncertainty bound.
The fixed chart frame is distinct from moving physical sample times; temporal
component visibility cannot change the samples. Shared component results are
request-scoped admissions checked against current observer resources. Existing
chart capability refusals, including natural-satellite tracks, remain unchanged;
scientific-API Moon parity does not admit a new chart product.

## Asteroid resource-chain invariants

Asteroid Cartesian admission retains the primary small-body SPK and every
planetary dependency, including byte digests and coverage on TDB. Their coverage
intersection is necessary; it does not fill segment gaps or invent a validity
domain. Existing backend segment/frame/centre checks still apply. Kernel-returned
PV must reach point and track consumers while preserving orbit solution,
selected segment, provider IDs and resource lineage. Unknown physical/model
errors remain unknown; transport parity is not an absolute accuracy claim.

Ceres's complete accepted solution facts move unchanged to the versioned source
manifest. Its osculating epoch is a source fact, distinct from each evaluation
or reception instant. Installed SPK bytes remain checked against their own
acquisition receipt. No new source acquisition, orbit propagation, physical
qualification follows from this state-transport refactor.

## Comet routing invariants

The comet adapter retains the selected orbit solution and its non-gravitational
model/quality parameters; it does not reimplement the model from A1/A2. Returned
Cartesian PV feeds the existing one-way-light-time and apparent services before
point/track consumers. Exact per-sample times and fixed product axes are retained.
An existing provider PsAng sample remains source-owned data with its original
request/observer context. Missing samples preserve the established fallback;
refusal is never converted into a fabricated angle or a raw-state fallback.

Discovery/photometry/reporting retain validated provider identities and their
sampled model magnitudes, missing values, UTC epochs, observer coordinates,
solution/resource provenance and stated uncertainty limits. They do not generate
position queries for scalar model quantities. Existing explicit acquisition,
workload and cache policies are unchanged and stay outside deterministic drawing.
No new comet propagation, physical accuracy, selection or visibility capability
is admitted. K3.30 reference routing and full K3/K5 closure remain separate.

## Antisolar construction provenance

An antisolar reference is derived geometry, never an independent physical body.
Comet provider PsAng retains priority; absent angles use the same apparent
Sun-comet separation, conjunction/opposition exclusion, position angle and tangent
offset. Known Skyfield Sun states pass through the existing Cartesian adapter,
with one original light-time owner and unchanged apparent corrections. Resource
identity is provenance, not independent qualification of an SPK model.
Sampled symbols retain their actual sample observation rather than claiming the
fixed chart-axis instant as their evaluation time. Suppression means no available
tangent, not a fabricated direction. No morphological tail evolution is implied.

Explicit `CelestialPoints` antisolar points retain the legacy Astropy `get_sun`
geocentric GCRS unit-direction conversion and ICRS antipode at construction time.
Their receipt preserves that source convention and the construction site/time;
it does not qualify the legacy unit-direction conversion as a new finite-distance
or topocentric physical Sun model. Display at another time retains the original
construction anchor. No antisolar object-state query or new motion is introduced.
