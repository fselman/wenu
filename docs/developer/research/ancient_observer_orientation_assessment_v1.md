# Ancient observer orientation assessment

Version 1 · 2026-10-31 · K4b.08.R2

## Status and agreement

Fernando accepted the investigation of nominal forced nutation, preserving
the existing VCW mean axes and explicitly omitting ancient polar motion,
with “Agreed. Proceed.” on 2026-10-31. He then confirmed clean synchronized
Mac main `7935541c211588e1d4442e535e00feae64c13e84`.
This is an assessment and diagnostic scope, not production-model selection
or authorization for the entire ancient observer/chart integration.

Source inspection is complete for the owners below. Numerical comparison,
complete Mac documentation verification, synthesis and user review are pending.
No diagnostic result is claimed in this edition. No production, dependency,
SDK, default, source catalogue or resource change is introduced.

## Existing owners and constraints

| Owner at the agreed base | Finding and disposition |
|---|---|
| [Astrometric conventions](../../../src/wenu/astrometric_coordinates.py) | `LongTermFrame` uses corrected ERFA VCW2011/2012 `ltpb`/`ltecm`, finite TT coverage and separately retained backend/matrix identities. Reuse this mean-axis owner. Frame bias is already included; do not add it twice. |
| [Rotation model](../../../src/wenu/earth_rotation.py) | Accepted named Espenak--Meeus Delta-T and split UT1 receipts; the Skyfield adapter changes timing, not all celestial orientation. |
| [Reception and realization](../../../src/wenu/astrometric_observation.py) | Modern reception uses verified final EOP, `xys06a`, observed pole offsets, `s06`, `era00`, `sp00`, `epv00` and `apco`. Keep its existing conservative date/resource admission. Do not extend it by changing a constant. |
| [Ordinary observer](../../../src/wenu/observer.py) | Existing Skyfield/Astropy product routes are retained. They do not automatically consume the explicit VCW or rotation selection. |
| [Existing coordinate tests](../../../tests/test_astrometric_state.py) | Published ERFA regressions, independent pole construction and long-frame convention/refusal tests already exist. Reuse unchanged evidence; a diagnostic does not replace later composition tests. |
| [Observer-resource tests](../../../tests/test_observer_resources.py) | Accepted rotation/callable integration owner. The modern reception and complete observer composition retain distinct gates. |

Skyfield upstream source review is pinned to
[`31a6ed7584cd09b6e48e07546a4b5921e1cd5bb4`](https://github.com/skyfielders/python-skyfield/tree/31a6ed7584cd09b6e48e07546a4b5921e1cd5bb4).
Its [time owner](https://github.com/skyfielders/python-skyfield/blob/31a6ed7584cd09b6e48e07546a4b5921e1cd5bb4/skyfield/timelib.py)
constructs `M = N P B`, computes GAST from GMST plus the equation of the
equinoxes, and has separately selected polar-motion data. Its
[nutation owner](https://github.com/skyfielders/python-skyfield/blob/31a6ed7584cd09b6e48e07546a4b5921e1cd5bb4/skyfield/nutationlib.py)
contains IAU 2000A and a polynomial mean-obliquity expression.
The installed Mac versions/hashes must be recorded separately: upstream source
inspection does not prove which version the Mac executes.

## Candidate prescriptions

| Candidate | Basis | Question to resolve |
|---|---|---|
| IAU 1980 forced nutation | ERFA `nut80`; documented Horizons long-span precedent | Polynomial fundamental arguments and linearly time-dependent amplitudes are extrapolated at J-8000. Horizons' Owen precession differs from VCW; its use is not a VCW compatibility proof or an ancient error bound. |
| IAU 2000A forced nutation | ERFA `nut00a`; luni-solar and planetary terms, unpredictable FCN excluded | More detailed modern theory does not imply better ancient accuracy. Its ecliptic/obliquity conventions and long-period terms need review before VCW composition. |
| IAU 2006-adjusted 2000A | ERFA `nut06a` | Adjustment is specifically for IAU 2006 obliquity and secular J2 treatment. Include as a diagnostic, not an automatic VCW correction. |
| No nutation | Explicit mean-axis diagnostic baseline | Useful to measure the size of omitted terms; not the selected production answer. |

ERFA source review is pinned to
[`1a8044cde5b7763295d472a6443387239127c6c8`](https://github.com/liberfa/erfa/tree/1a8044cde5b7763295d472a6443387239127c6c8).
Relevant routines:
[nut80](https://github.com/liberfa/erfa/blob/1a8044cde5b7763295d472a6443387239127c6c8/src/nut80.c),
[nut00a](https://github.com/liberfa/erfa/blob/1a8044cde5b7763295d472a6443387239127c6c8/src/nut00a.c),
[nut06a](https://github.com/liberfa/erfa/blob/1a8044cde5b7763295d472a6443387239127c6c8/src/nut06a.c),
[numat](https://github.com/liberfa/erfa/blob/1a8044cde5b7763295d472a6443387239127c6c8/src/numat.c) and
[obl80](https://github.com/liberfa/erfa/blob/1a8044cde5b7763295d472a6443387239127c6c8/src/obl80.c).

`numat` requires a mean obliquity consistent with the nutation/precession
conventions, and maps mean-equatorial to true-equatorial components.
`nut00a` documents its classical angles relative to the equinox/ecliptic of date
and distinguishes frame bias and precession adjustments.
`nut06a` explicitly adjusts obliquity convention and secular J2 effects for
IAU 2006. These contracts prevent assuming interchangeable full matrices.

## Composition questions

1. Derive the VCW mean obliquity from its mean-equatorial/ecliptic poles at the
   same split TT event. Compare it with conventional polynomial obliquities;
   never replace the accepted VCW orientation with those polynomials.
2. Quantify the candidate angles and their differences over declared sample
   epochs and local 19-Julian-year windows. A window samples behavior; it does
   not imply an exact constant 18.6-year period at remote epochs.
3. Evaluate trial `N * P_bias` transformations as explicitly synthetic hybrid
   diagnostics. Measure the pole displacement, obliquity sensitivity and
   multiplication-order effect. Matrix finiteness/closure is a software check,
   not scientific qualification of that hybrid.
4. Inspect fundamental arguments, precession/nutation long-period partition,
   reference-ecliptic differences and secular amplitude treatment. Differences
   between candidate formulas are not physical error estimates.
5. Define a coherent equinox/sidereal-angle or CIO/ERA construction before an
   observer implementation. A pole direction alone does not fix the terrestrial
   meridian orientation. Do not reuse modern polynomial `s06`, GMST/GAST or
   `sp00` at remote epochs without a separately justified policy.
6. Preserve the near-orthogonal first-order frame-bias semantics of `ltpb`.
   An exact inverse must not silently be replaced by a transpose.
7. Select a nominal policy and finite domain only after synthesis and explicit
   agreement. No new universal nutation accuracy interval is inferred.

## Agreed polar-motion disposition

For the proposed ancient/future nominal route, omit instantaneous polar motion
explicitly: `xp = yp = 0`. This means omitted, not reconstructed as physically
zero. Actual polar-motion error remains unknown. Do not synthesize or extend
final IERS records, extrapolate the Chandler phase from present measurements,
or claim an ancient terrestrial reference frame was measured.

Observed celestial-pole offsets and unpredictable free core nutation are also
unavailable for this ancient route and must be disclosed separately.
The terrestrial-origin locator and site/datum assumptions still need explicit
composition decisions; `xp = yp = 0` does not settle those choices.
Modern measured-EOP behavior is preserved.

## Bounded diagnostic and acceptance

Use only already installed NumPy/ERFA/Skyfield; no downloads or ephemeris loads.
At TT Julian years -8000, -2000, 0, 2000, 2026 and 8000, sample 229 events over
the centered 19-Julian-year interval. Preserve exact sample definitions and
installed package/source/binary hashes in a retained JSON report.

Report nutation ranges, prescription differences, VCW-versus-polynomial
obliquity differences, trial pole shifts and matrix-order sensitivity.
Check the reference ERFA nutation matrix against an explicitly constructed
Euler matrix; a sign-reversed construction must fail that comparison.
That check tests implementation conventions, not independent ancient physics.
ERFA and Skyfield share theory/heritage and must not be presented as independent
observational oracles.

Use a unique `~/Software/build/wenu/test/` run with
`run-provenance.json` written before execution and updated after success/failure.
Run the complete existing documentation gate, plugin autoload disabled, empty
`PYTEST_ADDOPTS`, and fresh bytecode/pytest cache/temp. No new permanent test
or diagnostic module is added to the repository for this assessment.

Exit: source assessment, executed diagnostic receipt with honest limitations,
recommended composition and remaining gaps, complete documentation acceptance,
then user review. If source compatibility remains unresolved, report it;
numerical agreement alone cannot close it. Later production integration needs
its own agreed roadmap scope, owner/seam tests and actual chart acceptance.

## Primary references

Reviewed 2026-10-31:

- [JPL Horizons manual, long-term ephemerides](https://ssd.jpl.nasa.gov/horizons/manual.html#long-term-ephemerides):
  long-span service uses Owen precession outside the modern interval and
  IAU 1980 nutation. This is an operational precedent, not a J-8000 error bound.
- [VCW 2011](https://doi.org/10.1051/0004-6361/201117274) and
  [2012 correction](https://doi.org/10.1051/0004-6361/201117274e):
  existing Wenu mean-axis authority, not a complete terrestrial-orientation model.
- [IERS Conventions 2010](https://iers-conventions.obspm.fr/content/tn36.pdf),
  chapter 5: modern celestial/terrestrial transformation conventions.
- [USNO Earth orientation explanation](https://maia.usno.navy.mil/information/what-is-eop):
  annual/Chandler components coexist with largely unpredictable polar motion.
- [IERS rapid service](https://www.iers.org/iers/en/organization/productcentres/rapidservicepredictioncentre/rapid):
  modern measurements and short predictions do not reconstruct ancient polar motion.
