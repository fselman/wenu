# A physicist's guide to time in Wenu

Version 1 · 2026-11-03 · conceptual guide and agreed K4b.08 time-policy requirements

## Purpose and current status

This guide connects three ideas: the time parameter in dynamical equations,
the proper time measured by an atomic clock, and Earth's rotation angle
expressed as a time scale. It explains why Wenu keeps them distinct when
combining stellar motion, planetary ephemerides and a terrestrial observer.

Fernando requested this developer guide on 2026-11-03 and selected an
ephemeris-based TT–TDB realization, retaining equality and the full ERFA model
as optional, explicitly CLI-requestable alternatives. The selection is a
requirement for the new observer route, not an implemented CLI feature or a
change to existing modern defaults. See [the agreed selection](#agreed-wenu-time-policy).
The [roadmap](kernel_roadmap_v0.9.5.md#k4b08-selected-observer-contract-definition)
governs subsequent implementation scope and acceptance.

## Proper time and coordinate time

An ideal atomic clock measures proper time, τ, along its own worldline. Two
identical clocks on different trajectories, or at different gravitational
potentials, generally accumulate different elapsed times. The SI second is
realized locally by physical frequency standards; relativity tells us how to
compare separated clocks.

A coordinate time labels events throughout a chosen spacetime coordinate
system. It is the time variable that can appear in our equations of motion.
It need not equal the reading of a particular physical clock. In a weak-field,
slow-motion approximation, a clock's relation to a suitable coordinate time t
has the familiar leading form

```text
dτ/dt ≈ 1 − (U + v²/2)/c²,
```

where U is the positive Newtonian potential and v is the coordinate velocity.
The full metric supplies higher-order terms. Both the coordinate convention
and the clock's worldline matter; a statement that a clock “runs faster” needs
an identified comparison. See [the relativistic reference-system explanation](#references),
reference 1.

## TCB: the barycentric coordinate time

The Barycentric Celestial Reference System (BCRS) describes the Solar System
globally. Its spatial origin is the Solar System barycentre, and its time
coordinate is TCB, Barycentric Coordinate Time.

In a dynamical equation schematically written as

```text
d²x_i/dt² = F_i(x, v, t),
```

we may take t=TCB, with the positions, velocities, gravitational parameters and
relativistic terms consistently expressed in that system. The relativistic
reference system specifies more than just where we place a spatial origin.

“Barycentric” does not mean TCB is the reading of a clock placed at the
barycentre. Such a clock would still measure its own proper time, related to
TCB by its motion and the local metric. TCB labels events throughout the BCRS.
Reference 2 gives the IAU definitions of the BCRS and GCRS.

## TCG: the geocentric coordinate time

For phenomena near Earth, the Geocentric Celestial Reference System (GCRS)
uses an origin following Earth's centre of mass and kinematically nonrotating
axes. Its time coordinate is TCG, Geocentric Coordinate Time. TCG is not the
proper time of a hypothetical clock at Earth's centre either.

At the geocentre, the leading relationship has the schematic form

```text
dTCG/dTCB ≈ 1 − (v_E²/2 + U_external(x_E))/c².
```

Here v_E is Earth's barycentric velocity and the external potential includes
the Sun and other bodies, excluding Earth's own potential. Away from the
geocentre, position-dependent synchronization terms also enter. Integration
requires an origin convention, Earth motion and gravitational information.

There is a mean rate difference plus varying terms associated with Earth's
orbit and the other bodies. Thus the TCB–TCG connection involves a physical
Solar System model, not just a fixed numerical offset. References 1 and 3
explain this transformation; the displayed expression is not a complete
implementation formula.

## TT: terrestrial coordinate time with a chosen scale rate

Terrestrial Time, TT, is defined as a linear rescaling of TCG, with a specified
origin:

```text
dTT/dTCG = 1 − L_G,
L_G = 6.969290134 × 10⁻¹⁰ exactly.
```

The rate was chosen to closely match clocks on a conventional terrestrial
reference equipotential, approximately the rotating geoid. The modern
definition fixes L_G; it does not redefine TT whenever geoid knowledge changes.
TCG gains approximately 22 milliseconds per Julian year relative to TT,
calculated from the defining constant. This is a coordinate-rate difference.

TT is convenient for terrestrial astronomy and is the conventional argument
of precession/nutation models. It is continuous and is not adjusted by leap
seconds. References 4–6 cover TT, its realizations and its orientation use.

## Atomic time: TAI and realizations of TT

International Atomic Time, TAI, is a continuous scale produced by the BIPM
using atomic-clock data and frequency standards. Local clock readings require
relativistic rate corrections to contribute to a common terrestrial scale.
The conventional reference equipotential is part of that comparison; raw
readings from clocks at different heights cannot simply be averaged unchanged.

The usual atomic realization of TT is

```text
TT(TAI) = TAI + 32.184 seconds.
```

The 32.184 seconds preserves historical continuity with Ephemeris Time. It
changes the origin of the labels, not their rate, and is not a gravitational
time-dilation correction.

Distinguish the ideal defined TT from a practical realization. TT(TAI) inherits
TAI's realization errors. The retrospective TT(BIPM) realizations use more
complete frequency-standard information for demanding long-term work.
References 4 and 5 distinguish these concepts.

An ancient epoch can be expressed in TT even though there was no atomic clock
then. Mapping a historical observation or local clock indication to that TT
epoch is a separate inference, with its own uncertainty. Ancient observer
requests do not require an invented ancient TAI or UTC realization.

## TDB: rescaled barycentric coordinate time

Barycentric Dynamical Time, TDB, is a fixed linear rescaling of TCB, with a
specified origin and offset:

```text
dTDB/dTCB = 1 − L_B,
L_B = 1.550519768 × 10⁻⁸ exactly.
```

The scaling was chosen to keep TDB close to TT over extended intervals around
the present era, while providing a convenient barycentric ephemeris argument.
TCB gains approximately 0.49 seconds per Julian year relative to TDB. The
complete relation, including its offset, is defined by IAU 2006 Resolution B3
(reference 7); the rate equation alone is not enough to implement it.

TDB is not a second physical clock. Its current definition fixes its
relationship to TCB. TCB–TDB conversion is conventional arithmetic; TT–TDB
requires the physical connection between geocentric and barycentric coordinates.
Near the present era the remaining TT–TDB difference is mainly periodic and
of millisecond size. Strict periodicity for all epochs is not the definition.

TCB, TDB, TCG and TT can all be expressed using seconds and Julian dates.
Their differences are not a choice between unrelated units: they are different
coordinate labels/rates with explicitly defined relationships. An identical
numerical JD in two scales generally denotes different events.

Changing a dynamical calculation to TDB-compatible conventions requires
consistent spatial and gravitational-parameter scaling as well. It is unsafe
to change the time label while keeping incompatible state conventions.
For the conventional matching TCB/TDB scalings, position scales by (1−L_B)
and coordinate velocity is unchanged because space and time scale together.
This scaling is distinct from the full geocentric/barycentric transformation.
See reference 8 and Wenu's [implemented convention seam](implementation_reference.md#barycentric-time-and-coordinate-conventions).

## UT1: Earth's spin expressed as time

UT1 expresses Earth's spin angle, whether or not its rotation is uniform
relative to atomic time. Modern UT1 is linearly related by definition to the
Earth Rotation Angle (ERA). Schematically,

```text
ERA = ERA_reference + nominal_rate × UT1,
```

with a defined origin and an unwrapped rotation count before reduction modulo
one turn. This does not assume uniform rotation against TT. Irregular rotation
appears in the nonuniform relationship between UT1 and TT. Equivalently, one
could describe the spin directly by an angle θ(TT).

The connection used for historical work is

```text
ΔT = TT − UT1.
```

This involves Earth-rotation observations or a model of rotational history,
including geophysical effects. It is not the same problem as relativistic
clock conversion. UT1 supplies the spin angle; pole direction and polar motion
are additional parts of the complete orientation. Reference 9 explains the
rotation definition.

UTC is the civil dissemination scale related to atomic time with the applicable
published integer-second offsets. It is neither the smooth time argument we
want for dynamical integration nor a reconstruction of ancient local clocks.
Its applicable rules/resources must be admitted explicitly. This guide does
not prescribe an ancient or distant-future UTC convention.

## How the concepts connect

| Quantity | Role | Connection |
|---|---|---|
| Proper time τ | Reading of an ideal local clock | Clock worldline and spacetime metric |
| TCB | Barycentric coordinate time | BCRS definition |
| TDB | Rescaled barycentric coordinate time | Exact linear definition from TCB |
| TCG | Geocentric coordinate time | Relativistic transformation from the BCRS |
| TT | Rescaled geocentric coordinate time | Exact linear definition from TCG |
| TAI | Practical atomic realization of terrestrial time | Clock comparisons, standards and relativistic corrections |
| UT1 | Earth spin angle expressed as time | Rotation observations or a rotational-history model |
| UTC | Civil time dissemination | Applicable published atomic-time offsets and civil conventions |

There are two independent connections for Wenu:

- TT ↔ TDB ↔ TCB connects orientation, planetary and stellar time arguments.
- TT ↔ UT1 connects the observing epoch to Earth's spin angle.

Improving the first does not reconstruct ancient rotation. Improving the second
does not replace a relativistic conversion. A planetary ephemeris can support
the first without supplying the actual historical rotation required by the second.

## Agreed Wenu time policy

Fernando selected the following requirements on 2026-11-03: “Accept going the
third way but 1 and 2 should be optional and requestable through the CLI.”
The numbering refers to the alternatives discussed in the scientific review.

| Review option | Meaning | Agreed role for the new observer |
|---|---|---|
| 3: ephemeris-based | Compute TT–TDB from an admitted ephemeris-based relativistic time calculation, or evaluate an admitted prepared time ephemeris | Selected primary/default approach |
| 1: TT=TDB | Deliberately use the same numerical time label as an approximation | Optional, explicitly requestable through the future CLI |
| 2: full ERFA model | Use the full Fairhead–Bretagnon TT–TDB model through ERFA, with explicit location treatment | Optional, explicitly requestable through the future CLI |

All three must remain named, distinguishable model policies. Equality is an
explicit approximation, not an exact relativistic conversion. The analytical
model's stated modern accuracy does not qualify it over J−13000..J+13000.
ERFA documents its comparison interval and the distinction between the model
and numerical ephemeris integration (reference 10).

CLI requestability is an agreed requirement, not existing syntax. The option
name and accepted values must be defined and tested in the later bounded
implementation. No runnable flag is documented here. Selection must flow
through the shared time/observer service, with equivalent Python inputs;
the CLI must not implement another numerical engine.

The selected route must record exact input/output split dates, time scales,
policy/version, actual model/resource/code identity, finite coverage, location
convention and separate numerical/physical/source-time uncertainties. Unknown
errors stay unknown. Do not silently use option 1 or 2 when option 3 lacks a
required resource, refuses a date or fails evaluation. Optional routes require
explicit selection and their own coverage/error admissions. Existing modern
Observer/Astropy/final-IERS defaults are unchanged by this new-route selection.

For option 3, an Earth/Sun position SPK is not evidence that a TT–TDB time
segment is present. Inspect the actual resource contents and supported domains.
Choose a compatible time ephemeris or an explicitly qualified calculation with
its required bodies, constants, integration origin and numerical controls.
JPL describes its time transformation in the DE440/DE441 paper (reference 11).
Specific resources, acquisition, integration algorithm, geocentric/site term,
supported interval and numerical qualification still need a bounded design.
Selecting the approach does not establish universal ancient accuracy or authorize
new downloads, long numerical workloads or silent extrapolation.

This time selection is distinct from spatial composition. Fernando subsequently
selected the standard IAU post-Newtonian spatial formulation within GR,
β=γ=1. Concrete retained order/terms still require design/qualification;
adjustable PPN deviations are not selected. JPL already supplies Earth-centre
orbital PV; site motion must derive consistently from the same fixed-site,
orientation and spacetime transformation. The
[observer velocity definition](research/earth_bound_observer_contract_v1.md#site-velocity-definition-and-existing-inputs)
records this boundary, local derivative identities and rate/domain refusal
rules. Numerical rate construction, apparent corrections and product adoption
remain separate; none is implemented by this guide.

## Concrete realization review

The [TT–TDB design review](research/tt_tdb_realization_design_v1.md) now owns the resource assessment and proposed
split-date calculation. It distinguishes a published DE440 time-series candidate
from retained position-only resources and unresolved long-span time admission.
It also separates geocentric mapping from the site's relativity-of-simultaneity
term and identifies the existing SDK's finite-numerical-bound requirement.
The proposed first geocentric implementation is not selected; this guide's
agreed three-policy requirement and modern-default preservation remain current.

## Implemented Wenu seams and remaining work

| Owner | Current behavior to preserve | Remaining boundary |
|---|---|---|
| `astrometric_coordinates.py`: `TcbTdbAdapter` | Explicit linear TCB/TDB conversion and receipts | Does not supply TT/TDB |
| Same owner: `HistoricalDate`, `resolve_historical_date` | Explicit calendar/year numbering/scale and chronology evidence; existing resolver targets TCB through admitted conversion | No invented ancient UTC or implicit arbitrary TT/TCB conversion |
| Same owner: `NominalEarthOrientation.evaluate` | Exact split TT, named R1 split UT1 and full R3 orientation receipts | Does not supply site PV or TT/TDB |
| `earth_rotation.py`: `EarthRotationModel` | Selected Espenak–Meeus ΔT with finite coverage and extrapolation disclosure | No claim to measured ancient rotation or a derivative/rate contract |
| `astrometric_observation.py`: `ErfaReceptionBackend` | Existing resource-bound modern reception including DTDB/EPV00/final IERS | Its admission limits remain unchanged; not the new remote-epoch route |
| `ephemeris_companion.py`: `EphemerisCompanion.at` | Verified exact TDB Earth-centre/Sun states | No implicit TT event link or time-ephemeris capability |

These interfaces are described in the [implementation reference](implementation_reference.md).
The [coordinate guide](coordinate_system_guide_v0.9.5.md#5-time-vocabulary)
retains calendar/epoch/reference details; this guide owns the physical time-scale
explanation and agreed three-option policy. The [scientific contracts](scientific_contracts.md#planned-ancient-and-future-earth-bound-observers)
and roadmap preserve qualification and implementation limits.

Later acceptance must distinguish arithmetic identities from model comparisons:
test exact TCB/TDB definitions, input/event bindings, forward/inverse TT/TDB
round trips, independent ephemeris references, actual resource coverage and
failure behavior. A round trip alone cannot prove physical correctness.
Compare options 1 and 2 against option 3 at admitted modern/ancient/future
events and report effects on requested directions without inventing a universal
bound. CLI/Python selection, provenance, explicit approximations, no fallback
and request isolation need public-path tests before CLI availability is claimed.
No such new numerical or CLI result is claimed by this documentation update.

## References

Primary sources checked 2026-11-03; no ephemeris acquisition is performed by
this guide or its documentation tests.

1. [Soffel et al. (2003), The IAU 2000 resolutions for astrometry, celestial mechanics and metrology in the relativistic framework](https://arxiv.org/html/astro-ph/0303376v1): coordinate/proper time, metrics and transformations.
2. [IAU 2000 resolutions B1.3/B1.5/B1.9](https://syrte.obspm.fr/IAU_resolutions/Resol-UAI.htm): barycentric/geocentric systems and TT definition.
3. [IERS: relationship between TCG and TCB](https://www.iers.org/iers/en/service/faqs/thenewiauresolutions/relationshipbetweentcg-tcb-104-158): orbital velocity, external potential and time transformation.
4. [CGPM Resolution 2 (2018), On the definition of time scales](https://www.bipm.org/en/committees/cg/cgpm/26-2018/resolution-2): TT, TAI, reference potential and UTC.
5. [BIPM: Terrestrial Time and TT(BIPM)](https://www.bipm.org/en/time-department/tt): ideal scale versus practical realizations.
6. [IERS: time argument for IERS products](https://www.iers.org/iers/en/service/faqs/time/whatithetimeargumentforusingiersproducts-157): TT argument for precession/nutation.
7. [IAU 2006 Resolution B3](https://iauarchive.eso.org/static/resolutions/IAU2006_Resol3.pdf): complete defining TCB/TDB relation and constants.
8. [Fienga et al. (2016), GAIA DPAC INPOP final release: INPOP10e, IMCCE Note S104](https://www.imcce.fr/content/medias/publications/publications-recherche/nst/docs/S104.pdf): consistent TCB/TDB state scaling.
9. [IERS explanatory supplement to Bulletins A and B](https://iers.obspm.fr/eoppc/bul/bulb/explanatory.pdf): UT1, ERA and Earth-orientation quantities.
10. [ERFA `dtdb.c`, SOFA-derived implementation notes](https://github.com/liberfa/erfa/blob/master/src/dtdb.c): full Fairhead–Bretagnon model, location term and stated comparison limits.
11. [Park et al. (2021), The JPL Planetary and Lunar Ephemerides DE440 and DE441, Section 2.3](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440_and_de441.pdf): ephemeris coordinate time and relativistic TT/TDB transformation.
