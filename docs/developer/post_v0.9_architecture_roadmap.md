Warning: truncated output (original token count: 85729)
Total output lines: 5779

# Wenu post-v0.9 architecture roadmap

**Status:** Active; architecture 0.9.5, 49F, and 49G complete; 49H.3 accepted

**Planning baseline:** `52e9411`

**Decision date:** 2026-08-19


## Current forward roadmap

## Atlas organisation checkpoint (2026-10-09)

The label work (PR #211) and Chile location catalogue (PR #212) are merged.
The current baseline is `7e71ae8c008d6b495dc57180f634524f8dd0879c`; Fernando's
catalogue acceptance receipt records 3,123 passing tests and a clean branch.
The agreed next priority is atlas organisation, then general stellar curation
(including multiple and variable stars), deep-sky curation and individual
chart/report review. This checkpoint supersedes the earlier sequencing of
stellar designations, minor bodies, atlas publication and satellites below;
those historical milestones remain evidence, not the current next-action list.

The [atlas user guide](../user_guide/atlas.md) supplies the command/input
diagram and the user preparation steps. The designer CLI is accepted and merged
in PR #220; the installed index plotter is accepted and merged in PR #221
(see the publication checkpoint). `wenu_design_atlas` produces **only resolved JSON**;
`wenu_plot_atlas` consumes it with independent index presentation inputs;
`wenu_create_atlas` consumes it with publication and curation inputs.
The original planning checkpoint did not implement or freeze their CLI/schema;
the later designer checkpoint specifies its bounded version-1 request.

| Stage | Work | Acceptance gate |
|---|---|---|
| Contract and audit | Audit existing chart, projection, clipping, report and export owners; define versioned request/JSON boundaries | Physical useful rectangle, frame/equinox, identity, numbering and validation contracts reviewed |
| Spherical coverage | Compare candidate field sizes/projections and resolve tangent-plane centres, including two polar sheets | Whole-sphere coverage with no gaps; overlap measured; primary areas and neighbours validated |
| Designer | Implement `wenu_design_atlas` with common-meridian RA and total overview-band width | Deterministic resolved JSON only; no catalogue selection or figure |
| Index plotter | Implement `wenu_plot_atlas`; compose the overlapping hemispheric polar views and optional astronomy layers | Same JSON supports different index presentations; primary borders exclude overlap; numbering is consistent |
| Page producer | Implement `wenu_create_atlas` through the canonical chart pipeline | B4 landscape right chart/left report pairs; requested PNG/PDF/SVG exports; repeatable sample generation |
| Reports and selection | Preserve catalogue entries while selecting/indexing plotted objects; classify observational interest | Naked-eye/binocular/amateur-telescope categories and pending curation remain explicit; overlap cross-references and extended-object membership reviewed |
| Pilot curation | Review Orion and a contrasting region; establish star sizes, typography and report appearance | Sample pairs accepted before a complete atlas batch |
| Atlas curation and publication | Stellar multiples/variables, deep-sky selection, individual charts, zoom subcharts and print organisation | Reviewed chart/report pairs, retained object index and reproducible publication revision |

The initial physical target is ISO B4 landscape (353 × 250 mm), not a fixed
angular tiling. Projection and field size remain decisions for comparison.
Actual polar atlas sheets are distinct from hemispheric index views. Sheet
overlap, the total shared equatorial band width and overlap on the printed
index are independent parameters. Changing index styling never changes tiling;
changing individual-sheet geometry requires a new resolved design.

Authority review: this is planned orchestration, not an implemented architecture
change. The current architecture, implementation reference, source responsibility
map, diagram inventory and coordinate-system guide were reviewed; their runtime
ownership remains unchanged. Coordinate-frame/equinox conventions remain distinct
from stellar source epochs. Later implementation requires its own as-is audit
and bounded acceptance.



### Atlas geometry contract candidate (2026-10-09)

Fernando accepted workflow head `c49b908adecdf7219fc15223ed13c5511a66db66`
and requested the next step. This is its documentation-only as-is audit and
contract candidate. CLI flags, schema keys, projection choice and tiling
algorithm remain proposed; no atlas command is installed. Workflow acceptance
does not record Mac verification or a separate merge/deletion instruction.

#### Implementation audit at the accepted head

| Inspected owner | Existing capability | Consequence |
|---|---|---|
| `geometry/frame.py:SphericalFrame` | Spherical rotation/inverse | Reuse tangent bases; it does not transform astronomical frames |
| `projections/stereographic.py:StereographicProjection` | Arbitrary tangent frame, inverse projection, angular/plane radius conversion | Derive footprints from exact plane rectangles |
| `charts/projection_selection.py` and projection directory | Stereographic, Mollweide and polar azimuthal equidistant | Gnomonic is not installed/selectable; its comparison needs a later canonical projection extension |
| `charts/regional.py:RegionalChart` | Rectangular stereographic viewport and export | Centres are Alt/Az; `from_coordinate` transforms through an observer. A fixed-equatorial sheet adapter is missing |
| `charts/polar_planisphere.py:PolarPlanisphereChart` | Equatorial polar cap, stereographic option and canonical render | Reuse overview cap/projection; paired index composition and tiling borders need work |
| `charts/request.py:ChartRequest`, `charts/request_generation.py` | Immutable requests, composition and export | Reuse canonical flow; current observer-backed API must not make atlas geometry depend on location/time |
| `charts/regional.py:ExportOptions` | PNG/PDF/SVG with optional tight crop | Validate physical page dimensions; tight crop alone is not B4 page acceptance |
| `charts/stellar_report.py:write_stellar_report` | Stellar Markdown/JSON sidecars | Reuse discrepancies/designations; general curated-object reports and facing-page typesetting are not implemented |
| `pyproject.toml` | Existing entry points | No atlas CLI yet |

The designer must require no catalogue, observer, ephemeris, renderer or network.
Module placement for geometry orchestration requires review before runtime work.

#### Proposed geometry request

These are candidate field groups, not runnable flags or schema-v2 chart-overlay
keys. Give atlas inputs a separate versioned schema.

| Group | Content and convention |
|---|---|
| Version | Schema version, design identity/revision; reject unknown major versions and unknown keys |
| Coordinates | Propose ICRS initially, RA/Dec in degrees in JSON; unit-aware hours only at input. ICRS is not FK5 J2000; source epoch is not equinox |
| Paper | Width/height and top/bottom/inner/outer margins in mm; positive useful rectangle. Initial B4 landscape, right-page inner margin on left |
| Projection | Explicit supported projection and scale convention; existing stereographic for first prototype, final choice unresolved |
| Field | Full central horizontal angular span, not radius, diagonal or RA span. Convert half-width through projection, derive plane half-height from useful-paper aspect ratio, then inverse-convert angular height |
| Coverage | Explicit neighbouring-sheet overlap specification; propose minimum angular overlap, with measurement/construction to compare in prototype. Degrees and percentages are different choices |
| Orientation | Resolved position angle, handedness and meridian-based polar tangent orientation; pole RA alone is insufficient |
| Overview | Common-meridian RA, total shared equatorial width W; symmetric limits −W/2 north and +W/2 south, proposed domain 0 ≤ W < 180° |
| Ordering | Seed longitude and numbering policy; Orion is editorial, not catalogue centring. Band/RA ordering is a candidate |
| Precision | Declared angular approximation/validation tolerances; reject non-finite values and unsupported precision claims |

Preserve uniform physical scale. Do not derive angular height by multiplying
angular width by paper aspect ratio: use the projected rectangle.
Retain exact projection parameters and rectangle as authoritative footprint
geometry; sampled spherical edges are approximations with an error bound.

#### Proposed resolved JSON

| Group | Resolved information |
|---|---|
| Identity/provenance | Schema, design ID/revision, generator version, generating request and input provenance |
| Coordinates/page | Frame, units and handedness; paper, margins and useful rectangle |
| Overview | Common meridian and total shared band, independent of figure placement |
| Sheets | Internal ID, editorial number, polar/non-polar role, centre RA/Dec, tangent basis, projection parameters and exact plane viewport |
| Footprints | Inverse-projection definition plus spherical boundary representation with declared approximation error |
| Primary areas | Disjoint ownership regions covering the sphere; defining geometry and deterministic shared-boundary tie rule |
| Navigation | Reciprocal neighbour references and overlap measures |
| Verification | Method, tolerance, coverage/area/gap checks, overlap minima and status |

Readers must reproduce footprints without rerunning tiling. Reject duplicate
IDs/numbers, missing neighbours, invalid coordinates, inconsistent tangent bases
and disagreements between exact geometry and derived boundaries.

Every primary area must lie inside its sheet footprint. Nearest-centre/Voronoi
ownership is only a candidate if containment is verified; rectangular footprints
do not guarantee it. Handle RA wrap/poles as spherical geometry, not flat RA/Dec
polygons. Sampling alone is not proof of gap-free coverage: declare a conservative
error-bounded method and distinguish estimated coverage from certified acceptance.
A design unable to meet tolerance remains unresolved.

Identical deterministic inputs reproduce geometry, IDs and numbers. A structural
redesign receives a new design revision and namespace; correspondence of IDs
must not be assumed. Later editorial renumbering can preserve IDs for unchanged
geometry with a separate order revision. Provenance timestamps must not change
geometric identity.

#### Next bounded runtime candidate

Establish geometry records, validation and deterministic serialization using the
existing stereographic projection before automatic all-sky tiling. An explicit-
centre specimen may test the contract but must be identified as incomplete.
Install `wenu_design_atlas` only once a real complete design is resolvable and
validated; never emit a placeholder incomplete atlas as a final design.

Check projection/inverse round trips at centres, rectangle edges/corners, RA wrap
and both poles; handedness, position angle, aspect ratio and angular-height
derivation; invalid values/schema/identities; deterministic output with no
catalogue/observer/renderer/network dependency. Later coverage work checks primary
containment, reciprocal neighbours, overlap and gap-free sphere coverage before
production. Preserve existing charts and track-date placement.

Architecture/reference/source-owner documents, diagram inventory and coordinate
guide were reviewed. Their implemented ownership is unchanged: this candidate
installs no runtime module or scientific transform. Contract details require
review separately from the already accepted workflow.


**Regional v10 reference and grid correction:**
Regional v10 reference placement measures the visible contiguous curve and
its rendered label width in final display units. Automatic names search near
the curve ends; when length exceeds `label_repeat_length_factor` (default 5)
times text width, independent end windows supply two labels. Full text must
fit the sky boundary. Tangents, normal offsets, explicit anchors, polar
reference policy and temporal annotations retain their existing owners.
Schema-v2 `grids_references.references.label_repeat_length_factor` translates
through furniture and survives CLI reference selection. Coordinate latitude
lists now use symmetric multiples of their interval from zero; equatorial
grids include zero declination even without a separately requested reference.
The 70-degree regional review requests `--declination-step 15` explicitly.
Automatic density thresholds remain unchanged; no new module is introduced.


**La Ligua v6 containment follow-up (2026-10-07):** Parent `a811f55b`
passed 3,094 Mac tests in 268.54 seconds with a clean synchronized branch.
Fernando rejected narrow-region inward fallback: full constellation text must
fit its own visible IAU region and sky boundary, otherwise omit the name.
This supersedes the v4 fallback policy below. Coordinate fonts increase another
20% to atlas 5.04 and cartoon 5.76 points, with smaller crossing offsets.
Ordinary cardinal labels retain the compact band; dense diagonal text may
expand measured furniture. The authored Scorpius figure replaces sigma–delta
with sigma–beta1 without other edge changes. Existing renderer and resource
owners implement these changes. Temporal anchors and orientation remain fixed.
New candidate Mac/full and visual acceptance remain pending; PR #211 stays
 draft and unmerged. No cleanup is authorized.

**La Ligua v4 typography follow-up (2026-10-07):** Exact head `385c1b13`
passed all 3,080 Mac tests in 310.31 seconds with a clean synchronized tree.
Fernando reviewed v4 and authorized 20% larger grid labels without a wider
ring, a 1-point location-planisphere line-gap default, inward constellation
names, stronger text clearance and containment of linework at the horizon.
The candidate extends existing style/configuration, composition and final
renderer owners. Ordinary marginal text is centred in the existing band;
custom oversize text remains measurable and may enlarge furniture. Narrow
visible-region names may use bounded inward fallback positions, preserving
upright or polar orientation, colour and fixed temporal dates. Explicit CLI
and TOML gaps, including zero, retain precedence. The coordinate guide and
architecture diagrams were reviewed and remain current: scientific meaning,
ownership and pipeline are unchanged. New focused/full and visual acceptance
are required. PR #211 remains draft and unmerged; cleanup is unauthorized.

**Exterior-band follow-up (2026-10-07):** Exact shared-placement head
`bf0cdb8f` passed all 3,067 Mac tests in 280.23 seconds with clean diff and
synchronized branch. La Ligua v3 separates companion/name collisions;
constellation rim clearance and linework interference remain review issues.
Fernando authorized exterior coordinate bands for non-polar planisphere,
regional/constellation and binocular charts, choosing opaque white and a black
frame as defaults. The bounded candidate adds measured exterior furniture,
colour/width controls and real-crossing marginal anchors under existing
owners. Grid cadence, duplicate edge labels, pole-aware regional rules and
remaining constellation collisions are not closed. The coordinate guide was
reviewed and remains current: this changes appearance only. PR #211 stays
unmerged pending new full-suite and visual acceptance; no cleanup authorized.

**Label-policy milestone (2026-10-07):** Fernando authorized chart-specific
orientation overrides, preservation during collision avoidance, and a label
guide with cartographic references. The bounded candidate extends existing
chart preparation, style/configuration, and Matplotlib point-label placement.
Polar labels keep up away from the pole; other charts stay upright. Track
dates and reference tangents retain their existing paths. The image-review
correction adds actual-boundary point containment, exterior azimuth labels,
and altitude labels on cardinal spokes for horizon planispheres.
Annealing, CLI unresolved-collision reports,
other exterior coordinate bands, CLI/TOML spoke controls and density refinements remain
later work. `ChartContext` and `AdaptiveDetailPolicy` already own scale/detail
evidence; inspect those before admitting a new scale module. Grid cadence and
limiting magnitude must remain independently overridable. See the
[label guide](../user_guide/labels.md). The coordinate guide was reviewed and
remains current: no scientific coordinates, frames, epochs, equations, or
provenance changed. This candidate requires Mac full-suite and visual acceptance.

**Shared collision follow-up (2026-10-07):** After exact head `3d950643`
passed all 3,059 Mac tests in 277.66 seconds, Fernando's La Ligua image
confirmed the horizon correction but retained companion/name and
reference/star collisions. He authorized the shared candidate process.
The candidate joins stellar, bounded constellation and curve-constrained
reference alternatives under the existing automatic placement setting.
Grid labels, explicit reference anchors and temporal dates remain fixed.
Boundary and text separation precede marker/ownership/cosmetic preferences;
deterministic coordinate descent and bounded pair moves preserve typography.
No annealing or new module is added. The coordinate guide remains current.
New focused/full Mac and visual acceptance are required; PR #211 remains
unmerged, with no cleanup authorized for this branch.

**PR #210 closure (2026-10-07):** The constellation all/exclusion and Albireo
work below merged into `main` at `948b90932748da5c4c140999142b0950fa2b92ef`.
The final candidate `aec1dfe8` passed all 3,029 plugin-disabled Mac tests in
273.66 seconds; diff check passed. The branch was deleted locally and remotely,
and Fernando confirmed clean synchronized `main`. This supersedes the older
pending-validation statements below, without closing the stellar programme.

**Albireo name follow-up (2026-10-07):** Fernando requested the exact
`Cyg:Albireo` name selector after visually checking the all-constellation chart.
An authored association with HIP 95947 (β¹ Cyg; IAU component Aa) supplements
the frozen Wikidata candidates through existing curation. β² Cyg is already
available as HIP 95951 and remains distinct. Full-suite receipt at `4af4973f`
is 3,023 passing tests; the additional name candidate requires new focused and
Mac full-suite validation before acceptance. The scientific coordinate guide
was reviewed; astrometry, equations, frames and position sources are unchanged.

**Constellation-selection follow-up (2026-10-07):** Based on synchronized
`main` at `afe8e909` (PR #209), Fernando authorized independent `all` feature
selection and chose the name `exclude` for per-feature subtraction. The
bounded implementation is a review candidate on
`feat/constellation-all-and-exclusions`: CLI/TOML parity, public Serpens
adaptation and existing chart-local partial-region label preparation. Mac
full-suite and visual acceptance remain pending; this does not close the
stellar programme or alter the future-order table below. Scientific-guide
review found no change to astronomical positions, frames, equations or data
sources, so the canonical coordinate guide remains unchanged.

**Resumption checkpoint:** 2026-10-05, clean synchronized `main` at
`91f7841235d4ed49b20ae6bf5d6b3e678de4e5c5`.
The satellite foundation merged through PR #201 at `8311bd08`; comet
photometry merged through PR #121 at `91f78412`. Both development branches
were then removed locally and remotely. Merge and branch deletion preserve
accepted work and history; neither closes the unfinished 50A or 50S program.
The current checkpoint and sequence below supersede earlier future-order and
candidate-status statements in the historical milestone sections.

| Order | Work | Next reviewable outcome |
|---:|---|---|
| 1 | Bayer/Flamsteed stellar designations | Bounded as-is catalogue and label audit, then implementation using existing stellar metadata, detail/style and rendering machinery. Wikidata candidate resource and HIP metadata attachment implemented, with integration authorized; explicit name/Bayer resolution, detail/CLI/TOML, labels and optional 77-case chart reports are now a review candidate under Fernando’s approved handling policy; next verify on the Mac and review the candidate. |
| 2 | Minor-body completion (50A) | Complete automatic asteroid names and unnumbered/provisional selections (bounded audits required) → 50A.5D.3 reports → 50A.5E.0 database audit → 50A.5E.1 construction → 50A.5E.2 runtime policy → 50A.5E.3 cache lifecycle → 50A.6 final acceptance. |
| 3 | Atlas output curation and publication (50B) | Select representative atlas products, review publication/print practice (50B.0), adopt output standards (50B.1), measure specimens (50B.2), implement monochrome/grayscale profiles (50B.3), accept physical prints (50B.4), and close evidence/docs (50B.5). |
| 4 | Satellite resumption (50S) | Reopen the paused 50S.7D.3 Phase B preflight at its exact accepted boundary; later complete 50S.6I and the remaining illumination, brightness, detector and closure stages. |

### Current stellar-designation audit

The [Bayer/Flamsteed audit](stellar_designations_audit.md) records the
source-verified as-is state at `b929325a`, HIP-linked resource/preference
contract, metadata attachment, detail/style/CLI placement, label suppression,
rights gates and acceptance sequence. Fernando accepted the design and amended
name/Bayer selectors on 2026-10-05: selected stars bypass the magnitude limit;
proper names win; full Bayer text is optional; CLI and TOML agree. Future
variable/multiple curation remains separate from labels and catalogue flags.
The accepted design merged in PR #204 at `bf904a28`; the Wikidata
candidate resource and metadata attachment are now implemented, with integration authorized
(2026-10-06); see the [resource checkpoint](stellar_designations_audit.md#10-wikidata-resource-checkpoint-2026-10-06).
PR #205 includes the expanded source comparison and resource incorporation. Fernando chose Wikidata
structured data (CC0) as the resource; Kostjuk, Yale BSC, HYG and IAU/WGSN remain
comparison evidence, with no silent backfill. The 77 HIP/field discrepancies
retain their original pending cells in the frozen ledger, while Fernando’s
approved handling policy unblocks development (audit section 11). Labels/aliases are candidates,
not preferred proper names; limited name-query coverage and component identities
still need curation. Explicit label selection, CLI/TOML and optional discrepancy
reports are implemented for review; Mac acceptance is next. No Gaia
runtime is added. This resource milestone does not close the stellar programme.

### Minor-body pause and resumption

**Status:** Implemented partial program, paused; 50A.5D.1B.1 closed on
2026-10-05. Numbered asteroids and comets already have descriptor-based
points/tracks, object-centred charts, explicit offline resource collections,
and installed-CLI identity/acquisition preflight with verified cache reuse.
The Ceres/Apophis, Encke and second-comet validation evidence is retained;
comet discovery and observer-dependent sampled Horizons model photometry are
accepted. The [completed photometry revision](archive/milestone_history/50a_minor_bodies/comet_photometry_revision_50a5d1b1.md)
records the final 2,923-test gate and live 214-comet/cache/error acceptance.

| Remaining stage | Missing outcome and owner |
|---|---|
| Selection completion | Automatic asteroid names and unnumbered/provisional designations remain pending; reuse exact typed identity and resource preflight. Installed asteroid aliases with an explicit resource directory and exact comet names/designations already work. See the selection checkpoint below. |
| 50A.5D.3 | Natural moving-object text/JSON reports from already realized temporal results, including apparent angular rates and driver-convention warnings. Start with a bounded as-is report/temporal ownership audit; do not calculate ephemerides again or add another renderer. |
| 50A.5E.0–1 | Scientific/packaging audit and reproducible versioned distributable database: representation, identity, important-object/dwarf-planet inclusion policy, coverage, uncertainty, provenance, licensing and verification. No packaged database is implemented. |
| 50A.5E.2 | Explicit `wenu-database` policy and governed cache → provider → database fallback at the existing verified resource-collection boundary. This planned third source must not be described as a current runtime fallback. |
| 50A.5E.3 | Safe inspection, size/coverage reporting, dry-run pruning and explicitly confirmed cache flushing. This is future lifecycle work, not authority to remove resources now. |
| 50A.6 | Final public-interface/provenance/docs audit, scientific regression and human PNG/PDF/SVG acceptance across the admitted minor-body scope. The program remains open. |

Resume through `comet_discovery_and_reporting_audit_50a5d.md`, the current
architecture/reference/source map, `cli/chart.py`, the existing minor-body
identity/acquisition/resource owners, and temporal realization owners.
Photometry remains in `comet_photometry.py`; it does not own natural-object
reports or chart geometry. Physical coma/tail models, empirical activity and
visibility are not implied by the accepted symbolic drawing or sampled model
magnitudes.

### Minor-body selection completion (pending; 2026-10-05)

Fernando confirmed that ordinary chart selection by number or name belongs
to the remaining 50A completion scope. The source check at `2804afcf`
found the following as-is boundary, shared by point, track and explicitly
classed centre requests:

| Selection | Implemented behavior / pending gap |
|---|---|
| Numbered asteroid, e.g. `--asteroid 79989` | Automatic verified-cache reuse or provider acquisition is implemented for positive permanent numbers, subject to identity and epoch coverage. |
| Asteroid name, e.g. `--asteroid Ceres` | An exact installed name/alias works with an explicit `--minor-body-resource-directory`. Without that explicit directory, CLI preflight rejects nonnumeric asteroid selections before automatic cache lookup or provider identity resolution. Automatic name resolution/acquisition remains pending. |
| Unnumbered asteroid provisional designation | Automatic CLI selection currently rejects nonnumeric asteroid identifiers. Supporting an unnumbered body requires a bounded identity, descriptor, SPK-target/record, acquisition and coverage audit; it is not just removal of the CLI guard. |
| Comet designation/name, e.g. `10P`, `C/2006 P1`, `Tempel 2` | Exact designation or name resolution, class checking, cache reuse and acquisition are implemented. Partial, absent, ambiguous or fragment-ambiguous identities fail closed; a bare number such as `10` is not a comet designation. This existing capability must not be relisted as wholly unimplemented. |

The first future slice is a fresh bounded as-is audit for automatic asteroid
names, then separately reviewed implementation and acceptance. Audit
unnumbered/provisional asteroid support as a separate bounded extension and
complete both selection gaps before claiming general 50A chart selection or
closing 50A.6. No new numeric milestone identifier or runtime change is
admitted by this documentation amendment. Bayer/Flamsteed remains next in
the agreed project sequence.

Reuse `minor_body_identity.py` and its mandatory object-class constraint:
the generic resolver already has a tested asteroid-name route (Hygiea), but
ordinary CLI preflight does not admit it automatically. Keep request-level
selection, deduplication and coverage composition in `cli/chart.py`, exact
installed aliases in `minor_body_resources.py`, and verified immutable
acquisition/publication in `minor_body_acquisition.py`. Extend the existing
chart argument, centre, descriptor and resource seams only where the as-is
audit demonstrates a gap. All names/designations must converge on one exact
identity and one verified resource collection before ordinary chart
construction; do not introduce a second geometry or drawing pipeline.

Acceptance must cover point, track and centre requests across the supported
chart families, name/number equivalence, case/whitespace normalization,
absent/ambiguous/wrong-class selections, mixed asteroid/comet requests,
adequate and inadequate epoch coverage, offline/warm-cache behavior, explicit
resource authority and deliberate refresh. Preserve exact solution/target
binding, provenance and independent numerical fixtures. No fuzzy guessing,
silent orbit fallback or network access during realization/rendering is
implied. Existing evidence owners are `tests/test_minor_body_identity.py`
(`test_generic_boundary_can_resolve_an_asteroid_when_explicitly_requested`)
and `tests/test_minor_body_acquisition.py`
(`test_explicit_resource_directory_preserves_installed_name_selection` and
`test_automatic_name_lookup_remains_outside_numbered_asteroid_slice`).

### Satellite pause and resumption

**Status:** Implemented crossing foundation and direct-Sun radiometry;
50S.7D.3 Moonlight validation paused. The last accepted scientific checkpoint
is `da499b4d748d1f4ffa4a86076630dafc075d108d` (2026-09-23,
PR #195): exact resource identities, three sampled SPK/PCK coverage instants,
segment-centre metadata and final/predicted IERS statuses. It is not a lunar
geometry comparison or numerical Moonlight acceptance.

| Capability | Accepted boundary / remaining work |
|---|---|
| 50S.0–6G crossing foundation | Cached SatChecker sampled candidates; immutable OMM snapshots; Vallado-validated SGP4/TEME; explicit IERS-bound topocentric geometry; exhaustive circular-FoV oracle, conservative selection and multi-FoV coordination; exact reports/file protocol and shared-pipeline PNG/PDF/SVG tracks. Sampled candidates are not the exact local oracle. |
| Representative scale evidence | The accepted 256-record, ten-FoV equivalence matrix had zero crossings. It establishes bounded equality and conservative partition evidence, not demonstrated acceleration on non-empty large production workloads. |
| 50S.6H / 6I | Offline planning advisory and non-writing Paranal profile are accepted; ELT is reserved. Governed production refresh, automatic snapshot selection, rectangular detector footprints and one exposure-query workflow remain 50S.6I work. No operational observatory integration is implemented. |
| 50S.7B–C / 7D.1–2 | Direct-Sun illumination, geometric observer night, certified shadow transitions, nominal bolometric incident irradiance and digest-bound native-grid TSIS-1 spectral irradiance are accepted. Incident light is not observer brightness or detector signal. |
| 50S.7D.3 Phase B | LIME preflight and offline inspection are accepted. External resources and three coverage samples are recorded, but final Cartesian case rows, kernel load order/frame conventions, predicted-EOP uncertainty and the exact LIME signed-phase rule remain open. `moonlight` remains `not_evaluated`. |
| Later closure | After independent lunar geometry/model/resource/licensing validation: 50S.7D.4 direct-source closure, 50S.7E solar/lunar Earth-reflected fields, 50S.7F component bundling, 50S.8 calibrated brightness/uncertainty, 50S.9 detector contamination and 50S.10 statistics, scale evidence and final program acceptance. |

The first resumption slice is a separately reviewable source/resource/case
preflight under the [Phase B run protocol](satellite_moonlight_geometry_run_protocol_phase_b.md).
Rehash external LIME/package, coefficient, DE440 and IERS receipts on the Mac;
files were deliberately not vendored and their continued presence is not
assumed. The resource manifest digest is
`362787651c4438565c20b5e2f65a756f4be3d58c7b703e600a008c5a5c9cf24d`.
Do not infer coverage of final cases from three sample dates or combine the
historical LIME DE421 pool with the independent DE440 pool. Freeze the
scientific conventions and discriminating LEO/MEO/GEO/HEO cases before a
separately authorized comparison. No SPICE geometry comparison, LIME rerun,
new download or numerical Moonlight implementation is authorized by this
checkpoint. Existing ownership remains `satellites/illumination.py` for
geometry, `satellites/radiometry.py` for model-resource/native-band radiometry,
and `satellites/topocentric.py` for Earth-orientation/state transformations.
The [program log](satellite_program_log.md) preserves exact acceptances and
the [satellite guide](satellite_guide.md) preserves scientific definitions.

## 1. Purpose and authority

This roadmap preserves three future enhancements after the physical
polar-planisphere work:

1. rationalize astronomical coordinates and time-dependent position
   generation for planets, natural satellites, and artificial satellites;
2. make SVG a documented and verified vector-output product;
3. support time sequences in which celestial geometry, the observer horizon,
   and moving phenomena evolve on explicitly different timescales.

It records the active direction and sequencing after the closed v0.9
architecture. Each implementation stage requires a fresh as-is assessment and
its own small, testable milestone.

The coordinate decisions in `archive/audits/coordinate_transformation_audit_09a2afd.md`
remain authoritative scientific input. The longer-term astrometry sequence in
`archive/roadmap_history/polar_delivery_and_astrometry_roadmap.md` is consolidated here so that it no
longer depends on the urgent polar-delivery numbering.

## 2. Two independent development tracks

Post-v0.9 work has two complementary tracks.

### 2.1 Scientific-state architecture

This track owns reference frames, origins, epochs, observation instants, time
scales, physical position status, ephemeris/orbit providers, transformation,
and reusable celestial realization.

### 2.2 Product and output architecture

This track owns supported export formats and time-sequence products. It may
reuse the current canonical static-render pipeline but must not create a
second astronomical, projection, preparation, rendering, furniture, or
export pipeline.

SVG verification can proceed independently. Optimized horizon rotation and
moving-object sequences depend on the scientific-state contracts.

## 3. Preserved architectural boundaries

The canonical flow remains:

```text
catalogue, ephemeris, or orbit provider
    -> explicit astronomical state
    -> astronomical coordinate service
    -> typed spherical geometry in the product frame
    -> coordinate-neutral projection alignment
    -> projection
    -> projected geometry and chart preparation
    -> renderer
    -> furniture and export
```

Position generation and coordinate transformation are different operations.
A provider determines where an object is at an instant. The coordinate
service represents that state in an explicitly requested frame. Projection
alignment remains a coordinate-neutral spherical rotation and rendering
performs no astronomical calculation.

`CelestialSphere.draw_chart()` remains the canonical execution core until an
approved milestone deliberately evolves that public boundary.

## 4. Milestone 49A - Close v0.9 and refresh the as-is audit

- close the physical-planisphere acceptance and documentation;
- record the exact post-v0.9 implementation baseline;
- reconcile the 2026-08-16 coordinate audit with intervening changes;
- inventory every Astropy, Skyfield, handwritten, and chart-owned transform;
- inventory time parsing, UTC offsets, time scales, and observer construction;
- preserve current visual products as regression authorities.

This milestone changes documentation and tests only unless the audit exposes
a correctness defect that must be isolated separately.

## 5. Milestone 49B - Explicit astronomical-state vocabulary

### Milestone 49B.1 — Frozen coordinate vocabulary

**Status:** Accepted and merged in `d63c300`.

Add `CoordinateSpec`, `ObservationContext`, `PositionStatus`, the
structural `PositionProvider` protocol, and the `SphericalGeometry` union.
This milestone changes no numerical transformation, geometry constructor, or
chart output. Attaching coordinate identity to geometry remains 49B.2, and
adapting existing astronomical objects remains 49B.3.

Introduce immutable specifications for:

- reference frame and origin;
- coordinate epoch or equinox where applicable;
- observation instant and time scale where applicable;
- units and representation;
- geometric, astrometric, apparent, or topocentric status;
- provider/model identity and provenance;
- refraction, light-time, aberration, deflection, precession/nutation, and
  Earth-orientation policy when relevant.

Static celestial products resolve an explicit observer-independent product
frame. Local observing products resolve an explicit observer and AltAz
policy. Frame-less astronomical longitude/latitude must not cross the new
public boundary.

### Milestone 49B.2 — Typed spherical geometry

**Status:** Accepted and merged in `db946cc`.

Make `CoordinateSpec` a required keyword-only member of every
`SphericalPoints`, `SphericalCurves`, `SphericalPolygons`, and
`SphericalGrid` record. Every production constructor supplies an explicit
scientific identity; derived geometry preserves or deliberately replaces it,
and grids reject components whose identity differs from the grid identity.
This milestone changes no coordinate values or transformation equations.

### Milestone 49B.3 — Existing position providers

**Status:** Accepted and merged in `2492846`.

Adapt the existing stellar catalogue, non-stellar catalogue centres, and
open-cluster catalogue to the structural `PositionProvider` boundary. Providers
return native ICRS `SphericalPoints`; extended morphology and constructed
reference geometry remain separate. Static catalogues accept but do not use the
optional evaluation instant. No existing rendering path or coordinate
calculation changes.

## 6. Milestone 49C - One astronomical coordinate service

### Milestone 49C.1 — Central transformation service

**Status:** Accepted and merged in `5131500`.

Add one Astropy-backed service accepting every spherical geometry kind and
returning the same kind. Preserve semantic arrays, metadata, segmentation,
rings, grid component names, and closure topology. Support ICRS, Galactic,
barycentric mean ecliptic, and explicit observer-local AltAz transformations.
Do not migrate production callers in this milestone.

- add one Astropy-backed package service for supported astronomical frame
  transformations;
- transform points, curves, polygons, grids, and disconnected geometry while
  preserving identifiers, topology, labels, and provenance;
- keep specialized adapters for states such as TEME where their physical
  transformation path requires them;
- migrate reference grids, planes, poles, and ecliptic keypoints first;
- add spherical coincidence and round-trip tests;
- retire independent `radec_to_altaz()` mathematics after all callers move.

Projection classes must not import astronomical frames or infer them from
longitude/latitude argument names.

### Milestone 49C.2 — Migrate production transformations

**Status:** Accepted and merged in `f42f236`.

The accepted candidate routes reference points and grids, chart compatibility
conversions, deep-sky centres and morphology, constellation labels and
boundaries, observer-keyed caches, circumpolar boundaries, fixed-sky
orientation references, and regional celestial-north orientation through
`CoordinateService`.

Skyfield's Hipparcos apparent topocentric realization remains position-provider
work rather than being replaced by a second Astropy calculation. Constellation
lines reuse that single stellar realization. Native AltAz horizon geometry
also remains direct reference construction; only conversion of that geometry
to a celestial product frame passes through the service.

Acceptance evidence: the routine suite passed 1779 tests with 30 deselected in
26.99 seconds; the complete suite passed 1809 tests in 86.11 seconds; the
49H.3 fixed-sky/rotating-horizon reference frames were visually accepted by
Fernando on 2026-08-28.

### Milestone 49C.3 — Retire compatibility authorities

**Status:** Accepted and merged in `034bdd8`.

Retire `radec_to_altaz()`, remove the chart-owned compatibility wrappers, and
reduce `Observer` to explicit context construction without changing numerical
results or product appearance.

Acceptance evidence: the routine suite passed 1775 tests with 30 deselected in
24.59 seconds; the complete suite passed 1805 tests in 86.29 seconds; the
49H.3 fixed-sky/rotating-horizon reference frames were visually accepted by
Fernando on 2026-08-28.

### Milestone 49C.4 — Accept architecture 0.9.5

**Status:** Accepted and merged in `1a15076`.

The current as-is diagrams were reviewed and accepted. Scientific and topology
checks passed; the routine suite passed 1779 tests with 30 deselected in 27.31
seconds; and the complete suite passed 1809 tests in 84.99 seconds. Fernando
visually accepted both the corrected J2000 equinox intersections in the La
Ligua stereographic planisphere and the final fixed-sky/rotating-horizon
reference on 2026-08-28. Compatibility authorities are absent.

## 6.1 Immediate post-v0.9.5 public-interface follow-up

After the 49C.4 closure merge, audit every executable example and developer
tool before beginning new astronomical-object work:

- make the installed `wenu_chart` command the ordinary public route for every
  reproducible user example;
- reserve `tools/` for diagnostics, audits, benchmarks, migrations, and
  software acceptance rather than user workflows;
- move the physical planisphere demonstration into the examples area once
  `wenu_chart` can reproduce it completely;
- create one examples guide that identifies every supported example, its
  output, and the documented parameters users may adapt;
- expose coordinate system, frame, epoch/equinox, and relevant `of_date`
  policies through validated CLI and configuration values translated into
  `CoordinateSpec`;
- prohibit CLI, example, and tool code from constructing an independent
  astronomical transformation authority.

The public frame/equinox controls require their own small milestone and
scientific acceptance. They do not reopen the accepted internal 0.9.5
coordinate ownership.

### Public celestial reference policy — implemented and accepted

The first recommended slice is implemented and scientifically accepted. One
`CelestialReferencePolicy` carries a J2000, `of_date`, or explicit supported
equinox through ordinary request grids and the coupled celestial equator,
true ecliptic, and seasonal keypoints. The installed command exposes
`--reference-equinox`; schema-version-1 TOML exposes
`[coordinates.references].equinox`. J2000 remains the compatibility default.
Product-frame selection and provider position-epoch propagation remain out of
scope pending separate scientific milestones.

Acceptance used default J2000, explicit J2000.0, J2016.0, and `of_date`
regional SVGs. The default and explicit J2000 requests produced identical
normalized graphical records; J2016.0 and of-date moved the coupled reference
axes without moving apparent stellar directions. The first of-date render
found and closed the missing chart-view observer handoff. Final evidence was
1,786 routine tests passed with 30 deselected in 25.26 seconds and 1,816 full
tests passed in 86.71 seconds.

The completed as-is inventory, executable dispositions, public coordinate
vocabulary, validation constraints, and recommended implementation slices are
recorded in `archive/audits/public_interface_audit_v0.9.5.md`. Arbitrary supported equinoxes
are coordinate-representation requests; arbitrary position epochs remain
provider operations and must be rejected until the relevant provider can
propagate them physically.

## 7. Milestone 49D - Observer-independent celestial realization

### Milestone 49D.1 — Celestial-scene dependency and ownership audit

**Status:** Accepted and merged in `9e16ed2`.

The as-is inventory and minimum planet-enabling scene boundary are recorded in
`archive/milestone_history/49d_scene/celestial_scene_dependency_audit_49d1.md`. It distinguishes the reusable
loaded sphere from its currently observer-bound spherical realizations and
classifies content as celestial background, dynamic astronomical objects, or
observer-local geometry.

All enabled layers must converge in one explicit spherical product frame
before the existing projection and preparation path. A future planet enters
after provider evaluation and coordinate transformation as an ordinary
semantic sky layer; it does not enter through the renderer, furniture, command,
or a parallel scene graph. This audit changes no runtime behavior and
authorizes no caching.

49D.2 may add the smallest immutable layer-realization context and a controlled
test provider while preserving the current
`layer.spherical_geometry(observer, **geometry_options)` compatibility call.
A real ephemeris provider remains Milestone 49E and the first planet remains a
49I vertical slice. Completing every 49D migration is not a prerequisite for
that planet, but this bounded dependency contract prevents the provider from
being attached at the wrong architectural layer.

Fernando accepted the dependency classification, convergence point, insertion
point, and non-goals on 2026-08-29. Verification passed 39 documentation tests
in 2.78 seconds, 1,789 routine tests with 30 deselected in 26.62 seconds, and
all 1,819 tests in 84.41 seconds. No visual comparison was required because
49D.1 changes no production source or runtime output.

### Milestone 49D.2 — Minimal layer-realization context

**Status:** Accepted and merged in `85c7392`.

The exact contract and acceptance requirements are recorded in
`archive/milestone_history/49d_scene/layer_realization_context_49d2.md`. A frozen `LayerRealizationContext`
carries product coordinate identity, optional observation context, a pair…62729 tokens truncated…cale 1.7 as the leading quadratic comparison and
authorized a full-atlas visual review. Chart keys bracket the exact visible
magnitude range; facing reports keep the full reference scale with interval
counts, a dotted chart-range box and configurable inactive-row veil. Shared
legend packing now contains the enlarged disks and avoids row collisions.

The existing furniture hook, legend descriptors/workflow/rendering and atlas
presentation/report owners are extended. No new production or test module
is admitted. The coordinate-system guide was reviewed and remains current:
selection geometry, native coordinates and saved-sphere contracts are unchanged.
Focused owner/seam tests and five-region rendering cover the candidate; the
final accepted merge candidate still requires one complete suite. PR #227
remains unmerged pending whole-atlas visual acceptance.

### Stellar sizing and magnitude-key visual acceptance (2026-10-11)

Fernando visually accepted executable candidate
`ef7ca11c6bdf0688dc0a8e71cf8e691a1975e115` and explicitly requested
documentation, PR #227 merge and branch cleanup. This supersedes earlier
pending visual-acceptance and no-merge-authorisation wording for PR #227.
The accepted review profile is quadratic dmin 0.30 mm, a 0.04 mm per squared
magnitude difference, reference/selection magnitude 8 and diameter factor 1.7.
It is not a universal preset or an accepted print calibration.

The full saved-sphere run produced all 34 chart/report pairs. Their product
hashes, B4 dimensions and interval-count totals were verified. The facing
book contains 71 pages including its index and two sizing diagnostic pages.
The user guide now gives the complete direct CLI recipe. Shared sizing,
legend, canonical furniture/export and buffered PDF assembly remain the
implementation owners; coordinates and sphere contents are unchanged.

A final plugin-disabled full-suite attempt is required before merging.
The review environment lacks the DE440s ephemeris and has a known Matplotlib
3.10 font-inheritance test incompatibility; focused receipts do not replace
the final full-suite receipt. Merge and cleanup are authorised but must
retain an explicit record of any unresolved verification blocker.
Later appearance changes and object inventories/curation remain separate work.

### PR #227 final Mac verification and merge authorisation

On 2026-10-11 Fernando ran the exact documentation-complete candidate
`07b4a5d0954a74a2fe16cdfb34a577743bb33a1d` on the Mac with plugins
disabled and MPLBACKEND=Agg: all 3,438 tests passed in 694.21 seconds.
This resolves the earlier environment-specific full-suite blocker.
Whole-atlas visual acceptance and explicit merge/cleanup authorisation are
already recorded above. This documentation-only receipt changes no executable
content, scientific fixtures, dependencies, configuration, packaging or tests;
the passing full-suite receipt remains valid for its merge.
The next work remains separately scoped appearance refinement and object
inventories/curation; no new runtime milestone is started by closure.

### Candidate: geometry-driven atlas tiling (2026-10-11)

Fernando authorised paper size, orientation, angular chart field and overlap
as inputs, with band layout computed as output, and requested preservation
of the existing five-band input choices. The reference version-1 example is
unchanged and documented. Version-2 B4 requests omit algorithm/profile keys.
The existing geometry owner now searches symmetric, unequal-height bands
on a one-degree boundary grid plus exact polar boundaries. It fixes safe
polar caps first and minimizes total charts then interior band count by
dynamic programming. Continuous analytic halfspace validation certifies
coverage and overlap. This is a finite-family optimum, not a global arbitrary
placement optimum. Portrait 50-degree/.25-degree example yields 22 charts;
landscape yields 34. New JSON retains canonical inputs and derived layout.

Closest production and test owners are extended; no new modules or test files
are admitted. The coordinate guide was reviewed and remains current: ICRS,
stereographic geometry, no-observer design and final projection semantics
are unchanged. Focused geometry/CLI/documentation checks and index inspection
are required before Mac review. Final full-suite receipt and separate
acceptance/merge remain pending. No curation or moving-object work is begun.

### Geometry-driven atlas acceptance and closure (2026-10-11)

Fernando visually accepted the complete 22-chart portrait B4 atlas with
selection limit 7.5, quadratic sizing reference 8, dmin 0.30 mm, coefficient
0.04 mm per squared magnitude difference and diameter multiplier 1.7.
The four-worker saved-sphere run was the accepted comparison. He explicitly
authorised PR #228 merge and branch cleanup. Exact executable candidate
`904160eacd2854f6b530b97107c20f912c69f009` passed all 3,446 plugin-disabled
Mac tests with MPLBACKEND=Agg in 751.75 seconds. This supersedes pending
acceptance/verification wording above. This receipt changes documentation
only, so that full-suite result remains valid for merge.

The next separately bounded appearance change is equatorial grid labels at
the chart frame, with at least 50 percent more coordinate-label border space
and a slightly smaller physical sky rectangle while preserving angular
field and centre. Assess the existing grid, frame, layout and export owners
before implementation. Keep it outside the accepted geometry candidate.


### Atlas coordinate-grid candidate (2026-10-12)

Fernando requested this bounded milestone after confirming clean synchronized
Mac main at 28e52bae5f19e41f1f38b8c84680bb1e95437ce0: 2h RA / 30-degree Dec
interior lines; whole-hour edge labels; smaller 20m/40m labels; all 10m RA ticks;
10-degree Dec ticks and labels; inward tick slopes following projected curves.
Keep coordinate text clearly legible and the nominal frame minimum 50% wider,
shrinking only physical sky size while preserving angular coverage.

As-is: native preparation registered only an equator under equatorial_grid;
ordinary exterior anchors selected one crossing, had no edge tick contract,
and atlas axes occupied the complete useful page. The candidate extends existing
scientific/reference, boundary, renderer and shared chart request owners.
Font-measured outward lanes resolve polar overlaps without moving coordinate
marks. The exposed grid_lines_visible switch permits later lines-off review.
Actual sky area now governs stellar area budgets. An exact-antipode regression
found during polar review is corrected in the shared stereographic owner,
rather than being hidden by an atlas-specific projection workaround.

Test admission extends existing coordinate-grid, boundary-anchor, renderer,
projection and atlas CLI files. New fault models are separate major/tick
cadences, immutable native state, all-crossing deduplication/closure, physical
DPI-invariant slopes, singularity breaks, outward label collision clearance,
paper containment and unchanged viewports. Existing lower-level tests retain
ownership; no module, dependency, source acquisition or test file is added.
The coordinate-system guide and current ownership diagrams were reviewed;
scientific coordinate meaning remains current. Mac scientific/print acceptance,
full final-candidate suite before merge, merge and cleanup remain separate.

The corrected command boundary routes the atlas CLI through `wenu_chart
atlas-sheet`, with explicit prepared native input and one sky per worker.
Shared request generation now owns sheet execution; regional CLI/TOML admits
the same mark policy and physical frame helpers. Existing chart/configuration
tests additionally protect command admission, source reuse, native-versus-observer
coordinate meaning, no-clobber output, spawn dispatch and regional parity.


Fernando revised the candidate to 1h RA / 10-degree Dec lines, superscript h/m
units, Dec labels normal to their projected curves, and darker interior lines.
The scientific viewport, 10m tick cadence and 20m/40m smaller labels are retained.
Existing atlas tests now execute the actual 22-chart portrait design at sheets
1, 5, 8, 10, 11 and 22. Index review exports PNG, SVG and PDF together.

Fernando clarified Dec text should be parallel to the curve at the boundary,
requested default 2h RA lines with configurable spacing, optional 20m/40m text
hidden by default, lighter lines and paler blue MW/MCs. Uploaded chart 10 shows
generic Messier dotted outlines over dedicated galaxies; canonical category
ownership now suppresses those duplicate generic outlines while preserving
source data and restoring generic presentation when a dedicated layer is off.
Index review explicitly opens/checks independent PNG/SVG/PDF files.

After 612 Mac focused tests passed, real chart rendering exposed an inherited
Galaxies._geometry_table keyword mismatch. The correction preserves subclass
method admission and extends an end-to-end batch test with synthetic galaxies
and co-located Messier labels. Fernando clarified Messier is a heterogeneous
designation catalogue; atlas sheets now draw its labels only. Requested legend
text/title is 12 points, configurable independently of report headings.

Atlas review candidate: independently sized 40-degree polar primary caps with
55-degree nonpolar central height produce 32 B4 portrait charts at the existing
margins and 0.25-degree overlap. Existing geometry and serialization owners are
extended; the chart-presentation Messier fontsize becomes configurable at 7
points. Chart count and analytic coverage do not establish label readability;
Mac index/print review and final-candidate full tests remain pending. The
coordinate-system guide was reviewed and remains current: frames, epochs,
provenance and scientific transformations are unchanged.

Atlas visual candidate: 1.8-times DSO diameters, configurable yellow filled
cluster circles (internal cross for globulars), 80-percent Dec labels, per-chart
visible-star count in report legends, and a final cumulative catalogue-count
appendix. The user selected log N versus magnitude; zero/negative magnitudes
are valid on that linear x-axis. Counts use actual source photometry, unique HIP
identifiers and the atlas cutoff, not duplicated chart appearances.
After visual acceptance, final-candidate full verification and separately
requested merge/cleanup, the next work is category-by-category cluster and SNR
curation: inspect histograms of physical catalogue characteristics one at a time
and overlay the corresponding small-telescope catalogue selections. Specific
comparison catalogues and scientific characteristic definitions will be resolved
within that later curation step. No such curation or merge is claimed complete.


### Binding common-scale atlas implementation candidate (2026-10-12)

Fernando accepted the instruction checkpoint b831b69a and authorised runtime
implementation. The 36-chart revision has identical angular fields, fixed
physical sky rectangles and equal central scale, with analytic coverage and
overlap revalidated. Font-derived fixed bands replace independent sheet
fitting. Nonpolar/polar RA cadence is 1h/2h; edge collisions use RA priority
horizontally and Dec priority vertically, and polar Dec labels are interior.

Portrait/landscape index composition and standalone publication PNG/SVG/PDF,
the index-following blank page and report-left/chart-right display sequence,
and a reversed actual-count magnitude axis are implemented as a candidate.
Existing owners and tests are extended. The coordinate-system guide was
reviewed and remains current; no scientific catalogue curation is begun.
Focused checks and representative render inspection precede Mac native
equivalence and visual acceptance. Final full tests before merge and explicit
merge/cleanup remain separate.


### Atlas chart/report frame correction (2026-10-13)

Fernando reported the smaller chart frame, unused coordinate-band space and
insufficient clearance for slanted RA labels in the generated full atlas.
The bounded correction adds explicit sky aspect to the existing geometry owner,
revalidates a versioned 36-chart revision, fits the fixed bands to the full
report-frame dimensions, and corrects edge-normal label clearance. Historical
designs remain unchanged. Mac catalogue-backed and visual acceptance remain
required; this correction does not authorize PR merge, cleanup or curation.


### Open-cluster observing-list comparison (2026-10-13)

After atlas PR 229 was merged and cleaned up at `96e6d4fb`, Fernando requested
Caldwell ingestion and comparison of Dias clusters with Caldwell and Messier.
The bounded milestone adds the complete source-traced 109-entry Caldwell
resource and an offline identity crosswalk using existing catalogue owners.
It does not choose an observability cutoff, curate physical duplicates, alter
atlas chart density or automatically draw Caldwell symbols. Initial matches
are 27 Messier clusters and 29 Dias clusters for 28 Caldwell entries. C37 and
C50 retain competing alias rows as review cases. Histograms and decisions
about retained telescope targets remain subsequent curation work.

Provider-policy preflight checked on 2026-10-13: OpenNGC's pinned README and
CC BY-SA 4.0 licence establish attribution/redistribution conditions. GitHub
[API best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)
require conservative serial access and stopping on throttling. The maintenance
tool uses three serial pinned raw-file GETs, with no polling, concurrency or
automatic retries, or a fully cached source directory with exact digests.
Chart runtime and comparison perform no network access. Membership facts were
checked against the Astronomical League's published list; no guide prose or
images are redistributed. The parameter snapshot carries OpenNGC attribution
and its licence. Mac focused/full-suite acceptance and merge remain separate.


### Open-cluster parameter-plane review (2026-10-13)

Fernando requested IR/embedded exclusions as marks rather than source-row
deletion, a two-dimensional Caldwell/Messier comparison, scripts under tools
reading data and writing output, selectable axes, E(B-V) cuts and optional
filtered-catalogue creation. The bounded implementation preserves all Dias
rows, derives IR/E marks, supports explicit plot/export selection and adds
source-traced V photometry without inferring absent values. Atlas filtering is
opt-in through the existing layer and new version-5 style. No final reddening,
brightness, richness or diameter threshold has been accepted. Physical-duplicate
curation and globular-cluster comparison remain subsequent work.

The photometry maintenance entry reuses the earlier OpenNGC pinned-file policy:
two serial raw-file GETs (or digest-verified cache), no concurrency, polling or
automatic retries. OpenNGC v20260501/CC BY-SA 4.0 attribution and the separately
packaged licence are retained. All plotting/selection commands are offline.



### Hunt & Reffert member curation tool boundary (2026-10-13)

The existing tools/compare_open_clusters.py selects Dias, Hunt & Reffert 2024,
or its separately prepared converted-V5<11 subset. No-argument invocation
prints catalogue/column help without loading data or writing outputs.
tools/hunt_reffert_catalogue.py owns offline CDS parsing, observed Gaia-to-BVR
relations, probability/aperture member statistics and the comparison adapter;
tools/query_hunt_reffert2024.py owns explicit serial raw acquisition or verified
cache preparation. These are developer-tool responsibilities, not production
sky layers, coordinate services or alternate chart renderers. Existing comparison
and scatter/export functions remain shared. The installed Dias chart catalogue
and atlas snapshot defaults remain unchanged. Full source-backed preparation
and its counts await Mac acquisition; partial data never claim full membership.

Observed Johnson V/B and Cousins R follow official Gaia DR3 polynomial domains.
V5 ranks members in converted V, with strict <11 selection; membership defaults
to probability >=0.5 within the estimated tidal radius. Full rows, source IDs,
missing diagnostics, source hashes and separate candidate exports are retained.
Hunt diameter is 2r50, E(B-V) is explicitly AV50/3.1 under assumed R_V=3.1,
and member sums are incomplete observed estimates. Catalogue ICRS centres keep
J2016.0 provenance; this offline curation adds no stellar-position provider,
epoch propagation or chart-frame reinterpretation. Source attribution and
provider-policy preflight are recorded in the living user curation guide.

### Complete Hunt resource receipt and identifier audit (2026-10-13)

Fernando published the full/curated Gaia-member resources at `7ff3a403`, after
complete source acquisition, hash validation, 7,167 aggregate / 1,291,929 member
count checks and exact full-to-curated row comparison. The 431 type-o V5<11
candidates are an initial member-brightness selection, not final amateur curation.
The source remains offline and digest-bound; no new download is required.

The comparison identifier owner normalizes published underscore separators and
keeps primary identities ahead of source aliases. The actual-source regression
checks all 29 Caldwell components and 27 Messier matches, plus the retained
Melotte_25/CWNU_1242 alias distinction. The IR/E and E(B-V)<=3 review sample
contains 5,485 open clusters, all with diameter/V5; adding V5<11 retains 428,
including 22 Caldwell components and 23 Messier clusters. M11, M26, M29 and
M103 fail the V5 threshold and require scientific interpretation, not silent
replacement. Source data/photometry and chart defaults are unchanged by this
identifier correction. The curation guide records the exact receipt and
selection meanings; Mac focused and later final full-suite acceptance remain
separate from source publication.

### Tenth-member open-cluster cutoff (2026-10-13)

The existing comparison adapter accepts optional strict --max-v10 in addition
to --max-v5. Both supplied limits must pass; missing rank magnitudes receive
explicit missing_V5/missing_V10 reasons. No-argument help advertises the option,
and Dias rejects these member-specific cuts. The same packaged source/member
policy, BVR conversion, identifier owner, plot/export owner and IR/E/reddening
selection are reused without acquisition or resource changes. The full Hunt
source with V10<11, IR/E exclusions and E(B-V)<=3 retains 229 candidates,
including 20 Caldwell components and 21 Messier clusters. The named
hunt-curated source remains the previously prepared V5 subset; independent
V10 comparisons use hunt-reffert2024 and separate versioned filtered exports.
The coordinate guide was reviewed and remains current: rank-10 photometry
already exists and this selection option changes no coordinate meaning,
provider, frame, epoch, position, sky layer or chart pipeline.


### Source-preserving Wenu open-cluster union tool (2026-10-13)

Fernando requested software delivery before catalogue curation. The new
`tools/merge_open_clusters.py` owns offline candidate compilation from complete
supplied Dias and Hunt tables. It is a developer tool, not a production sky
layer, coordinate service or alternate rendering pipeline. Identifier
normalization and observing-reference resolution remain shared with
`tools/compare_open_clusters.py`; its existing comparison behavior is preserved.
No-argument invocation prints help and writes nothing. No real combined
database is generated or adopted during this software milestone.

The candidate schema orders wenu_id, RA, Dec, dias_id and all dias_* parameters,
hunt_id and all hunt_* parameters, then Messier_id, Caldwell_id, NGC_id and
other identifiers. Every supplied source row is represented once, retaining
all types, classifications, parameters, source positions, units and masks.
Primary identities precede reciprocal unique published aliases; competing
claims remain separate with a review ledger. No positional guess or same-source
collapse creates identities. C14 still annotates two distinct components.
An explicit persistent WOC identity registry preserves IDs during updates and
rejects proposed merges/splits of published identities for review.

Displayed RA/Dec use Hunt when available, otherwise Dias, without averaging,
epoch propagation or reinterpretation. Both original source positions and
metadata are retained. Hunt keeps J2016.0 provenance; an unknown Dias position
epoch is not inferred from its J2000 frame/equinox description. Physical
parameters are never silently averaged/coalesced. The tool supplies candidate
ECSV/CSV, source/reference crosswalks, ID registry and a completion receipt with
source/product hashes. Existing products are refused; the receipt is written
last. The logical database is wenu_open_clusters, but acceptance/filtering,
clean-database generation commands and chart adoption belong to later curation.

The defaults retain all 1,931 packaged Dias and 7,167 full Hunt rows. Dias's
existing normalization had already excluded 235 of the original 2,166 records;
an alternate normalized Dias input can supply a fuller population. This tool
cannot recover earlier provider exclusions and explicitly records that scope.
The owning user guide documents schema, help, policies and outputs. Synthetic
regressions in the existing open-cluster test owner cover row conservation,
ambiguity, observing components, source immutability, units/masks, stable IDs,
registry conflicts, digest-bound outputs, help and overwrite refusal.
Focused open-cluster/package validation passes 23 tests; exact-head Mac
historical-documentation acceptance and the final full suite remain separate.


### Published-centre positional audit for cluster union (2026-10-13)

The existing developer union tool now audits every Dias/Hunt cross-source pair
using spherical angular separation of supplied centres, without propagation.
The strict test is separation < BOTH catalogue radii; each radius is half the
selected angular diameter. Defaults use apparent_diameter_arcmin (Hunt 2r50);
explicit --dias-diameter-column/--hunt-diameter-column options record alternative
boundaries. Angular units are converted; unitless sizes mean arcminutes and
unitless coordinates mean degrees. Invalid/missing centres or nonpositive,
masked/nonfinite radii are unassessable. Missing columns/incompatible units fail
before outputs. This adds no identity merge, position provider or chart change.

The printed/receipt audit counts established identity pairs as pass/fail/unknown
and other passing pairs as both_unmatched or matched_elsewhere. Pair and distinct
source-object counts are separate, with deduplicated combined counts. The new
_positions.csv ledger retains both original centres, separation, radii, source
and Wenu IDs, category/status for all identifier pairs and other passing pairs.
It is product-hashed with the existing completion receipt. Existing source
catalogues remain untouched; real compilation remains a later curation step.
No-argument help covers parameters, radius meanings, strict criterion, outputs
and usage. The existing owning tests check spherical wrap/polar geometry,
unequal radii, exact boundary, missing values, units, neighbour multiplicity,
matched-elsewhere classification and CLI receipts. The focused open-cluster /
package gate passes 25 tests; exact-head Mac/documentation acceptance and the
final full suite remain pending. The living curation guide owns user details.


### Amateur observing-list source acquisition v1 (2026-10-13)

Fernando requested source acquisition before selecting public/beginner targets.
The new data-directory registry
`src/wenu/data/observing_lists/observing_sources_v1.json` inventories
13 distinct source lists/catalogues plus the generic Best of the NGC alias.
Eighteen checked source-table products are delivered separately in the versioned
wenu_observing_catalogues_v1.zip, with publisher/edition URLs, retrieval dates,
source and derivative SHA-256, byte counts and observed membership counts.
The resource README and living user curation guide own this acquisition record.
This is provenance/guide work, not a new loader, sky layer, rendering pipeline,
physical identity union or adopted interesting-target selection. Existing
Messier/Caldwell parameter resources and all software remain unchanged.

Count distinctions are explicit: AL Messier membership 110 vs packaged HEASARC
109; SAC named 110 vs 111 source rows; RASC 110 observing numbers vs 112 rows;
AL open clusters 125+89 downloaded rows vs advertised 90 southern additions;
globulars 190 with a 50-object requirement; double stars now 200 with a
100-object requirement; multiple stars now 115. Southern Herschel/planetary
supplements and northern PN alternates are acquired separately. Barnard's
349-row public ASU export and notes replace rejected HTTP-200 HTML FTP
responses; original coordinate-system metadata remains source authority.
Abell's 86-entry original scanned Table 2 is acquired, with parent-paper hash
and extraction provenance, but OCR is not accepted numeric coordinates.
No source frame/epoch, component separation or position angle is silently
reinterpreted or propagated. Raw list documents stay in the separate acquisition
archive; no public redistribution licence is inferred. Membership normalization,
physical classifications/crosswalks, visual selection and chart integration
remain later curation milestones. Each archived product was hash/length checked;
ZIP contents and CRC were verified. Exact-head Mac documentation acceptance and
the final software full suite remain separate before merge.


### Cluster-list CSV first pass and explicit memberships (2026-10-13)

Fernando requested CSV conversion before observing memberships, then narrowed
this milestone to star clusters. tools/convert_observing_catalogues.py owns
first-pass offline conversion of nine acquired cluster-containing list files
(Messier/Caldwell/Herschel400/II/RASC/SAC/ALOC/ALGC and southern Herschel).
Mixed lists retain every row. Non-cluster programme and Abell/CDS work is
deferred. tools/observing_list_membership.py owns source verification,
source-format decoding, conservative name normalization and membership review.
These are developer maintenance responsibilities, not new production modules,
resource loaders, position providers or parallel chart pipelines.

The real requested CSV first pass produces 10 source grids/tables plus a
1,796-record membership index and last-written hash-bound conversion receipt.
Excel sheet separation, blank rows, titles/repeated headers and source cell
positions are preserved. PDF identity/coordinate fields retain original row
text and unparsed tails. CSV parameters remain source strings; no scientific
homogenization or source replacement is implied. pypdf is an existing Wenu
dependency; standard-library XLSX parsing needs no Excel package. Only legacy
southern XLS conversion uses optional maintenance xlrd>=2,<3; the merge compiler
consumes verified CSVs and needs no Excel reader. No global dependency changed.

The union tool defaults to observing_lists/csv_v1 and adds in_messier,
in_caldwell, in_herschel400, in_herschel2, in_rasc_finest_ngc, in_sac_best_ngc,
in_best_ngc (same SAC alias), in_al_open_clusters, in_al_globular_clusters and
in_herschel400_south. True is resolved explicit ID membership; false is no
resolved identifier; competing claims are masked and retained in _observing.csv.
Primary names precede aliases; explicit RASC/Caldwell compounds keep distinct
physical rows. Historical AL M24/M45 approximate NGC associations do not
replace the existing observing crosswalk. Extragalactic GC names retain host
scope; questioned/mislabeled narrative names are not adopted as aliases.
No positional coincidence creates membership or alters source union/stable IDs.

Missing/unverified CSV receipts fail before writing. --observing-directory
selects a verified conversion; --without-observing-lists explicitly emits masked
flags. Both tools print parameter/usage help without arguments. Source and
conversion hashes/counts are recorded. Full source rows/types and every
Dias/Hunt parameter, coordinate and positional-audit meaning remain unchanged.
The real CSV conversion is explicitly authorized; no real combined catalogue
is generated. The existing owning tests cover flags, alias precedence/conflicts,
compound memberships, skipped masks, stored XLSX cell/blank-row fidelity,
conversion hashes/counts, help and overwrite refusal. Twenty-eight focused
open-cluster/package cases pass in 8.86 s; all three tools compile. Actual nine
source files yield 11 verified CSVs; index1796, raw Excel row locations and
RASC explicit companions/negative alias case were checked. Mac exact-head
focused/documentation acceptance and final full-suite merge acceptance remain
separate. The user guide/resource README own the workflow details.


## Observing-list additions and first-membership comparison checkpoint

Fernando requested the six remaining observing lists, source provenance and
an observing guide, including urban southern coverage and the history of the
Herschel programmes. `observing_additions_v1.json` records seven publisher
source snapshots independently of `observing_sources_v1.json`; the existing
source and CSV receipts remain valid. `tools/observing_list_additions.py` owns
the supplementary HTML/ZIP/XLSX/PDF decoding and verified CSV reader.
`tools/convert_observing_catalogues.py --additions` selects this separate
conversion. `tools/merge_open_clusters.py` auto-loads installed supplementary
CSVs, supports `--observing-additions-directory`, and masks unavailable lists.
Exact observing references may annotate compound targets; stars near clusters
and asterism narrative references never establish physical cluster identity.
Raw list targets stay separate from the Dias–Hunt cluster union.

`tools/plot_merged_open_clusters.py` is an offline curation diagnostic for
published source radii versus Hunt-derived V10. First true list membership
selects one configurable symbol, with Messier/Caldwell first by default.
Matched Dias points explicitly share Hunt V10; Dias-only objects remain in a
missing-V10 panel. Filled/hollow symbols distinguish source radii. Point and
summary ledgers retain filters, unavailable flags and exclusions. No-argument
help writes nothing. `docs/user_guide/curation.md` explains list objectives,
verified counts, urban southern limits, condition-specific observing demands,
and modern Herschel programme selection. Existing owning tests cover source
masking, exact identities, compound references, first-list precedence, shared
V10, strict cuts and supplementary digest rejection. No new public sky layer,
canonical pipeline change, curated database adoption or software merge occurs.


## Member-count comparison axis checkpoint

Fernando selected the previous two radius–V10 views plus a member-count–V10
view, with source data read from Wenu's data directory and products written
under output. The existing `tools/plot_merged_open_clusters.py` now accepts
`--x radius|members`. Radius retains the half-diameter default; members uses
the separate published `dias_member_count` and `hunt_member_count` directly,
without halving counts or substituting photometrically accepted members.
Only the selected axis columns are required; invalid/nonpositive x values
are excluded and logged for the logarithmic x axis. The point ledger retains
radius, member_count and x_value; summary records axis/source columns.
V10 sharing for matched Dias rows, missing-V10 panel, source-specific reddening,
strict V10 cuts, first-list priority, masks and plot exports retain their scope.
The owning guide documents both axes and running from tools with ../src and
../output paths. Existing owning tests exercise unequal source counts, missing
radius independence, masked/zero counts, strict cuts, CLI exports and help.
No catalogue data, physical identity policy, public sky layer, chart default,
canonical pipeline or dependency changes. Software delivery remains separate
from final catalogue curation and branch merge.


## Explicit open-cluster curation v0.1 checkpoint

Fernando requested the filtering script and a v0.1 CSV, confirming brighter
V10<12.5 and V10 below 17.5-(12.5/3)*log10(radius_arcmin), E(B-V)<=3 for
additional candidates, and intersection across both available source points.
The five mandatory observing lists bypass all numeric cuts; unresolved list
claims are retained and flagged for review. The former plot's V10<11 cut is
not inherited. `tools/curate_open_clusters.py` owns this offline selection from
the complete source-preserving union. It reuses the existing spherical audit
and numeric-field reader; primary/alias pairs remain intact. Reciprocal unique
unmatched pairs inside both published radii may be combined provisionally,
with original ID lineage, source parameters and unresolved alias flags retained.
Competing positions and objects matched elsewhere remain review evidence;
audit-only mode makes no positional combinations.

CSV/ECSV, all-row selection ledger, pairing ledger and digest-bound completion
summary preserve source origin, mandatory reasons, thresholds, per-source
numeric decisions and positional provenance. Previous plotting commands read
the ECSV; full-selection checks omit global cuts to show mandatory exceptions.
The owning guide documents parameters, strict boundaries, source-policy choices,
ID redirects and curation commands. The verified real run selects 583 rows,
including 142 resolved mandatory, 27 unresolved mandatory claims and 414 further
numeric-only rows; seven positional pairs are provisional before selection and
one remains selected. Existing owning tests cover log-boundary endpoints,
strict cuts, mandatory overrides, missing fields, all/any source policies,
one-to-one positional pairing, ambiguity, ID conservation, source preservation,
help and admission failures. No curated data is installed or committed as a
chart resource, and no software merge, pipeline or dependency change occurs.


## Curated open-cluster atlas catalogue (v0.2)

`tools/prepare_open_cluster_catalogue.py` publishes a new version from an
existing selected union. It keeps Hunt type `o` and Dias-only rows, excludes
single-source rows without another catalogue designation or resolved list
membership, and retains masked claims for review. Modern discovery catalogues
including OC count; HSC alone does not corroborate a Hunt entry. Source rows,
IDs, coordinates, masks, selection criteria and provisional pairing flags are
preserved. Every exclusion is recorded; proximity never causes deletion.

The installation boundary copies immutable versioned ECSV bytes into a chosen
catalogue directory and optionally atomically selects them using the relative
`open_star_clusters.ecsv` symlink. Existing versions and regular selector files
are refused. This is separate from software installation and package resources.
`OpenClusters.normalize_catalogue` adapts the union at the existing layer
boundary: Hunt-preferred coordinates/diameters and source member counts, stable
Wenu geometry IDs and readable labels. V10 is never integrated photometry.

`wenu_create_atlas --open-cluster-catalogue PATH` replaces only the open-cluster
source in `CelestialSphereLoadProfile`. The selector resolves once before
preparation; the existing native snapshot hashes and serializes the selected
catalogue for all workers. An override with `--from-sky` is rejected. Other
layers, atlas geometry, presentation and stellar settings are unchanged.
Tests extend `test_open_clusters.py` and `test_atlas_cli.py` at the normalization,
installation, profile-propagation and saved-sky boundaries. No atlas software
merge or chart adoption is implied by producing a candidate.


## Open-cluster symbols at the atlas central scale

Atlas open-cluster circles now use the catalogue angular diameter at the
central chart scale, bounded below by the existing styled symbol diameter.
Hunt diameter is 2*r50; Dias-only entries use the published Dias diameter.
Missing, masked, nonfinite or nonpositive diameters retain the current minimum.
Colours, outlines, labels, catalogue selection and all other layers are unchanged.

The atlas request owns the angular-to-projection conversion (projection radius
multiplied by pi/21600 per arcminute). The generic renderer converts supplied
point diameters to physical scatter areas using the actual equal-aspect axes
width and viewport width. It accepts a caller-specified metadata key and unit
scale; it does not choose catalogues or know source definitions. The helper in
rendering/preparation.py preserves the current area floor. Scatter area is the
square of the normalized circle diameter in points, independent of export DPI.
No local projection-distortion correction is applied away from the centre.

AtlasChartPresentation.open_cluster_angular_sizes defaults to true. The atlas
CLI exposes --open-cluster-size angular|fixed; fixed restores previous sizes.
Existing saved skies can be reused because catalogue metadata is unchanged.
Tests extend the existing Matplotlib renderer and atlas CLI owners, checking
physical dimensions at two DPIs, equal central/edge sizing, missing-value
floors, rendered chart scale, fixed mode and presentation admission.


## Standard catalogue maintenance layout

Scientific sources remain under src/wenu/data/catalogs. Observing selections
now live in src/wenu/data/observing_lists, with one named directory per list,
original files, CSVs, README and provenance. Barnard/Abell physical catalogues
belong to scientific sources. Trials and diagnostic products belong to output;
accepted bundles and the relative active selector belong to
src/wenu/data/curated_catalogs/open_clusters.

catalogue_data_layout.py owns offline path resolution, collision-safe copying,
per-list provenance and conversion publication. migrate_catalogue_data.py
verifies historical source/conversion receipts, moves legacy flat folders only
after verified copies, and records migration evidence. Registry/receipt bytes,
membership records, source identifiers and scientific selection rules remain
unchanged. Legacy flat inputs remain readable; new publication is per list.
The shared resolver is used by both source-specific observing converters/loaders.

prepare_open_cluster_catalogue.py separates trial depuration from accepted
--promote-catalogue publication. Promotion checks the complete summary-bound
bundle, preserves trial outputs, copies accepted data/review evidence and
atomically changes only the selector. The plot tool defaults to that accepted
selector while accepting explicit trial inputs. Merger defaults use the new
observing root. Working observing/curated trees are excluded from automatic
package discovery; installed software reads explicit catalogue paths. The
existing atlas pipeline, saved-sky format, symbol sizing and source selection
are unchanged. The curation guide documents each tool and the complete workflow.

## Planetary-nebula comparison milestone (2026-10-14)

Fernando authorized an offline overlay of current best observing lists,
Messier/Caldwell and the AL planetary lists over the large PN catalogue.
The Mac was clean on synchronized main at
`8f91504aa399635c80f46159d3c6b8e20d57f737`.
As-is: 1,143 Strasbourg-ESO objects have optical diameters and H-beta fluxes,
without a visual-observability cut. Broad list conversions exist; the three
PN workbooks remain original Excel sources with verified per-list provenance.
There was no dedicated PN comparison tool.

The bounded candidate is `tools/compare_planetary_nebulae.py`, with all-row
annotation, explicit identities, disjoint first-list symbols, flux and
surface-proxy views, missing/diameter-limit panels and digest-bound review
products. Source catalogues and chart defaults remain unchanged.
The reference run resolves 178 distinct objects; Sh 2-216 and four southern
identity conflicts remain review cases. No final visibility threshold,
classification revision, curated catalogue promotion or atlas adoption is
authorized by generating these plots.

The coordinate-system guide was reviewed and updated for diagnostic
provenance/quantity interpretation. Existing planetary-nebula tests are the
closest stable owner and are extended for matching, signed namespaces,
source checksums, limits, surface-area units and CLI receipt/no-clobber seams.
No new test or production-module family is introduced. Focused verification
precedes Mac scientific review; full-suite verification remains the final
candidate merge gate under the accepted test policy.

Fernando authorized candidate selection on 2026-10-14 after the comparison:
all resolved reference-list members OR observed log H-beta > -12. The first
selection has 319 rows, including 141 additional flux-only objects. Public
interest is separate: only the highest surface brightness warrants review,
and even M57 is challenging for newcomers. No object is automatically approved
for the public. Optional selected CSV/ECSV and a ranked, quality-labelled review
table extend the same offline owner. No public numerical cutoff or atlas
installation has been accepted. The Mac comparison gate passed 12 tests after
installation of the existing optional xlrd dependency; the expanded candidate
requires its own focused verification and final merge gate.

Fernando requested recreating the atlas with the curated PN v1 on 2026-10-14,
explicitly requiring the same open-cluster mechanism. At clean synchronized
Mac head `7c5287ef3971e45d5e938e46971566cc1dfd0b4c`, the prior full suite passed
3,581 tests. That receipt covers the comparison/selection, not this new runtime
connection. The as-is load profile already supports a PN filename; only the
atlas CLI/publication mapping and separate verified bundle/selector promotion
were missing. The candidate extends those existing owners, preserves curation
metadata in the PN layer, and adds no module, default selection, coordinate
transform or pipeline. Tests extend the real atlas-command preparation seam
for simultaneous selectors and saved-sky rejection, and the existing PN export
test for immutable promotion, checksums, regular-selector refusal, normalization
and native realization. New runtime content needs focused verification and a
final candidate full-suite gate; previous comparison tests cannot substitute.

## PN contrast and selection appendices (2026-10-14)

Fernando requested larger, higher-contrast PN symbols and atlas pages with
selection plots stored beside curated catalogues. The bounded candidate extends
existing presentation, diagnostic, immutable-publication and PDF owners.
PN diameters increase 25%, with dark green and heavier outlines. PN plots retain
the full source population; cluster plots describe the accepted population and
stored selection/depuration rules. Catalogue hashes bind all criteria pages.
Fernando accepted the atlas appearance and selection appendices on 2026-10-14
at `12be5079643bd423be69468a5f3d16bec41039b9`, and explicitly requested
documentation, merge and cleanup. The Mac focused gate passed 21 tests in
35.54 seconds and both catalogue-bound criteria bundles were generated.
This acceptance does not approve any PN for public interest. Merge and branch
cleanup are authorized. The final-candidate Mac full suite at
`6f48b9d073529ef8dcb798eee1ad510acf572034` passed all 3,581 tests in
1,085.62 seconds (18:05) on 2026-10-14. This supersedes the pending-gate status.
The earlier 3,581-test receipt at 7c5287ef does not cover this runtime content.
This acceptance update changes documentation only.

## Next nebular catalogue: EN-MS / NE-EM

Fernando chose the future catalogue name **massive-star ejecta nebulae**,
**EN-MS**, or **nebulosas de eyeccion de estrellas masivas**, **NE-EM**, on
2026-10-14. Keep this physical class separate from planetary nebulae, including
PNe with [WR] central stars. Record massive-star association and evidence for
stellar ejecta separately from morphology and wind-swept interstellar gas.
This checkpoint names the next catalogue; it acquires no sources, admits no
objects and implements no new layer. PN atlas closure and software cleanup
remain the current task. The full-suite receipt above is retained across this
documentation-only update; rerun the affected documentation contract.


## General curated catalogue installation candidate (2026-10-14)

Fernando requested accepted bundles be tracked, then selected normal package
installation with curated defaults. The published data correction is at
`4c6392987293141765a08daa88462dac9bb3ae47`, with clean synchronized Mac tree.
The bounded candidate adds generic bundle verification, portable wheel/sdist
activation, editable-source support, explicit original-source access and
automatic matching criteria appendices. It preserves source snapshots,
scientific rows and canonical chart/native-sky owners. No new nebular class or
object-report table is implemented. EN-MS / NE-EM remains the next catalogue.

New build-only module and installation-test admission are recorded in source_tree.
The clean-install oracle uses declared synthetic bundles and tests wheel,
source-archive and editable routes outside the repository. Actual accepted
513-row OC/319-row PN wheel verification and the final full-suite merge gate
remain Mac acceptance steps. No merge or branch deletion for this new software
candidate is authorized by the earlier PN-atlas closure.

The Mac focused gate at `65d3cb3799eb63c52a34d4ffd0e47b7fd0ad783f`
passed 21 tests but stopped in the editable-install oracle: an existing Wenu
installation could precede the fixture's editable source on the import path.
The corrected oracle processes the fixture before dependency locations and
includes a competing ambient Wenu package to detect shadowing. This changes
verification only; actual accepted-bundle wheel and full-suite receipts remain
pending.
