# Wenu developer-document archive

This directory preserves superseded architecture, migration, and design
documents as historical evidence. Archived documents are not current
architectural authority and assistants must not read them routinely when
planning ordinary work.

Use the active documents in the parent directory for current decisions:

- `current_architecture_v0.8.md` records the implemented baseline;
- `target_architecture_v0.9.md` records the active product target;
- `wenu_migration_0.8_to_0.9.md` records the active migration;
- `post_v0.9_architecture_roadmap.md` records accepted future directions;
- `implementation_reference.md` and `source_tree.md` record current APIs and
  responsibilities.

The archive is organized by purpose:

- `architecture_history/` contains versioned implemented baselines and target
  architectures superseded by the current baseline;
- `migration_history/` contains completed version-to-version roadmaps;
- `pre_versioned/` contains the original unversioned architecture, roadmap,
  and UML material;
- files directly under this directory are older milestone records retained
  from the repository's initial archive layout.

Consult an archived document only to investigate provenance, recover the
reason for an old decision, or maintain a compatibility contract that names
it explicitly. Moving a document here does not delete its history or revoke
an implemented public compatibility promise.
