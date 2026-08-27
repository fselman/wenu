# Installed temporal sequence CLI and configuration

**Milestone:** 49G.4  
**Status:** implemented; installed-CLI restart/resume acceptance complete  
**Base:** `46eba51`

## Purpose

49G.4 exposes the accepted 49G.1–49G.3 contracts through the installed
`wenu_chart` command and schema-version-1 TOML configuration. It adds no
second astronomical, projection, rendering, or export path.

## Shared translation boundary

Static and sequence commands resolve through the same command-line argument
plan and the same immutable `ChartRequest`. The shared plan owns:

- subject and framing;
- selected style, mode, and output format;
- astronomical content and grid selection;
- detail and visual overrides;
- furniture, legends, title, language, and credits;
- translated effective TOML configuration.

Static generation passes that plan to `draw_chart_view()`. Sequence
generation converts the same plan with `chart_view_request()`, pairs it with
a `TemporalTimeline`, and delegates every frame to
`generate_observer_time_chart_sequence()`. That function continues to call
only `generate_chart_request()`.

## Public CLI vocabulary

```text
--sequence-stop TIME
--sequence-frames COUNT
--display-timezone IANA_ZONE
--playback-duration SECONDS
--frames-per-second FPS
--restart-policy {restart,resume}
```

`--observer-time` owns the inclusive start. The stop is inclusive and
requires an explicit UTC offset. A sequence requires one explicit format and
an output directory.

Playback duration and rate are presentation metadata. They must imply exactly
the requested frame count and never change physical simulation time.

## Configuration ownership

`ConfigurationDefaults` now includes immutable `SequenceDefaults`. The
packaged `[sequence]` table is disabled by default. A user overlay activates
it only by specifying both stop and frame count. CLI values override
configuration values.

The complete translated effective configuration is passed to every canonical
static frame and included in manifest identity. Resume therefore rejects a
configuration change before rendering instead of combining products created
under different styles, modes, detail, or furniture.

Existing programmatic sequences with `configuration=None` preserve their
previous schema-1 manifest document representation.

## Validation

Configuration and CLI adapters reject:

- stop without frame count or frame count without stop;
- fewer than two uniform frames;
- playback duration without frame rate or the inverse;
- nonpositive playback values;
- playback cadence inconsistent with frame count;
- display, playback, or resume controls without a sequence;
- a stop without an explicit UTC offset;
- all-products, implicit-format, and single-file sequence outputs.

## Installed-CLI acceptance

A real three-frame circumpolar sequence was generated on the Mac through
`wenu_chart`:

| Frame | Simulation UTC | Civil display time | Bytes | SHA-256 prefix |
|---|---|---|---:|---|
| frame-0000.png | 2026-08-22T01:00:00+00:00 | 2026-08-21T21:00:00-04:00 | 364,582 | b6b92d5b4d7b |
| frame-0001.png | 2026-08-22T04:00:00+00:00 | 2026-08-22T00:00:00-04:00 | 364,807 | 7471e7a8a409 |
| frame-0002.png | 2026-08-22T07:00:00+00:00 | 2026-08-22T03:00:00-04:00 | 357,064 | 237ed44a6525 |

The manifest was schema 1, kind `observer_time`, recorded the effective
configuration, and had identity
`eaf7f6d8cfbfb27376baf85bfb80613a86b67f0f0a40458961386299efac2f68`.

Frame 1 was replaced by an incomplete file and the same installed command was
run with `--restart-policy resume`. Frames 0 and 2 retained their exact
bytes and modification times. Only frame 1 was regenerated.

The regenerated PNG had the same dimensions, pixel-identical decoded RGBA
content, and identical declared Matplotlib and DPI metadata as the original.
Its compressed PNG bytes differed across the separate processes. The
manifest correctly recorded the newly verified bytes; the contract does not
misrepresent compression-byte identity as scientific or visual identity.

The completed focused CLI, configuration, static drawing, sequence,
manifest, documentation, package, and renderer set passed:

```text
163 passed in 28.30s
```

Final repository verification from a clean synchronized branch passed:

```text
1744 passed in 80.10s
```

## Remaining 49G scope

49G.4 does not add FFmpeg execution, video output, moving-object providers,
proper-motion propagation, cross-frame scientific caches, or the fixed-sky
rotating-horizon presentation. Complete independent frames remain the
correctness oracle for those later milestones.
