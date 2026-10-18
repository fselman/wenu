# Current scientific contracts and paused work

**Baseline:** `6708f54a` (2026-10-17). These invariants survive documentation
cleanup and the future kernel migration. Archived audits retain detailed
proofs and source receipts; moving them does not revoke a compatibility promise.

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
coordinate-encoding/metadata correction, not motion propagation. Observed
Skyfield realization and native constellation-label anchors remain unmigrated.
No historical-epoch or Gaia accuracy claim follows from this adapter.

## Catalogue identity and curation

Nonstellar angular encodings use declared source units when available; the
normalizer converts them to its canonical degrees/arcminutes before geometry.
Incompatible declared units fail before replacing a loaded catalogue. Original
table metadata and unconsumed fields remain available, with independent metadata
copies on geometry. Unitless compatibility inputs are not evidence of source
units, frame or epoch. These preserved facts do not yet constitute full
complete scientific admission. `NonStellarCatalogueMetadata` validates and mirrors
declared facts and input-byte identity, reporting absent facts explicitly. Strict
admission refuses missing frame/origin/epoch/time scale/edition/provenance/units;
legacy chart interpretation is explicitly `legacy-unverified-catalogue-encoding`.
An unknown measurement epoch is never replaced by an equinox or release date.
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

Sampled SatChecker candidates are not exact local connected visits. A
conservative selector cannot discard an exact crossing; fallbacks and
completeness claims must retain their accepted bounded domains. A zero-crossing
field is a valid result, not evidence for untested positive cases or capacity.

Exact reports retain canonical JSON identity, strict decoding, ECSV/VOTable
losslessness, explicit nullable Unicode handling, atomic no-clobber file
publication and the distinction between geometric crossing and visibility.
Tracks consume accepted solved evidence through the existing chart pipeline.
The planning advisory does not write to observatory systems.

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
