# Venus physical-appearance state — Milestone 49I.3B

**Status:** Scientifically and architecturally accepted

**Acceptance date:** 2026-08-31

**Implementation baseline:** `217abbe`

## 1. Purpose

49I.3B adds the first renderer-neutral physical appearance of a spherical
Solar-System body. It computes Venus angular diameter, phase angle, illuminated
fraction, and bright-limb position angle from the accepted observer-relative
direction chain. It adds no disk geometry, chart layer, request option, style,
renderer behavior, or visible output.

## 2. As-is insertion point

The accepted `ApparentDirection` remains the authoritative observer-origin
apparent ICRS centre. Its retained `AstrometricDirection` supplies the
retarded observer-target distance and observer state. 49I.3B accompanies that
direction with a frozen `SolarSystemApparentDisk`; it does not replace or
recompute the accepted Venus direction.

`src/wenu/solar_system_appearance.py` is renderer-neutral and does not import
chart, projection, preparation, rendering, style, or export packages.

## 3. Frozen physical state

`SolarSystemApparentDisk` records:

- target and display identity;
- accepted target and Sun apparent directions;
- physical radius and radius-model identity;
- angular diameter in arcseconds;
- phase angle in degrees;
- illuminated fraction;
- bright-limb position angle in degrees;
- an explicit position-angle convention;
- ephemeris and calculation provenance.

It deliberately contains no display magnification, projection coordinates,
page units, marker size, chart family, colour, output path, or caching policy.

`SolarSystemAppearanceRealizer` computes this state from the accepted target
and Sun directions plus one reception-time Sun state. It owns no chart or
rendering policy.

## 4. Venus radius and angular diameter

The adopted spherical Venus radius is `6051.8 km`, the mean radius reported
by JPL Solar System Dynamics in its Planetary Physical Parameters table, based
there on the IAU/IAG cartographic-coordinate and rotational-element report.

The astronomical unit is `149597870.7 km`. For accepted retarded
observer-target distance (Delta), the angular diameter is

[
d = 2arcsinleft(rac{R_mathrm{Venus}}{Delta}ight).
]

The physical diameter is not multiplied by any display magnification in
49I.3B.

## 5. Phase and illuminated fraction

The phase angle (i) uses the Skyfield convention
Sun–target–observer:

- (i=0^circ): fully illuminated;
- (i=180^circ): dark side toward the observer.

The target vector is the accepted retarded observer-to-Venus astrometric
vector. The Sun barycentric state is evaluated at reception, matching
Skyfield's `phase_angle(sun)` semantics. The phase angle uses the stable
vector expression

[
i = operatorname{atan2}(|mathbf{u}	imesmathbf{v}|,
                         mathbf{u}cdotmathbf{v}).
]

For a spherical body, the illuminated fraction is

[
k = rac{1+cos i}{2}.
]

This quantity is physical illumination, not apparent magnitude and not a
linear brightness fraction.

## 6. Bright-limb position angle

The bright-limb position angle is measured in the observer-origin apparent
ICRS tangent plane:

- zero at celestial north;
- positive toward celestial east;
- normalized to ([0^circ,360^circ)).

Given apparent target coordinates ((alpha,delta)) and apparent Sun
coordinates ((alpha_odot,delta_odot)), the accepted convention is

[
chi = operatorname{atan2}left(
 cosdelta_odotsin(alpha_odot-alpha),
 sindelta_odotcosdelta
 -cosdelta_odotsindeltacos(alpha_odot-alpha)
ight).
]

The angle points from the disk centre toward the midpoint of the illuminated
limb and therefore toward the apparent Sun. The terminator is approximately
perpendicular to this direction.

(chi) is not a page rotation. 49I.3C must transform the tangent direction
through the product frame and projection before drawing a disk.

## 7. Numerical validation

`tools/validate_49i3b_venus_appearance.py` refuses to download a missing
kernel and uses installed DE440 for La Ligua at
`2026-08-30T00:00:00Z`.

The accepted result is:

| Quantity | Value |
| --- | ---: |
| observer-target distance | `0.5698057720372052 AU` |
| angular diameter | `29.287846514361 arcsec` |
| phase angle | `101.448595072558 deg` |
| illuminated fraction | `0.400755659841` |
| bright-limb PA, apparent ICRS | `295.354967208388 deg` |

Direct Skyfield comparison produced:

| Residual | Value | Acceptance tolerance |
| --- | ---: | ---: |
| angular diameter | `6.927e-11 arcsec` | `1e-8 arcsec` |
| phase angle | `1.353e-10 deg` | `1e-9 deg` |
| illuminated fraction | `-1.158e-12` | `1e-11` |
| bright-limb PA | `2.080e-11 deg` | `1e-9 deg` |

The small phase/fraction differences reflect Wenu's accepted light-time
convergence versus Skyfield's internal observation solution. The tolerances
are comparison tolerances, not claims of physical ephemeris accuracy.

## 8. Celestial versus local orientation diagnostic

At the validation instant, direct Skyfield gives:

| Object | Altitude | Azimuth |
| --- | ---: | ---: |
| Venus | `24.315259593189 deg` | `271.851611798768 deg` |
| Sun | `-20.488126019912 deg` | `267.813489194932 deg` |

The same Sun-from-Venus tangent direction is:

- `295.354967208388 deg` from celestial north toward east;
- `185.355190511946 deg` from the local zenith toward increasing azimuth.

Thus the illuminated side points almost straight down in a zenith-up local
chart, toward the Sun. The roughly 110-degree change is the rotation between
celestial north and the local zenith at Venus. This diagnostic confirms that
the ICRS position angle must not be handed directly to the renderer.

## 9. Runtime ownership

- `solar_system_appearance.py` owns validation and realization of the frozen
  physical state.
- `solar_system_directions.py` continues to own target/Sun astrometric
  directions and their observation-time evidence.
- `skyfield_ephemeris.py` continues to own the installed JPL/Skyfield state
  and apparent-place adapters.
- `tests/test_solar_system_appearance.py` owns deterministic contract,
  convention, and error coverage.
- `tools/validate_49i3b_venus_appearance.py` owns installed-kernel numerical
  evidence.

No chart or sky layer consumes `SolarSystemApparentDisk` in 49I.3B.

## 10. Scientific acceptance

Fernando accepted the radius authority, angular-diameter model,
Sun–target–observer phase convention, spherical illuminated fraction,
celestial-north-through-east bright-limb convention, local-orientation
interpretation, calibrated tolerances, numerical results, and output-neutral
runtime boundary on 2026-08-31.

Initial verification passed all 9 deterministic appearance tests in 1.38
seconds. The installed-DE440 validator passed with the values and residuals
recorded above. Final verification passed 116 focused architectural tests in
4.73 seconds, 1,936 routine tests with 30 deselected in 27.32 seconds, and all
1,966 tests in 89.97 seconds.

## 11. Non-goals

49I.3B does not add:

- spherical or projected disk geometry;
- an illuminated-region polygon;
- display magnification;
- a resolved Venus layer;
- CLI, TOML, request, detail, style, or chart-family controls;
- symbolic photometry or magnitude-scaled markers;
- a Venus glyph;
- Moon appearance or orientation;
- page-space angle calculation;
- PNG, PDF, or SVG output changes.

49I.3C remains responsible for the first opt-in resolved Venus disk and for
transforming the accepted tangent direction through the chart machinery.

## 12. Stop conditions

Stop and re-audit if later work would:

- recompute the accepted Venus centre or repeat its light-time solution;
- treat illuminated fraction as apparent magnitude;
- store display magnification in `SolarSystemApparentDisk`;
- interpret the ICRS bright-limb angle as a page rotation;
- enlarge a scatter marker and call it a physical disk;
- bypass canonical geometry, projection, clipping, rendering, or export;
- copy the Venus model to the Moon without separate validation.
