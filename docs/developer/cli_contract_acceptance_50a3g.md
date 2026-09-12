# CLI center/content visual acceptance (Milestone 50A.3G)

**Status:** Candidate documentation and visual-acceptance closure

**Base:** `c0c78415358322b5a35afabdffc798699fbb0ab6`

## Purpose

PR 98 installed the explicit CLI contract audited in
`chart_cli_semantics_audit_50a3f.md`. Before comet work begins, this bounded
closure checks the rendered consequences and makes the active README, user
guides, architecture, source map, implementation reference, and schema
language agree with the implementation.

This milestone changes no astronomical calculation, catalogue, projection,
selection threshold, style, renderer, or exporter.

The coordinate-system guide was reviewed for this documentation/acceptance
slice. Its scientific coordinate, frame, time, and provider explanations
remain current; no change is required there.

## Contract under review

- A center comes only from `--center-on`, one complete coordinate pair, or the
  effective `[centers.*]` configuration.
- A center is not drawn unless an independent content selector requests it.
- A content selector never changes the center, whether it selects one or many
  objects.
- Constellation lines, labels, boundaries, and masks each name their own IAU
  selection.
- `[constellations].system = "western"` supplies vocabulary and line-figure
  tradition; it does not enable a layer.
- The configured stellar/background baseline is content from the effective
  schema-v2 profile, not a side effect of center resolution.

## Reproducible visual matrix

List the products without rendering:

```bash
python tools/render_50a3g_cli_contract_matrix.py --list
```

Render all eleven products, including numbered asteroid `(79989)`:

```bash
python tools/render_50a3g_cli_contract_matrix.py \
  --minor-body-resource-directory ~/.cache/wenu/minor_bodies/numbered-asteroids \
  --output /tmp/wenu-50a3g
```

The output directory and `manifest.json` remain outside the repository.

## Human inspection checklist

1. `center-virgo-no-constellation-content` frames Virgo without drawing Virgo
   merely because it is the center.
2. `center-virgo-draw-venus` has the same framing and adds Venus only when its
   apparent point falls inside the field.
3. `center-venus-draw-mask-virgo` centers and draws Venus independently, and
   applies only the explicitly requested Virgo lines, label, and mask.
4. `center-icrs-coordinate` honors the literal ICRS center and field, and its
   default title records RA as `hh:mm:ss.s` and declination as signed
   `dd:mm:ss.s`.
5. The Sirius, Centaurus A, and Omega Centauri products center the named fixed
   targets without manufacturing an implicit target drawing request.
6. `center-asteroid-79989` centers and draws the same installed asteroid
   through two independent requests and the existing offline resource chain.
7. `center-virgo-draw-three-planets` keeps the Virgo field while ordinary
   clipping admits only planets actually inside it.
8. The two Sirius orientation products retain the same center and field;
   only celestial-north-up versus zenith-up rotation changes.

## Visual finding under review

Fernando's first atlas-presentation inspection accepted the two Virgo-centered
products. The Venus-centered masked product exposed a mode-adaptation defect:
the mask geometry reduced exterior contrast, but its configured light-gray
veil had been replaced by the blue sky color and was therefore invisible.
The candidate correction preserves the style-owned mask color and opacity
through presentation adaptation. The regenerated product must visibly retain
the semi-transparent light veil while leaving the Virgo opening clear.

Fernando's visual acceptance, the complete macOS test gate, and the exact
accepted source commit must be recorded before this milestone closes. 50A.4
comet numerical validation remains next and is not authorized by this file.
