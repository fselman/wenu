# Wikidata stellar designation snapshot

Edition `wikidata-2026-10-05`; compiled offline from the frozen source-audit
responses. These are **candidates**, not scientifically approved labels.

The structured source data is CC0-1.0:
https://www.wikidata.org/wiki/Wikidata:Copyright
https://creativecommons.org/publicdomain/zero/1.0/
No prose or images from Wikimedia pages are included. Other catalogues are
comparison evidence; their values do not backfill this resource.

## Contents and limits

- 3,606 HIP-linked records, retaining separate Wikidata item identities.
- 4,864 distinct Bayer/Flamsteed statements, including deprecated evidence.
- 167 statements remain unjoined: missing, malformed or non-unique active HIP.
- English labels and aliases were queried only for the audit's 566 named HIP
  targets. They are not an exhaustive proper-name catalogue, nor automatically
  official or preferred names. Their item, language and role are preserved.
- Raw designation strings retain component suffixes, spelling and catalogue
  interpretation. No normalized Bayer selector or physical-component merge is
  implemented by this resource. A numeric catalogue claim is not independently
  certified as a historical Flamsteed designation.
- Statement rank, HIP link statements and reference URLs survive compilation.
  Claims without references remain explicit evidence. SPARQL response receipts
  freeze acquired bytes, not a consistent transaction or entity revisions.

`manifest.json` records acquisition times, input SHA-256 digests, output digest,
counts, licence, name scope and the review-ledger digest. `source/` includes the
original responses compressed losslessly with gzip, their receipts and queries.
The JSON is deterministic and is verified before use. Loading needs no network.

## Rebuild and review

From the repository root:

```sh
python tools/build_wikidata_star_designations.py
```

The compiler verifies the decompressed source bytes against acquisition
receipts. It accepts only a ledger with pending decisions and cannot apply
editorial preferences. Review 77 HIP/field discrepancies in
`docs/developer/data/stellar_designations_review.json`; all are
`pending_fernando`, with `selman: null`. The human-readable review table
`docs/developer/stellar_designation_review.md` contains the blank Selman column
for later decisions. Wikidata is used provisionally while review is deferred;
pending cases do not prevent loading. This inventory covers measured five-source designation
conflicts, not every coverage gap, proper-name disagreement or possible error.
Generic aliases and unreviewed candidates must not be silently selected as
proper names. Future decisions need an explicit separate curation layer.

`wenu.star_designations.load_star_designations()` exposes immutable candidates.
`Stars.load()` attaches them by HIP before magnitude selection;
`Stars.position()` and `Stars.spherical_geometry()` preserve aligned metadata
and the snapshot edition/digest. Hipparcos remains the position/magnitude
provider. Missing designations yield `None`, not a guessed match.

This stage does not activate labels or add CLI/TOML options. The accepted
`--star-label-name`, `--star-label-bayer` and
`--show-full-bayer-designation` remain the next implementation milestone.
