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
  — candidate dependency, immutable-snapshot, SGP4/TEME, Earth-orientation,
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
  — candidate same-observer, airmass-bounded multi-FoV, observatory
  interchange, exact chart-track, and four-source illumination roadmap audit.
- [`satellite_guide.md`](satellite_guide.md) — living artificial-satellite
  scientific and implementation guide maintained separately during the 50S
  foundation branch.
- [`comet_discovery_and_reporting_audit_50a5d.md`](comet_discovery_and_reporting_audit_50a5d.md)
  — active parent contract for observer-dependent comet discovery magnitude
  and natural moving-object reports.
- [`comet_model_magnitude_audit_50a5d1b.md`](comet_model_magnitude_audit_50a5d1b.md)
  — accepted scientific/provider contract for the bounded observer-dependent
  comet model-magnitude implementation.

The accepted 50A.0 through 50A.3C records and completed 50A.3D through
50A.5D.2C records are archived under
[`archive/milestone_history/50a_minor_bodies/`](archive/milestone_history/50a_minor_bodies/).
The completed 49J program and its superseded combined future-program document
are archived under [`archive/milestone_history/49j_performance/`](archive/milestone_history/49j_performance/)
and [`archive/roadmap_history/`](archive/roadmap_history/).

Do not place completed milestone records directly in this directory. Move them
to the matching archive family and update active links and documentation tests
in the same change.
