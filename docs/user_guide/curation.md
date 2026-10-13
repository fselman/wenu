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
bound unless one is supplied.

## Script registry and input data

Run scripts from the repository root with Wenu installed and `PYTHONPATH=src`.

| Script | Responsibility | Inputs and outputs |
|---|---|---|
| `tools/compare_open_clusters.py` | Offline membership comparison, marking, configurable two-parameter plot and candidate export | Reads packaged catalogues under `src/wenu/data/catalogs/`; writes versioned products under `output/` by default |
| `tools/query_caldwell_openngc.py` | Explicit maintenance of Caldwell membership/parameters | Reads the versioned membership ledger and pinned OpenNGC files; writes Caldwell resources and provenance |
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

The current CLI filters infrared/embedded flags and reddening. It does **not**
yet expose magnitude, surface-brightness or Trumpler cutoffs. Discuss the
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
