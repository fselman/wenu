# 50S.7D.3A external LIME distribution preflight

**Status:** Candidate documentation-and-receipt preflight; no Moonlight runtime

**Preflight date:** 2026-09-22

**As-is base:** `801cc6e80eb4a59db12cbc6752ab7a90400ec83d`

**Scope:** Identify and freeze one authoritative LIME distribution, inspect its
published license, model-resource layout, geometry interface, native model
anchors, domain, uncertainty path, and available reference evidence. Fernando
explicitly authorized this next preflight on 2026-09-22. The authorization
allowed retrieval and archive inspection only; it did not allow installation,
execution, vendoring, redistribution, coefficient transcription, or Wenu
runtime changes.

## 1. Outcome

The CEOS LIME page now directs users to the University of Valladolid LIME site,
which directs installers to the public `LIME-ESA/lime_tbx` GitHub releases.
The latest release inspected was LIME Toolbox `v1.4.2`, published 2026-07-27.

The exact macOS release asset was retrieved without installation or execution.
Its independently measured byte count and SHA-256 match GitHub's values:

- filename: `lime.pkg`;
- byte count: `516220150`;
- SHA-256: `e0a84e250dc4f5beb8a8305278756bbc0b2b136814b9c4defb053970f983ba21`;
- tag commit: `b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f`;
- source tree: `fe8ae947903ba17de65419d25e038ab697887638`.

This replaces the former unversioned-distribution uncertainty with an exact
candidate. It does not admit runtime. Coefficient selection, coefficient/data
licensing, third-party binary terms, exact lunar conventions, and authoritative
executable reference outputs remain unresolved. Moonlight therefore remains
`not_evaluated`.

## 2. Authoritative discovery chain

1. CEOS: <https://calvalportal.ceos.org/lime>;
2. LIME downloads: <https://lime.uva.es/downloads/>;
3. official releases: <https://github.com/LIME-ESA/lime_tbx/releases>;
4. `v1.4.2`: <https://github.com/LIME-ESA/lime_tbx/releases/tag/v1.4.2>;
5. versioned documentation: <https://lime-esa.github.io/lime_tbx/>.

The release API reported `immutable=false`. Wenu must identify the candidate
by exact bytes and commit, never by `latest`, a mutable page, or tag alone.

## 3. Release receipt

The release was published at `2026-07-27T10:37:02Z`. Retrieval began at
`2026-09-22T18:29:59Z`. GitHub returned one redirect to its release-asset host,
then HTTP 200 with content length `516220150`. No retry, fallback,
installation, or execution occurred.

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `lime.pkg` | 516220150 | `e0a84e250dc4f5beb8a8305278756bbc0b2b136814b9c4defb053970f983ba21` |
| `LimeTBX_installer_1.4.2.exe` | 163780394 | `a1d7de599aa8ad700ebf3e74552d7ff75cefca89e24f9eaef813adda9d175785` |
| `lime_1.4-2.deb` | 157370440 | `7ff97cbe73e45fc02d629b84a7efd3c36bb2c1c0ca54c5a34d44f532a5f245cd` |
| `lime_installer.zip` | 226623463 | `ead784373b5d1a425a54a87f310966d1356b8ca8dbc77ad0fdbd2eb44df3d2e4` |
| `User.Guide.v1.4.2.pdf` | 1746514 | `3f6ad3160ee11ab3482d0242263f828e4b7f55dd9d4d14836983341139f0a8e5` |

The exact source tag was cloned outside Wenu for read-only inspection. It
resolved to commit `b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f`, tree
`fe8ae947903ba17de65419d25e038ab697887638`, with `670` tracked files and a
clean detached worktree.

## 4. Why `v1.4.2` is the candidate baseline

Earlier releases are not interchangeable:

- `v1.3.0` has a published channel-assignment defect;
- `v1.4.0` added coefficient set `20251010_v1` and corrected channel mapping;
- `v1.4.2` corrected solar selenographic longitude CSV units, TLE propagation,
  satellite equality, and time-reference handling, and updated EO-CFI to 4.31.

The tag and asset digest, not merely the version, belong in future identity.

## 5. License and redistribution finding

The source tag contains the GNU Lesser General Public License version 3.
`pyproject.toml` declares `LGPL-3.0-only`, and the versioned documentation says
that code and documentation are licensed under LGPL-3.0.

This does not yet establish that every bundled or downloadable datum and
third-party binary may be redistributed by Wenu. Coefficient files lack a
separately inspected license declaration; EO-CFI, SPICE kernels, and datasets
need their own notice review; and the combined installer notice inventory was
not extracted. Wenu must neither vendor nor redistribute these resources.

## 6. Candidate coefficient inventory

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `LIME_MODEL_COEFS_20231120_V02.nc` | 127522 | `33fe61c327be84838a60501b9354057fd499d4f06135110439187ea8df20a6f7` |
| `LIME_MODEL_COEFS_20250608_V01.nc` | 154362 | `c4ed998e04e6d56227606d971bff9b05f167721fde7fba7394c7804ac2f5cc3b` |
| `LIME_MODEL_COEFS_20251010_V01.nc` | 154366 | `8e6839d95315eb2d797484be559ad70b69010cc1eb9b614770f61bb5ce2cf691` |

The documented schema contains reflectance coefficients, uncertainties, and
error-correlation matrices. The toolbox can download new coefficients and no
`selected.txt` is frozen in the tag. Wenu must disable updates and require one
explicit file; `v1.4.2` alone is not a complete model identity.

Source evidence identifies six established anchors at `440`, `500`, `675`,
`870`, `1020`, and `1640 nm`; the code also supports a possible `2130 nm`
seventh anchor. The exact wavelength coordinate, coefficient count,
uncertainty arrays, and covariance of `LIME_MODEL_COEFS_20251010_V01.nc` still
require a read-only netCDF inventory. No coefficient was transcribed into Wenu.

## 7. Native anchors versus interpolated spectrum

LIME evaluates its empirical model at coefficient-file CIMEL anchors. The
toolbox can then interpolate lunar reflectance using an ASD-based or
Apollo/composite reference spectrum, multiply by a selected solar spectrum,
and integrate through a user SRF. Its full output has `2151` wavelengths,
normally `350-2500 nm` at 1 nm spacing.

Native anchors, the derived interpolated spectrum, and SRF-integrated values
are distinct products. Uncertainty propagation uses correlation resources and
Monte Carlo machinery, not independent point errors. Wenu's first possible
runtime amendment must remain restricted to exact admitted native anchors.

## 8. Geometry interface and Wenu ownership

The toolbox offers geographic, direct selenographic, and satellite routes.
The direct route accepts:

1. Sun-Moon distance in au;
2. observer-Moon distance in km;
3. observer selenographic latitude in degrees;
4. observer selenographic longitude in degrees;
5. solar selenographic longitude in degrees; and
6. signed lunar phase angle in degrees.

The satellite route propagates OSF or TLE data through EO-CFI. Wenu must not
use that route in production because it would duplicate the accepted Wenu
OMM/SGP4/TEME/topocentric authority.

A future adapter must compute and retain Wenu's same-instant geometry, validate
it independently against LIME/SPICE, and supply direct selenographic inputs.
LIME may own lunar reflectance and uncertainty; it may not own Wenu orbit,
ephemeris, coordinate, crossing, visibility, or output behavior.

The implementation regards `2 <= abs(phase_angle) <= 90` degrees as valid.
Input layers represent wider values, so validity must bind to the model
predicate. Exact phase sign, lunar orientation, longitude direction,
light-time and aberration policies, and distance normalization remain open.

## 9. Platform and dependency finding

Documented platforms are Windows x86-64, Linux x86-64 with GLIBC at least
2.23, macOS x86-64, and macOS ARM64 through Rosetta. Source installation needs
Python 3.10 or newer and a large numerical/GUI/SPICE stack; satellite mode adds
compiled EO-CFI. Wenu must not adopt that stack as an ordinary dependency
without a later architecture decision.

## 10. Reference-output and execution stop gate

The source contains tests and saved examples, but this preflight did not find a
publisher-designated immutable reference set for `v1.4.2` with coefficient
`20251010_v1`. The toolbox was neither installed nor executed.

A separately authorized offline Mac inspection must extract notices, inventory
the coefficient netCDF, disable updates and all network access, run frozen
direct-selenographic cases, preserve exact outputs and digests, cover both
phase signs and domain edges, and compare geometry with direct Wenu/SPICE.
No such execution is authorized by this candidate.

## 11. Architecture and coordinate review

This preflight changes no production source, dependency, coordinate value, or
API. Future Moonlight geometry remains reserved to
`satellites/illumination.py`; exact LIME admission and native-band radiometry
remain reserved to `satellites/radiometry.py`. No chart, crossing, report, CLI,
or planning owner may import LIME directly.

The coordinate-system guide remains current for implemented behavior. Runtime
must add exact lunar orientation, longitude, phase-sign, time, distance, and
correction conventions before acceptance.

## 12. Explicit non-goals

This preflight adds no LIME installation or execution; vendored resource;
dependency; API; geometry; numeric Moonlight; interpolation; passband;
magnitude; detector result; implicit network access; replacement propagation;
or 50S.7D.4+ behavior.

## 13. Recommendation and authorization boundary

Retain LIME Toolbox `v1.4.2` at exact commit
`b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f` and macOS SHA-256
`e0a84e250dc4f5beb8a8305278756bbc0b2b136814b9c4defb053970f983ba21`
as the candidate distribution. Retain candidate coefficient
`LIME_MODEL_COEFS_20251010_V01.nc` SHA-256
`8e6839d95315eb2d797484be559ad70b69010cc1eb9b614770f61bb5ce2cf691`,
subject to schema and license confirmation.

Treat this record and the satellite-guide explanation as candidates for
Fernando's scientific and architectural review. Do not install or execute
LIME, begin Moonlight runtime, or authorize 50S.7D.4+. If accepted and merged,
only a separately authorized offline Mac resource-and-reference-output
inspection may follow.
