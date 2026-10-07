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

## Accepted policy and report resources

The label/report candidate activates explicit name/Bayer selectors and optional
reports; see developer audit section 11. `research.json` is byte-identical to
the authored 77-case dossier merged in PR #206. `research_policy.json` records
Fernando’s accepted handling policy and twelve explicit shared-star preferences.
`research_manifest.json` binds both by SHA-256 and records their origin/base.
This separate manifest does not alter the original Wikidata snapshot, compiler,
review ledger or its digest. New research loading verifies those two resources
once and exposes an immutable HIP index; report callers receive independent
records. The compiler continues to rebuild only the frozen Wikidata resources.
The research is authored commentary and comparison evidence, not installation
of another astrometric catalogue. Source links and publication cautions remain
in each case. Missing Wikidata assignments remain missing.
## Authored name associations

The optional `name_associations` collection in `curation.json` binds exact
names to one HIP and canonical constellation, with matching Bayer identity,
component scope, basis and source URLs. These are authored associations,
separate from the immutable Wikidata snapshot and its labels/aliases.
`StarDesignations.curated_names` retains their evidence; explicit selection
uses them and the existing report note exposes their component scope.

Albireo is associated with HIP 95947 (β¹ Cyg), verified against the IAU WGSN
HR 7417 / Aa entry and SIMBAD HIP cross-identification on 2026-10-07.
The Wikidata system item Q67622059 lists both HIP 95947 and HIP 95951, so it
does not justify assigning this name to HIP 95951 (β² Cyg). The latter keeps
its existing curated Bayer identity. No source claim or position is rewritten.
