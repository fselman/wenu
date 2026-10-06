# Styles, modes, detail, and furniture

Wenu keeps chart concerns independent:

- chart type owns projection, framing, viewport, and final boundary;
- style owns appearance;
- mode adapts appearance to print or presentation;
- detail owns astronomical selection and density;
- furniture owns references, poles, legends, context, and credits.

## Styles and modes

Choose `--style atlas` for the detailed reference appearance or
`--style cartoon` for a simplified explanatory appearance. Choose
`--mode print` for paper or `--mode presentation` for slides and screens.
Neither choice changes chart geometry.

Cartoon presentation uses deep blue, yellow astronomical structure and
context, and white footer text. Cartoon print uses white paper and black
structure and context.

## Detail and content

These options are shared by all six examples:

```text
--magnitude-limit VALUE
--constellation-lines IAU[,IAU...]
--constellation-labels IAU[,IAU...]
--constellation-boundaries IAU[,IAU...]
--horizon
--horizon-mask
--equatorial-grid
--equatorial-grid-labels
--declination-step DEGREES
--ecliptic-grid
--ecliptic-grid-labels
--galactic-grid
--galactic-grid-labels
--grid-references SELECTION
--poles
--pole-labels
```

`--declination-step` changes only equatorial declination-parallel spacing; it
does not increase the number of right-ascension meridians. When omitted, each
chart family retains its established grid-density policy.

Omitting these switches leaves constellation structure and references off.
The all-sky family supplies its labeled Galactic grid by default; the other
families supply a labeled equatorial grid by default. `--grid-references`
accepts a comma-separated selection of `equatorial`,
`ecliptic`, and `galactic`, or `all`. Poles select visible
celestial, ecliptic, and Galactic crosses; `--pole-labels` adds their standard
abbreviations.

Named atlas products automatically use the packaged density policy for their
chart family: large fields receive shallower catalogue limits, larger minimum
object sizes, and suppression of crowded specialized layers. Named cartoon
products use a restrained explanatory subset containing the Milky Way,
Magellanic Clouds, galaxies through magnitude 8, open clusters at least 60
arcmin across, and globular clusters at least 30 arcmin across. Planetary
nebulae and supernova remnants are omitted from that cartoon baseline. These
values may be replaced in a user TOML overlay; explicit Python detail policies
and command-line magnitude/layer overrides retain precedence.

`--horizon` draws the observer's unlabeled altitude-zero reference without
changing chart selection. `--horizon-mask` independently shades the sky below
that reference with the resolved translucent mask appearance. Using both
switches draws the line and shades the below-horizon side. If a constellation
mask is also selected, Wenu intersects the openings and paints one translucent
mask, so their overlap is not darker.

The packaged cartoon style uses a translucent warm-white outside mask. It
clearly separates the selected region while leaving the surrounding sky
visible; atlas retains its own independent mask appearance.
Both packaged defaults and `[styles.cartoon.mask]` user overlays retain their
configured color and opacity in cartoon print and presentation modes.

The planisphere already uses the observer's horizon as its intrinsic chart
boundary. Both horizon switches are therefore intentional no-ops for that
family. On a Galactic Mollweide all-sky chart the same observer-bound horizon
is transformed and seam-split through the ordinary coordinate-frame and
projection pipeline.

Equatorial grid lines and numeric labels default to subtle blue-grey, ecliptic
ones to orange, and Galactic ones to blue. Presentation and cartoon modes may adapt
them for contrast while keeping the systems visually distinct. Grid labels
contain only their numeric coordinate values; semantic names belong to the
separately selected reference curves.
Equatorial labels use `hh:mm` for right ascension and signed `dd:mm` for
declination. Regional charts use denser 15-degree sampling through 60-degree
fields; circumpolar meridians are separated by two hours. Binocular grids
remain opt-in.

## Appearance overrides

Explicit overrides apply after mode defaults and therefore take precedence:

```text
--constellation-line-width VALUE
--constellation-line-color COLOR
--constellation-label-color COLOR
--constellation-boundary-width VALUE
--constellation-boundary-color COLOR
```

Colors use any value accepted by Matplotlib, such as `black`, `#ffcc33`, or
`0.4`. These are appearance choices only.

Constellation abbreviations have an independent font size in schema-v2
profiles. For atlas labels at half the packaged size:

```toml
schema_version = 2

[styles.atlas.constellation_labels]
font_size = 4.25
```

The main chart title has an independent color in the style's canvas table:

```toml
schema_version = 2
[styles.atlas.canvas]
title_color = "#0262AD"
```

This makes the title match the default atlas presentation sky blue without
changing other foreground elements. Use `[styles.cartoon.canvas]` for cartoon.
The override is retained in both print and presentation modes. The default
`title_color = "none"` (also `"inherit_canvas"`) inherits the effective
foreground color, preserving existing titles. This is the main chart title,
separate from legend titles. Combine this table with other tables in your
existing TOML overlay and pass it with `--config`.

Load the profile with `--config PATH`. This leaves the canvas, coordinate-grid,
object, and legend font sizes unchanged. Both print and presentation modes
apply their usual font scale to the constellation size. Use
`--no-equatorial-grid --altaz-grid-labels` for a labeled AltAz grid without
the default equatorial grid.

## Legends and counts

```text
--legends
--object-legend
--magnitude-legend
--star-counts
```

`--legends` enables both canonical legends. The individual switches enable
only one. `--star-counts` appends cumulative counts to magnitude entries when
the magnitude legend is enabled. Each count describes rendered stars with
magnitude less than or equal to the entry after detail selection, projection,
and chart-footprint clipping.

## Credits and contextual lines

`--credits` requests the copyright footer at lower left and the installed Wenu
version at lower right. The canonical examples also accept chart-family
context switches such as `--no-center`, `--no-grid`, `--location`, `--date`,
and `--local-time`.

Use `python examples/<name>.py --help` for the exact family-specific choices.

## Explicit star labels and discrepancy reports

Only requested stars receive labels. Selected stars bypass the magnitude limit
but still obey the chart boundary. Exact names are English Wikidata labels or
aliases; unavailable or ambiguous requests fail rather than guessing.

```bash
wenu_chart regional \
  --center-icrs-ra 2.096916deg --center-icrs-dec 29.090431deg \
  --field-width 25 --field-height 20 \
  --observer-time 2026-10-16T01:00:00Z \
  --star-label-bayer Peg:delta --show-full-bayer-designation \
  --stellar-report --output alpheratz.png
```

Alpheratz displays `δ Peg` in Pegasus context and `α And` in Andromeda context;
both contexts use the modern `α And` fallback. A repeated
`--star-label-name 'Sco:Antares,Shaula'` requests exact names; names take priority
over Bayer labels for the same HIP. Greek spellings/glyphs and suffixes such as
`iota1` normalize; Latin-letter case remains significant.

Equivalent optional configuration:

```toml
schema_version = 2

[detail.star_labels]
names = []
bayer = ["Peg:delta"]
show_full_bayer_designation = true

[reports]
stellar_designations = true
```

CLI lists replace their corresponding TOML lists. `--no-stellar-report`
disables a configured report. Reports are `alpheratz.png.stars.md` and
`alpheratz.png.stars.json`; they contain only retained stars from the 77-case
research list, preserving historical and identity cautions and source links.
Reports work without labels and do not claim general object-interest or
visibility predictions. Both labels and reports default off. Sequence reports
and global automatic labels remain later.
