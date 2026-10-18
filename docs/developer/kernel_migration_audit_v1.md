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
the historical J2000 stamp. This fixes the open-cluster portions of M4/M6, not
the shared defaults or other nonstellar families.

| ID / priority | Owner and evidence | Consequence and required action | Verification owner |
|---|---|---|---|
| M1 / fixed | `objects/stars.py` and `stellar_state.py` repeated epoch, source edition and provenance, despite `epoch_year` and the packaged Hipparcos ReadMe | Ingest through `stellar_catalogue.py`; metadata document binds exact source bytes, preserves original fields and mirrors a validated immutable record. Native geometry and kernel queries obtain their epoch/edition/provenance from it. Missing or conflicting metadata is refused. | `test_stellar_state.py`, stellar/public-position owners |
| M2 / fixed | `sky/constellation_lines.py` and `sky/constellation_labels.py` supplied their own Hipparcos epoch/provider descriptions | Native endpoints inherit returned position specifications; label metadata comes from the stellar interface. Label-anchor computation remains a separate legacy state consumer. | Native constellation geometry and frozen label/gap consumers |
| M3 / fixed | `sky/native_snapshot.py` embedded J1991.25 both in writing and admission and did not persist the source metadata envelope | New schema v3 persists metadata, verifies it against source identity/row epochs and restores the same runtime record. v1/v2 compatibility uses an explicit source-bound packaged profile; unidentified legacy sources are refused. Nonstellar snapshot assumptions remain M6. | Snapshot admission/corruption, v1/v2 compatibility, source-free process and serial/spawn consumers |
| M4 / cluster path fixed; shared defaults open | `coordinates.py::icrs_catalogue_spec` and `ICRS_ASTROMETRIC_SPEC` still supply J2000.0 by default. Open-cluster geometry now explicitly consumes row epochs/source lineage; the active table retains nested Hunt provenance under `input_catalogue_metadata.hunt_metadata` | The cluster path no longer inherits J2000. Mixed or unknown collections expose no scalar epoch; selected known rows retain their source label. Change the shared helper to require explicit epoch/unknown only after migrating its other callers. | `test_open_clusters.py`, stellar/nonstellar position contracts and curated saved-sky consumers |
| M5 / mechanism implemented; source gaps open | `objects/nonstellar.py` preserves source fields/metadata/units and mirrors declared coordinate facts in a frozen `NonStellarCatalogueMetadata` record bound to input bytes. Native and observed specifications consume it; source provider identity replaces copied labels. Conflicting declarations and strict incomplete admission fail before publication | Missing facts remain null and discoverable in `missing_fields`; `require_complete()` and strict load refuse them. Legacy charts retain the explicit `legacy-unverified-catalogue-encoding` model. Actual source frame/origin and model-required epoch/scale gaps must be resolved before physical provider closure. Galaxy static directions do not require a measurement epoch. Their centre consumers now use the kernel with an explicitly unknown origin when missing; shape axes/PA remain above it. Compatibility is not evidence of accuracy. | `nonstellar-admission`: owner regressions, real family geometry, cold/saved/source-free and public CLI consumers |
| M6 / header defaults fixed; legacy interpretation explicit | Snapshot v5 derives fixed headers from each provider, stores nonstellar records, checks source identity/table metadata/units/header agreement and retains the separate open-cluster row contract | Readers admit v1-v4 historical formats without treating their J2000 headers as measurement epochs. Missing legacy units/digests are not reconstructed as facts. Resource gaps from M5 remain open; shared coordinate helper defaults are still M4. | Existing corruption owner plus nonstellar record/header conflicts, actual known/unknown epoch round trips and legacy admission |
| M7 / medium, open | `sky/ceres.py::CERES_SOLUTION` embeds Horizons solution number/date, osculating epoch and quality fields; `minor_body_resources.py` treats this descriptor as the expected identity, while newer comet identities are manifest-derived | A Ceres resource update requires a code edit and can diverge from its acquisition evidence. Migrate the complete solution identity to a versioned data manifest; preserve the existing descriptor-to-manifest/SPK digest and frame checks. | Minor-body resources/ephemeris and Ceres public state/track owners |
| M8 / medium, open | `satellites/radiometry.py` embeds TSIS product DOI/URL, byte digest/count, grid bounds/sampling, header and audit integral | These are edition-specific resource facts and belong to a validated resource metadata document. Current code deliberately admits one exact resource and verifies it; this is inflexibility/duplication, not evidence of corrupted radiometry. Preserve the numerical integral and malformed-resource oracles when extracting it. | Satellite radiometry resource/parser owner |
| M9 / medium, open | `sky/milky_way.py` and `sky/magellanic_clouds.py` provide fixed source descriptions/ICRS semantics while loaders retain chiefly source paths and feature levels | Preserve dataset edition, source coordinate semantics and provenance in their own metadata envelope. `epoch=None` may be appropriate for diffuse morphology; do not turn it into a fictitious stellar epoch. | Isophote loading/native geometry and saved-ring consumers |
| M10 / low, open | `skyfield_ephemeris.py::_model_from_filename` identifies a DE model from its filename unless explicitly supplied | Prefer the acquisition/validated resource identity. Renaming is not evidence that kernel contents changed; explicit-model admission is already supported. Coverage and digest are read from the resource. | `test_skyfield_ephemeris.py` resource identity owner |

Examples already following the intended boundary include satellite OMM records
(`satellites/elements.py` reads epoch, frame, centre and time system and validates
its supported contract), SPK segment centre/frame/coverage checks, manifest-bound
comet resources and hashed observer-location records. Preserve these checks.

### Nonstellar source declaration audit at `0d25179c`

The following describes the embedded metadata of the actual active tables,
not reconstructed measurement facts. Source bytes and all original declarations
are retained; no catalogue files are changed by the admission slice.

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
