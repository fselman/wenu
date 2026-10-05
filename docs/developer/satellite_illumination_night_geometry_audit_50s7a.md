# 50S.7A illumination and night-geometry audit

**Status:** Accepted documentation-only scientific and architectural audit

**Audit date:** 2026-09-20

**Accepted by Fernando:** 2026-09-20

**Accepted program base:** `2659b46ea9194a9d2e0e7cdad311a5fc68d51b4c`

**Scope:** Sunlight, solar Earthshine, Moonlight, Lunar-Earthshine,
finite-source shadow transitions, and observer-night geometry. No runtime,
brightness, detector, scheduling, or facility behavior is added by this audit.

## 1. Decision summary

50S.7 must represent four physically different incident-light components:

1. **Sunlight** — direct solar radiation incident on the satellite;
2. **Earthshine** — sunlight reflected by Earth and incident on the satellite;
3. **Moonlight** — sunlight reflected by the Moon and incident on the satellite;
4. **Lunar-Earthshine** — Moonlight reflected by Earth and incident on the
   satellite.

The fourth term follows Caddy et al. (2026), which explicitly defines it as
Moonlight scattered from Earth toward a satellite. It is not the conventional
planetary-science use of “earthshine” for sunlight reflected by Earth onto the
Moon. Wenu must always serialize the unambiguous component key
`lunar_earthshine` and retain the longer definition in human-readable output.

The four components do not all have the same mathematical shape. Sunlight and
Moonlight can be represented as finite-disk source beams. Earthshine and
Lunar-Earthshine are extended directional radiance fields over the Earth disk.
They may not be collapsed to one scalar or one central ray before a later
surface orientation and BRDF are known.

This audit therefore separates three products:

- **illumination geometry** in 50S.7: source directions, distances, angular
  extents, occultation fractions, observer solar altitude, and events;
- **incident-light source fields** in 50S.7: component-resolved radiometric
  inputs with model identity and uncertainty; and
- **apparent brightness** in 50S.8: spacecraft attitude, projected area,
  material BRDF, observer direction, passband, range, and atmospheric
  extinction.

Detector trail contamination remains 50S.9. None of these later results may
change a geometric crossing interval accepted in 50S.5/50S.6.

## 2. As-is assessment

The accepted repository already owns the inputs needed for the first geometry
slice:

- immutable OMM snapshot and orbit-solution identity;
- explicit WGS-72 SGP4 geometric TEME state;
- installed-IERS-A TEME-to-ITRS transformation;
- WGS-84 observer position and vacuum AltAz;
- an installed DE440s-backed `EphemerisStateSource` for Sun, Moon, Earth, and
  other Solar-System states; and
- exact connected crossing intervals and exact local-track evidence.

No current Wenu owner calculates a physical illumination state. SatChecker
illumination flags are provider evidence only. `visibility.py` only partitions
caller-supplied altitude samples and is not a satellite illumination owner.
The accepted offline planning advisory explicitly reports illumination,
brightness, detector effect, and operational disposition as unknown.

The first 50S.7 implementation must compose the accepted state owners. It must
not add another propagator, ephemeris loader, Earth-orientation path, observer
type, crossing solver, chart path, or planning decision.

## 3. Evidence and model maturity

### 3.1 Four-source observational evidence

Caddy et al., *The First Observations of Moonlit Satellites*, arXiv:2609.07057
v1 (2026), defines the four component names used above and reports 147
night-time ISS detections under Moonlight plus Lunar-Earthshine. Its extended
lumos-sat comparison has residuals of `0.03 +/- 0.80 mag`, and its STK study
finds Lunar-Earthshine can dominate nadir-facing components.

This is important motivating evidence, but it is a recent version-1 preprint,
not a frozen numerical standard. Its simplified Moon model, Earth BRDF,
assumed attitudes, missing Rayleigh scattering, and commercial-STK comparison
must not silently become Wenu constants. Wenu may pin a reviewed revision as
validation evidence only after the relevant 50S.7 reflected-source slice is
separately accepted.

Primary link:
<https://arxiv.org/html/2609.07057v1>

Fankhauser, Tyson, and Askari (2023), *Satellite Optical Brightness*, includes
direct sunlight and Earthshine and demonstrates that Earth-reflected light can
materially change predicted satellite brightness. Its spacecraft BRDF and
observer-flux work belongs to 50S.8; its Earth-surface quadrature is relevant
prior art for a 50S.7 source field.

Primary link:
<https://doi.org/10.3847/1538-3881/ace047>

### 3.2 Shadow and occultation precedent

Skyfield `is_sunlit()` is a useful binary external comparison, but its own
documentation calls the result a simple geometric estimate. It does not
supply Wenu's required partial-disk fraction or typed transition sequence.

Primary link:
<https://rhodesmill.org/skyfield/earth-satellites.html#find-when-a-satellite-is-in-sunlight>

NAIF SPICE `gfoclt` distinguishes full, annular, partial, and any occultation
and supports ellipsoidal foreground bodies. It provides an independent
classification/event-search precedent, not a new Wenu runtime dependency.

Primary link:
<https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/gfoclt_c.html>

### 3.3 Night terminology

The U.S. Naval Observatory defines civil, nautical, and astronomical twilight
from the geometric altitude of the Sun's center at `-6`, `-12`, and `-18`
degrees. It also warns that actual light levels depend on atmosphere, clouds,
and horizon conditions. Wenu therefore reports a geometric twilight class,
not a sky-brightness or visibility claim.

Primary link:
<https://aa.usno.navy.mil/faq/RST_defs>

### 3.4 Radiometric references

The IAU 2015 nominal total solar irradiance is exactly `1361 W m-2` as a
nominal conversion constant, not a claim that the instantaneous Sun is
constant. A direct-solar radiometric slice may use it only with explicit
inverse-square distance scaling and a named spectral/bolometric convention.

Primary link:
<https://arxiv.org/abs/1605.09788>

NASA distinguishes total solar irradiance from wavelength-resolved solar
spectral irradiance. Wenu must do the same; a bolometric number cannot be
quietly used as a passband flux.

Primary link:
<https://earth.gsfc.nasa.gov/climate/projects/solar-irradiance/about>

## 4. Scientific decomposition

### 4.1 Geometry state at one instant

A future immutable `SatelliteIlluminationGeometry` should bind:

- satellite identity, snapshot identity, orbit-solution identity, and one UTC
  evaluation instant;
- the accepted SGP4/TEME state and Earth-orientation evidence;
- geocentric satellite position in an explicitly declared frame;
- satellite-to-Sun, satellite-to-Moon, and satellite-to-Earth geometry;
- source and occultor distances and apparent angular extents;
- direct-solar visible-disk fraction in `[0, 1]`;
- a typed solar occultation class;
- observer-centred geometric vacuum Sun altitude;
- observer twilight class; and
- complete ephemeris, Earth-shape, solar-radius, lunar-radius, time-scale,
  and numerical-policy provenance.

The state must be independent of satellite attitude, shape, material,
passband, observer throughput, and detector.

### 4.2 Common instant and frame

All vectors in one geometry state refer to the same physical evaluation
instant. The public instant remains canonical UTC. Ephemeris evaluation may
use TDB internally and Earth rotation may use UT1, but both conversions and
their resources remain provenance.

The accepted satellite route supplies an Earth-centred geometric state. The
accepted installed ephemeris supplies Earth, Sun, and Moon states. A future
composition must explicitly transform them into one common Cartesian frame
before vector subtraction. It may not subtract TEME, ITRS, GCRS, or ICRF
components merely because each is a three-vector.

For near-Earth satellites, no observer-to-satellite light-time correction is
introduced into the physical illumination instant. Solar and lunar source
state conventions must nevertheless be named: geometric same-instant versus
retarded/apparent directions cannot be mixed silently.

### 4.3 Finite-source solar occultation

The Sun is a finite disk. The Earth is not a point and not generally a circle
as seen from a nearby satellite. The accepted first-fidelity target is a
uniform finite solar disk occulted by the vacuum WGS-84 ellipsoid, evaluated
in Earth-fixed geometry at the common instant.

The direct-solar fraction is the unblocked fraction of the modeled solar disk.
It is exactly bounded in `[0, 1]` and has these semantic classes:

- `sunlit`: no modeled solar-disk occultation;
- `penumbra`: partial solar-disk occultation;
- `umbra`: complete solar-disk occultation; and
- `antumbra`: the occultor lies wholly inside the solar disk, if a future
  admitted geometry can physically produce that case.

Contact instants are events, not extra states. Exact equality must be handled
by a declared numerical tolerance and stable side classification. A result
cannot alternate classes under sub-tolerance perturbations.

Uniform-disk fraction is a geometric quantity. Limb-darkened solar irradiance,
atmospheric transmission and refraction around Earth's limb, terrain, clouds,
and wavelength-dependent extinction are separate later models. The first
implementation must say `vacuum` and must not call a geometric umbra an
observational disappearance prediction.

The Moon can rarely occult the Sun as viewed from a satellite. The geometry
contract reserves multiple occultors, but the first bounded implementation
may return a typed `not_evaluated` lunar-occultor status. It may not silently
assert that the lunar contribution is zero.

### 4.4 Shadow-transition events

A future `SatelliteShadowTransition` is found by a bounded event search over
the accepted propagation route, not by interpolating chart samples. It binds:

- the left and right solar-occultation classes;
- transition kind;
- canonical UTC instant;
- a certified time bracket and tolerance;
- orbit, snapshot, ephemeris, Earth-orientation, and shadow-model identity;
  and
- terminal failure if the requested accuracy or evaluation budget is not met.

The solver must detect every class boundary in the requested closed interval,
including two transitions between coarse samples. It uses deterministic
bracketing/refinement and fails closed on discontinuity, non-finite state,
coverage failure, or budget exhaustion.

### 4.5 Observer-night geometry

Observer night is evaluated independently of satellite illumination. The
accepted observer and Earth-orientation policy produce the geometric vacuum
altitude of the Sun's center. The initial classification is:

- `day`: altitude greater than or equal to `0 deg`;
- `civil_twilight`: `-6 deg <= altitude < 0 deg`;
- `nautical_twilight`: `-12 deg <= altitude < -6 deg`;
- `astronomical_twilight`: `-18 deg <= altitude < -12 deg`;
- `astronomical_night`: altitude below `-18 deg`.

This zero-degree day boundary is deliberately geometric and distinct from the
USNO apparent sunrise/sunset convention of `-0.8333 deg`. Both conventions may
be supported only under different explicit policy identifiers.

Observer night does not imply that the satellite is above the horizon, in the
field, illuminated, bright enough, or detectable. Conversely, a satellite may
be geometrically illuminated while the observer is in daylight.

## 5. Incident-light component contract

### 5.1 Shared result vocabulary

Each component result needs:

- one of `evaluated`, `not_evaluated`, `outside_model_domain`, or
  `unavailable_input`;
- a component key and human definition;
- source geometry identity;
- radiometric quantity and units, including wavelength interval or passband;
- source-model identifier, version, parameters, and resource digests;
- value plus uncertainty/bounds where defensible; and
- warnings and explicit exclusions.

Unknown is never encoded as numeric zero. A zero value is valid only when the
accepted model evaluated the component and physically produced zero.

### 5.2 Sunlight

Direct sunlight is a finite-disk beam. A later radiometric slice may combine
the geometric visible fraction with a declared total or spectral solar
irradiance model and Sun-satellite distance. A bolometric output and a
passband output are different types.

### 5.3 Moonlight

Direct Moonlight is reflected sunlight from the lunar disk. Its irradiance
depends on lunar phase, libration, Sun-Moon and Moon-satellite distances,
wavelength, and lunar photometric model. A single illuminated-fraction
multiplier is not sufficient near opposition and is not accepted as a
publication-quality default.

Earth eclipse of the Moon and occultation of the Moon from the satellite must
be represented as model-domain conditions. The recent four-source preprint's
phase-magnitude formula is a useful first-order comparison, not an accepted
Wenu coefficient set.

### 5.4 Earthshine and Lunar-Earthshine

Both Earth-reflected terms are extended fields. A future result must preserve
a deterministic Earth-surface quadrature or equivalent directional field:

- surface-element location and solid angle at the satellite;
- incident-source direction and visibility;
- outgoing direction toward the satellite;
- Earth BRDF/albedo class;
- cloud/atmosphere policy;
- spectral or passband convention; and
- quadrature resolution and convergence evidence.

Solar Earthshine uses Sun-to-Earth-to-satellite paths. Lunar-Earthshine uses
Moon-to-Earth-to-satellite paths. The two may share an Earth-reflection
integrator, but they must retain distinct source identity and separate output
values.

A constant Lambertian Earth can be admitted as an explicitly low-fidelity
validation tier, never as an unqualified physical truth. Spatially varying
land, ocean, cloud, atmosphere, and specular reflection materially affect the
field. Live weather acquisition is outside 50S.7; any map or climatology must
be immutable, licensed, digest-identified, and covered by a separate data
audit.

## 6. Ownership and proposed sequence

The eventual production owner should be
`src/wenu/satellites/illumination.py`. It composes accepted state providers and
owns only illumination geometry, component fields, event search, validation,
and provenance. It must not import chart, renderer, planning, or detector
policy.

The proposed delivery sequence is:

1. **50S.7A — this audit:** terminology, ownership, fidelity tiers, event and
   validation contracts; documentation only.
2. **50S.7B — direct-Sun and observer-night geometry:** immutable geometry
   state, finite uniform solar disk, WGS-84 vacuum Earth occultation, typed
   shadow class, and geometric twilight; no radiometry.
3. **50S.7C — transition solver:** complete bounded shadow-contact search with
   certified brackets and independent event oracles.
4. **50S.7D — direct-source radiometry:** reviewed solar and lunar irradiance
   models with spectral/passband identity and explicit domain limits.
5. **50S.7E — reflected-source fields:** solar Earthshine and
   Lunar-Earthshine through one deterministic extended-Earth quadrature,
   immutable surface policy, uncertainty, and convergence evidence.
6. **50S.7F — component bundle and closure:** all four components preserved
   independently for 50S.8 consumption, plus representative LEO/MEO/GEO and
   night-transition specimens.

Only 50S.7B may be authorized by acceptance of this audit. Every later slice
requires a new as-is check, focused acceptance, and explicit authorization.

## 7. Failure and identity rules

The service fails closed for missing ephemeris coverage, Earth-orientation
coverage, propagation failure, frame mismatch, non-finite geometry,
unsupported source policy, invalid radiometric units, quadrature non-
convergence, or event-budget exhaustion.

Stable typed failure codes must distinguish at least:

- `propagation_failure`;
- `earth_orientation_unavailable`;
- `ephemeris_coverage_unavailable`;
- `frame_mismatch`;
- `non_finite_geometry`;
- `unsupported_shadow_model`;
- `unsupported_source_model`;
- `source_not_evaluated`;
- `quadrature_not_converged`; and
- `transition_search_exhausted`.

Geometry identity includes the satellite/orbit/snapshot identities, instant,
state and ephemeris resources, time and frame policies, Earth/Sun/Moon shape
constants, shadow model, and numerical policy. Incident-field identity adds
component model, spectral/passband convention, immutable data resources,
quadrature policy, and uncertainty policy.

Ordering, serialization, and digests must be deterministic. Model upgrades
change identity. Results from two model versions may be compared but never
silently substituted.

## 8. Validation and acceptance gates

### 8.1 Geometry unit evidence

Construct analytic and high-precision synthetic cases for:

- clear Sun, exterior contact, partial overlap, interior contact, full umbra,
  and an annular geometry;
- exact range endpoints and transition ordering;
- polar, equatorial, and grazing Earth-limb geometry;
- LEO, MEO, GEO, and highly elliptical states;
- observer Sun altitudes on both sides of `0`, `-6`, `-12`, and `-18` degrees;
- UTC/UT1/TDB conversion and ephemeris-coverage boundaries; and
- every typed terminal failure.

### 8.2 Independent comparisons

The first geometry implementation must compare:

- spherical special cases against analytic disk-overlap formulae;
- binary full-light/full-shadow cases against pinned Skyfield results;
- full/partial/annular classification and selected event times against a
  separately executed SPICE or Orekit oracle; and
- observer solar altitude against an independent Astropy/ERFA calculation.

An oracle is never imported into production merely to reproduce itself in a
test. Exact versions, kernels, shape constants, input states, timescales,
tolerances, and output receipts are pinned.

### 8.3 Reflected-source evidence

50S.7E requires quadrature convergence, energy/bound checks, symmetry cases,
land/ocean and cloud-policy sensitivity, and comparison with at least one
independent implementation. The Caddy et al. night ISS observations are a
valuable empirical end-to-end check, but brightness residuals also contain
spacecraft attitude and BRDF error and therefore cannot alone validate the
incident Earth field.

### 8.4 Required specimens

Network-free review specimens must include:

- a pass crossing an Earth-shadow transition;
- a fully sunlit night-observer case;
- a fully shadowed astronomical-night case;
- a partial-solar-disk state;
- a Moonlit/Lunar-Earthshine-relevant full-Moon geometry; and
- a zero/unknown component case proving that unknown is not serialized as
  zero.

Each specimen retains exact inputs, component statuses, model identities,
digests, numerical budgets, and machine-readable values. Plots may explain
the geometry but are not acceptance truth.

## 9. Explicit exclusions

This audit adds no production module, public API, dependency, package data,
network request, chart layer, style, CLI, file protocol, planning adapter, or
facility integration. It does not authorize:

- apparent magnitude or a visibility/detectability claim;
- spacecraft attitude, shape, projected area, or material BRDF;
- glint probability or deterministic flare prediction;
- atmospheric sky brightness, extinction, or refraction around Earth's limb;
- live cloud, albedo, or weather data;
- terrain or local-horizon modeling;
- detector electrons, saturation, persistence, masking, or schedule changes;
- using SatChecker illumination as local scientific truth; or
- changing accepted crossing, report, track, chart, or advisory identities.

## 10. Recommendation and authorization boundary

Adopt this decomposition and begin, only after Fernando's separate scientific
and architectural acceptance, with 50S.7B direct-Sun and observer-night
geometry. That implementation must remain output-neutral and network-free.

Earthshine, Moonlight radiometry, Lunar-Earthshine, component summation,
apparent brightness, detector effects, and observatory action remain
unauthorized. The candidate audit itself authorizes no implementation, merge,
branch deletion, or later milestone.

## 11. Accepted 50S.7A audit and 50S.7B authority

Fernando scientifically and architecturally accepted this documentation-only
audit on 2026-09-20 at candidate revision
`fdf7e005a41a5a4d45200f841e914815d37da870`. The final 206
plugin-disabled current-documentation tests passed in 5.87 seconds; diff,
exact-head, upstream, and clean-working-tree checks also passed.

After this audit is merged, implement only the bounded 50S.7B direct-Sun and
observer-night geometry implementation: immutable output-neutral geometry,
finite uniform-Sun/WGS-84 vacuum Earth occultation, typed shadow state,
geometric observer twilight, complete provenance, and focused offline
validation.

50S.7C and later transition, radiometric, reflected-source, component-bundle,
50S.8 brightness, 50S.9 detector, facility, visibility, and scheduling work
remain unauthorized. This acceptance does not itself authorize implementation
before merge. PR merge and branch deletion still require separate explicit
authorization.
## 12. Candidate 50S.7B implementation record

The unaccepted candidate at branch
`feature/50s7b-direct-sun-night-geometry` implements only the authorized
direct-Sun and observer-night slice. `wenu.satellites.illumination` composes
an accepted `SatelliteTopocentricState` with an injected
`EphemerisStateSource`; it does not propagate, search crossings, find shadow
transitions, render, report, plan, or schedule.

The candidate requests one same-instant geometric Earth-to-Sun state in ICRF
axes, rotates the ICRF/GCRS-aligned geocentric vector into ITRS with the exact
installed-IERS-A evidence already bound to the satellite state, and performs
all subtraction in ITRS. It evaluates a uniform finite solar disk against the
vacuum WGS-84 ellipsoid by deterministic equal-solid-angle ray quadrature.
Successive bounded refinements record their absolute fraction difference and
fail closed with `quadrature_not_converged` when the declared tolerance is
not met.

The immutable result retains the topocentric and ephemeris states, common UTC
instant and ITRS vectors, bounded visible-disk fraction, typed
`sunlit`/`penumbra`/`umbra`/`antumbra` class, geometric vacuum observer
Sun altitude, exact twilight class, explicit model/numerical policy,
provenance, and warnings. Lunar solar occultation is
`not_evaluated`, never numeric zero.

Focused analytic tests cover clear, exterior contact, partial, interior
contact, umbra, annular, polar/equatorial, LEO/MEO/GEO/high-orbit, twilight
boundaries, immutable identity, frame failure, convergence failure, and an
independent Astropy AltAz comparison. The offline
`tools/validate_50s7b_illumination_geometry.py` refuses downloads and is
reserved for installed-DE440 binary comparison with Skyfield plus selected
SPICE ellipsoid classification. Its controlled Mac receipt remains an
acceptance gate.

This candidate does not authorize 50S.7C transition search, radiometry,
Earthshine, Moonlight radiometry, Lunar-Earthshine fields, brightness,
visibility, detector effects, facility integration, or scheduling. Merge and
branch deletion require separate explicit authorization.
### Controlled 50S.7B independent-validation receipt

Fernando ran the offline validator on 2026-09-21 at candidate `51b935f`.
The focused illumination gate first passed all 24 tests in 5.58 seconds. SPICE
independently classified the selected clear, partial, umbra, and annular cases
as `sunlit`, `penumbra`, `umbra`, and `antumbra`; Wenu agreed. The
reported visible fractions were `1.000000000`, `0.567165799`,
`0.000000000`, and `0.593750000`.

The installed ephemeris was model `DE440`, file `de440s.bsp`, SHA-256
`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`.
Against Skyfield `is_sunlit()`, the validator obtained 20 matching
full-light states and 5 matching full-shadow states with no mismatch. The
validator downloaded nothing.

This completes the independent numerical receipt but does not accept the
candidate. Expanded, complete, documentation, diff, exact-head, upstream, and
clean-tree gates remain required before Fernando's separate review.

### Complete 50S.7B candidate gate evidence

Executable candidate `086e7da1` completed the controlled Mac gates on
2026-09-21:

- the expanded satellite/ephemeris/documentation gate passed all 291 tests in
  18.81 seconds;
- the final current-documentation gate passed all 208 tests in 6.47 seconds;
- `git diff --check c68e997777b8a2b1e5faf3bbe100fb4d8c445be8...HEAD`
  was clean;
- the complete plugin-disabled repository suite passed all 2,796 tests in
  233.66 seconds; and
- exact head/upstream equality and a clean working tree were confirmed.

The earlier offline SPICE/Skyfield receipt remains part of this evidence.
These results establish a verified candidate for Fernando's separate
scientific and architectural review. They do not themselves authorize merge,
branch deletion, 50S.7C, or later work.

## 13. Accepted 50S.7B implementation

Fernando scientifically and architecturally accepted the complete bounded
50S.7B implementation on 2026-09-21 at candidate revision
`054ac53a1f2d50aca06c268cfc7ff5fb074c690f`. The accepted evidence comprises the analytic and independent
geometry validation, installed-DE440/Skyfield comparison, 291-test expanded
gate, 2,796-test complete repository gate, clean diff, exact upstream, clean
tree, and final 208-test documentation gate in 4.19 seconds.

The accepted implementation owns only immutable output-neutral direct-Sun and
observer-night geometry: same-instant ITRS composition, a uniform finite solar
disk occulted by the vacuum WGS-84 ellipsoid, bounded adaptive quadrature with
fail-closed convergence, typed solar occultation and twilight states, explicit
lunar `not_evaluated`, complete resource/model identity, provenance, and
warnings.

Acceptance authorizes merge of PR 181 only when Fernando gives a separate
explicit merge instruction. It does not authorize branch deletion. After
merge, only a documentation-first 50S.7C shadow-transition audit is authorized
next. Transition runtime, radiometry, Earthshine, Moonlight radiometry,
Lunar-Earthshine fields, brightness, visibility, detector effects, facility
integration, and scheduling remain unauthorized.

## 14. Candidate 50S.7C shadow-transition audit handoff

The documentation-only 50S.7C candidate is recorded in
`satellite_shadow_transition_audit_50s7c.md`. It refines the reserved event
contract into observer-independent directed class boundaries with continuous
finite-Sun/WGS-84 contact geometry, certified UTC brackets, complete bounded
closed-interval search, fail-closed budgets, deterministic identity, and
independent SPICE/Orekit event evidence.

The accepted visible-fraction quadrature remains the fraction owner and is not
a contact root function. A later implementation would remain in
`satellites/illumination.py`, with only a minimal shared geocentric ITRS seam
in the existing topocentric owner. This candidate adds no runtime and does not
authorize implementation, merge, branch deletion, 50S.7D+, brightness,
visibility, detector, facility, or scheduling work.

## 15. Accepted 50S.7C audit handoff

Fernando accepted the documentation-only 50S.7C transition audit at
`030a6322` on 2026-09-21 after 210 documentation tests passed in 5.81
seconds and repository checks were clean.

After merge, only the bounded transition implementation defined in
`satellite_shadow_transition_audit_50s7c.md` is authorized. It must preserve
the accepted 50S.7B fraction and class meanings while adding continuous
contact geometry, complete bounded search, directed events, certified
brackets, deterministic identity, terminal failure, a minimal shared
geocentric ITRS seam, and independent event validation. 50S.7D+ and every
brightness, visibility, detector, facility, or scheduling use remain
unauthorized. Merge and branch deletion remain separate.

## Candidate 50S.7C shadow-transition implementation handoff

The unaccepted bounded candidate realizes the accepted next slice without
changing 50S.7B visible-fraction or observer-night meaning. Continuous
finite-Sun/WGS-84 contact margins drive one complete bounded search for one
selected record and interval; six adjacent directed events retain certified
UTC brackets, complete identity, resource evidence, and terminal failures.

At executable `69375fab`, 58 focused tests passed in 16.67 seconds. The
no-download SPICE `gfoclt` receipt reproduced full and annular four-contact
sequences, and Skyfield matched 20 full-light plus 5 full-shadow states using
the accepted installed DE440 digest. Complete gates and acceptance remain
pending. 50S.7D+, reflected fields, radiometry, brightness, visibility,
detector, facility, scheduling, and output integration remain unauthorized.

## 16. Accepted 50S.7C shadow-transition implementation handoff

Fernando scientifically and architecturally accepted the complete bounded
50S.7C implementation at
`eaeab6085b52bfed6136d37f3010c2f353e59f53` on 2026-09-21. The accepted
evidence comprises executable `bf877404`, the independent no-download
SPICE/Skyfield receipt, 311 expanded tests, 212 documentation tests, all 2,816
plugin-disabled repository tests, clean diff, exact upstream, clean tree, and
the final 212-test documentation clarification in 4.72 seconds.

Preserve 50S.7B visible-fraction and observer-night meanings while retaining
50S.7C continuous contact geometry, complete bounded search, directed events,
certified brackets, deterministic identity, shared geocentric ITRS evidence,
and fail-closed behavior. PR 183 merge and branch deletion remain separate.
50S.7D+, output attachment, radiometry, reflected fields, brightness,
visibility, detector, facility, and scheduling remain unauthorized.
## 17. Candidate 50S.7D direct-source radiometry handoff

The dedicated documentation-only audit in
`satellite_direct_source_radiometry_audit_50s7d.md` refines the accepted
50S.7 sequence without changing its four-component separation. Direct
Sunlight and Moonlight remain 50S.7D; Earthshine and Lunar-Earthshine remain
50S.7E.

Because the model maturity differs, the candidate proposes only a bounded
50S.7D.1 implementation after separate acceptance: IAU 2015 nominal
bolometric normal-plane Sunlight, inverse-square Sun-satellite distance
scaling, and the accepted uniform-disk visible fraction. Spectral TSIS-1
Sunlight and ROLO/LIME-class Moonlight remain later separately audited slices.

The candidate authorizes no runtime. 50S.7D.1 implementation, 50S.7D.2+,
50S.7E+, output integration, brightness, visibility, detector, facility,
scheduling, merge, and branch deletion remain unauthorized.

## 18. Accepted 50S.7D direct-source radiometry handoff

Fernando scientifically and architecturally accepted the documentation-only
50S.7D audit at exact candidate
`362199d04bd917741a8be88f20608967af75530e` on 2026-09-21. All 214
plugin-disabled current-documentation tests passed in 7.00 seconds, and
repository checks were clean.

After merge, implement only bounded 50S.7D.1 IAU-nominal bolometric
normal-plane Sunlight, inverse-square Sun-satellite distance scaling, and
composition with the accepted uniform-disk visible fraction in the existing
illumination owner. Direct Sunlight and Moonlight remain distinct 50S.7D
components; Earthshine and Lunar-Earthshine remain 50S.7E.

50S.7D.2+ spectral and lunar models, 50S.7E+, component bundling, outputs,
spacecraft response, brightness, visibility, detector, facility, scheduling,
and unrelated work remain unauthorized. PR 184 merge and branch deletion
remain separate explicit decisions.

## 19. Candidate 50S.7D.1 implementation handoff

Executable `4b5f8e6925f88df38a2923c057f4d039328e3d2b` implements the first
accepted radiometric composition downstream of this geometry: IAU-nominal
bolometric normal-plane direct Sunlight, inverse-square distance scaling, and
the already-converged uniform-disk visible fraction. It preserves all geometry
identity and does not modify occultation or twilight behavior.

Physical/model uncertainty stays `not_evaluated`; the inherited quadrature
difference remains numerical convergence evidence only. The candidate is
unaccepted and adds no spectral Sunlight, Moonlight, reflected fields,
spacecraft response, brightness, visibility, detector, output, facility, or
scheduling behavior.

## 20. Verified candidate 50S.7D.1 implementation handoff

Exact head `5bf5d52e81670f1a69af0476283195d12a3119bc` passed the independent
installed-resource receipt for sunlit, penumbral, and umbral LEO/MEO/GEO
geometry with zero irradiance residuals, 308 expanded tests in 24.79 seconds,
and all 2,832 plugin-disabled tests in 236.81 seconds. Geometry identity,
occultation state, and convergence evidence remain unchanged and upstream.

This is verification evidence only. The implementation remains unaccepted;
merge, branch deletion, spectral Sunlight, Moonlight, reflected fields,
spacecraft response, brightness, visibility, detector, output, facility, and
scheduling remain unauthorized.

## 21. Accepted 50S.7D.1 implementation handoff

Fernando scientifically and architecturally accepted exact verified candidate
`f974b9996d2708ee0f2db7c747e45c481a457bb9` on 2026-09-22. The accepted
consumer preserves the full 50S.7A geometry and composes only same-instant
direct-Sun bolometric normal-plane irradiance.

The zero-residual nine-case receipt, 308 expanded tests, complete 2,832-test
suite, and final 223 documentation/package-boundary tests passed. The
acceptance does not authorize 50S.7D.2+, merge, branch deletion, or any later
illumination/output behavior.

## 22. Candidate 50S.7D.2 spectral handoff

The proposed TSIS-1 HSRS v2 evaluator consumes complete accepted 50S.7A
geometry and applies the accepted distance and uniform-disk fraction without
recomputing either. Wavelength-dependent limb darkening remains unevaluated.
This documentation-only handoff authorizes no runtime or 50S.7D.3+ work.

## 23. Accepted 50S.7D.2 spectral handoff

Fernando accepted exact documentation-only candidate
`0a1a6a681bc3e9b4dd562a0b0b57ae48ff5caefe` on 2026-09-22. After audit
merge, the bounded spectral evaluator must consume accepted 50S.7A geometry
without recomputing distance or occultation, preserve achromatic uniform-disk
scaling as an explicit approximation, and use the external installed TSIS-1
HSRS v2 resource. This acceptance adds no runtime and does not authorize
50S.7D.3 Moonlight.
