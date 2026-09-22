# 50S.7D.3B offline LIME resource and reference-output inspection

**Status:** Candidate controlled Mac inspection with explicit unsigned-package amendment; no Moonlight runtime

**Inspection-plan date:** 2026-09-22

**As-is base:** `c550da2e6c6ed5e17b489b09aaf4b95fe059f542`

**Scope:** Execute only the exact accepted LIME Toolbox `v1.4.2` macOS
distribution outside Wenu production code, with networking denied, to inventory
the selected coefficient resource and preserve native direct-selenographic
reference outputs. Fernando explicitly authorized this next step by saying
“proceed” after 50S.7D.3A was merged and its branch was removed.

## 1. Decision and stop line

This milestone supplies a reviewable operator harness and an evidence format.
It does not contain, install, import, wrap, or redistribute LIME. It does not
add a Wenu dependency, API, geometry evaluator, coefficient loader, or numeric
Moonlight result. `moonlight` remains `not_evaluated`.

The exact inputs remain:

- LIME Toolbox `v1.4.2`, source commit
  `b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f`;
- `lime.pkg`, `516220150` bytes, SHA-256
  `e0a84e250dc4f5beb8a8305278756bbc0b2b136814b9c4defb053970f983ba21`;
- coefficient `LIME_MODEL_COEFS_20251010_V01.nc`, `154366` bytes,
  SHA-256
  `8e6839d95315eb2d797484be559ad70b69010cc1eb9b614770f61bb5ce2cf691`;
  and
- coefficient selector `20251010_v1`.

Any identity mismatch, missing macOS control, resource ambiguity, output
mismatch, or execution failure stops the inspection. It does not authorize a
substitute package, coefficient, platform, network fallback, or production
implementation. A preexisting installed app is recorded and never selected.

### 2026-09-22 signature and installation amendment

On Fernando's Mac, the freshly downloaded exact-size, exact-SHA-256 package
returned `Status: no signature` from `pkgutil --check-signature`. The separately
installed v1.4.2 app returned `bundle format is ambiguous (could be app or
framework)` for `QtDataVisualization.framework` under strict `codesign`; its
selected coefficient matched the frozen digest. This is evidence of failed
signature gates, not a successful signature verification or proof that the
installed executable equals the accepted package. Fernando explicitly
authorized a revised inspection protocol after these observations.

The amended trust basis is the exact external package byte count and SHA-256
frozen in 50S.7D.3A, plus an exact bundled coefficient digest. The tool
records and admits only these two known signature results; any different
signature result or failure component stops before execution. The package and
app remain **unverified by signature**. The installed app is ignored, not
removed or executed. Do not interpret the receipt as code-signing assurance.

## 2. Why execution is required

Source and archive inspection established the interface but could not establish
the executable's exact native outputs. The remaining questions are empirical:

- the coefficient netCDF dimensions, variables, attributes, and wavelength
  coordinate actually bundled in the signed app;
- package and third-party notice inventory;
- CLI version/help behavior from the frozen asset;
- native CIMEL wavelengths, reflectance, irradiance, and uncertainty values;
- the toolbox's signed-phase and valid-domain behavior at both boundaries; and
- repeatability of a no-uncertainty calculation from identical inputs.

These are reference facts about an external candidate. They are not Wenu model
semantics until a later geometry comparison and separately accepted runtime
amendment establish compatibility.

## 3. No-install and no-network controls

`tools/validate_50s7d3b_lime_offline_inspection.py` is the sole operator
harness. On macOS it:

1. enters the network-denied sandbox before parsing bundled native libraries;
2. records, but never selects, any existing `/Applications/LimeTBX.app`;
3. verifies the exact package byte count and SHA-256;
4. records the exact unsigned result from `pkgutil --check-signature`;
5. uses `pkgutil --expand-full` in a temporary directory instead of running the
   installer;
6. records the known strict `codesign` failure on the extracted app and rejects
   any other failure component;
7. verifies the exact coefficient bytes inside that extracted app;
8. runs only the extracted executable with a minimal environment, isolated
   `HOME` and `TMPDIR`; the child inherits the harness's single macOS
   `sandbox-exec` profile
   `(version 1) (allow default) (deny network*)`;
9. poisons conventional proxy variables as defence in depth; and
10. never invokes LIME's `-u`/`--update` route.

The first amended Mac attempt at `49e8fb38` reached the extracted `-v` call
after package, coefficient, and signature diagnostics, then exited 71 with
`sandbox-exec: sandbox_apply: Operation not permitted`. The harness had entered
the sandbox successfully but attempted to apply it again to LIME. No LIME
process started, no native output or manifest was produced, and the partial
evidence directory is retained unchanged. The correction removes the nested
`sandbox-exec` call; the child inherits the enclosing sandbox. Invocation
without that enclosing sandbox fails before starting the executable. A new
evidence directory and fresh Mac gates are required for any later attempt.

The harness writes only to one caller-selected new evidence directory and a
temporary expansion that is deleted on exit. It never copies model resources
into the repository or Python package.

## 4. Frozen direct-selenographic cases

Every row uses Sun-Moon distance `0.98 au`, observer-Moon distance `420000 km`,
observer selenographic latitude `20.5 deg`, observer selenographic longitude
`-30.2 deg`, and solar selenographic longitude `69 deg`. Only signed phase
changes:

| Case | Phase (deg) | Expected LIME domain flag |
| --- | ---: | --- |
| negative above domain | -90.001 | outside |
| negative edge | -90 | inside |
| negative mid | -15 | inside |
| negative inner edge | -2 | inside |
| negative below domain | -1.999 | outside |
| positive below domain | 1.999 | outside |
| positive inner edge | 2 | inside |
| positive mid | 15 | inside |
| positive edge | 90 | inside |
| positive above domain | 90.001 | outside |

This freezes evidence for the source predicate
`2 <= abs(phase_angle) <= 90`; it does not claim that every inside-predicate
satellite geometry is scientifically admitted.

## 5. Native outputs and repeatability

The harness requests direct-selenographic netCDF output with exact coefficient
`20251010_v1` and CIMEL points enabled. It preserves:

- `cimel_wlens`;
- `irr_cimel` and `irr_cimel_unc`;
- `refl_cimel` and `refl_cimel_unc`;
- `outside_mpa_range`;
- `distance_sun_moon`, `distance_obs_moon`, `sun_lon`, `obs_lat`, `obs_lon`,
  and `mpa`; and
- the complete netCDF dimension, variable, and attribute-name inventory.

It performs the uncertainty-skipping calculation twice and requires exact
equality of native wavelengths, central irradiance and reflectance, geometry,
and domain flags. It then performs one uncertainty-enabled calculation.
Non-finite external values are preserved as explicit JSON strings rather than
emitted as non-standard JSON numbers.

The evidence directory contains the input rows, failed package and app
signature receipts with exit codes, CLI version/help, coefficient schema, raw netCDF outputs,
native-value JSON projections, logs, and a manifest with byte counts and
SHA-256 digests. The manifest explicitly records `network_access=false`,
`preexisting_installation_present=true` when applicable,
`installed_by_inspection=false`, `production_runtime_changed=false`, and
`moonlight_status=not_evaluated`.

## 6. Two-phase review

Phase A is the operator run defined here. Successful execution produces
candidate external evidence only. Fernando must return the console summary and
manifest for inspection; no automatic acceptance follows.

Phase B is a later review of that immutable evidence plus an independent
Wenu/SPICE geometry comparison. It must characterize, rather than assume,
LIME's lunar orientation, longitude direction, signed-phase convention,
distance convention, light-time policy, and aberration policy. Representative
LEO, MEO, GEO, and highly elliptical cases remain required by the parent audit.

The frozen scalar rows in Phase A deliberately isolate the LIME model from
orbit and frame computation. They cannot satisfy Phase B by themselves.

## 7. Ownership and repository effect

The new tool is developer validation infrastructure, not production runtime.
No production or package file changes. Existing durable future ownership stays
unchanged:

- `satellites/illumination.py` remains the reserved owner of same-instant
  Moonlight source geometry and typed eclipse/occultation state; and
- `satellites/radiometry.py` remains the reserved owner of exact external LIME
  admission, native-band radiometry, uncertainty, and failure behavior.

The coordinate-system guide was reviewed and remains current because this
milestone implements no coordinate value. Phase B and any runtime proposal
must update it when a lunar body-fixed convention becomes implemented.

## 8. Acceptance requirements

Before this candidate may be accepted, require:

- focused static harness tests, current-documentation tests, package-boundary
  tests, whitespace inspection, and the complete plugin-disabled suite;
- exact branch/head, upstream, and clean-tree confirmation;
- one controlled Mac Phase-A run against the exact package into a new external
  directory;
- review of the explicit signature failures, notices, coefficient schema, native outputs, logs,
  manifest, and every digest; and
- explicit scientific and architectural acceptance by Fernando.

Successful Phase A does not authorize Phase B execution, LIME installation,
vendoring, redistribution, API/dependency changes, or Moonlight runtime. Those
remain separate decisions.

## 9. Explicit non-goals

This milestone adds no package installation, resource acquisition, network
access, update check, EO-CFI/TLE route, coefficient transcription, Wenu lunar
geometry, numeric Moonlight, interpolation, custom passband, bolometric value,
eclipse or occultation calculation, GIRO execution, chart/report/CLI product,
spacecraft response, brightness, visibility, detector, facility, scheduling,
or 50S.7D.4+ behavior.

## 10. Recommendation

Treat the amended harness and this plan as a candidate until its static
repository gates and the single controlled Mac run are reviewed. If Phase A succeeds,
preserve the returned evidence without modification and audit it before
proposing the independent Wenu/SPICE geometry comparison. If it fails, stop
and diagnose the exact failed control; do not weaken the sandbox, change the
resource identity, install LIME, or retry with a different path implicitly.
