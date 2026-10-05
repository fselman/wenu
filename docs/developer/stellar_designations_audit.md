# Stellar Bayer/Flamsteed designation audit

**Status:** Documentation-only candidate; implementation and catalogue admission
remain pending separate acceptance.
**Date:** 2026-10-05
**Exact as-is base:** `b929325aeb51fad75193d4216f0e5f8e383fa7ae` on
clean synchronized `main`, as reported by Fernando.
**Scope authorized:** bounded as-is audit and proposal; no production changes,
provider requests during chart construction, catalogue installation or
redistribution, or Gaia integration.

## 1. Outcome and preserved boundaries

Add optional Bayer/Flamsteed labels to the stars already realized for an
ordinary `wenu_chart` request. Keep HIP as stable stellar identity and keep
the existing astrometry, celestial-state realization, projection, preparation,
renderer and exporter. Designations are catalogue metadata; their spelling is
not an astronomical coordinate or a new celestial object.

The first implementation should support a declared, immutable HIP-linked
resource and opt-in labels with deterministic text selection. Default charts
retain labels off. Proper names, alias-based star selection, crowding
optimization and Gaia cross-matching are later slices, not prerequisites for
Bayer/Flamsteed display.

## 2. Verified as-is ownership

| Existing owner | Current behavior | Required extension |
|---|---|---|
| `resources.py:catalog_path` | Packaged Hipparcos is the supported stellar catalogue. | Resolve a designation resource separately; do not replace the astrometric catalogue. |
| `objects/stars.py:Stars.load` | Skyfield Hipparcos rows are indexed by HIP; full source and selected catalogues preserve row identity. Classification metadata is already attached by HIP. | Attach validated designation columns by HIP before selection, preserving order/count and original coordinates, magnitudes and classifications. |
| `Stars.position`, `spherical_geometry`, `observed_altaz` | Native ICRS and apparent AltAz routes retain HIP IDs; selected metadata arrays follow the same rows. Observer geometry is cached. No Bayer/Flamsteed labels are supplied. | Transport designation metadata through both routes; do not create a label-only coordinate evaluation or mutate observer caches for presentation. |
| `geometry/spherical.py`, `geometry/projected.py`, `rendering/preparation.py` | Generic collections already carry IDs, labels, names and metadata; preparation subsets per-entity metadata. | Verify alignment through clipping/projection using these existing containers. |
| `charts/detail.py` | Star magnitude/content selection, extra HIP IDs and curated label overrides exist. `CartoonDetail.label_named_stars` is declared, but is not forwarded by its current `resolve` method; `label_density` is not an implemented stellar-name thinning algorithm. | Explicitly resolve designation mode and eligibility; do not infer a working Bayer/Flamsteed route from those fields. |
| `charts/style_components.py:StellarStyle`, `charts/styles.py` | Star symbol sizing/classification overlays exist; normal star options supply markers/overlays, not designation labels. | Add stellar label appearance and preserve the grouped-style to publication-style adapter. |
| `charts/detail_application.py` | Owns render-local selection/options, curated-label formatter and a callable star-render composition for sizing. | Compose detail eligibility, HIP-keyed overrides and label appearance with the existing callable; preserve sizing, overlays, precedence and render isolation. |
| `rendering/matplotlib.py` | Generic point labels prefer labels, then names, then IDs. A formatter returning `None` suppresses a label. | Reuse this path. Never fall back to HIP numbers for missing Bayer/Flamsteed labels. |
| `charts/command_line.py`, configuration translators/validator/defaults | Existing ordinary chart argument and strict schema machinery. | Expose only the bounded new opt-in settings through the existing paths; reject invalid modes/settings rather than silently dropping them. |

Current architecture, target vocabulary, implementation reference, source map,
schema-v2 authority and the coordinate guide were reviewed. The indexed
current architecture/coordinate diagrams preserve the canonical flow and
need no as-built topology change for this documentation-only proposal. The
coordinate guide remains current: designation attachment must not change
state, origin, frame, epoch, equinox, time scale, observer or position status.
No current public API is changed by this audit.

## 3. Catalogue evidence and admission gates

Primary source checked on 2026-10-05:
[Kostjuk IV/27A ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/IV/27A?format=html&tex=true).
The described main table has 3,690 rows; its cross-identifiers are HD, DM,
GC, HR and optional HIP, with separate Flamsteed, Bayer and constellation
fields. The 277-row addendum marks duplicates, designations outside the
current constellation and a nova. Alternative designations, alternative
HD/DM identities and proper names are separate tables. Gaia IDs are absent.

Do not treat every row as a unique HIP star or every alternative as a
preferred label. Preserve original field values, source table/row identity,
flags and reference links. Parse nullable HIP explicitly. Report missing-HIP,
missing-designation, duplicate, conflicting and unmatched entries; never
position-match or silently attach them to another star. Rows sharing a HIP
must remain separate candidate records until a documented preference resolves
them; identical records may be deduplicated with their receipts retained.

Proposed first policy: preferred main-table designations can enter the label
map after the join is verified. Keep historical alternatives and the flagged
addendum as reviewable evidence; do not automatically promote them to preferred
labels or concatenate the addendum into the main table. Produce a conflict
ledger and require an explicit curated decision for contested component or
constellation assignments. Source coordinates may help review but must not
replace Wenu's Hipparcos astrometry. Coverage claims require measured results
from admitted bytes, not the catalogue's advertised row count.

This audit inspected documentation, not a frozen catalogue payload. No
source file hashes, matched-HIP counts or complete scientific mapping are
claimed yet. Admission must freeze exact files, URLs, acquisition date, byte
counts, SHA-256, parser/schema version, transformation policy and validation
summary in a manifest. Download/build is a deliberate acquisition step;
ordinary imports, catalogue loading from an installed snapshot, realization,
rendering and export must not query CDS or another service.

### Rights and publication

The inspected ReadMe supplies bibliographic provenance but no explicit
catalogue redistribution licence. The catalogue landing page exposed an
unresolved licence template in the accessible response, not verified terms.
The [CDS usage/licence page](https://cds.unistra.fr/vizier-org/licences_vizier.html)
linked by VizieR was blocked by robots.txt during this audit. Consequently
redistribution rights remain unverified. This is not a finding that use is
prohibited, nor a grant of rights.

Before shipping catalogue-derived bytes, freeze applicable catalogue/provider
terms or explicit permission and the required attribution. Distinguish local
use of an explicitly supplied resource, distribution of a derived data
snapshot, and publication of original charts/atlas products. Attribution alone
must not be recorded as a verified blanket permission. No contact message was
sent and no catalogue bytes are vendored by this candidate. Parser/join/label
logic can be developed and tested against small synthetic records while this
resource gate is resolved; release of a bundled real dataset and acceptance
of source-derived publication specimens remain gated on the applicable terms.

## 4. Proposed data and module contract

A frozen designation record should retain HIP, supporting HD/HR identifiers,
source Bayer token (Greek abbreviation or Latin letter), component/superscript,
Flamsteed number, designation constellation, preferred/alternative status,
source flags and record/reference provenance. Missing fields are explicit
missing values, never fabricated empty identifiers or numeric zero. Proper
names remain a separate future field family; do not choose the first historical
name as a modern canonical proper name.

Preserve raw tokens alongside normalized/display forms. Use an explicit Greek
abbreviation map; preserve Latin letters and case, component indices and the
source constellation. Do not infer a Bayer letter from magnitude, sky
position or constellation membership. Render examples such as `α Ori`,
`ι¹ Sco` and `58 Ori` are typography examples, not newly verified HIP joins.
Changing the label form does not change HIP or semantic object identity.

Proposed durable ingestion owner: `src/wenu/star_designations.py` (not yet
created). Its independent responsibility is resource validation, immutable
identity-keyed designation records, conflict reporting and pure normalization;
it imports no Observer, chart, projection, renderer or exporter. Existing
`Stars` owns attachment and row selection. This justifies one small module,
not a new star subclass, provider framework, milestone-named module or
subpackage. `resources.py` retains installed-resource path resolution.

Attach read-only/scalar record provenance plus aligned per-star arrays under
separate designation metadata. Astrometric coordinate-spec provenance remains
Hipparcos/Skyfield; label-source provenance must not masquerade as a position
provider. Load a snapshot once per stellar catalogue load, not per label,
projection or animation frame. Preserve copy/isolation obligations for all
arrays and keep a single immutable source revision.

## 5. Detail, style and ordinary CLI contract (proposed)

All setting names below are proposals, not current CLI/API capabilities.

- Detail owns `star_label_mode`: `none` (default), `bayer`, `flamsteed`,
  `bayer-or-flamsteed` (Bayer preferred, Flamsteed fallback), or `both`
  (Bayer then Flamsteed in deterministic order). Include the catalogue's
  constellation abbreviation in designation text. Missing requested fields
  produce no label; they do not fall back to HIP or a proper name.
- Detail also owns a label magnitude cap and optional HIP eligibility set.
  Eligibility is the intersection of already drawn stars, admitted usable
  designations and those explicit bounds. Label settings must not add/remove
  stars or alter their magnitude selection. Existing content-label overrides
  remain keyed by HIP and can replace text or suppress it with `None`.
- `StellarStyle` owns colour, font size, alpha and offset for label appearance;
  output mode continues to own physical scaling. Keep label font changes
  independent of constellation-label fonts, title/furniture and star sizes.
- Compose a value-semantic HIP-to-display-text formatter in the existing
  detail application using the realized star metadata. The existing renderer
  gets text or `None`; it must not look up HIP in a catalogue or understand
  Bayer tokens. Suppress every ineligible/unmatched HIP explicitly, because
  generic renderer precedence otherwise prints an ID. With labels left unset
  on the stellar geometry, the renderer supplies HIP to this formatter; a
  plain label-text lookup is insufficient if upstream labels are populated.
- Reuse the existing star-render callable composition so normalized sizes,
  variable/multiple overlays, detail overrides and explicit layer options
  remain intact. Do not overwrite a callable with an uncomposed dictionary.
  Respect current base/style → detail → explicit call-site precedence.
- Proposed ordinary CLI opt-in: `--star-labels MODE`, with corresponding
  typed detail/configuration settings. Resource-path admission is separate
  from label mode. Use the existing strict schema/translation/default rules;
  do not expose raw Python callables in TOML. No global automatic download.

Initial selection is deterministic and explicit. No new collision solver,
nearest-neighbour matcher or promise that every dense chart is readable is
included. Use the existing label offset/text path, record overlap limitations,
and accept representative dense and sparse products visually.

## 6. Schematic flow

```mermaid
flowchart TD
  H["Hipparcos astrometry and HIP"] --> S["Stars: attach by HIP"]
  K["Admitted designation snapshot"] --> S
  S --> G["Existing geometry and preparation"]
  D["Detail eligibility and label mode"] --> F["Render-local label formatter"]
  A["Stellar label appearance"] --> F
  G --> F
  F --> R["Existing renderer and export"]
```

This diagram shows ownership, not a second render pipeline. Text resolution
and appearance are render options on the same prepared stars; coordinates
remain governed by the existing celestial realization.

## 7. Validation and delivery sequence

1. Accept this audit and the record/preference, label and ownership contracts.
2. Freeze usable source terms and exact data receipts for the selected resource
   distribution strategy. A local externally supplied snapshot is distinct
   from a bundled database. Close the conflict/coverage ledger before claiming
   real-catalogue completeness.
3. Implement the bounded ingestion/attachment and ordinary label composition,
   preserving labels-off behavior and typed strict settings. No Gaia runtime
   or proper-name display is included. Source-specific admission gates must
   not be bypassed by bundling unverified bytes.
4. Verify the new seams, complete Mac regression, scientific mapping review
   and PNG/PDF/SVG visual/print acceptance before closure.

Closest existing tests: `test_stars.py` for HIP attachment and metadata row
alignment; `test_detail_policy.py` for eligibility/precedence;
`test_style_contracts.py` and configuration translation/overlay tests for
appearance and strict public activation; `test_matplotlib_renderer.py` and
`test_renderer_contracts.py` for generic label suppression and clipping;
`test_render_isolation.py` for shared-sphere order independence; and existing
semantic-SVG tests for stable HIP entity IDs. Extend these for changed seams.
A future `test_star_designations.py` is justified only if the independently
owned resource/parser/conflict lifecycle is admitted; no milestone-named test
file or duplicated astrometry oracle.

Required evidence includes:

- exact record/row normalization, duplicate/conflict/missing-HIP handling,
  hash mismatch and deterministic join independent of catalogue row order;
- the same designation metadata on native and apparent routes after magnitude,
  altitude, projection-domain and clipping selection;
- labels-off output equivalence and unchanged IDs, coordinates, magnitudes,
  classifications, star inclusion and constellation vertices in every mode;
- every label mode, missing-field suppression, HIP-keyed curated overrides,
  magnitude/ID eligibility and wrong setting rejection;
- successive differently labelled charts sharing one sphere, with unchanged
  source metadata, style/detail settings and observer geometry cache;
- independent source-backed verification of accepted HIP joins, including
  Latin/Greek tokens, superscripts and genuinely contested/multiple cases;
- regional, binocular and stereographic `wenu_chart` specimens in PNG/PDF/SVG,
  both sky orientations and representative print styles, with Greek/superscript
  glyphs inspected, unchanged constellation/title font sizes and stable SVG
  identity. Physical polar products need a separate bounded closure if their
  composition route introduces a distinct setting seam.

Data facts come from the frozen source records, not image tolerances. Human
review must decide ambiguous catalogue preferences and readability; tests
cannot infer canonical names or legal permission.

## 8. Gaia and later extensions

Kostjuk has no Gaia IDs. A later independently versioned bridge may use
[Gaia DR3 Hipparcos2 best-neighbour metadata](https://gaia.aip.de/metadata/gaiadr3/hipparcos2_best_neighbour/)
to connect HIP to a release-qualified Gaia source ID, retaining match evidence
and ambiguity/coverage status. This is not a universal one-to-one identity
promise. Validate catalogue compatibility, components and missing matches;
keep Gaia ID plus release separate from HIP and designation spelling. No Gaia
query, cross-match, astrometric migration or new Gaia dependency belongs to
the first Bayer/Flamsteed milestone. Proper-name and historical-alias products
also require their own preference/source review.
