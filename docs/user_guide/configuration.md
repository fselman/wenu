# Unified command and editable configuration

Object-label orientation defaults to the chart family. The mutually exclusive
`--labels-upright` and `--labels-up-away-from-cp` overrides leave grid labels,
reference names, and track dates under their existing policies. The latter
requires a polar-planisphere chart. TOML uses
`styles.atlas.canvas.labels_orientation` (or `styles.cartoon.canvas`) with
`chart`, `upright`, or `up-away-from-cp`; explicit CLI values take precedence.
See the [label placement and typography guide](labels.md) for scope,
limitations, proposed grid policy, and references.

For one runnable command per chart family, begin with the
[complete chart examples](chart_examples.md).

Installing Wenu provides one command for every ordinary chart family:

```text
wenu_chart all-sky ...
wenu_chart planisphere ...
wenu_chart regional ...
wenu_chart circumpolar ...
wenu_chart binocular ...
```

`[constellations].system` defaults to `"western"`. It supplies vocabulary
and line-figure semantics only when a constellation operation is explicitly
requested; it does not enable lines, labels, boundaries, or masking.

## Create an editable template

Create the destination directory, then export Wenu's complete commented
version-2 configuration:

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
  --center-on constellation:Cen,Cru,Mus \
  --output output/centaurus-cross-musca.png
```

Explicit command-line values override the selected file, which in turn
overrides Wenu's packaged defaults:

```text
packaged defaults.toml < --config TOML < explicit CLI arguments
```

Without `--write`, `wenu_chart defaults` prints the same complete document to
standard output.

## All visible constellations and exclusions

Each constellation feature accepts an explicit IAU list or `all`:

```text
--constellation-labels all --constellation-labels-exclude Oct,Hyi
--constellation-lines all --constellation-lines-exclude Oct
--constellation-boundaries all --constellation-boundaries-exclude Hyi
```

The three selections are independent. Exclusions win over both `all` and
explicit inclusion, and never enable a feature. Options may be repeated;
`all` must be the sole token in its comma-separated argument. Exclusions
require explicit IAU codes. `Ser` includes or excludes both Serpens regions.
Star-name and Bayer selections remain independent.

`all` uses the existing chart projection and clipping, including partial
constellation figures and regions. Automatic constellation-name anchors use
the visible IAU region when the usual anchor falls outside the chart. A thin
visible fragment still qualifies, though typography may be clipped at the
edge. This feature does not change constellation subjects or mask syntax.

The equivalent optional version-2 configuration is:

```toml
[detail.constellations]
labels = ["all"]
lines = ["all"]
boundaries = []
labels_exclude = ["Oct", "Hyi"]
lines_exclude = ["Oct"]
boundaries_exclude = []
```

All six lists default empty. An explicit CLI option replaces the corresponding
configuration list; the other five lists retain their configured values.

## Valid line styles

Every configurable line-bearing element independently declares `color`,
`line_width`, and `line_style`. The complete version-2 `line_style` vocabulary
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
| `binocular-observing.toml` | center, binocular field and detail limits |

Each command accepts one profile:

```bash
wenu_chart planisphere --config profiles/papudo.toml
```

Version 2 intentionally has no profile inheritance or multi-file stacking.
When one chart needs choices from several themes, keep a dedicated combined
profile. An inheritance feature should be added only if experience with these
ordinary single-file overlays demonstrates that it is necessary.

## Planet symbols

Every ordinary chart family can add apparent major planets with `--planet`.
Supply a comma-separated list, repeat the option, or combine both forms:

```bash
wenu_chart planisphere \
  --planet mercury,venus,mars,jupiter \
  --planet saturn,uranus,neptune \
  --output output/planets.png
```

Wenu plots the conventional astronomical symbol while retaining the complete
planet name in the chart's semantic metadata:

| CLI name | English name | Symbol |
|---|---|:---:|
| `mercury` | Mercury | ☿ |
| `venus` | Venus | ♀ |
| `mars` | Mars | ♂ |
| `jupiter` | Jupiter | ♃ |
| `saturn` | Saturn | ♄ |
| `uranus` | Uranus | ♅ |
| `neptune` | Neptune | ♆ |

Planet names are case-insensitive. Earth is the observer's reference body and
is not a drawable apparent target. In atlas presentation mode, planet symbols
use the same Venus cream as the chart's other planetary marks.


## Installed numbered asteroids and dated tracks

Wenu can draw the apparent position and dated track of a numbered asteroid.
With the default `acquire-if-missing` policy, the installed `wenu_chart`
command verifies its immutable cache and downloads a bounded Horizons SPK
during preflight when necessary. Chart construction and rendering remain
offline. Selection by permanent number therefore needs no separate download:

```bash
wenu_chart regional --center-on asteroid:79989 --asteroid 79989 \
  --observer-time 2026-01-15T00:00:00Z \
  --field-width 20 --field-height 15 --output output/79989.png
```

The preflight writes a structured `acquisition-report.json` plus bounded,
content-addressed Horizons SPKs and verifies identity against JPL SBDB.
Use `--data-policy offline` to prohibit downloads or `--data-policy refresh`
to request a new provider solution. The same default is configurable as:

```toml
[data]
moving_object_policy = "acquire-if-missing"
```

An explicit `--minor-body-resource-directory` remains authoritative, is
validated for every requested identity and epoch, and is never modified or
refreshed. Automatic asteroid acquisition deliberately accepts positive
permanent numbers only. Exact comet selections may instead be acquired or
reused automatically through `--comet`, `--comet-track`, or an explicitly
classed `--center-on comet:SELECTION`; partial names and wildcards are never
guessed. A mixed asteroid/comet request uses one verified resource collection.
The standalone
`tools/acquire_numbered_asteroids.py` command remains available for controlled
offline preparation.

### Moving-object authorities and Wenu data services

The Minor Planet Center (MPC) is the International Astronomical Union's
clearinghouse for minor-planet and comet observations and designations. A
permanent periodic-comet designation such as `10P/Tempel 2` uses the MPC's
permanent number: `10P` is not the tenth periodic comet discovered in a given
year. NASA's Planetary Data System (PDS), including its Small Bodies Node,
archives and distributes planetary and small-body datasets and cross-reference
catalogues.

Wenu does not query MPC or PDS directly while listing or charting. Its moving-
object services are NASA/JPL endpoints:

- `wenu_retrieve_comets` lists comets through the SBDB Query API.
- Exact `--comet` identity resolution uses the SBDB API.
- Automatic minor-body acquisition uses the Horizons API to obtain a bounded
  SPK, then stores and verifies it as an immutable local resource.

MPC remains the upstream designation authority, while PDS is an archival and
reference system. Once Wenu's preflight has resolved or acquired the required
resource collection, chart construction and rendering are offline.

Expected command failures are printed as one concise `wenu_chart: error:`
message. Add `--debug` to the chart command to re-raise the failure with its
complete Python traceback when diagnosing provider or resource problems.

Select the symbolic hollow diamond with `--asteroid 79989`, the trajectory
with `--asteroid-track 79989`, or both. If a manifest declares an official
name, that exact name is also accepted case-insensitively. The permanent number
remains the identity if the object is named later. The shared track timing
options have the same meaning as for a planet:

```bash
wenu_chart regional \
  --observer-location "La Ligua" \
  --observer-time 2026-01-15T00:00:00Z \
  --center-on constellation:Psc \
  --asteroid 79989 \
  --asteroid-track 79989 \
  --track-start 2026-01-15T00:00:00Z \
  --track-sample-step 1d \
  --track-tick-step 7d \
  --track-tick-count 4 \
  --track-tick-labels \
  --style atlas --mode presentation --format svg \
  --output output/79989-track.svg
```

### Ceres point and dated track compatibility

The accepted 50A.2 resource set remains compatible, so existing
`--asteroid ceres` commands continue to work with
`~/.cache/wenu/minor_bodies/50a2`.

The point uses the chart observation time. Track samples use their stated
epochs and are transformed into the chart's fixed product frame. The diamond
has no magnitude or angular-size meaning. Requests outside the acquired SPK
coverage, or with a missing/mismatched manifest, target, hash, solution, or
segment, fail before output is written.

The resource directory may instead be stored in a profile; an explicit CLI
value takes precedence:

```toml
[observer]
minor_body_resource_directory = "~/.cache/wenu/minor_bodies/numbered-asteroids"
```

## Resolved Moon and observed sequences

Bare `--moon` draws the Moon's physical illuminated disk. Use
`--moon-appearance symbolic` for the compatibility point, or apply bounded
display scaling with `--moon-disk-magnification FACTOR`.

An observed multi-epoch Moon sequence uses one complete group:

```bash
wenu_chart regional \
  --center-on constellation:Sgr,Sco,Oph \
  --observer-location "La Ligua" \
  --observer-time 2026-09-16T12:00:00Z \
  --moon-disk-sequence \
  --disk-sequence-model observed \
  --disk-sequence-start 2026-09-12T00:00:00Z \
  --disk-sequence-step 1d \
  --disk-sequence-n-steps 7 \
  --disk-sequence-labels \
  --moon-disk-magnification 8 \
  --output output/moon-sequence.png
```

The start is included, so seven intervals draw eight independently realized
Moons. The ordinary observer time fixes the chart background, horizon,
projection, and tangent plane. Every sequence epoch supplies a new topocentric
Moon position, distance, size, phase, and orientation, all projected into that
one fixed chart frame. Magnification is graphical only; it changes no physical
Moon value. Frozen-Earth lunar sequences are not supported.


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

Version 2 accepts `.png`, `.pdf`, and `.svg` output extensions. SVG always
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

## Stellar selectors and reports

Albireo has an explicit curated name association with HIP 95947 (β¹ Cyg).
To label Albireo and its β² companion independently, use:

```text
--star-label-name Cyg:Albireo --star-label-bayer Cyg:beta2
```

`Cyg:beta2` resolves to HIP 95951. The IAU name Albireo refers to component
Aa of β¹ Cyg; Wenu attaches the requested label to the HIP 95947 catalogue
entry and does not resolve its subcomponents. Exact curated names supplement
the Wikidata name selectors without changing the frozen Wikidata snapshot.

See [explicit star labels and discrepancy reports](styles_modes_detail.md#explicit-star-labels-and-discrepancy-reports)
for CLI/TOML examples and precedence. `[detail.star_labels]` owns selector
lists; `[reports].stellar_designations` enables optional static-chart notes.
`[styles.atlas.stars.labels]` and `[styles.cartoon.stars.labels]` own appearance.

Celestial-reference repetition uses the positive numeric setting
`grids_references.references.label_repeat_length_factor`, default `5.0`.
Automatic non-polar labels search near visible curve ends; repeat at both
ends when the contiguous visible arc exceeds this many rendered text widths.
Explicit anchors and polar reference furniture preserve their established policy.

## Named Chilean observers

`--observer-location` and `[observer].location` accept a unique short name or
`Country:Region:Province:Comune:City`, including unique contiguous suffixes. See
[Named Chilean locations](locations.md) and the versioned CSV catalogue for
municipal and observatory references, aliases, height conventions and
regional timezone defaults. Explicit height and timezone overrides still win.
