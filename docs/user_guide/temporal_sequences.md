# Observer-time chart sequences

The installed `wenu_chart` command can generate a uniformly sampled series
of ordinary static charts. Every frame uses the same chart request,
configuration, projection, composition, renderer, and exporter as a one-frame
chart. Only the observer time changes.

## Command-line sequence

`--observer-time` supplies the inclusive start. `--sequence-stop` supplies
the inclusive end and must be an ISO 8601 datetime with an explicit UTC
offset. `--sequence-frames` includes both endpoints.

```bash
wenu_chart circumpolar \
  --observer-location "La Ligua" \
  --observer-time "2026-08-21T21:00:00-04:00" \
  --sequence-stop "2026-08-22T03:00:00-04:00" \
  --sequence-frames 3 \
  --display-timezone America/Santiago \
  --pole south \
  --limiting-declination -60 \
  --format png \
  --output output/circumpolar-sequence
```

A sequence requires one explicit output format and an output directory.
`--all-products` and a suffixed single-file output are rejected.

The generated files are named `frame-0000.png`, `frame-0001.png`, and so
on. The output directory also contains
`wenu-sequence-manifest.json`.

## Physical time and playback

Simulation time is physical UTC time. `--display-timezone` changes only the
civil-time representation recorded for each frame. It does not change the
physical instant.

Optional playback metadata is likewise presentation-only:

```text
--playback-duration 12
--frames-per-second 12
```

Their product must equal the requested frame count. Wenu records these values
in the manifest; it does not invoke FFmpeg or create a movie in this
milestone. Playback speed must never be interpreted as physical time.

## Restart and verified resume

The default `--restart-policy restart` starts a fresh manifest and renders
every frame.

`--restart-policy resume` first requires a compatible manifest. A completed
frame is reused only when its filename, byte count, and SHA-256 digest still
match. Missing, truncated, replaced, or altered frames are rendered again
through the canonical static generator.

A regenerated PNG is required to be scientifically and visually equivalent.
PNG compression bytes may differ between separate processes even when decoded
pixels and declared PNG metadata are identical. The manifest records and
verifies the actual bytes of the current completed file.

## TOML configuration

The packaged profile is disabled by default:

```toml
[sequence]
stop = "none"
frames = "none"
display_timezone = "none"
playback_duration = "none"
frames_per_second = "none"
restart_policy = "restart"
```

A profile activates a sequence by supplying both `stop` and `frames`.
Playback duration and frame rate must likewise be supplied together. Explicit
CLI arguments override the profile.

```toml
[sequence]
stop = "2026-08-22T03:00:00-04:00"
frames = 25
display_timezone = "America/Santiago"
playback_duration = 2.0
frames_per_second = 12.5
restart_policy = "resume"
```

The complete translated effective configuration participates in manifest
identity. A resume using different style, mode, detail, furniture, observer,
or sequence configuration is therefore rejected rather than silently mixing
products.

## Scope

This contract generates complete independent static frames. It introduces no
alternate sky, projection, rendering, or export pipeline and performs no
scientific caching.

Observed Moon disks within one fixed chart are supported separately from
observer-time sequences; see
[configuration and Solar-System controls](configuration.md). Fixed-sky
presentation remains a separately governed reference path, and scientifically
keyed reuse remains future 49J work. Video encoding, interpolation, and
artificial-satellite sequences remain outside this contract.
