# Kernel migration: as-is functionality and test audit

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
