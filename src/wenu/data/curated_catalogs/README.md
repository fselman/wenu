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
This tree is excluded from Python package discovery as executable code.
The general build mechanism explicitly installs verified active bundles as
package resources and makes them defaults. It preserves all bound catalogue,
selection and report bytes. Original source catalogues remain available, and
explicit paths still allow local adoption without rebuilding the package.

Planetary-nebula versions use the same verified-bundle mechanism under
`planetary_nebulae/`, with a relative `planetary_nebulae.ecsv` selector. Promote
with `tools/compare_planetary_nebulae.py --promote-catalogue PATH --activate`.
Promotion copies all summary-bound evidence without filtering again. Atlas
preparation uses `--planetary-nebula-catalogue` alongside the open-cluster path,
with a new sky rather than an older saved snapshot.
