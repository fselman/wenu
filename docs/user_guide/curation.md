# Catalogue curation guide

This is the living guide for catalogue curation in Wenu. Update its script
registry, commands, parameter definitions and acceptance record whenever a
curation script or supported filter changes. Work on open clusters first;
globular clusters and supernova remnants are subsequent, separate stages.

## Standard working-data workflow

Use these locations for all new work:

| Location | Contents |
|---|---|
| `src/wenu/data/catalogs/<catalogue>/` | Scientific source catalogues, original downloads and their provenance |
| `src/wenu/data/observing_lists/<list>/` | Observing-group selections, original files, converted CSVs, README and provenance |
| `output/<experiment>/` | Trial unions, filtered candidates, plots, summaries and review ledgers |
| `src/wenu/data/curated_catalogs/open_clusters/` | Accepted versioned Wenu catalogues, complete review/provenance bundles and active selector |

Observing selections are not uniform original scientific survey catalogues.
Their membership reflects the compilers' observing objectives; they do not
generally claim completeness. Barnard and Abell are scientific catalogues and
their acquired originals stay under `catalogs/barnard/` and
`catalogs/abell_planetary_nebulae/`, even though their names appeared in the
earlier mixed acquisition inventory.

### Tool responsibilities

| Tool | Input and output |
|---|---|
| `query_hunt_reffert2024.py` | Explicit scientific source download or verified offline source cache; prepared scientific tables under `data/catalogs/open_clusters/` |
| `migrate_catalogue_data.py` | Verify and relocate legacy sources/CSVs; optionally promote the accepted cluster bundle; preserve historical receipt bytes |
| `convert_observing_catalogues.py` | Original per-list files to per-list CSVs, immutable conversion receipts and descriptive provenance |
| `merge_open_clusters.py` | Scientific Dias/Hunt tables plus verified observing-list CSVs to a source-preserving trial union and review ledgers in `output/` |
| `curate_open_clusters.py` | Explicit trial union from `output/` to a versioned filtered candidate and selection/pairing evidence in `output/` |
| `prepare_open_cluster_catalogue.py` | Depurate a selected output candidate; separately verify and promote an accepted output bundle |
| `plot_merged_open_clusters.py` | Explicit trial ECSV, or the accepted active selector by default; plots and point ledgers in `output/` |
| `compare_open_clusters.py` | Scientific source comparisons; reads `data/catalogs/` and writes diagnostic outputs |
| `compare_planetary_nebulae.py` | Offline PN radius/H-beta comparison with verified observing-list overlays; writes all-row diagnostics under `output/` |
| `wenu_create_atlas` | Explicit accepted selector when preparing a new sky, or an existing frozen sky when redrawing it |

All CLI tools display their parameters with `--help`. The standalone catalogue
tools display help without writing when invoked without arguments.
`catalogue_data_layout.py` owns shared path resolution and provenance publication;
`observing_list_membership.py` and `observing_list_additions.py` remain the
source-specific membership/conversion owners.

### Download, convert, iterate, review, promote

1. Download the original files into the appropriate named scientific catalogue
   or observing-list directory. Keep versioned filenames and record publisher,
   URL, edition, acquisition date, byte count, SHA-256 and rights information.
   Current observing sources are bound by the two pinned acquisition registries;
   changing an edition requires updated source bindings, not overwriting a file.
2. Convert observing files to CSV beside their original sources. From the
   repository root, for a fresh/unconverted pinned acquisition:

```bash
PYTHONPATH=src python tools/convert_observing_catalogues.py --source-directory src/wenu/data/observing_lists
PYTHONPATH=src python tools/convert_observing_catalogues.py --additions --source-directory src/wenu/data/observing_lists
```

   An existing completed conversion is refused. Already migrated conversions
   need no reconversion. Legacy flat folders remain readable for verification;
   new CLI publication always follows the named-list layout.
3. Build a new union, then filter and depurate into explicit experiment folders.
   Examples below use new version names; existing products are refused:

```bash
PYTHONPATH=src python tools/merge_open_clusters.py --output-directory output/cluster_union_v4 --name wenu_open_clusters_v4
PYTHONPATH=src python tools/curate_open_clusters.py --catalogue output/cluster_union_v4/wenu_open_clusters_v4.ecsv --output-directory output/curation_v0.3 --name wenu_open_clusters_v0.3
PYTHONPATH=src python tools/prepare_open_cluster_catalogue.py --catalogue output/curation_v0.3/wenu_open_clusters_v0.3.ecsv --output-directory output/depuration_v0.3 --name wenu_open_clusters_v0.3
```

   For later full unions, use `--id-registry` with the preceding full-union
   `_ids.json` to retain stable Wenu IDs. Change catalogue versions or experiment
   folders for each iteration; preserve prior results and their provenance.
4. Plot the candidate explicitly and inspect selection, identity and positional
   ledgers. The membership priority and numeric filters are documented below:

```bash
PYTHONPATH=src python tools/plot_merged_open_clusters.py --catalogue output/depuration_v0.3/wenu_open_clusters_v0.3.ecsv --x radius --output-directory output/depuration_v0.3/plots --name radius_v10_v1
PYTHONPATH=src python tools/plot_merged_open_clusters.py --catalogue output/depuration_v0.3/wenu_open_clusters_v0.3.ecsv --x members --output-directory output/depuration_v0.3/plots --name members_v10_v1
```

5. Only after acceptance, promote the complete bundle without filtering again:

```bash
PYTHONPATH=src python tools/prepare_open_cluster_catalogue.py --promote-catalogue output/depuration_v0.3/wenu_open_clusters_v0.3.ecsv --activate
```

   Promotion verifies every recorded product hash, copies ECSV/CSV, the summary
   and review ledgers into `src/wenu/data/curated_catalogs/open_clusters/`, and
   atomically updates the relative `open_star_clusters.ecsv` selector. Trial
   outputs remain unchanged. Different existing bytes are refused; identical
   accepted bundles can be reused. A regular selector file is never overwritten.
   No scientific source, observing-list membership or catalogue selection is
   recalculated during promotion.

Plot the active accepted version by omitting `--catalogue` from the merged plot
tool. Prepare a new atlas with
`--open-cluster-catalogue src/wenu/data/curated_catalogs/open_clusters/open_star_clusters.ecsv`.
An existing saved sky remains self-contained and can still be reused with
`--from-sky`; moving the original data does not rewrite its historical source
paths or hashes. Working observing/curated trees are excluded from automatic
package discovery. An installed Wenu reads the explicitly selected working
catalogue path, so data acceptance does not require a software rebuild.

### Migrating the current files

From the repository root:

```bash
PYTHONPATH=src python tools/migrate_catalogue_data.py --legacy-directory src/wenu/data/catalogs/observing_lists --accepted-catalogue output/curation_v0.2/wenu_open_clusters_v0.2.ecsv
```

The migration verifies all acquired and converted files against their existing
receipts before copying. Each observing list receives its own named folder,
README and provenance. Historical registries/receipts are unchanged; aggregate
membership indices and conversion receipts use original/additions versioned
filenames at the new root. Source and converted CSV bytes may share one file
when they are identical. Source-specific identifiers and list counts do not
change. The 45 legacy source/CSV/receipt files map to the new layout without
discarding evidence. The four obsolete flat folders are removed only after
verified copies exist.

The accepted v0.2 bundle is promoted intact and selected at the curated path.
The old top-level `data/catalogs/open_clusters/` version/selector is removed
only when it matches the accepted bytes; empty obsolete parents are then
removed. Other top-level data is preserved. `output/`, saved skies and atlases
remain untouched. A migration receipt records the final product hashes.


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
| `tools/merge_open_clusters.py` | Offline source-preserving union and cross-identification compiler, separate from curation | Reads complete supplied Dias/Hunt tables and observing references; writes a versioned candidate ECSV/CSV, crosswalks, ID registry and receipt only when invoked |
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
route additionally supports strict fifth-member `--max-v5` and tenth-member
`--max-v10` criteria. Unknown values fail their supplied cut; if both cuts
are supplied, both must pass. Discuss the
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


## Tenth-member comparison (V10)

Choose `--y v10` and `--max-v10 11` to apply the same strict apparent-magnitude
threshold to the tenth-brightest accepted member in converted Johnson V.
The default p>=0.5/tidal member policy, observed-colour conversion, IR/E marks,
E(B-V) handling, alias crosswalk and source hashes are identical to the V5 route.
Fewer than ten valid converted members yields missing V10: retain the row with
`missing_V10` as its exclusion reason when this cut is supplied. Without the
cut, selected objects missing V10 remain in the plot's categorical margin.
The source V10 column is already packaged; no download or rebuild is needed.

Use `--catalogue hunt-reffert2024` for this comparison. The `hunt-curated`
preset is still the named V5<11 source subset, so it would preselect on V5.
The V10 candidate is a separate `_filtered.ecsv`, with `max_v10` and any other
criteria retained in its selection metadata. Both member cuts, if supplied,
combine by logical AND; the axes themselves never impose a magnitude cut.

```bash
(
  set -e
  cd /Users/fselman/odrive/Dropbox/software/wenu
  review_dir="$(mktemp -d "$HOME/Downloads/wenu-hunt-v10-v3.XXXXXX")"

  PYTHONPATH=src MPLBACKEND=Agg python tools/compare_open_clusters.py \
    --catalogue hunt-reffert2024 --output-directory "$review_dir" \
    --name hunt_diameter_v10_ebv3_v3 \
    --x diameter --y v10 --max-ebv 3 --write-filtered-catalogue

  PYTHONPATH=src MPLBACKEND=Agg python tools/compare_open_clusters.py \
    --catalogue hunt-reffert2024 --output-directory "$review_dir" \
    --name hunt_v10lt11_ebv3_v3 \
    --x diameter --y v10 --max-ebv 3 --max-v10 11 \
    --write-filtered-catalogue

  open "$review_dir"
)
```


## Wenu open-cluster union: software before curation

The logical database name is `wenu_open_clusters`. The developer tool
`tools/merge_open_clusters.py` compiles a candidate union; it does not create an
accepted clean database, replace a source catalogue, select attractive targets,
change chart/atlas defaults or merge software. Fernando requested that this
software milestone precede a separate curation stage. During development only
explicitly synthetic inputs are compiled in tests. Real-catalogue generation,
identity decisions, filtering, accepted parameter choices and adoption wait for
the later curation request. No final combined database is committed now.

The default inputs are the current packaged Dias 1,931-row normalized snapshot
and the full Hunt 7,167-row prepared table. All rows/types in those inputs are
represented exactly once: unflagged, infrared, embedded, moving-group,
globular, rejected and other rows are not removed by this compiler. Dias's
original source had 2,166 entries, and Wenu's existing normalization had already
excluded 235. The tool cannot restore those upstream rows; `--dias-catalogue`
accepts another normalized source retaining a fuller population. The receipt
records input counts, source hashes, source metadata and this input-scope limit.

### Column order and scientific meaning

| Column group, in order | Contents |
|---|---|
| `wenu_id`, `RA`, `Dec` | Wenu identity and displayed ICRS centre, in degrees |
| `dias_id`, `dias_*` | Original Dias name and every source parameter, including source RA/Dec, units, masks and classifications |
| `hunt_id`, `hunt_name`, `hunt_*` | Original numeric Hunt ID, source name and every source parameter/derived member statistic; existing `hunt_type`/`hunt_note` names remain prefixed only once |
| `Messier_id`, `Caldwell_id`, `NGC_id` | Source/reference identifications; multiple claims are pipe-separated |
| `IC_id`, `Melotte_id`, `Collinder_id`, `Other_ids` | Additional source identifiers and the retained complete name/alias set |
| `RA_source`, `position_epoch`, `match_method`, review/source flags | Provenance, match reason, unresolved claims and source-presence diagnostics |

RA/Dec use Hunt when present, otherwise Dias, without averaging or epoch
propagation. Both source coordinates remain separately available. Hunt retains
its supplied J2016.0 epoch. A Dias source position epoch is not inferred from
its J2000 coordinate/equinox description; `position_epoch` is unknown there,
and the original source metadata remains authoritative. This policy is explicit
in the candidate receipt; a later curation stage may adopt another position.
Physical parameters are never averaged or silently coalesced: Hunt's 2r50
and AV50/3.1 proxy remain distinct from Dias's diameter and E(B-V).

### Identity matching and stable Wenu IDs

The compiler shares identifier normalization and observing crosswalks with
`compare_open_clusters.py`. Exact source primary matches take precedence.
After reserving those pairs, only reciprocal unique published-alias pairs are
combined. Position proximity alone never merges objects. One-to-many,
many-to-one, competing alias claims and references requiring review remain
explicit. Source rows within the same catalogue are not collapsed. A compound
reference such as C14 annotates its two components and never merges them into
one cluster. All observing-reference types may annotate retained source rows;
this does not declare non-open Hunt aggregates to be accepted open clusters.

`wenu_id` uses the `WOC00000001` form. A first run assigns deterministic IDs
from source keys; reorderings do not change those assignments. For later
updates, supply the prior `_ids.json` with `--id-registry`: new sources receive
new IDs, old IDs are retained, and inactive registry entries are not deleted.
A proposed merge of two existing Wenu IDs or split of one ID fails closed for
review. A registry is therefore essential for stable identity across added
catalogue records; restarting without it is a new identity allocation, not a
safe update. Duplicate source keys and invalid registries are rejected.

### Help and outputs

Calling the script without arguments displays help and creates nothing.

| Option | Responsibility |
|---|---|
| `--data-directory` | Root of packaged source/reference catalogues |
| `--dias-catalogue`, `--hunt-catalogue` | Explicit alternate normalized ECSV inputs; all supplied rows are retained |
| `--id-registry` | Preserve existing IDs using the previous registry |
| `--dias-diameter-column` | Angular Dias diameter for positional audit; default `apparent_diameter_arcmin` |
| `--hunt-diameter-column` | Angular Hunt diameter for positional audit; default `apparent_diameter_arcmin` (2r50); alternatives `tidal_diameter_arcmin` and `total_diameter_arcmin` |
| `--output-directory` | Separate candidate destination; never an automatic installed-database replacement |
| `--name` | Versioned prefix such as `wenu_open_clusters_v1`; must end `_vN` |

Outputs are `<name>.ecsv` (authoritative typed candidate), `<name>.csv`
(readable copy), `<name>_crosswalk.csv` (matched/review source pairs),
`<name>_references.csv` (observing-reference assignments/ambiguities),
`<name>_positions.csv` (positional audit of identity pairs and other passing pairs),
`<name>_ids.json` (persistent identity registry) and `<name>_summary.json`
(source/product digests, counts, policy and completion receipt). Missing source
parameters are masked, not zero-filled scientific values. Existing products
are refused. The summary is written last; its absence marks an interrupted
candidate rather than a complete compilation. Source catalogues remain intact.

Actual compilation commands and clean-database decisions will be supplied in
the separate curation stage, at Fernando's request. Source integrity and
coverage can be assessed then without merging software or automatically
accepting ambiguous physical identities.

### Positional coincidence audit

Each explicit compilation also audits the original published source centres,
using spherical angular separation (including RA wrap and polar geometry).
The strict criterion is separation < Dias radius AND separation < Hunt radius.
Each radius is half the selected source diameter, converted to arcminutes.
Columns with angular units are converted; unitless diameter columns are
interpreted as arcminutes and unitless RA/Dec as degrees. Missing diameter
columns or incompatible units are errors before output creation. Missing,
masked, nonfinite or nonpositive radii and invalid centres are unassessable;
they never pass. Supplied centres are compared without epoch propagation.

The default Hunt radius is r50, its half-member radius; the Dias source radius
has a different definition. This is an audit using the selected catalogue
quantities, not proof of common identity. The two diameter-column options allow
explicit alternative angular boundaries, recorded in the receipt. No positional
pair changes the identifier union, existing Wenu IDs or curation status.

The printed audit and the summary's `positional_audit` report identifier-matched
pairs separately as pass, fail and unassessable. Other passing pairs are split
into `both_unmatched` (neither source row has an accepted identifier match) and
`matched_elsewhere` (at least one row is already matched to another object).
Each category reports pair count and distinct Dias/Hunt cluster counts. Their
combined counts are also supplied, deduplicating objects across categories.
One cluster can have several positional neighbours; pair count therefore need
not equal cluster count. Invalid/missing centre and radius counts are given for
each source; these diagnostics can overlap for the same row.

The `_positions.csv` ledger contains every established identifier pair, including
failed/unassessable pairs, and every other passing positional pair. It retains
source and Wenu IDs, both centres, angular separation, both radii, category and
positional status. Nonidentified pairs that fail or cannot be assessed are not
expanded into a full Cartesian ledger. No-argument help describes the options,
criterion, output meanings and usage. Real-catalogue execution remains the
separate curation step requested by Fernando.

## Observing-list source acquisition, version 1

Fernando requested the source catalogues before deciding which objects belong
in Wenu's public/beginner selection. The versioned download
`wenu_observing_catalogues_v1.zip` contains 18 source-table files, with the
inventory/provenance ledger `observing_sources_v1.json` and validation counts.
The same ledger is tracked under
`src/wenu/data/observing_lists/observing_sources_v1.json`.
Each product records its source URL, publisher, retrieval time, byte count,
SHA-256, edition/count distinctions and any extraction from a parent source.
Archive source files are separate from installed chart resources. This stage
does not filter attractive targets, cross-identify physical objects, introduce
a sky layer or change atlas defaults. The existing Messier/Caldwell parameter
resources and their earlier provenance remain intact.

### Verified inventory and corrections to the earlier table

| Catalogue/list | Acquired source and count | Meaning and review distinction |
|---|---|---|
| [Messier](https://old.astroleague.org/al/obsclubs/messier/messlist.html) | AL table, 110 numbered entries; factual CSV | Existing HEASARC Wenu parameter table has 109 rows and omits M102. The additional observing membership does not resolve its disputed physical identification. |
| [Caldwell](https://old.astroleague.org/al/obsclubs/caldwell/cldwlist.html) | AL table, 109 entries; factual CSV | Existing OpenNGC-backed resource and CC BY-SA 4.0 provenance retain parameter authority. Mixed object types and compound entries remain distinct. |
| [Herschel 400](https://www.astroleague.org/herschel-400-observing-program/) | NGC-order PDF, 400 rows; southern XLS supplement, 150 | Publisher accepts manual NGC1750 or online NGC7814. This snapshot follows the online list. Southern certification combines 150 supplementary with 250 original targets. |
| [Herschel II](https://www.astroleague.org/herschel-ii-observing-program/) | 2020 NGC-order PDF, 400 rows | Confirmed replacements NGC1985, NGC4517, NGC7492; removed NGC1750, NGC1990, NGC2253 absent. |
| Best of the NGC | Alias of SAC below in this inventory | The earlier table supplied no distinct publisher/source for this generic name; it is not counted as an independently verified additional list. |
| [RASC Finest NGC](https://rasc.ca/finest-ngc-objects) | Checklist 2.1a (2021-06-19), PDF; 110 base observing numbers, 112 displayed object rows | Number 82 has two object rows; 99 has a/b components. Other compound identifications are retained in the original checklist. Observing target count is not a physical-object count. |
| [SAC 110 Best of the NGC](https://www.saguaroastro.org/110-best-ngc-objects/) | A.J. Crayon/Steve Coe, version 1.0 (1990-01-04), factual CSV; 111 distinct NGC rows | Publisher title says 110. Preserve the 111 supplied rows and this distinction rather than removing one to fit the title. Source prose/descriptions are omitted from the CSV. |
| [AL Open Cluster Program](https://www.astroleague.org/open-cluster-observing-program/) | Complete-list XLSX dated 2025-10-04; 125 original + 89 southern = 214 rows | Programme page advertises 90 supplementary objects. This workbook contains 89 southern rows. Membership does not guarantee current scientific classification as an open cluster. |
| [AL Globular Cluster Program](https://www.astroleague.org/globular-cluster-observing-program/) | 2021-11-16 XLSX; 190 regular object rows plus 8 challenge rules | 50 is the observing requirement, not the source catalogue size. Challenge rules can describe classes/groups rather than individual catalogue objects. |
| [AL Planetary Nebula Program](https://www.astroleague.org/planetary-nebula-observing-program/) | Standard XLSX 110 rows; southern XLS 110; northern-alternate XLS 26 | Repeated spreadsheet headers are not objects. Four optional proto-PN mentioned on the page are absent from this standard workbook; no rows are invented for them. Southern list preserves publisher corrections. |
| [AL Double Star Program](https://www.astroleague.org/double-star-observing-program/) | June 2026 XLSX, 200 numbered systems | 100 is the award requirement. June 2026 expanded the list to include southern targets. Source URL's `202660628` filename is retained literally. |
| [AL Multiple Star Program](https://www.astroleague.org/multiple-star-observing-program/) | Appendix 2026-03-16 XLSX, 115 systems | Supersedes the earlier 114 count. Worksheet title still says `Current List 20200510`; that stale title does not determine the acquisition edition. |
| [Barnard](https://cdsarc.cds.unistra.fr/viz-bin/cat/VII/220A) | CDS VII/220A; 349 object rows in VizieR TSV, separate notes TSV and ReadMe | Barnard 1927, NAOJ electronic compilation, diameters/notes supplied by Bill Gray, position corrections through 2008-06-30. Names have gaps and suffixes; CDS `recno` is not an object ID. |
| [Abell planetary-nebula candidates](https://doi.org/10.1086/148602) | G.O. Abell, ApJ 144,259 (1966), Table 2; 86 entries in two original scanned table pages | Extracted from NASA ADS's historical paper scan. Historically provisional PN classifications are preserved. Acquisition is complete as a scanned catalogue; numeric normalization requires verified transcription, not unreviewed OCR. |

### Source fidelity and provenance

The AL, RASC and SAC lists are observing memberships, not physical catalogues
or proof that every entry is a beginner showpiece. Herschel II and Abell in
particular contain difficult objects. Keep programme membership, source
classification, accepted scientific classification and future visual selection
as separate attributes. Compound observing entries must not silently collapse
their constituent objects in the future crosswalk.

Source coordinates, magnitudes, diameters, stellar component separations and
position angles remain publisher values. They are not homogenized measurements
or current double-star ephemerides. Barnard's TSV explicitly preserves FK4
B1875 and FK5 J2000 systems. Abell's table labels its positions 1950. Neither
resource is silently interpreted as native ICRS. Later adapters must document
their position/epoch transformations within Wenu's canonical pipeline.

All Excel/PDF source lists are retained unchanged. The Messier, Caldwell and
SAC webpages are represented by factual table CSV extractions; the ledger binds
them to the downloaded parent-page URL/hash. Narrative observing descriptions
are not reproduced. Abell's catalogue-table PDF preserves only original Table
2 pages 10-11 of the parent scan (printed pages 268-269); its parent URL/hash
and extraction are recorded. OCR text is not shipped as accepted coordinates.

The Barnard FTP `.dat` requests returned HTTP-200 HTML anti-bot pages, which
failed content validation and were excluded. The documented public VizieR ASU
interface supplied the actual 349-row table and notes. This is recorded as a
source-format choice; HTTP success alone never establishes a valid catalogue.

Public download availability is not treated as a new redistribution licence.
The source files remain acquisition/review material; the ledger records rights
status separately from origin and scientific validation. AL and RASC copyright
notices are preserved in their original files. No third-party guide or image
collection is incorporated into Wenu's distributed scientific resources at this
stage. Later curation, licence decisions, membership normalization and chart
integration are explicit subsequent work.

## First CSV pass and cluster-list membership

Fernando requested CSV conversion before membership integration, and then
limited the current milestone to star clusters. `tools/convert_observing_catalogues.py`
therefore handles the nine acquired files for Messier, Caldwell, Herschel 400,
Herschel II, RASC Finest NGC, SAC Best NGC, AL open clusters, AL globular clusters
and the southern Herschel supplement. The original complete rows of mixed
lists remain intact. PN, Abell, Barnard and double/multiple-star programme work
is deferred; their acquired originals remain untouched.

The converter reads the installed `observing_lists` directory and
verifies each relevant source against `observing_sources_v1.json`. It produces
10 per-list source CSVs and root `observing_memberships_original_v1.csv`, with
`conversion_receipt_original_v1.json` binding source registry, source and output hashes.
There are 1,796 source-list membership records; they are not deduplicated
physical objects. Globular challenge rules remain a separate CSV sheet rather
than eight invented object memberships. Existing conversion receipts and differing product bytes are refused.
Conversion is staged and verified before publication beside the list sources.

Excel sheets retain their complete stored cell grid, including blank rows,
titles and repeated headers; `source_row` and `source_column_N` locate every
original cell. Each nonempty sheet has its own CSV. These are first-pass
source grids, not yet typed homogeneous scientific parameter tables. PDF CSVs
expose identity and source-coordinate fields while preserving the original row
and unparsed tail. No unknown coordinate, magnitude, diameter or classification
is silently imputed. CSV sources retain their factual fields. Parameters from
these observing lists do not replace the separate Dias/Hunt source columns.

No-argument invocation displays help and writes nothing. Usage from the
repository root is:

```bash
PYTHONPATH=src python tools/convert_observing_catalogues.py \
  --source-directory src/wenu/data/observing_lists
```

The default destination is `src/wenu/data/observing_lists`.
`--output-directory` chooses a fresh directory; `--registry` selects the
acquisition registry. XLSX conversion uses the Python standard library; PDF
conversion uses Wenu's existing pypdf dependency. The legacy southern XLS
requires the optional maintenance dependency `xlrd>=2,<3` (install with
`python -m pip install 'xlrd>=2,<3'`). Merge compilation reads the resulting
CSVs and needs no Excel reader.

`tools/merge_open_clusters.py` defaults to that CSV directory. It verifies the
conversion receipt and every CSV digest before adding the membership columns:

| Column | Source list |
|---|---|
| `in_messier` | Messier membership, using the existing observing crosswalk |
| `in_caldwell` | Caldwell membership, using the existing component crosswalk |
| `in_herschel400` | Original Herschel 400 list |
| `in_herschel2` | Herschel II 2020 list |
| `in_rasc_finest_ngc` | RASC Finest NGC checklist |
| `in_sac_best_ngc`, `in_best_ngc` | Same SAC selection; the generic title is an alias |
| `in_al_open_clusters` | Original and southern AL open-cluster rows |
| `in_al_globular_clusters` | The 190 regular AL globular entries |
| `in_herschel400_south` | The separate 150-object southern supplement |

True means a resolved explicit identifier membership; false means no resolved
identifier in that list; masked means an unresolved competing claim. False is
not proof of physical absence when an object has unrecognized aliases. Source
primary names take precedence over aliases, with competing claims preserved.
Explicit abbreviations such as Berk/Berkeley, Ru/Ruprecht, Tr/Trumpler and
Cr/Collinder are normalized. Extragalactic globular names retain their host
scope. Questioned/mislabeled narrative identifiers are not adopted as aliases.
RASC's explicitly named companions and Caldwell's C14 components remain
separate physical rows with membership in their observing target.

Messier/Caldwell flags use the established reference crosswalk rather than
reinterpret approximate historical AL associations: e.g. M45 is not assigned
to a cluster by treating NGC1432 as the Pleiades, and M24 is not silently
equated with NGC6603. The CSV source fields preserve those published values
for review. No list membership is inferred from proximity to a star system.

`--observing-directory` overrides the CSV location. Missing conversions fail
before output creation. `--without-observing-lists` explicitly skips loading
and emits masked membership columns, never false absences. The separate
`<name>_observing.csv` ledger records per-source designation, resolved Wenu IDs
and review IDs, including unmatched targets. Summary/metadata record list
counts and the conversion receipt. Boolean annotations change neither source
pairing nor stable IDs, parameter values, positional audit or chart defaults.
Only synthetic union tests are generated during software development; the
real first-pass CSV conversion is permitted by Fernando's separate instruction.


## Observing-list additions: purpose, objects and conditions (v1)

Wenu uses these lists to help select observing targets and annotate their
provenance. They are selections for different observing goals, not uniform
all-sky surveys or interchangeable measures of completeness. Membership in
several lists is retained; a plot's first-match symbol is only a presentation
choice. A successful sighting, resolving individual stars, and seeing fine
structure are different observing tasks.

### The seven requested lists

Counts below are verified against the downloaded source files, not inferred
from programme names or the number of observations required for an award.

| List | Acquired entries | Objective and object characteristics |
|---|---:|---|
| Herschel 400 Southern | 150 supplementary targets (already installed) | Southern replacements for inaccessible northern Herschel 400 targets. Mixed deep-sky objects; combine these 150 with at least 250 original targets for the southern programme. |
| SAC 110 Objects Beyond the NGC | 110 | Explore other designations: clusters, galaxies, nebulae, galaxy clusters and a quasar. A heterogeneous selection: bright wide clusters such as Collinder 140 and Melotte 111 coexist with faint or low-contrast targets. |
| SAC Urban List | 100 fixed targets; 10 observer-chosen targets are not a predefined catalogue | A programme for light-polluted metro-Phoenix skies. Contains open/globular clusters, double and variable stars, planetary nebulae, galaxies and other nebulae. |
| SAC Red Stars v2.0 | 333 | Enjoy stellar colours. Includes cool stars and carbon stars, many variable; colour index, spectral classification and brightness are preserved. This is larger than the older 70-star web list. |
| SAC Asterisms v3.2 | 114 | Recognizable patterns of stars, not necessarily bound clusters. Angular extent determines whether naked eye, binoculars, or a telescope provides a useful field. Published positions, sizes and magnitudes are approximate. |
| AL Carbon Stars, June 2026 workbook | 100 main + 28 southern | Observe stellar colour and variability. Brightness changes with phase; identifying the correct star and recording colour are central tasks. The southern sheet is preserved separately in the source workbook. |
| AL Dark Nebulae | 35 required + 105 optional | Recognize obscuring clouds against a luminous background. Programme completion requires the 35 required objects plus 35 chosen from the optional set, not every optional target. Includes named large features such as the Great Rift, which has no single centre. |

Sources: [SAC Beyond the NGC](https://www.saguaroastro.org/110-objects-beyond-the-ngc/),
[SAC Urban](https://www.saguaroastro.org/the-urban-list/),
[SAC downloads](https://www.saguaroastro.org/sac-downloads/),
[AL Carbon Stars](https://www.astroleague.org/carbon-star-observing-program/),
[AL Dark Nebulae](https://www.astroleague.org/dark-nebula-observing-program/),
and [AL Herschel 400/Southern](https://www.astroleague.org/herschel-400-observing-program/).
The acquisition registry supplies exact download URLs, editions, timestamps,
byte lengths and SHA-256 digests. Publisher upload timestamps are not taken
as the scientific edition dates.

### Urban skies and southern coverage

The SAC list was selected for Phoenix. Its 100 fixed rows include 26 targets
with negative declination; M41, NGC2362, M6 and M7 provide southern examples.
The southernmost target is M7, at the published declination −34°48′. Thus it
includes southern objects but leaves the far-southern sky outside its coverage.
The title's 110 consists of 100 fixed entries plus 10 chosen by the observer.
The programme defines its urban setting by the Milky Way being invisible to
the unaided eye; this does not guarantee every target in every urban sky.

Computed from the source declinations at latitude −32.443342° (La Ligua),
87 fixed targets rise geometrically and 63 culminate at least 20° high.
This uses h_max = 90° − |latitude − declination|; it excludes terrain,
refraction, season, weather and sky brightness. It is an accessibility check,
not an observing-success prediction. The source's NGC2244 row has malformed
fields (`+04 57 O`, type `C`); first-pass CSV preserves these for review.

### What “challenging” means

Do not interpret an entire list as a single difficulty category. For clusters,
compare member magnitudes (including V10), concentration, angular size,
extinction, altitude and background. Integrated magnitude alone does not
predict whether individual members will be visible. Diffuse galaxies and
nebulae depend strongly on surface brightness and sky contrast. Stellar
colour lists depend on current variable-star brightness, field identification
and the observer's colour perception. Large asterisms require a sufficiently
wide field. Dark nebulae need a visible background and are not a general urban
recommendation. Distinguish catalogue measurements from individual observer
reports; no universal `difficulty` value is added to Wenu.

### Were the Herschel lists compiled by William Herschel?

William Herschel compiled the historical observations from which many NGC
entries originate. The Herschel **400** is a modern subset selected by the
Ancient City Astronomy Club of St Augustine, Florida. Herschel **II** is
another modern 400-object programme, introduced in 1997 and maintained by the
Rose City Ancient Astronomers. Neither modern 400-target checklist was chosen
by William Herschel. The southern 150 is a modern programme supplement.

Herschel II is predominantly galaxies, with most targets at magnitudes 11–13;
its purpose includes careful identification and technical descriptions. That
makes completion more demanding than a showpiece list, without implying all
of its clusters are unusually hard. The publisher describes an 8-inch
instrument under good dark skies as suitable for much of the list and suggests
10 inches or more for completing it. See [Herschel II](https://www.astroleague.org/herschel-ii-observing-program/).

### Other acquired lists

Messier supplies familiar mixed deep-sky targets; Caldwell broadens the
selection, including southern targets. RASC Finest NGC and SAC Best NGC are
showpiece selections with different memberships; the generic “Best of NGC”
label in Wenu aliases SAC rather than creating a third independent source.
The AL open-cluster programme emphasizes comparing star-cluster appearance;
the globular programme emphasizes compact stellar systems. The double- and
multiple-star programmes concern stellar systems, not physical open clusters.
Planetary-nebula programmes and Abell concern planetary nebulae; Barnard is a
historical dark-nebula catalogue. Their full raw sources remain acquired, but
planetary-nebula conversion/adoption is deferred as requested. These original
files and counts are documented in the existing acquisition inventory.

### Data, conversion and cluster membership

Keep additions in their named list directories under `observing_lists/`.
The immutable registries and conversion receipts retain the historical acquisition grouping.
The additions contain seven original source snapshots for six lists, seven
CSVs including the membership index, and a conversion receipt. CSVs preserve
source values without imputing modern positions or astrophysical properties;
dark-nebula CSVs contain designation/coordinate facts, while original PDFs
retain the full tables and commentary.

To reproduce conversion offline from the repository root:

```bash
PYTHONPATH=src python tools/convert_observing_catalogues.py \
  --additions \
  --source-directory src/wenu/data/observing_lists \
  --output-directory /path/to/new/observing_lists
```

The merged cluster tool automatically reads the supplementary CSV directory
when installed. `--observing-additions-directory` overrides that location;
an explicitly supplied missing or corrupt directory fails before writing.
Absent supplementary lists produce masked flags, not false absences.
New columns are `in_sac_urban`, `in_sac_beyond_ngc`, `in_sac_red_stars`,
`in_sac_asterisms`, `in_al_carbon_stars`, and `in_al_dark_nebulae`.
Only explicit primary designations are used for these additions. A note saying
that a red star or asterism lies near a cluster does not tag that cluster.
Original non-cluster targets stay in their own list and unmatched ledger;
they never become extra rows in the Dias–Hunt cluster union.

### Radius–V10 comparison with one symbol per object

`tools/plot_merged_open_clusters.py` reads the combined ECSV and exports
PNG/SVG/PDF, a point ledger and a summary. Each source point receives the
symbol of its first true membership flag, starting with Messier and Caldwell.
The remaining priority is a configurable observing preference; Urban is the
next default because of the requested urban emphasis. `--priority` replaces
the order with comma-separated supported list names. Filled points use Dias
radii, hollow points use Hunt radii; radii are half each chosen diameter.
Matched Dias points share Hunt-derived V10. Dias-only objects have no V10 and
remain in the separate missing-V10 panel, not assigned a synthetic magnitude.

```bash
PYTHONPATH=src python tools/plot_merged_open_clusters.py \
  --catalogue /path/to/wenu_open_clusters_v2.ecsv \
  --output-directory /path/to/new/plots --name wenu_radius_v10_v1 \
  --max-v10 11 --max-ebv 3
```

V10 < 11 is strict; E(B−V) ≤ 3 is evaluated separately for each source.
Missing reddening under that cut is excluded and logged. Omitting either cut
removes that filter. All tools print help and write nothing with no arguments.
This work does not adopt a curated database, change sky charts or merge the
software branch.


### Member-count axis and the three comparison plots

`tools/plot_merged_open_clusters.py --x members` plots original
`dias_member_count` and `hunt_member_count` directly against Hunt-derived V10.
It does not halve counts or replace Hunt's published N with the smaller
accepted-member subset used for photometry. The source counts have different
membership definitions and should be interpreted as separate catalogue
measurements. Radius remains the default (`--x radius`); it is half each
selected published diameter. Both x-axis choices use a logarithmic scale;
nonpositive, missing or nonfinite x values are excluded and logged. V10,
reddening cuts, source masks, first-list priority and no-V10 panel retain
their existing meanings. Point exports preserve radius, member_count and
the actual x_value; the summary records the selected axis/source columns.
No-argument help lists both axis choices.

Fernando selected three views: radius versus V10 with E(B−V)≤3; the same
with the strict V10<11 cut; and member count versus V10 with E(B−V)≤3.
The source/catalogue inputs stay under `src/wenu/data/catalogs`; an unadopted
combined candidate can be generated under `output` and reused by all three
plots. Running from `tools` uses `PYTHONPATH=../src`,
`--data-directory ../src/wenu/data/catalogs` for the merge, and relative
`../output/...` destinations. There is no need to move the candidate into
the installed data directory or to download another catalogue.


### Wenu open-cluster selection v0.1

`tools/curate_open_clusters.py` creates Fernando's explicit first selection
from a full combined ECSV. The confirmed mandatory lists are Messier,
Caldwell, SAC Urban, **RASC** Finest NGC (`rasc_finest_ngc`, correcting the
request's `rsac` spelling), and SAC Best NGC. Every resolved cluster row in
these lists is retained regardless of magnitude, radius, reddening or missing
V10. Unresolved list claims are also retained with an explicit review reason;
this avoids silently excluding a possible mandatory object. This is a
selection of the supplied cluster union, not the insertion of every galaxy,
star or nebula in the original observing lists.

Additional objects must satisfy the intersection of:

- finite Hunt-derived V10 strictly brighter than 12.5;
- V10 < 17.5 − (12.5/3) log10(radius in arcmin), the line through
  (1,17.5) and (1000,5) on the logarithmic radius axis;
- source-specific E(B−V) ≤ 3, with missing reddening excluded;
- positive finite radius and member_count, so the point is assessable in both
  radius and member-count views. There is no additional member-count threshold.

“Above” refers to the inverted magnitude axes, hence the less-than inequalities.
Fernando confirmed both available Dias/Hunt points must pass for an additional
object (`--source-policy all`); a single-source object uses its one available
point. Dias-only objects without a Hunt V10 cannot pass the numeric selection,
but mandatory membership still retains them. The plotted V10<11 restriction
is explicitly not inherited. The line is extrapolated outside 1–1000 arcmin.
`--source-policy any`, `--max-v10`, `--max-ebv`, and `--without-ebv-cut` permit
explicit later alternatives, which are recorded in the outputs.

Primary/alias pairs from the union remain intact. The curation tool also
checks every cross-source positional pair using the published centres and
half each apparent diameter (Hunt r50). Only reciprocal unique, otherwise
unmatched Dias–Hunt pairs inside both radii are combined provisionally.
Existing alias ambiguities remain review flags, not erased by coincidence.
Competing positional candidates and pairs involving an object already matched
elsewhere remain separate. `--position-match audit-only` checks positions
without combining them. The retained Wenu ID is the smaller of the two existing
IDs; `previous_wenu_ids` and summary redirects preserve both input IDs. The
union ID registry is not modified, and no epoch propagation is performed.

The CSV has a normal first-row header and preserves both catalogue parameter
blocks and identifiers. Explicit `selection_*` columns record source origin,
mandatory lists, unresolved claims, numerical pass/reason for each source,
line-boundary values, the final selection reason and a readable criteria string.
The input ECSV digest is included. An ECSV companion preserves units, masks
and original source/list provenance for the existing plotting tool. Separate
selection and pairing ledgers include excluded rows and remaining ambiguity;
the completion JSON records criteria, counts, input digest, ID lineage and
product digests. Existing versioned products are refused. No arguments prints
help and writes nothing.

From `tools`, using the full candidate generated for the three plots:

```bash
PYTHONPATH=../src python curate_open_clusters.py \
  --catalogue ../output/open_cluster_comparison_v3/wenu_open_clusters_v3.ecsv \
  --output-directory ../output/curation_v0.1 \
  --name wenu_open_clusters_v0.1

PYTHONPATH=../src MPLBACKEND=Agg python plot_merged_open_clusters.py \
  --catalogue ../output/curation_v0.1/wenu_open_clusters_v0.1.ecsv \
  --output-directory ../output/curation_v0.1/plots \
  --name selected_radius_v10_v1 --x radius
```

For a member-count check use `--x members` and a distinct output prefix.
Do not reapply the global magnitude/reddening cuts when inspecting the full
selection: they would hide mandatory-list exceptions. The existing plot
continues to distinguish filled Dias and hollow Hunt values and show missing
V10 separately.

The verified packaged-source run starts with 7,873 union rows, finds seven
additional provisional positional pairs (with 13 competing unmatched edges
left for review), and selects 583 rows: 142 resolved mandatory-list rows,
27 rows retained for unresolved mandatory claims, and 414 further numeric-only
rows. Categories in this count are disjoint for this run; general per-criterion
flags may overlap. Of the seven positional pairs, one is retained in the
selection. Positional matching remains provisional and the 27 list-claim rows
require review. This v0.1 output is a requested curation snapshot; it is not
installed as a sky-chart source and does not merge the software branch.



## Depuration and atlas installation of the selected catalogue

Software and catalogue curation remain separate. Keep the v0.1 selection and
publish a new v0.2, retaining its source identifiers, coordinates, memberships,
selection criteria and unresolved identity flags. This amateur open-cluster
layer contains Hunt type o and Dias-only open clusters. Hunt globular clusters
and moving groups are excluded; the existing globular atlas database remains
unchanged. Single-source objects without another catalogue designation or
resolved observing-list membership are excluded. Masked membership claims stay
for review. All modern catalogues, including OC, count; an HSC name alone does
not provide another compilation.

For the reviewed v0.1 input, 583 rows become 513: 48 globular clusters, 17 moving
groups and five HSC-only entries are excluded. The latter are HSC 1865, 2304,
2384, 2764 and 2911. The retained source counts are 328 both, 4 Dias-only and
181 Hunt-only. Absence means absence of corroboration in the installed source
resources, not absence from all astronomical literature.

Run from the repository's tools directory:

```bash
PYTHONPATH=../src python prepare_open_cluster_catalogue.py --help
PYTHONPATH=../src python prepare_open_cluster_catalogue.py \
  --catalogue ../output/curation_v0.1/wenu_open_clusters_v0.1.ecsv \
  --output-directory ../output/curation_v0.2 \
  --install-directory ../src/wenu/data/curated_catalogs/open_clusters \
  --activate
```

The output contains ECSV, CSV, a row-by-row depuration ledger, all passing
source-centre comparisons in a positions ledger, and a summary with input and
product hashes. The seven retained overlap pairs are review candidates, not
seven confirmed duplicates. Separations and both published diameters are in
arcminutes; radius is half the supplied diameter. All Dias/Hunt combinations
are checked, including two positions from the same source. No epoch propagation
or additional identity merge occurs. 76 retained rows carry identity-review
flags; they remain available for scientific inspection.

The accepted working directory is the curated_catalogs tree, excluded from
automatic package discovery. Each version is immutable. The relative symlink
`src/wenu/data/curated_catalogs/open_clusters/open_star_clusters.ecsv` selects
`wenu_open_clusters_v0.2.ecsv`. An installed Wenu can read this same directory;
without an explicit installation directory, activation uses
`src/wenu/data/curated_catalogs/open_clusters`. A regular file at the selector path
is never overwritten. Selecting a different version changes the symlink only;
old versions remain available. Catalogue generation and activation are explicit,
and ordinary Wenu defaults continue to use the packaged catalogue.

Plot the new output ECSV with `plot_merged_open_clusters.py` using the same
radius/member/V10 options as before. To recreate the atlas, run from the
repository root with the existing design, index, presentation and stellar
options, adding:

```bash
--open-cluster-catalogue src/wenu/data/curated_catalogs/open_clusters/open_star_clusters.ecsv
```

Use a new output directory and a new saved-sky directory. Do not reuse an old
`--from-sky` bundle: it contains its original open-cluster database. The
catalogue override resolves the symlink once and reaches the existing sky
preparation profile. The saved sky records the actual source hash and retains
source columns/masks; all workers read the same prepared objects. No other
catalogue, atlas layout, symbol styling or stellar setting is replaced.
V10 remains a selection statistic and is never interpreted as integrated V.
Geometry IDs are Wenu IDs; display labels retain catalogue names. Programmatic
`OpenClusters(selected=[...])` accepts Wenu IDs as well as display names.


## Angular sizes for atlas open-cluster symbols

Open-cluster symbols use the catalogue diameter at the central scale of the
chart. The displayed diameter in millimetres is the larger of:

- The existing styled symbol diameter (the minimum).
- Catalogue diameter in arcminutes / 60, multiplied by the chart's central
  scale in millimetres per degree.

Hunt entries use diameter 2*r50, the adopted half-member radius doubled;
Dias-only entries use the Dias diameter. This is a source-defined size, not a
tidal boundary. Missing, masked or nonpositive sizes retain the minimum symbol.
The central scale is used throughout each chart, without a local correction
for projection distortion. Star sizes, other object symbols, labels, colours,
outline widths and catalogue contents are unchanged. The deep-sky symbol scale
continues to control the minimum; it does not multiply catalogue-derived sizes.

Angular sizes are the atlas default. Use `--open-cluster-size angular` explicitly,
or `--open-cluster-size fixed` to reproduce the previous fixed symbols. The
presentation TOML equivalent is `open_cluster_angular_sizes = true` or false.
The atlas CLI help describes this choice.

The accepted v0.2 saved sky can be reused: omit `--open-cluster-catalogue` and
`--save-sky`, and supply
`--from-sky output/atlas_open_clusters_v0.2/native_sky_v1`. Keep the same design,
presentation and stellar settings, choose a new output directory, and reuse
the existing index. This redraws the current catalogue without reinstalling or
recurating it. The existing per-chart report records the central scale used.

## Planetary-nebula observing-list comparison

`tools/compare_planetary_nebulae.py` is an offline diagnostic. It retains all
1,143 Strasbourg-ESO/HEASARC rows and highlights the same broad observing lists
used for open-cluster comparisons, plus the AL planetary-nebula standard,
southern and northern-alternate lists. It performs no final visual selection,
catalogue promotion or atlas change.

Default first-list priority is Messier, Caldwell, SAC Urban, RASC Finest NGC,
SAC Best NGC, Herschel 400 South, Herschel 400, Herschel II, SAC Beyond NGC,
AL Planetary Nebulae, AL Planetary Nebulae South, AL Northern Alternates.
One symbol is assigned per nebula; every resolved membership remains in the
table. The displayed legend counts describe disjoint first-list groups in the
main panel, not total list memberships. Use `--priority` with comma-separated
supported keys to change the display preference.

```bash
PYTHONPATH=src MPLBACKEND=Agg python tools/compare_planetary_nebulae.py \
  --output-directory output/planetary_nebulae_comparison_v1 \
  --name planetary_nebulae_comparison_v1
```

No arguments prints help without writing. `--view flux|surface-brightness|both`
selects the view; both is the default. `--data-directory` selects scientific
sources; `--observing-directory` selects the named-list working tree.
Output names must end in an explicit `_vN` version. Existing products are
refused. Legacy AL workbooks use the existing Excel reader and require
`xlrd>=2,<3`; the existing tools already use this optional dependency.

The x axis is optical angular radius in arcminutes, half the Acker diameter.
The y axes are observed H-beta flux and a mean H-beta surface-brightness proxy:

```text
log10(S_Hbeta) = log_hbeta_flux - log10(pi*(60*radius_arcmin)^2)
```

Flux is in erg s-1 cm-2, numerically equivalent to mW m-2; the surface proxy
is per square arcsecond. HEASARC's primary quantity documentation was checked
on 2026-10-14 at
[PLNEBULAE](https://heasarc.gsfc.nasa.gov/W3Browse/nebula-catalog/plnebulae.html).
H-beta is not V magnitude or [O III] flux. No extinction correction is applied.
The surface quantity assumes a circular optical aperture, is not an
independently measured surface brightness, and may mix flux/diameter apertures.
These are exploratory optical diagnostics, not guarantees of eyepiece visibility.
Central-star magnitudes and heterogeneous list magnitudes are not substituted.

Missing data are retained in labelled margins and the ledger, never imputed.
Diameter limits remain limits and do not enter measured-radius main panels;
uncertain diameters are plotted with hollow symbols. A missing flux does not
mean radio-only, and reference-list membership does not prove visual visibility.

The source and reference ECSV digests are verified against adjacent provenance.
Broad memberships reuse the existing original/additions conversion loaders.
The three original AL workbooks are verified against their per-list provenance
and parsed only in identity columns, with exact counts 110, 110 and 26.
Explicit PN G and PK signs are retained. Abell/A, Jonckheere/J, Hubble/Hb,
Jones/Jn and Pease/Ps are catalogue-name expansions. Consecutive combined NGC
designations retain both explicitly named components; parenthetical host
names such as M15 in Pease 1 are not nebular aliases. Published combined
identity cells are split without using narrative nicknames or positions.
Conflicting identifiers remain ambiguous and do not acquire resolved membership.

Outputs are `_catalogue.csv/.ecsv`, `_crosswalk.csv`, `_summary.json`, and
`_radius_hbeta_flux.png/.svg/.pdf` plus the corresponding
`_radius_hbeta_surface-brightness` files. CSVs have a normal first-row header.
The summary records the exact Git commit, command, source/conversion hashes,
quantity definitions, missing/limit policy, all-list counts and product hashes.
It is written last. Raw scientific and observing resources are unchanged.

At base `8f91504aa399635c80f46159d3c6b8e20d57f737`, verified source parsing
finds 178 distinct rows with resolved list membership, including all four
Messier and 13 Caldwell planetary nebulae. There are 796 main-panel points,
128 measured-radius rows without H-beta flux, 195 flux-bearing rows without
usable measured radius, and 24 unavailable in both axes. The surface-proxy
view has 219 unavailable in both axes because it requires a measured area.
The AL standard list resolves 109 of 110 rows; Sh 2-216 is unmatched in this
historical snapshot. Four southern-list records have conflicting published
identity fields: NGC 3918, Shapley 1, NGC 6302 and NGC 6445. Their positive
PN G latitude fields disagree with the negative-latitude objects claimed by
their other identifiers. Preserve both candidates for review, without silently
correcting the publisher's source. General-list unmatched records often describe
other physical object types; they are not all missing planetary nebulae.

### Candidate inclusion and public-interest review

Add `--write-selected-catalogue` to export Fernando's first PN selection:
resolved membership in any reference list OR finite observed log H-beta flux
strictly greater than -12. `--min-log-hbeta` changes only the latter threshold.
Membership bypasses the flux cut, including missing flux or size; diameter
limits do not remove a flux-qualified object. An unresolved list claim does
not create resolved membership, but a candidate may qualify independently by
its measured flux. All-row selection reasons and identity-review flags remain.

The verified input selects 319 of 1,143 rows: 178 reference-list objects and
141 additional H-beta-only objects, with 824 excluded. The full comparison
plots remain intact, with a dashed flux boundary and its mapped surface-proxy
curve. No separate surface-brightness inclusion cutoff is applied.

New products are `_selected.csv`, `_selected.ecsv` and `_public_review.csv`.
The public review table contains the selected objects in decreasing finite
surface-brightness order, with missing values last, stable identifier ties,
angular sizes and explicit diameter-quality flags. This ordering is a review
aid, not public approval. Every `public_interest` flag remains false and its
`public_review_status` is unassessed. False here means not approved, not an
assessed rejection. Fernando specifically considers even M57 challenging for
newcomers: only the highest-surface-brightness objects may be public targets,
if any. Very small high-surface-brightness nebulae still require evaluation.
No public numerical cutoff, visual guarantee or atlas adoption is inferred.

```bash
PYTHONPATH=src MPLBACKEND=Agg python tools/compare_planetary_nebulae.py --output-directory output/planetary_nebulae_selection_v1 --name planetary_nebulae_selection_v1 --write-selected-catalogue --min-log-hbeta -12
```

### Promote planetary-nebula v1 and prepare a new atlas

Use the same mechanism as the open-cluster catalogue: separately promote a
verified selected bundle, activate a relative selector, then pass that selector
when preparing a new atlas sky. This is not another filtering operation.

```bash
PYTHONPATH=src python tools/compare_planetary_nebulae.py --promote-catalogue output/planetary_nebulae_selection_v1/planetary_nebulae_selection_v1_selected.ecsv --activate
```

The default destination is `src/wenu/data/curated_catalogs/planetary_nebulae`.
Every completion-summary product and the summary itself is preserved, with
checksum, selected-row/count, unique-identity and finite-position validation.
Existing identical bytes can be reused; different versions and regular
selector files are refused. `planetary_nebulae.ecsv` is an atomically updated
relative symlink to the versioned selected ECSV. Original output experiments
remain unchanged. `--curated-directory` permits an explicit destination.

Add `--planetary-nebula-catalogue src/wenu/data/curated_catalogs/planetary_nebulae/planetary_nebulae.ecsv`
to `wenu_create_atlas`, alongside the existing `--open-cluster-catalogue`.
Both selectors resolve once and reach `CelestialSphereLoadProfile`; the existing
native snapshot hashes the actual sources for every worker. Use new output
and saved-sky directories. A catalogue override with `--from-sky` is rejected
because the saved sky retains its earlier catalogue. No geometry, presentation,
stellar sizing, other catalogue or rendering owner is changed. The PN layer
retains selection/list/public-review columns as metadata without filtering again.
