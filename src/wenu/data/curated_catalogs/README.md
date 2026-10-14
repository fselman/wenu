# Accepted Wenu catalogues

Maintain accepted versioned catalogues here, separately from scientific sources
and observing selections. For open clusters use `open_clusters/`, containing
ECSV/CSV, the verified provenance summary, exclusion/position review ledgers and
a relative `open_star_clusters.ecsv` selector. Original trial outputs remain in
repository `output/`.

Promote an accepted output using `tools/prepare_open_cluster_catalogue.py
--promote-catalogue PATH --activate`. Promotion verifies the complete output
bundle and preserves its bytes. Different existing versions are never
replaced; byte-identical products can be reused. The selector alone may change.
This working-data tree is excluded from automatic package discovery. An
installed Wenu reads an explicitly chosen catalogue path; adopting data does
not require changing or rebuilding its software package.

Planetary-nebula versions use the same verified-bundle mechanism under
`planetary_nebulae/`, with a relative `planetary_nebulae.ecsv` selector. Promote
with `tools/compare_planetary_nebulae.py --promote-catalogue PATH --activate`.
Promotion copies all summary-bound evidence without filtering again. Atlas
preparation uses `--planetary-nebula-catalogue` alongside the open-cluster path,
with a new sky rather than an older saved snapshot.
