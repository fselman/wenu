# Wenu Earth rotation models

## Current support, model study and proposed modular design

Version 1 · 30 October 2026 · Research and design guide

**Status:** research study with a subsequent implementation-selection update. The K4b.08.R1 candidate now implements one named model and Skyfield seam; Mac acceptance and ancient observer integration remain pending. This study does not qualify ancient observer accuracy. “Canonical” here means established and citable, not a universally mandated ancient-Earth solution.

## Executive summary

The immediate objective is a working ancient-sky chart with a well-defined rotation timeline. Historical residual fitting and comprehensive uncertainty propagation can follow later. A modest, reproducible baseline is more useful now than an unfinished reconstruction framework.

Four choices were examined: a custom secular-deceleration model; the Stephenson–Morrison–Hohenkerk historical reconstruction with its 2020/2021 update; Espenak–Meeus; and IERS Earth-orientation data. The last is a data source with final, rapid and predicted regimes, not an ancient-rotation formula. There is no single prescribed extrapolation common to all implementations.

**Subsequent implementation selection (2026-10-31):** after this study, Fernando explicitly chose Espenak--Meeus (2006), its same-parabola remote extension, and a named modular selection boundary for Skyfield. K4b.08.R1 now contains the candidate implementation; Mac acceptance is pending. The originally proposed pinned Skyfield composite remains a possible later adapter. The first default applies to the new model service, not to existing observer/chart defaults. See the [current API](../implementation_reference.md#named-nominal-earth-rotation-model).

Provide an explicit model-selection boundary from the outset. Pin coefficients, tables, implementation and splice policy; report the regime actually used. Do not silently download new tables, change extrapolation, or let one chart layer compute a different UT1 from another. Modern measured operation must remain available independently of ancient nominal operation.

Numerical study illustrates why this matters. Two commonly encountered long-term parabolas differ by about **554 seconds at formula year −2000** and **4,841 seconds at −8000**, equivalent to roughly **2.31° and 20.23° of rotation**. These are model differences, not confidence intervals. Specifying only a deceleration coefficient is also insufficient: reference phase and reference rate materially affect the ancient result.

## 1. What Wenu supports at the inspected baseline

Repository baseline: `fselman/wenu`, main commit `99d8414494b3ff180b4be6ad37640c30921fc26a`. The user confirmed clean synchronization and branch cleanup after PR #365. The assessment made no production changes and ran no Wenu runtime acceptance tests. Saving this guide changes documentation only.

| Existing owner/capability | Actual boundary |
|---|---|
| Ordinary `Observer` | Resolves civil timestamps through Python datetime/time-zone handling; constructs a Skyfield timescale with `loader.timescale()`; offers no explicit rotation-model selector. Its effective ΔT policy depends on the installed Skyfield and its data. This is not an admitted BCE observer interface. [R1] |
| `ErfaReceptionBackend` | Copies caller-verified local leap and final IERS-B data. Intersects resource coverage with a conservative 1950–2050 model interval; its UTC input adapter is post-1972. Uses explicit final EOP, ERFA EPV00/APCO and vacuum realization. It refuses unsupported coverage. [R2] |
| Stellar epoch products and `wenu_chart atlas-sheet --stellar-epoch-config` | Accepted observer-free saved-catalogue route. Stellar reuse/advancement does not establish terrestrial rotation. [R3] |
| Exact-event Earth/Sun companions | Accepted geometric ephemeris state persistence. A saved Earth PV does not include UT1, polar motion or the terrestrial site's orientation. [R3] |
| Named spin timing and ancient observer charts | K4b.08.R1 implements an Espenak--Meeus model-service candidate with an explicit name and Skyfield callable. Mac acceptance is pending. Ordinary ancient observer charts and the other model adapters remain unimplemented. [R3] |

Long-term mean-axis orientation already has a separate admitted role. It must not be mistaken for a complete precession–nutation–Earth-rotation–polar-motion observer transformation.

## 2. Separate the physical quantities

The proposed spin service supplies the relation between a uniform dynamical time and terrestrial rotation:

\[
\Delta T = TT-UT1,\qquad UT1=TT-\Delta T.
\]

Differences are expressed in SI seconds; the two-part Julian-date conversion must preserve that convention. Modern data often provide DUT1 instead:

\[
DUT1=UT1-UTC,\qquad
\Delta T=(TAI-UTC)+32.184\ {\rm s}-DUT1.
\]

Apply the appropriate historical UTC/TAI convention. Ancient dates must not be passed through a fictitious leap-second or modern timezone history. IAU SOFA documents the time-scale conversions and their assumptions. [R10]

The observer transformation also needs axis orientation and polar motion, plus the site and relevant optical corrections. Earth Rotation Angle is computed from UT1 through the common transformation owner; a ΔT adapter should not build a competing rotation matrix. IAU SOFA treats these as distinct parts of Earth attitude. [R11]

JPL SPKs supply orbital states through stored interval representations. They do not reconstruct terrestrial spin history. Repeated ancient-epoch evaluation does not require integrating the Solar System backwards from today; saved exact-event states primarily provide reproducibility and detached access. [R17]

## 3. The four choices

| Choice | Representation | Empirical regime | Outside that regime | Proposed Wenu role |
|---|---|---|---|---|
| Custom secular model | Constant nominal angular deceleration, or an explicitly defined quadratic ΔT approximation | No observational reconstruction unless separately calibrated | Its entire admitted domain is a nominal extension | Transparent experimental/control model |
| Updated historical reconstruction | Piecewise historical spline, based on the 2016 study and 2020/2021 update | Audited updated coefficient table spans scalar years −720 to 2019 | Requires a named continuation and join rule | Preferred historical component |
| Espenak–Meeus (2006) | Piecewise polynomial ΔT prescription | A mixture of historical fits, measurements and estimates | Quadratic outer branches; NASA presentation covers −1999 to +3000 | Later comparison/reproduction model |
| IERS EOP | Versioned observations, rapid estimates and bounded predictions | Actual coverage and status of the chosen product | No ancient continuation; prediction horizon belongs to its product | Modern reference, with refusal outside admitted coverage |

### 3.1 Custom monotonic secular model

The exact constant-angular-deceleration construction is

\[
\theta(t)=\theta_0+\omega_0(t-t_0)+\tfrac12\alpha(t-t_0)^2,
\quad\alpha<0,
\]

with a specified angular/time convention and reference frame. It needs **three** anchored parameters: phase, rate and acceleration. A deceleration number alone does not determine an ancient rotation angle. The rate can be monotonic even though ΔT is not monotonic.

A convenient first-order alternative uses a linear change in day length. Let `a` be its increase in seconds per Julian century and `C=(y−y0)/100`. Then

\[
\Delta T(C)=D_0+B C+\tfrac12(36525)aC^2.
\]

Here `D0` is the reference ΔT and `B` is the reference slope in seconds per century. This quadratic is a definition of a nominal model; it must not be described simultaneously as an exact constant-LOD-derivative model and an exact constant-angular-acceleration model. Those conventions agree only to the appropriate approximation order.

The 2021 reconstruction's mean deceleration, `−(4.59 ± 0.08) × 10^-22 rad s^-2`, corresponds approximately to `+1.72 ± 0.03 ms/century` in day length. That historical mean motivates a nominal coefficient but does not remove phase/rate calibration or irregular changes. [R5]

For `a=0.00172 s/century`, the quadratic coefficient is `31.4115 s/century²`. **Illustrative anchors, not a proposed calibration:** taking `y0=2000`, `D0=63.86 s` and `B=0` gives ΔT = 314,178.86 s at `y=−8000`. Changing only the slope to `0.4 s/year` gives 310,178.86 s: a 4,000-second difference, about 16.71° of rotation. Both have the same curvature. This is why “anchor it to modern data” must specify both value and derivative, with uncertainty.

**Assessment:** simplest to audit and useful as a controlled experiment; a poor choice for an unnamed scientific default. Its computational domain must remain finite, with positive rotation rate and a well-behaved time mapping. Physical error is unknown unless separately assessed.

### 3.2 Historical splines, update editions and implementation tails

Stephenson, Morrison and Hohenkerk (2016) reconstructed ΔT from eclipse and occultation observations and supplied a spline representation. Their long-term parabola is

\[
\Delta T=-320+32.5\left(\frac{y-1825}{100}\right)^2\ {\rm s}.
\]

This is a long-term trend, not the complete historical curve; evaluating the trend near 2000 even gives a negative value while the historical fit is positive. It must not replace the observational spline indiscriminately. [R4]

The 2021 addendum refines the reconstruction. Its supplementary coefficient tables and the distributed updated table provide a distinct edition; the audited table has 58 polynomial intervals spanning −720 to 2019. The table boundary is a computational coordinate, not a promise of equally strong historical evidence at every point. Preserve each source's BCE/year-zero convention rather than silently equating its title with a numerical boundary. [R5, R6]

**Implementation finding:** at upstream Skyfield commit `31a6ed7584cd09b6e48e07546a4b5921e1cd5bb4` (source declares version 1.55), `build_delta_t()` combines `Table-S15.2020.txt`, recent data and the **2016** parabola. It inserts an 800-year ancient-side transition, adjusts the historical/recent join, and constructs a data-dependent future transition before reaching the parabola. This is an identifiable composite, not a unique pure “2021 extrapolation”. Its result can change with the recent table. Skyfield's adoption of the updated historical splines is also documented in its changelog. [R6, R15]

Stellarium offers the historical spline/parabolic option alongside other ΔT algorithms; its documented default is a modified Espenak–Meeus variant. Established software therefore does not use one universal ancient prescription. [R16]

**Assessment:** strongest first historical baseline among these choices. Before implementation, choose explicitly between reproducing a pinned backend composite and evaluating pinned published coefficients with a separately defined continuation. Never interchange those identities.

### 3.3 Espenak–Meeus (2006)

NASA publishes a piecewise polynomial prescription for its Five Millennium Canon, over years −1999 to +3000. For example its early branch is

\[
\Delta T=-20+32\left(\frac{y-1820}{100}\right)^2\ {\rm s},\quad y<-500.
\]

The same parabola appears after 2150; intervening future branches include a transition. Future values on the original page are estimates made from the data available then, not today's measured EOP. The page also specifies a lunar-secular-acceleration correction for the particular lunar ephemeris used by the Canon. Record whether that correction is applied; do not transfer it blindly to DE440/DE441 or apply it twice. [R7]

**Assessment:** compact, established and useful for reproducing a published computation. Plain NASA, modified Stellarium and any other implementation variant require separate identifiers. Evaluability beyond the Canon's advertised span is not observational qualification at J−8000.

### 3.4 IERS observations and predictions

IERS supplies several products. C04 has daily series beginning in 1962; C01 supplies longer, differently sampled historical series. Bulletin B provides final data, whereas Bulletin A contains rapid estimates and roughly one-year predictions. Product flags, epochs and actual row coverage matter more than a generic “IERS” label. None supplies an ancient extrapolation. [R8, R9]

The spin adapter should use UT1 consistently with the admitted time convention. At modern leap boundaries, interpolate a continuous representation such as UT1−TAI rather than smoothing raw UT1−UTC across a one-second jump. Treat pre-1972 UTC conventions separately. Formal tabulated errors must not be converted into a claimed independent daily noise process without their covariance assumptions. [R10]

**Assessment:** retain the existing explicit final-data route for modern work. A composite may select historical or nominal regimes outside it, but that selection is another recorded policy, not IERS extrapolation.

## 4. Numerical comparisons performed for this guide

These are reproducible formula/representation checks, **not independent empirical validation**. Upstream Skyfield source and its bundled NPZ were read through GitHub. A local NumPy calculation evaluated the unmodified spline evaluator with the bundled coefficient table; no full Skyfield or Wenu runtime was installed or exercised. The NPZ SHA-256 was `2d12bd3e789543b78a1f53c8b76ed7fecffdf7e5149cfb6a0aed21a8b3db5ff6`.

### 4.1 Long-term tails

| Scalar formula year y | 2016 historical-family parabola, ΔT seconds | Morrison–Stephenson parabola used in NASA outer branches, seconds | Difference | Rotation-angle difference |
|---|---:|---:|---:|---:|
| −2000 | 47,229.53 | 46,675.68 | 553.85 s | 2.31° |
| −8000 | 313,404.53 | 308,563.68 | 4,840.85 s | 20.23° |

The second row is an explicit mathematical extension outside NASA's advertised Canon interval. Neither difference is a measured error or confidence interval. Values are for the formulas' scalar `y`; they are **not** a conversion of Wenu's Julian TCB epoch labels J−2000/J−8000 into calendar years. [R4, R7]

### 4.2 Historical representations

| Scalar y | Updated bundled historical spline, seconds | NASA piecewise prescription, seconds |
|---|---:|---:|
| 0 | 10,441.313 | 10,583.600 |
| 1000 | 1,650.393 | 1,574.200 |
| 2000 | 63.809 | 63.860 |

The NASA column uses the relevant piecewise branch, not its outer parabola. No lunar correction was applied. The spline column is the raw updated table, not Skyfield's modern-data composite. A future implementation must additionally follow each model's exact definition of decimal year and calendar. [R6, R7]

## 5. Proposed modular contract

This section is a design recommendation, not an existing Wenu API or an adopted package boundary. Reuse current time/resource/observer owners; do not introduce a parallel chart pipeline.

### 5.1 Responsibilities

| Responsibility | Input and output |
|---|---|
| Chronology/time admission | Original calendar/date uncertainty → explicit split-JD TT, plus admitted TCB/TDB conversions as required |
| Rotation provider | TT + immutable model selection → split-JD UT1, ΔT and a rotation receipt |
| Axis-orientation provider | TT + admitted precession/nutation policy → orientation and its own receipt |
| Polar-motion provider | Event + selected EOP/nominal policy → xp/yp and provenance; unavailable observations remain unavailable |
| Ephemeris provider | Explicit TDB event → geometric Earth/Sun/body states and independent coverage |
| Observer realization | Compose the compatible inputs, site and declared corrections once |
| Chart consumer | Consume returned positions and receipts; no embedded ΔT formulas or provider fallbacks |

A conceptual interface is `rotation.evaluate(tt, selection) -> RotationResult`. It must be pure with respect to numerical evaluation; acquisition and local-resource verification occur explicitly outside rendering.

### 5.2 Selection must identify more than a model name

Use a small explicit allowlist of adapters rather than arbitrary imports or evaluated configuration expressions. Identifiers considered in the study; Espenak--Meeus is now a candidate, the others remain **proposed**:

- `nominal-quadratic/1`, with an explicit definition of all coefficients and epoch coordinate.
- `historical-spline-2020/1`, pinned coefficient edition; continuation selected separately.
- `skyfield-deltat-composite/1`, pinned backend, historical table, recent table and splice algorithm.
- `espenak-meeus-2006/1`, with an explicit lunar-correction policy.
- `iers-final/1`, naming the product/edition and exact local resource digests.

If future automatic selection is offered, version the selector itself: its precedence, boundaries and every constituent are part of the model identity. It must report the effective adapter for each request. A backend upgrade must not silently change an existing research result.

### 5.3 Required result and provenance

Return immutable, detached records containing:

1. Input TT and output UT1 as two-part Julian dates; ΔT in seconds; numerical precision/rounding information.
2. Scientific family, coefficient edition, implementation/backend version, code identity, resource hashes and parameter values.
3. Effective regime: `measured-final`, `rapid`, `predicted`, `historical-fit`, `transition`, `extrapolated` or `nominal`.
4. Original data coverage, the model's admitted evaluation domain, and any separately qualified domain. These are different fields.
5. Extrapolation and join identities; any source convention or ephemeris-related adjustment.
6. Separate numerical, measurement and model-error channels. Unsupported uncertainty is null/unknown, never zero. Model differences are scenarios, not automatically statistical confidence intervals.

An optional rate result needs its derivative convention and units. Prefer tabulated LOD where admitted; do not manufacture a trustworthy acceleration by differentiating noisy daily observations. A derivative is optional, not required merely to render a chart.

### 5.4 Prevent likely integration surprises

- **One event throughout:** the same admitted UT1/TT must reach every layer and backend. Do not supply ΔT to Skyfield while allowing Astropy independently to fetch or infer a different UT1.
- **No global mutation:** per-request or process-owned immutable context; no monkeypatch of a shared timescale. If a backend cannot honor the input, refuse.
- **Explicit extrapolation:** out-of-coverage refuses unless the selected named continuation covers the target. No silent clamping, zero ΔT, last-value reuse or provider substitution.
- **Join behavior is scientific behavior:** document value/rate continuity, any deliberate discontinuity and the transition interval. Do not silently “improve” published formulas by smoothing them.
- **Time mapping must remain invertible:** require increasing UT1 with increasing TT across the admitted domain. ΔT itself need not increase. An eventual UT1→TT inverse needs bounded root solving across declared segments, not a relabelled JD.
- **Leap/calendar discipline:** signed years/year zero, calendar cutover, day origin and decimal-year formula are explicit. Never collapse a large ancient JD to one float before subtracting seconds.
- **Complete observer contract:** choosing ΔT cannot silently choose nutation, polar motion, a site-evolution model, refraction or a Solar System ephemeris.
- **Caches and workers:** bind cached geometry and worker descriptors to the whole scientific selection and exact resources. Reconstruct and verify per process; do not pickle live providers.
- **Reproducibility:** explicit offline data refresh creates a new identity; old pinned research products remain loadable. Reviewed licensing/acquisition rules precede any redistribution of coefficients or data.

## 6. Focused acceptance for the first working version

1. Reference values for each admitted branch; exact endpoint and immediately adjacent-event cases; signed-year and time-scale checks.
2. Exact receipt identity and deterministic cold/reloaded/worker behavior; hash mismatch and missing-resource refusal.
3. Same TT with two deliberately different model selections must change UT1 and the horizon geometry as predicted, while preserving stellar source identity. This detects a hidden backend override.
4. Numerical time/angle sensitivity against an independent analytic check. For explicit matrices, retain the existing convention and independent transformation checks.
5. Retained modern measured-reference comparison and ancient end-to-end specimens, initially including the existing J−2000/J−8000 material where all other required models are admitted.
6. Preserve the modern stellar population and measured inputs. A missing radial velocity must not silently remove an otherwise usable angular star merely because a new observer composition favors full Cartesian rows.
7. Record omitted corrections explicitly. A nominal zero-polar-motion or vacuum policy is allowed only as a declared model assumption, not as invented ancient measurements.

These are proposed checks to scope against existing owners. They are not a demand to complete historical fitting, atmospheric research or the entire covariance feature before providing a working chart.

## 7. Discussion digest and scientific qualifications

This is an edited synopsis of the dialogue, not a verbatim transcript.

**Ephemeris snapshots.** The question was whether an ancient stellar catalogue should have a parallel ephemeris product. We distinguished efficient local SPK evaluation from full-catalogue stellar realization. Exact Earth/Sun snapshots already exist; a stellar reuse window does not apply to an orbit. [R3, R17]

**Rotation uncertainty.** Modern rate measurements are precise, but past spin phase depends on the integrated history. A formal secular-slope error is not a complete ancient-phase uncertainty. Published historical observations constrain some epochs directly; very early predictions depend on model assumptions. Older NASA uncertainty tables are useful for scale, not a universal error prescription for every implementation. [R14]

**Tides and glacial adjustment.** Lunar braking explains the dominant secular slowdown; net observations also include other processes. The sign of local uplift alone is insufficient: the axial moment depends on distance from the spin axis. Present post-glacial mantle redistribution can accelerate rotation, whereas pole-to-equator redistribution of meltwater tends to slow it. A 2024 study discusses this budget and its limitations. [R12]

**Large earthquakes.** JPL's widely reported preliminary estimates were day shortenings of 1.26 μs for Chile 2010 and 1.8 μs for Japan 2011. These were model-derived, not direct isolated measurements of the steps. They represent abrupt redistribution, unlike a continuing tidal torque. [R13]

**The proposed random walk.** At 10 independent zero-mean permanent kicks per century, 10,000 years contains an expected 1,000 events. For RMS day-length kick `q`, endpoint LOD uncertainty is `q√N`; integrated phase has clock uncertainty `q√N T_days/√3`. For `q=1.8 μs`, this is about 57 μs in final LOD and 120 seconds/0.50° in accumulated phase. For `q=5 μs`, the corresponding phase is about 333 seconds/1.39°. These are our calculations under an illustrative stochastic assumption, not a measured earthquake budget. A nonzero mean adds drift; integrating a mean 1 μs shortening per event gives about 7.6° over the same interval. Do not add this speculative uncertainty to an empirical reconstruction automatically: that can double-count processes already represented.

**User priority.** Obtain a functioning chart soon, with a well-defined baseline even if its ancient physical phase is wrong. Investigating departures from observations comes later. Model selection should remain possible. The discussion first proposed a constant-deceleration timeline, then favored examining established prescriptions before adopting that simplification.

**Original recommendation, superseded by the explicit selection above.** The study initially proposed one pinned composite or one published spline plus explicit continuation. Keep the custom quadratic available as a later controlled alternative. The IERS route remains the modern measured reference. Future observation-fitting can supply a versioned residual on top of a named baseline, with independent inputs and provenance; it is not required for initial charting.

## 8. Decisions still needed before runtime implementation

- Espenak--Meeus is now selected as the first nominal numerical owner. Published historical splines and the pinned Skyfield composite remain future adapter choices.
- Specify the finite initial date domain and the exact distant continuation. A formula's ability to return a number is insufficient to admit every epoch.
- Define axis/nutation and polar-motion assumptions compatible with that domain, plus the existing site/chronology/ephemeris interfaces.
- Record this bounded K4b.08 selection in the authoritative roadmap before runtime changes. Reconcile PR #365 acceptance there when that documentation is next updated; the merged snapshot still has pre-acceptance candidate wording.

This guide does not choose those details on the user's behalf. It supplies the comparison and contract needed to choose them without hidden defaults.

## References and inspection record

Sources checked on 30 October 2026. Mutable upstream links are supplemented with pinned identities where available. The previous project synthesis was read as context; scientific claims below are grounded in the cited primary sources and inspected code.

- **[R1] Wenu ordinary observer:** [observer.py at inspected baseline](https://github.com/fselman/wenu/blob/99d8414494b3ff180b4be6ad37640c30921fc26a/src/wenu/observer.py).
- **[R2] Wenu explicit reception:** [astrometric_observation.py](https://github.com/fselman/wenu/blob/99d8414494b3ff180b4be6ad37640c30921fc26a/src/wenu/astrometric_observation.py); [astrometric_coordinates.py](https://github.com/fselman/wenu/blob/99d8414494b3ff180b4be6ad37640c30921fc26a/src/wenu/astrometric_coordinates.py).
- **[R3] Wenu scope/status:** [roadmap at main 99d84144](https://github.com/fselman/wenu/blob/99d8414494b3ff180b4be6ad37640c30921fc26a/docs/developer/kernel_roadmap_v0.9.5.md); [accepted CLI PR #365](https://github.com/fselman/wenu/pull/365). The acceptance receipt supersedes pending wording in the frozen source document.
- **[R4] Stephenson, F. R., Morrison, L. V. & Hohenkerk, C. Y. (2016).** “Measurement of the Earth's rotation: 720 BC to AD 2015.” Proceedings of the Royal Society A 472, 20160404. [DOI](https://doi.org/10.1098/rspa.2016.0404); [open text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5247521/).
- **[R5] Morrison, L. V., Stephenson, F. R., Hohenkerk, C. Y. & Zawilski, M. (2021).** “Addendum 2020 to ‘Measurement of the Earth's rotation: 720 BC to AD 2015’.” [DOI](https://doi.org/10.1098/rspa.2020.0776); [supplement inspected](https://s3-eu-west-1.amazonaws.com/pstorage-rs-4828782598/26513566/rspa20200776_si_001.pdf). The supplementary coefficient table, not the title's date shorthand, determines exact numerical boundaries.
- **[R6] Skyfield source, pinned upstream commit 31a6ed75:** [timelib.py](https://github.com/skyfielders/python-skyfield/blob/31a6ed7584cd09b6e48e07546a4b5921e1cd5bb4/skyfield/timelib.py); [curvelib.py](https://github.com/skyfielders/python-skyfield/blob/31a6ed7584cd09b6e48e07546a4b5921e1cd5bb4/skyfield/curvelib.py); [bundled delta_t.npz](https://github.com/skyfielders/python-skyfield/blob/31a6ed7584cd09b6e48e07546a4b5921e1cd5bb4/skyfield/data/delta_t.npz). Inspected timelib blob: `5fb7616ea933a56a57c40d15bccb794479f74ef1`; NPZ blob: `db4515fb72841fc01efb6b2794c051b659dbeb34`. This is the upstream study snapshot, not a claim about the version installed on the user's Mac.
- **[R7] Espenak, F. & Meeus, J. (2006).** NASA, Five Millennium Canon of Solar Eclipses; [Polynomial Expressions for ΔT](https://eclipse.gsfc.nasa.gov/SEcat5/deltatpoly.html). Distinguish this documented prescription from later software modifications.
- **[R8] IERS:** [Earth-orientation product catalogue](https://data.iers.org/eop.php). Product edition, frames, flags, sampling and data coverage must be retained.
- **[R9] IERS Rapid Service/Prediction Centre, USNO:** [Bulletin A](https://maia.usno.navy.mil/products/bulletin-a); [ΔT products](https://maia.usno.navy.mil/products/deltaT).
- **[R10] IAU SOFA:** [Time Scale and Calendar Tools](https://www.iausofa.org/s/sofa_ts_c.pdf).
- **[R11] IAU SOFA:** [Tools for Earth Attitude](https://www.iausofa.org/s/sofa_pn_c.pdf), including Earth rotation and celestial/terrestrial composition.
- **[R12] Kiani Shahvandi et al. (2024).** “The increasingly dominant role of climate change on length of day variations.” PNAS 121, e2406930121. [DOI](https://doi.org/10.1073/pnas.2406930121); [open text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11287281/).
- **[R13] NASA/JPL (2011).** [Japan Quake May Have Shortened Earth Days, Moved Axis](https://www.jpl.nasa.gov/news/japan-quake-may-have-shortened-earth-days-moved-axis/). Preliminary calculations and their observational limitations.
- **[R14] NASA eclipse resources:** [Uncertainty in ΔT](https://eclipse.gsfc.nasa.gov/LEcat5/uncertainty.html). Historical summary and explicitly model-dependent distant estimates; not a present universal uncertainty standard.
- **[R15] Skyfield documentation:** [installation/changelog](https://rhodesmill.org/skyfield/installation.html), especially v1.38; [dates and time](https://rhodesmill.org/skyfield/time.html).
- **[R16] Stellarium official API documentation:** [DeltaTAlgorithm enumeration and descriptions](https://stellarium.org/doc/head/classStelCore.html). This mutable page was inspected for evidence of implemented choices, not used as a pinned numerical oracle.
- **[R17] JPL/NAIF:** [DE440/DE441](https://ssd.jpl.nasa.gov/doc/de440_de441.html); [SPK Required Reading](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/spk.html).
- **Project context:** *Wenu — Ancient skies, Earth orientation and Galactic motion*, conversation synthesis dated 28 October 2026, `wenu_ancient_skies_conversation_synthesis.docx`. Its exploratory suggestions remain distinct from adopted roadmap requirements.

### Verification performed for this document

Inspected the named Wenu owners and pinned upstream model representation; evaluated the historical spline and separate illustrative formulas locally; checked arithmetic, Markdown structure and reference identifiers. No models were installed into Wenu, no new observer capability was tested or accepted, and no physical accuracy envelope was established. Source availability and redistribution permissions for a future implementation still require their normal review.
