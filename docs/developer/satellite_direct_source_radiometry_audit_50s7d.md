# 50S.7D direct-source radiometry audit

**Status:** Candidate documentation-only scientific and architectural audit

**Audit date:** 2026-09-21

**As-is base:** `17a8dd37ab3c361084c240cc68f9f8c3a25e5e3d`

**Scope:** Direct Sunlight and direct Moonlight incident radiometry, with only
a bounded solar-first 50S.7D.1 implementation proposed after separate
acceptance. This audit authorizes no runtime, resource acquisition, dependency,
brightness, detector, scheduling, facility, report, chart, or CLI behavior.

## 1. Decision summary

50S.7D is the incident-radiometry bridge between accepted illumination
geometry and later spacecraft brightness. It answers how much direct-source
radiant power reaches a unit area normal to the incoming beam at the
satellite. It does not answer how much power a spacecraft surface intercepts,
reflects toward an observer, or deposits in a detector.

The complete 50S.7D scientific responsibility contains two direct components:

1. **Sunlight:** Sun to satellite.
2. **Moonlight:** Sun to Moon to satellite.

The sources have different model maturity. Direct-Sun bolometric irradiance
admits a small reproducible first slice. Publication-quality Moonlight needs a
reviewed phase/libration- and wavelength-dependent lunar model plus immutable
coefficient or tool resources. A lunar illuminated-fraction multiplier is not
an acceptable substitute.

The proposed delivery sequence is therefore:

1. **50S.7D.1 — direct-Sun bolometric irradiance:** IAU 2015 nominal total
   solar irradiance, inverse-square Sun-satellite distance scaling, and the
   accepted uniform-disk visible fraction.
2. **50S.7D.2 — spectral direct-Sun irradiance:** an immutable,
   digest-identified TSIS-1 HSRS v2 resource and explicit wavelength
   integration contract.
3. **50S.7D.3 — direct-Moonlight irradiance:** a separately accepted
   reproducible lunar spectral/passband model with phase, libration, distance,
   domain, uncertainty, and licensing evidence.
4. **50S.7D.4 — direct-source closure:** stable two-component interchange for
   later 50S.7F bundling and 50S.8 consumption.

Acceptance of this audit would authorize only the bounded 50S.7D.1
implementation after merge. Every later slice remains separately reviewed.

## 2. As-is assessment

Accepted 50S.7B already supplies one immutable
`SatelliteIlluminationGeometry` at one canonical UTC instant, including:

- exact satellite, orbit, snapshot, ephemeris, and Earth-orientation identity;
- same-instant satellite-to-Sun geometry;
- Sun-satellite distance;
- a converged uniform-solar-disk visible fraction in `[0, 1]`;
- typed `sunlit`, `penumbra`, `umbra`, and `antumbra` state;
- explicit lunar solar-occultor `not_evaluated`; and
- complete shadow-policy provenance and warnings.

Accepted 50S.7C adds observer-independent directed shadow-transition events.
It does not alter the ordinary instantaneous geometry or turn event brackets
into radiometric samples.

No current production owner calculates incident irradiance. No existing
crossing, track, report, chart, CLI, or planning result carries illumination
radiometry. The accepted `satellites/illumination.py` owner is therefore the
closest bounded owner for the first scalar direct-Sun composition. The existing
`tests/test_satellite_illumination.py` remains the closest enduring
scientific and failure-boundary test owner.

The as-is implementation already defines the IAU nominal astronomical unit,
nominal solar radius, and accepted finite-disk geometry. 50S.7D.1 requires no
new propagator, ephemeris provider, Earth-orientation path, data resource,
package dependency, network access, renderer, exporter, or output pipeline.

## 3. Primary radiometric evidence

### 3.1 Nominal bolometric Sun

IAU 2015 Resolution B3 defines the nominal total solar irradiance
`S_sun^N = 1361 W m-2` at exactly 1 au. It is an exact nominal conversion
constant representing mean total electromagnetic energy integrated over all
wavelengths. The resolution explains that the underlying cycle-23 mean was
`1361 +/- 1 W m-2` at two sigma and that physical TSI varies at roughly the
`0.08%` level. Exact nominal identity must therefore not be described as
zero physical or model uncertainty.

Primary source:
<https://www.iau.org/common/Uploaded%20files/IAUGA2015-Resolution-B3-recommended-nominal-conversion.pdf>

### 3.2 Spectral Sun

TSIS-1 HSRS v2 is the current CEOS-WGCV-recommended solar spectral irradiance
reference. The observational composite spans `0.202-2.730 um`, contains more
than 97% of TSI, and publishes wavelength-dependent uncertainty. Its full
extension spans `0.115-200 um` and nearly all TSI, partly using observations
and partly model knowledge outside the measured range.

The spectrum is appropriate future 50S.7D.2 evidence, but it is not equivalent
to the IAU bolometric nominal constant. Before runtime use Wenu must freeze the
exact dataset DOI, byte digest, wavelength and irradiance units, bin meaning,
integration convention, redistribution status, and admitted wavelength
domain.

Primary sources:

- <https://doi.org/10.1029/2022EA002637>
- <https://doi.org/10.25980/ta3f-7h90>
- <https://calvalportal.ceos.org/home/-/asset_publisher/1aO8bapeanp9/content/tsis-1-hsrs-solar-irradiance-reference-spectrum>

### 3.3 Direct Moonlight

Kieffer and Stone's ROLO work models disk-integrated lunar spectral irradiance
with explicit phase and libration dependence. It established the durable
model form but reported several-percent absolute-scale uncertainty and has
multiple operational implementations.

Primary source:
<https://doi.org/10.1086/430185>

ESA's 2024 LIME model uses SI-traceable measurements and a modified ROLO form,
reports output uncertainty below 2% at coverage factor `k=2`, and uses the
TSIS-1 spectrum. It also reports visible/near-infrared outputs 3%-5% above
GIRO/ROLO, incomplete selenographic coverage, band-specific coefficients, and
controlled toolbox/code availability. These are material model and resource
questions, not details that may be silently guessed.

Primary source:
<https://doi.org/10.5194/acp-24-3649-2024>

The 2026 Caddy et al. Moonlit-satellite observations remain valuable later
end-to-end evidence, but their residuals also include spacecraft attitude,
surface BRDF, observer geometry, atmosphere, and detector effects. They cannot
alone validate incident Moonlight.

Primary source:
<https://arxiv.org/html/2609.07057v1>

The audit therefore reserves Moonlight but authorizes no lunar coefficient,
toolbox, phase law, spectral interpolation, or numerical output.

## 4. Bounded 50S.7D.1 physical model

### 4.1 Quantity and reference surface

The result is **bolometric normal-plane irradiance** in `W m-2`: radiant
power per unit area on an abstract plane perpendicular to the incoming
Sunlight beam at the satellite. It is not irradiance on a spacecraft panel.
Surface normal, attitude, projected area, self-shadowing, material response,
and BRDF remain 50S.8.

The quantity is bolometric. It has no wavelength interval or photometric
passband. Code and documentation must not label it `V`, `r`, visible,
spectral, monochromatic, or passband irradiance.

### 4.2 Equations

For accepted Sun-satellite distance `r`, exact astronomical unit `au`,
IAU nominal irradiance `S_sun^N`, and accepted uniform-disk visible fraction
`f_visible`:

```text
E_clear    = S_sun^N * (au / r)^2
E_incident = f_visible * E_clear
```

where `S_sun^N = 1361 W m-2`.

`E_clear` is the unocculted model value at the satellite.
`E_incident` is the direct-Sun value remaining after the accepted vacuum
WGS-84 occultation model. The multiplication is valid only because 50S.7B
explicitly models a uniform-radiance solar disk. A later limb-darkened or
spectral disk requires a new model and identity.

Both values are finite and non-negative. `E_incident <= E_clear`. A numeric
zero is valid only after successful evaluation with `f_visible = 0`.
Unknown is never numeric zero. Unavailable, unsupported, and not-evaluated states are likewise never encoded as zero.

### 4.3 Nominal value and uncertainty language

The policy must call 1361 W m-2 **nominal**, not measured at the requested
instant. Its exact stored decimal is exact only as the IAU nominal convention.
The first slice does not model solar-cycle or short-timescale variability and
must not attach a zero physical uncertainty.

The result retains the accepted finite-disk convergence evidence. It may expose
the corresponding coarse/fine irradiance difference as numerical convergence
evidence, but it must not relabel that difference as total physical
uncertainty. Physical/model uncertainty status remains explicitly
`not_evaluated` with a warning that the nominal model omits solar variability
and limb darkening.

## 5. Proposed immutable contract

A later accepted 50S.7D.1 implementation may add only:

- `DirectSolarIrradiancePolicy`;
- `DirectSolarIrradiance`; and
- `DirectSolarIrradianceEvaluator`.

The policy binds:

- model identifier
  `iau-2015-nominal-tsi-uniform-disk-bolometric-v1`;
- exact nominal `1361 W m-2`;
- exact IAU astronomical unit already used by Wenu;
- quantity kind `bolometric_normal_plane_irradiance`;
- accepted uniform-disk occultation compatibility;
- uncertainty status `not_evaluated`; and
- source citations and exclusions.

The result binds:

- component key `sunlight` and status `evaluated`;
- canonical UTC instant and exact geometry identity;
- satellite, orbit, snapshot, ephemeris, EOP, and shadow-policy identity;
- Sun-satellite distance in kilometres and astronomical units;
- occultation class and visible-disk fraction;
- `unocculted_normal_irradiance_w_m2`;
- `incident_normal_irradiance_w_m2`;
- numerical convergence evidence;
- policy/model identity, provenance, warnings, and deterministic identity.

The evaluator consumes one accepted `SatelliteIlluminationGeometry`. It does
not propagate an orbit, query an ephemeris, recompute an occultation fraction,
or accept an observer, surface normal, passband, instrument, or crossing.

Unsupported geometry/model combinations fail closed through the existing
illumination failure boundary with stable `unsupported_source_model`,
`source_not_evaluated`, `non_finite_geometry`, or a narrowly added invalid
radiometry-input code only if implementation evidence proves it necessary.

## 6. Moonlight and spectral reservations

50S.7D.1 must expose no numeric Moonlight field. Existing lunar
`not_evaluated` meaning remains authoritative. A future component bundle
must preserve that status rather than synthesize zero.

50S.7D.2 may be proposed only after an immutable TSIS-1 HSRS v2 resource audit.
It must retain the native wavelength grid and units, forbid silent
interpolation or extrapolation, define bin integration and passband weighting,
and distinguish energy-weighted from photon-weighted quantities.

50S.7D.3 may be proposed only after selecting a reproducible lunar model and
freezing all coefficients/resources. It must define phase-angle sign,
selenographic Sun/observer longitude and latitude, Sun-Moon and
Moon-satellite distances, spectral bands, eclipse/occultation domain,
interpolation, uncertainty, provenance, and licensing. ROLO, GIRO, LIME, or a
later model may be compared; none is silently accepted by this audit.

## 7. Ownership and dependencies

The bounded scalar 50S.7D.1 evaluator remains in
`src/wenu/satellites/illumination.py` because it composes the geometry type
owned there, has the same evaluation lifecycle, introduces no independent
resource, and changes for the same direct-Sun model reason. File size alone
does not justify a new module.

`tests/test_satellite_illumination.py` remains the closest durable owner for
formula, identity, failure, zero-versus-unknown, and composition evidence.
No new production or test file is proposed for 50S.7D.1.

A later spectral or lunar resource has a distinct data lifecycle and may
justify a separate incident-radiometry owner, but only after a source-tree and
resource-admission audit. This document does not authorize that module.

No new package dependency, installed data resource, download, provider call,
cache, CLI, schema, report, chart, planning adapter, renderer, or exporter is
authorized.

## 8. Coordinate and time review

50S.7D.1 introduces no new vector, frame transform, time scale, or observer.
It consumes the same-instant Sun-satellite distance and occultation fraction
already present in accepted geometry. UTC remains result identity; TDB
ephemeris and UT1/EOP evidence remain inherited provenance.

The coordinate-system guide was reviewed and remains current. Irradiance is a
scalar physical quantity attached to explicit geometry identity, not a
coordinate status. The normal-plane convention is a radiometric reference
surface, not a spacecraft frame.

## 9. Validation and acceptance gates

### 9.1 Analytic contracts

Focused tests must cover:

- `1361 W m-2` at exactly 1 au with `f_visible = 1`;
- inverse-square ratios at `0.5`, `1`, and `2 au`;
- fractions `0`, `0.25`, and `1`;
- `E_incident <= E_clear` and non-negative finite outputs;
- exact zero only for an evaluated zero visible fraction;
- clear separation of bolometric and passband/spectral requests;
- nominal-exact versus physical-uncertainty language;
- deterministic identity and changes under policy/geometry changes;
- inherited convergence evidence without a false uncertainty claim;
- rejection of invalid, non-finite, unsupported, or incompatible geometry;
  and
- absence of observer, surface, BRDF, magnitude, detector, and output fields.

### 9.2 Independent recomputation

A validator or focused independent calculation must recompute the formula from
the IAU source constant and retained geometry values without calling the
production evaluator. It must include representative LEO, MEO, and GEO
sunlit, penumbral, and umbral states using the installed no-download resource
chain.

The independent receipt records the IAU source identifier, exact constant,
astronomical unit, accepted geometry identity, input distances and fractions,
expected and actual values, absolute residuals, versions, and absence of
network access. Agreement validates implementation of the declared nominal
model; it does not validate instantaneous solar variability.

### 9.3 Repository gate

Before implementation acceptance require:

- focused illumination and ephemeris tests;
- the independent offline receipt;
- current-documentation and package-boundary tests;
- the complete plugin-disabled repository suite;
- clean diff, exact head/upstream equality, and clean worktree; and
- Fernando's separate scientific review of names, units, equations, warnings,
  specimens, and scope.

## 10. Explicit non-goals

This audit and the proposed 50S.7D.1 slice add no:

- spectral or passband irradiance;
- direct Moonlight number or lunar phase law;
- solar variability or limb darkening;
- lunar eclipse or satellite-view lunar occultation model;
- solar Earthshine or Lunar-Earthshine;
- spacecraft attitude, surface normal, projected area, self-shadowing, BRDF,
  glint, polarization, or thermal response;
- observer-directed radiance, flux, magnitude, atmospheric extinction,
  visibility, or detectability;
- crossing filtering, report, chart, CLI, planning, facility, or scheduling
  integration;
- detector, trail, saturation, exposure, or signal-to-noise effect; or
- 50S.7E, 50S.7F, 50S.8, 50S.9, or 50S.10 behavior.

## 11. Acceptance boundary

This candidate is documentation only and authorizes no runtime. Fernando's
separate scientific and architectural acceptance is required before any
50S.7D.1 implementation.

If accepted and merged, implement only the bounded direct-Sun bolometric
normal-plane irradiance contract above in the existing illumination owner with
focused offline evidence. Do not begin spectral Sunlight, Moonlight,
Earth-reflected fields, component bundling, apparent brightness, detector
effects, output integration, facility behavior, scheduling, or unrelated
refactoring. Audit merge and branch deletion remain separate explicit
decisions.

## 12. Accepted 50S.7D audit and implementation authority

Fernando scientifically and architecturally accepted this documentation-only
audit on 2026-09-21 at exact candidate revision
`362199d04bd917741a8be88f20608967af75530e`. The complete
current-documentation gate passed all 214 plugin-disabled tests in 7.00
seconds. The branch diff check, exact local/upstream equality, and clean
working tree also passed.

After this audit is merged, implement only bounded 50S.7D.1 direct-Sun
bolometric normal-plane irradiance in
`src/wenu/satellites/illumination.py`: immutable policy/result/evaluator
contracts, the exact IAU 2015 nominal `1361 W m-2` value at 1 au,
inverse-square Sun-satellite distance scaling, composition with the accepted
uniform-disk visible fraction, explicit physical/model uncertainty
`not_evaluated`, deterministic identity and provenance, focused tests in the
existing illumination test owner, and offline independent recomputation.

50S.7D.2 spectral Sunlight, 50S.7D.3 Moonlight, 50S.7D.4 closure, 50S.7E
reflected fields, 50S.7F bundling, 50S.8 brightness, 50S.9 detector effects,
outputs, visibility, facilities, scheduling, and unrelated refactoring remain
unauthorized. Acceptance does not authorize PR 184 merge or branch deletion;
both remain separate explicit decisions.

## 13. Candidate 50S.7D.1 implementation

Implementation began from exact merged audit base
`664b6bc849776b4769ce8cc223f2c7dce8b8cc53`. Executable
`4b5f8e6925f88df38a2923c057f4d039328e3d2b` adds only the accepted immutable
`DirectSolarIrradiancePolicy`, `DirectSolarIrradiance`, and
`DirectSolarIrradianceEvaluator` contracts in the existing illumination
owner, intentional package exports, focused existing-owner tests, and one
offline independent-recomputation tool.

The evaluator consumes one accepted `SatelliteIlluminationGeometry`, applies
the exact nominal `1361 W m-2` value at 1 au, inverse-square distance scaling,
and the retained visible-disk fraction, and returns clear and incident
bolometric normal-plane irradiance. It preserves complete geometry and model
identity, explicit `not_evaluated` physical/model uncertainty, numerical
convergence evidence, provenance, warnings, and fail-closed compatibility.

The focused illumination/ephemeris gate passed 86 tests in 9.80 seconds. The
installed-resource independent receipt, Mac complete suite, documentation and
package-boundary gates, exact-upstream/clean-tree checks, and Fernando's
scientific and architectural acceptance remain pending. 50S.7D.2+, 50S.7E+,
outputs, brightness, visibility, detector, facility, scheduling, merge, and
branch deletion remain unauthorized.

## 14. Verified candidate 50S.7D.1 implementation

Fernando's Mac verified exact feature-branch head
`5bf5d52e81670f1a69af0476283195d12a3119bc`. The independent offline
receipt used installed DE440
`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`
and installed IERS evidence with `network_access=false`. It covered sunlit,
penumbral, and umbral LEO, MEO, and GEO states. Every independently computed
clear and incident irradiance residual was `0.000e+00`; numeric zero occurred
only for evaluated umbra. Receipt SHA-256 was
`43037267cd841232dcffca05797a2d55dce3d90b9caf8b84fbf785b19129fc73`.

The combined illumination, ephemeris, documentation, and package-boundary gate
passed all 308 tests in 24.79 seconds. The complete plugin-disabled repository
suite passed all 2,832 tests in 236.81 seconds. Diff, exact-head/upstream, and
clean-tree checks passed.

The candidate is verified but not scientifically or architecturally accepted.
Fernando's separate review remains required. Merge, branch deletion,
50S.7D.2+, 50S.7E+, outputs, brightness, visibility, detector, facility,
scheduling, and unrelated work remain unauthorized.
