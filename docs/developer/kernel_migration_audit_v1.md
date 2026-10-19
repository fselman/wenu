# Kernel migration: as-is functionality and test audit

## Catalogue metadata audit, 2026-10-18

Inspected source: PR #248 head `90d51334`, based on accepted main `bf804cbb`;
the ingestion correction in this PR follows that inspection. Static searches
cover production Python and the separate kernel for epoch, equinox, frame,
origin/centre, unit, catalogue edition, provenance, manifest and resource
identity literals. The findings below trace the significant candidates into
loaders, normalized tables, source ECSV/ReadMe/provenance documents, snapshots
and public geometry. This is a metadata audit, not numerical revalidation of
unmodified providers or proof that every literal is wrong.

**Result:** catalogue-specific knowledge is duplicated beyond the stellar
position bug. Wenu cannot yet claim that every scientific consumer obtains its
metadata from a source record. The stellar path is corrected here; the remaining
findings are explicit migration work, ordered before the affected provider can
be considered modular or frozen. Never replace an unknown epoch by J2000.
The open-cluster followup now consumes the already-preserved `position_epoch`
and `RA_source` fields and carries source metadata into geometry. At inspected
base `c0dee24c`, the active 513-row table declares 509 J2016.0 Hunt positions and
four unknown Dias epochs. Selection retains row lineage/masks; only uniformly
known selections expose a scalar epoch. Snapshot v4 validates that header, while
v2/v3 compatibility recomputes geometry from preserved rows rather than trusting
the historical J2000 stamp. K3.09 now removes the remaining shared implicit
measurement-epoch defaults; other nonstellar source qualification remains open.

| ID / priority | Owner and evidence | Consequence and required action | Verification owner |
|---|---|---|---|
| M1 / fixed | `objects/stars.py` and `stellar_state.py` repeated epoch, source edition and provenance, despite `epoch_year` and the packaged Hipparcos ReadMe | Ingest through `stellar_catalogue.py`; metadata document binds exact source bytes, preserves original fields and mirrors a validated immutable record. Native geometry and kernel queries obtain their epoch/edition/provenance from it. Missing or conflicting metadata is refused. | `test_stellar_state.py`, stellar/public-position owners |
| M2 / fixed | `sky/constellation_lines.py` and `sky/constellation_labels.py` supplied their own Hipparcos epoch/provider descriptions | Native endpoints inherit returned position specifications; label metadata comes from the stellar interface. Native and observed label inputs now use the public stellar state interface through accepted K3.07/K3.08. | Native constellation geometry and frozen label/gap consumers |
| M3 / fixed | `sky/native_snapshot.py` embedded J1991.25 both in writing and admission and did not persist the source metadata envelope | New schema v3 persists metadata, verifies it against source identity/row epochs and restores the same runtime record. v1/v2 compatibility uses an explicit source-bound packaged profile; unidentified legacy sources are refused. Nonstellar snapshot assumptions remain M6. | Snapshot admission/corruption, v1/v2 compatibility, source-free process and serial/spawn consumers |
| M4 / accepted PR #273 | `icrs_catalogue_spec` now defaults to `epoch=None`; `ICRS_ASTROMETRIC_SPEC` no longer assigns J2000.0. Explicit admitted stellar and cluster epochs remain unchanged | ICRS axes alone establish no measurement epoch. Shared raw point/curve observation helpers, celestial north, constructed points, native grids and transformed B1875 boundary outputs inherit unknown epoch. Stellar/open-cluster source owners still supply their own epochs; diffuse geometry already supplies None. No numerical frame transform or source bytes change. | `catalogue-coordinate-defaults`: vocabulary/transform/point/grid/boundary/regional callers plus nonstellar and snapshot admission |
| M5 / mechanism implemented; source gaps open | `objects/nonstellar.py` preserves source fields/metadata/units and mirrors declared coordinate facts in a frozen `NonStellarCatalogueMetadata` record bound to input bytes. Native and observed specifications consume it; source provider identity replaces copied labels. Conflicting declarations and strict incomplete admission fail before publication | Missing facts remain null and discoverable in `missing_fields`; `require_complete()` and strict load refuse them. Legacy charts retain the explicit `legacy-unverified-catalogue-encoding` model. Actual source frame/origin and model-required epoch/scale gaps must be resolved before physical provider closure. Galaxy static directions do not require a measurement epoch. Their centre consumers now use the kernel with an explicitly unknown origin when missing; shape axes/PA remain above it. Compatibility is not evidence of accuracy. | `nonstellar-admission`: owner regressions, real family geometry, cold/saved/source-free and public CLI consumers |
| M6 / header defaults fixed; legacy interpretation explicit | Snapshot v5 derives fixed headers from each provider, stores nonstellar records, checks source identity/table metadata/units/header agreement and retains the separate open-cluster row contract | Readers admit v1-v4 historical formats without treating their J2000 headers as measurement epochs. Missing legacy units/digests are not reconstructed as facts. Resource gaps from M5 remain open; the shared coordinate helper correction is verified separately under M4. | Existing corruption owner plus nonstellar record/header conflicts, actual known/unknown epoch round trips and legacy admission |
| M7 / medium, open | `sky/ceres.py::CERES_SOLUTION` embeds Horizons solution number/date, osculating epoch and quality fields; `minor_body_resources.py` treats this descriptor as the expected identity, while newer comet identities are manifest-derived | A Ceres resource update requires a code edit and can diverge from its acquisition evidence. Migrate the complete solution identity to a versioned data manifest; preserve the existing descriptor-to-manifest/SPK digest and frame checks. | Minor-body resources/ephemeris and Ceres public state/track owners |
| M8 / medium, open | `satellites/radiometry.py` embeds TSIS product DOI/URL, byte digest/count, grid bounds/sampling, header and audit integral | These are edition-specific resource facts and belong to a validated resource metadata document. Current code deliberately admits one exact resource and verifies it; this is inflexibility/duplication, not evidence of corrupted radiometry. Preserve the numerical integral and malformed-resource oracles when extracting it. | Satellite radiometry resource/parser owner |
| M9 / source assessment complete; contract decision open | `sky/milky_way.py` and `sky/magellanic_clouds.py` provide fixed source descriptions/ICRS semantics while loaders retain chiefly source paths and feature levels | Preserve dataset edition, source coordinate semantics and provenance in their own metadata envelope. `epoch=None` may be appropriate for diffuse morphology; do not turn it into a fictitious stellar epoch. | Isophote loading/native geometry and saved-ring consumers |
| M10 / low, open | `skyfield_ephemeris.py::_model_from_filename` identifies a DE model from its filename unless explicitly supplied | Prefer the acquisition/validated resource identity. Renaming is not evidence that kernel contents changed; explicit-model admission is already supported. Coverage and digest are read from the resource. | `test_skyfield_ephemeris.py` resource identity owner |

Examples already following the intended boundary include satellite OMM records
(`satellites/elements.py` reads epoch, frame, centre and time system and validates
its supported contract), SPK segment centre/frame/coverage checks, manifest-bound
comet resources and hashed observer-location records. Preserve these checks.

### Nonstellar source declaration audit

Rechecked the packaged admission records at main `d7ad9923` on 2026-10-19,
including both Messier and Caldwell. The following describes the embedded metadata of the actual active tables,
not reconstructed measurement facts. Source bytes and all original declarations
are retained; no catalogue files are changed. Strict admission still refuses
these gaps. K3.09 remains partial: removing shared defaults does not establish
missing physical source facts or close M5. The primary-source assessment below
remains the existing 2026-10-18 evidence, not a claim of a new external review.

| Catalogue | Declared frame | Measurement epoch/scale | Edition/provenance | Remaining admission work |
|---|---|---|---|---|
| Messier/HEASARC | Absent | Absent | Sky Catalog reference and HEASARC URLs retained | Frame/origin and epoch/scale |
| Caldwell/OpenNGC | ICRS/J2000 | Absent | Release, membership URL, source-file URLs/digests retained | Origin and epoch/scale |
| Galaxies/OpenNGC | Absent | Absent; optional for the explicit static model | Release/license/source-file URLs/digests retained | Frame/origin; epoch/scale do not block static admission |
| Harris globular clusters | Absent | Absent | December 2010 edition reference and HEASARC/McMaster URLs retained | Frame/origin and epoch/scale |
| Strasbourg-ESO PN selection | ICRS/J2000 as served by TAP | Absent | 1992 edition, HEASARC and comparison/selection provenance retained | Origin and epoch/scale |
| Green remnants | ICRS/J2000 | Absent | 2024 October edition and CDS/original-source URLs retained | Origin and epoch/scale |

Primary documentation checked 2026-10-18:
[HEASARC Messier](https://heasarc.gsfc.nasa.gov/w3browse/all/messier.html)
describes RA/Dec in the requested equinox, and
[HEASARC Harris](https://heasarc.gsfc.nasa.gov/w3browse/all/globclust.html)
explicitly describes an input equinox of 2000. Neither statement establishes a
common measurement epoch/time scale for these rows or a precision ICRS origin
solution. The initially unavailable release-pinned OpenNGC documentation was
subsequently retrieved through GitHub at `v20260501`:
[README](https://github.com/mattiaverga/OpenNGC/blob/v20260501/README.md)
(blob `11b2668f5aacd1224e932094024612435528d879`) says coordinates usually come
from NED, and [field guide](https://github.com/mattiaverga/OpenNGC/blob/v20260501/NGC_guide.txt)
(blob `7e5e1447c3cccd54cd5cbebb29387e5b30b05cc1`) labels RA/Dec as J2000 epoch.
Those statements do not establish a new precision frame/origin solution for
each source row. No catalogue bytes or coordinate frame declarations are changed.
The user-selected galaxy chart model is explicitly static; measurement
epoch/scale are provenance rather than admission prerequisites for that model.
Other required source facts remain open and are refused in strict mode. Legacy chart
compatibility is an explicitly labelled interpretation, not a metadata repair.

<a id="m5-source-assessment-and-proposed-admission-distinction-2026-10-19"></a>

### M5 source assessment and agreed admission distinction, 2026-10-19

**Assessment base:** accepted main `2df8954b15ebbe36cddaf977355efdd53a65f2a8`.
The shared-default correction is accepted through PR #273: 248 focused Mac,
36 documentation and eight tooling cases passed. This assessment changes no
catalogue bytes, runtime admission rule, SDK contract or numerical calculation.

Primary evidence rechecked for the actual packaged editions:

| Source | Supported declaration | Limit of this evidence |
|---|---|---|
| [HEASARC Messier](https://heasarc.gsfc.nasa.gov/w3browse/all/messier.html), RA/Dec definitions | Coordinates are expressed in the requested equinox | No common measurement date/scale is established by that wording; an equinox is not a motion-reference epoch |
| [HEASARC Harris](https://heasarc.gsfc.nasa.gov/w3browse/all/globclust.html), RA/Dec definitions | Original cluster-centre coordinates use equinox 2000 | This is not an explicit common measurement epoch or a new precision ICRS frame solution |
| [OpenNGC v20260501 guide](https://github.com/mattiaverga/OpenNGC/blob/v20260501/NGC_guide.txt) and [README](https://github.com/mattiaverga/OpenNGC/blob/v20260501/README.md) | Guide labels RA/Dec with J2000 epoch terminology; README identifies heterogeneous inputs, usually NED for coordinates, with per-object source information | Retain the source's terminology. These documents do not establish one common observation date/time scale or independently qualify every row's frame/origin. Pinned blobs remain `7e5e1447c3cccd54cd5cbebb29387e5b30b05cc1` and `11b2668f5aacd1224e932094024612435528d879` |
| [HEASARC Strasbourg-ESO PN](https://heasarc.gsfc.nasa.gov/W3Browse/nebula-catalog/plnebulae.html), RA/Dec and Ref_Position definitions | Certain/probable PN originally have 1950 equatorial coordinates, while possible PN originally have 2000 coordinates; the service presents a requested equinox and retains positional references | Wenu selects certain/probable PN. Its preserved header saying ICRS/J2000 as served by TAP is acquisition metadata, not proof supplied by this overview of a precision ICRS conversion. Do not silently switch to B1950 or assert the existing numbers are wrong; conversion provenance requires separate evidence |
| [Green 2024 October documentation](https://www.mrao.cam.ac.uk/surveys/snrs/snrs.info.html) and [CDS VII/297 ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/VII/297?format=html&tex=true) | J2000 equatorial positions identify source centroids, generally from radio maps, with resolution depending on remnant size | These are not automatically central-star/neutron-star coordinates or a centre-of-mass motion solution. A radio-centroid position cannot acquire a compact object's proper motion merely by cross-identification |

The [HEASARC coordinate-converter help](https://heasarc.gsfc.nasa.gov/Tools/convcoord_help.html)
uses FK5 for its J2000 option. That is evidence about that tool only; it does not
establish the original TAP response's frame or justify rewriting Wenu's source
records. No new TAP query, catalogue acquisition or coordinate conversion was
performed. Initially failing raw GitHub/CDS URLs were recovered through the
GitHub connector and the CDS HTML ReadMe; unavailable links were not treated as
evidence. Existing packaged frame declarations remain preserved and unpromoted.

**As-is admission:** `NonStellarCatalogueMetadata.missing_fields_for` requires
frame and origin for both models, and additionally epoch/scale for its default
source-epoch model. Galaxies already use a separate static-direction chart
model, while the SDK/shared catalogue adapter already support catalogue lookup.
Thus some remaining refusals concern the requirements of the selected model,
not information that another documentation search can manufacture.

**Agreed by Fernando on 2026-10-19:** distinguish baseline catalogue lookup
from physical model admission, incorporating his proper-motion-only clarification
and explicit instruction to incorporate the policy and proceed. Policy agreement
is recorded before implementing the bounded K3.09 admission distinction.

1. A catalogue lookup returns preserved positions through existing kernel
   interfaces, retaining IDs, units, edition, byte binding, original reference
   labels and known metadata. Missing measurement epochs remain unknown.
   Incomplete reference evidence remains explicitly labelled compatibility
   interpretation, never strict physical qualification or a fabricated origin.
2. Each physical capability retains its own required inputs. Known position,
   reference epoch and both PM components suffice to admit angular propagation
   without distance or RV; no universal PM-only time cutoff is imposed. Distance
   is required for distance-dependent observer parallax. Full space motion has
   separate requirements and perspective treatment. Uncertainties, approximation
   limits and requested angular accuracy control suitability. No missing
   input becomes zero, no new lookback interval is certified, and no expansion
   or central-star/nebular-centroid substitution is introduced.
3. Baseline routing can be accepted with those explicit limitations while the
   unresolved physical qualification stays separately visible. This would not
   claim that source facts have been recovered or automatically close K5, the
   positional extension, or any other family's routing milestone.

Fernando selected the lookup/physical-admission distinction rather than blocking
baseline routing until every source has a full physical solution. Original source
metadata and incomplete qualification remain visible. No catalogue replacement,
coordinate conversion or new physical model is authorized by this admission slice.

Selected K3.09 implementation: extend the existing nonstellar admission owner with
an explicit catalogue-lookup policy and public validation method. Require source
identity, edition/provenance and angular units; retain strict physical admission
unchanged. Lookup coordinate meaning must disclose unresolved reference facts,
not promote missing facts to verified ICRS/barycentric states. No other family's
kernel routing or reduced-input propagation is activated here. Gate: extend the
existing catalogue-coordinate-defaults selection with lookup/strict separation,
missing required lookup inputs, disclosure and source immutability coverage.
The accepted native/observed and snapshot seams remain selected. SDK, source
bytes, dependencies/build, snapshot schema and renderer remain unchanged.

Existing well-governed satellite/SPK/comet resource admission remains unchanged.

Not every literal is catalogue metadata. ICRS/TEME support restrictions, NAIF
frame identifiers, serialization version identifiers, mathematical unit
conversions, IAU-defined nominal constants and an explicitly selected model or
grid equinox are contracts or definitions. They remain in their owning code or
configuration. Catalogue edition facts, measurement epochs, acquisition dates,
resource digests and source-specific units must come from data records. This
distinction prevents replacing useful scientific constraints with arbitrary
metadata acceptance.

The source map and machine inventory include the new ingestion owner and shared
synthetic metadata fixture. The expanded focused gate adds ingestion, schema
and installation checks because those boundaries changed. The separate
`open-cluster-metadata` gate verifies the bounded M4/M6 cluster correction;
other unmodified provider physics is audited statically here, not claimed newly
tested or repaired.

## Open-cluster motion and lookup audit, 2026-10-18

Inspected accepted main `5f8fca4c4a391ea54aba05401163bb1c245ce7ff`.
Resource blob identities were checked against that GitHub tree. Counts below
describe these exact Wenu derivatives, not completeness of the published catalogues.

| Resource | Rows | Proper-motion pairs retained | Position lineage |
|---|---:|---:|---|
| Dias HEASARC ECSV | 1,931 | 1,872 finite pairs, declared mas/yr | Measurement epoch not declared; J2000 frame/equinox text is not a measurement date |
| Hunt/Reffert full Wenu derivative | 7,167 | No motion columns | ICRS, source label J2016.0; no explicit numerical epoch scale in this metadata |
| Hunt/Reffert V5 derivative | 431 | No motion columns | Same source metadata as full derivative |
| Active curated v0.2 | 513 | 331 finite Dias pairs (332 unmasked, one nonfinite) | 509 Hunt centres/J2016.0; four Dias centres/unknown epoch |

All four Dias-centred rows have finite Dias motions. The other 327 finite Dias
pairs accompany Hunt-selected centres; a cross-catalogue combination needs an
explicit reviewed astrometric policy, not column presence alone. Current
`OpenClusters.position(instant)` ignores the instant; neither native nor observed
cluster geometry applies these retained motions. Observer/date transformation is
separate and does not replace physical source motion.

Primary-source verification (2026-10-18):
[CDS Hunt/Reffert ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/A+A/686/A42?format=html&tex=true)
defines cluster `pmRA` as mean motion multiplied by cos(dec), `pmDE`, their
standard errors and dispersions, parallax/error and radial-velocity fields.
The published catalogue therefore has astrometry omitted by Wenu's derivative.
[HEASARC OPENCLUST documentation](https://heasarc.gsfc.nasa.gov/w3browse/all/openclust.html)
defines mean RA/Dec motions in mas/yr, motion errors and references, and radial
velocity/error fields. Its displayed RA description alone does not settle the
cos(dec) convention; check the original CDS source before propagation. A mean
motion dispersion must not silently substitute for uncertainty of the mean.

Before propagation, ingest a source-bound standard astrometric record retaining
the selected centre's source/epoch/scale/frame/origin, motion convention/units,
available uncertainties and correlations, distance/parallax, radial velocity and
their source identities. Preserve masks and raw columns; absent motion is
unknown, never zero. Prefer the matching Hunt solution for a Hunt centre after
source verification, with an explicitly declared alternative for Dias-only rows.
No acquisition, automatic cross-source merge or resource-byte change occurs in
this prerequisite. Re-ingestion must retain the existing 513-object membership
unless a separate selection change is requested.

The ingestion prerequisite now recovers the published aggregate astrometry in a
versioned companion bound to the accepted 513-row catalogue bytes. All 509 Hunt
IDs/names/centres match exactly; 502 have radial velocities. The four Dias-only
rows have masked Hunt fields and an explicit unresolved-adoption policy. Existing
Dias columns, member photometry, masks, selection and active resource are unchanged.
The reader consumes the captured CDS ReadMe through Astropy; source byte offsets,
units and descriptions are not reimplemented for this recovery. All retained
fields and reviewed meanings enter the source-bound metadata envelope. Explicit
offline attachment is checked through the existing immutable cluster record.

ReadMe and aggregate gzip checksums exactly match the earlier photometric
acquisition. The aggregate was retrieved once on 2026-10-19; no member table or
per-cluster network queries were needed. Scientific-use policy/attribution and
article CC BY 4.0 statements are recorded with primary-source URLs; no blanket
CC0 or OpenNGC relicensing claim is made. Tests contain exact captured records
and the original ReadMe, not reconstructed fixed-width provider fixtures.
The preserved v1 time-scale/origin gaps require explicit qualification/adoption;
unavailable cluster-mean covariances remain unknown. Mean cluster motions do not
redefine the densest-point centre. Numerical
propagation and default adoption require a separate reviewed model.

The accepted SDK dev8 introduces `catalogue_lookup`: it admits incomplete
per-object source epochs without invoking the galaxy static model and refuses
physical epoch accuracy, velocity and temporal reuse. The cluster adapter now
binds preserved metadata/fields/units/masks and original/derived digests to its
resource identity. Native/public/observed/saved centres use returned kernel
vectors without fallback; production pins accepted main `9dd1909f`. This is
source lookup, not source-metadata closure or motion propagation. Only a later
explicit propagation model may claim positions at a new epoch.
For ancient charts, bulk cluster motion and changes to member distribution are
different questions; translating a present-day symbol does not reconstruct the
historical membership or morphology.

## Cluster propagation qualification and model contract

**Inspected base:** `fed1305e76455f952cca4c2a49afd14205ce30b7`.
**Source review:** 2026-10-19 UTC. The
[source-bound qualification record](data/cluster_astrometry_qualification_v1.json)
separates direct declarations, inherited conventions, unresolved lineage and
proposed model policies. It binds the accepted selected catalogue, original Dias
snapshot and Hunt companion/specification by SHA-256. It preserves four exact
record pairs from the original B/ocl and Dias 2014 tables, together with full-file
hashes, sizes, URLs and source row indices. No catalogue bytes are changed.

### Source qualification

Hunt & Reffert [Paper II, sections 2.1 and 3.3](https://arxiv.org/html/2303.13424v2)
uses Gaia DR3 astrometry, derives density-mode centres and calculates core-member
mean motions. [Paper III](https://arxiv.org/html/2403.05143v2) updates this catalogue.
ESA's [reference-system definition](https://gea.esac.esa.int/archive/documentation/GDR3/Data_processing/chap_cu3ast/sec_cu3ast_intro/ssec_cu3ast_intro_refsystems.html)
and [DR3 data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html)
define barycentric ICRS directions, TCB and Julian-year epochs. Together with the
captured cluster ReadMe's epoch 2016.0, this supports **source-derived inheritance
of J2016.0(TCB) and solar-system-barycentric direction conventions** for the Hunt
aggregate. It is an inference from this specific documented chain, not an explicit
new statement in the cluster ReadMe or a general rule inferred from a name.
The old v1 null declarations remain preserved; adopting this qualification in a
runtime solution requires a separate versioned ingestion/admission step.

All four Dias-only entries (NGC 2239, NGC 2252, NGC 6514 and NGC 6885) identify
D14 as their proper-motion reference in the original
[B/ocl table and reference list](https://cdsarc.cds.unistra.fr/ftp/cats/B/ocl/).
Their two mean motions exactly match the
[Dias et al. (2014) table](https://cdsarc.cds.unistra.fr/ftp/J/A+A/564/A79/).
Its ReadMe explicitly defines cluster RA motion as mu_alpha times cos(delta),
ICRS. That convention is now resolved for these four motions. D14 labels its
coordinates at J2000.0; they agree with the retained centres within tabular
rounding, but the [HEASARC position description](https://heasarc.gsfc.nasa.gov/w3browse/all/openclust.html)
establishes only J2000 equinox. The retained centre's epoch lineage and time scale
are not yet proven, so those four numerical source epochs stay unknown.

Do not import uncertainty semantics along with a matching mean value. The
B/ocl and D14 error fields differ substantially for all four rows; both original
values are preserved in the audit record. No conversion or interpretation is
adopted without its original methodological evidence. D14's cluster-star
correlation is not a full covariance matrix for the cluster mean. Hunt likewise
has no published full cluster-mean astrometric covariance. A density maximum is
not a material point whose trajectory has been measured independently.

### Proposed propagation boundary

The first nominal numerical subset is now implemented through the explicit
[cluster provider API](implementation_reference.md#nominal-cluster-motion-provider).
The implemented cluster provider now also verifies numerical direction bounds
and certifies reuse against exact arithmetic on its admitted binary64 SI model.
Measurement, input-conversion and physical-model uncertainty remain separate and
uncertified. Interactive selective reuse and reproducible full-model fallback use
the unchanged SDK; chart/snapshot adoption remains open. See the
[proof and API](implementation_reference.md#cluster-direction-reuse-bound).
Keep `catalogue_lookup` as the default until explicit adoption and compatibility
acceptance. Register a distinct versioned cluster-centre motion model; never
silently change the meaning of a saved lookup state.

The explicit nominal model uses a coherent rectilinear barycentric astrometric
solution, following ESA's [standard-motion definition](https://gea.esac.esa.int/archive/documentation/GDR3/Data_processing/chap_cu3ast/sec_cu3ast_intro/ssec_cu3ast_intro_motion.html).
Given the source direction u, local east/north bases p and q, distance d and
mu_alpha_star/mu_delta, the model construction is

\[
 b_0=d u,\qquad v=d(\mu_{\alpha *}p+\mu_\delta q)+v_r u,
 \qquad u(t)=\frac{b_0+(t-t_0)v}{\lVert b_0+(t-t_0)v\rVert}.
\]

Angles, distance, velocity and elapsed time must first use coherent units and
TCB conventions. This describes an astrometric chart-centre approximation;
its time argument is light arrival at the barycentre, not a reconstructed
simultaneous emission event. A spectroscopic RV used as an astrometric proxy
must be declared as model policy. Use a reviewed existing numerical service
and independent oracle rather than implementing a second chart pipeline.

Distance selection is explicit: a chosen source distance estimator and its
percentiles must not silently become inverse mean parallax or Gaussian errors.
The 502 available RVs are candidate inputs, not 502 certified trajectories.
The full model must refuse missing RV. An angular-only approximation, if offered,
is a separately named opt-in model with omitted perspective effects reported;
unknown RV must not be published as a measured zero. Four Dias-only entries
remain unavailable for physical propagation until their missing facts are
qualified. A mixed request must report unavailable objects explicitly, without
silent omission or a raw-coordinate fallback labelled as propagated.

Transporting today's density maximum with a mean core motion is an explicit
modelling assumption. It does not reconstruct membership, tidal tails, internal
motions, angular size or morphology in antiquity. Keep shape/display parameters
above the state provider. Galactic acceleration and centre-model uncertainty
need an evaluated budget before any ancient-date absolute-accuracy claim;
do not invent a universal range of thousands of years.

### Uncertainty, validity and reuse

Keep three separate questions: measurement/model accuracy relative to the real
sky, numerical accuracy relative to the chosen model, and the error from reusing
an older computed state. Missing initial-centre errors, covariances or systematic
bounds remain unknown. A small proper-motion standard error or source dispersion
alone cannot supply the missing total uncertainty or a hard confidence bound.
An absolute angular-accuracy request must refuse unevaluated physical errors.
A nominal model evaluation may instead return explicitly unknown physical errors.

The provider owns finite physical/model coverage and proves a reuse certificate
over an admitted interval. For a held direction at anchor a, certify

\[
 \sup_{t\in I}\operatorname{angle}(u(t),u(a))+
 \epsilon_{\mathrm{numerical},a}\leq\epsilon_{\mathrm{reuse}}.
\]

A proper-motion-times-elapsed-time estimate is useful for screening; full
rectilinear motion needs a bound accounting for perspective and changing distance.
Unknown physical validity cannot be repaired by satisfying this computational
reuse inequality. No reuse chains: propagate from the original admitted solution,
and associate reuse with an original computed anchor. The existing SDK checks
certificate identities, metric, scope, time scale, coverage and error channel;
it does not infer a physical bound from catalogue motions. Existing same-scale
sessions require explicit TCB queries or a separately admitted time conversion,
not a relabelled TT request. Numerical backends must establish their own coverage.

Cache identities include source bytes, adopted qualification, centre/motion/
distance/RV policy, model/backend versions, time conventions and requested subset.
Only changed object families/solutions are invalidated. Updating cluster epochs
must not re-evaluate static galaxies or unrelated providers. Tests must cover
source facts, refusal, independent motion oracles, pole/wrap/zero-motion cases,
forward/backward epochs, strict-accuracy refusal, certificate boundaries and
unrelated-provider call counts. Add chart/saved/installation seams when routing
or transport changes; do not pre-emptively rerun unrelated suites for this contract.

## Original functionality and test audit

**Audit revision:** 1, 2026-10-18. **Inspected revision:**
`856fed20d2e38da3e315c1b15ed9c2e14b51d678`, PR #236 before these amendments.
Production still matches the accepted `6708f54a` baseline. No kernel runtime,
catalogue, dependency or science test is changed by this audit.

## Finding and limits

Wenu has useful geometry, ephemeris, observer and renderer boundaries, but
its installed package and test suite do not yet provide independently testable
astronomical modules. The main problem is responsibility and dependency
coupling, rather than simply the number of tests. The current broad package
facade eagerly imports product/domain owners. Even `from wenu.coordinates`
first initializes `wenu`; a narrow-looking import is not proof of isolation.

The [machine-readable inventory](kernel_migration_inventory_v1.json) pins all
262 production Python files and all 239 Python files under `tests` to Git blob
identities. It includes eight installed commands and 118 operational artifacts
(examples, tools, packaged notebooks and the build helper). AST inspection
was supplemented with targeted source/test review of the public interfaces,
boundary rules, shared fixtures, atlas, catalogue, rendering and scientific
routes. The [source map](source_tree.md) supplies current module responsibilities.

This is static evidence, not a fresh pytest collection, coverage report or
performance profile. Imports identify dependencies, not assertions reached at
runtime. File completeness does not prove every execution path is covered.
The functionality ledger below records located test owners; each runtime
migration must add named public-path and failure evidence before marking its
row complete. Unknown or untested behavior remains explicit.

## Measured suite structure

| Static measurement | Result | Interpretation |
|---|---:|---|
| Test modules | 226 | Plus two helpers and eleven example-fixture scripts |
| Test function definitions | 2,440 | Not the parametrized collected-case count |
| Parametrization decorators | 313 | Includes useful interactions; not automatically redundancy |
| Modules containing integration / visual / slow markers | 11 / 3 / 2 | A marker can apply to only one test in a mixed file |
| Modules containing none of those three markers | 212 | Cannot select reliable cost tiers from present marks |
| Modules importing the broad `wenu` facade explicitly | 86 | Submodule imports can also initialize the facade |
| Modules with top-level Matplotlib imports | 30 | Collection itself can require the rendering stack |
| Explicit fixture declarations by scope | 21 function / 8 module | No central `tests/conftest.py` at the inspected revision |

The last full production receipt remains 3,606 passed in 1,136.74 s on the
Mac, before documentation cleanup. K1's 15-test receipt covers its selected
documentation gate only. Neither receipt establishes the current full collected
count or explains where those 19 minutes are spent. Profile representative
owner gates with `--durations`, separately measuring collection, cold source
loading and warm numerical work, before promising a speedup.

### Concrete coupling and repetition candidates

| Evidence | Why selection is currently too broad | Required treatment |
|---|---|---|
| `test_open_clusters.py`: 1,034 lines, 32 definitions | Catalogue science, curation tools, observer realization, projection and PNG/PDF/SVG drawing share a file and imports | Split by provider, maintenance, realization and renderer responsibility as each owner migrates |
| `test_atlas_cli.py`: 1,612 lines, 40 definitions | Input validation, subprocess entry, physical layout, reports, snapshot/worker lifecycle and rendering matrices share one owner file | Retain installed-path and lifecycle integrations; move pure validation and furniture contracts to their owners |
| Atlas grid/orientation matrix | 3 polar choices × 2 grid settings × 2 orientations × 2 minute-label settings invoke real drawing | Verify the fault/interactions before reducing cases; test orthogonal option translation below rendering and retain meaningful visual interactions |
| Atlas report sizing matrix | 2 typography × 2 dimensions × 2 star choices × 2 polar choices | Separate arithmetic/selection from physical book-layout evidence; do not delete combined cases merely for speed |
| `test_style_contracts.py`: 1,445 lines, 69 definitions | Pure resolution and rendered/observer behavior are mixed | Keep style semantics independent of providers; retain a small public render seam |
| `test_reusable_canonical_sphere.py` | Real maximal-sky module fixtures and multiple chart families intentionally cross owners | Keep as integration/order-independence coverage, not a provider development gate |
| Three pouch tests import `test_polar_pouch_rendering` | A test module becomes another test's fixture library | Move shared fixtures into an owning helper/conftest with explicit dependencies |
| Package/dependency boundary tests | Valuable AST restrictions coexist with runtime imports of the complete package | Retain existing rules; add core/provider import and collection checks in genuinely minimal installations |

There is no evidence here for deleting independent scientific oracles,
positive/negative cases, cold-start behavior, order independence, immutable
snapshot tests or public CLI coverage. Parametrization is not by itself a
performance defect. A profile and a protected-fault map must precede reduction.

## Current functionality ledger

Source paths are relative to `src/wenu`; test names are under `tests`.
These are responsibility groups, not proposed giant packages. Several groups
need multiple eventual packages. Existing public names remain supported.

| Capability | Current source owners / located test evidence | Migration obligation |
|---|---|---|
| Time, frame, origin, status, epoch/equinox | `coordinates.py`, `coordinate_service.py`; `test_coordinate_vocabulary.py`, `test_coordinate_service.py` | Typed kernel/realization adapters; preserve meanings and failure admission |
| Position and Cartesian ephemeris protocols | `positions.py`, `ephemeris.py`, `skyfield_ephemeris.py`; `test_position_providers.py`, `test_ephemeris.py`, `test_skyfield_ephemeris.py` | One uniform state interface; retain resource chains, coverage, centres and units |
| Observer lifetime, site and observed cache | `observer.py`, `sky/realization.py`; `test_observer_resources.py`, `test_observer_boundaries.py`, `test_observed_cache.py`, `test_layer_realization.py` | Separate native state from realization, resource ownership and observation invalidation |
| Native catalogue assembly and reusable sky | `sky/maximal_sphere.py`, `sky/celestial_sphere.py`; `test_maximal_sphere.py`, `test_reusable_canonical_sphere.py` | Compatible facade/session assembly; remove concrete-provider coupling |
| Stars and visual symbols | `objects/stars.py`; `test_stars.py`, `test_stellar_symbols.py`, `test_stellar_magnitude_legend.py` | Add honest Gaia propagation through star provider; keep photometry/membership/marker law separate |
| Names, components and research policy | `star_designations.py`, `stellar_research.py`; `test_star_designations.py` | Preserve HIP/component identities, curated/contextual labels and source provenance |
| Constellation figures, labels and official boundaries | `sky/constellations.py`; `test_constellation_geometry.py`, `test_constellation_boundaries.py`, `test_constellation_labels.py`, `test_constellation_resolver.py` | Stellar endpoints consume propagated IDs; official boundaries retain defining frame |
| Nonstellar/Messier points and object identity | `objects/nonstellar.py`; `test_nonstellar_catalogue.py`, `test_nonstellar_points.py`, `test_object_center.py` | Retain label-only versus scientific layers and independent source membership |
| Open clusters and curated selection | `objects/open_clusters.py`; `test_open_clusters.py`, `test_curated_catalogues.py` | Independent provider and curation owner; preserve sizes, membership, criteria and original sources |
| Globular clusters | `objects/globular_clusters.py`; `test_globular_clusters.py` | Independent provider and its own science/conformance gate |
| Galaxies and extended geometry | `objects/galaxies.py`; `test_galaxy_catalogue.py`, `test_galaxy_geometry.py`, `test_deep_sky_polygons.py` | Preserve direction, angular dimensions, orientation and no fabricated velocity |
| Planetary nebulae | `objects/planetary_nebulae.py`; `test_planetary_nebulae.py`, `test_curated_catalogues.py` | Separate catalogue/criteria from display scale and default bundle |
| Supernova remnants | `objects/supernova_remnants.py`; `test_supernova_remnants.py` | Preserve provider-specific geometry and data fidelity |
| Milky Way and Magellanic isophotes | `sky/milky_way.py`, `sky/magellanic_clouds.py`; `test_isophotes.py`, `test_magellanic_clouds.py` | Extended celestial geometry adapter; not artificial point-body states |
| Equatorial, ecliptic, Galactic and AltAz grids | `sky/coordinate_grids.py`; `test_coordinate_grids.py`, `test_altaz_grid.py` | Constructed reference geometry; observer dependencies explicit |
| Horizon, visibility and masks | `sky/horizon.py`, `visibility.py`; `test_visibility.py`, `test_horizon_reference.py`, `test_horizon_mask_geometry.py` | Realization/local geometry service; no mutation of native sky |
| Spherical/projected geometry and clipping | `geometry/`; `test_spherical.py`, `test_projected.py`, `test_clipping.py`, `test_geometry_pipeline.py` | Preserve topology, metadata, IDs and guard/clip ordering; no provider dependency |
| All three projection implementations | `projections/`; `test_mollweide_projection.py`, `test_polar_azimuthal_equidistant_projection.py`, `test_projection_regression.py` | Keep Mollweide, stereographic and polar azimuthal equidistant; no astronomical transform hidden in alignment |
| Five ordinary chart families and target/group centres | `charts/`; `test_all_sky_chart.py`, `test_full_sky_chart.py`, `test_regional_chart.py`, `test_canonical_circumpolar_example.py`, `test_canonical_binocular_example.py`, `test_target_resolver.py` | Every public product consumes state via session/realization; preserve centre/mask independence |
| Styles, detail, modes, independent layer selection | `charts/composition.py`, `configuration/`; `test_style_contracts.py`, `test_detail_policy.py`, `test_chart_composition.py` | Pure product services; avoid loading numerical providers for option translation |
| Furniture, labels, references and physical legends | `charts/`; `test_chart_furniture.py`, `test_legend_export.py`, `test_reference_label_placement.py`, `test_constellation_labels.py` | Keep physical units, collision policy and scientific/appearance distinction |
| Matplotlib and PNG/PDF/SVG export | `rendering/`, `svg_document.py`; `test_matplotlib_renderer.py`, `test_svg_output.py`, `test_svg_cross_product_acceptance.py`, `test_output_policy.py` | Preserve semantic SVG, fonts, vector/raster choices, single save and no-clobber contracts |
| Polar planisphere pairs and calendar | `charts/polar_planisphere.py`; `test_polar_planisphere_pair.py`, `test_polar_calendar.py`, `test_polar_classroom_disk_freeze.py` | Preserve both projections, fixed classroom scene and physical scale |
| Polar pages, pouches, sheet assembly | `charts/`; `test_polar_page_export.py`, `test_polar_pouch_export.py`, `test_polar_pouch_sheet.py` | Preserve physical printable products, calendar/reference furniture and accepted appearance |
| Ordinary temporal sequences, resume and playback | `temporal.py`, `charts/sequence.py`; `test_temporal.py`, `test_chart_sequence.py`, `test_sequence_manifest.py` | Query common state/realization; preserve civil versus physical time, manifests and resume identity |
| Fixed-sky baseline and rotating-horizon reference | `charts/fixed_sky_sequence.py`, `charts/fixed_sky_orientation.py`, `charts/fixed_sky_baseline.py`; `test_fixed_sky_sequence.py`, `test_fixed_sky_orientation.py`, `test_fixed_sky_baseline.py` | Preserve distinct anchor/local instants and both scientific and graphical oracles |
| Major planets, Moon and apparent directions | `solar_system_directions.py`, `sky/solar_system_points.py`; `test_apparent_major_planets.py`, `test_moon_direction_validation.py`, `test_solar_system_directions.py` | Existing backend and one light-time owner; preserve body/barycentre distinctions |
| Resolved disks, appearance and frozen/observed sequences | `solar_system_appearance.py`, `solar_system_disk_geometry.py`; `test_moon_disk_display.py`, `test_venus_disk_display.py`, `test_frozen_earth_disk_sequences.py` | Keep physical versus magnified display geometry and chronology conventions |
| Natural-body tracks and temporal components | `sky/solar_system_tracks.py`, `temporal_components.py`; `test_solar_system_tracks.py`, `test_solar_system_track_cli.py`, `test_temporal_components.py` | Sample requested instants via kernel; preserve fixed chart axes and component admission |
| Numbered asteroids and offline minor-body resources | `minor_body_*.py`; `test_minor_body_ephemeris.py`, `test_minor_body_resources.py`, `test_minor_body_identity.py` | Separate asteroid provider; preserve exact manifests, coverage and close/rollback behavior |
| Comet discovery, identity, acquisition and photometry | `comet_*.py`, `minor_body_acquisition.py`; `test_comet_discovery.py`, `test_comet_numerical_validation.py`, `test_minor_body_acquisition.py` | Separate maintenance, physical provider and model magnitude; no rendering-time network |
| Antisolar reference | `antisolar.py`; `test_50a5b_antisolar_evidence.py` | Preserve observer-relative reference and provenance; not a new physical body |
| Satellite element snapshots and SGP4/TEME | `satellites/`; `test_satellite_elements.py`, `test_satellite_sgp4.py`, `test_satellite_snapshot_admission.py`, `test_satellite_topocentric.py` | Independent satellite provider; retain EOP/time/resource domain and Vallado evidence |
| Sampled-provider satellite candidates | `satchecker.py`, `satellite_presentations.py`; `test_satchecker.py`, `test_satellite_presentations.py` | Explicit provider/maintenance adapter; do not conflate candidates with exact visits |
| Exact crossings, batch selection and tracks | `satellite_crossings.py`, `satellites/`; `test_satellite_crossing_oracle.py`, `test_satellite_crossing_acceleration.py`, `test_satellite_crossing_batch.py`, `test_satellite_exact_tracks.py` | Kernel states for non-chart consumers too; preserve conservative completeness and solved-evidence route |
| Exact reports, tabular interchange, CLI and advisories | `satellite_crossing_reports.py`, `_satellite_tabular_reports.py`, `satellite_planning_advisories.py`; `test_satellite_crossing_reports.py`, `test_satellite_crossing_cli.py`, `test_satellite_planning_advisories.py` | Retain canonical identity, Unicode/null losslessness, atomic publication and offline advisory behavior |
| Satellite illumination and finite-Sun shadows | `satellites/`; `test_satellite_illumination.py` | Retain native/topocentric geometry, shadow transitions, physical domains and independent evidence |
| Bolometric and spectral solar radiometry | `satellites/`; `test_satellite_radiometry.py` | Preserve solar constant, exact TSIS resource/native sampling and uncertainty limits; no new Moonlight claims |
| Atlas geometry, layouts and standalone index | `atlas_design.py`, `charts/atlas_index.py`; `test_atlas_design.py`, `test_atlas_cli.py` | Public chart contract below atlas; all registered layouts including hemispheres |
| Atlas publication, reports, saved sky and workers | `charts/atlas_publication.py`, `sky/native_snapshot.py`; `test_atlas_cli.py` | Preserve frozen resources/coverage/design binding, chart numbering, physical sheets, PDF assembly and atomic failure cleanup |
| Configuration overlays, preset resources and translations | `configuration/`, `resources.py`, `translations.py`; `test_configuration_user_overlay.py`, `test_configuration_runtime_closure.py`, `test_translations.py` | Keep schema/precedence, separate layout/index/style protocols and localized labels |
| Canonical examples and installers | `example_scripts/`, `cli/examples.py`, `cli/notebooks.py`; `test_canonical_examples.py`, `test_example_installer.py` | Six examples, eight commands and five packaged notebooks remain release obligations; notebook installer lacks located direct test |
| Curation/acquisition, resource packaging and offline tools | `resources.py`, `src/curated_catalogue_packaging.py` (outside Wenu), `tools/`; `test_curated_catalogues.py`, `test_repository_sources.py`, `test_open_clusters.py` | Separate maintenance/build gates, exact resource identity and offline fixtures; do not automatically execute network tools |

Full inventory prevents silent disappearance of small modules or operational
scripts not individually named above. Not every maintenance script is an
accepted public API or independently tested tool: classify each before changing
it. Five packaged notebooks are inventoried; no direct notebook-installer test
reference was located in the 239 Python test files. Treat that as a coverage
review item, not proof that all notebook behavior fails or is untested indirectly.

Unfinished features remain unfinished: automatic/provisional minor-body
selection, detailed atlas object inventories, satellite reflected-light and
detector science, and numerical Moonlight. The current
[scientific contracts](scientific_contracts.md) govern these limits.

## Explicit native cluster motion consumer boundary

Native Python chart layers now accept an admitted motion catalogue per call and
a matching explicit TCB context epoch. `OpenClusters.position` and native layer
realization query the accepted provider/kernel and use returned vectors, retaining
ordered/duplicate identities and original state provenance. Source digest and
complete identity-set mismatches, unavailable selected rows and kernel failures
refuse without lookup fallback. Default lookup, source table bytes and metadata
remain unchanged. Observer-dependent motion is refused.

Restored v5 source skies inherit the same facade; they do not reload original
catalogues, install the model globally or become persisted epoch states. The
canonical chart guard admits matching epoch-bearing barycentric astrometry while
static neighbours retain source meaning. The consumer gate covers real saved/cold
geometry/pixels, fresh-process offline use, default native page compatibility and
the shared context/failure contracts. Provider science/SDK/reuse are unchanged;
their accepted receipts remain separate. CLI/TOML model selection, observer
adoption and any evaluated-state snapshot format remain open.

## Continuous test migration and closure evidence

1. **K1, now:** inventory and classify before runtime work. Repair the stale
   atlas index/test and three fixed-sky documentation checks found by this audit.
   Preserve the exact old test editions in the audit archive, with blob IDs in
   the inventory. Production/scientific tests remain unchanged.
2. **Every K2 onward slice:** identify changed owner, its public contract,
   affected consumers and closest existing assertions. Separate mixed tests
   when that owner changes. Record old node IDs to new node IDs, protected
   faults, retained independent oracles and fixture ownership. Do not defer
   all test reorganization to the final release or perform a speculative
   mass move before an actual implementation boundary exists.
3. **K2:** core unit and shared provider-conformance gates collect/run in a
   minimal environment with synthetic providers only. Contract tests are a
   reusable kit run independently against each provider, not one suite requiring
   every provider. Prove forbidden imports/dependencies are absent at startup
   and collection, not merely absent from selected test execution.
4. **K3–K5:** each current functionality row gains migration status, owning
   package/service, public entry points, instrumented query evidence, immediate
   seam/failure cases and an acceptance receipt. Audit direct position reads,
   saved-sky restoration and worker startup for bypasses. Keep numerical,
   visual, print and classroom acceptance separate. Pure layout/installation
   code need not query the kernel; every scientific state consumer must.
5. **K6–K8, package by package:** extract corresponding tests/fixtures and
   build an isolated wheel/environment gate with unrelated providers absent.
   The package is not complete until this passes. Keep installed product
   combinations in a separate release gate. A compatible internal provider
   change does not run that release gate or another provider's science suite.
6. **K9:** reconcile all inventory entries and functionality rows, including
   resources, tools, examples/notebooks and non-chart consumers. Any removed
   assertion needs an explicit replacement/fault argument; any capability
   changed or retired needs separate approval. Remaining gaps cannot be
   silently reported as migration coverage.

An owner/dependency-based selection manifest must accompany the first isolated
runtime gate. It records what changed, selected suites, relevant contracts and
why other suites are excluded. Follow [testing policy](testing_policy.md) for
changes to shared contracts/dependencies, unknown impact and integration.

## Verification of this audit

All 262 cached production modules and all 239 fetched test-side Python files
were checked against their exact baseline Git blobs and parsed. Public scripts
were read from `pyproject.toml`; imports, fixtures, markers and parametrization
were counted from ASTs. Targeted source/test pairs above support the findings.
No current duration, full-suite pass or executable modularity is claimed.

After the amendments, 32 actual documentation test functions executed directly
and passed in this environment. Active links/anchors were additionally checked
against the Git tree and amended documents. Three injected inventory faults
(omitting a source module, a test-side file or an installed command) each failed
the inventory gate and were restored. Pytest and Wenu runtime dependencies are
unavailable here: this is not a pytest receipt. The public-import execution and
original cleanup archive checks require the complete Mac gate below.

The amended documentation gate includes `test_current_documentation.py`,
`test_user_guide.py` and `test_fixed_sky_documentation.py`. A fresh Mac result
is required for that amended gate. Current runtime remains the accepted
production tree; K2 has not begun.

Preserved originals: [user-guide tests](archive/kernel_audit_20261018/tests/test_user_guide.py.txt)
and [fixed-sky documentation tests](archive/kernel_audit_20261018/tests/test_fixed_sky_documentation.py.txt).

## K3.16 diffuse geometry assessment and architectural resolution

**Inspected base:** main `21653198502b2b6687af8d82556a7f98922eb4fd`,
2026-10-19. Fernando selected K3.16 with “proceed” after its bounded proposal.
This assessment did not authorize a new SDK capability or snapshot format;
the subsequent service-kernel clarification is recorded below.
No runtime, SDK, source-resource, dependency or serialization change is made here.
K3.16 remains open for runtime work under the architectural resolution below.

### Source and runtime evidence

| Owner/resource | Preserved evidence | Remaining admission gap |
|---|---|---|
| Milky Way canonical `milky_way_d3.json` and five runtime single-level GeoJSON files | D3-Celestial blob `ce06eaa01d80a4eed149c538d2d162c919b58a84`, captured provenance/BSD licence; canonical SHA-256 `c6cf082cb0ffb9a6080858f673eb8f119df585b00730a5bcfd5ea43dc3f98627`; OL1–OL5 MultiPolygons | GeoJSON has no document/feature frame or epoch declaration. README says source celestial longitude/latitude degrees. Existing runtime ICRS encoding is compatibility interpretation, not recovered source qualification. Bind the canonical/provenance and actual loaded split bytes without inventing a measurement epoch |
| LMC/SMC derived GeoJSON | Document properties explicitly declare ICRS, RA/Dec degrees, outer-to-inner levels and `g_flux`; features retain cloud/level/fraction. Captured sidecar declares Gaia DR3, processing, ADQL and product digests | Loaders discard these document/source properties. No morphology measurement epoch, distance or physical origin is declared; do not assign Gaia's stellar reference epoch to a derived contour |
| LMC product identity | SHA-256 `9ad2298999577bbf96a2ad743b90106c3e971948ed2cc832e2fd33cb59f2fc4e` matches the captured sidecar | Keep byte-bound identity and processing provenance in a runtime envelope |
| SMC product identity | SHA-256 `348d0f485088d6c40efb70dd04fcad3247aa7d9a0e1fe26611b6b10e3f972695` matches the captured sidecar | Same requirement; retain cloud-specific identity and levels |
| `sky/milky_way.py`, `sky/magellanic_clouds.py` | Existing `features` preserve compounds/rings/holes; Milky Way realization also computes filled-side, area and pole-winding metadata. Native and observed paths consume raw rings; observer cache identities use paths/revision/levels | Admit immutable source/reference/geometry identity before native output or warm-cache reuse. Preserve topology and original vertex encodings. Observation/projection/rendering remain above the kernel |
| `sky/native_snapshot.py` | v5 records diffuse features plus source paths and Cloud fractions; manifest binds source digests. Restoration assigns those fields directly | Original GeoJSON document/feature properties and a runtime metadata envelope are not serialized. Extending source metadata transport requires an explicit format/legacy-admission design, not relabelling old snapshots as newly qualified |

No acquisition was run and no captured source or licence record was changed.
The PM/parallax selection used when deriving the Cloud maps does not turn their
contours into member-star states or a motion model.

### Architectural resolution: agreed service kernel

Fernando clarified on 2026-10-19 that spherical geometry and projections belong
to the shared service kernel, and subsequently requested these architectural
decisions be documented. The [agreed target and prior-K disposition](kernel_roadmap_v0.9.5.md#proposed-architecture)
are authoritative. The existing state SDK remains one component of that kernel.
Its lack of a compound-ring StateBatch variant is not, by itself, a missing
prerequisite for diffuse geometry migration.

The earlier proposal to add a new SDK geometry query/result/admission capability
and require a new snapshot format was not approved or implemented. It is withdrawn
as the default solution. Direct use of shared spherical geometry/topology and
projection services is valid kernel routing, not an exception to closure.

K3.16 will start from existing SphericalPolygons and the current geometry,
coordinate/observation and projection interfaces. Source-specific contour ingestion,
levels, fractions and qualification remain domain responsibilities; generic ring
operations and projection mathematics belong to reusable kernel services. No
artificial body/ObjectRecord is created for each contour vertex. A new query
protocol needs a concrete discovery/lifetime/dispatch requirement before it can
be proposed again; naming something a kernel does not establish that requirement.

The M9 source and snapshot evidence above remains valid. The runtime envelope
must preserve declared versus absent coordinate facts and byte-bound provenance;
metadata-preserving transport and explicit legacy/source-free behavior still
require a concrete bounded design. This architecture decision does not choose a
snapshot version, alter existing schemas, relocate code or authorize acquisition.

### K3.16 acceptance direction under the agreed boundary

- Source/geometry owners: `test_isophotes.py` and `test_magellanic_clouds.py` retain
  exact vertex/topology/level/Cloud fraction and source-metadata/refusal coverage.
- Geometry, observer and projection seams: retain independent filled-side,
  pole-winding and hole oracles; test public geometry-service use, source/returned
  geometry identity and warm-cache refusal where admission changes.
- Snapshot/product composition: preserve native/observed cold/restored geometry,
  actual atlas PNG/PDF/SVG, legacy admission and source-free process evidence for
  each transport change actually implemented.
- Dependency/installation checks: demonstrate the changed service boundary without
  concrete catalogue/product/renderer imports. Run independent SDK tests only if
  that component's code/contracts actually change; a new SDK release/pin is not
  automatically required for calling existing geometry services.

The current change is documentation only. K3.16 runtime admission/transport remains
unimplemented; no other pending milestone is activated.

## KG.01 shared geometry service inventory

**Assessment base:** main `cb40ede9ad0be68e6a4863c8d7b6d2c3dbb87a93`,
2026-10-19; tree `c2b9ee88c80d71bf5d71c99a2b98842eeec40c91`.
Fernando selected KG.01 after accepting revision 32. This is an assessment,
not the KG.02 interface decision, a runtime migration or the KG.06 completed-K
audit. The [machine inventory](kernel_migration_inventory_v1.json) records
`geometry_service_assessment`, inspected owner blob hashes and 66 direct
absolute-import consumer modules. All 512 locally available production/test
Python files were checked against accepted Git blobs with no mismatch.
Imports inside functions are included; relative package exports were inspected
separately. Import references locate potential callers, not executed coverage.

### Existing services and dependency boundaries

All paths below are relative to `src/wenu/`. These are current owners, not
proposed final package names.

| Current owner and public entry points | Actual responsibility/dependencies | KG.02 disposition to resolve |
|---|---|---|
| `geometry/spherical.py`: SphericalPoints, SphericalCurves, SphericalPolygons, SphericalGrid | NumPy arrays in degrees, required CoordinateSpec from `coordinates.py`, per-entity IDs/labels/names and metadata; validates dimensions/counts and grid spec equality | Reuse the data model first. Decide shared CoordinateSpec ownership and explicit topology/metadata contracts; arrays are not admitted physical state batches |
| `geometry/projected.py`: ProjectedPoint(s), ProjectedCurve(s), ProjectedPolygon(s), ProjectedGrid | NumPy planar records, finite masks and bounds; no source/provider/renderer imports in this module | Preserve collection identity and metadata after splitting; define planar scale and mutable ownership rather than treating these as immutable SDK states |
| `geometry/frame.py`: SphericalFrame, SphericalCoordinates | NumPy spherical rotations, inverse and matrix construction; frame transform normalizes longitude to [-180,180) | Generic geometry service; distinguish this orientation rotation from astronomical frame/time conversion |
| `geometry/viewport.py`: Viewport | Frozen dataclass, finite rectangular bounds, contains/size/centre helpers, NumPy | Mathematical rectangle is reusable; product chooses its extent/aspect/physical page scale |
| `geometry/clipping.py`: clip_point_to_viewport, clip_curve_to_viewport, clip_polygon_to_viewport, clip_polygon_to_convex_boundary, clip_line_segment_to_viewport, polygon_centroid | NumPy plus projected records/Viewport; nonfinite breaks and fragmented curves; convex-boundary polygon operations | Retain existing supported algorithms and their failure/empty/fragment semantics; do not claim a general spherical Boolean polygon engine |
| `projections/stereographic.py`: StereographicProjection | NumPy, spherical/projected records, SphericalFrame and Viewport; vector/scalar and collection dispatch, forward/inverse, radius helpers, legacy AltAz wrapper | Existing public service starting point; preserve EW orientation, position-angle order and antipode NaN breaks |
| `projections/polar_azimuthal_equidistant.py`: PolarAzimuthalEquidistantProjection | Subclasses StereographicProjection; overrides forward/inverse/radial math and domain checks | Preserve inherited dispatch and linear angular-radius behavior; explicitly specify supported projection capabilities rather than assuming all APIs identical |
| `projections/mollweide.py`: MollweideProjection | NumPy and geometry records; equal-area forward projection, seam-aware curve/polygon splitting, pole/winding handling, per-piece metadata expansion | Keep seam preparation with applicable mathematics. This class does not expose the same inverse/radius interface as stereographic |
| `rendering/preparation.py`: project_geometry_for_viewport, projection_cap_for_viewport, project_polygons_to_projection_cap, clip_polygons_to_projection_cap, clip_polygons_to_latitude, clip_to_latitude | Imports NumPy and geometry records; contains spherical cap clipping/intersection/slerp, filled-side complements, winding-band stitching and metadata propagation | **Mixed owner:** reusable mathematical services coexist with magnitude sizing, point_styles, radial_label_offset and diameter_marker_areas. Extract responsibilities through agreed interfaces; moving the whole module would move appearance policy into the kernel |
| `sky/milky_way.py`: _native_ring_interior and layer realization | Numerical solid-angle/orientation math combined with source ring interpretation, hole/level metadata, observed-cache and resource loading | Identify the reusable math separately from catalogue filled-side convention and source qualification; K3.16 still owns M9 admission/transport |
| `coordinates.py`, `coordinate_service.py` | CoordinateSpec/status vocabulary versus Astropy-backed scientific realization and metadata propagation | Geometry depends on the vocabulary today. Scientific conversion is a separate service/backend boundary; do not pull Astropy conversion into a plain spherical rotation |
| `charts/projection_selection.py`, `charts/boundaries.py`, `charts/styles.py` | Projection/frame allowlist and lazy construction; boundary construction plus label-anchor/style policy; horizon threshold and appearance preparation | Product selection, labels and policy stay outside; review generic boundary primitives individually. A chart's horizon cut is not the projection singularity guard |
| `rendering/matplotlib.py`, `_matplotlib_primitives.py`, `_matplotlib_axes.py` | Draw projected values, compound paths and viewport artists | Renderer remains outside; geometric service must not depend on Matplotlib |
| `sky/celestial_sphere.py`: draw_chart | Orders layer realization → selected projection callback → preparation → renderer; owns concrete layers | Retain canonical orchestration. Correct ownership/imports without introducing a parallel scientific/rendering pipeline |

### Topology and domain contracts that already cross boundaries

SphericalPolygons represents implicitly closed rings, with at least three
vertices; holes and compound-polygon identity are not dedicated typed fields.
Existing consumers use metadata such as `is_hole`,
`spherical_interior_left`, `spherical_interior_area_sr`,
`projection_cap_topology_inversion` and projection-source latitude arrays.
Mollweide seam splitting and cap clipping can turn one source entity into
several pieces. IDs, labels and per-ring attributes must expand with those pieces;
they cannot be blindly zipped against the original unsplit arrays.

The cap service performs spherical clipping **before** unsafe planar polygon
projection. Its viewport entry point derives a near-hemisphere cap using the
projection's radial inverse capability; it delegates normally when that
capability or a polygon/viewport is absent. Later viewport clipping and
chart-specific horizon/mask policy remain distinct. The current capability is
duck-typed, not a frozen common protocol. KG.02 must document those supported
branches before KG.04 changes ownership.

Geometry dataclasses generally retain writable NumPy arrays using
`np.asarray`; metadata dictionaries are shallow copies. The frozen
SphericalFrame does not imply every returned array is immutable; supplied
rotation matrices are copied and marked read-only, while construction validates
their shape, not a general arbitrary-matrix orthogonality guarantee.
Projection instances hold mutable configuration fields. KG.02 must state
ownership/lifetime/aliasing and compatibility rules; KG.01 neither changes
these semantics nor promises an immutable kernel geometry API.

### Callers and import isolation

The machine inventory records exact import names for every detected direct
absolute-import consumer, grouped conceptually here:

| Consumer group | Observed use | Boundary consequence |
|---|---|---|
| Object facades: stars, nonstellar, galaxies, open clusters and PN | Produce/consume spherical collections; dedicated globular/SNR behavior also inherits shared nonstellar mechanics | Keep object identity/source/model decisions outside shared math. Indirect inheritance and dynamic calls require later KG.06 review, not just import counts |
| Sky layers: points, constellation figures/labels/boundaries, grids, horizon, diffuse contours, solar-system/satellite/sequence layers | Construct spherical values and use existing observation/preparation helpers | Preserve supported coordinate status/spec and source identity; not every ring vertex is a physical provider object |
| Regional/full/all-sky/polar/circumpolar charts, atlas design/index/publication, reference and mask helpers | Construct projections/boundaries; call cap-safe projection, clipping and label anchoring | Chart policy remains outside; mathematical service calls should become explicit public dependencies |
| CoordinateService, positions, solar-system directions/disk geometry, temporal components and ephemeris adapters | Exchange geometry or frame rotations across science/product seams | Separate numerical geometry from backend-specific realization; do not infer identical scientific semantics from array shape |
| Renderer/primitives/label placement and geometry/projection implementations | Consume projected records or apply shared geometry | Kernel interfaces may be imported by a renderer, never the reverse |

A fresh subprocess importing `wenu.geometry.spherical` loaded
`wenu.observer`, `wenu.objects.nonstellar`, `wenu.charts.regional`,
`wenu.rendering.matplotlib`, Matplotlib, Astropy and Skyfield.
This confirms the broad `wenu/__init__.py` application facade defeats independent
geometry import today. Separately, `rendering/__init__.py` eagerly exports
Matplotlib implementations and preparation functions together. The algorithm
bodies' narrow direct imports do not establish package isolation. The existing
stdlib state SDK stays separate; no new geometry wheel or dependency is selected
by this finding. KG.02 must propose concrete placement/import compatibility.

### Existing test owners and protected faults

These tests were inspected/located, **not rerun as numerical acceptance** in
this documentation-only assessment. Their current success is not asserted here.
No new test selection, production resource, dependency or build change is made.

| Existing owners under tests/ | Evidence/faults to retain in the corresponding migration |
|---|---|
| test_spherical.py, test_projected.py, test_projected_collections.py | Dimensions/counts, grid grouping, metadata copying, finite/bounds and collection identity |
| test_spherical_frame.py | Identity, inverse round trip, orthogonal constructed rotations, scalar input and public import |
| test_projection_regression.py, test_projected_geometry_projection.py, test_projection_geometry.py | Existing stereographic formula, EW flip, dispatch/types/metadata, argument refusal and antipode disconnected breaks |
| test_polar_azimuthal_equidistant_projection.py | Known pole/quadrants, forward/inverse round trip, linear radius, PA/flip order and invalid-domain refusal |
| test_mollweide_projection.py | Known centre/equator/seam/pole coordinates, local equal-area scale, seam splits, finite breaks and winding closure |
| test_clipping.py, test_viewport.py, test_projection_and_clipping_contracts.py | Viewport/convex clipping, split curves, cap-before-projection ordering, four-corner cap coverage, horizon composition, filled-side complements and winding-band fragments |
| test_viewport_rendering.py, test_projection_selection.py | Renderer viewport composition and product projection/frame admission |
| test_isophotes.py, test_magellanic_clouds.py | Real/source and synthetic rings, hole/level/fraction selection, independent filled-side/raster membership and observed-cache behavior |
| test_reusable_canonical_sphere.py and affected atlas/polar product owners | Source-free/cold/restored geometry and output equivalence at integration acceptance; exact specimens chosen from the actual later diff |

KG.02 must map these owners to the concrete interface/placement diff and add
only missing seam/isolation evidence. Numerical oracles must remain independent
of the service implementation. KG.05 needs actual output acceptance in addition
to unit geometry tests; this inventory alone does not establish it.

### Findings and next bounded work

1. **KG01.F1:** mathematical clipping/topology shares rendering preparation with
   appearance helpers; split by responsibility rather than moving the whole file.
2. **KG01.F2:** geometry import runs the broad application facade; establish an
   independent service import with compatibility for old callers.
3. **KG01.F3:** CoordinateSpec ownership and implicit topology/metadata expansion
   need explicit public contracts.
4. **KG01.F4:** generic ring math is mixed with source-specific interior policy;
   preserve source facts while identifying the reusable operation.
5. **KG01.F5:** writable arrays, shallow metadata copies and mutable projection
   configuration need honest lifecycle/aliasing semantics.

**Next bounded milestone: KG.02**, public contracts and incremental placement
plan, after acceptance of this assessment and explicit task selection.
Do not relocate implementations, invent a geometry query, change science,
force a snapshot version or activate K3.16 here. The coordinate guide remains
current because this assessment changes no scientific semantics or runtime
ownership. The later KG.06 audit will determine modifications to completed K
deliveries using the established services, retaining their applicable receipts.
