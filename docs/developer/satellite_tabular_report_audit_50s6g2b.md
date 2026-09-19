# 50S.6G.2B ECSV and VOTable interoperability audit

**Status:** Candidate documentation-only scientific, logical, and interoperability
contract. No 50S.6G.2B implementation is authorized until Fernando separately
accepts this audit.

**Parent authority:** `satellite_delivery_audit_50s6g.md`

**Input authority:** the accepted
`wenu.artificial_satellite_exact_crossing_report` version-1 logical model and
its canonical JSON identity.

## 1. Decision

50S.6G.2B may add two lossless, in-memory interoperability encodings of the
accepted exact-crossing report:

- Astropy Enhanced Character-Separated Values (ECSV), as one table with an
  explicit `record_kind` discriminator;
- IVOA VOTable 1.5, as one RESOURCE containing separate `report`, `field`,
  and `crossing` TABLE elements joined by stable identifiers.

Neither encoding is a new scientific product. Both are alternate carriers of
the same immutable version-1 report. Encoders consume an already validated
`ExactSatelliteCrossingReport`; decoders must reconstruct that type and then
pass its existing closed-schema, semantic, ordering, and digest validation.
They perform no propagation, coordinate transformation, crossing search,
airmass calculation, acceleration, visibility evaluation, or future science.

## 2. Identity and determinism

`report_identity_sha256` remains the canonical logical identity. It is
recomputed from the accepted compact JSON scientific payload, never from ECSV
or XML bytes. Successful decoding requires the reconstructed report identity
to equal the identity carried by the input.

ECSV and VOTable bytes are deterministic only for the declared Wenu encoder
identity and supported Astropy version. XML lexical details and YAML header
formatting are not promoted to cross-tool scientific identity. The required
portable invariant is:

```text
from_ecsv(report.to_ecsv()) == report
from_votable(report.to_votable()) == report
decoded.report_identity_sha256 == report.report_identity_sha256
decoded.to_json() == report.to_json()
```

Repeated encoding by the same accepted encoder must return identical UTF-8
ECSV text or identical VOTable XML bytes. Format metadata records the Wenu
encoder identity, Astropy version, report schema version, and logical digest.

## 3. Shared lossless mapping rules

Both encodings preserve every required JSON value, exact array order, explicit
zero-crossing fields, Unicode, integer NORAD identifiers, warnings,
provenance, caller-supplied creation time, observer and snapshot identity,
batch policy, airmass and acceleration evidence, coordinate meaning,
tolerances, and nullable future-science fields.

Stable keys are `field_ordinal`, `field_id`, `crossing_ordinal`, and
`norad_catalog_id`. Ordinals are zero-based integers and are the normative
array-order reconstruction mechanism. A field row exists even when its
`crossing_count` is zero; it then has no crossing rows. Empty arrays are not
confused with missing values.

Physical columns use explicit units accepted by Astropy and VOTable:
`deg`, `m`, `km`, `s`, and `deg / s`. Dimensionless counts,
identifiers, hashes, classifications, policies, and provenance have no unit.
UTC instants retain the accepted fixed microsecond `...Z` lexical form.
No encoder rounds or changes a floating-point value.

Version-1 `illumination`, `apparent_magnitude`, `detector_effect`, and
`exact_track_samples` remain null/not evaluated. A non-null value is rejected;
the tabular format cannot authorize 50S.6G.3 or later science.

## 4. ECSV contract

The public candidate boundary is pure text:
`report.to_ecsv() -> str` and
`ExactSatelliteCrossingReport.from_ecsv(text_or_utf8_bytes)`.

The table contains `report`, `field`, and `crossing` rows selected by
`record_kind`. Exactly one report row is required. Every accepted field has
one field row, including a validated field with zero crossings. Crossing rows
reference a field by both ordinal and identifier.

The fixed column set is the union of the flattened record shapes. Columns
inapplicable to a row kind are masked, using Astropy's explicit
`serialize_method="data_mask"` representation so an empty string is never
silently converted into a missing value. Nested ordered strings and integer
partitions use JSON-array text in specifically named columns; they are parsed
with strict JSON and checked against fixed element types. Arbitrary object
columns or executable/custom YAML classes are forbidden.

Required table metadata includes:

- `wenu_product`, `wenu_scientific_status`, `wenu_report_schema_version`;
- `wenu_tabular_schema_version = 1` and
  `wenu_tabular_format = "ecsv"`;
- `report_identity_sha256`, `wenu_tabular_encoder`, and
  `astropy_version`;
- retained coordinate frame, origin, position status, time scale,
  refraction policy, and Earth-orientation policy.

The decoder requires ECSV 1.0, the fixed ordered physical column set, exact
dtypes, exact units, exact masks, allowed metadata only, and the expected row
ordering: report first, then each field followed immediately by its crossings.
It rejects duplicate or unknown columns, unknown metadata, unexpected mixin or
serialized classes, reordered or orphaned rows, and context duplicated with a
different value.

## 5. VOTable contract

The public candidate boundary is pure bytes:
`report.to_votable() -> bytes` and
`ExactSatelliteCrossingReport.from_votable(xml_or_utf8_bytes)`.
Text input may be accepted only after strict UTF-8 encoding. The accepted
writer uses VOTable 1.5 and `BINARY2`, whose null flags can represent missing
values for every datatype.

One RESOURCE with a fixed ID contains exactly three TABLEs in order:
`report` (one row), `field` (one row per field), and `crossing` (zero or
more rows). The field table makes zero-crossing validation representable.
Version 1 has no sample TABLE.

VOTable-specific metadata are built with `astropy.io.votable` objects and
written from the resulting `VOTableFile`; conversion through a bare
`Table.write(format="votable")` is insufficient because it can discard PARAM
and INFO metadata. FIELD values declare fixed `datatype`, `arraysize`, unit,
ID, name, and description. PARAM values carry product, status, schema,
encoder, Astropy version, digest, and retained coordinate policies. UCDs may
aid discovery but never replace Wenu names or semantics.

A VOTable 1.5 TIMESYS element with `timescale="UTC"` and
`refposition="TOPOCENTER"` is required and referenced by every UTC FIELD.
The RESOURCE also carries the accepted topocentric GCRS-axes direction
identity; TIMESYS does not imply a coordinate transformation or an
astrometric-position claim.

The decoder rejects external entities and remote references, multiple or
unknown RESOURCEs/TABLEs, unknown FIELDs/PARAMs/INFOs, duplicate IDs, unsafe
XML constructs, unsupported serialization, unit/datatype/arraysize/null-policy
changes, missing TIMESYS references, row-count or join mismatches, non-finite
numbers, and any warning from strict VOTable validation. It applies bounded
input-size and row-count limits before constructing the logical report.

## 6. Reusable architecture contract

The implementation must separate the accepted logical report, one shared
reusable format-neutral tabular projection, and thin format adapters:

```text
ExactSatelliteCrossingReport
        <-> shared validated tabular records
        <-> ECSV adapter / VOTable adapter
```

One internal immutable projection owns record kinds, fixed field definitions,
ordinals and joins, units, masks/nulls, metadata names, logical reconstruction,
and resource limits. ECSV and VOTable adapters only translate that projection
to or from their wire syntax. They must not duplicate scientific flattening,
ordering, unit, join, or reconstruction rules.

The shared projection and validators should be small pure helpers with names
and responsibilities that can be reused by 50S.6G.2C publication and future
additional lossless encodings. They accept and return values or text/bytes,
never paths. Format-specific metadata such as ECSV serialization directives,
VOTable FIELD/PARAM objects, TIMESYS, and XML validation remains in thin
format adapters.

Reuse does not mean premature public API. Only the report encode/decode methods
are public in 50S.6G.2B; shared helpers remain private until another accepted
consumer proves a stable public abstraction. Existing JSON schema validation
and typed semantic reconstruction are reused as the final authority rather
than reimplemented.

Tests must exercise the shared projection independently, require both adapters
to reconstruct the same canonical JSON, and use common parameterized
corruption cases where the failure rule is format-neutral. Adapter-only tests
cover syntax-specific metadata and security. No copy-pasted ECSV/VOTable field
map or validator is acceptable.

## 7. Failure and security contract

Malformed UTF-8, ECSV/YAML, JSON-array cells, or XML fails closed. Decoding
does not access the network, filesystem, clock, provider, IERS download,
propagator, or crossing engine. It does not accept paths or file-like objects.
Duplicate semantic keys, unsupported versions, unknown content, non-finite
numbers, invalid calendar instants, changed units, changed coordinate
metadata, masked required values, unmasked inapplicable values, digest
mismatch, and any accepted logical invariant violation raise a stable
`ValueError`-class failure.

Resource limits cover bytes, rows, columns, string lengths, and nested JSON
cell lengths. Tests must demonstrate that XML entity expansion and external
entity resolution are unavailable.

## 8. Candidate ownership and tests

If this audit is accepted, the bounded implementation may add one focused
private tabular-interchange module adjacent to
`src/wenu/satellite_crossing_reports.py`, or keep equivalently focused private
helpers in that owner if the implementation preflight shows a separate module
would be artificial. The decision must minimize coupling and make the shared
projection reusable without moving JSON or scientific ownership. Public report
methods delegate to it. `tests/test_satellite_crossing_reports.py` remains
the stable public-contract test owner; a focused private-helper test file is
allowed only if it materially clarifies shared projection responsibility.

A packaged tabular schema is not introduced: the fixed mapping is code-owned
once beside the accepted logical model and verified by tests.

Required tests cover positive and validated-zero fields; multiple fields and
crossings; Unicode and empty strings; masks versus empty values; exact dtypes,
units, TIMESYS, coordinate metadata, and joins; deterministic same-encoder
bytes; ECSV and VOTable typed round trips back to byte-identical canonical
JSON; rejection of unknown, duplicate, malformed, unsafe, oversized,
non-finite, reordered, orphaned, and digest-changing inputs; and proof that
decoding performs no service, filesystem, clock, propagation, coordinate, or
crossing work.

## 9. Explicit exclusions and next gate

50S.6G.2B does not include plain CSV, FITS, Parquet, CLI commands, paths,
overwrite policy, filenames, atomic publication, manifests, exact tracks,
charts, illumination, magnitude, detector effects, scheduling adapters,
provider access, another real matrix run, or unrelated refactoring.

Atomic filesystem publication belongs to 50S.6G.2C. Exact tracks belong to
50S.6G.3A. Until Fernando's separate scientific and architectural acceptance,
no 50S.6G.2B implementation is authorized.

## References

- Astropy, “ECSV Format”:
  https://docs.astropy.org/en/stable/io/ascii/ecsv.html
- Astropy, “VOTable Handling”:
  https://docs.astropy.org/en/stable/io/votable/
- IVOA Recommendation, “VOTable Format Definition, Version 1.5”:
  https://www.ivoa.net/documents/VOTable/20231115/


## Candidate verification evidence

The documentation candidate at `ef14bc1` passed all 181 plugin-disabled
`tests/test_current_documentation.py` tests in 4.88 seconds.
`git diff --check 57c8bec...HEAD` passed, and the working tree was clean,
synchronized with `origin/docs/50s6g2b-tabular-report-audit`.

This evidence verifies documentation consistency only. The audit remains
candidate documentation; it does not authorize 50S.6G.2B implementation.
