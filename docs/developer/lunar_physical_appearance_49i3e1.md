# Lunar physical-appearance state — Milestone 49I.3E.1

**Status:** Scientifically accepted and regression-verified; ready for integration

**Implementation date:** 2026-09-02

**Implementation baseline:** `86bbbf1`

## Purpose

49I.3E.1 installs the output-neutral physical identity and appearance
capability accepted in `resolved_moon_audit_49i3e0.md`. It adds no resolved
disk geometry, chart layer, public option, magnification, style, renderer,
exporter, or visible-output change.

## Catalog identity and capability

`MOON_BODY` is one immutable `SolarSystemBodyDescriptor` and remains the
descriptor used by the accepted symbolic `MoonLayer`. It records:

- NAIF physical body ID `301`;
- body class and classification `natural_satellite`;
- parent key `earth`;
- English `Moon` and Spanish `Luna` display names;
- JPL equal-volume mean radius `1737.4 km`;
- symbolic-point and output-neutral `spherical_physical_appearance`
  capabilities.

`EARTH_BODY` supplies the non-drawable parent identity with NAIF body ID
`399`. It has no drawable capability and cannot enter `--planet` selection.
The catalog relationship query therefore returns the Moon as Earth's child
without making Earth a chart target.

The Moon deliberately does not yet advertise `resolved_spherical_disk` or
`observed_disk_sequence`. Those drawable capabilities remain 49I.3E.2 and
49I.3E.3. The `--planet` adapter also continues to select only symbolic
catalog entries classified as planets, so catalog registration does not add a
second public Moon spelling.

Venus now explicitly advertises the same output-neutral spherical-appearance
capability that its accepted runtime state already implements. This metadata
change does not alter Venus output.

## Generic physical state

No lunar appearance class was added. `SolarSystemAppearanceRealizer` consumes
the existing accepted Moon and Sun apparent directions plus catalog radius
metadata and returns the same immutable `SolarSystemApparentDisk` used for
Venus. The state retains:

- observer-origin apparent ICRS lunar centre;
- topocentric retarded observer–Moon distance through the accepted
  astrometric evidence;
- physical radius and radius authority;
- physical angular diameter;
- Sun–Moon–observer phase angle;
- spherical illuminated fraction;
- bright-limb position angle from apparent celestial north toward east;
- source and calculation provenance.

It has no display magnification, page coordinate, chart family, output mode,
style, geometry, or renderer field.

## Deterministic contracts

`tests/test_moon_appearance_state.py` proves immutable catalog identity,
Earth–Moon relationship, radius/model ownership, capability boundaries, and
generic appearance realization. Existing `MoonLayer`, semantic identity,
default-off selection, symbolic style, and maximal-sphere contracts remain
unchanged.

## Installed-DE440 validation

`tools/validate_49i3e1_lunar_appearance.py` refuses to download a missing
kernel. It uses the installed DE440-family resource and direct Skyfield
topocentric observations over a year-long candidate interval. It
deterministically selects cases nearest new, crescent, quarter, gibbous, and
full phase; sampled distance minima/maxima; and four bright-limb orientation
quadrants. Duplicate cases are removed.

For every selected epoch it compares Wenu and an independent direct-Skyfield
calculation of apparent ICRS centre, topocentric distance, exact angular
diameter, phase angle, illuminated fraction, and wrapped bright-limb angle. It
also reports nonzero geocentric/topocentric parallax, resource coverage,
actual provider IDs, observer height, and the frozen radius authority.

The accepted validation tolerances are:

| Quantity | Maximum absolute residual |
| --- | ---: |
| apparent ICRS right ascension | `2e-7 deg` |
| apparent ICRS declination | `2e-7 deg` |
| topocentric distance | `5e-12 au` |
| physical angular diameter | `5e-6 arcsec` |
| phase angle | `2e-7 deg` |
| illuminated fraction | `1e-9` |
| wrapped bright-limb angle | `5e-6 deg` |

Fernando accepted this revised envelope on 2026-09-02 after the first
eight-epoch run isolated small finite differences between Wenu's explicit
generic realization and Skyfield's integrated `observe()` path. The limits
were given independent margins rather than fitted to the observed maxima.
The rerun completed cleanly, and Fernando scientifically accepted the
49I.3E.1 numerical validation on 2026-09-02. The accepted evidence is:

- model `DE440`, file `de440s.bsp`, SHA-256
  `c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`;
- eight deterministic cases spanning phase, sampled distance extrema,
  bright-limb quadrants, and angle wrap;
- maximum residuals `1.338e-07 deg` in apparent right ascension,
  `2.885e-08 deg` in apparent declination, `4.427e-12 au` in topocentric
  distance, `2.994e-06 arcsec` in angular diameter, `9.726e-08 deg` in
  phase angle, `2.606e-10` in illuminated fraction, and `2.268e-06 deg`
  in wrapped bright-limb position angle;
- minimum reported topocentric parallax `0.272607 deg`, with the selected
  cases reaching `1.023322 deg`.

All residuals satisfy the accepted envelope. This accepts only the
output-neutral physical state; 49I.3E.2 remains a separate drawable milestone.

Final regression evidence on Fernando's Mac is 73 documentation tests in
`2.75 s`, 124 focused tests in `8.36 s`, 2,051 routine tests with 30 deselected
in `31.09 s`, and all 2,081 tests in `91.18 s`.

Run from the repository root:

```bash
python tools/validate_49i3e1_lunar_appearance.py
```

The numerical results, scientific acceptance, and regression evidence above
close 49I.3E.1 for integration. They do not authorize 49I.3E.2.

## Coordinate-guide review

The coordinate guide was updated because the Moon now has catalog-owned
physical identity and an implemented output-neutral apparent state. No
coordinate transformation changed: observation instant remains distinct from
reference epoch and equinox, and the apparent-ICRS position angle remains a
tangent-plane quantity rather than a page rotation.

## Non-goals

49I.3E.1 does not add disk geometry, a resolved Moon layer, default-resolved
selection, symbolic compatibility controls, Moon magnification, sequence
requests, fixed-chart transport, chart-family enablement, clipping, semantic
disk descendants, visual output, surface texture, libration, eclipses,
occultations, animation, or frozen-Earth lunar behavior.
