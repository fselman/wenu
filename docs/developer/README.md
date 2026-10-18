# Wenu developer documentation

**Current baseline:** main `6708f54a0d8984c0be348b2c8cb02b311646a02b`, 2026-10-17.
PR #234 is integrated. Its tree is identical to `ea8dc505`, which passed all
3,606 plugin-disabled Mac tests in 1,136.74 s; 16 overlay tests passed in 4.03 s.

## Read for current work

| Document | Authority |
|---|---|
| [Current architecture](current_architecture_v0.9.md) | What the code does now; known missing barriers |
| [Implementation reference](implementation_reference.md) | Existing API entry points and extension owners |
| [Source tree](source_tree.md) | Complete production-module inventory |
| [Scientific contracts](scientific_contracts.md) | Current scientific invariants and capability limits |
| [Coordinate guide](coordinate_system_guide_v0.9.5.md) | Scientific vocabulary, mathematics and calendars |
| [Configuration schema](configuration_schema_v2.md) | Implemented schema-v2 configuration |
| [Satellite guide](satellite_guide.md) | Satellite science and current limitations |
| [Testing policy](testing_policy.md) | Focused verification now and module independence target |
| [As-is migration audit](kernel_migration_audit_v1.md) | Current functionality, pinned source/test inventory and continuous test migration |
| [Proposed kernel contract K1](kernel_contract_k1.md) | Proposed SDK types, operations, capabilities, errors and conformance gates |
| [Assistant instructions](assistant_instructions.md) | Contribution and delivery workflow |

## Forward work

[Roadmap to v0.9.5: kernel and loadable packages](kernel_roadmap_v0.9.5.md)
is the single active forward roadmap. Both architecture diagrams are in that
document and in the [diagram index](diagrams/README.md).
It starts with Gaia DR3, prepares a DR4 adapter, requires every existing
functionality to use the kernel, and then extracts one package at a time.
This is a plan, not a claim that the kernel or Gaia integration exists.
The [K1 contract](kernel_contract_k1.md) is the current review candidate;
its acceptance precedes the bounded K2 synthetic-provider implementation.

The `v0.9.5` name is provisional. The old document with this version in its
title described the completed 49B/49C coordinate work, not this new kernel.
Its [original edition](archive/pre_kernel_20261017/docs/developer/target_architecture_v0.9.5.md)
is archived. Release naming must be confirmed before a tag is made; no package
version, release tag or runtime is changed by this documentation cleanup.

## Curation and unresolved science

The [stellar designation review](stellar_designation_review.md) and its
[ledger](data/stellar_designations_review.json) retain Fernando's review cells.
The [research dossier](data/stellar_designation_research/README.md) remains
available. Blank historical decisions do not block the accepted label policy.
Current source-data, selection and promotion workflows are in the
[curation guide](../user_guide/curation.md).

Minor-body automatic-name/provisional selection and satellite Moonlight,
brightness and detector science remain incomplete. They are paused behind the
kernel work; completed history is not an instruction to resume them.

## Archive

[Archive index](archive/README.md) preserves earlier architecture, proposals,
receipts and superseded instructions. The
[cleanup ledger](documentation_cleanup_v1.json) records exact original Git
blob identities and old-to-new paths. Read historical material only when its
scientific detail or provenance is needed; do not append milestone diaries to
the current architecture, coordinate guide, API reference or source map.
