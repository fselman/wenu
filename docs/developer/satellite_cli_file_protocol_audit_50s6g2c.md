# 50S.6G.2C CLI and two-call file-protocol audit

Status: documentation-only candidate for Fernando's separate scientific and
architectural acceptance. It changes no runtime and authorizes no
implementation.

## 1. Decision and bounded scope

50S.6G.2C may add one installed offline satellite-crossing command and one
filesystem/publication adapter. The adapter composes the accepted multi-FoV
coordinator and the accepted JSON/ECSV/VOTable exact-report model. It owns
argument parsing, request and validation documents, path safety, publication,
exit status, and interruption cleanup. It owns no orbital, coordinate,
airmass, crossing, report-identity, or tabular-format science.

The bounded implementation after separate acceptance may provide:

- direct CLI calculation from explicit arguments, with whole-request atomic
  validation and atomic no-clobber report-bundle publication;
- a versioned JSON initial-request protocol;
- a first file call that validates every FoV before solving any FoV;
- deterministic validation-output JSON when one or more FoVs are invalid;
- a second explicit call that calculates only the embedded valid subset while
  retaining the invalid-FoV audit record;
- exact JSON, ECSV, and VOTable report files generated only through the
  accepted in-memory encoders.

This audit adds no provider access, acquisition, snapshot discovery, new
execution science, broader admission, positive-crossing search, track sample,
chart layer, visibility rule, illumination, brightness, detector model,
scheduling adapter, or unrelated refactor.

## 2. As-is assessment and ownership

At baseline `35281736c1b85267ba046076c06298f861554d3b`:

- `satellites/crossing_batch.py` owns complete ordered batch validation,
  field-centre complete-interval airmass admission, and exact solving;
- `satellite_crossing_reports.py` owns the immutable exact-local report,
  canonical JSON, strict decode, and `report_identity_sha256`;
- `_satellite_tabular_reports.py` owns the single schema-derived
  format-neutral projection and thin deterministic ECSV/VOTable 1.5 adapters;
- external snapshot loading and digest-bound admission remain explicit and
  offline;
- no installed satellite crossing CLI, request-file schema,
  validation-output schema, or report-bundle publisher exists.

The closest CLI owner is `src/wenu/cli/`. A dedicated satellite command is
warranted because this protocol has a distinct two-call lifecycle, typed exit
contract, and multi-artifact publication transaction. It must not be placed in
`crossing_batch.py`, either report module, `utils`, or the chart CLI.

The closest stable test owners are
`tests/test_satellite_crossing_reports.py` for reuse of accepted report
encodings, the existing batch tests for scientific atomicity, and an enduring
CLI/file-protocol test owner for process status, paths, interruption, and
publication. Lower-level scientific and serialization tests are not repeated.

## 3. One command and three mutually exclusive inputs

The proposed installed command is `wenu_satellite_crossings`. Its calculation
operation accepts exactly one of:

1. direct arguments describing one observer, one explicitly identified
   snapshot, policy, and one or more ordered FoVs;
2. `--request PATH`, naming an initial-request JSON document;
3. `--validated-request PATH`, naming a first-call validation-output JSON
   document.

The command requires an explicit caller-supplied report creation instant. It
must not read the system clock to manufacture scientific report identity.
Direct and initial-file modes have identical domain semantics; only their
input carriers differ.

The direct mode validates the complete request before any solve. On any invalid
FoV it emits a concise ordered diagnostic to stderr, publishes nothing, and
returns the field-validation status. It never silently removes an FoV.

The two file forms are distinct products and are never auto-detected by
filename or opportunistic key inspection. Supplying incompatible input modes,
a validation-output document to `--request`, or an initial request to
`--validated-request` fails before snapshot loading or calculation.

## 4. Initial-request JSON contract

The initial request is UTF-8 JSON governed by a packaged, closed Draft 2020-12
schema. Duplicate object keys, a byte-order mark, invalid UTF-8, non-finite
numbers, unknown properties, wrong product/version values, invalid UTC
instants, duplicate FoV identifiers, and empty fields fail closed.

Version 1 contains:

- fixed product identity and schema version;
- the caller-supplied report creation instant;
- one observer;
- one explicit absolute snapshot-directory path plus expected
  `snapshot_id` and canonical-record `content_sha256`;
- the accepted batch and airmass policy;
- one non-empty semantically ordered `fields` array carrying each stable
  identifier, coordinate specification, inclusive interval, and circular FoV;
- no output paths, provider URL to query, presentation format choice, or
  hidden default catalogue.

Canonical request identity is SHA-256 over deterministic compact UTF-8 JSON of
the complete semantic request payload, excluding only its identity member. The
protocol also records SHA-256 of the exact source bytes. The semantic digest
binds meaning; the source digest binds the particular first-call input. Neither
digest replaces snapshot/report identity.

## 5. First-call validation and invalid FoVs

The first file call parses and semantically validates the complete initial
request, loads and digest-checks the explicit snapshot, constructs every field
request, and runs the accepted whole-batch validation phase in input order
before any crossing solve.

If every FoV is valid, calculation continues atomically and no
validation-output file is created.

If one or more FoVs are invalid:

- no FoV is solved and no report bundle is created;
- every invalid FoV is recorded once in original order with its stable
  identifier, zero-based source index, typed reason code, and deterministic
  human-readable detail;
- every valid FoV remains in original relative order in an embedded derived
  request;
- the complete original ordered field summary remains present, so invalid
  fields are explicit rather than silently absent;
- a missing valid subset is represented by `derived_request: null`;
- exactly one explicitly named validation-output JSON file is published
  atomically and the command returns the field-validation status.

A reason code is stable protocol data. The detail is diagnostic and is not used
to reconstruct or authorize a request. Tracebacks, local temporary names, and
unordered exception representations never enter deterministic output.

The validation-output identity is SHA-256 over canonical JSON excluding only
its own identity member. It binds product/schema version, exact source-byte and
semantic request digests, complete snapshot identity, ordered validation
results, and the embedded derived request.

## 6. Second-call validated-subset calculation

The second call accepts only a validation-output JSON document. It verifies its
closed schema, duplicate-key rule, semantic identity digest, source-request
digests, ordered partition, and snapshot identity before scientific work.

Invalid FoVs remain explicit audit entries but are not reconstructed,
revalidated, propagated, or solved. Wenu constructs only the embedded valid
subset, preserving original identifiers and relative order. It then revalidates
that subset against the current explicit snapshot and accepted current domain
contracts; a changed snapshot, policy/context mismatch, stale/tampered
document, or newly invalid valid-subset field fails closed.

If `derived_request` is null, the second call returns a clear no-valid-fields
status and publishes nothing. It never treats an empty subset as a successful
zero-crossing report.

The resulting exact report records the validation-output identity and ordered
excluded-FoV identifiers in publication provenance outside the canonical
scientific report payload. The accepted exact report and its
`report_identity_sha256` are not changed to encode CLI history.

## 7. Output bundle, filenames, manifest, and digests

Calculation publishes one explicitly named destination directory. Version 1
contains exactly:

- `report.json`, the accepted canonical exact-report JSON bytes;
- `report.ecsv`, the accepted deterministic ECSV bytes;
- `report.vot`, the accepted deterministic VOTable 1.5/BINARY2 bytes;
- `manifest.json`, written last in staging and serving as the completion
  record.

The closed canonical manifest records product/version, command implementation
identity, request mode, request or validation identity, snapshot identity,
`report_identity_sha256`, and for each payload its fixed filename, media
type, byte count, and SHA-256. Its own `manifest_identity_sha256` excludes
only that member. Semantic ordering is fixed, not filesystem enumeration order.

All three report files must decode to the same typed exact report and canonical
JSON identity before publication. ECSV/VOTable are never reparsed as request
files. There is no plain CSV.

## 8. Path, no-clobber, and symlink contract

Input JSON must be an existing non-symlink regular file. The snapshot retains
its accepted explicit non-symlink loader contract. The destination parent and
validation-output parent must already exist as real non-symlink directories.
Each existing path component is checked without silently following a symlink;
the final input/output name is checked again at open or commit time.

The final validation-output path and final bundle directory must not exist.
A regular file, directory, symlink, dangling symlink, or other filesystem entry
at either destination is a no-clobber failure. Version 1 has no `--force`,
overwrite, merge, resume, append, retry, or auto-numbering behavior.

A single-file validation result is written to an exclusive temporary sibling,
flushed, and atomically renamed to the absent final name. A report bundle is
built in a newly created private sibling staging directory; files are created
exclusively, flushed, validated, and the staging directory is atomically
renamed to the absent final directory. The implementation rechecks destination
absence immediately before commit and treats a losing race as no-clobber
failure. It never deletes or replaces a pre-existing user path.

Filesystem atomicity is limited to one filesystem: a cross-device publication
is rejected rather than copied. Parent-directory durability is attempted with
the supported platform primitives and any unsupported durability guarantee is
reported honestly; logical completeness is always defined by a valid final
manifest and matching payload digests.

## 9. Failure atomicity and interruption

Parsing, schema, snapshot, field validation, calculation, encoding, cross-format
round-trip, and manifest construction complete before the publication commit.
Any failure before commit removes only the command-owned staging entry and
leaves the final destination absent.

SIGINT/KeyboardInterrupt returns 130; SIGTERM follows the conventional 143
status when handled. Interruption requests cancellation at safe boundaries,
cleans only verified command-owned staging paths, and never retries or resumes.
It must not catch an interrupt and continue solving another FoV.

The atomic rename is the publication commit point. If interruption occurs after
that rename, the complete digest-valid final artifact is retained and never
deleted as “cleanup”; the process may still return the interruption status.
No partial final bundle or final validation file is considered successful.

Cleanup must use retained parent identity and exact staging name. It must never
recursively remove a path resolved from untrusted JSON, a symlink target, the
destination path, workspace root, home directory, or current directory.

## 10. Exit-status and stdout/stderr contract

Version 1 freezes these statuses:

- `0`: calculation and publication succeeded;
- `2`: command-line usage error (argparse);
- `3`: malformed, schema-invalid, or semantically invalid protocol input;
- `4`: one or more FoVs invalid; in first file mode the deterministic
  validation-output was published successfully;
- `5`: invalid, stale, tampered, mismatched, or empty validated-subset input;
- `6`: unsafe path, existing destination, cross-device, or publication I/O
  failure;
- `7`: snapshot admission, crossing calculation, report construction, or
  format-validation failure;
- `130`/`143`: handled SIGINT/SIGTERM interruption.

If validation-output publication itself fails, status 6 supersedes status 4
because no promised audit artifact exists. Expected failures emit one concise
diagnostic to stderr without traceback. Success emits a concise manifest path
and report identity to stdout. Scientific/report bytes never share stdout with
diagnostics.

## 11. Determinism and service isolation

For identical accepted inputs and implementation/dependency identities,
request JSON normalization, validation-output JSON, report encodings, and
manifest bytes are deterministic. Path spelling may be recorded only where the
protocol explicitly requires the absolute snapshot reference; temporary paths,
process IDs, random staging suffixes, wall-clock time, locale, directory order,
and exception reprs are excluded.

The command is offline. Tests must prove that neither call accesses a provider,
downloads IERS data, consults the clock, discovers a snapshot, or changes
crossing science. The second call must prove that invalid FoVs do not reach the
airmass evaluator, propagator, exact solver, or report constructor.

## 12. Implementation seam and test admission

After separate audit acceptance, the bounded implementation may add:

- one dedicated CLI/filesystem adapter under `src/wenu/cli/`;
- packaged closed schemas for initial request, validation output, and bundle
  manifest when executable validation requires them;
- one installed script entry;
- focused process/filesystem tests owned by the durable CLI/file protocol;
- minimal documentation/source-tree updates required by those additions.

The adapter calls public accepted domain/report APIs. It does not duplicate the
JSON report encoder, the shared tabular projection, field validation, snapshot
validation, or crossing solve.

Focused evidence must cover direct success and invalid atomicity; positive and
zero-crossing reports; first-call all-valid and mixed-validity behavior;
no-valid-subset refusal; deterministic output; exact partition and order;
tamper/staleness; all fixed exit statuses; existing files/directories and
dangling symlinks; malicious path forms; publication races; injected failures
before and after each staging phase; SIGINT/SIGTERM before and after commit;
cross-format identity; and proof that invalid FoVs are not recomputed on the
second call.

## 13. Coordinate-guide review and exclusions

`coordinate_system_guide_v0.9.5.md` was reviewed for this audit and remains
scientifically current. 50S.6G.2C introduces no new frame, transformation,
refraction, airmass definition, field geometry, or satellite-state meaning. It
only transports already accepted coordinate documents and calls the accepted
centre-only complete-interval validator.

This candidate authorizes no implementation. After Fernando's separate
scientific and architectural acceptance, only the bounded CLI/file-protocol
implementation described here becomes eligible. 50S.6G.3A and every track,
chart, planisphere, illumination, brightness, provider, or new-execution
milestone remain separately unauthorized.

## 14. Accepted audit and implementation handoff

Fernando scientifically and architecturally accepted this documentation-only
50S.6G.2C audit on 2026-09-19 at
`bcac40453ae244348b9fc33447246db1c587d722`, after all 188 plugin-disabled
current-documentation tests passed in 5.29 seconds; the diff check and
synchronized Mac working tree were clean.

Implement only the bounded offline CLI/filesystem adapter, closed initial and
validation JSON protocols, explicit validated-subset second call, fixed
JSON/ECSV/VOTable report bundle and digest manifest, path and symlink checks,
no-clobber atomic publication, typed exit statuses, interruption cleanup, and
focused tests specified here. Preserve the accepted batch science and report
encoders without duplication. This acceptance does not authorize provider
access, new execution science, tracks, charts, visibility, illumination,
brightness, detector effects, scheduling adapters, or unrelated refactoring.

## 15. Candidate implementation verification

Treat the bounded implementation at
`e08ebf5e0061dbf1e69c8cc58a55a9696e785300` as a verified candidate awaiting
Fernando's separate scientific and architectural acceptance. On Fernando's
Mac, the 235-test immediate CLI/batch/report/documentation gate passed in 7.63
seconds; the complete 2,709-test plugin-disabled suite passed in 237.35
seconds. The module help preflight, diff check, synchronized branch, and clean
working tree also passed.

This evidence establishes repository compatibility, not acceptance. Preserve
the offline adapter, validation-only coordinator seam, three closed schemas,
fixed report bundle, no-clobber/symlink/exit/interruption contracts, and focused
fault coverage. Do not merge or begin 50S.6G.3A before separate acceptance.

## 16. Accepted implementation and next boundary

Fernando scientifically and architecturally accepted the bounded 50S.6G.2C
implementation on 2026-09-19. Executable commit
`e08ebf5e0061dbf1e69c8cc58a55a9696e785300` passed the 235-test immediate
gate in 7.63 seconds and all 2,709 plugin-disabled tests in 237.35 seconds.
Documentation evidence commit `f2bb49c6f44281428d546d5d2adbf35f74b7fc6d`
passed all 191 current-documentation tests in 5.50 seconds. CLI help, diff,
branch synchronization, and working-tree checks were clean.

Preserve the offline adapter, public validation-only coordinator seam, three
closed schemas, explicit invalid-field evidence, revalidated valid-subset
second call, accepted JSON/ECSV/VOTable encoders, fixed digest manifest,
no-clobber and symlink safety, typed exit statuses, and interruption cleanup.
This acceptance authorizes no provider access, new execution science, track,
chart, visibility, illumination, brightness, detector, or scheduling work.
Only a separately bounded documentation-first 50S.6G.3A exact-local-track
audit is authorized next; no track implementation is authorized.
