# External catalogue and large-resource ledger

Version 1 · 2026-11-03 · user-selected storage requirement; migration open

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

**Observed status:** directory creation and complete Mac data inventory are
pending. No dataset is claimed moved or consumer path repaired by this document.
Known local paths below come from Fernando's reported inventories; unknowns
remain explicit. The size of a parent run is not the size of a catalogue.

## Needed catalogues and preparation sources

| Dataset / edition | Needed role and owner | Observed storage / size | Required action and status |
|---|---|---|---|
| Gaia DR3 bounded acquired stellar subset and raw query evidence | Accepted stellar preparation and source capture, not the full Gaia archive; offline audit owner `tools/gaia_crossmatch_audit.py` | Raw cache path/total bytes pending Mac inventory. Derived v4 audit copy at `~/wenu-output/gaia_crossmatch_audit_v4_source_v1` was about 1,078 MiB; this is audit evidence, not proof of the raw cache location | Inventory actual cache, source identities and consumers. Put any large required external dataset under `wenu-data/catalogues/`; preserve manifests/query provenance. No new Gaia acquisition |
| Hipparcos / Hipparcos-2 and Kervella supplementary source inputs | Accepted stellar identity/astrometry and reproducible source preparation; catalogue/source metadata remains authoritative | Runtime/preparation source paths, exact editions and sizes to recover from actual manifests. Do not infer them from a directory label | Retain required originals and receipt chains outside builds; small packaged products need no forced move |
| Prepared stellar source capture and selected saved epoch catalogues | Source-capture and saved-epoch owners; user-selected epoch inputs can be runtime dependencies as well as acceptance outputs | `~/Software/build/wenu/output/stellar-epoch-acceptance-v1-ynpv71ip` about 1,940 MiB total, containing J2000/J-8000 states/models/source bundles; `epoch-consumers-acceptance-v1-lgsgoia9` about 1,084 MiB including J-2000 and chart/test products | Inspect manifests and actual selected consumers. Relocate required source/saved products to `wenu-data/stellar-epochs/` regardless of per-file size; retain expensive results, remove disposable duplicates only after consumer verification. Runtime selection and migration pending |
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
| JPL DE440 and both DE441 parts | `wenu.skyfield_ephemeris.open_pinned_ephemerides` admits explicit existing files, model roles, SHA-256 and conservative actual coverage; exact-event companion preparation consumes them | Mac resource/receipt paths and exact bytes pending inventory; earlier acquisition run `~/Software/build/wenu/output/jpl-de440-de441-acquisition-v2-vrlyhrov` is an evidence location, not proof of kernel location | Inventory actual payload paths and receipts. Required large external kernels belong under `wenu-data/ephemerides/`; preserve model/coverage/hash admission and update explicit consumers. No automatic replacement or download |
| LIME / lunar orientation preparation resources | Separate radiometry/reference work, not a stellar catalogue | `~/Downloads/wenu-lime-50s7d3b`: about 492 MiB installer, 12 MiB DE440 orientation kernels and 4 MiB result evidence | Installer is not a catalogue or proof of runtime use. Check actual consumers before cleanup; retain needed resources/results in appropriate stable storage. Do not activate paused scientific work |

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

The first source assessment establishes owner behavior, not a complete Mac
filesystem dependency audit. No uniform relocation, new loader, environment
variable, CLI flag or distribution mechanism is implemented here. Record actual
Mac inventory and relocation receipts in the PR/ledger before claiming closure.

## Authority and owner references

- [Roadmap: selected operational work](../kernel_roadmap_v0.9.5.md#external-catalogue-storage-and-accepted-build-cleanup)
- [Storage and cleanup instructions](../assistant_instructions.md#build-test-and-output-locations-and-provenance)
- [Packaged catalogue/resource owner](../../../src/wenu/resources.py)
- [Ordinary Observer data directory](../../../src/wenu/observer.py)
- [Offline Gaia audit](../../../tools/gaia_crossmatch_audit.py)
- [Open-cluster preparation](../../../tools/hunt_reffert_catalogue.py)
- [Open-cluster catalogue documentation](../../../src/wenu/data/catalogs/open_clusters/README.md)
- [Pinned ephemeris owner](../../../src/wenu/skyfield_ephemeris.py)
