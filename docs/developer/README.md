# Active Wenu developer documents

Only current authority, retained target direction, the active roadmap, and
work in progress live directly in this directory. Completed audits,
migrations, milestone evidence, and superseded roadmaps are under
[`archive/`](archive/README.md).

## Current architecture and interfaces

- [`current_architecture_v0.9.md`](current_architecture_v0.9.md) — implemented
  architecture authority.
- [`implementation_reference.md`](implementation_reference.md) — current
  public and advanced API reference.
- [`source_tree.md`](source_tree.md) — current source responsibility map.
- [`configuration_schema_v2.md`](configuration_schema_v2.md) — implemented
  configuration schema.
- [`assistant_instructions.md`](assistant_instructions.md) — contribution and
  delivery rules.

## Retained target direction

- [`target_architecture_v0.9.5.md`](target_architecture_v0.9.5.md) — retained
  target and scientific-vocabulary authority.
- [`coordinate_system_guide_v0.9.5.md`](coordinate_system_guide_v0.9.5.md) —
  living scientific and implementation guide.

## Roadmap and current work

- [Stellar Bayer/Flamsteed designation audit](stellar_designations_audit.md)
  — accepted design amended for explicit name/Bayer selection beyond the
  magnitude limit, CLI/TOML parity and future curation boundaries.
  Implementation, resource admission and merge remain pending; Gaia stays later.

**2026-10-05 checkpoint:** Both development branches are merged into clean
`main` at `91f78412` and have been deleted; both programs remain incomplete.
The [roadmap checkpoint](post_v0.9_architecture_roadmap.md#current-forward-roadmap)
is the current status and resumption authority. Agreed order: Bayer/Flamsteed
→ finish minor bodies → curate atlas/publication outputs → resume satellites.
Historical candidate and merge-gate statements in retained milestone records
must be read with their later acceptance entries.

The [minor-body selection checkpoint](post_v0.9_architecture_roadmap.md#minor-body-selection-completion-pending-2026-10-05)
adds the remaining automatic asteroid-name and unnumbered/provisional selection
gaps. Explicit installed asteroid aliases and exact comet names/designations
already work; these pending extensions must be closed before general 50A
selection is claimed. They remain after the Bayer/Flamsteed work.

- [`post_v0.9_architecture_roadmap.md`](post_v0.9_architecture_roadmap.md) —
  the single active forward roadmap for remaining minor-body work, artificial
  satellites, and publication output.
- [`artificial_satellite_crossing_audit_50s0.md`](artificial_satellite_crossing_audit_50s0.md)
  — accepted SatChecker-first, provider-policy, local-oracle, conservative-filter,
  snapshot, specimen-builder, and apparent-brightness decisions for
  artificial-satellite crossings.
- [`satchecker_provider_contract_audit_50s2a.md`](satchecker_provider_contract_audit_50s2a.md)
  — accepted SatChecker endpoint, time-scale, candidate-envelope, async,
  cache, provenance, failure, and redistribution contract for 50S.2B.
- [`satellite_report_drawing_audit_50s3a.md`](satellite_report_drawing_audit_50s3a.md)
  — accepted contract for honest sampled-evidence reports, shared-path charts,
  stable satellite semantics, and the bounded 50S.3B implementation.
- [`satellite_snapshot_propagation_audit_50s4a.md`](satellite_snapshot_propagation_audit_50s4a.md)
  — accepted dependency, immutable-snapshot, SGP4/TEME, Earth-orientation,
  topocentric-validation, and specimen-builder contract for 50S.4.
- [`satellite_crossing_oracle_audit_50s5a.md`](satellite_crossing_oracle_audit_50s5a.md)
  — accepted coordinate, query, validated-numerical-completeness, failure,
  validation, and ownership contract for the bounded 50S.5B local oracle.
- [`satellite_crossing_acceleration_audit_50s6a.md`](satellite_crossing_acceleration_audit_50s6a.md)
  — accepted zero-false-negative, staged-filter, exact-oracle-equivalence,
  benchmark-admission, and ownership contract for bounded 50S.6B work.
- [`satellite_crossing_coordination_audit_50s6c.md`](satellite_crossing_coordination_audit_50s6c.md)
  — accepted exact-solver coordination, broader-domain evidence, fallback,
  equivalence, and benchmark-admission contract for bounded 50S.6D work.
- [`satellite_multifov_interchange_audit_50s6e.md`](satellite_multifov_interchange_audit_50s6e.md)
  — accepted same-observer, airmass-bounded multi-FoV, observatory
  interchange, exact chart-track, and four-source illumination roadmap audit.
- [`satellite_delivery_audit_50s6g.md`](satellite_delivery_audit_50s6g.md)
  — accepted representative-snapshot, canonical-report, two-call file,
  exact-track, and chart-delivery decomposition for 50S.6G.
- [`satellite_binocular_regional_track_audit_50s6g3b.md`](satellite_binocular_regional_track_audit_50s6g3b.md)
  — accepted ordinary-request, fixed-frame, lifecycle, styling, semantic-SVG,
  and PNG/PDF/SVG specimen contract for binocular and regional exact tracks.
- [`satellite_stereographic_planisphere_track_audit_50s6g4a.md`](satellite_stereographic_planisphere_track_audit_50s6g4a.md)
  — accepted corrective contract for exact tracks on the ordinary
  zenith-centred observer-horizontal AltAz stereographic planisphere.
- [`satellite_exact_local_track_audit_50s6g3a.md`](satellite_exact_local_track_audit_50s6g3a.md)
  — accepted exact connected-visit evidence, deterministic anchored sampling,
  identity, fail-closed behavior, and output-neutral layer contract.
- [`satellite_snapshot_preflight_audit_50s6g1b.md`](satellite_snapshot_preflight_audit_50s6g1b.md)
  — accepted two-phase provider-policy, single-bulk-request, immutable
  publication, representative-tier, and evidence contract for 50S.6G.1B.
- [`satellite_tabular_report_audit_50s6g2b.md`](satellite_tabular_report_audit_50s6g2b.md)
  — accepted lossless ECSV/VOTable interoperability, shared reusable tabular
  projection, metadata, strict decode, and round-trip contract for 50S.6G.2B.
- [`satellite_cli_file_protocol_audit_50s6g2c.md`](satellite_cli_file_protocol_audit_50s6g2c.md)
  — accepted direct CLI and digest-bound two-call JSON, no-clobber
  publication, path-safety, exit-status, and interruption contract.
- [`satellite_exact_crossing_report_audit_50s6g2a.md`](satellite_exact_crossing_report_audit_50s6g2a.md)
  — accepted immutable exact-crossing logical model, Draft 2020-12 JSON
  Schema, deterministic JSON, digest, and round-trip contract for 50S.6G.2A.
- [`satellite_snapshot_admission_audit_50s6g1b2a.md`](satellite_snapshot_admission_audit_50s6g1b2a.md)
  — accepted exact-digest-plus-manifest, shared evidence-only external
  snapshot admission contract for 50S.6G.1B.2A.
- [`satellite_medium_specimen_audit_50s6g1b2c.md`](satellite_medium_specimen_audit_50s6g1b2c.md)
  — accepted deterministic stratification, receipt, and external medium
  publication contract for 50S.6G.1B.2C.
- [`satellite_guide.md`](satellite_guide.md) — pedagogical artificial-satellite
  guide to acronyms, scientific language, formulae, principles, and module relationships.
- [`satellite_program_log.md`](satellite_program_log.md) — chronological 50S
  candidate, verification, acceptance, and authorization record.
- [`comet_discovery_and_reporting_audit_50a5d.md`](comet_discovery_and_reporting_audit_50a5d.md)
  — active parent contract for observer-dependent comet discovery magnitude
  and natural moving-object reports.
- [`comet_photometry_revision_50a5d1b1.md`](archive/milestone_history/50a_minor_bodies/comet_photometry_revision_50a5d1b1.md)
  — accepted operational revision of comet sampling, workload control,
  Horizons transport, and CLI failures; closed on 2026-10-05 with the full
  2,923-test Mac gate and the live 214-comet/cache/error acceptance.

The accepted 50A.0 through 50A.3C records and completed 50A.3D through
50A.5D.2C records, including the original 50A.5D.1B comet-photometry
acceptance evidence, are archived under
[`archive/milestone_history/50a_minor_bodies/`](archive/milestone_history/50a_minor_bodies/).
The completed 49J program and its superseded combined future-program document
are archived under [`archive/milestone_history/49j_performance/`](archive/milestone_history/49j_performance/)
and [`archive/roadmap_history/`](archive/roadmap_history/).

Do not place completed milestone records directly in this directory. Move them
to the matching archive family and update active links and documentation tests
in the same change.

- [50S.6G.1B.2D exact-equivalence matrix audit](satellite_equivalence_matrix_audit_50s6g1b2d.md)
  — accepted documentation-only contract for strict exhaustive/accelerated
  equality and external matrix evidence.
- [50S.6H observatory-planning adapter audit](satellite_observatory_planning_adapter_audit_50s6h.md)
  — accepted documentation-only contract for an offline general planning
  advisory, a non-writing Paranal profile, and a reserved ELT profile.

- [50S.7A illumination and night-geometry audit](satellite_illumination_night_geometry_audit_50s7a.md)
  — accepted documentation-only contract for four incident-light components,
  finite-source shadow transitions, geometric twilight, fidelity tiers,
  provenance, and a bounded direct-Sun-first implementation sequence.
- [50S.7C shadow-transition audit](satellite_shadow_transition_audit_50s7c.md)
  — accepted documentation-only contract for continuous finite-Sun/WGS-84
  contact geometry, complete bounded event search, certified UTC brackets,
  identity, failure, and independent event validation.
- [50S.7D direct-source radiometry audit](satellite_direct_source_radiometry_audit_50s7d.md)
  — accepted documentation-only contract for direct-source model separation,
  IAU nominal bolometric Sunlight, solar spectral-resource reservation,
  lunar-model reservation, uncertainty, validation, and a bounded
  solar-first 50S.7D.1 implementation.
- [50S.7D.2 spectral direct-Sun radiometry audit](satellite_spectral_solar_radiometry_audit_50s7d2.md)
  — accepted documentation-only contract for one digest-bound TSIS-1 HSRS
  v2 product, native-grid energy semantics, uncertainty, and offline use.
- [50S.7D.3 direct-Moonlight radiometry readiness audit](satellite_moonlight_radiometry_audit_50s7d3.md)
  — accepted documentation-only comparison of ROLO, GIRO, and LIME; preferred
  LIME model family; required lunar geometry, uncertainty, resource, and
  licensing evidence; and an explicit runtime stop gate.
- [50S.7D.3A external LIME distribution preflight](satellite_lime_distribution_preflight_50s7d3a.md)
  — accepted receipt for exact LIME Toolbox v1.4.2 source, release assets,
  coefficients, licensing, geometry interface, domain, and remaining runtime
  blockers; no installation, execution, or Moonlight runtime.

Accepted 50S.7D.3A freezes exact candidate `27e1ee1c` and its documentation-
only LIME identity and architecture boundary. Later accepted offline inspection
is recorded below; neither record admits numerical Moonlight.

- [50S.7D.3B offline LIME inspection](satellite_lime_offline_inspection_audit_50s7d3b.md)
  — accepted external evidence from a no-install, network-denied Mac inspection;
  both signatures remain unverified and no numeric Wenu Moonlight exists.
- [Phase B independent Moonlight geometry comparison audit](satellite_moonlight_geometry_comparison_audit_50s7d3_phase_b.md)
  — accepted documentation-only plan for named lunar frames, signed phase,
  frozen satellite states, direct SPICE oracles, and later comparison gates.

- [Phase B frozen-kernel comparison protocol](satellite_moonlight_geometry_run_protocol_phase_b.md)
  — accepted protocol and resource/three-sample coverage receipts; final
  Cartesian specimens, signed phase, EOP uncertainty and runtime load order
  remain open. Comparison execution and numerical Moonlight remain blocked.
