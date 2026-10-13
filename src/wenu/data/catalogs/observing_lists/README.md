# Observing-list acquisition registry

`observing_sources_v1.json` records the 2026-10-13 source-acquisition milestone
for Fernando's requested amateur target catalogues. It inventories 13 distinct
catalogues/lists and the generic Best of the NGC alias, with 18 downloaded or
source-table derivative products in `wenu_observing_catalogues_v1.zip`.

The registry contains publisher/edition URLs, source and derivative hashes,
retrieval times, byte counts, count/classification/coordinate distinctions,
source rights status and rejected HTML responses. Source list documents stay
in the separate acquisition archive; this directory is a provenance registry,
not a newly installed sky catalogue. No resource loader or chart default
consumes these files. Existing Messier/Caldwell scientific parameter resources
remain authoritative for their current chart roles.

The owning user instructions and full corrected inventory are in
[`docs/user_guide/curation.md`](../../../../../docs/user_guide/curation.md).
Source acquisition, future membership normalization, physical cross-identities,
visual target curation and chart integration remain separate stages. Scanned
Abell Table 2 is acquired but is not yet an accepted machine-readable parameter
table. No redistribution licence is inferred from public download availability.

Fernando installed the 18 checked originals under `sources_v1/`. The current
cluster-focused first CSV pass is owned by `tools/convert_observing_catalogues.py`:
nine relevant files become 10 source CSVs plus a hash-bound membership index in
`csv_v1/`. These local source/CSV directories are not committed automatically.
`tools/observing_list_membership.py` owns exact-name memberships and review
ledgers; `tools/merge_open_clusters.py` reads the verified CSV receipt and adds
10 membership flags, including the SAC/Best-NGC alias and southern Herschel
supplement. PN, dark-nebula and double/multiple-star programme conversion is
deferred. See the owning guide for formats, help and optional legacy-XLS reader.
