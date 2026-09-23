# Phase B: frozen-kernel lunar geometry comparison protocol

**Status:** Documentation-only candidate; resource and convention gates remain open. No comparison run or Moonlight runtime is authorized.

**Date:** 2026-09-23

**As-is base:** `29302ed65e04b9280a5cb31631985e41deb25c7c` on `program/50s-crossing-foundation`; Fernando reported a clean, synchronized Mac tree.

**Parent:** [Accepted Phase B geometry audit plan](satellite_moonlight_geometry_comparison_audit_50s7d3_phase_b.md). This protocol makes its input, independence and stop gates reviewable. It is **not yet an executable, fully frozen run card**: the four lunar/time kernels below were not found in the bounded Mac inventory, the HEO specimen is missing, and the precise LIME geometry convention has not been proven. Fill those gaps in a separate reviewed amendment before asking to run a comparison.

## Resource ledger and stop gate

The operator's read-only inventory on 2026-09-23 reported the following installed resources. Paths are local provenance, never download destinations or redistribution grants. Verify each size and hash afresh before an authorized run; reject a mismatch.

| Resource | Local identity | Bytes | SHA-256 | Gate |
| --- | --- | ---: | --- | --- |
| DE440s position SPK | `/Users/fselman/.cache/wenu/de440s.bsp` | 32,726,016 | `c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2` | Installed; verify coverage and target/centre IDs. |
| IERS-A finals | `/Users/fselman/anaconda3/lib/python3.11/site-packages/astropy_iers_data/data/finals2000A.all` | 3,755,676 | `d4bb5af084caf3e82621bc75aad902dc7ad9e38e785a97d3fcac0a23d89644fb` | Installed; verify EOP coverage, UT1-UTC and polar motion per epoch. |
| Lunar orientation PCK | `moon_pa_de440_200625.bpc` | unknown | unknown | **NOT_FOUND**; stop. |
| Paired lunar frame FK | `moon_de440_220930.tf` | unknown | unknown | **NOT_FOUND**; stop. |
| Leap seconds LSK | `naif0012.tls` | unknown | unknown | **NOT_FOUND**; stop. |
| Generic text PCK for diagnostic `IAU_MOON` | `pck00011.tpc` | unknown | unknown | **NOT_FOUND**; stop for this diagnostic. |

NAIF's [DE440 frame specification](https://naif.jpl.nasa.gov/pub/naif/pds/wgc/kernels/fk/moon_de440_220930.tf) pairs the named FK with `moon_pa_de440_200625.bpc`. Use exactly that pair, with frame `MOON_PA_DE440` and diagnostic `MOON_ME_DE440_ME421`; do not substitute generic aliases without inspecting their loaded definitions. Publisher locations for the other resources are [lunar binary PCK](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/), [generic text PCK](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/), and [LSK](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/). Listing a publisher URL does not authorize a download. Acquire nothing and run no geometry under this document alone. Freeze bytes, hashes, licensing, coverage, version, load order and full local paths in a follow-up amendment; prohibit implicit downloads and mixed ephemeris/orientation versions. The exact LSK must support every candidate UTC epoch. Do not assume that an IERS-A snapshot covers a later selected UTC merely because it exists.

The installed interpreter reported SpiceyPy `6.0.3`, Astropy `7.1.0`, astropy-iers-data `0.2026.7.27.0.56.29`, Skyfield `1.54`, and sgp4 `2.25`. Record Python, OS, CSPICE runtime version, and the final tool versions in the execution manifest; these inventory values are not a runtime attestation.

## Independent reference recipe (after gates are satisfied)

Pin every row as `(UTC, Earth-centred satellite position and velocity, state frame, km and km/s, provenance)`. Transform an ITRS specimen to inertial coordinates with an independently specified, EOP-bound Earth-orientation recipe; record UT1-UTC, polar motion, terrestrial/celestial conventions, and a separate transform cross-check. Prefer a directly supplied inertial state where this extra conversion is unnecessary. Never treat TEME, GCRS, ICRF, ITRS and SPICE `J2000` labels as interchangeable without an explicit documented mapping. A Wenu orbit snapshot may be the common *input* to both paths; Wenu lunar geometry code must not feed the SPICE reference.

In an isolated SPICE kernel pool, load the verified LSK, DE440s SPK, paired lunar PCK/FK, and the text PCK only if testing `IAU_MOON`; record the exact order. Convert each UTC with that LSK to ET/TDB, check SPK and PCK coverage at ET, and use `spkpos('MOON', et, 'J2000', 'NONE', 'EARTH')` and `spkpos('SUN', et, 'J2000', 'NONE', 'EARTH')` (or equivalent verified state calls) for geometric centre positions in km. Confirm available bodies/centres in the *actual* SPK before making the calls. Set `r_ms = r_sun - r_moon`, `r_mq = r_sat - r_moon`, `d_ms = |r_ms|`, `d_mq = |r_mq|`, and `phase = acos(clamp(dot(r_ms,r_mq)/(d_ms*d_mq), -1, 1))` in degrees. Use the exact astronomical unit declared by the eventual LIME input evidence to report the Sun-Moon distance in au; retain the km value and conversion constant.

At the **same ET**, explicitly call `pxform('J2000', 'MOON_PA_DE440', et)` and transform both Moon-centred vectors with that matrix. Derive observer and solar longitude with `atan2(y,x)` and latitude with `atan2(z,hypot(x,y))`; record degrees, east-positive axis convention, `[-180,180)` wrap, and a circular longitude residual. Diagnose `MOON_ME_DE440_ME421` separately and `IAU_MOON` only after loading its text PCK. Log angular matrix differences and transformed-coordinate differences; do not choose a frame based on whichever residual is smallest. Moon-centred direction here is not a surface-intercept/subsolar-point computation. For any named `SUBSLR`/`SUBPNT` diagnostic, state method, observer, reference frame, illumination/shape assumption and correction explicitly; keep its result in a different column.

The independent second check must reproduce the unsigned phase from inertial unit vectors and verify transformed vector norms and dot products under rotation. Compute the satellite-Moon and Moon-Sun paths separately; label Earth occultation, Earth-limb and lunar eclipse status without setting any unvalidated flux to zero. The baseline uses one physical instant and `abcorr='NONE'`. Optional `LT`, `CN`, `LT+S`, or `CN+S` diagnostics need separate rows, explicit observation epoch and target/observer choice; do not combine an apparent Earth-observer Moon direction with a geometric satellite state.

## Specimen ledger to freeze before execution

The existing [`synthetic_50s4b_v1` snapshot](../../src/wenu/data/satellites/snapshots/synthetic_50s4b_v1/README.md) supplies synthetic LEO `300001`, MEO `300002`, and GEO-like `300003` OMM records at `2026-09-15T00:00:00Z`. Their immutable record and manifest digests, propagator status, actual Cartesian states, frame conversion, and coverage must be included in an amendment. They do **not** supply a HEO or license arbitrary propagation months away to obtain lunar phases. Use explicit, independently checkable synthetic Cartesian state fixtures for other epochs and label them as synthetic; never report them as observed spacecraft.

| ID | Regime / discriminant | Candidate input | Required outcome before run |
| --- | --- | --- | --- |
| S1–S3 | LEO, MEO, GEO-like range/parallax | Existing snapshot IDs 300001–300003 at its own epoch | Freeze exact propagated states and independently checked transformation, source digests and domain flags. |
| S4–S5 | HEO perigee and apogee | **Missing** paired synthetic states on a single declared orbit | Freeze orbit/frame/epoch and independent propagation plus distance evidence; reject absent states. |
| P1–P4 | Waxing, waning, in-domain near 2° and near 90° | **Missing** distinct UTCs and independently constructed synthetic states | Freeze raw Cartesian components, model-domain classification and authoritative sign rule; no retrospective tuning. |
| F1–F3 | Both hemispheres, high latitude, nonzero libration, solar/observer longitude separation and ±180° wrap | **Missing** asymmetric state/epoch fixtures | Verify named-frame coordinate signs and circular differences. |
| X1–X3 | Unocculted, Earth-limb/fully occulted Moon, lunar eclipse | **Missing** geometric path fixtures | Record Earth/Moon/Sun radii and path/intercept assumptions, separate statuses, no invented radiometric correction. |
| C1 | Correction contrast | One identical frozen physical specimen with separate `NONE` and named corrected calculations | Show correction-dependent deltas without silently replacing baseline. |

Cases may serve multiple discriminants only with a row-by-row coverage map. Preselect UTCs inside SPK, PCK, IERS-A and LSK coverage and outside ill-conditioned singular configurations. Include out-of-domain examples only as geometry diagnostics, never admissible LIME predictions. The ten Phase-A manually entered LIME rows are interface evidence, not satellite-state geometry fixtures.

## LIME convention gate and residual receipt

The precise v1.4.2 direct `-l` argument mapping, sign of the moon phase, lunar frame/longitude, distance centre, body-fixed orientation epoch and correction semantics must be proven from pinned publisher source or documentation (tag commit `b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f`) and independently checked on nondegenerate waxing/waning and longitude cases. The [published CLI interface](https://github.com/LIME-ESA/lime_tbx) calls for a solar selenographic longitude in degrees; do not confuse it with a netCDF observational field expressed in radians. Preserve the exact input interface and link line-level source evidence in the follow-up amendment. Opposite-sign Phase-A central radiance equality cannot fix the phase sign. If source evidence is ambiguous, record `signed_phase_unresolved`; never flip a sign to make a table agree. LIME's EO-CFI satellite route remains excluded.

For each authorized run, write an external-only manifest with exact code and input revision, execution command, fixed case IDs/Cartesian states, physical UTC and ET, kernel/version/load order, file size and SHA-256, EOP/LSK identities, frames, correction flags, raw vectors/matrices, all component values, domain/path statuses, warnings, and raw output file hashes. Compute Wenu-minus-SPICE signed and absolute residuals separately for each component, circular longitude residuals, plus regime/correction summaries. State tolerances and their conditioning and uncertainty basis **before** inspecting residuals. A missing resource, uncovered epoch, unsupported frame, mixed centre/correction policy, unresolved LIME mapping, or absent HEO/phase specimen stops the run. A later candidate Wenu evaluator must be compared only after it separately exists and is authorized.

Geometry agreement alone does not admit LIME bands, uncertainties, license/redistribution, eclipse policy or Moonlight radiation. No dependency, runtime, command, coefficient, package, output, fixture, or model number is added in this milestone. The coordinate guide was reviewed; its implemented-coordinate explanations stay current because this protocol changes no runtime. The next decision is review of the resource/specimen/convention amendment, then a separate explicit authorization for a bounded controlled run. Moonlight remains `not_evaluated`.

## Accepted Phase B protocol boundary

Fernando scientifically and architecturally accepted exact tested candidate
`0ad4c6e67e37d9eb96f4278913c5871735937d27` on 2026-09-23.
On the Mac, 236 focused documentation/package tests passed in 10.67 seconds,
and all 2,873 plugin-disabled tests passed in 249.24 seconds. The exact-head,
ancestry, diff and clean-tree checks completed. This acceptance covers the
reviewable documentation protocol and its missing-resource/specimen/convention
stop gates. No lunar kernel download, SPICE comparison, LIME rerun, production
geometry, numerical Moonlight, or 50S.7D.4+ is authorized. The frozen-resource
amendment and controlled execution require separate review and authorization.
PR 192 merge and branch deletion remain separate decisions.

## Candidate Phase B source and specimen amendment (2026-09-23)

**Review status:** Source trace and deterministic specimen design only. The missing
kernel bytes and input rows cannot yet be called frozen. This amendment does
not supersede the accepted independent DE440 reference, authorize a download,
or authorize a SPICE/LIME run.

### Exact LIME source trace

At the official LIME Toolbox v1.4.2 tag commit
`b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f`:

| Claim | Pinned source and conclusion |
| --- | --- |
| Direct-interface units | [User guide, selenographic input](https://github.com/LIME-ESA/lime_tbx/blob/b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f/docs/content/user_guide/simulations.md#simulation-using-selenographic-coordinates) specifies Sun-Moon distance in au, observer-Moon distance in km, observer latitude/longitude and solar longitude in decimal degrees, phase in degrees. [CLI `run_lunar_simulation`, lines 675–718](https://github.com/LIME-ESA/lime_tbx/blob/b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f/lime_tbx/presentation/cli/cli.py#L675-L718) converts *solar longitude* with `np.radians` and retains both `abs(phase)` and signed phase. [CSV reader, lines 611–655](https://github.com/LIME-ESA/lime_tbx/blob/b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f/lime_tbx/application/filedata/csv.py#L611-L655) makes the same conversion. The internal radians field and observational netCDF field are not the CLI's input unit. |
| Orbit-derived geometry | [MoonDataFactory, lines 151–205](https://github.com/LIME-ESA/lime_tbx/blob/b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f/lime_tbx/application/simulation/moon_data_factory.py#L151-L205) sends satellite states through EOCFI and SPICE; [SPICEAdapter, lines 339–383](https://github.com/LIME-ESA/lime_tbx/blob/b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f/lime_tbx/business/spice_adapter/spice_adapter.py#L339-L383) calls the external `spicedmoon.get_moon_datas_xyzs` and enumerates `de421.bsp`, `moon_pa_de421_1900-2050.bpc`, `moon_080317.tf`, `pck00010.tpc`, `naif0011.tls` and Earth frame/orientation kernels. [Constants, line 12](https://github.com/LIME-ESA/lime_tbx/blob/b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f/lime_tbx/common/constants.py#L11-L12) names `MOON_ME`. This is a **DE421-family legacy path**, not evidence that direct `-l` inputs themselves specify a DE421 frame. Never execute the LIME satellite route for Wenu. |
| Delegated signed phase | [SPICEAdapter, lines 339–366](https://github.com/LIME-ESA/lime_tbx/blob/b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f/lime_tbx/business/spice_adapter/spice_adapter.py#L339-L366) receives `md.mpa_deg` from `spicedmoon` and stores its absolute value separately. [LIME dependency declaration](https://github.com/LIME-ESA/lime_tbx/blob/b28f1e87fdf98b3ee58c6b38bd0ccb55ca97047f/pyproject.toml) specifies `spicedmoon~=1.1`, not the bundled exact version or the sign equation. The tagged LIME code examined here does not establish which sign is waxing. Retain `signed_phase_unresolved` until exact bundled dependency bytes/source and an independent sign discriminator are recorded. |

The [spicedmoon publisher's package description](https://pypi.org/project/spicedmoon/)
lists the DE421 kernel family and describes a signed phase returned for
observer geometry, but does not itself pin LIME's bundled build or map the
sign to waxing/waning. Treat this as provenance context rather than an
independent orbit oracle.

### Two comparison columns, never mixed

| Column | Resource family and role | Stop condition |
| --- | --- | --- |
| Wenu reference | Installed `de440s.bsp` and separately verified DE440 lunar PCK/FK plus LSK/EOP; independent direct SPICE vectors and `MOON_PA_DE440`/`MOON_ME_DE440_ME421` diagnostics at one epoch with `NONE`. | Absent PCK/FK/LSK or out-of-coverage epoch; no silent substitution of DE421. |
| Historical LIME geometry | Exact v1.4.2 `spicedmoon` dependency, its actual DE421 SPK/lunar PCK/FK/LSK/Earth kernel identities and frame selection; source-reading comparison only unless later separately authorized. | Bundled dependency version or kernel bytes unknown; source names do not prove which files the installed binary selected. |

The *direct* `-l` call accepts six operator-supplied scalars; it does not
derive them from an orbit. The comparison must first establish LIME's
expected meaning of those scalars, then separately characterize DE421-vs-DE440
frame/ephemeris differences if historical LIME geometry is used as evidence.
Do not relabel a DE440 lunar vector as `MOON_ME` from the DE421 FK, and do not
make a numerical residual disappear by altering longitude or sign.

### Deterministic specimen construction

Retain existing hand-authored, non-operational snapshot
`synthetic_50s4b_v1` with `records.json` SHA-256
`2e5288a6aad9fbe29cfe6d9a60e0045be28501859d8c739135fd302460ece5fe`
and row IDs `300001`, `300002`, `300003` at their OMM epoch
`2026-09-15T00:00:00Z`. The separately verified propagated TEME states,
time/EOP conversion, frame and Earth-centre/units still have to be written
as explicit immutable rows; these OMM records are not J2000 Cartesian states.

Define *proposed* HEO-P/HEO-A synthetic Earth-centred inertial two-body
fixtures with gravitational parameter `mu = 398600.4418 km^3/s^2`, perigee
radius `rp = 7000 km`, apogee radius `ra = 42000 km`, semimajor axis
`a = (rp+ra)/2 = 24500 km`, and `t0 = 2026-09-15T00:00:00Z`.
HEO-P at `t0` has position `(rp,0,0) km` and velocity
`(0,+sqrt(mu*(2/rp-1/a)),0) km/s`. HEO-A at
`t0 + pi*sqrt(a^3/mu) seconds` has position `(-ra,0,0) km` and velocity
`(0,-sqrt(mu*(2/ra-1/a)),0) km/s`. The specified inertial axes must be
independently tied to SPICE `J2000` before reference comparison. These are
analytic idealizations, not propagated real satellite observations or a
general-perturbations OMM. Freeze an explicit timestamp, floating-point
serialization, coverage, and independent vis-viva/specific-energy check in
the future case file before using them.

For signed-phase, longitude, latitude, libration, eclipse and occultation
discriminants, freeze preselected UTCs and raw inertial state vectors in a
separate digest-bound case file *after* checking the exact kernel and EOP
coverage. Record a case-by-case requirement table before computing any
residual or tuning an input. Until those files exist, the rows P1–P4, F1–F3
and X1–X3 of the accepted protocol remain missing. No Phase-A opposite-sign
central radiance value resolves this provenance gap.

### Resource preflight to complete this amendment

The 2026-09-23 Mac inventory did not find the DE440 lunar PCK/FK,
`naif0012.tls`, or `pck00011.tpc` in its bounded paths. Their official
candidate publisher locations are respectively
[NAIF PCK](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de440_200625.bpc),
[NAIF FK](https://naif.jpl.nasa.gov/pub/naif/pds/wgc/kernels/fk/moon_de440_220930.tf),
[NAIF LSK](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls),
and [NAIF generic PCK](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc).
Read-only checks for already bundled or independently installed copies may
fill the inventory; URLs alone cannot fill byte count, SHA-256, coverage,
license or matching-frame proof. Before any acquisition, submit the exact
resources and controlled retrieval procedure for separate authorization;
before execution, freeze every required byte and case input for scientific
review. No geometry, LIME execution, kernel acquisition, dependency change,
production value or Moonlight admission occurs under this addendum.

### Read-only installed-app kernel receipt (2026-09-23)

Fernando inventoried `/Applications/LimeTBX.app/Contents` without opening the
app or invoking its executable. The installed executable was 15,074,016 bytes,
SHA-256 `cfaa059102688faa551a4a459d19f90f88e7cc9e68728e21002decb9d25908e3`;
the selected coefficient was 154,366 bytes, SHA-256
`8e6839d95315eb2d797484be559ad70b69010cc1eb9b614770f61bb5ce2cf691`.
Both match previously recorded Phase-A identities, **but this does not prove
the entire installed app is byte-identical to the verified `lime.pkg`**.

| Installed file under `Contents/Resources/kernels/` | Bytes | SHA-256 |
| --- | ---: | --- |
| `de421.bsp` | 16,790,528 | `08b20db2ae22488650641c5a9033e5bfda4b1c4b440cfeaf20f621cfa18ecdb3` |
| `earth_070425_370426_predict.bpc` | 5,751,808 | `0e5b9108a86c1d23894578cfd31c952e16c3b6712960208d1d3aa01d090f5062` |
| `earth_assoc_itrf93.tf` | 7,522 | `aab7bbc19b8a69bad11988ee1b4812a3963812a03a029c2776863e680719b336` |
| `earth_latest_high_prec.bpc` | 4,262,912 | `2b5bde55b5b34e172487cf1b984e92aa554a7c08fe326dd99cc759f937166b8f` |
| `moon_080317.tf` | 21,437 | `78732477b96f9863e7b0d65bcee3c22b8707ca5ed0db56d1173319cb2e8c7993` |
| `moon_pa_de421_1900-2050.bpc` | 1,770,496 | `656f90616403d75a75f0cd6c8830fc5b44f8cb4facb5ccb8915e752b397520cf` |
| `naif0011.tls` | 5,086 | `cdbb9adc1addca89b8d14347c2ad13e1e4ade1798aa731ad015c1ffa9bc40463` |
| `pck00010.tpc` | 126,143 | `59468328349aa730d18bf1f8d7e86efe6e40b75dfb921908f99321b3a7a701d2` |

This bounded inventory found none of the four DE440/time candidate files and
printed no `spicedmoon` Python-source or distribution metadata match. The
absence of that metadata in the selected paths does not show that the
packaged library is missing; it may be frozen or bytecode only. Do not infer
its version, phase-sign algorithm, or actual runtime kernel-selection path
from the filenames. A later read-only extraction of the already verified
`lime.pkg`, with a fresh package digest gate, can compare these kernel bytes
against the exact distribution without installing or executing LIME. A
publisher-backed sign rule and separate DE440 kernel receipt remain required
before any geometry execution.
