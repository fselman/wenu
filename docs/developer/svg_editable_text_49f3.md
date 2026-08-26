# Milestone 49F.3: Editable SVG text and output format policy

## Status

Implementation and focused acceptance complete on `feature/svg-output-font-policy`. Final full-suite verification remains pending.

## User-facing contract

Wenu exposes three public chart-output formats:

- `png`: fixed raster output.
- `pdf`: portable publication and printing output.
- `svg`: editable vector output with genuine SVG text.

SVG has one coherent text contract: text is retained as SVG `<text>` elements. Wenu does not expose a separate SVG font-policy switch. Publication-oriented text-to-path behavior is not part of the ordinary public SVG interface; PDF serves the portable publication role.

The CLI accepts:

```text
--format {png,pdf,svg}
```

When an explicit format contradicts a single-file output suffix, the request is rejected. Existing commands that omit `--format` retain their previous naming behavior.

## Architectural boundary

The public output-format vocabulary is owned by Wenu rather than exposing backend-specific Matplotlib terms. The canonical final-save boundary selects SVG text retention. PNG and PDF behavior is unchanged.

## Automated verification

The focused suite passed on Fernando Selman's Mac:

```text
76 passed in 6.25s
```

Covered tests:

- `tests/test_output_policy.py`
- `tests/test_chart_product_options.py`
- `tests/test_chart_arguments.py`
- `tests/test_wenu_chart_cli.py`
- `tests/test_svg_output.py`
- `tests/test_package_boundaries.py`
- `tests/test_renderer_contracts.py`

## Real-chart acceptance

A regional chart was generated through the public CLI with:

```text
--format svg
--output /tmp/wenu-49f3-svg/regional.svg
```

The generated document contained:

```text
text elements: 32
semantic artists: 232
edit policies: {'layout': 4, 'style': 228}
```

In Inkscape, Fernando confirmed:

1. The chart looked correct.
2. A constellation label was recognized as text rather than glyph paths.
3. Its wording could be edited.
4. Its font family, size, weight, and color could be changed.
5. The label could be moved.
6. A constellation line remained individually selectable.

## Inkscape round trip

The original and the separately saved Inkscape copy both reported exactly:

```text
text elements: 32
semantic artists: 232
edit policies: {'layout': 4, 'style': 228}
```

Thus Inkscape preserved editable text, semantic identity, and editing-policy metadata through the round trip.

## Important limitation

An editable SVG normally names fonts but does not embed their font files. A computer without the requested font may substitute another font and alter text metrics. Wenu should document its supported/default font family and fallbacks; embedded SVG fonts are not part of this milestone.

## Remaining acceptance

Run the complete test suite from a clean, synchronized branch:

```bash
git pull --ff-only
git status
git diff --check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```
