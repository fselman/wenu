# Label placement and chart typography

This guide records Wenu's agreed label policies, implemented controls, and
remaining publication work. The chart family determines the default
orientation; projection name and inclusion of a celestial pole alone do not.

## Implemented object-label orientation

| Chart | Default object and constellation labels |
|---|---|
| Polar planisphere, north or south | Tangential around its pole; typographic up points away from the pole |
| Location-centred stereographic planisphere | Upright on the page |
| Regional or constellation chart, including one containing a pole | Upright on the page |
| Binocular or Galactic all-sky chart | Upright on the page |

Polar orientation deliberately permits upside-down text on a fixed page.
It supports turning a polar disk to read the corresponding sector. Never
flip these labels merely to make them readable from the bottom of the page.
The north and south faces use the same typographic rule in projected space.

The mutually exclusive CLI overrides are:

```text
--labels-upright
--labels-up-away-from-cp
```

The latter requires a polar-planisphere chart with its unambiguous pole at
the projected origin. It is rejected for other families, even if a celestial
pole is visible. The ordinary `wenu_chart planisphere` is location-centred;
use `--labels-upright` there, or leave the default unchanged. These shared
controls are also available to the Python example argument parsers; they do
not add a new CLI chart family.

TOML equivalents, with the CLI taking precedence:

```toml
schema_version = 2

[styles.atlas.canvas]
labels_orientation = "upright"
```

Values are `chart` (default), `upright`, and `up-away-from-cp`. The same key is
available under `[styles.cartoon.canvas]`. Python callers can use
`ChartStyleOverrides(labels_orientation="upright")`.

The controls cover stellar, constellation, deep-sky, and ordinary moving-body
point labels. They preserve font size, colour, offsets, and curated polar
symbol/label adjustments. They exclude coordinate-grid labels, chart titles,
legends, reference-plane labels, and temporal track/sequence annotations.
Planet and small-body track dates retain their established anchors and
orientation and act as fixed obstacles during automatic stellar placement.

## Collision avoidance: current implementation and next work

`--star-label-placement auto` enables a shared final-display-space search
for stellar labels, constellation names and automatically anchored celestial
reference names. The same TOML stellar-label placement setting enables it.
The process preserves font size, colour, identity and the agreed orientation.
Stellar and temporal labels retain their identities and scientific positions.
Constellation names are omitted when no valid contained placement exists.

The process is:

1. Measure actual text bounds at nearby stellar candidates, constellation
   candidates, and sampled positions on each reference curve.
2. Require the entire constellation text box to fit within its own prepared
   visible IAU region and the sky boundary. Omit the name if no candidate fits;
   never move it into another constellation. Fixed constellation names are
   validated at their original anchor without movement. Other label families
   retain best-effort containment when no fitting candidate exists.
3. Reserve 1.5 points between movable text bounds (0.75 point against fixed
   text). Prefer separating text, then clearing star symbols, retaining stellar
   association, and minimizing displacement or crossings of other lines.
4. Revisit assignments with coordinate descent and bounded simultaneous
   pair moves, allowing both conflicting labels to yield together.
5. Preserve unresolved overlaps for inspection through the renderer's
   `unresolved_label_collisions` tuple of text pairs.

This is not a guarantee of collision-free output. Candidate counts and
search rounds are finite, and rotated bounding rectangles conservatively
estimate occupied space. No simulated annealing is implemented here.
Sub-resolution companions may share a visible marker; separated names still
retain their individual catalogue identities.

The celestial equator, ecliptic and Galactic equator move only along the
same contiguous projected curve segment, recomputing the local tangent and
retaining the normal offset. On non-polar charts the search is restricted to
windows near the visible curve ends. A curve longer than five rendered text
widths gets a label near each end; shorter curves get one. Each copy stays
within its own end window, and labels with no fully contained candidate are
omitted. Explicitly supplied reference anchors remain
fixed. Coordinate-grid labels keep their agreed anchors and act as obstacles.
Planet and small-body track dates retain their established anchors and
orientation and remain fixed obstacles. Titles, legends and sequence
annotations also stay fixed. Fixed stellar placement keeps constellation anchors fixed but still validates
contained text boxes. Automatic reference-end search also runs with fixed
stellar placement; explicitly supplied reference anchors stay fixed.

Further work includes grid-specific alternatives that respect their assigned
spokes or margins, stronger search, curved glyph placement and CLI diagnostic
integration. `unresolved_label_collisions` is currently a Python renderer
inspection value, not a command-line report. `suppressed_region_labels` lists
omitted constellation names in the renderer.

## Implemented horizon-grid placement

For a location-centred planisphere, `--altaz-grid-labels` places azimuth
labels upright outside the horizon. The exterior band uses
measured text bounds rather than a fixed fraction of chart radius. With the
band enabled, marginal labels sit close to the boundary crossing;
without it they retain a 0.65 em gap. Export includes these unclipped marginal
labels. Altitude labels
remain upright inside the horizon along azimuths 0°, 90°, 180°, 270°.
Noncentral altitude labels use a 0.2 em normal offset; the zenith retains
0.65 em. A requested altitude 90° label appears only once at the zenith. These anchors
follow projection rotation, east/west reflection, and off-zenith centres.

Python callers can set `FullSkyChart(altitude_label_azimuths_deg=(45, 225))`.
CLI/TOML spoke selection and independent azimuth-label cadence remain proposed.
Grid-line density is unchanged. Track dates and reference-plane labels retain
their existing anchors.

## Exterior grid-label band and frame

Non-polar planispheres, regional/constellation charts and binocular charts
have an opaque white exterior band with a black 0.8-point exterior frame by
default. The sky boundary remains separate. Polar planispheres and Galactic
all-sky charts retain their existing furniture.

Packaged coordinate labels are another 20% larger: atlas 5.04 points
(previously 4.2), cartoon 5.76 points (previously 4.8). Atlas coordinate-label opacity is 1.0.
Ordinary cardinal labels fit in the existing band near their crossings.
Dense diagonal labels may require additional measured width. The minimum reserved width is 8.5 points plus twice the configured
2-point padding and half-frame allowance. Custom oversized text can still
expand the measured surround; requested text is never shrunk or clipped to
force it into a thin band. Circular charts use an annulus;
regional charts use a rectangular surround. The band is a compound path with
a genuine interior hole: it never fills the sky or alters viewport limits.
The exterior furniture remains visible when the page background is transparent.
Exterior grid lettering defaults independently to black, including presentation
mode; `label_color` configures it without changing interior or stellar text.
Titles are cleared above the frame. Repeated finalization replaces furniture
rather than accumulating patches. Semantic SVG identifies the band and frame
separately for style editing.

Regional and binocular coordinate labels use actual curve-boundary crossings
near their existing selected anchors, with upright measured exterior offsets.
Bottom marginal text on rectangular charts keeps 1.5 points between its ink
bounds and the inner viewport edge; other margins retain their closer placement.
Curves that do not cross the boundary have no marginal label. This does not
implement new cadence, duplicate top/right labels, or pole-aware RA/Dec rules.
Horizon-planisphere altitude labels remain on their interior cardinal spokes.

```text
--no-grid-label-band
--grid-label-band-fill-color none
--grid-label-band-frame-color black
--grid-label-band-line-width 0.8
```

`none` selects transparent fill (or no frame colour); zero width suppresses
the stroke. CLI values override TOML, which uses this table for either style:

```toml
schema_version = 2
[styles.atlas.canvas.grid_label_band]
enabled = true
fill_color = "white"
frame_color = "black"
label_color = "black"
line_width = 0.8
padding_points = 2.0
```

Python uses the corresponding `CanvasStyle.grid_label_band*` fields or
`ChartStyleOverrides` (enabled, fill/frame colours and line width). Turning
the band off restores the existing regional/binocular grid anchors. Fill and
frame overrides do not change stars, tracks, scientific positions or density.

## Constellation line clearance

A location-centred planisphere defaults to a 1-point gap beyond each drawn
stellar marker. Other families retain zero extra gap. Short connections thus
retain more visible line than with a 2-point gap. CLI and TOML values override
the family default; explicit zero disables extra endpoint clearance:

```text
--constellation-line-gap 1
```

```toml
[styles.atlas.constellation_figures]
gap_points = 1.0
```

The packaged value `gap_points = "none"` means inherit the chart-family
choice. Remove an old explicit `--constellation-line-gap 2` to use the new
default. Linework remains clipped at the inner sky boundary after final
physical endpoint trimming. The opaque band covers low-order linework at
that edge; a transparent band continues to rely on the real clip path.

## Remaining grid policies: proposed, not implemented by this milestone

| Chart | Coordinate-label policy |
|---|---|
| Pole-centred equatorial planisphere | RA in an exterior annulus, every 2h by default; declination inside along RA 0h, 6h, 12h, 18h, configurable |
| Nonpolar rectangular regional/constellation chart | Prefer RA outside top/bottom, declination outside left/right; anchor to actual curve–edge crossings |
| Regional/constellation chart containing a pole | Retain the chart's viewport; RA may use its whole perimeter, declination uses interior meridians |

Azimuth uses 0° north, increasing through east. Put one altitude 90° label at
the zenith, where all azimuth spokes meet. RA is undefined at a celestial
pole: use one pole annotation rather than converging RA labels there.

A location-centred horizon chart does not have a uniform RA clock scale:
equatorial labels belong at actual meridian–horizon crossings. If both RA
and azimuth marginal scales are requested, use distinct bands and explicit
units. Avoid duplicate 0h/24h labels at the same crossing.

Reserve margins using measured text bounds, rotation, a consistent small
gap from the border, and padding. Opaque white with a black exterior frame is the default band appearance;
transparent or another configurable fill remains available. Keep corners clear.

Automatic intervals should consider angular span, projection distortion,
physical output size, and text width. RA 1h/2h and declination 10°/20° are
useful broad-field defaults, not the only intervals permitted for small
fields. Explicit settings take precedence. Label cadence and grid-line
density must remain independent.

Wenu already has `ChartContext` and `AdaptiveDetailPolicy` in the existing
chart detail owner. Assess and extend that responsibility before proposing a
new scale module. Automatic limiting magnitude and grid density may share
scale evidence, but changing one control must not silently change the other.

## Style, readability, and visual acceptance

The guiding aims are legibility, unambiguous association, and an orderly
visual hierarchy. External coordinate labels protect sky detail and establish
a clear border. Use restrained typography and consistent spacing; coordinate
furniture should not compete with named stars. Colour can reinforce a
label's association with its curve, but units and placement must carry that
meaning too. Small halos or masks are optional readability aids, not a cure
for ambiguous placement.

Horizontal point labels are the general cartographic convention. Our polar
disk convention is an explicit product-specific exception. Curve-following
reference names follow the general line-feature convention. These are design
choices supported by practice, not proof that one layout is universally best
for every reader.

Review at intended physical print size as well as on screen. Shrinking labels
to 75% keeps their colour, but small type may become difficult under observing
conditions. Automatic avoidance must not compensate by shrinking requested
type further. Inspect close double stars, crowded constellation names, curve
crossings, horizon edges, pole regions, both polar faces, and mirrored charts.
Compare track dates against their prior layout. A low overlap score alone is
insufficient visual acceptance.

## Literature and precedents

Sources consulted 2026-10-07. Policy decisions above are Wenu decisions;
these sources provide principles and examples rather than prescribing our
exact angular intervals.

- Eduard Imhof (1975), [Positioning Names on Maps](https://doi.org/10.1559/152304075784313304), *The American Cartographer*, 2(2), 128–144. Publisher abstract consulted: name placement and legibility; full text was not available in this review.
- Ordnance Survey, [Text on maps](https://docs.os.uk/more-than-maps/geographic-data-visualisation/guide-to-cartography/text-on-maps): horizontal readability, feature association, placement preferences, gentle curve alignment, and restrained masking.
- UCGIS GIS&T Body of Knowledge, [Typography](https://gistbok-ltb.ucgis.org/current/concept/CV-03-010): hierarchy, density, output-dependent legibility, proximity, and limits on curved text.
- Esri, [Graticules](https://doc.esri.com/en/arcgis-pro/latest/help/layouts/add-and-modify-graticules.html): independent lines/ticks/labels, scale-dependent intervals, edge selection, and offsets.
- Olivier Hainaut, ESO, [Astrolabe Generator](https://www.eso.org/~ohainaut/astrolabe/manual.html): astronomical precedent for RA on the rim, declination on an interior meridian, and azimuth along the horizon.
- Jon Christensen, Joe Marks, and Stuart Shieber (1995), [An empirical study of algorithms for point feature label placement](https://www.eecs.harvard.edu/~shieber/Biblio/Papers/label-algs-tog.pdf), *ACM Transactions on Graphics*, 14(3), 203–232: search algorithms, including simulated annealing. Annealing is a candidate search technique; admissible positions and design criteria still define acceptable typography.

The authored Scorpius figure connects σ Sco to β¹ Sco (HIP 80112–78820),
replacing σ Sco–δ Sco; all other figure connections remain unchanged.

Scorpius connections are stored as independent edge records because the
legacy reader connects consecutive identifiers. This prevents an unintended
π Sco–β¹ Sco bridge when replacing σ Sco–δ Sco with σ Sco–β¹ Sco.

## Reference repetition and uniform declination intervals

The repetition factor is configurable in a schema-version-2 overlay:

```toml
[grids_references.references]
label_repeat_length_factor = 5.0
```

The factor compares visible contiguous arc length with rendered text width,
not angular span or character count. Changing font size or output scale is
therefore accounted for. Automatic endpoint search does not join disconnected
curve fragments. Explicit anchors and polar-planisphere reference placement
retain their previous behavior. Date annotations on tracks are unchanged.
For a partially visible closed curve, visible samples across the 360°–0°
array seam are joined before identifying its endpoints. The sampling origin
is not a visible endpoint; changing it must not move the endpoint windows.
Complete closed loops have no endpoints and retain one automatic label.

Request `--declination-step 15` for the 70-degree Sco/Sgr/Oph regional chart.
Equatorial grids include the celestial equator and use symmetric declination
multiples from zero, so all adjacent parallels have the requested interval.
A separately requested equator name remains reference furniture.
