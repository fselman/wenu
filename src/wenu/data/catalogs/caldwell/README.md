# Caldwell observing catalogue

All 109 Caldwell designations are retained. Membership is a factual
cross-identification ledger checked against the Astronomical League's
[Caldwell list](https://old.astroleague.org/al/obsclubs/caldwell/cldwlist.html)
on 2026-10-13. The historical reference is Patrick Moore, *Beyond Messier:
The Caldwell Catalog*, Sky & Telescope, December 1995. No observing-guide
descriptions or images are reproduced.

Coordinates, dimensions, B/V photometry, object types and field-source codes
come from Mattia Verga's [OpenNGC](https://github.com/mattiaverga/OpenNGC)
release `v20260501`. The normalized parameter catalogue is distributed under
CC BY-SA 4.0; the licence is included. It is a mixed observing list, not a
physical object category, and is not automatically enabled in atlas charts.

Canonical data: `caldwell_openngc.ecsv`; inspection derivative:
`caldwell_openngc.csv`; source and product hashes:
`caldwell_openngc.provenance.json`. The membership ledger separately preserves
observing identifiers, cluster components and related aliases. C14 denotes
NGC 869 and NGC 884 together; C41 matches Dias's Melotte 25. C50 preserves
NGC 2244 while OpenNGC supplies parameters under NGC 2239; C37 likewise
preserves NGC 6885 with parameters under NGC 6882. These alternate Dias rows
remain explicit review cases in the comparison, not automatically merged.
C100 includes a cluster with nebulosity. Missing magnitudes are not inferred,
and OpenNGC diameters need not use the same aperture definition as Dias.

Regenerate the pinned catalogue with `python tools/query_caldwell_openngc.py`.
Run the entirely offline comparison from the repository root:

```bash
PYTHONPATH=src python tools/compare_open_clusters.py --output-prefix open_clusters_comparison_v1
```

The comparison emits all Dias rows with membership tags, a component crosswalk
including unmatched/ambiguous/alternate-alias cases, and a summary of available
parameters. Every comparison sample uses Dias parameters; it does not mix
photometry or angular diameters from different sources or change chart density.
