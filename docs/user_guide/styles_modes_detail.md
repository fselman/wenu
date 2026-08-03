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

These options are shared by all five examples:

```text
--magnitude-limit VALUE
--constellation-labels
--constellation-boundaries
--references
--poles
--pole-labels
```

Omitting a switch preserves the family/style default. References select the
semantic Ecliptic and Galactic-plane annotations. Poles select visible
celestial, ecliptic, and Galactic crosses; `--pole-labels` adds their standard
abbreviations.

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
