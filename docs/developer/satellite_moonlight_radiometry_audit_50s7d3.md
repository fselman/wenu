# 50S.7D.3 direct-Moonlight radiometry readiness audit

**Status:** Candidate documentation-only scientific, resource, and architectural audit

**Audit date:** 2026-09-22

**As-is base:** `5074358550051094c840bcab827760861fec101a`

**Scope:** Direct Moonlight incident radiometry only. This audit selects a
preferred scientific model family and defines the missing geometry, resource,
domain, uncertainty, and validation gates. It deliberately authorizes no
runtime, model-resource acquisition, redistribution, dependency, output,
brightness, detector, facility, or scheduling behavior.

## 1. Decision summary

Direct Moonlight is sunlight reflected by the lunar disk and received by an
abstract unit area normal to the incoming beam at the satellite. It is distinct
from solar Earthshine, Lunar-Earthshine, spacecraft response, apparent
brightness, atmospheric propagation, and detector response.

The reviewed model families are not interchangeable:

- ROLO supplies the durable phase- and libration-dependent analytical form but
  carries approximately 5%-10% absolute irradiance uncertainty.
- GIRO is a reproducible operational implementation of ROLO and is appropriate
  independent comparison evidence; it does not remove ROLO's absolute-scale
  limitation.
- LIME uses a modified ROLO form, SI-traceable measurements, TSIS-1 solar
  irradiance, band-specific uncertainty, and reports expanded uncertainty
  generally below 2% at its measured bands.

**LIME is the preferred production candidate.** It is not yet an admitted Wenu
model. The published paper states that the coefficient-retrieval code is ESA
property and directs users to the LIME Toolbox to reproduce model outputs. The
same paper reports incomplete selenographic coverage. The public CEOS page
advertises the toolbox but the present audit could not freeze an exact
versioned distribution, byte identity, coefficient resource, or redistribution
license.

The scientific choice is therefore accompanied by a mandatory stop gate:
**50S.7D.3 runtime is not authorized.** The next bounded operation, after
separate acceptance and merge of this audit, is only an explicit external LIME
distribution preflight. It must retrieve no bytes until separately authorized,
then record exact version, filenames, byte counts, SHA-256 digests, platform
requirements, complete license terms, coefficient/band schema, documented
domain, and reproducible reference outputs. Failure to establish any item
leaves Moonlight `not_evaluated`.

## 2. As-is assessment

Accepted 50S.7B supplies same-instant satellite and Sun geometry, direct-solar
occultation, and observer twilight. Its `lunar_occultor_status` only reserves
whether the Moon occults the Sun; it is not Moonlight geometry and must not be
repurposed.

Accepted 50S.7D.1 supplies scalar bolometric direct-Sun irradiance in
`satellites/illumination.py`. Accepted 50S.7D.2 supplies exact external
TSIS-1 spectral-resource admission and native-grid solar composition in
`satellites/radiometry.py`. Neither owner currently supplies:

- an Earth-to-Moon state retained with the satellite state;
- Moon-to-satellite distance and direction;
- Sun-to-Moon distance and direction;
- lunar phase with a frozen sign convention;
- selenographic Sun and satellite coordinates in a frozen lunar body frame;
- Earth occultation of the Moon as viewed from the satellite;
- Earth eclipse of incident sunlight at the Moon; or
- a lunar radiometric model or coefficient resource.

The existing ephemeris stack can provide geometric Earth, Sun, and Moon states,
but an admitted 50S.7D.3 geometry composition must transform them and the
satellite into one explicit same-instant Cartesian frame before subtraction.
No current chart, lunar appearance, crossing, track, report, CLI, or planning
type is an incident-Moonlight owner.

## 3. Primary evidence and model comparison

### 3.1 ROLO and GIRO

Kieffer and Stone model disk-integrated lunar spectral irradiance as a function
of phase and lunar libration. ROLO observations cover phase angles
approximately from -90 to +90 degrees in 32 VNIR/SWIR passbands. Its analytical
form remains the basis of both GIRO and LIME.

GIRO uses SPICE geometry and implements the ROLO model. Published comparisons
found GIRO and ROLO equivalent apart from numerical-instability cases. That
makes GIRO valuable as an independent executable oracle. It does not establish
a new absolute radiometric scale; the reported ROLO absolute uncertainty
remains approximately 5%-10%.

Primary evidence:

- <https://doi.org/10.1086/430185>
- <https://acp.copernicus.org/articles/24/3649/2024/>

### 3.2 LIME

LIME derives a modified ROLO analytical model from SI-traceable ground
measurements. The published model uses absolute phase, selenographic observer
latitude and longitude, solar selenographic longitude, Sun-Moon distance,
Moon-observer distance, band-specific coefficients, and TSIS-1 solar
irradiance. It reports expanded `k=2` uncertainty generally below 2% at its
measured bands and predicts visible/near-infrared irradiance about 3%-5% above
ROLO/GIRO in the reported comparisons.

Those advantages make LIME preferable for Wenu's publication-quality target,
but three limitations are acceptance-critical:

1. coefficients are band-specific rather than a continuous native spectrum;
2. the publication reports incomplete selenographic coverage; and
3. the coefficient-retrieval code is ESA property while model reproduction is
   delegated to a separately distributed toolbox.

Primary sources:

- <https://doi.org/10.5194/acp-24-3649-2024>
- <https://doi.org/10.5194/acp-24-3649-2024-corrigendum>
- <https://calvalportal.ceos.org/lime>

### 3.3 Selection disposition

| Candidate | Scientific scale | Reproduction role | 50S.7D.3 disposition |
| --- | --- | --- | --- |
| ROLO | established, approximately 5%-10% absolute uncertainty | published analytical comparison | not production default |
| GIRO | ROLO-equivalent operational implementation | independent offline oracle if exact release and access are frozen | validator only |
| LIME | SI-traceable, band-specific `k=2` uncertainty generally below 2% | preferred production candidate through exact toolbox/resource | blocked pending resource and license preflight |

No undocumented coefficient transcription, third-party reimplementation, or
unversioned web service is admissible.

## 4. Required Moonlight geometry contract

A future implementation may evaluate one satellite and one canonical UTC
instant only after binding all of the following immutable evidence:

- satellite, orbit solution, snapshot, ephemeris resource, Earth-orientation
  resource, and evaluation identity;
- same-instant Earth, Sun, Moon, and satellite Cartesian states in explicitly
  declared source frames;
- one explicit common-frame transformation policy;
- satellite-to-Moon and Moon-to-Sun vectors and distances;
- unsigned geometric phase angle in `[0, 180]` degrees;
- the model's separately frozen signed phase convention, including
  waxing/waning interpretation and zero definition;
- selenographic Sun longitude and latitude plus satellite-observer longitude
  and latitude in one named IAU lunar body-fixed frame, with longitude
  direction, epoch/orientation model, and units;
- lunar apparent angular radius at the satellite;
- Earth occultation status or visible lunar-disk fraction along the
  Moon-to-satellite path;
- lunar-eclipse status along the Sun-to-Moon path; and
- numerical policy, convergence evidence, provenance, and warnings.

The production implementation must not infer the toolbox's phase sign, lunar
frame, longitude direction, light-time policy, aberration policy, or reference
distance from a similarly named Wenu quantity. A controlled preflight must
reproduce the toolbox geometry convention with direct SPICE evidence before
runtime is proposed.

The source state is geometric. Near-Earth satellite illumination uses one
physical reception instant; it must not mix an apparent observer direction with
same-instant geometric distances. Any model-required light-time convention
must be explicit and independently validated.

## 5. Required radiometric contract

The first possible production result is **band-integrated normal-plane direct
Moonlight irradiance** in `W m-2` at the satellite. It is not lunar radiance,
surface irradiance, illuminance, magnitude, or detector signal.

An immutable future result must retain:

- component key `moonlight` and status `evaluated`;
- complete Moonlight geometry identity;
- exact admitted LIME distribution and coefficient identity;
- native LIME band identifier and documented spectral response;
- model reflectance or reference irradiance as actually defined by LIME;
- reference and actual Sun-Moon and Moon-satellite distances;
- unocculted and incident normal-plane irradiance;
- model uncertainty value, coverage factor, confidence meaning, and correlation
  limitations exactly as supplied;
- eclipse and occultation statuses;
- deterministic identity, provenance, warnings, and exclusions.

The initial implementation must expose only native admitted LIME bands. It may
not interpolate coefficients, synthesize a continuous spectrum, convolve an
arbitrary passband, extrapolate wavelength or phase, renormalize to ROLO/GIRO,
or combine native-band uncertainties. Integrated or cross-band uncertainty
remains `not_evaluated` unless the admitted resource supplies the needed
covariance.

Numeric zero is valid only after successful evaluation of a model-domain
geometry whose Moon-to-satellite path has zero visible source contribution.
Missing resource, unsupported geometry, lunar eclipse outside the model
domain, numerical failure, and unknown occultation are never numeric zero.

## 6. Domain, eclipse, and occultation policy

The external preflight must freeze the exact LIME domain for phase,
selenographic coordinates, distance normalization, bands, and supported
platform geometry. A satellite observer close to Earth must not be assumed
valid merely because the model accepts an observer position.

Until separate model evidence exists:

- phase or selenographic extrapolation fails closed;
- partial or total lunar eclipse returns `not_evaluated`, not a phase-scaled
  value;
- unresolved Earth occultation of the lunar disk returns `not_evaluated`;
- a fully Earth-occulted Moon may become evaluated zero only after a separately
  accepted finite-disk occultation model proves zero visibility; and
- solar Earthshine on the Moon, polarization, thermal emission, and wavelength-
  dependent lunar topography remain excluded.

Earth eclipse at the Moon and Earth occultation between Moon and satellite are
different paths and must have different typed statuses.

## 7. Resource, licensing, and dependency gate

A later resource preflight must operate outside the repository and package. It
must not install or execute newly acquired software without separate explicit
authorization. Its receipt must record:

- authoritative retrieval URL and retrieval UTC;
- HTTP status and redirect chain, if retrieval is authorized;
- release/version identifier and publisher;
- every archive and science-resource filename, byte count, and SHA-256;
- exact license text and whether local use, CI use, coefficient extraction,
  modification, redistribution, and publication of derived outputs are allowed;
- required runtime, architecture, operating-system, and SPICE dependencies;
- coefficient table, band response, reference-distance, uncertainty, and
  geometry schemas;
- authoritative example inputs and outputs; and
- `network_access=false` for every later science evaluation.

If redistribution is not explicitly allowed, Wenu must use an external
installed-resource workflow analogous to 50S.7D.2. If programmatic automation,
offline execution, or stable version pinning is prohibited, LIME cannot be the
production dependency and a new audit must reconsider ROLO/GIRO or a later
model.

## 8. Ownership and dependency direction

The current durable ownership remains appropriate:

- `satellites/illumination.py` is the closest owner for new same-instant
  Moonlight source geometry and typed eclipse/occultation states;
- `satellites/radiometry.py` is the closest owner for exact external model
  admission, native-band policy/result/evaluation, uncertainty, and failures;
- `tests/test_satellite_illumination.py` owns geometry/frame/path evidence;
- `tests/test_satellite_radiometry.py` owns model-resource, scaling,
  uncertainty, zero-versus-unknown, and fail-closed contracts.

No new production or test file is authorized by this audit. A later proposal
must justify any separate lunar-resource module by its distinct lifecycle,
dependency, provenance, or failure boundary rather than by milestone number or
file size. No renderer, chart, crossing, report, CLI, planning, or detector
owner may import the lunar model directly.

## 9. Validation gates for a later proposal

Before any runtime audit may be accepted, require all of the following.

### 9.1 Resource and license evidence

- exact LIME distribution receipt and complete license review;
- offline repeatability on Fernando's Mac;
- no implicit network access or mutable remote service;
- stable native-band and uncertainty metadata; and
- byte-identical reloading with deterministic resource identity.

### 9.2 Geometry evidence

- direct SPICE recomputation of phase, selenographic coordinates, and both
  distances for representative LEO, MEO, GEO, and highly elliptical states;
- waxing and waning cases, near-full-Moon opposition behavior, and admitted
  domain edges;
- explicit Earth occultation and lunar-eclipse specimens; and
- component tolerances selected from characterized residuals, not guessed.

### 9.3 Radiometric evidence

- exact reproduction of authoritative LIME reference cases in every admitted
  native band;
- comparison against GIRO/ROLO with the expected model-scale difference
  recorded as a comparison, not a tolerance;
- independent distance scaling without calling the production evaluator;
- pointwise uncertainty reproduction including `k` meaning; and
- zero, unknown, unavailable, and out-of-domain states remaining distinct.

### 9.4 Repository gate

A later executable candidate requires focused illumination, radiometry,
ephemeris, package-boundary, and documentation tests; an external offline
receipt; the complete plugin-disabled suite; clean diff; exact upstream
equality; clean worktree; and Fernando's separate scientific and architectural
review.

## 10. Coordinate-system guide review

This audit introduces no runtime coordinate value. It identifies a future
lunar body-fixed geometry obligation that the current guide does not yet
implement: the model's exact selenographic frame, orientation version,
longitude sign, and phase sign must be bound at the provider/model boundary.

The coordinate-system guide was reviewed and remains current for implemented
behavior. A later runtime proposal must update it before acceptance because
selenographic geometry would become a new implemented coordinate
responsibility.

## 11. Explicit non-goals

This audit adds no:

- numeric Moonlight or coefficient table;
- LIME, GIRO, or ROLO download, installation, execution, or redistribution;
- continuous lunar spectrum, arbitrary passband, interpolation, extrapolation,
  or bolometric Moonlight;
- lunar-eclipse or Earth-occultation runtime;
- solar Earthshine or Lunar-Earthshine;
- spacecraft attitude, projected area, self-shadowing, surface, BRDF, glint,
  polarization, temperature, or magnitude;
- atmospheric extinction, observer visibility, detector response, trail
  contamination, facility integration, or scheduling;
- crossing, transition, report, chart, CLI, planning, or output integration; or
- 50S.7D.4, 50S.7E, 50S.7F, 50S.8, 50S.9, or 50S.10 behavior.

## 12. Recommendation and authorization boundary

Treat this document as a candidate readiness audit, not an implementation
contract. Fernando's separate scientific and architectural acceptance is
required before merge.

If accepted and merged, authorize only a documentation-and-receipt LIME
distribution preflight under separately approved retrieval conditions. That
preflight may inspect exact model resources and licensing but may not modify
runtime, vendor resources, install or execute newly acquired software, or
produce a Moonlight value.

50S.7D.3 implementation remains blocked until a later accepted amendment
records an exact reproducible LIME distribution, byte identities, licensing,
native bands, coefficients, geometry conventions, supported domain,
uncertainty, and authoritative reference outputs. PR merge and branch deletion
remain separate explicit decisions.

## 13. Accepted 50S.7D.3 readiness audit

Fernando scientifically and architecturally accepted exact documentation-only
candidate `abbb1b78fbd272ef8b5553d515e9f2a896a0aa55` on 2026-09-22.
The final current-documentation and package-boundary gate passed all 230
plugin-disabled tests in 11.39 seconds. The diff check, exact upstream
equality, and clean worktree also passed.

Preserve LIME as the preferred production candidate and GIRO/ROLO as comparison
evidence. This acceptance authorizes no Moonlight runtime, resource retrieval,
installation, execution, redistribution, coefficient transcription, or numeric
output. After this audit is merged, proceed only to a separately controlled
external LIME distribution preflight that freezes exact version, files, byte
identities, license, native bands, coefficients, geometry conventions, domain,
uncertainty, and authoritative reference outputs.

Do not begin the preflight before merge. A later documentation amendment and
Fernando's separate acceptance remain mandatory before any 50S.7D.3 runtime.
PR 188 merge and branch deletion remain separate explicit decisions.
