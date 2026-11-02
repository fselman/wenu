# Nominal Earth orientation and meridian contract

Version 1 · 2026-11-02 · K4b.08.R3 definition candidate

## Selection, status and scope

After accepting/merging K4b.08.R2 through PR #368, Fernando confirmed clean
synchronized Mac main `067e3b337b6d2af52cf0447c6f7c229ee9c140df` and local/remote
task-branch deletion. He then selected “defining the complete orientation and
meridian convention before integrating the ancient Earth-bound observer”
with “Proceed.” This authorizes this assessment/contract document, not runtime
implementation, an unqualified observer, or the entire K4b.08 backlog.

This document proposes a concrete complete-orientation definition and a bounded
implementation/acceptance boundary for review. It changes no runtime behavior.
The numerical algorithm, workload and complete-matrix acceptance described below
have not run. Existing R1/R2 receipts remain valid for their narrower claims.
R3 definition acceptance and a subsequent implementation selection are separate.

## As-is assessment and placement

| Existing owner | Responsibility to preserve | Missing composition |
|---|---|---|
| [Astrometric conventions](../../../src/wenu/astrometric_coordinates.py) | `LongTermFrame` supplies corrected VCW mean-equatorial/ecliptic axes, first-order frame bias and finite TT admission | No full nutating pole history, nonrotating celestial origin or terrestrial meridian |
| [Named rotation](../../../src/wenu/earth_rotation.py) | R1 maps the exact input TT to split UT1 with named Delta-T and provenance | UT1 supplies the rotation angle, not the celestial origin |
| [Modern reception](../../../src/wenu/astrometric_observation.py) | Final-IERS, modern `xys06a/s06/sp00/epv00/apco` admission and bounded observer realization | Cannot extend its date limits to obtain the proposed ancient model |
| [Coordinate guide](../coordinate_system_guide_v0.9.5.md) | Axes, physical origin/status, time scale and source event remain separate | A rotation matrix does not supply observer translation/corrections |
| [R2 assessment](ancient_observer_orientation_assessment_v1.md) | Nominal IAU2000A/VCW recommendation; explicit polar-motion omission; measured trial-pole diagnostics | The pole alone did not establish rotation about that pole or full horizon geometry |

The orientation policy belongs in the astronomical convention/service layer,
alongside the existing coordinate/time owners, not in charts, renderers,
generic kernel geometry, stellar providers or source catalogues.
Extend the existing convention owner when implementing this scope unless
the actual lifecycle/dependency review demonstrates a distinct enduring owner.
Keep ERFA/NumPy loading lazy as appropriate; no new dependency, arbitrary plugin
loading or mutable global model selection is proposed.

## Proposed pole definition

Use the accepted VCW mean axes and classical, unadjusted IAU2000A
forced-nutation prescription recommended in R2:

1. Evaluate `LongTermFrame` mean-equator/equinox and mean-ecliptic/equinox
   at the same explicit split TT event. Derive mean obliquity from their
   normalized pole vectors. Preserve their original backend/matrix identity.
2. Obtain classical `nut00a(TT1, TT2)` longitude/obliquity angles.
   Retain extrapolated arguments/amplitudes and unknown physical error.
   No automatic `nut06a` secular correction or arbitrary series-term deletion.
3. Form the trial mean-to-true nutation rotation with that VCW obliquity.
   In the column-vector convention, let `B = N * P_bias`.
4. Define the nominal instantaneous celestial pole `n(TT)` by normalizing
   row 3 of `B`. Frame bias has already been applied once.
   Preserve the existing first-order near-orthogonal VCW matrix unchanged;
   the new service derives an exact orthonormal output frame from the pole.

This is an explicitly named Wenu nominal combination, not an IAU-standard
long-term solution, measured ancient CIP, or a certified angular-accuracy model.
Reference-ecliptic/model differences remain disclosed assumptions.
R2's diagnostics support a practical candidate; they are not a physical bound.

## Proposed celestial origin: transport the same pole history

A full celestial orientation needs a zero point on the equator as well as its
pole. Define that zero point kinematically from the SAME nominal pole history.
Do not choose a new zero point independently for each requested date.

Reference event: TT J2000.0 = JD(2451545, 0).
Proposed versioned initial-origin convention:

- Evaluate the modern standard `erfa.c2i06a` only at J2000.0 and take its
  first-row celestial-origin vector as the reference direction.
- Project that direction onto the plane perpendicular to the nominal hybrid
  pole at J2000.0 and normalize. This makes the seed compatible with the chosen
  pole rather than relabelling a different model's full frame.
- The second row is the cross product of the pole with that first row.
  Record the exact seed, ERFA/backend identity and projection convention.
  Refuse a degenerate projection. This is a conventional alignment, not a
  measured historical orientation or a claim of exact standard-model identity.

Propagate the celestial-origin unit vector `a(t)` without rotation within
the moving equatorial plane, with `t` measured consistently on TT:

```text
 da/dt = -n * (a dot dn/dt),    a dot n = 0,    |a| = 1.
```

Then `b = n cross a`, and the rows `(a,b,n)` define the celestial-to-
intermediate matrix `C(TT)`. The displayed text is a mathematical definition,
not shipped code. Numerical transport must include the nutation path, not only
the mean precession path. Re-normalization alone does not establish convergence.

An equivalent reference uses the IERS Conventions (2010) Eq. (5.8) locator
integral for the SAME normalized `(X,Y,Z)` pole and matching initial origin:

```text
 s(t) = s(t0) - integral[t0..t] (X*dY/dt - Y*dX/dt)/(1+Z) dt.
 C(t) = erfa.c2ixys(X(t), Y(t), s(t)).
```

The seed locator must reproduce the projected initial frame, with its sign and
phase checked. Do not reset the integration constant at another epoch, assume
`s(t0)=0`, replace the exact denominator by a modern small-angle expansion,
or choose a longitude offset to match one ancient chart.
The scalar representation must refuse its coordinate singularity; vector
transport provides a separate formulation without that particular singularity.

These two expressions are the proposed mathematical contract. A numerical
algorithm can implement one and use the other for independent software checks.
Agreement checks validate their implementation, not ancient Earth physics.

## Published long-term locator and alternatives

VCW 2011 Sect. 5, Eq. (26), Table 9 supplies a long-term approximation
`s_A` for PRECESSION. The paper explicitly states that full `s` also
needs nutation effects: a secular contribution and short-period terms.
Therefore `s_A` alone must not silently accompany the full nutating pole.

The published locator is valuable as a mean-precession comparison and potential
acceleration ingredient. It is not automatically the exact integral of the
corrected, biased, nutating pole used here: reconcile the seed, bias, fitted
parameterization and missing nutation contribution before any substitution.

| Alternative | Disposition |
|---|---|
| Modern `s06` or GMST/GAST polynomials evaluated at J-8000 | Excluded from this proposed route; their precession/time development does not match the chosen long-term pole history |
| VCW `s_A` with the full nutating pole and no further treatment | Incomplete origin model; useful only as a labelled comparison |
| Explicit mean-pole/mean-origin approximation | Scientifically different product policy; not silently substituted for the accepted forced-nutation direction |
| Full-history nonrotating-origin definition above | Recommended complete mathematical contract |
| Accelerated transport, analytic correction or verified interpolation | Implementation choices only after convergence/cost evidence; no persistent cache format or reuse interval is selected here |

No new multi-million-sample workload is selected merely by publishing this
definition. The future implementation must first qualify the numerical method
on short intervals, then measure the necessary long-path workload.
A performant formula cannot be selected solely because two endpoint poles agree.

## Spin and proposed terrestrial-origin convention

Use R1's named `EarthRotationModel.evaluate(TT)` for the SAME event.
Compute `ERA = erfa.era00(UT1_1, UT1_2)` from its split UT1 receipt.
Do not independently obtain another UT1 from Astropy/Skyfield.

Retain the agreed ancient polar-motion omission. Explicitly propose
`xp=yp=0` AND terrestrial-origin locator `s'=0`, giving an identity
polar/origin matrix `W`. The extra `s'=0` is a proposed convention in
this R3 definition, not a deduction that measured polar motion was zero.
ERFA documents `sp00` as a small empirical secular approximation to an
essentially unpredictable integral of observed polar motion; do not extrapolate
that drift into the proposed ancient fixed-pole terrestrial model.

Use the ERFA column-vector/passive-rotation convention:

```text
 celestial_to_terrestrial = W * R3(ERA) * C(TT),    W = identity.
 R3(angle) = [[cos(angle), sin(angle), 0],
              [-sin(angle), cos(angle), 0],
              [0, 0, 1]].
```

The inverse of this newly constructed orthonormal frame is its transpose.
That statement does not change the first-order-bias inverse contract of the
original `LongTermFrame` matrix.

If equinox-based reporting is needed, derive an orthonormal true-equator/
equinox triad from the same `B` and the same pole, with the projection/
normalization convention explicit. Use matching `s` and `erfa.eors`
to obtain `EO`, then `GAST = ERA - EO`.
Require equality of the complete CIO and equinox terrestrial matrices.
This is a consistency check, not another independent spin or precession model.

Outputs describe a NOMINAL terrestrial-axis convention. They must not be
advertised as a measured ancient ITRF realization or as reconstructing a
historical Greenwich meridian, tectonic motion or site geography.

## Proposed domain, receipts and failure boundary

Propose the initial computational admission TT Julian years -8000 through +8000,
with finite caller-request coverage inside it. This is a reviewable scope limit,
not a physical-accuracy interval established by R2's six sampled windows.
The J2000-to-event history is a declared dependency of every transported origin:
model-path coverage is separate from narrower caller-request coverage.
All required models must cover the entire path and event; no extrapolation
outside the explicitly admitted computational domain or omitted path segments.

Retain at least:

- Exact split TT input and the independent split UT1/Delta-T receipt.
- Mean-frame, nutation, initial-origin, transport and terrestrial-origin policy
  identities; installed backend versions/hashes and seed vectors.
- The normalized pole, origin locator/frame, ERA, complete forward/inverse
  matrices and their input/output axis conventions.
- Requested coverage, history interval, algorithm settings, step/refinement/
  convergence diagnostics and model extrapolation/omission status.
- Unknown physical error and separately unknown numerical error unless an
  actual bound is qualified. A convergence estimate is not a certified bound.
- Recorded timing/workload and lifecycle identity for any prepared orientation.

Refuse wrong scales, mismatched event/model receipts, missing path coverage,
invalid seed/pole/matrix, singular scalar locator coordinates, nonconvergence,
unsupported policy or accuracy requests that cannot be met. Check failure
after successful/warm use as well. Do not reuse an orientation across a changed
event/model/seed/algorithm merely because its displayed year label matches.

This layer returns orientation only. It does not admit TT/TDB/TCB conversion,
Earth/site translation, aberration, deflection, parallax, light time, atmosphere,
site datum/height, chart-family adoption, worker descriptors or a new SDK scale.
Those remain later bounded observer/correction/product responsibilities.

## Proposed smallest implementation and acceptance boundary

After definition review and explicit implementation selection:

1. Add a named, immutable orientation service at the justified existing owner,
   composing current frame/nutation/rotation services without changing defaults.
   The first deliverable is a complete matrix and receipts, not a chart.
2. Qualify the nonrotating-origin algorithm with constructed fixed-pole,
   analytically moving-pole and closed-loop/geometric-phase cases. Compare
   vector transport with the scalar integral and show refinement behavior.
3. Compare modern complete matrices with ERFA standard orientation using the
   SAME UT1 and identity polar/origin matrix. Report expected model differences;
   never infer ancient accuracy from the modern agreement.
4. Check independent split-UT1 ERA evaluation, one-turn/sign conventions,
   forward/inverse, determinant/orthogonality, and complete CIO/equinox matrix
   equivalence. Inject wrong signs/order, frozen/zero locator and bad seed.
   A fault must demonstrably fail its corresponding check.
5. Exercise J-2000, J-8000 and selected future endpoints with finite-path
   admission, refinement/cost and failure controls. These are full-frame checks;
   retain R2's unchanged pole-only receipt instead of repeating it.
6. Record cold/warm/sequence costs before admitting a practical algorithm.
   Long-period precession acceleration must not alias the shorter nutation terms.
   No claim of fast request-level use follows from an unmeasured integral.
7. Extend closest existing coordinate/observer-resource test owners, preserve
   existing modern and mean-axis defaults, and run the complete documentation
   gate. Do not run unrelated source-acquisition/render suites for this matrix
   service. Actual observer charts follow their later public-product gate.

The nominal mathematical definition can be accepted without claiming that
the implementation, numerical tolerance or performance is already qualified.
Do not close parent K4b.08 or activate observer/chart integration with R3 alone.

## Primary sources and source review

Reviewed 2026-11-02:

- IERS Conventions (2010), chapter 5, Eq. (5.8) and sections 5.4–5.5:
  https://iers-conventions.obspm.fr/content/tn36.pdf
- VCW 2011, Sect. 5, Eqs. (24)–(28), Table 9:
  https://doi.org/10.1051/0004-6361/201117274
  Published-paper copy inspected at
  https://www.archaeoastronomy.it/Archaeoastronomy%20Program/Vondrak/Vondrak.pdf
- Authors' 2011 summary (precession part of the locator):
  https://syrte.obspm.fr/jsr/journees2011/pdf/vondrak.pdf
- Corrected mean-axis implementation remains the accepted VCW2011/2012 ERFA
  owner; the separately fitted locator series is not silently substituted for it.
- ERFA source inspection pinned to
  https://github.com/liberfa/erfa/tree/1a8044cde5b7763295d472a6443387239127c6c8
  Routines: `c2ixys`, `c2tcio`, `eors`, `era00`, `s06` and `sp00`.
  No copied library implementation or new numerical execution is claimed.
