# Wenu production source map

**As-is baseline:** `6708f54a`, 2026-10-17. This inventory covers every Python
file under `src/wenu`; it describes current ownership, not future package names.
The [architecture](current_architecture_v0.9.md) explains cross-cutting seams;
the [roadmap](kernel_roadmap_v0.9.5.md) defines proposed changes.

All entries link to actual source. Package extraction is not implied by a
directory boundary. The one Python build helper outside `wenu`,
[`curated_catalogue_packaging.py`](../../src/curated_catalogue_packaging.py),
owns verified curated-resource packaging and is not a science provider.

The development-only [gate runner](../../tools/run_test_gate.py) and
[reviewed selections](../../tools/test_gates_v1.json) live outside product and
SDK packages. Its [stdlib tests](../../tools/tests/test_test_gates.py) validate
selection/runner failures independently of Wenu. It neither discovers affected
owners automatically nor changes root pytest collection. See the
[testing policy](testing_policy.md) for the consumer matrix and scope limits.

## (root services)

The independent [kernel project](../../packages/wenu_kernel/README.md) lives
outside `src/wenu`. Its `records.py`, `errors.py`, `providers.py`, `kernel.py`
and small `__init__.py` own candidate SDK values, errors, protocol and session
lifecycle respectively. `reuse.py` owns angular certificate identities and
interval/error admission and canonical plan identity without physical motion
equations. `providers.py` also declares the optional canonical planning protocol;
`kernel.py` admits its schedule and owns atomic per-object anchor caching.
`records.py` also owns SI Cartesian values and explicit velocity availability;
`kernel.py` validates the matching native variant and independent error bounds,
including optional source epochs only for explicit `static_direction` admissions.
The conformance kit checks static invariance across supplied query/probe times.
[`time.py`](../../packages/wenu_kernel/src/wenu_kernel/time.py) owns explicit
time-adapter admission, conversion records and the TimeService boundary;
[`time_adapters.py`](../../packages/wenu_kernel/src/wenu_kernel/time_adapters.py)
owns the optional bounded TT(TAI)/TAI conversion. No implicit session conversion
or astronomical backend import is introduced.
[`conformance.py`](../../packages/wenu_kernel/src/wenu_kernel/conformance.py)
ships the optional portable provider test suite, case and activity vocabulary;
it imports only the SDK and standard library, not repository fixtures.
All source/test
paths and the explicit selection manifest are tracked in
[the migration inventory](kernel_migration_inventory_v1.json).
The native stellar adapter imports it lazily; unrelated product imports do
not eagerly initialize it. Root packaging declares the separate SDK dependency.
K3 request isolation remains inside the existing owners:
`charts/request_generation.py` owns `open_chart_request_scope`, shared by
ordinary generation, direct drawing and native atlas sheets, plus the journal,
temporary layer/registry restoration and build lifetime. Horizon, disk and
track configuration owners remember their attribute writes through that journal;
`minor_body_resources.py` owns atomic resolver binding/restoration. No new
catalogue clone is introduced by lifecycle isolation. The separate
`catalogue_state.py` owner now binds immutable copied direction tables and
queries the SDK. `stellar_state.py` retains the native stellar facade; `objects/stars.py` owns selection, public source-native HIP lookup and
geometry conversion. Native constellation lines consume that public lookup,
not source-table coordinates. Native page
creation in `charts/request_generation.py` also owns its fixed-resolution
offscreen canvas, separately from raster export dpi. The kernel imports no
concrete Wenu classes.

| Module | Present responsibility |
|---|---|
| [`__init__.py`](../../src/wenu/__init__.py) | Wenu: publication-quality astronomical chart generation. |
| [`_satellite_tabular_reports.py`](../../src/wenu/_satellite_tabular_reports.py) | Lossless in-memory tabular interchange for exact crossing reports. |
| [`antisolar.py`](../../src/wenu/antisolar.py) | Observer-relative apparent antisolar direction geometry. |
| [`astrometric_state.py`](../../src/wenu/astrometric_state.py) | Object-independent immutable SI rows, nominal rectilinear direction/Cartesian evaluation, domain validation and direction numerical/reuse certification through the SDK; no catalogue or observer dependencies. |
| [`atlas_design.py`](../../src/wenu/atlas_design.py) | Observer-independent atlas geometry specimens and strict versioned JSON. |
| [`chart_document.py`](../../src/wenu/chart_document.py) | Neutral records shared by chart orchestration and renderers. |
| [`cluster_state.py`](../../src/wenu/cluster_state.py) | Cluster-specific source qualification, unit conversion, centre policy and provider identity facade over the shared astrometric engine; native chart adaptation remains with the object layer. |
| [`comet_designations.py`](../../src/wenu/comet_designations.py) | Lossless IAU/MPC comet-designation identity vocabulary. |
| [`comet_discovery.py`](../../src/wenu/comet_discovery.py) | Provider-neutral comet discovery through the NASA/JPL SBDB Query API. |
| [`comet_photometry.py`](../../src/wenu/comet_photometry.py) | Observer-dependent comet model magnitude from NASA/JPL Horizons. |
| [`coordinate_service.py`](../../src/wenu/coordinate_service.py) | Central astronomical transformations for typed spherical geometry. |
| [`coordinates.py`](../../src/wenu/coordinates.py) | Astronomical coordinate vocabulary and legacy conversion functions. |
| [`ephemeris.py`](../../src/wenu/ephemeris.py) | Typed Cartesian ephemeris-state boundary. |
| [`minor_body_acquisition.py`](../../src/wenu/minor_body_acquisition.py) | Networked preflight acquisition for immutable numbered-asteroid resources. |
| [`minor_body_ephemeris.py`](../../src/wenu/minor_body_ephemeris.py) | Offline minor-body states from one borrowed Horizons SPK resource. |
| [`minor_body_identity.py`](../../src/wenu/minor_body_identity.py) | Exact installed/provider identity resolution for minor bodies. |
| [`minor_body_resources.py`](../../src/wenu/minor_body_resources.py) | Explicit offline resolution and lifecycle for minor-body resources. |
| [`observer.py`](../../src/wenu/observer.py) | Observer. |
| [`output_policy.py`](../../src/wenu/output_policy.py) | Public output-format vocabulary. |
| [`positions.py`](../../src/wenu/positions.py) | Astronomical position-provider boundary. |
| [`resources.py`](../../src/wenu/resources.py) | Resources. |
| [`satchecker.py`](../../src/wenu/satchecker.py) | Policy-compliant SatChecker crossing adapter and exact local cache. |
| [`satellite_crossing_reports.py`](../../src/wenu/satellite_crossing_reports.py) | Canonical immutable reports for exact local satellite crossings. |
| [`satellite_crossings.py`](../../src/wenu/satellite_crossings.py) | Provider-neutral artificial-satellite crossing contracts. |
| [`satellite_planning_advisories.py`](../../src/wenu/satellite_planning_advisories.py) | Offline observatory-neutral advisories from exact satellite reports. |
| [`satellite_presentations.py`](../../src/wenu/satellite_presentations.py) | Renderer-neutral reports for normalized SatChecker candidate evidence. |
| [`skyfield_ephemeris.py`](../../src/wenu/skyfield_ephemeris.py) | Skyfield adapter for one already-resolved JPL SPK resource. |
| [`solar_system_appearance.py`](../../src/wenu/solar_system_appearance.py) | Renderer-neutral physical appearance of spherical Solar-System bodies. |
| [`solar_system_directions.py`](../../src/wenu/solar_system_directions.py) | Observer-relative Solar-System direction realization. |
| [`solar_system_disk_geometry.py`](../../src/wenu/solar_system_disk_geometry.py) | Renderer-neutral physical spherical geometry for apparent body disks. |
| [`star_designations.py`](../../src/wenu/star_designations.py) | Offline, immutable HIP-linked Wikidata candidates, separate from astrometry. |
| [`stellar_research.py`](../../src/wenu/stellar_research.py) | Immutable, offline HIP index of designation research and accepted policy. |
| [`catalogue_state.py`](../../src/wenu/catalogue_state.py) | Shared immutable direction-table provider with optional aligned per-row epochs, vector decoding and owned kernel scope; no catalogue decoding, observer or graphics. |
| [`stellar_state.py`](../../src/wenu/stellar_state.py) | Source-epoch native stellar facade over the shared table/provider boundary; no propagation or acquisition. |
| [`stellar_catalogue.py`](../../src/wenu/stellar_catalogue.py) | Validated stellar ingestion, immutable metadata mirror and standard table envelope; source facts read from data documents. |
| [`svg_document.py`](../../src/wenu/svg_document.py) | Deterministic semantic annotations for Matplotlib SVG output. |
| [`temporal.py`](../../src/wenu/temporal.py) | Renderer-neutral temporal sequence vocabulary. |
| [`temporal_components.py`](../../src/wenu/temporal_components.py) | Shared visibility policy for start-inclusive temporal components. |
| [`translations.py`](../../src/wenu/translations.py) | Package-wide translation of generated visual labels. |
| [`visibility.py`](../../src/wenu/visibility.py) | Visibility utilities. |

## charts

| Module | Present responsibility |
|---|---|
| [`charts/__init__.py`](../../src/wenu/charts/__init__.py) | Chart specifications, styles, and rendering results. |
| [`charts/_masking.py`](../../src/wenu/charts/_masking.py) | Presentation helpers for constellation-region masks. |
| [`charts/all_sky.py`](../../src/wenu/charts/all_sky.py) | Production configuration for Galactic Mollweide all-sky charts. |
| [`charts/atlas_index.py`](../../src/wenu/charts/atlas_index.py) | Resolved atlas index presentation through canonical chart/render/export owners. |
| [`charts/atlas_modes.py`](../../src/wenu/charts/atlas_modes.py) | Print and presentation realizations of the atlas chart style. |
| [`charts/atlas_publication.py`](../../src/wenu/charts/atlas_publication.py) | Design-bound atlas planning and canonical chart-page publication. |
| [`charts/automatic_legends.py`](../../src/wenu/charts/automatic_legends.py) | High-level automatic composition of chart legends. |
| [`charts/binocular.py`](../../src/wenu/charts/binocular.py) | Circular binocular-field chart type. |
| [`charts/boundaries.py`](../../src/wenu/charts/boundaries.py) | Reusable projected boundaries and coordinate-label anchors. |
| [`charts/cartoon.py`](../../src/wenu/charts/cartoon.py) | Convenience composition for educational cartoon charts. |
| [`charts/cartoon_composition.py`](../../src/wenu/charts/cartoon_composition.py) | Deprecated compatibility wrappers for cartoon chart composition. |
| [`charts/cartoon_modes.py`](../../src/wenu/charts/cartoon_modes.py) | Print and presentation realizations of the cartoon chart style. |
| [`charts/center_arguments.py`](../../src/wenu/charts/center_arguments.py) | Explicit named-center parsing and offline namespace resolution. |
| [`charts/chart_arguments.py`](../../src/wenu/charts/chart_arguments.py) | Shared command-line arguments for canonical chart requests. |
| [`charts/chart_legend_workflow.py`](../../src/wenu/charts/chart_legend_workflow.py) | Render a chart and compose its independent legends in one workflow. |
| [`charts/circumpolar.py`](../../src/wenu/charts/circumpolar.py) | Reusable north- and south-circumpolar chart type. |
| [`charts/command_line.py`](../../src/wenu/charts/command_line.py) | Shared command-line adaptation for ordinary chart views. |
| [`charts/composition.py`](../../src/wenu/charts/composition.py) | Composition of chart geometry, style, mode, and content detail. |
| [`charts/constellation_label_placement.py`](../../src/wenu/charts/constellation_label_placement.py) | Chart-local preparation of automatic constellation label anchors. |
| [`charts/constellation_resolver.py`](../../src/wenu/charts/constellation_resolver.py) | Offline resolution of IAU constellation sets and packaged groups. |
| [`charts/context.py`](../../src/wenu/charts/context.py) | Output-neutral geometric context supplied by chart specifications. |
| [`charts/detail.py`](../../src/wenu/charts/detail.py) | Output-neutral contracts and adaptive chart-detail policies. |
| [`charts/detail_application.py`](../../src/wenu/charts/detail_application.py) | Apply resolved chart detail to a populated celestial sphere. |
| [`charts/drawing.py`](../../src/wenu/charts/drawing.py) | Ordinary drawing of prepared observer-bound chart views. |
| [`charts/export_workflow.py`](../../src/wenu/charts/export_workflow.py) | Canonical high-level export for resolved chart compositions. |
| [`charts/fixed_sky_baseline.py`](../../src/wenu/charts/fixed_sky_baseline.py) | Complete-render baseline and PNG comparison for fixed-sky work. |
| [`charts/fixed_sky_orientation.py`](../../src/wenu/charts/fixed_sky_orientation.py) | Renderer-neutral orientation for a fixed circumpolar celestial scene. |
| [`charts/fixed_sky_sequence.py`](../../src/wenu/charts/fixed_sky_sequence.py) | Planning contract for a fixed celestial scene and rotating local horizon. |
| [`charts/footer_furniture.py`](../../src/wenu/charts/footer_furniture.py) | Matplotlib-facing rendering of canonical figure-margin footers. |
| [`charts/full_sky.py`](../../src/wenu/charts/full_sky.py) | Production configuration and orchestration for full-sky charts. |
| [`charts/furniture.py`](../../src/wenu/charts/furniture.py) | Backend-independent options for canonical chart furniture. |
| [`charts/horizon_mask.py`](../../src/wenu/charts/horizon_mask.py) | Projection preparation for observer-horizon mask openings. |
| [`charts/label_placement.py`](../../src/wenu/charts/label_placement.py) | Reusable discrete placement rules for constellation labels. |
| [`charts/legend.py`](../../src/wenu/charts/legend.py) | Configurable informational legends for static sky charts. |
| [`charts/legend_composition.py`](../../src/wenu/charts/legend_composition.py) | Coordinate independently rendered object and stellar legends. |
| [`charts/legend_geometry.py`](../../src/wenu/charts/legend_geometry.py) | Extract legend inputs from completed chart-rendering results. |
| [`charts/legend_inputs.py`](../../src/wenu/charts/legend_inputs.py) | Resolve stellar-legend inputs from chart detail and visual style. |
| [`charts/legend_metadata.py`](../../src/wenu/charts/legend_metadata.py) | Backend-independent metadata for informational chart legends. |
| [`charts/legend_plan.py`](../../src/wenu/charts/legend_plan.py) | Backend-independent plans for composing chart legends. |
| [`charts/legend_symbols.py`](../../src/wenu/charts/legend_symbols.py) | Backend-independent descriptions of symbols used by chart legends. |
| [`charts/magnitude_legend.py`](../../src/wenu/charts/magnitude_legend.py) | Backend-independent stellar magnitude-scale descriptions. |
| [`charts/magnitude_legend_matplotlib.py`](../../src/wenu/charts/magnitude_legend_matplotlib.py) | Matplotlib rendering for stellar magnitude–size legends. |
| [`charts/magnitude_legend_style.py`](../../src/wenu/charts/magnitude_legend_style.py) | Style configuration for stellar magnitude–size legends. |
| [`charts/magnitude_legend_workflow.py`](../../src/wenu/charts/magnitude_legend_workflow.py) | Chart-level workflow for stellar magnitude–size legends. |
| [`charts/modes.py`](../../src/wenu/charts/modes.py) | Output-medium modes for chart composition. |
| [`charts/object_center.py`](../../src/wenu/charts/object_center.py) | Typed resolution of point-object chart centres. |
| [`charts/polar_binocular_targets.py`](../../src/wenu/charts/polar_binocular_targets.py) | Packaged binocular content for paired physical polar planispheres. |
| [`charts/polar_calendar.py`](../../src/wenu/charts/polar_calendar.py) | Immutable common-year calendar geometry for polar planispheres. |
| [`charts/polar_calendar_furniture.py`](../../src/wenu/charts/polar_calendar_furniture.py) | Resolved physical calendar furniture for paired polar planispheres. |
| [`charts/polar_horizon_overlay.py`](../../src/wenu/charts/polar_horizon_overlay.py) | Observer-latitude horizon geometry for paired polar overlays. |
| [`charts/polar_label_curation.py`](../../src/wenu/charts/polar_label_curation.py) | Reviewed label clearances for the physical polar planisphere. |
| [`charts/polar_magnitude_scale.py`](../../src/wenu/charts/polar_magnitude_scale.py) | Polar-only stellar magnitude-scale semantics and physical placement. |
| [`charts/polar_magnitude_scale_rendering.py`](../../src/wenu/charts/polar_magnitude_scale_rendering.py) | Shared Matplotlib realization of polar-only magnitude-scale furniture. |
| [`charts/polar_page_export.py`](../../src/wenu/charts/polar_page_export.py) | Canonical single-save export of paired physical polar pages. |
| [`charts/polar_page_furniture.py`](../../src/wenu/charts/polar_page_furniture.py) | Renderer-neutral A4 page furniture for paired polar planispheres. |
| [`charts/polar_page_rendering.py`](../../src/wenu/charts/polar_page_rendering.py) | Matplotlib realization of resolved polar physical-page furniture. |
| [`charts/polar_planisphere.py`](../../src/wenu/charts/polar_planisphere.py) | Single-face polar-planisphere disk geometry. |
| [`charts/polar_planisphere_pair.py`](../../src/wenu/charts/polar_planisphere_pair.py) | Immutable paired north/south polar-planisphere geometry. |
| [`charts/polar_planisphere_style.py`](../../src/wenu/charts/polar_planisphere_style.py) | Canonical physical-print appearance for polar planisphere disks. |
| [`charts/polar_pouch_export.py`](../../src/wenu/charts/polar_pouch_export.py) | Actual-size export of paired folded polar-pouch faces. |
| [`charts/polar_pouch_furniture.py`](../../src/wenu/charts/polar_pouch_furniture.py) | Renderer-neutral A4 pouch furniture for paired polar overlays. |
| [`charts/polar_pouch_preview.py`](../../src/wenu/charts/polar_pouch_preview.py) | Diagnostic composition of canonical disks behind polar-pouch marks. |
| [`charts/polar_pouch_rendering.py`](../../src/wenu/charts/polar_pouch_rendering.py) | Matplotlib realization of resolved polar-pouch furniture. |
| [`charts/polar_pouch_sheet.py`](../../src/wenu/charts/polar_pouch_sheet.py) | Single-A4 imposition of the paired folded polar-pouch faces. |
| [`charts/polar_pouch_sheet_export.py`](../../src/wenu/charts/polar_pouch_sheet_export.py) | Actual-size export of one imposed folded polar-pouch sheet. |
| [`charts/polar_pouch_sheet_rendering.py`](../../src/wenu/charts/polar_pouch_sheet_rendering.py) | Vector rendering of both pouch faces on one folded A4 sheet. |
| [`charts/presets.py`](../../src/wenu/charts/presets.py) | Named, complete visual presets for Wenu charts. |
| [`charts/product_options.py`](../../src/wenu/charts/product_options.py) | Shared selection and naming for user-facing chart products. |
| [`charts/projection_selection.py`](../../src/wenu/charts/projection_selection.py) | Immutable chart projection selection and construction boundary. |
| [`charts/reference_furniture.py`](../../src/wenu/charts/reference_furniture.py) | Canonical rendering of celestial reference chart furniture. |
| [`charts/reference_keypoint_legend.py`](../../src/wenu/charts/reference_keypoint_legend.py) | Backend realization of visible celestial-reference legend entries. |
| [`charts/reference_policy.py`](../../src/wenu/charts/reference_policy.py) | Validated public policy for coupled celestial references. |
| [`charts/regional.py`](../../src/wenu/charts/regional.py) | Production configuration and orchestration for regional sky charts. |
| [`charts/rendered_legend_composition.py`](../../src/wenu/charts/rendered_legend_composition.py) | Compose chart legends from an existing chart-rendering result. |
| [`charts/request.py`](../../src/wenu/charts/request.py) | Immutable user-facing chart-request contracts. |
| [`charts/request_chart.py`](../../src/wenu/charts/request_chart.py) | Construct canonical chart geometry from one resolved chart request. |
| [`charts/request_composition.py`](../../src/wenu/charts/request_composition.py) | Product-specific composition choices for declarative chart requests. |
| [`charts/request_disks.py`](../../src/wenu/charts/request_disks.py) | Resolved Solar-System disk request and dynamic layer installation. |
| [`charts/request_furniture.py`](../../src/wenu/charts/request_furniture.py) | Late chart-context realization for declarative request furniture. |
| [`charts/request_generation.py`](../../src/wenu/charts/request_generation.py) | Canonical composition and export for declarative chart requests. |
| [`charts/request_grids.py`](../../src/wenu/charts/request_grids.py) | Request-time semantic coordinate-grid configuration. |
| [`charts/request_horizon.py`](../../src/wenu/charts/request_horizon.py) | Request-time semantic observer-horizon configuration. |
| [`charts/request_realization.py`](../../src/wenu/charts/request_realization.py) | Scientific layer-realization context for ordinary chart requests. |
| [`charts/request_resolver.py`](../../src/wenu/charts/request_resolver.py) | Resolution and load-profile validation for declarative chart requests. |
| [`charts/request_satellite_tracks.py`](../../src/wenu/charts/request_satellite_tracks.py) | Request-owned presentation of already-realized exact satellite tracks. |
| [`charts/request_tracks.py`](../../src/wenu/charts/request_tracks.py) | Request-owned registration of one drawable Solar-System track. |
| [`charts/sequence.py`](../../src/wenu/charts/sequence.py) | Canonical repeated-static observer-time chart sequences. |
| [`charts/sequence_arguments.py`](../../src/wenu/charts/sequence_arguments.py) | Command-line adaptation for canonical temporal chart sequences. |
| [`charts/sequence_manifest.py`](../../src/wenu/charts/sequence_manifest.py) | Deterministic manifests for canonical observer-time chart sequences. |
| [`charts/solar_system_disk_preparation.py`](../../src/wenu/charts/solar_system_disk_preparation.py) | Projected display magnification for resolved Solar-System disks. |
| [`charts/solar_system_track_annotations.py`](../../src/wenu/charts/solar_system_track_annotations.py) | Projected annotation and label layout for Solar-System tracks. |
| [`charts/spatial_selection.py`](../../src/wenu/charts/spatial_selection.py) | Render-local spatial catalogue selection for resolved chart fields. |
| [`charts/stellar_report.py`](../../src/wenu/charts/stellar_report.py) | Designation notes for stars retained by the canonical chart render. |
| [`charts/stellar_sizing_report.py`](../../src/wenu/charts/stellar_sizing_report.py) | Stellar SVG measurements and actual-catalogue atlas count appendices. |
| [`charts/style_components.py`](../../src/wenu/charts/style_components.py) | Typed, composable configuration for complete chart styles. |
| [`charts/style_overrides.py`](../../src/wenu/charts/style_overrides.py) | Render-local visual overrides applied after style and mode resolution. |
| [`charts/styles.py`](../../src/wenu/charts/styles.py) | Reusable publication styles for Wenu charts. |
| [`charts/subject_arguments.py`](../../src/wenu/charts/subject_arguments.py) | Shared command-line adaptation for constellation chart subjects. |
| [`charts/target_resolver.py`](../../src/wenu/charts/target_resolver.py) | Offline resolution of packaged and explicit chart targets. |
| [`charts/view.py`](../../src/wenu/charts/view.py) | Ordinary observer-bound geometrical chart views. |
| [`charts/view_defaults.py`](../../src/wenu/charts/view_defaults.py) | Authoritative geometrical defaults for ordinary chart views. |

## cli

| Module | Present responsibility |
|---|---|
| [`cli/__init__.py`](../../src/wenu/cli/__init__.py) | Command-line tools for Wenu. |
| [`cli/atlas.py`](../../src/wenu/cli/atlas.py) | Installed atlas adapters for geometry, index and chart-page production. |
| [`cli/chart.py`](../../src/wenu/cli/chart.py) | Installed command-line interface for ordinary Wenu chart generation. |
| [`cli/comets.py`](../../src/wenu/cli/comets.py) | Installed command for explicit networked comet discovery. |
| [`cli/examples.py`](../../src/wenu/cli/examples.py) | Install Wenu's canonical example scripts in the current directory. |
| [`cli/notebooks.py`](../../src/wenu/cli/notebooks.py) | Copy the example Wenu notebooks into a user-selected directory. |
| [`cli/satellite_crossings.py`](../../src/wenu/cli/satellite_crossings.py) | Offline CLI and two-call file protocol for exact satellite crossings. |

## configuration

| Module | Present responsibility |
|---|---|
| [`configuration/__init__.py`](../../src/wenu/configuration/__init__.py) | Versioned, validated configuration resources for Wenu. |
| [`configuration/furniture_product_export_translation.py`](../../src/wenu/configuration/furniture_product_export_translation.py) | Translate validated TOML furniture, product, and export values. |
| [`configuration/geometry_detail_translation.py`](../../src/wenu/configuration/geometry_detail_translation.py) | Translate validated TOML values into geometry and detail contracts. |
| [`configuration/sequence_translation.py`](../../src/wenu/configuration/sequence_translation.py) | Translation of temporal sequence configuration defaults. |
| [`configuration/style_mode_translation.py`](../../src/wenu/configuration/style_mode_translation.py) | Translate validated TOML values into existing style and mode contracts. |
| [`configuration/translation.py`](../../src/wenu/configuration/translation.py) | Aggregate translation of one validated effective configuration. |
| [`configuration/validation.py`](../../src/wenu/configuration/validation.py) | Strict validation for Wenu schema-version-2 configuration data. |

## data

| Module | Present responsibility |
|---|---|
| [`data/__init__.py`](../../src/wenu/data/__init__.py) | Package exports and initialization. |
| [`data/catalogs/caldwell/__init__.py`](../../src/wenu/data/catalogs/caldwell/__init__.py) | Packaged Caldwell observing catalogue and source-traced membership. |
| [`data/catalogs/galaxies/__init__.py`](../../src/wenu/data/catalogs/galaxies/__init__.py) | Bundled bright-galaxy catalogue data. |
| [`data/catalogs/globular_clusters/__init__.py`](../../src/wenu/data/catalogs/globular_clusters/__init__.py) | Packaged Harris Milky Way globular-cluster catalogue. |
| [`data/catalogs/hipparcos/__init__.py`](../../src/wenu/data/catalogs/hipparcos/__init__.py) | Package exports and initialization. |
| [`data/catalogs/hipparcos/download_hipparcos.py`](../../src/wenu/data/catalogs/hipparcos/download_hipparcos.py) | Download hipparcos. |
| [`data/catalogs/messier/__init__.py`](../../src/wenu/data/catalogs/messier/__init__.py) | Packaged Messier catalogue data. |
| [`data/catalogs/open_clusters/__init__.py`](../../src/wenu/data/catalogs/open_clusters/__init__.py) | Packaged Galactic open-cluster catalogue. |
| [`data/catalogs/planetary_nebulae/__init__.py`](../../src/wenu/data/catalogs/planetary_nebulae/__init__.py) | Packaged Galactic planetary-nebula catalogue. |
| [`data/catalogs/star_designations/__init__.py`](../../src/wenu/data/catalogs/star_designations/__init__.py) | Frozen Wikidata stellar designation resources. |
| [`data/catalogs/supernova_remnants/__init__.py`](../../src/wenu/data/catalogs/supernova_remnants/__init__.py) | Packaged Green Galactic supernova-remnant catalogue. |
| [`data/constellations/__init__.py`](../../src/wenu/data/constellations/__init__.py) | Package exports and initialization. |
| [`data/constellations/iau/__init__.py`](../../src/wenu/data/constellations/iau/__init__.py) | Package exports and initialization. |
| [`data/constellations/mapuche/__init__.py`](../../src/wenu/data/constellations/mapuche/__init__.py) | Package exports and initialization. |
| [`data/constellations/western/__init__.py`](../../src/wenu/data/constellations/western/__init__.py) | Package exports and initialization. |
| [`data/isophotes/magellanic_clouds/__init__.py`](../../src/wenu/data/isophotes/magellanic_clouds/__init__.py) | Gaia-derived Magellanic Cloud isophote data. |
| [`data/isophotes/milky_way/__init__.py`](../../src/wenu/data/isophotes/milky_way/__init__.py) | Packaged Milky Way isophote data. |
| [`data/satellites/__init__.py`](../../src/wenu/data/satellites/__init__.py) | Packaged artificial-satellite data. |
| [`data/satellites/snapshots/__init__.py`](../../src/wenu/data/satellites/snapshots/__init__.py) | Installed immutable artificial-satellite snapshots. |
| [`data/satellites/snapshots/synthetic_50s4b_v1/__init__.py`](../../src/wenu/data/satellites/snapshots/synthetic_50s4b_v1/__init__.py) | Synthetic 50S.4B validation snapshot resources. |

## example_scripts

| Module | Present responsibility |
|---|---|
| [`example_scripts/__init__.py`](../../src/wenu/example_scripts/__init__.py) | Packaged copies of Wenu's canonical example scripts. |
| [`example_scripts/all_sky.py`](../../src/wenu/example_scripts/all_sky.py) | Generate the canonical Galactic Mollweide all-sky map. |
| [`example_scripts/binocular_object.py`](../../src/wenu/example_scripts/binocular_object.py) | Generate a binocular chart centered on any packaged object. |
| [`example_scripts/circumpolar.py`](../../src/wenu/example_scripts/circumpolar.py) | Generate the canonical southern circumpolar chart. |
| [`example_scripts/planisphere.py`](../../src/wenu/example_scripts/planisphere.py) | Generate the canonical visible-sky planisphere for La Ligua. |
| [`example_scripts/regional_constellation.py`](../../src/wenu/example_scripts/regional_constellation.py) | Generate a regional chart for one IAU constellation. |
| [`example_scripts/regional_constellation_group.py`](../../src/wenu/example_scripts/regional_constellation_group.py) | Generate a regional chart for an arbitrary constellation group. |

## geometry

| Module | Present responsibility |
|---|---|
| [`geometry/__init__.py`](../../src/wenu/geometry/__init__.py) | Coordinate-neutral geometry values and algorithms. |
| [`geometry/clipping.py`](../../src/wenu/geometry/clipping.py) | Clipping. |
| [`geometry/frame.py`](../../src/wenu/geometry/frame.py) | Coordinate-neutral rotations of the celestial sphere. |
| [`geometry/projected.py`](../../src/wenu/geometry/projected.py) | Projected. |
| [`geometry/spherical.py`](../../src/wenu/geometry/spherical.py) | Spherical. |
| [`geometry/viewport.py`](../../src/wenu/geometry/viewport.py) | Viewport. |

## notebooks

| Module | Present responsibility |
|---|---|
| [`notebooks/__init__.py`](../../src/wenu/notebooks/__init__.py) | Example notebooks distributed with Wenu. |

## objects

| Module | Present responsibility |
|---|---|
| [`objects/__init__.py`](../../src/wenu/objects/__init__.py) | Physical astronomical chart layers. |
| [`objects/astronomical_object.py`](../../src/wenu/objects/astronomical_object.py) | Base class for physical astronomical chart layers. |
| [`objects/galaxies.py`](../../src/wenu/objects/galaxies.py) | Source-bound static galaxy centre provider and shape metadata; chart/observer consumers use kernel centres before domain outline construction. |
| [`objects/globular_clusters.py`](../../src/wenu/objects/globular_clusters.py) | Milky Way globular-cluster catalogue layer. |
| [`objects/nonstellar.py`](../../src/wenu/objects/nonstellar.py) | Atomic ingestion, immutable source admission/gap record, angular normalization and metadata-owned centre/outline specifications. |
| [`objects/open_clusters.py`](../../src/wenu/objects/open_clusters.py) | Source-bound cluster lookup metadata/provider, public/native/observed kernel centres and vectorized symbols; default lookup with explicit per-call nominal motion for native Python chart and restored-source consumers. |
| [`objects/planetary_nebulae.py`](../../src/wenu/objects/planetary_nebulae.py) | Planetary-nebula catalogue represented by fixed chart symbols. |
| [`objects/stars.py`](../../src/wenu/objects/stars.py) | Stellar selection, kernel-backed native positions/HIP lookup and spherical point geometry; legacy observed route. |
| [`objects/supernova_remnants.py`](../../src/wenu/objects/supernova_remnants.py) | Green Galactic supernova-remnant catalogue layer. |

## projections

| Module | Present responsibility |
|---|---|
| [`projections/__init__.py`](../../src/wenu/projections/__init__.py) | Coordinate-neutral map projections. |
| [`projections/mollweide.py`](../../src/wenu/projections/mollweide.py) | Coordinate-neutral Mollweide projection with longitude-seam topology. |
| [`projections/polar_azimuthal_equidistant.py`](../../src/wenu/projections/polar_azimuthal_equidistant.py) | Polar azimuthal-equidistant projection for physical sky disks. |
| [`projections/stereographic.py`](../../src/wenu/projections/stereographic.py) | Stereographic. |

## rendering

| Module | Present responsibility |
|---|---|
| [`rendering/__init__.py`](../../src/wenu/rendering/__init__.py) | Geometry preparation and graphical rendering backends. |
| [`rendering/_matplotlib_axes.py`](../../src/wenu/rendering/_matplotlib_axes.py) | A small renderer-side helper rather than giving Viewport knowledge of Matplotlib |
| [`rendering/_matplotlib_primitives.py`](../../src/wenu/rendering/_matplotlib_primitives.py) | Matplotlib rendering primitives for projected Cartesian geometry. |
| [`rendering/label_placement.py`](../../src/wenu/rendering/label_placement.py) | Backend-neutral placement for labels on projected curves. |
| [`rendering/layers.py`](../../src/wenu/rendering/layers.py) | Backward-compatible numeric names for Wenu paint roles. |
| [`rendering/matplotlib.py`](../../src/wenu/rendering/matplotlib.py) | Generic Matplotlib renderer for projected Cartesian geometry. |
| [`rendering/paint_roles.py`](../../src/wenu/rendering/paint_roles.py) | Typed paint-order roles shared by chart rendering and documents. |
| [`rendering/preparation.py`](../../src/wenu/rendering/preparation.py) | Generic preparation between projection and rendering. |
| [`rendering/symbols.py`](../../src/wenu/rendering/symbols.py) | Reusable, independently constructed astronomical chart symbols. |

## satellites

| Module | Present responsibility |
|---|---|
| [`satellites/__init__.py`](../../src/wenu/satellites/__init__.py) | Local artificial-satellite state and resource domain. |
| [`satellites/crossing_acceleration.py`](../../src/wenu/satellites/crossing_acceleration.py) | Conservative first-stage selection for local satellite crossings. |
| [`satellites/crossing_batch.py`](../../src/wenu/satellites/crossing_batch.py) | Atomic same-observer coordination of bounded local crossing queries. |
| [`satellites/crossing_matrix.py`](../../src/wenu/satellites/crossing_matrix.py) | Strict offline exhaustive/accelerated crossing-matrix evidence. |
| [`satellites/crossing_matrix_execution.py`](../../src/wenu/satellites/crossing_matrix_execution.py) | Explicit offline production path for satellite equivalence evidence. |
| [`satellites/crossing_oracle.py`](../../src/wenu/satellites/crossing_oracle.py) | Complete local circular-field crossing oracle for satellite snapshots. |
| [`satellites/elements.py`](../../src/wenu/satellites/elements.py) | Canonical immutable OMM/GP satellite element records. |
| [`satellites/exact_tracks.py`](../../src/wenu/satellites/exact_tracks.py) | Exact local track evidence for one accepted satellite crossing. |
| [`satellites/illumination.py`](../../src/wenu/satellites/illumination.py) | Direct-Sun occultation and observer-night geometry for satellites. |
| [`satellites/radiometry.py`](../../src/wenu/satellites/radiometry.py) | Offline direct-Sun spectral radiometry for artificial satellites. |
| [`satellites/sgp4.py`](../../src/wenu/satellites/sgp4.py) | Validated Vallado-compatible SGP4 propagation into geometric TEME. |
| [`satellites/snapshot_acquisition.py`](../../src/wenu/satellites/snapshot_acquisition.py) | Provider-governed construction of external satellite snapshots. |
| [`satellites/snapshot_admission.py`](../../src/wenu/satellites/snapshot_admission.py) | Explicit digest-bound admission for external satellite snapshots. |
| [`satellites/snapshot_evidence.py`](../../src/wenu/satellites/snapshot_evidence.py) | Deterministic offline evidence specimens derived from admitted snapshots. |
| [`satellites/snapshots.py`](../../src/wenu/satellites/snapshots.py) | Immutable installed artificial-satellite element snapshots. |
| [`satellites/topocentric.py`](../../src/wenu/satellites/topocentric.py) | Earth-orientation and observer transformation for satellite TEME states. |

## sky

| Module | Present responsibility |
|---|---|
| [`sky/__init__.py`](../../src/wenu/sky/__init__.py) | Package exports and initialization. |
| [`sky/celestial_sphere.py`](../../src/wenu/sky/celestial_sphere.py) | Celestial-sphere layer ownership and chart orchestration. |
| [`sky/ceres.py`](../../src/wenu/sky/ceres.py) | Catalog-owned identity for the first drawable asteroid. |
| [`sky/constellation_boundaries.py`](../../src/wenu/sky/constellation_boundaries.py) | Official IAU constellation boundaries as spherical domain geometry. |
| [`sky/constellation_labels.py`](../../src/wenu/sky/constellation_labels.py) | Constellation label anchors represented as spherical point geometry. |
| [`sky/constellation_lines.py`](../../src/wenu/sky/constellation_lines.py) | Curated edge topology joined to public native HIP positions or legacy observer-time geometry. |
| [`sky/constellations.py`](../../src/wenu/sky/constellations.py) | Constellation layer grouping without projection or rendering state. |
| [`sky/coordinate_grids.py`](../../src/wenu/sky/coordinate_grids.py) | Observer-time AltAz, equatorial, ecliptic, and Galactic grid geometry. |
| [`sky/earth.py`](../../src/wenu/sky/earth.py) | Non-drawable Earth identity for moving-body relationships. |
| [`sky/frozen_earth_disk_sequences.py`](../../src/wenu/sky/frozen_earth_disk_sequences.py) | Frozen-Earth geometric planet-disk sequence state. |
| [`sky/frozen_earth_reference_grids.py`](../../src/wenu/sky/frozen_earth_reference_grids.py) | Observer-independent reference geometry for frozen-Earth charts. |
| [`sky/frozen_earth_venus_disk_sequence.py`](../../src/wenu/sky/frozen_earth_venus_disk_sequence.py) | Generic drawable frozen-Earth body sequence in fixed ecliptic axes. |
| [`sky/geometrical_object.py`](../../src/wenu/sky/geometrical_object.py) | Base class for geometrical constructs on the celestial sphere. |
| [`sky/horizon.py`](../../src/wenu/sky/horizon.py) | Observer-local altitude-zero reference geometry. |
| [`sky/magellanic_clouds.py`](../../src/wenu/sky/magellanic_clouds.py) | Gaia-derived Magellanic Cloud isophote layers. |
| [`sky/major_planets.py`](../../src/wenu/sky/major_planets.py) | Catalog data for ordinary apparent major-planet symbolic points. |
| [`sky/maximal_sphere.py`](../../src/wenu/sky/maximal_sphere.py) | Canonical loading profile and maximal celestial-sphere factory. |
| [`sky/mercury.py`](../../src/wenu/sky/mercury.py) | Descriptor-only physical identity for output-neutral Mercury state. |
| [`sky/milky_way.py`](../../src/wenu/sky/milky_way.py) | Milky Way surface-brightness isophote layer. |
| [`sky/moon.py`](../../src/wenu/sky/moon.py) | Catalog-governed output-neutral physical identity for the Moon. |
| [`sky/native_snapshot.py`](../../src/wenu/sky/native_snapshot.py) | Verified data-only native sky snapshots; v5 binds nonstellar metadata and retains cluster rows with explicit v1-v4 admission. |
| [`sky/observed_cache.py`](../../src/wenu/sky/observed_cache.py) | Keys for observer-dependent spherical-geometry caches. |
| [`sky/points.py`](../../src/wenu/sky/points.py) | Celestial reference points as spherical domain geometry. |
| [`sky/realization.py`](../../src/wenu/sky/realization.py) | Immutable scientific input for one sky-layer realization. |
| [`sky/rendering_results.py`](../../src/wenu/sky/rendering_results.py) | Results returned by generic celestial-chart orchestration. |
| [`sky/satellite_candidate_layer.py`](../../src/wenu/sky/satellite_candidate_layer.py) | Drawable layers for normalized SatChecker sampled candidate evidence. |
| [`sky/satellite_exact_track_layer.py`](../../src/wenu/sky/satellite_exact_track_layer.py) | Output-neutral layers for exact local satellite track evidence. |
| [`sky/semantic_identity.py`](../../src/wenu/sky/semantic_identity.py) | Renderer-neutral semantic identity for chart layers. |
| [`sky/sky_layer.py`](../../src/wenu/sky/sky_layer.py) | Common contract for chartable celestial-sphere layers. |
| [`sky/solar_system_bodies.py`](../../src/wenu/sky/solar_system_bodies.py) | Typed identities and capabilities for moving Solar-System bodies. |
| [`sky/solar_system_catalog.py`](../../src/wenu/sky/solar_system_catalog.py) | Built-in moving-body catalog; external catalogs can extend this value. |
| [`sky/solar_system_disk_sequences.py`](../../src/wenu/sky/solar_system_disk_sequences.py) | Observed multi-epoch physical Solar-System disk sequences. |
| [`sky/solar_system_points.py`](../../src/wenu/sky/solar_system_points.py) | Shared renderer-neutral orchestration for symbolic Solar-System points. |
| [`sky/solar_system_track_layer.py`](../../src/wenu/sky/solar_system_track_layer.py) | Scientific Solar-System track layer. |
| [`sky/solar_system_tracks.py`](../../src/wenu/sky/solar_system_tracks.py) | Renderer-neutral scientific Solar-System trajectory realization. |
| [`sky/venus.py`](../../src/wenu/sky/venus.py) | Configured symbolic-point specialization for apparent Venus. |
| [`sky/venus_disk.py`](../../src/wenu/sky/venus_disk.py) | Generic request-owned resolved-body disk component layers. |
| [`sky/venus_disk_sequence.py`](../../src/wenu/sky/venus_disk_sequence.py) | Generic drawable observed-body disk sequence in one chart frame. |

## utils

| Module | Present responsibility |
|---|---|
| [`utils/__init__.py`](../../src/wenu/utils/__init__.py) | Package exports and initialization. |
| [`utils/visible.py`](../../src/wenu/utils/visible.py) | Visible. |
