# Nominal Earth orientation and meridian contract

Version 1 · 2026-11-02 · K4b.08.R3 accepted definition; implementation selected

## Selection, status and scope

After accepting/merging K4b.08.R2 through PR #368, Fernando confirmed clean
synchronized Mac main `067e3b337b6d2af52cf0447c6f7c229ee9c140df` and local/remote
task-branch deletion. He then selected “defining the complete orientation and
meridian convention before integrating the ancient Earth-bound observer”
with “Proceed.” This authorizes this assessment/contract document, not runtime
implementation, an unqualified observer, or the entire K4b.08 backlog.

PR #369 was accepted and merged as `9eb453b7`, with all 36 revised documentation
cases passing at `cdbb5be1`. Clean Mac main and task-branch cleanup are confirmed.
Fernando then selected implementation of this orientation calculation and its
numerical qualification, extending the target to J-13000..J+13000. The algorithm
and numerical workload are not yet qualified. Existing R1/R2 receipts retain
their narrower claims; observer/chart integration remains separate.

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
intermediate matrix `C(TT)`. This is the mathematical definition implemented by the new explicit service. Numerical transport must include the nutation path, not only
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

The selected implementation first qualifies short paths, then measures the
necessary long-path workload. Full-history qualification can require millions
of pole samples; its measured cost and successful convergence remain gates.
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

Fernando selected the computational target TT Julian years -13000 through +13000,
with finite caller-request coverage inside it. This expands the former proposed
-8000..+8000 target; it is not a physical-accuracy interval established by R2's
six sampled windows. See the component validity table below.
The J2000-to-event history is a declared dependency of every transported origin:
model-path coverage is separate from narrower caller-request coverage.
The pole models must cover the entire path; the spin model covers the event
where UT1 is needed. No extrapolation outside explicit computational admission
or omitted pole-history segments.

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

## Component validity and extrapolation limits

**Earlier target change, 2026-11-02:** after the original definition passed
36 Mac documentation cases at `6e2e25a`, Fernando asked about J-12000 to
J+12000, then instructed “Proceed. Make a note on what the validity range
limitations of each component model are.” This selects the expanded
computational target and the following explicit limitations. It does not
turn the unimplemented numerical method or extrapolated physics into a
qualified model, or authorize observer/chart integration.

**Selected implementation/range, 2026-11-02:** after acceptance/merge and
confirmed cleanup, Fernando instructed “Proceed, but extend it to -13000 to
+13000. This way we can check the results after a full precession cycle.”
The ledger now applies to that expanded target. A 26,000-year span is about a
precession cycle, not an exact closed pole path. Endpoint equality is not an
acceptance criterion; report pole separation and accumulated origin phase.

Four distinct facts must stay separate: a published model interval, a caller's
computational admission, the interval actually tested, and empirical physical
accuracy. A formula returning a finite value establishes none of the others.

| Component | Published/implemented range or meaning | Limitation for J-13000..J+13000 |
|---|---|---|
| VCW2011/2012 mean-equator and mean-ecliptic axes via ERFA | Published long-term span J2000 +/-200,000 Julian years; existing Wenu frame admission is TT Julian years -198000..+202000, further bounded by caller coverage | Target is within that modeled span. Accuracy degrades away from J2000; no per-event numerical or physical angular bound is admitted. The span is not a claim of uniformly modern accuracy. |
| Classical IAU2000A forced nutation (`nut00a`) | Theory is calibrated/qualified for modern precision use; the inspected implementation states current-epoch precision and does not supply a certified physical-validity interval reaching +/-13,000 | Fundamental-argument polynomials, time-dependent amplitudes and Earth response are extrapolated. No ancient/future precision bound is claimed. R2 sampled six 19-year windows about J-8000, -2000, 0, 2000, 2026, +8000 only; neither new endpoint nor the complete intervening interval was qualified. |
| IAU1980 and IAU2006-adjusted nutation comparisons | R2 comparison formulas, not selected additional production models. Horizons uses IAU1980 as a long-span operational prescription; `nut06a` adjusts 2000A specifically for IAU2006 precession | Computability/operational precedent does not establish ancient accuracy or VCW compatibility. The new range does not adopt the IAU2006 secular adjustment or another independent precession path. |
| Espenak--Meeus 2006 Delta-T, Wenu R1 | NASA publishes expressions for calendar years -1999 through +3000. Wenu flags complete calendar years outside that interval and extends the same outer parabola under explicit finite TT coverage | Both remote endpoints use nominal extrapolation, not measured Earth rotation. Secular-parabola/prediction regimes may be extrapolated even inside the published application interval. Unknown Delta-T error propagates to unknown terrestrial rotation/horizon error. No -7200 BCE calibration limit or new fit is claimed. |
| Earth Rotation Angle (`era00`) | Defining UT1-to-angle relationship, evaluated from split UT1; it has no independent historical Earth-rotation reconstruction interval | Algebraic evaluation at a remote UT1 does not validate the supplied UT1. Domain and physical uncertainty are inherited from the TT-to-UT1 policy; numerical precision must be checked at remote dates. ERA is not a second empirical spin model. |
| Full celestial origin by pole-history transport | Mathematical nonrotation definition with one declared seed; the explicit service is an implementation candidate, with no full-span qualified numerical date range yet | The entire J2000-to-event history, derivative/transport method, convergence and cost must be admitted. The selected +/-13,000 target is not an already passed numerical gate. No disjoint endpoint or pole-only test can certify the full matrix. |
| Modern standard frame used as origin seed (`c2i06a`) | Evaluated once at TT J2000.0, then its reference direction is projected onto the nominal hybrid equator | Only the seed is borrowed. Neither the IAU2006 precession polynomial nor modern `s06` series is evaluated at the remote event. This projection is an explicit convention, not a measured ancient alignment. |
| VCW precession locator `s_A` (Eq.26/Table9) | Published long-term PRECESSION locator; fitted within the VCW long-term study, separately from the complete nutating-origin history | Potential comparison/acceleration ingredient only. It excludes nutation's secular/periodic contribution, is not automatically the exact integral of the corrected biased pole, and must not silently replace the full locator at any date. |
| Ancient polar motion, celestial-pole offsets and FCN | `xp=yp=0` is the agreed omission; observed pole offsets and unpredictable free-core nutation are unavailable in this nominal route | No physically validated ancient/future range is implied by zeros/omissions. Their actual errors remain unknown throughout the target range; no synthetic final-IERS observations or backward Chandler-phase prediction. |
| Proposed terrestrial-origin locator `s'=0` | Fixed-origin convention, not a geophysical prediction. ERFA `sp00` approximates a secular drift of a fundamentally observation-dependent polar-motion integral | Do not replace this explicit convention with an extrapolated modern drift. Its physical discrepancy is unknown; it supplies no historical terrestrial reference-frame reconstruction. |
| Modern final-IERS reception service | Existing Wenu conservative model interval 1950–2050, intersected with actual admitted final-EOP/leap resources; its UTC adapter is post-1972 | Preserved and not extended to +/-13,000. It is a separate modern route, not a fallback for unavailable ancient orientation. |
| Modern locator/sidereal-time approximations | `s06`, modern IAU2006 precession/GMST developments and empirical `sp00` are model-specific, modern-precision expressions | Excluded as remote-event substitutes in the selected route. A polynomial's ability to return a number is not a long-term admission; matching the moving pole alone does not fix the meridian. |

The orientation layer has no ephemeris or stellar-state dependency, but an
eventual observer/chart product will have additional, independently intersected
limits:

| Later dependency | Range/qualification that must be checked |
|---|---|
| Earth/Sun geometric ephemeris | JPL publishes DE440 for years 1550–2650 and DE441 for -13200..+17191. Those are source calendar labels, not exact split-JD segment boundaries or interchangeable TT/TDB/TCB events. DE441 broadly encompasses the target, but each selected local file/body/centre/segment, boundary and overlap still needs exact admitted coverage. No selected-resource failure may silently fall back or extrapolate. Published coverage is not uniform accuracy. |
| Stellar motion/source models | Per-object source/model/capability domains remain authoritative. An orientation range cannot create missing historical models, invent radial velocity/distance, drop usable modern stars or automatically extend a saved catalogue/reuse policy. |
| TT/TDB/TCB and site/correction services | Each later conversion, spatial convention, fixed-site assumption and correction needs its own admission/receipt. The exact linear TCB/TDB convention does not itself solve TT-to-dynamical-time mapping or historical civil clocks. Ancient UTC/time-zone/leap reconstruction is not supplied. |

Range labels here use astronomical year numbering. J-13000/J+13000 mean TT
Julian epochs (`2000 + (JD_TT-2451545)/365.25`); NASA's Delta-T application
years and JPL's published coverage labels are calendar years and must not be
treated as exact interchangeable event boundaries.

**Required additional acceptance:** retain R2's unchanged evidence as sampled
comparison only; include J-13000 and J+13000 endpoints, their entire origin
histories and intermediate negative/positive epochs in the future full-matrix
gate. Check just-inside/at/outside admission, scale/phase wrapping, refinement,
failure after warm use and measured long-path cost. If numerical reliability or
resource coverage fails at a requested event, refuse rather than implying that
the agreed target has already been achieved. Physical error may remain unknown
even when all numerical gates pass.

## Selected implementation and acceptance boundary

Definition acceptance and implementation selection are recorded above. Acceptance requires:

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
5. Exercise J-13000 and J+13000, retained J-2000/J-8000 references and
   intermediate negative/positive epochs with finite-path admission, full-history
   refinement/cost and failure controls. These are full-frame checks;
   retain R2's unchanged pole-only receipt instead of repeating it.
6. Record cold/warm/sequence costs before admitting a practical algorithm.
   Long-period precession acceleration must not alias the shorter nutation terms.
   No claim of fast request-level use follows from an unmeasured integral.
7. Extend closest existing coordinate/observer-resource test owners, preserve
   existing modern and mean-axis defaults, and run the complete documentation
   gate. Do not run unrelated source-acquisition/render suites for this matrix
   service. Actual observer charts follow their later public-product gate.

The nominal accepted mathematical definition does not establish that the implementation,
numerical tolerance or performance is already qualified.
Do not close parent K4b.08 or activate observer/chart integration with R3 alone.

## Orientation-service implementation candidate

The existing `wenu.astrometric_coordinates` owner now exposes
`NominalEarthOrientation`, `OriginTransportSettings` and immutable
`NominalOrientationResult`/`OriginTransportReceipt` records. The service is
opt-in; no modern observer/chart route calls it.

The scalar locator is evaluated by exact connection increments along shortest
great-circle edges between sampled poles. Each increment is minus the signed
solid angle of the triangle formed by north, old pole and new pole. For a
smooth path these polygon integrals converge to the stated nonrotation integral.
Nested, uniformly spaced paths halve the step; Richardson extrapolation removes
successive even-power terms. At least four paths are required, and both last
diagonal differences must meet the requested refinement tolerance. This is a
convergence estimate, not a certified error bound or proof against every possible
alias. Fixed, great-circle and closed-loop analytic cases plus independent
Rodrigues vector transport protect the definition/sign/geometric phase; actual
short-path vector comparison protects composition.

Default maximum initial step is eight TT days; tolerance is `1e-8` radians
(about 2.1 milliarcseconds) on that estimate, with six maximum refinements and
50 million total samples. Callers may choose tighter finite settings; finite
work-budget or convergence failure refuses output. Memory is chunked; all
J2000-to-event path segments are evaluated. No coarse mean-only shortcut,
truncated nutation, persistent cache or previous-request origin is used.
The northern gauge formula uses the normalized full pole and exact `1+Z`;
its singularity and ambiguous long polygon edges refuse.

The public endpoint and anchor use explicit split TT; interior path samples use
binary64 TT offsets from J2000, and ERFA's Julian-year conversion is disclosed by
the unchanged mean-frame receipts. Total numerical error remains unknown.
A request for a certified physical or total numerical bound refuses.
The result records exact TT/UT1, mean-frame identities, backend versions and
owner/ERFA file SHA256 hashes, seed/pole/origin, unwrapped locator, all refinement
diagonals/panel counts, cumulative samples and timings, ERA and forward/inverse
matrices. Model identity binds event, request/path/spin coverage, policies,
settings, backend/code hashes and the actual computed frame. Timing does not
enter deterministic identity.

A prepared result can be applied repeatedly to directions at its exact event;
preparing another event integrates independently. Cold preparation is not
promised to be chart-interactive. The long-path acceptance prints retained JSON
receipts at J-13000, J0 and J+13000, then endpoint pole separation and accumulated
unwrapped-origin phase. It does not demand exact 26,000-year periodicity.
The J0 result supplies an intermediate negative epoch. All full-path numerical
and practical-cost admission remains pending until that marked slow gate runs.

Local isolated verification: 75 selected convention/long-frame cases passed in
2.57 s using Python 3.12, NumPy 1.26.4, PyERFA 2.0.1.5/ERFA 2.0.1/SOFA
20231011. This fetched dependency subset is not a full Wenu/Mac acceptance run.
No new endpoint transport result or full-span qualification is claimed.

## Primary sources and source review

Reviewed 2026-11-02:

- NASA Espenak--Meeus polynomial application interval and coefficients:
  https://eclipse.gsfc.nasa.gov/SEcat5/deltatpoly.html
- JPL DE440/DE441 published spans and model distinction:
  https://ssd.jpl.nasa.gov/doc/de440_de441.html
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
