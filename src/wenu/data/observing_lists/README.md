# Observing selections

This directory contains selections compiled by observing groups and programme
organizers: Messier, Caldwell, Herschel programmes, RASC, SAC and Astronomical
League lists. They are observing selections, not uniform original scientific
survey catalogues, and do not generally establish all-sky completeness.

Each named list directory keeps versioned original source files, converted CSVs,
a README and provenance together. Provenance records retain publisher/source
URLs, retrieval dates, editions, byte counts, hashes, source descriptions and
rights observations. Existing source and conversion receipts remain unchanged.
Mixed lists may include galaxies, nebulae, stars and asterisms; membership does
not classify every object as a physical cluster.

Scientific catalogues such as Dias, Hunt–Reffert, Barnard and Abell belong under
`../catalogs/`. Accepted Wenu catalogues belong under `../curated_catalogs/`.
Trial unions, selections, review ledgers and plots belong in repository `output/`.

`observing_sources_v1.json` and `observing_additions_v1.json` bind historical
source acquisitions. The original/additions distinction remains only in those
immutable receipts and aggregate membership-index filenames, not in separate
source/CSV directory trees. Tools resolve each source/CSV by its list owner.

From the repository root, display help with:

```bash
PYTHONPATH=src python tools/migrate_catalogue_data.py
PYTHONPATH=src python tools/convert_observing_catalogues.py
PYTHONPATH=src python tools/merge_open_clusters.py
```

See `docs/user_guide/curation.md` for the maintained download → CSV → trial
curation → plot/review → accepted-promotion workflow. These working directories
are excluded from automatic package discovery; local maintenance does not
silently add bulk downloads or accepted experiments to a distribution.
