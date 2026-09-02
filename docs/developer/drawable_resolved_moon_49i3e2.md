# Drawable resolved Moon — Milestone 49I.3E.2

**Status:** Implemented for review; scientific, visual, and regression acceptance pending  
**Implementation base:** `b83459a`  
**Review date:** pending

## Purpose and boundary

This milestone connects the accepted output-neutral lunar appearance state to
Wenu's existing generic single-disk machinery. Supplying `--moon` now requests
one resolved physical Moon by default. Explicit
`--moon-appearance symbolic` preserves the earlier point representation.

This slice adds no multi-epoch Moon request, sequence model, interpolation,
animation, texture, libration, eclipse, refraction, occultation, or lunar
surface-feature behavior. Those remain separately governed work.

## Scientific and architectural contract

The Moon retains physical body ID `301`, parent `earth`, and the JPL
equal-volume mean radius `1737.4 km`. The accepted generic apparent-direction
and `SolarSystemAppearanceRealizer` path produces the topocentric apparent
centre, retarded observer–Moon distance, angular diameter, phase angle,
illuminated fraction, and bright-limb position angle.

`SolarSystemDiskGeometryRealizer` then constructs the illuminated face, limb,
and terminator with the shared default of `720` samples. No Moon-specific
geometry realizer, projector, renderer, or exporter exists. The three ordinary
components keep stable semantic descendants:

- `sky/solar_system/natural_satellites/moon/disk/illuminated`
- `sky/solar_system/natural_satellites/moon/disk/limb`
- `sky/solar_system/natural_satellites/moon/disk/terminator`

The Moon descriptor owns permission to display a resolved disk in `regional`,
`binocular`, `circumpolar`, `planisphere`, and `all_sky` charts. Descriptor
policy leaves Venus restricted to its accepted regional and binocular
families; enabling the Moon does not broaden another body's capabilities.

## Public interface

```text
--moon
--moon-appearance resolved|symbolic
--moon-disk-magnification FACTOR
```

The rules are:

- omitted `--moon` means no Moon;
- bare `--moon` means resolved appearance at physical scale;
- `--moon-appearance symbolic` selects the compatibility point;
- appearance and magnification controls cannot silently enable the Moon;
- symbolic appearance and disk magnification are mutually exclusive;
- magnification is finite and satisfies `1 <= M_moon <= 1000`;
- factor `1` means physical angular scale.

Magnification is display-only and is applied after projection about the
separately projected physical centre. It changes neither the physical lunar
state nor the chart centre. It is unrelated to Wenu's `presentation` output
mode and follows the same rule in print and presentation modes.

## Rendering ownership

`SolarSystemDiskDisplayRequest` owns target resolution and the governed
magnification. Generic disk factories install the illuminated, limb, and
terminator layers. Ordinary coordinate transformation moves every physical
spherical vertex into the product frame. `MagnifyProjectedDisk` then scales
only projected offsets about the exact projected centre. Existing clipping,
polygon/curve renderers, semantic SVG support, and PNG/PDF/SVG exporters
complete the pipeline.

Moon style values are publication-style data selected by descriptor entity
key. The default resolved face, limb, and terminator use opaque `#E6E1D3`;
the dark hemisphere remains the chart sky. There is no Moon-specific renderer.

## Reproducible visual review

Run:

```bash
python tools/render_49i3e2_resolved_moon_review.py
```

The tool renders physical scale, visually legible magnification `8`, and
explicit symbolic compatibility in all five chart families at
`2026-01-19T00:00:00Z` for La Ligua. Its generated configuration restricts
content to stars through magnitude `5.0`; deep-sky objects are omitted. It also
renders magnified regional PDF and semantic SVG parity products and writes
`manifest.json` under `output/49i3e2-resolved-moon-review/`. Automated request
contracts separately exercise the maximum factor `1000` in every family.

Human review must confirm:

1. the magnified Moon is present and legible in every family;
2. phase orientation and centre placement are coherent across projections;
3. magnification changes size without moving the centre;
4. limb and terminator remain legible at seams and circular boundaries;
5. explicit symbolic output preserves the compatibility representation;
6. PNG, PDF, and SVG agree for the regional parity case.

## Acceptance gate

Before integration, Fernando must accept the visual matrix and report focused
Moon/display tests, current-documentation tests, the routine suite with
intentional deselections, and the complete suite with deselections enabled.

Until those results and the human visual decision are recorded, this document
does not claim scientific, visual, operational, or regression acceptance.
Milestone 49I.3E.3 multi-epoch Moon behavior remains unimplemented.
