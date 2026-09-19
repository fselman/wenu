# 50S.6G.2A canonical exact-crossing report and JSON audit

**Status:** Candidate documentation-only scientific, logical-model, JSON Schema,
serialization, round-trip, ownership, and failure-contract audit.

**Base:** accepted bounded 50S.6G.1B closure at merge commit `3f234cc`.

**Runtime effect:** None. This audit creates no production type, schema resource,
encoder, decoder, file command, report artifact, track, chart, or provider
access.

## 1. Purpose

50S.6G.2A must carry already accepted exact local crossing results across one
renderer-neutral and serialization-neutral information boundary. It must not
recompute a crossing, propagation, coordinate, airmass admission, conservative
selection, or acceleration decision.

The product is a scientific report of geometric field crossings. It is not a
visibility forecast, illumination calculation, brightness estimate, detector
contamination assessment, or observatory scheduling decision.

## 2. As-is assessment

The integrated repository already provides:

- immutable `SatelliteObserver`, `SatelliteFieldOfView`,
  `InclusiveTimeInterval`, `SatelliteCrossingCandidate`, and
  `SatelliteCrossingResult` values;
- complete local-query identity and tolerances in
  `LocalSatelliteCrossingQuery`;
- ordered `MultiFieldCrossingResult` values containing exact crossings,
  centre-airmass admission, and acceleration evidence;
- immutable snapshot manifests and explicit external admission;
- deterministic SatChecker sampled-candidate JSON in
  `satellite_presentations.py`, with an explicitly different scientific
  status;
- deterministic canonical JSON and atomic-write practice in the sequence
  manifest and satellite evidence implementations.

The repository does not provide a canonical exact-crossing logical report,
versioned JSON Schema, exact-report encoder/decoder, report identity digest, or
round-trip validation. `satellite_presentations.py` owns SatChecker
sampled-candidate evidence and must not silently acquire exact-local-report
ownership.

## 3. Scientific-status separation

The exact report product identity is
`wenu.artificial_satellite_exact_crossing_report`. Its status is
`geometric exact local crossings — visibility not evaluated`.

It must remain distinct from
`wenu.satchecker_sampled_candidate_evidence`. A decoder must reject the
sampled-candidate product identity, and the SatChecker presentation must not
accept exact-local results.

A zero-crossing field is a valid explicit scientific result. An absent field,
failed field, omitted field, or null crossing collection is not equivalent to
a validated field with zero crossings.

## 4. Immutable logical model

The candidate production owner is a new dedicated module adjacent to
`satellite_presentations.py`, provisionally
`satellite_crossing_reports.py`. This is a distinct responsibility because
its inputs, scientific status, schema, round-trip contract, and future ECSV and
VOTable consumers differ from sampled-candidate presentation. The final module
name requires the implementation slice's source-tree assessment.

One immutable report contains:

1. schema version, document kind, product identity, scientific status, and one
   explicit UTC creation instant;
2. Wenu version plus report-model, encoder, crossing-oracle, acceleration, and
   batch-coordinator implementation identities;
3. complete observer identity and policy;
4. complete snapshot manifest identity and content digest, including source,
   acquisition, provider-policy, builder, warnings, record count, and epoch
   bounds already retained by the snapshot;
5. batch policy, processing chunk size, maximum airmass, exact time and angular
   tolerances, and ordered field count;
6. every ordered field request, coordinate specification, inclusive interval,
   centre-airmass admission, warnings, and explicit crossing count;
7. every exact connected visit with stable field identity, full NORAD
   identity, element epoch, entry, closest-approach and exit instants,
   closest-approach angle, time in field, range, angular rate, oracle and
   acceleration provenance, and warnings;
8. explicit nullable future-science values for illumination, apparent
   magnitude, detector effect, and exact-track samples.

The creation instant is supplied explicitly when constructing the immutable
report. It is normalized once to UTC microseconds and is never read from the
clock during serialization or decoding. Therefore repeated serialization of
one report is byte-identical.

In schema version 1 the four future-science values must be JSON `null`.
Non-null illumination, magnitude, detector, or track content is rejected until
the separately accepted 50S.7, 50S.8, 50S.9, or 50S.6G.3A milestone evolves
the schema. Null means not evaluated, never false, dark, zero, or absent.

## 5. Ordering and identity

The report preserves batch field order. Within each field, crossings use the
accepted oracle order: full NORAD catalogue identifier, then entry instant.
The constructor rejects duplicate field identifiers, context mismatches,
crossings belonging to another field/query/snapshot, duplicate connected
visits, inconsistent element identity, and crossing counts that disagree with
the retained tuple.

Arrays retain semantic order. JSON object-key order has no semantic meaning;
the encoder sorts keys for deterministic bytes.

The logical report has a `report_identity_sha256` computed from compact
canonical UTF-8 JSON of the complete scientific payload excluding only the
identity field itself. The creation instant is part of the payload. Pretty
serialization and compact identity serialization therefore describe the same
logical content.

The digest is report identity, not snapshot identity, file identity,
authorization, signature, or proof of visibility.

## 6. JSON and JSON Schema contract

JSON is UTF-8 with a final newline, two-space indentation, sorted object keys,
stable array order, `ensure_ascii=False`, and finite numbers only. NaN and
infinity fail before publication. UTC instants use exactly six fractional
digits and `Z`.

A packaged JSON Schema Draft 2020-12 resource must:

- identify the exact document kind and schema version;
- close every object with `additionalProperties: false`;
- require every field, including nullable future-science fields;
- express integer, finite-number, string, array, nullability, digest, and UTC
  lexical constraints;
- preserve full NORAD integers without five-digit truncation;
- declare descriptive units and scientific meaning;
- reject unknown fields and unsupported schema versions.

Schema validation is necessary but not sufficient. Construction and decoding
must also enforce cross-field invariants that JSON Schema cannot express,
including shared observer/snapshot identity, field order and uniqueness,
interval containment, event ordering, radius containment, count agreement,
and report-digest agreement.

## 7. Encoding, decoding, and round trips

The implementation slice may add pure operations equivalent to:

- `ExactSatelliteCrossingReport.from_results(...)`;
- `report.document`;
- `report.to_json()`;
- `ExactSatelliteCrossingReport.from_json(text)`.

Names remain candidate API, not authorization.

The encoder consumes only the immutable report and performs no scientific
calculation. The decoder accepts text or UTF-8 bytes only through an explicit
boundary, parses JSON without accepting duplicate object keys, validates the
packaged schema, reconstructs typed immutable values, enforces all semantic
invariants, and verifies the report digest.

Required equality is:

`from_json(report.to_json()) == report`

and the re-encoded bytes must equal the original canonical bytes. Decoding and
re-encoding must not consult the network, clock, filesystem, Astropy
transformation services, SGP4, or a crossing solver.

Atomic filesystem publication belongs to 50S.6G.2C. 50S.6G.2A exposes no path,
overwrite, CLI, or file-writing API.

## 8. Validation specimens and test ownership

Implementation tests belong in a new
`tests/test_satellite_crossing_reports.py` only if the production module is
accepted. The stable responsibility is exact-report logical modeling, schema
validation, deterministic JSON, and round trips; extending
`test_satellite_presentations.py` would mix distinct scientific statuses and
fault models.

Use hand-authored accepted synthetic exact results to cover:

- one positive crossing;
- multiple crossings and full NORAD identifiers;
- ordered multiple fields with independent intervals;
- a validated zero-crossing field;
- nullable future-science fields;
- Unicode names and warnings;
- byte-identical repeated serialization;
- typed and byte-identical round trips;
- unknown field, duplicate JSON key, non-finite number, invalid UTC, invalid
  digest, changed schema/product/status, reordered or mismatched context,
  count disagreement, and non-null future-science rejection.

Representative external evidence is not required, discovered, copied, or read
for this implementation gate. The accepted real report had zero crossings and
is provenance for the boundary, not a packaged fixture.

## 9. Ownership and exclusions

The exact-report owner formats retained values only. It does not own:

- crossing solving, propagation, coordinate transformation, or airmass;
- acceleration selection or equivalence;
- snapshot acquisition, admission, or discovery;
- ECSV or VOTable encoding, which remains 50S.6G.2B;
- CLI, request files, validation-output files, or atomic publication, which
  remains 50S.6G.2C;
- exact track sampling, which remains 50S.6G.3A;
- chart integration, illumination, brightness, or detector effects.

No renderer or exporter consumes this report in 50S.6G.2A.

## 10. Candidate implementation boundary

If Fernando scientifically and architecturally accepts this audit, only the
bounded immutable logical model, packaged Draft 2020-12 JSON Schema, pure
deterministic encoder/decoder, and focused tests described above are authorized.

Do not implement ECSV, VOTable, CLI/files, track samples, chart integration,
illumination, magnitude, detector effects, scheduling adapters, provider
access, another real matrix run, or unrelated refactoring.

## 11. Acceptance gate

The documentation audit requires:

- agreement across active architecture, roadmap, implementation reference,
  source tree, coordinate guide, satellite guide, and assistant instructions;
- developer-index and top-level-file allowlist updates;
- documentation tests protecting scientific status, required fields,
  determinism, digest scope, closed-schema behavior, semantic validation,
  test placement, and exclusions;
- coordinate-guide review recording no coordinate-semantic change;
- plugin-disabled current-documentation tests and `git diff --check`;
- Fernando's separate scientific and architectural acceptance.

Until that acceptance, no 50S.6G.2A implementation is authorized.
