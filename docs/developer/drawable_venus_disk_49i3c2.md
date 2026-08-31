# Drawable resolved Venus disk — Milestone 49I.3C.2

**Status:** Scientifically, architecturally, and visually accepted  
**Implementation baseline:** `da0e332`  
**Review date:** 2026-08-31

## Purpose

This milestone makes the accepted physical Venus disk geometry drawable in
regional and binocular charts. The symbolic Venus point remains the default.
Resolved appearance is explicit and object-specific.

The implementation keeps the illuminated face, limb, and terminator as
separate components. Their physical geometry is sampled before projection.
Display magnification is applied after projection about the separately
projected physical centre.

## Visual angular-scale calibration reference

The accepted Virgo review image is a reusable calibrator for relating physical
planet size, display magnification, and chart angular span.

### Scientific state

- observer: La Ligua;
- reception instant: `2026-08-30T00:00:00Z`;
- physical apparent Venus diameter:
  `29.287846514361 arcsec`;
- illuminated fraction: `0.400755659841`;
- display magnification: `200`.

The nominal displayed angular diameter is therefore

[
D_{display}
  = M D_{physical}
  = 200 	imes 29.287846514361\,arcsec
  = 5857.5693028722\,arcsec
  = 1.62710258413117\,deg.
]

This is the angular size represented in the chart projection near the Venus
centre; it is not a claim that Venus physically subtends 1.627 degrees.

For reuse,

[
M = \frac{3600 D_{display,deg}}{D_{physical,arcsec}}.
]

At this epoch:

| Desired displayed diameter | Magnification |
| ---: | ---: |
| 0.5 deg | 61.459 |
| 1.0 deg | 122.918 |
| 1.5 deg | 184.377 |
| 2.0 deg | 245.836 |

### Chart and raster calibration

- chart family: regional;
- subject: Virgo;
- field width: `55 deg`;
- field height: `45 deg`;
- orientation: zenith up;
- observer horizon: visible;
- product: atlas/presentation;
- raster resolution: `600 dpi`;
- resolved-disk color: one opaque cream;
- dark hemisphere: chart sky color;
- limb: thin short dashes;
- terminator: thin solid curve.

Fernando accepted the magnification-200 rendering as the normative visual
and angular-scale calibrator: the phase is immediately legible while the disk remains small
relative to Virgo and the surrounding chart structure.

### Reproduction command

Use an overlay containing:

```toml
schema_version = 1

[modes.presentation]
dpi = 600
```

Then run:

```bash
wenu_chart regional \
  --config 600dpi.toml \
  --constellations Vir \
  --observer-location "La Ligua" \
  --observer-time "2026-08-30T00:00:00Z" \
  --field-width 55 \
  --field-height 45 \
  --orientation zenith-up \
  --style atlas \
  --mode presentation \
  --language en \
  --magnitude-limit 6.0 \
  --constellation-lines \
  --constellation-labels \
  --horizon \
  --planet-appearance venus=resolved \
  --planet-disk-magnification venus=200 \
  --output venus-virgo-calibrator.png
```

## Accepted public contract

- `--planet-appearance venus=resolved` explicitly selects resolved display.
- `--planet-disk-magnification venus=FACTOR` supplies the object-specific
  post-projection magnification.
- Factor `1` means physical angular scale.
- Magnification alone cannot enable a resolved disk.
- Symbolic and resolved Venus cannot be requested simultaneously.
- Resolved disks are restricted to regional and binocular products.
- Planisphere and all-sky products retain symbolic representation.


## Verification recorded before suite closure

- 39 focused disk-display and physical-appearance tests passed in 2.50 seconds.
- 177 chart-pipeline regression tests passed in 7.18 seconds.
- 89 display and style tests passed after the cream-palette change.
- 171 closure-focused request, execution, style, semantic, and dependency tests
  passed in 5.75 seconds.
- The 600-dpi Virgo rendering was visually accepted with magnification 200.

Multi-epoch resolved disks remain deferred to milestone 49I.3C.3.
