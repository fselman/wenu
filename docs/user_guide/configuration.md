# Unified command and editable configuration

Installing Wenu provides one command for every ordinary chart family:

```text
wenu_chart all-sky ...
wenu_chart planisphere ...
wenu_chart regional ...
wenu_chart circumpolar ...
wenu_chart binocular ...
```

## Create an editable template

Create the destination directory, then export Wenu's complete commented
version-1 configuration:

```bash
mkdir -p profiles
wenu_chart defaults --write profiles/publication.toml
```

The command prints the written path. The file is an exact UTF-8 copy of the
installed `defaults.toml`: comments, schema version, section and key order,
formatting, and final newline are reproducible. Running the command again for
the same path replaces that file. It does not create a missing parent
directory.

Use the edited file with any chart family:

```bash
wenu_chart regional \
  --config profiles/publication.toml \
  --constellations Cen,Cru,Mus \
  --output output/centaurus-cross-musca.png
```

Explicit command-line values override the selected file, which in turn
overrides Wenu's packaged defaults:

```text
packaged defaults.toml < --config TOML < explicit CLI arguments
```

Without `--write`, `wenu_chart defaults` prints the same complete document to
standard output.

## Valid line styles

Every configurable line-bearing element independently declares `color`,
`line_width`, and `line_style`. The complete version-1 `line_style` vocabulary
is:

- `solid`
- `dashed`
- `dotted`
- `dash_dot`
- `none`

Other spellings are rejected with the complete configuration path.

## Named profiles

Profiles are normal TOML files whose filenames describe their purpose. They
do not require Python changes:

| Profile | Typical sections to edit |
|---|---|
| `publication.toml` | atlas style, print mode, product and export |
| `presentation.toml` | presentation mode, canvas, labels and symbols |
| `outreach.toml` | cartoon style, larger labels, legends and furniture |
| `papudo.toml` | observer location, elevation, timezone and time |
| `binocular-observing.toml` | subject, binocular field and detail limits |

Each command accepts one profile:

```bash
wenu_chart planisphere --config profiles/papudo.toml
```

Version 1 intentionally has no profile inheritance or multi-file stacking.
When one chart needs choices from several themes, keep a dedicated combined
profile. An inheritance feature should be added only if experience with these
ordinary single-file overlays demonstrates that it is necessary.


## Output format in profiles

For a one-off command, select the public format explicitly:

```bash
wenu_chart regional ... --format svg --output output/chart.svg
```

A reusable TOML profile may instead set the existing product extension:

```toml
[products.default]
extension = ".svg"
```

Version 1 accepts `.png`, `.pdf`, and `.svg` output extensions. SVG always
uses Wenu's editable-text contract; there is no TOML font-policy switch.
An explicit CLI `--format` overrides extension-based selection for generated
names and must agree with an explicitly suffixed single-file `--output`.

The mode setting `prefer_vector` is an appearance/export preference retained
by the configuration schema. It does not itself choose PDF or SVG. Choose the
format with `--format` or `products.default.extension`.

See [SVG output and editing](svg_output.md) for semantic metadata, supported
editor operations, font substitution, and the safe Inkscape workflow.


## Observer-time sequence profiles

The packaged `[sequence]` table is disabled with `stop = "none"` and
`frames = "none"`. A profile activates uniform observer-time generation by
setting both values. Optional `playback_duration` and `frames_per_second`
must also be supplied as a pair and must imply the configured frame count.

```toml
[sequence]
stop = "2026-08-22T03:00:00-04:00"
frames = 25
display_timezone = "America/Santiago"
playback_duration = 2.0
frames_per_second = 12.5
restart_policy = "resume"
```

The ordinary observer time is the inclusive sequence start. Explicit
`--sequence-stop`, `--sequence-frames`, `--display-timezone`, playback, and
restart arguments override these profile values. See
[Observer-time chart sequences](temporal_sequences.md) for the complete
physical-time and verified-resume contract.
