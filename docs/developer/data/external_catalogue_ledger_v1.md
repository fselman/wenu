# External catalogue and large-resource ledger

Version 1 · 2026-11-03 · storage policy and verified initial relocations

## Storage decision and scope

Fernando instructed creation of `/Users/fselman/Developer/wenu-data` for all
large catalogues needed by Wenu, a ledger under docs, and removal of needed
catalogues from build directories. Distribution will be decided later.
“Large” means roughly 1 GB or more; use 1,000,000,000 bytes as an inventory
flag, not a scientific admission threshold. Consider a complete logical dataset
or multipart resource as well as individual files; report exact bytes and GB/GiB.
No needed catalogue of any size may remain solely in a disposable build.

This is a local external data directory beside the source checkout, not a Git
repository, package payload, test/build run or new runtime default. Do not add
large data to source control. Small packaged catalogues and valid managed data
locations can remain where they are. The audit must also identify required
inputs below the approximate size threshold when found in build/Downloads.

**Observed status:** the Mac directory exists. Initial inventory completed with
zero scan errors and 36 documentation tests passed at `5f255743`. Three saved
stellar catalogues and both large DE441 files have been relocated and verified,
as recorded below. Unknown raw-source facts remain explicit; this is not an
exhaustive audit of every custom Mac input. The size of a parent run is not the
size of a catalogue.

## Needed catalogues and preparation sources

| Dataset / edition | Needed role and owner | Observed storage / size | Required action and status |
|---|---|---|---|
| Gaia DR3 bounded acquired stellar subset and raw query evidence | Accepted stellar preparation and source capture, not the full Gaia archive; offline audit owner `tools/gaia_crossmatch_audit.py` | Raw cache path/total bytes pending Mac inventory. Derived v4 audit copy at `~/wenu-output/gaia_crossmatch_audit_v4_source_v1` was about 1,078 MiB; this is audit evidence, not proof of the raw cache location | Inventory actual cache, source identities and consumers. Put any large required external dataset under `wenu-data/catalogues/`; preserve manifests/query provenance. No new Gaia acquisition |
| Hipparcos / Hipparcos-2 and Kervella supplementary source inputs | Accepted stellar identity/astrometry and reproducible source preparation; catalogue/source metadata remains authoritative | Prepared stellar source at `~/.cache/wenu/stellar/stellar_enrichment_source_v1`; Kervella input observed at `~/.cache/wenu/stellar/kervella2022_a1_v1/tablea1.dat` (about 72 MiB). Exact dataset totals and scientific identities remain governed by their manifests | Retain required originals and receipt chains outside builds; small packaged products need no forced move |
| Prepared stellar source capture and selected saved epoch catalogues | Source-capture and saved-epoch owners; user-selected epoch inputs can be runtime dependencies as well as acceptance outputs | `/Users/fselman/Developer/wenu-data/stellar-epochs/{j2000-tcb-v1,jminus8000-tcb-v1,jminus2000-tcb-v1}` | Moved from the two historical build runs and verified using complete file hashes, public loader and exact-event reuse. Complete byte inventories/digests and current query paths are in the relocation record below; original build payload directories are gone |
| Hunt & Reffert (2024), full cluster/member preparation source | `tools/hunt_reffert_catalogue.py` full catalogue publication reads cluster/member tables and receipt. The astrometry-companion path only needs verified aggregate `clusters.dat.gz` and ReadMe | `~/Downloads/wenu-hunt-reffert2024-v1.Ctdnun/source`, about 374 MiB; member file about 371 MiB. Below large threshold. This location does not establish a normal-chart runtime dependency | Separate full regeneration from normal loading. Preserve any needed preparation source in stable data storage; verify installed prepared products. Do not describe the member table as mandatory for all charts |
| Small curated/packaged catalogues | `wenu.resources.curated_catalogue_bundle`, catalogue providers and installed validated manifests | Packaged catalogue resources; no Downloads dependency established by code assessment | Keep packaged products and admission checks. Catalogue rebuild input is distinct from runtime payload. Inventory any custom external overrides |

The v4 audit data in `gaia_crossmatch_audit_v4` and
`gaia_crossmatch_audit_v4_run2` already contain relative links to the retained
`gaia_crossmatch_audit_v4_source_v1` copy after verified cleanup. If that copy
is relocated, preserve/repair those references or retire their consumers before
deleting it. This existing audit deduplication is not permission to replace
strictly admitted catalogue or saved-epoch payloads with symlinks.

## Large supporting resources, kept distinct from catalogues

| Resource | Role / existing owner | Verified location and size | Action |
|---|---|---|---|
| JPL DE440 and both DE441 parts | `wenu.skyfield_ephemeris.open_pinned_ephemerides` admits explicit existing files, model roles, SHA-256 and conservative actual coverage; exact-event companion preparation consumes them | DE441 files now under `/Users/fselman/Developer/wenu-data/ephemerides/jpl-de441-v1/`; smaller DE440 remains at `~/.cache/wenu/de440.bsp` (119,799,808 bytes) | Verified relocated hashes, coverage/segment admission and unchanged Earth/Sun PV at three events through the existing public pinned-resource API. Current pin arguments and receipts below; no acquisition |
| LIME / lunar orientation preparation resources | Separate radiometry/reference work, not a stellar catalogue | `~/Downloads/wenu-lime-50s7d3b`: about 492 MiB installer, 12 MiB DE440 orientation kernels and 4 MiB result evidence | Installer is not a catalogue or proof of runtime use. Check actual consumers before cleanup; retain needed resources/results in appropriate stable storage. Do not activate paused scientific work |

## Verified relocations and current consumer paths

Fernando reported the following on 2026-11-03. These are actual Mac results,
not future destination proposals.

| Dataset | Former location | Current location relative to `/Users/fselman/Developer/wenu-data` | Verification |
|---|---|---|---|
| Saved J2000 TCB catalogue | `~/Software/build/wenu/output/stellar-epoch-acceptance-v1-ynpv71ip/j2000` | `stellar-epochs/j2000-tcb-v1` | Complete file hashes unchanged; public loader and exact-event query passed |
| Saved J-8000 TCB catalogue | Same historical run, `jminus8000` | `stellar-epochs/jminus8000-tcb-v1` | Same checks passed |
| Saved J-2000 TCB catalogue | `~/Software/build/wenu/output/epoch-consumers-acceptance-v1-lgsgoia9/jminus2000` | `stellar-epochs/jminus2000-tcb-v1` | Same checks passed |
| DE441 part 1 | `~/.cache/wenu/de441_part-1.bsp` | `ephemerides/jpl-de441-v1/de441_part-1.bsp` | 1,651,119,104 bytes; SHA-256 `13757827f5db41b835a24bbd637488636ce79a8ca754062fed17844f7d5b618e` |
| DE441 part 2 | `~/.cache/wenu/de441_part-2.bsp` | `ephemerides/jpl-de441-v1/de441_part-2.bsp` | 1,656,830,976 bytes; SHA-256 `3abb17dae2d78dd34880377544aacb54892104a0d4462b322cb9f4454d4887f6` |

The saved-catalogue relocation record is
`operations/stellar-relocation-v1-ch9i4ng5/run-provenance.json` under the data
root. It retains exact constituent byte counts/SHA-256 values, events, old/new
mapping and per-dataset verification. Use the adjacent `queries/` directory
for exact-event query files and replacements for discovered build query inputs.
Original build queries/captured jobs remain historical evidence with their
original identities; they are superseded for execution by those replacements.
Do not run an old command against a removed build catalogue path.

The current resource index is
`ephemerides/jpl-de440-de441-pins-v1.json`. Its `resources` entries are
arguments for the existing `PinnedEphemerisResource` constructor, not a new
public SDK schema or CLI flag. All three admitted roles are retained; DE440's
SHA-256 is `a4ce9bf9b3282becc9f4b2ac3cebe03a2ae7599981aabd7265fd8482fff7c4b5`.
Use these current arguments for new pinned-resource consumers. Historical
acquisition/companion selection receipts may retain their original path as
provenance; they must not be interpreted as a live locator or rewritten blindly.

The DE441 receipt is `operations/de441-relocation-v2-xg4v5li2/run-provenance.json`.
Original and relocated Earth-centre/Sun geometric position and velocity matched
exactly at native TDB JDs 2451545, -1000000 and 5000000. Public admission checked
resource hashes, actual conservative coverage and segments. This is a relocation
parity check, not a new physical-accuracy qualification. Acquisition receipts and
comments were copied to `ephemerides/jpl-de441-v1/acquisition/`.

Preserve the failed v1 record `operations/de441-relocation-v1-swlgqxv5/`:
it stopped before moving any data because its test event incorrectly used a
float rather than the required integer `jd1`. The v2 retry corrected that
argument and passed. Do not relabel the original run as successful.

The initial inventory/documentation evidence remains at
`~/Software/build/wenu/test/external-catalogue-inventory-v1-d6pb91hj`:
36 passed in 4.85 seconds, zero scan errors, source `5f255743`. A later docs
edit requires the normal documentation gate; it does not require repeating
these unchanged data transfers or expensive numerical work.

## Ledger fields and relocation acceptance

For each actual retained dataset record:

- Stable dataset ID, scientific edition, role (runtime/preparation/selected saved
  product), owning loader/tool and whether its use is mandatory or optional.
- Exact current and destination roots, constituent filenames, logical and
  allocated bytes, SHA-256 and original source/receipt identity.
- Required manifests, source metadata, configuration/CLI/job references and
  linked retained runs; dependencies cannot be inferred from folder names.
- Migration status: identified, prepared, verified at destination, consumers
  verified, old copy removed; unknown is not complete.
- Distribution status: **undecided**, with no implied redistribution rights.

Use descriptive dataset/version subdirectories under the external root; keep
original filenames and companion receipts. Choose actual destination names
from verified identities before moving data. Do not flatten distinct editions.
Copy or move without changing catalogue bytes; on this disk prefer a verified
same-volume rename when the entire dependency unit can move safely. Never
silently overwrite an existing dataset/version or reacquire missing data.

Check both data hashes and dependent receipts before and after relocation.
Relative paths internal to a bundle must remain valid. Absolute references in
configuration, manifests, saved jobs or retained evidence need owner-aware
handling; do not rewrite integrity-bound records with a generic text replacement.
Use public loaders to verify selected consumers at the new path. Only then
remove the old build copy. Temporary compatibility links, if needed, must be
explicit and removed after consumers change; they do not close migration.

Directory creation alone changes no runtime path. Existing ordinary Observer
uses `~/.cache/wenu` by default and explicit `data_directory` overrides;
this request does not silently change its downloads/cache behavior. Pinned
remote-epoch ephemerides use explicitly supplied paths. Coordinate/scientific
meaning and source population remain unchanged by storage maintenance.

## Cleanup rule and current limits

After a PR is accepted, remove its reproducible build/test products. Keep only
active installations, unique needed inputs, expensive numerical results and
small logs/provenance records. An acceptance-evidence label does not preserve
an entire temporary tree. Needed catalogues are data dependencies and must be
separated from disposable build outputs before cleanup.

The verified initial migration covers the three saved catalogues and DE441.
Audit remaining build payload manifests and custom inputs before a blanket
build deletion; source-preparation data, ephemeris companions and historical
render products have different retention roles. The raw Gaia acquisition-cache
location and optional preparation-only resources still need explicit catalogue
identity/consumer classification. No new loader, environment variable, CLI flag
or distribution mechanism is implemented. This ledger stays current as datasets
are added, retired or moved; unknown entries are not a claim of completion.

## Authority and owner references

- [Roadmap: selected operational work](../kernel_roadmap_v0.9.5.md#external-catalogue-storage-and-accepted-build-cleanup)
- [Storage and cleanup instructions](../assistant_instructions.md#build-test-and-output-locations-and-provenance)
- [Packaged catalogue/resource owner](../../../src/wenu/resources.py)
- [Ordinary Observer data directory](../../../src/wenu/observer.py)
- [Offline Gaia audit](../../../tools/gaia_crossmatch_audit.py)
- [Open-cluster preparation](../../../tools/hunt_reffert_catalogue.py)
- [Open-cluster catalogue documentation](../../../src/wenu/data/catalogs/open_clusters/README.md)
- [Pinned ephemeris owner](../../../src/wenu/skyfield_ephemeris.py)
