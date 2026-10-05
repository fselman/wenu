# Stellar Bayer/Flamsteed designation audit

**Status:** Design accepted by Fernando on 2026-10-05, including the amended
selection contract; documentation only. Implementation, catalogue admission
and separately requested merge remain pending.
**Date:** 2026-10-05
**Exact as-is base:** `b929325aeb51fad75193d4216f0e5f8e383fa7ae` on
clean synchronized `main`, as reported by Fernando.
**Scope authorized:** bounded as-is audit and proposal; no production changes,
provider requests during chart construction, catalogue installation or
redistribution, or Gaia integration.

## 1. Outcome and preserved boundaries

Add optional Bayer/Flamsteed labels and explicit name/Bayer stellar selection
to an ordinary `wenu_chart` request. Keep HIP as stable stellar identity and keep
the existing astrometry, celestial-state realization, projection, preparation,
renderer and exporter. Designations are catalogue metadata; their spelling is
not an astronomical coordinate or a new celestial object.

The first implementation should support a declared, immutable HIP-linked
resource and opt-in labels with deterministic text selection. Default charts
retain labels off and unchanged inclusion. Explicit proper-name and Bayer
selection/display are now included, with magnitude-limit bypass. Crowding
optimization, variable/multiple curation and Gaia cross-matching remain later.

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
names and reviewed aliases are a separately admitted field family; do not
choose the first historical name as a modern canonical proper name. Validate
name-to-HIP ambiguity and document preferred spellings.

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

The amended contract below was accepted on 2026-10-05; these are not yet
implemented CLI/API capabilities.

### Explicit selection and display

- Repeatable `--star-label-name 'Sco:Antares,Shaula'` resolves, includes and
  labels the requested stars with their admitted proper names.
- Repeatable `--star-label-bayer 'Sco:alpha,beta,gamma,delta,zeta,iota1'`
  resolves, includes and labels stars with their Bayer designations.
- Both selectors bypass the ordinary star magnitude limit, using the existing
  extra-HIP selection machinery. Resolve identifiers before catalogue selection
  and realization. Other stars remain governed by the ordinary magnitude limit.
  Field, altitude, projection-domain and viewport clipping still apply.
- Deduplicate by HIP. Name selection takes precedence over Bayer selection,
  independent of argument order. Existing curated HIP text/suppression overrides
  retain their higher priority. Only explicitly selected stars receive labels
  from these options; neither enables global automatic labels.
- Accept normalized Greek spellings/glyphs and explicit suffixes; preserve
  Latin-letter case. Unknown, unmatched or ambiguous identifiers fail clearly,
  rather than selecting an arbitrary record. No fuzzy or positional matching.
  A resolved target missing from Hipparcos cannot be added by inventing a position.
- `--show-full-bayer-designation` displays `α Sco` instead of `α`, and
  `ι¹ Sco` instead of `ι¹`. Default false. It adds the designation
  constellation abbreviation; proper names and independent constellation labels
  are unaffected.

Equivalent proposed TOML:

```toml
[detail.star_labels]
names = ["Sco:Antares,Shaula"]
bayer = ["Sco:alpha,beta,gamma,delta,zeta,iota1"]
show_full_bayer_designation = false
```

CLI repeated values accumulate per selector. A CLI selector replaces its
corresponding TOML list; an absent selector preserves that list. The boolean
follows existing CLI/config override rules. Initial global Bayer/Flamsteed
modes remain separate opt-in proposals; composition with explicit lists requires
an explicit decision before implementation, not accidental automatic labels.

### Ownership and rendering

Detail owns resolved extra HIP IDs, label eligibility and requested text.
Explicit targets must not be removed by an automatic label magnitude cap.
Reuse existing inclusion/selection and cached astrometry; do not mutate a
shared sphere catalogue for another chart's selection.

`StellarStyle` owns colour, font size, alpha and offset; output mode owns
physical scaling. Keep constellation/title fonts and star sizing independent.
Compose a value-semantic HIP-to-text formatter in existing detail application.
The renderer receives text or `None`, with no catalogue lookup.
Never fall back to HIP numbers for unmatched labels. Leaving geometry labels
unset lets the generic renderer supply HIP to the formatter.

Preserve the existing star-render callable, normalized sizes, variable/multiple
overlays and base/style → detail → explicit call-site precedence. Reuse strict
schema/default/translator machinery. Resource admission is separate; no implicit
provider queries or automatic download. No new collision solver is included.

### Future variable and multiple curation

Wenu already attaches Hipparcos `is_variable`, `is_multiple`, variability
flags and component fields, with optional classification symbol overlays.
Catalogue classification does not determine editorial notability.

Keep inclusion, label text and curated symbol eligibility independent.
A star can receive both classification marks and one label; name/Bayer selection
does not automatically activate either mark. Future curated selectors are not
implemented in this milestone.

Use explicit per-chart reviewed lists with source evidence and a reason for
inclusion. Candidate filters may consider visual amplitude, passband, time scale
and pedagogical/historical interest for variables; separation, magnitude contrast,
instrument context and scientific interest for doubles. No universal threshold
or assumption that all stars qualify is adopted.

Primary sources checked on 2026-10-05:
[AAVSO VSX FAQ](https://vsx.aavso.org/index.php?view=about.faq) distinguishes
photometric ranges, amplitudes and passbands;
[USNO WDS description](https://crf.usno.navy.mil/wdstext) records components,
separations, magnitudes and measurement epochs, and distinguishes physical,
optical and unknown systems. These are future candidate sources, not acquired
resources or new automated access routes.

Preserve system and component-pair identity (AB, AC, etc.) separately from the
HIP of a drawn point; do not assume a one-to-one HIP-to-pair mapping.
Bayer superscripts such as `ι¹` are designation suffixes,
not physical component A/B identities. Missing catalogue classification is
not proof that a star is constant or single. Resolved component geometry,
orbital propagation and time-varying brightness remain separate future science.

## 6. Schematic flow

```mermaid
flowchart TD
  H["Hipparcos astrometry and HIP"] --> S["Stars: attach by HIP"]
  K["Admitted designation snapshot"] --> S
  S --> G["Existing geometry and preparation"]
  D["Detail selection and labels"] --> S
  D --> F["Render-local label formatter"]
  A["Stellar label appearance"] --> F
  G --> F
  F --> R["Existing renderer and export"]
```

This diagram shows ownership, not a second render pipeline. Text resolution
and appearance are render options on the same prepared stars; coordinates
remain governed by the existing celestial realization.

## 7. Validation and delivery sequence

1. Record Fernando's 2026-10-05 acceptance of the audit and amended
   selection/display contract. Original head `e47e23e3` passed 240 Mac
   documentation/package-boundary tests in 10.78 s; this amendment needs a fresh
   focused documentation gate.
2. Freeze usable source terms and exact data receipts for the selected resource
   distribution strategy. A local externally supplied snapshot is distinct
   from a bundled database. Close the conflict/coverage ledger before claiming
   real-catalogue completeness.
3. Implement the bounded ingestion/attachment and ordinary label composition,
   preserving labels-off behavior and typed strict settings. No Gaia runtime
   is included; explicit admitted proper-name display is included. Source gates must
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
  classifications and constellation vertices; inclusion stays unchanged without
  selectors and is extended only by resolved explicit HIP targets;
- every label mode, missing-field suppression, HIP-keyed curated overrides,
  below-limit explicit inclusion, name precedence in either argument order,
  repeated selectors, CLI/TOML list replacement, short/full Bayer text,
  ambiguous token errors and ordinary clipping;
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
the first Bayer/Flamsteed milestone. Explicit proper-name selection/display is
now included with reviewed preferences. Wider historical-alias products and
variable/multiple curation remain later work.

## 9. Source comparison and publication freedom (2026-10-05)

**Status:** Candidate source-policy supplement, requested after the accepted
selection design; no real dataset is admitted by this comparison.
**Exact comparison base:** `bf904a284d36a530c2d4ae84619f10a4b43c1f88`.
**Requirement:** Fernando wants Wenu charts and atlas products to be publishable
commercially or noncommercially without forced output relicensing, royalties,
or case-by-case publication permission. Strictly condition-free reuse also
excludes mandatory attribution; an attribution-only source is a distinct
fallback to discuss, not assumed equivalent to CC0/public domain.

Kostjuk is not mandatory. The internal HIP-linked resource, selection,
precedence, CLI/TOML and renderer contracts are source-independent.
Source permission, scientific adequacy and exact snapshot integrity are three
separate admission checks.

### Evidence matrix

All URLs below were checked on 2026-10-05. These are documentation-level findings,
not a complete acquired-data coverage or discrepancy study.

| Candidate | Identity/designation suitability | Observed rights evidence | Current decision |
|---|---|---|---|
| Kostjuk IV/27A | Separate Bayer/Flamsteed fields, optional HIP and historical alternatives; suitable subject to conflict-ledger review. | ReadMe has no explicit redistribution grant; the linked CDS licence page could not be retrieved. | Keep as scientific reference/candidate, not admitted bundled data. |
| Yale BSC V/50 | Bayer/Flamsteed in Name, HR/HD and multiplicity/variability fields; primary table lacks HIP, requiring a verified identity bridge. | Inspected CDS and HEASARC descriptions did not establish a dataset-specific unrestricted grant. | Do not infer public-domain status from mirrors, app descriptions, catalogue age or NASA hosting. |
| HYG 4.1 | HIP, proper names and Bayer/Flamsteed; convenient compiled resource. | Maintainer explicitly declares CC BY-SA 4.0. | Not preferred for a condition-free bundled designation resource; a separate permission could change this. |
| IAU/WGSN CSN | Preferred proper names, HIP and Bayer columns for named entries; does not cover all unnamed Bayer/Flamsteed stars. | Current catalog/download/imprint pages inspected did not establish a primary-source dataset licence; an archived third-party processor claims CC BY. | Scientific name authority; current payload terms still require confirmation. |
| Wikidata structured items | HIP and catalog-qualified Bayer/Flamsteed statements exist; ranks, references, systems/components and completeness need review. | Wikidata's own policy releases structured data under CC0; this excludes Wikipedia prose/images and other non-structured content. | Preferred candidate to evaluate for condition-free metadata, not yet a scientifically admitted snapshot. |

Sources:
[Kostjuk ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/IV/27A?format=html&tex=true),
[CDS linked licence page](https://cds.unistra.fr/vizier-org/licences_vizier.html),
[Yale BSC ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/V/50?format=html&tex=true),
[HEASARC BSC5P](https://heasarc.gsfc.nasa.gov/W3Browse/star-catalog/bsc5p.html),
[HYG maintainer documentation](https://github.com/astronexus/HYG-Database/blob/main/hyg/README.md),
[WGSN catalog](https://exopla.net/star-names/modern-iau-star-names/),
[WGSN download index](https://exopla.net/iau-wgsn-catalogs/),
[WGSN imprint](https://exopla.net/imprint/),
[archived third-party processor](https://github.com/mirandadam/iau-starnames),
[Wikidata copyright policy](https://www.wikidata.org/wiki/Wikidata:Copyright),
[Wikidata licensing explanation](https://www.wikidata.org/wiki/Wikidata:Licensing).

HYG also documents unofficial secondary names such as “Albireo B”.
Do not promote these to IAU-preferred names. A software converter's MIT/CC0
licence is not evidence that its input catalogue has the same terms.
Likewise, a publicly downloadable table is not automatically public domain.

### Data and chart rights are different questions

The [CC BY-SA 4.0 legal code](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en)
covers licensed material, adaptations and applicable database rights.
It does not automatically require every chart or enclosing book to be BY-SA.
Whether a particular use triggers those rights is a separate question; do not
claim blanket atlas relicensing, or blanket exemption for extracting a few
columns. A derived distributed database can have different obligations from
an original chart. Avoid relying on uncertain exceptions to meet this project
requirement.

[CC0's legal text](https://creativecommons.org/publicdomain/zero/1.0/legalcode.en)
waives the affirmer's copyright and related/database rights to the extent
possible, with fallback provisions. It does not grant rights a contributor does
not own, clear trademarks, or guarantee correctness. Wikidata's policy expressly
discusses uncertainty around third-party dataset claims; CC0 is not a means of
laundering an entire restricted source compilation.

Scientific attribution/provenance remains desirable even where not legally
required. Credits can live in the resource manifest and atlas bibliography,
without automatically placing a credit beside each star. This review concerns
new designation metadata only; it is not a rights clearance for every existing
Wenu catalogue, image, font, ephemeris or exported product.

### Small scientific spot check

The inspected structured items contain the following HIP/Bayer pairs:

| Item | HIP statement | Bayer statement | Review limitation |
|---|---|---|---|
| [Antares Q12166](https://www.wikidata.org/wiki/Q12166) | 80763 | α Sco | Bayer reference is a Wikimedia import; its Flamsteed statement has no reference. |
| [Lambda Scorpii Q13023](https://www.wikidata.org/wiki/Q13023) | 85927 | λ Sco | Includes system/component identifiers; Bayer reference is a Wikimedia import. |
| [Iota1 Scorpii Q2711568](https://www.wikidata.org/wiki/Q2711568) | 87073 | ι¹ Sco | Bayer statement has no reference in the inspected page. |

The WGSN primary table independently agrees on Antares and Shaula's HIP/Bayer
identities. These checks establish plausibility, not measured all-sky coverage,
exact release receipts or a parser oracle. No raw catalogue has been frozen,
downloaded into Wenu or redistributed; no complete conflict counts are claimed.

### Recommended next bounded step

1. Evaluate a minimal Wikidata structured-data snapshot containing only required
   identifiers, names/aliases and designation statements, keeping item revisions,
   statement IDs, ranks, qualifiers and reference provenance.
2. Before designing automated acquisition, inspect current Wikimedia API/access
   policies; do not introduce requests during chart construction or assume a
   permitted concurrency/cadence from this licensing review.
3. Measure coverage against Wenu's HIP catalogue and the agreed selectors; report
   missing HIPs/designations, duplicate or conflicting identities, physical
   component ambiguity, Latin letters and Bayer superscripts. Check independently
   against scientific authorities; do not copy their prose or entire compilations
   into the CC0 resource.
4. Separate reviewed preferred proper names from generic Wikidata labels/aliases.
   Choose by a documented review decision, not “first English label”.
5. If coverage/quality is inadequate, seek an explicit unrestricted grant for a
   primary catalogue or propose a documented independently curated complement.
   Do not silently backfill a CC0 resource from HYG/Kostjuk/Yale bytes.
6. Freeze the selected raw payload and policy receipts with exact URLs, dates,
   sizes, SHA-256 and transformation version before dataset admission.

Recommendation: investigate CC0 structured metadata first; retain Kostjuk/Yale
and WGSN as scientific comparison authorities while their exact distribution
terms remain unresolved. HYG's clear licence is useful evidence but does not
satisfy strict condition-free distribution. The accepted selectors, magnitude
bypass, label precedence, HIP astrometry and future curation boundaries stand.
