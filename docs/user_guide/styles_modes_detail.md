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
--constellation-lines
--constellation-labels
--constellation-boundaries
--equatorial-grid
--equatorial-grid-labels
--ecliptic-grid
--ecliptic-grid-labels
--galactic-grid
--galactic-grid-labels
--grid-references SELECTION
--poles
--pole-labels
```

Omitting these switches leaves constellation structure and references off.
The all-sky family supplies its labeled Galactic grid by default; the other
families supply a labeled equatorial grid by default. `--grid-references`
accepts a comma-separated selection of `equatorial`,
`ecliptic`, and `galactic`, or `all`. Poles select visible
celestial, ecliptic, and Galactic crosses; `--pole-labels` adds their standard
abbreviations.

Equatorial grid lines and numeric labels default to black, ecliptic ones to
orange, and Galactic ones to blue. Presentation and cartoon modes may adapt
them for contrast while keeping the systems visually distinct. Grid labels
contain only their numeric coordinate values; semantic names belong to the
separately selected reference curves.

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
