# Wenu developer-document archive

This directory preserves superseded architecture, completed migrations,
milestone records, audits, and human acceptance evidence. Archived documents
are historical evidence, not current architectural authority, and assistants
must not read them routinely when planning ordinary work.

## Active developer authority

Use the small active set in the parent directory:

- `current_architecture_v0.9.md` records the implemented baseline;
- `implementation_reference.md` records current APIs;
- `source_tree.md` records current responsibility ownership;
- `post_v0.9_architecture_roadmap.md` records active milestone sequencing;
- `assistant_instructions.md` governs contribution workflow;
- `configuration_schema_v1.md` is the active configuration schema;
- `coordinate_transformation_audit_09a2afd.md` supplies the scientific
  baseline for coordinate work;
- `wenu_cli_feature_requests.md` retains the open CLI backlog;
- `deprecations_v0.5.md` remains an active compatibility policy.

## Archive organization

- `architecture_history/` contains superseded current and target
  architectures through the accepted v0.9 design;
- `migration_history/` contains completed version-to-version roadmaps;
- `roadmap_history/` contains superseded sequencing and background roadmaps;
- `audits/` contains completed as-is, configuration, request, and test-suite
  audits;
- `acceptance_history/` contains completed visual and physical acceptance
  records;
- `milestone_history/49f_svg/` contains the completed SVG product program;
- `milestone_history/49g_temporal/` contains the completed temporal-sequence
  contracts;
- `milestone_history/49h_fixed_sky/` contains the accepted fixed-sky and
  rotating-horizon work;
- `pre_versioned/` contains the original unversioned architecture, roadmap,
  and UML material;
- files directly under this directory are older milestone records retained
  from the repository's initial archive layout.

Consult archived material only for provenance, old compatibility reasoning, or
a current contract that explicitly cites it. Moving a document here does not
delete its Git history or revoke an implemented compatibility promise.
