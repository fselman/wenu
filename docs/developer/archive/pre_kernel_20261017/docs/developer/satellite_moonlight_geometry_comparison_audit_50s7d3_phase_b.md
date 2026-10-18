# Phase B: independent Moonlight geometry comparison audit plan

**Status:** Candidate documentation-only plan; Phase B execution and Moonlight runtime are not authorized.

**Date:** 2026-09-23

**As-is base:** `6fbceedc9c8b075ace42db4e32fe7b7344f43457` on `program/50s-crossing-foundation`.

**Purpose:** Specify an independent, reproducible comparison of Wenu's future
same-instant satellite-to-Moon geometry against direct SPICE calculations and
the actual geometry conventions required by the exact LIME v1.4.2 direct
selenographic interface. This plan is reviewable before any new resource
retrieval, SPICE comparison execution, LIME rerun, or production change.

## 1. Evidence already established and remaining gap

The accepted 50S.7D.3B Phase-A Mac receipt has manifest SHA-256
`c394d91238ce6e0cdddf05e21212f8091d90fd9cdec48516ea936e3444163575`.
The exact LIME package digest is
`e0a84e250dc4f5beb8a8305278756bbc0b2b136814b9c4defb053970f983ba21`;
the bundled coefficient digest is
`8e6839d95315eb2d797484be559ad70b69010cc1eb9b614770f61bb5ce2cf691`.
Ten manually supplied scalar rows confirmed six CIMEL bands, the
`2 <= abs(phase_angle) <= 90` output flags, deterministic central values,
and nonzero uncertainty values. The app and package signatures remain
unverified, and the notice inventory does not establish license clearance.
The external evidence remains on Fernando's Mac; do not commit the package,
coefficients, binary outputs, or copied model tables.

Those rows supply the lunar coordinates and signed phase *to* LIME; LIME
returns them in its outputs. They do not test their derivation from a
satellite orbit, identify LIME's lunar frame or phase-sign rule, or validate
an ITRS-to-lunar transformation. The central values happen to be symmetric
for the supplied opposite signs. Neither symmetry nor the in-domain flag can
establish the sign convention. No Wenu Moonlight value has been evaluated.

## 2. Scientific question and independence

For an immutable satellite Cartesian state at canonical UTC instant `t`,
can an independently computed SPICE reference and a future Wenu-owned
geometry composition agree on each model input, *after* the reference frame,
orientation epoch, longitude direction, angle definition, time scale, and
correction policy are explicitly frozen? Geometry agreement and compatibility
with LIME's intended convention are two distinct claims; prove each
separately.

The comparison must not call Wenu's proposed lunar geometry code to produce
the reference. Pin an immutable satellite state with frame, centre, units,
UTC, orbit/snapshot and Earth-orientation identities; independently form
geocentric and lunar-relative vectors from SPICE ephemeris states and an
explicitly selected rotation into the same inertial frame. If satellite
ITRS-to-inertial conversion is needed, independently specify and validate
that Earth-orientation conversion; SPICE Earth fixed frames cannot silently
stand in for Wenu's ITRS policy. The accepted Wenu propagation may supply
the *input* satellite state, not the reference Moonlight answer. A
separate SPICE calculation from these frozen inputs is the reference, and
comparison to Wenu is meaningful only once a Wenu candidate exists.

The initial physical calculation uses Sun, Moon, Earth, and satellite at one
instant, geometric SPICE states (`abcorr=NONE`), a named inertial frame,
and a named lunar body-fixed frame. No apparent Earth observer direction,
retarded ephemeris, or unannounced aberration correction may be substituted.
If LIME's intended convention differs, characterize both policies as
separate columns before proposing a scientifically justified choice; never
patch a disagreement by changing signs or fitted tolerances.

## 3. Frozen-input and kernel preflight for a later authorized run

Before execution, publish a reviewable, digest-bound case specification
outside the Python package. Each row must identify UTC (including time
scale conversion/LSK), satellite state and frame, orbit/snapshot/EOP
resources, SPK and lunar PCK/FK coverage, orientation frame and epoch,
shape assumptions, and the exact source of any independent comparison
value. Record tool versions, all kernel paths, byte counts, SHA-256 digests,
kernel load order, transformations, and SPICE correction flags. Reject a
missing kernel, out-of-coverage epoch, mixed DE versions, inconsistent
time scales or centres, or an unspecified frame; do not fetch a replacement
implicitly.

Do not assume that DE440/DE440s positions supply a compatible high-accuracy
lunar orientation. Inspect the lunar PCK and FK pairing and its declared
coverage first. Compare `IAU_MOON` with the DE440-compatible `MOON_ME` and
`MOON_PA` *as candidates*, recording their angular and coordinate
differences; choose the frame only from explicit LIME documentation/source
evidence and independent validation. NAIF cautions that the default
`IAU_MOON` orientation is less accurate than the appropriate lunar PCK/FK
frames. Named-frame SPICE routines or an explicit inertial-to-fixed
transformation avoid an implicit default.

The existing accepted external LIME package may be used only under a
separately authorized controlled protocol. This planning milestone does not
rerun it, download kernels, call LIME's EO-CFI satellite route, install
resources, or grant new execution authority.

## 4. Component definitions and comparison table

For each accepted case, retain independently recomputed raw Cartesian
vectors before angle conversion and report units and at least these
components:

| Component | Required comparison |
| --- | --- |
| Moon-to-Sun and Moon-to-satellite | Common-frame vectors, both centre-to-centre distances, Sun-Moon distance in au and satellite-Moon distance in km; confirm nominal au conversion and whether LIME expects centre distance. |
| Unsigned phase | Angle between the two Moon-centred vectors in `[0,180]` degrees; document zero at full-Moon geometry and the satellite, not terrestrial observer, as the receiving point. |
| Signed phase | Candidate sign from an explicit oriented lunar reference and Sun/observer geometry, with waxing/waning and near-zero discriminants; preserve `unresolved` until authoritative LIME evidence establishes its definition. |
| Lunar coordinates | Body-fixed observer and solar longitude/latitude in degrees, positive direction, wrapping range, pole/prime-meridian definition, lunar orientation epoch, and Sun latitude even though the current CLI does not take it. |
| Distances and timing | Centre-to-centre versus surface distances, same-instant geometric versus light-time-corrected variants, stellar aberration flags, and effects in each field. |
| Source paths | Sun-to-Moon eclipse and Moon-to-satellite Earth occultation as separate statuses; report these without folding them into phase or applying an unreviewed radiometric correction. |

Construct the signed phase from a written oriented-vector rule and verify
the sign on independent waxing and waning exemplars. Because opposite-sign
Phase-A outputs have equal central values, *do not infer the LIME sign from
the Phase-A radiance*. If the pinned LIME source, scientific documentation,
and independent orbit-based reference provide no authoritative sign mapping,
stop with `signed_phase_unresolved` and retain Moonlight
`not_evaluated`.

Explicitly distinguish the lunar frame origin from the rotation reference
epoch. A centre-to-centre vector rotated at `t` is not automatically the
same as an apparent subsolar *surface point*: record any light time and
surface intercept choices separately. Probe +/-180-degree longitude
wrapping and longitude sign with nondegenerate geometries.

## 5. Discriminating case matrix

The later evidence must include at least:

1. LEO, MEO, GEO, and highly elliptical satellite states, with perigee
   and apogee representatives for the latter; use immutable validated
   snapshot or explicitly labelled synthetic state evidence.
2. Positive and negative sign candidates in admitted lunar-phase regions,
   near full Moon but inside the `2` degree limit, mid-phase, and near the
   `90` degree limit; geometry cases outside `[2,90]` by absolute value
   may characterize frame/phase behavior but are excluded from model
   prediction.
3. Both lunar hemispheres, distinct observer and solar longitudes,
   longitude wrap, high latitude, and a geometry with nonzero libration;
   avoid only symmetric points that cannot distinguish candidate frames
   or signs.
4. Unocculted Moon, Earth-limb/fully Earth-occulted Moon, and a lunar
   eclipse exemplar, each with separate path statuses. Do not infer
   irradiance zero from unresolved partial occultation or eclipse.
5. Same epoch evaluated with `NONE` and separately named light-time or
   aberration variants, only to characterize convention-dependent
   differences, never to mix correction policies in one row.

A reference row must list expected qualitative behavior and exact
provenance before computing any numeric tolerance. Physical satellite
cases should cover materially different ranges to expose parallax and
unit mistakes; hand-picked Phase-A scalar rows are retained only as
external interface checks, not orbit-level validation.

## 6. Evidence, diagnostics, and decision gates

For each case preserve frozen input, kernel identities, named frames,
transform epochs, Wenu result if a later candidate exists, independent
SPICE result, per-component signed/absolute residuals, method and warning
log, and a manifest with byte counts and SHA-256 digests. Verify
longitude residuals with circular differences and report domain
classification separately from numeric residuals. An independent
second-path sanity check should reconstruct the inertial dot-product phase
from raw vectors and verify vector/distance invariants without calling the
proposed Wenu evaluator.

Characterize residual distributions by orbital regime and correction
policy; set thresholds only after documenting numerical conditioning and
kernel/EOP/orientation uncertainties. A component may pass only under one
declared convention with reproducible evidence. Distinguish a proven
match, a systematic convention mismatch, an ambiguous sign, a missing
resource, and an unsupported model-domain geometry. Do not assign a
tolerance that hides a frame, longitude, timing, or units error.

Before a later runtime proposal, obtain the exact LIME geometry and
correction definitions from pinned publisher documentation or source;
complete the separate license review; reproduce authoritative LIME
native-band cases under permitted offline use; and resolve model-domain,
uncertainty, eclipse, and occultation policies. Any unresolved component
blocks admission of numeric Moonlight. A successful SPICE comparison by
itself cannot establish radiometric correctness or permit redistribution.

## 7. Ownership, verification, and next decision

This milestone adds documentation only. No production lunar transform,
new dependency, API, coefficient/resource file, data acquisition, LIME
execution, test oracle, report, CLI, renderer, or Moonlight value is added.
`satellites/illumination.py` remains the future owner of same-instant
lunar geometry and typed path statuses; `satellites/radiometry.py`
remains the future owner of external LIME admission and native-band
radiometry. Existing satellite propagation, ephemeris source, EOP and
topocentric contracts remain authoritative; LIME's EO-CFI satellite route
stays excluded. The coordinate-system guide was reviewed and remains
current for implemented behavior because this audit adds no coordinate
value. A later runtime proposal must update it before acceptance.

This plan may be accepted after the documentation/package gate, full
plugin-disabled suite at the required milestone handoff, diff and clean
branch checks, and Fernando's scientific and architectural review.
Acceptance of this plan authorizes no Phase-B execution by itself. The
next bounded decision is a separately approved frozen-kernel and
comparison-run protocol that names exact resources, specimen cases, and
permitted commands. Execution receipts and any production implementation
would require their own subsequent review and acceptance.

## Primary reference material

- NAIF lunar FK for the DE440 family:
  https://naif.jpl.nasa.gov/pub/naif/pds/wgc/kernels/fk/moon_de440_220930.tf
- NAIF special lunar/Earth PCK/FK guidance:
  https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/Tutorials/pdf/individual_docs/23_lunar-earth_pck-fk.pdf
- NAIF `SUBSLR` documentation for explicit frame, epoch and aberration
  semantics:
  https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/subslr_c.html
- Official LIME Toolbox repository (pin the exact release/source commit
  before extracting a convention):
  https://github.com/LIME-ESA/lime_tbx

## Accepted Phase B audit plan

Fernando scientifically and architecturally accepted exact plan head
`21873e591d1ae592718e64894141ff31fe17ceb1` on 2026-09-23 and
explicitly requested PR 191 merge. At that head, 235 focused documentation
and package tests passed on the Mac in 12.30 seconds, all 2,872
plugin-disabled tests passed in 255.75 seconds, and diff, upstream and
clean-tree checks passed. Preserve the distinction between independently
recomputed geometry and proof of LIME's intended input convention: the
accepted Phase-A scalar outputs do not resolve signed phase. The next
proposal may freeze exact kernels and a controlled comparison-run protocol
for review. This acceptance does not authorize that run, new resource
acquisition, LIME execution, production Moonlight, licensing clearance, or
50S.7D.4+ work. Merge is authorized; branch deletion is a separate decision.
