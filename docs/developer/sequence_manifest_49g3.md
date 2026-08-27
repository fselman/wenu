# Deterministic sequence manifests and resume

**Milestone:** 49G.3  
**Status:** implemented; real restart/resume acceptance complete  
**Base:** `542a97f`

## Purpose

49G.3 makes an observer-time sequence restartable without treating an
arbitrary existing file as a valid scientific result.

The manifest is a portable deterministic statement of the complete planned
sequence plus independently verified completion records. It does not create a
second chart, astronomy, projection, rendering, or export path.

## Public contracts

`wenu.charts.sequence_manifest` defines:

- `ObserverTimeSequenceManifest`;
- `SequenceManifestFrame`;
- `SequenceRestartPolicy`;
- `SEQUENCE_MANIFEST_SCHEMA_VERSION`;
- `SEQUENCE_MANIFEST_NAME`;
- deterministic read, fresh-write, and progress-update functions.

`generate_observer_time_chart_sequence()` accepts:

- `restart_policy="restart"`, the default;
- `restart_policy="resume"`;
- an optional explicit manifest path.

Its result exposes the manifest path and rendered/reused frame counts. Each
frame result explicitly reports whether it was rendered now or safely reused.

## Deterministic identity

Schema version 1 records:

- sequence kind;
- complete normalized chart request;
- output format and every other product choice;
- physical time scale;
- display timezone;
- sampling kind;
- optional playback duration and frame rate;
- ordered frame indices, names, simulation instants, and display instants.

The base chart observer time is excluded because the ordered timeline owns
every frame instant. The output directory is excluded so the same sequence
plan can be moved without changing identity. Expected filenames and output
format remain part of identity.

Sets and mappings are deterministically ordered. Datetimes retain explicit UTC
offsets. Enums, paths, timedeltas, nested immutable dataclasses, tuples, and
optional values have explicit JSON representations. The canonical compact
identity payload is hashed with SHA-256. Pretty JSON bytes are deterministic.

The manifest does not use Python `repr()`, object addresses, Matplotlib
serialization, or mutable global state.

## Completion records

A frame begins without a completion record. After canonical static generation
returns the exact planned output, Wenu records:

- output byte count;
- SHA-256 of the complete file.

Progress is written atomically after each completed frame. Completion records
do not alter the plan identity.

A crash before the completion record is committed leaves the frame untrusted.
A later resume renders it again. This may repeat work, but it cannot silently
accept an incomplete result.

## Restart and resume policy

`restart`:

1. creates a fresh manifest for the requested plan;
2. renders every frame through `generate_chart_request()`;
3. replaces each prior completion record after successful output verification.

`resume`:

1. reads an existing manifest when present;
2. rejects it before rendering if its plan identity is incompatible;
3. reuses a frame only when the recorded filename, byte count, and SHA-256
   match the existing file;
4. renders missing, unrecorded, truncated, replaced, or altered frames;
5. creates a fresh manifest and renders normally when no manifest exists.

A reused result has no fabricated `ChartRequestGeneration`. Its disposition
is explicitly `reused`. A newly rendered result retains the ordinary complete
static generation.

## Architectural boundary

49G.3 does not add:

- CLI or TOML configuration;
- FFmpeg execution inside the package;
- multi-product sequences;
- temporal caching or shared mutable sky state;
- provider-time or celestial-realization-epoch sequences;
- weaker alternatives to canonical static generation.

Independent complete frames remain the correctness oracle. Hash verification
establishes file identity, not astronomical equivalence between different
plans.

## Acceptance criteria

The milestone requires tests proving:

- deterministic identity across different output directories and irrelevant
  base observer times;
- changed chart or timeline rejection;
- schema, offset, unknown-field, and hash validation;
- atomic write and round-trip preservation;
- completion records that do not alter plan identity;
- reuse of every valid completed frame;
- rerender of only an altered frame;
- rejection of an incompatible manifest before rendering;
- unconditional rendering under explicit restart;
- real canonical PNG generation followed by zero-render verified resume.

CLI/configuration exposure remains Milestone 49G.4.


## Real-directory acceptance

A three-frame circumpolar PNG sequence was generated on the Mac under
`/tmp/wenu-49g3-resume`. The audit then preserved frame 0, deleted frame 1,
and replaced frame 2 with incomplete bytes.

Verified behavior:

| Pass | Rendered | Reused | Result |
| --- | ---: | ---: | --- |
| initial restart | 3 | 0 | complete manifest and three outputs |
| selective resume | 2 | 1 | missing and altered frames restored |
| fully valid resume | 0 | 3 | no canonical render repeated |

The selective pass reported `reused, rendered, rendered`. All recovered
SHA-256 values matched the original outputs exactly. The final manifest used
schema 1, sequence kind `observer_time`, and identity
`7f31dee56261ea167c42b394135a3d11ddf93251c07c21143a00c168ce8155f9`.

The focused contract, real-frame, documentation, request-generation,
renderer-boundary, and package-boundary suite passed:

```text
82 passed in 27.29s
```

The clean branch full suite then passed:

```text
1721 passed in 83.03s
```
