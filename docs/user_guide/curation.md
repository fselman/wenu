# Catalogue curation guide

This is the living guide for catalogue curation in Wenu. Update its script
registry, commands, parameter definitions and acceptance record whenever a
curation script or supported filter changes. Work on open clusters first;
globular clusters and supernova remnants are subsequent, separate stages.

## Preserve sources and record decisions

Keep the packaged source catalogues intact. Mark excluded objects and record
why; export a separate candidate catalogue when requested. A candidate export
does not automatically replace the installed catalogue or become an atlas
selection. Record the exact Wenu commit, source hashes, command, criteria,
missing-value policy and manual-review decisions for each candidate.

Current working choice: exclude explicitly flagged infrared/embedded clusters
and use an inclusive **E(B−V) ≤ 3** ceiling. This replaces 0.5 as our working
comparison ceiling, not the underlying source values. No integrated-magnitude
or surface-brightness cutoff has yet been adopted. The CLI applies no reddening
bound unless one is supplied. The subsequent Hunt & Reffert workflow below
adopts converted fifth-member V < 11, separately from integrated magnitude.

## Script registry and input data

Run scripts from the repository root with Wenu installed and `PYTHONPATH=src`.

| Script | Responsibility | Inputs and outputs |
|---|---|---|
| `tools/compare_open_clusters.py` | Offline membership comparison, marking, configurable two-parameter plot and candidate export | Reads packaged catalogues under `src/wenu/data/catalogs/`; writes versioned products under `output/` by default |
| `tools/query_caldwell_openngc.py` | Explicit maintenance of Caldwell membership/parameters | Reads the versioned membership ledger and pinned OpenNGC files; writes Caldwell resources and provenance |
| `tools/query_hunt_reffert2024.py` | Explicit serial CDS acquisition or verified offline cache preparation | Writes full Hunt and V5<11 candidate ECSV resources plus provenance under `open_clusters/`; raw members stay outside the repository |
| `tools/hunt_reffert_catalogue.py` | Offline CDS parsing, Gaia conversions, member statistics and Hunt comparison adapter | Shared developer-tool helper, not a chart layer or stellar-position provider |
| `tools/query_open_cluster_photometry.py` | Explicit maintenance of the separate Dias V-photometry supplement | Reads Dias and pinned OpenNGC files; writes the supplement and its provenance under `open_clusters/` |

The Dias/HEASARC snapshot contains 1,931 retained rows. It provides positions,
angular diameter, distance, E(B−V), log age, estimated member count, metallicity,
kinematics and some Trumpler classifications, with incomplete coverage.
Its infrared-discovery and embedded flags mark 344 and 5 rows respectively.
These flags are positive evidence, not a complete modern classification of
every cluster; an unflagged object is not guaranteed to be unobscured.

The separate OpenNGC v20260501 supplement supplies V magnitudes for 317 Dias
rows. Do not substitute member count for integrated brightness. Messier and
Caldwell specify reference membership; the plotted physical quantities come
from the same Dias rows, and brightness from the same supplement, for all
three samples. C14 has two cluster components. C37 and C50 have other alias
rows requiring identity review. Matching is by explicit identifiers and
aliases, never by a nearest-position guess.

Read the catalogue README files and adjacent provenance JSON before changing
a source or its interpretation. The supplement is bound to the exact Dias and
photometry file digests; mismatches stop the comparison.

## First comparison: diameter versus observed brightness

On Fernando's Mac:

```bash
(
  set -e
  cd /Users/fselman/odrive/Dropbox/software/wenu
  review_dir="$(mktemp -d "$HOME/Downloads/wenu-open-clusters-ebv3-v4.XXXXXX")"

  PYTHONPATH=src MPLBACKEND=Agg python tools/compare_open_clusters.py \
    --data-directory src/wenu/data/catalogs \
    --output-directory "$review_dir" \
    --name open_clusters_ebv3_v4 \
    --x diameter --y brightness \
    --max-ebv 3 --missing-ebv exclude \
    --write-filtered-catalogue

  open "$review_dir"
)
```

The fresh directory prevents accidental overwriting. For another checkout,
run the following from its root; defaults read the packaged data and write
under `output/`. Use a fresh versioned name on every rerun:

```bash
PYTHONPATH=src MPLBACKEND=Agg python tools/compare_open_clusters.py \
  --name open_clusters_ebv3_richness_v4 \
  --x diameter --y members \
  --max-ebv 3 --missing-ebv exclude \
  --write-filtered-catalogue
```

With the current sources, the first command selects 1,526 rows, including
all 29 Caldwell cluster components and 27 Messier clusters. Only 317 selected
rows have both diameter and V magnitude: 24 Caldwell and 26 Messier components.
The missing-value margins account for the other 1,209 selected rows.
These are catalogue-snapshot checks, not permanent target counts.

## Choose axes and reddening policy

| Axis name | Quantity | Display |
|---|---|---|
| `diameter` | Dias apparent diameter, arcmin | Logarithmic |
| `brightness` | Supplement integrated apparent V magnitude | Linear; brighter up/right |
| `members` | Dias estimated membership, a richness proxy | Logarithmic |
| `distance` | Dias heliocentric distance, pc | Logarithmic |
| `ebv` | Dias E(B−V), mag | Linear |
| `log_age` | Dias log10 age in years | Linear |
| `metallicity` | Dias [Fe/H], dex | Linear |
| `physical_diameter` | Derived projected diameter, pc | Logarithmic |

Choose two different names with `--x` and `--y`.
Derived physical diameter is `2 d tan(theta/2)`; it inherits the source
distance and diameter uncertainties.

`--min-ebv` and `--max-ebv` are inclusive bounds.
With a bound present, `--missing-ebv exclude` excludes unknown reddening;
`--missing-ebv include` retains it as unknown, never as zero. Without either
bound, missing reddening does not exclude an object. Use
`--include-infrared-embedded` only for an explicitly labelled comparison of
the excluded population. All reference groups follow the same selection.

Missing plotted values remain in the annotated and selected catalogues and
appear in labelled plot margins. Non-positive logarithmic values cannot occupy
the main panel. Legend counts describe the main panel; the title describes the
whole selection. No missing measurements are imputed.

## Products and candidate review

| Suffix | Contents |
|---|---|
| `_dias.csv` | All 1,931 source rows plus membership, photometry, exclusion flags and selection reasons |
| `_crosswalk.csv` | Reference components and matched, ambiguous or unmatched identities, including alias-review cases |
| `_summary.json` | Selection, counts, parameter availability, source hashes and photometry provenance |
| `_figure.png`, `_figure.svg`, `_figure.pdf` | Raster, editable vector and publication versions of the comparison |
| `_filtered.ecsv` | Selected copy, written only with `--write-filtered-catalogue`; includes selection and source provenance |

Start by reviewing `in_amateur_sample`, `selection_exclusion_reason`,
`photometry_status`, `photometry_identity_review`, source identifiers and
notes. Audit lost Messier/Caldwell objects as well as selected Dias-only objects.
Keep accepted/rejected/uncertain manual decisions in a separate versioned
ledger with identifier, reason, evidence and date. Unknown data and rejected
objects are different states.

The Dias route filters infrared/embedded flags and reddening. It does **not**
expose integrated-magnitude, surface-brightness or Trumpler cutoffs. The Hunt
route additionally supports the strict fifth-member `--max-v5` criterion. Discuss the
meaning and missing-value policy before adding those options; do not describe
a planned filter as installed. The atlas presentation option
`open_cluster_exclude_infrared_embedded` controls only that flag-based
selection, not the candidate export's reddening ceiling.

## Why many Dias objects overlap the reference samples

Messier and Caldwell are observing lists, not exhaustive surveys or a uniform
cut in diameter and integrated magnitude. Caldwell deliberately complements
Messier. Lack of reference membership is not evidence that a cluster is
uninteresting. See [NASA's Caldwell overview](https://science.nasa.gov/mission/hubble/science/explore-the-night-sky/hubble-caldwell-catalog/).

For visual selection, investigate concentration, brightness range of members,
the number of members brighter than an instrument's limiting magnitude,
contrast against the local stellar field, nebulosity, and angular extent
relative to the eyepiece field. Total catalogue membership does not measure
how many stars a small telescope resolves. Trumpler classification is a useful
next diagnostic where available; the [Astronomical League open-cluster
program](https://www.astroleague.org/open-cluster-observing-program/) explicitly
uses it and records observing equipment and conditions. These are proposed
discriminants, not established Wenu selection thresholds.

First inspect identity and measurement quality: the same photometric source
can be attached to multiple source rows, and source diameters or integrated
fluxes may describe different apertures. Review those cases before inferring
that coincident plotted positions imply comparable visual appearance.

## Integrated magnitude and surface brightness: next experiment

For a circular aperture of diameter D arcmin, a mean V surface-brightness
proxy would be:

```text
mu_V = m_V + 2.5 log10(pi (30 D)^2)   [mag per square arcsecond]
```

This follows from spreading total flux over the aperture area. Smaller
values mean brighter mean surface brightness. It is a deterministic transform
of our existing diameter/magnitude axes: it can describe a selection boundary,
but adds no independent measurement to that plane.

Our current D and V come from different catalogue sources with potentially
different apertures. Treat this as an exploratory proxy, not measured cluster
surface brightness. Do not use OpenNGC's galaxy surface-brightness field for
open clusters. Resolved clusters also require information about individual
members and field contrast; a smooth-source threshold is insufficient.

Observed V already contains extinction. Combining an E(B−V) screen with an
observed-V cutoff is possible, but do not dim V a second time or substitute a
dereddened intrinsic magnitude as a direct measure of eyepiece visibility.
Before adopting a cutoff, compare retained/lost reference objects, missing
photometry, source-review cases and representative Dias-only clusters.
No numerical V or surface-brightness threshold is accepted at this stage.

## Regenerating sources is separate maintenance

Ordinary comparisons are offline and require no regeneration. Maintenance
scripts overwrite their destination resources, so use a separate candidate
data directory, retain attribution/licences and review diffs and hashes before
publishing any resource change. To reproduce using a local pinned-source cache:

```bash
PYTHONPATH=src python tools/query_caldwell_openngc.py \
  --source-directory /path/to/pinned-openngc-v20260501 \
  --output-directory /path/to/candidate-data/caldwell

PYTHONPATH=src python tools/query_open_cluster_photometry.py \
  --source-directory /path/to/pinned-openngc-v20260501 \
  --data-directory /path/to/candidate-data
```

The cache must contain the exact pinned `NGC.csv` and `addendum.csv`;
Caldwell maintenance also requires `CC-BY-SA-4.0.txt`. Caldwell maintenance reads the membership ledger from the installed repository
source directory even when its output directory differs. Prepare the candidate
open clusters directory with the unchanged Dias ECSV before running the second
command.
Without `--source-directory`, these tools explicitly download the pinned
release. A source digest mismatch stops the build; never silently substitute
a newer release.

## Extending this guide

For each new script or filter, document its owner, input paths, units,
measurement/derived/proxy status, defaults, missing-data policy, source and
licence, complete commands, outputs and validation. Add new object categories
only after their sources and scientific meanings are reviewed. Record accepted
criteria separately from experiments and keep original catalogue rows intact.



## Hunt & Reffert (2024): member-based curation

Source: Emily L. Hunt and Sabine Reffert, *Improving the open cluster census.
III. Using cluster masses, radii, and dynamics to create a cleaned open cluster
catalogue*, A&A 686, A42 (2024),
[paper DOI](https://doi.org/10.1051/0004-6361/202348662),
[CDS J/A+A/686/A42](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/A+A/686/A42).
The source has 7,167 aggregates and 1,291,929 member rows; types `o`, `m`, `g`,
`d`, `r` distinguish open clusters, moving groups, globular clusters, distant
unclassified objects and rejected objects. Full source rows remain retained.

The default member policy is **probability >= 0.5 inside the estimated King
tidal radius** (`inrt=1`). This is an initial reproducible policy, not a claim
that all accepted members are certain. The maintenance command can instead
use Jacobi-radius members or all published members, and a different probability
threshold. Every prepared product records the policy; rebuild into a fresh
candidate data directory when changing it. Gaia IDs remain decimal strings.

The curated resource contains source type `o` objects with **V5 strictly <11**.
V5 is the fifth-brightest member after converting each star and ranking in V;
it is not the V magnitude of the fifth-brightest star ranked in G. G5, B5 and
R5 have their own rankings and retained fifth-member Gaia IDs. Missing colours
and out-of-domain conversions remain missing. Five valid members are required;
missing other members can move V5 to a fainter value. A retained cluster has
at least five accepted members with valid estimated apparent V <11.

### Prepare the data once

The full source-backed Mac build is published at `7ff3a4031577bfb47a84a97340cdd153351b6540`.
All 7,167 aggregates and 1,291,929 member records passed source validation;
431 type-o clusters satisfy converted V5 <11 under p>=0.5/tidal selection.
The complete members.dat.gz is 389,517,674 bytes, SHA-256
`cd9cef40b3c5586579611fdf1034e927ea157acfdc8250a1fc502e6105fec794`.
Prepared full/curated tables and their digest-bound provenance are now packaged;
ordinary comparisons require no source download. The command below is for
explicit regeneration into a fresh candidate data directory; use
`--data-directory` to choose that directory. Existing prepared resources are
refused, so the original first-build command must not be rerun over the installed
resources. No incomplete member file is accepted as a full catalogue.

Run this explicit acquisition from the Mac repository root. It requests each
CDS file once, serially, without automatic retries or per-star queries. Cache
files are external, with hashes and retrieval receipts; existing caches and
prepared outputs are refused. Interrupted files carry `.partial`, and no
complete receipt is published. A large download may take substantial time.

```bash
(
  set -e
  cd /Users/fselman/odrive/Dropbox/software/wenu
  source_dir="$HOME/Downloads/wenu-hunt-reffert2024-source-v2"
  PYTHONPATH=src python tools/query_hunt_reffert2024.py \
    --download-directory "$source_dir" \
    --data-directory "$HOME/Downloads/wenu-hunt-candidate-data-v2"
)
```

For a complete previously acquired cache, replace `--download-directory` with
`--source-directory`; every original source digest is checked before parsing.
The full build requires the published cluster/member counts and exact record
widths. The cache retains ReadMe, clusters.dat.gz, members.dat.gz,
crossma.dat.gz and receipt.json. Only compact prepared tables go under data.
The source original tables are never replaced by the candidate export.

### Help, catalogue selection and plotting

Both commands display their help and exit successfully without arguments:

```bash
PYTHONPATH=src python tools/compare_open_clusters.py
PYTHONPATH=src python tools/query_hunt_reffert2024.py
```

Choose `--catalogue dias`, `--catalogue hunt-reffert2024` (all prepared rows,
with non-open types marked outside the review selection), or
`--catalogue hunt-curated` (the prepared V5<11 subset). The first is the default.
Hunt plotting is entirely offline and requires the prepared resources above.
Hunt member-only axes are rejected on the Dias route.

```bash
(
  set -e
  cd /Users/fselman/odrive/Dropbox/software/wenu
  review_dir="$(mktemp -d "$HOME/Downloads/wenu-hunt-v5-v1.XXXXXX")"
  PYTHONPATH=src MPLBACKEND=Agg python tools/compare_open_clusters.py \
    --catalogue hunt-reffert2024 \
    --data-directory src/wenu/data/catalogs \
    --output-directory "$review_dir" --name hunt_v5lt11_v1 \
    --x diameter --y v5 --max-v5 11 \
    --max-ebv 3 --write-filtered-catalogue
  open "$review_dir"
)
```

The comparison adds positive Dias IR/E evidence through explicit primary names
and Hunt's published AllNames aliases. Unmatched classification is `unknown`,
not evidence of optical transparency. The plot still highlights Caldwell and
Messier through the existing component crosswalk; ambiguous aliases remain
unresolved. The corrected complete-source crosswalk matches all 29 Caldwell components and
27 Messier clusters, preserving additional alias claims for review.
The `_hunt.csv` preserves all input rows and selection reasons; the optional
`_filtered.ecsv` also applies the chosen reddening and IR/E criteria. This
further selection is distinct from the prepared V5-only curated resource.

| Axis | Hunt definition |
|---|---|
| `diameter` | 2*r50 in arcmin: half-members radius within tidal radius; not Dias visual diameter |
| `tidal_diameter`, `total_diameter` | 2*rt and 2*rtot in arcmin; total includes tails |
| `members`, `accepted_members` | Published N and members passing probability/aperture policy |
| `g5`, `v5`, `b5`, `r5` | Fifth-brightest valid accepted member in each band |
| `g10`, `v10` | Tenth-brightest valid accepted member |
| `brightness` | Summed converted V of valid accepted members |
| `integrated_g`, `integrated_b`, `integrated_r` | Corresponding observed member sums |
| `bright_members` | Accepted members with valid converted V <11 |
| `av` | Published median AV50 |
| `ebv` | AV50/3.1 proxy, with assumed R_V=3.1; not published E(B-V) |
| `distance`, `log_age` | Published dist50 and logAge50 |
| `physical_diameter` | 2*d*tan(theta/2), using the chosen 2r50 diameter |
| `significance`, `cmd_quality` | Published CST and median CMD classification score |
| `metallicity` | Missing for this prepared Hunt resource; never substituted |

### Gaia to Johnson B,V and Cousins R

Use the official [Gaia DR3 photometric relations, Tables 5.9 and 5.10](https://gea.esac.esa.int/archive/documentation/GDR3/Data_processing/chap_cu5pho/cu5pho_sec_photSystem/cu5pho_ssec_photRelations.html).
For observed c = BP-RP, the relations give G-band differences, so **subtract**
the polynomial from G to recover the requested band:

```text
V = G - (-0.02704 + 0.01424*c - 0.2156*c^2 + 0.01426*c^3)
B = G - ( 0.01448 - 0.6874*c - 0.3604*c^2 + 0.06718*c^3 - 0.006061*c^4)
R = G - (-0.02275 + 0.3961*c - 0.1243*c^2 - 0.01396*c^3 + 0.003775*c^4)
```

V is admitted only for -0.5 < c <5. B and R are conservatively admitted for
-0.5 < c <2 and 0 < c <2 respectively: the published redder B/R domains
require confirmed M giants, which our source fields do not establish.
Do not extrapolate or infer spectral class from colour alone. R denotes
Cousins R, not Johnson R. Polynomial fit scatter is approximately 0.03017,
0.0633 and 0.03167 mag for V,B,R; this is not a per-star uncertainty guarantee.
Observed colours and magnitudes retain extinction. AV is not subtracted.

Integrated magnitudes sum fluxes, not magnitudes, over the accepted valid
members. They omit unavailable members and stars absent from Gaia; they are
not completeness-corrected total cluster photometry. Missing counts and
V5 status are retained. Very bright stars, unresolved systems, crowding,
membership ambiguity and high extinction require review before accepting an
observability ranking. The complete-source audit retains all 29 Caldwell components and 27 Messier
clusters in the E(B-V)<=3 review plane. Adding V5<11 leaves 22 Caldwell and
23 Messier components; M11, M26, M29 and M103 fail this member-brightness
criterion. This illustrates why V5 alone is not a complete visual-appeal measure.
The IR/E and E(B-V)<=3 criteria retain 428 of the 431 bright candidates,
excluding Alessi_20 (embedded), COIN-Gaia_23 and FSR_0686 (infrared discovery).
Names with underscores, such as NGC_188, normalize to their spaced catalogue
identifiers. Primary names take precedence over published aliases; other alias
claims remain review evidence rather than duplicate selected objects.

Provider policy was checked on 2026-10-13 against
[VizieR rules of usage](https://cds.unistra.fr/vizier-org/licences_vizier.html)
and its [bulk client documentation](https://vizier.cds.unistra.fr/vizier/doc/cdsclient.html).
No numeric concurrency/rate allowance was established; use serial bulk access,
no automated retries, verified cache reuse and source attribution. Cite Hunt &
Reffert, A&A, CDS/VizieR and ESA/Gaia/DPAC. VizieR's scientific-use availability
is not a blanket CC0 or unrestricted-commercial-use declaration. The raw
source and derived resources are not silently relicensed.
