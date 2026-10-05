# 50S.7D.2 spectral direct-Sun radiometry audit

**Status:** Accepted documentation-only scientific, resource, and architectural audit

**Audit date:** 2026-09-22

**As-is base:** `c76525c4986faabff0a70e534d1706baa4f550e6`

**Scope:** A bounded spectral direct-Sun proposal following accepted 50S.7D.1.
This audit authorizes no runtime, resource acquisition, redistribution,
dependency, Moonlight, reflected field, spacecraft response, output, detector,
facility, or scheduling behavior.

## 1. Decision summary

50S.7D.2 should add an empirical reference spectrum without changing the
accepted bolometric model. The proposed source is **TSIS-1 HSRS version 2**, DOI
`10.25980/ta3f-7h90`, using the provider's `tsis1_hsrs_1nm` product. This is the
1 nm FWHM Gaussian-convolved spectrum sampled every 0.1 nm, not the native
high-resolution line spectrum, not the 1 nm-binned full-spectrum extension,
and not a bolometric replacement.

The bounded implementation proposed after separate acceptance would:

1. admit one exact installed CSV resource by byte digest;
2. preserve all 25,281 native samples from 202.0 through 2730.0 nm;
3. return energy spectral irradiance and pointwise uncertainty at 1 au, scaled
   by accepted Sun-satellite distance and uniform-disk visible fraction;
4. provide explicit trapezoidal energy integration on the native wavelength
   coordinates; and
5. fail closed outside the admitted domain or when resource identity, schema,
   monotonicity, spacing, finiteness, or geometry is inconsistent.

No interpolation, extrapolation, renormalization to `1361 W m-2`, photon
quantity, arbitrary passband, solar-cycle variability, limb-darkening model,
or aggregate uncertainty is silently supplied.

## 2. Primary evidence and exact candidate resource

CEOS WGCV recommends TSIS-1 HSRS as the solar irradiance reference spectrum.
Coddington et al. (2023) describe version 2 as a solar-minimum reference over
0.202-2.730 micrometres, containing more than 97% of TSI, with 0.3%-1.3%
wavelength-dependent uncertainty. Version 2 corrects the 0.202-0.210
micrometre baseline, updates lines beyond 0.743 micrometres, and is distinct
from the partly model-based 0.115-200 micrometre full-spectrum extension.

Primary sources:

- <https://doi.org/10.1029/2022EA002637>
- <https://doi.org/10.25980/ta3f-7h90>
- <https://calvalportal.ceos.org/home/-/asset_publisher/1aO8bapeanp9/content/tsis-1-hsrs-solar-irradiance-reference-spectrum>
- <https://lasp.colorado.edu/lisird/data/tsis1_hsrs/>

The audit queried on 2026-09-22:

`https://lasp.colorado.edu/lisird/latis/dap/tsis1_hsrs_1nm.csv`

Observed candidate serialization:

- byte count: `1298915`;
- line count: `25282` including the header;
- SHA-256: `1cf3b07e6ac9669c429ad7ce9e92d50dfd741422efcfffa3d1e0eeb5f901616f`;
- columns: wavelength (`nm`), irradiance (`W/m^2/nm`), uncertainty
  (`W/m^2/nm`), and bandwidth (`nm`);
- 25,281 strictly increasing samples, 202.0-2730.0 nm inclusive, with 0.1 nm
  coordinate spacing and constant 1.0 nm bandwidth.

The digest identifies these retrieved bytes, not an assurance that the live
API can never change. Implementation must preserve the admitted bytes or a
separately reviewed canonicalization plus both source and canonical digests.
Redistribution terms were not explicit in the accessed metadata. Therefore
this audit does not authorize vendoring; redistribution evidence or an
external installed-resource workflow is an acceptance prerequisite.

## 3. Scientific semantics

The resource quantity is reference **energy spectral irradiance per unit
wavelength on a normal plane at 1 au**. For each native wavelength sample
`lambda_i`, accepted distance `r`, and accepted uniform-disk fraction `f`:

```text
E_clear(lambda_i) = E_HSRS(lambda_i) * (au / r)^2
E_incident(lambda_i) = f * E_clear(lambda_i)
```

Pointwise absolute uncertainty scales by the same non-negative factors. It
describes the provider spectrum, not distance, ephemeris, occultation,
solar-variability, or model-choice uncertainty.

The spectrum is a Dec 1-7, 2019 solar-minimum reference, not instantaneous
solar weather. Its finite domain omits roughly 3% of TSI. It must not be
renormalized to the exact IAU nominal `1361 W m-2`; accepted 50S.7D.1 remains
the bolometric nominal model. A native-grid trapezoidal audit integral of the
candidate CSV is `1325.759295697943 W m-2`; this is a resource invariant, not
a replacement TSI constant.

`bandwidth=1.0 nm` is spectral resolution (FWHM), while samples are spaced by
0.1 nm. Multiplying every sample by 1 nm would overcount by about a factor of
ten. Energy integration uses wavelength-coordinate intervals:

```text
integral = sum((lambda[i+1] - lambda[i])
               * (E[i+1] + E[i]) / 2)
```

No endpoint outside 202.0-2730.0 nm is inferred. Partial-domain requests must
use exact native endpoints. Arbitrary interpolation and extrapolation fail
closed.

## 4. Passbands, photons, occultation, and uncertainty

The spectral record is energy-weighted. A future admitted dimensionless
energy-response array `T_i` on the exact same grid may use trapezoidal
integration of `E_lambda T`; a photon-counting response requires the distinct
factor `lambda/(h c)` and distinct photon units. 50S.7D.2 must not infer which
convention an unlabeled passband uses. The bounded first implementation should
return the native spectrum and exact-grid energy integrals only; named
passbands and detector photon rates remain later contracts.

Applying one visible fraction at every wavelength preserves the accepted
uniform-radiance disk model but is an achromatic approximation. Solar limb
darkening and its wavelength dependence remain unevaluated and must be stated
in provenance, especially for penumbra. Umbra alone yields evaluated numeric
zero. Unknown or unsupported source state never becomes zero.

The resource lacks wavelength covariance. Pointwise uncertainty may be
retained, but integrated uncertainty must remain `not_evaluated`; treating
samples as statistically independent or fully correlated without evidence is
forbidden.

## 5. Proposed immutable contracts

After acceptance and merge, a bounded implementation may introduce:

- `SolarSpectralIrradianceResourceIdentity`: DOI, product name, source URL,
  byte count, SHA-256, access date, schema, units, domain, sample count,
  sampling, resolution, and redistribution status;
- `DirectSolarSpectralIrradiancePolicy`: exact resource identity, distance law,
  accepted uniform-disk occultation model, native-grid-only integration, and
  uncertainty statuses;
- `DirectSolarSpectralIrradiance`: complete accepted geometry, immutable native
  wavelength/irradiance/uncertainty tuples, resource identity, provenance,
  warnings, and deterministic identity; and
- `DirectSolarSpectralIrradianceEvaluator`: offline composition over one
  accepted `SatelliteIlluminationGeometry` and one admitted resource.

Arrays must be immutable by contract. Identity must not hash platform-specific
float text; it derives from the resource digest, policy, geometry identity,
and exact request boundaries. Loading validates UTF-8 CSV, exact header,
finite non-negative values, strict monotonicity, 25,281 rows, endpoints,
spacing, bandwidth, and digest before returning any science value.

The distinct resource lifecycle justifies a new
`src/wenu/satellites/radiometry.py` owner rather than further enlarging
`illumination.py`. Tests belong in `tests/test_satellite_radiometry.py`.
Any acquisition helper is a separate explicit network boundary and never runs
during evaluation or import. No new package dependency is required.

## 6. Validation and acceptance gates

Before implementation review require:

1. exact resource retrieval, byte digest, schema, count, endpoints, spacing,
   resolution, and trapezoidal-integral receipt;
2. resolved redistribution or explicit external-resource policy;
3. analytic distance scaling, sunlit equality, penumbra composition, umbra
   zero, native-subrange integration, and zero-versus-unknown tests;
4. corruption, digest, header, count, order, duplicate, non-finite, negative,
   endpoint, spacing, bandwidth, off-grid, interpolation, and extrapolation
   failures;
5. independent recomputation from the admitted bytes without calling the
   production evaluator;
6. current-documentation, package-boundary, focused, and complete
   plugin-disabled Mac gates; and
7. exact upstream, clean diff, and clean worktree evidence.

## 7. Explicit exclusions and authority

This candidate authorizes no implementation. It adds no high-resolution line
product, full-spectrum extension, solar-cycle/time-varying spectrum,
wavelength-dependent limb darkening, named passband library, photon detector
rate, Moonlight, Earth-reflected field, component bundle, surface/attitude/
BRDF response, observer brightness, magnitude, visibility, report, chart,
CLI, planning, facility, scheduling, or unrelated refactoring.

50S.7D.3 Moonlight, 50S.7D.4 direct-source closure, 50S.7E reflected fields,
50S.7F bundling, 50S.8 brightness, 50S.9 detector effects, implementation,
merge, and branch deletion remain separate explicit decisions.

## 8. Accepted scientific and architectural decision

Fernando scientifically and architecturally accepted this documentation-only
audit at exact candidate
`0a1a6a681bc3e9b4dd562a0b0b57ae48ff5caefe` on 2026-09-22. The
documentation/package gate passed all 225 tests; exact upstream equality and a
clean worktree were confirmed. No runtime or spectral resource was added.

The accepted bounded decisions are:

- TSIS-1 HSRS v2 product `tsis1_hsrs_1nm`, with 1 nm FWHM resolution;
- all 25,281 native samples at 0.1 nm spacing over 202-2730 nm;
- no interpolation, extrapolation, or renormalization to `1361 W m-2`;
- retained pointwise provider uncertainty, with integrated uncertainty
  remaining `not_evaluated`; and
- an external installed-resource workflow unless redistribution rights are
  separately established.

After this audit is merged, only the bounded offline 50S.7D.2 spectral
direct-Sun implementation described above is authorized. It must preserve the
accepted 50S.7D.1 bolometric model independently and must not vendor or acquire
the spectral resource implicitly. 50S.7D.3 Moonlight, reflected fields,
spacecraft response, brightness, visibility, detector effects, outputs,
facility behavior, scheduling, PR merge, and branch deletion remain separate
explicit decisions.

## 9. Candidate implementation evidence

Executable candidate `8e930db200b922cc3a4f403cde50cd00c34d0a27` implements
the accepted bounded offline slice in `satellites/radiometry.py`. It adds no
vendored resource or acquisition behavior. The explicit external-resource
receipt reproduced byte count `1298915`, SHA-256
`1cf3b07e6ac9669c429ad7ce9e92d50dfd741422efcfffa3d1e0eeb5f901616f`,
the exact four-column header, all 25,281 samples, 202.0-2730.0 nm endpoints,
0.1 nm sampling, 1.0 nm resolution, and production-loader equality.

The independent native-grid integral was `1325.759295697934 W m-2`; its
approximately `9e-12 W m-2` difference from the audit value is below the
declared `1e-9 W m-2` receipt tolerance. The 79-test focused gate passed.
Complete repository gates and Fernando's separate scientific and
architectural acceptance remain pending. 50S.7D.3, merge, and branch deletion
remain unauthorized.

## 10. Verified implementation candidate

Exact branch head `8f2ca825fa799b171717fccd10ce50fab95255d7` retains
executable candidate `8e930db200b922cc3a4f403cde50cd00c34d0a27`. The real
external-resource receipt, 132-test expanded gate, 227-test
documentation/package gate, clean diff, and all 2,858 plugin-disabled
repository tests passed; exact upstream equality and a clean worktree were
confirmed.

This evidence verifies, but does not accept, the bounded implementation.
Fernando's scientific and architectural acceptance, PR merge, branch deletion,
50S.7D.3 Moonlight, and every later behavior remain separate explicit
decisions.

## 11. Accepted implementation decision

Fernando scientifically and architecturally accepted exact verified candidate
`d1edeb46f4ea70c34121910c54758c331fe4293b` on 2026-09-22. The accepted
runtime is executable `8e930db200b922cc3a4f403cde50cd00c34d0a27`, with its
exact external-resource identity, immutable native grid, pointwise uncertainty,
distance and accepted achromatic occultation scaling, native-coordinate energy
integration, explicit uncertainty limits, typed failures, and no-download
validation boundary.

The real-resource receipt, 132 expanded tests, complete 2,858-test suite, and
final 228 documentation/package gate passed. PR 187 remains draft and
unmerged. Merge, branch deletion, 50S.7D.3 Moonlight, and every later behavior
remain separate explicit decisions.
