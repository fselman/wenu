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
