# Wenu Coordinate Systems and Astronomical Objects

**Subtitle:** Living scientific and implementation guide for architecture 0.9.5  
**Author:** Wenu project  
**Architecture version:** `0.9.5`  
**Guide version:** `0.9.5.20260831.30`  
**Last updated:** `2026-08-31T12:10:00Z`  
**Language:** English

# Table of contents

- [Status and purpose](#status-and-purpose)
- [How to read the depth markers](#how-to-read-the-depth-markers)
- [1. Scientific vocabulary](#1-scientific-vocabulary)
  - [1.1 A position is more than two angles](#11-a-position-is-more-than-two-angles)
  - [1.2 Position generation versus coordinate transformation](#12-position-generation-versus-coordinate-transformation)
- [2. Coordinate systems used or reserved by Wenu](#2-coordinate-systems-used-or-reserved-by-wenu)
  - [2.1 ICRS](#21-icrs)
    - [2.1.1 Gaia-CRF3](#211-gaia-crf3)
  - [2.2 FK5 equatorial coordinates](#22-fk5-equatorial-coordinates)
  - [2.3 Galactic coordinates](#23-galactic-coordinates)
  - [2.4 Ecliptic coordinates](#24-ecliptic-coordinates)
  - [2.5 Horizontal AltAz coordinates](#25-horizontal-altaz-coordinates)
  - [2.6 TEME and Earth-fixed frames](#26-teme-and-earth-fixed-frames-reserved-for-satellites)
  - [2.7 Equinox applicability by system and frame](#27-equinox-applicability-by-system-and-frame)
- [3. Origins and position status](#3-origins-and-position-status)
  - [3.1 Origins](#31-origins)
  - [3.2 Position states](#32-position-states)
- [4. Mathematical foundations](#4-mathematical-foundations)
  - [4.1 Spherical and Cartesian representation](#41-spherical-and-cartesian-representation)
  - [4.2 Orthogonal frame rotations](#42-orthogonal-frame-rotations)
  - [4.3 Local sidereal angle](#43-local-sidereal-angle)
  - [4.4 Topocentric parallax](#44-topocentric-parallax)
  - [4.5 Stellar space motion](#45-stellar-space-motion)
- [5. Time vocabulary](#5-time-vocabulary)
  - [5.1 Calendars as historical coordinates](#51-calendars-are-historical-coordinate-systems-for-time)
  - [5.2 Sumer, Babylonia, Egypt, and Greece](#52-from-sumer-and-babylonia-to-egypt-and-greece)
  - [5.3 Roman, Julian, and Gregorian calendars](#53-roman-julian-and-gregorian-calendars)
    - [5.3.1 Did Augustus steal a day from February?](#531-did-augustus-steal-a-day-from-february)
  - [5.4 A historian's minimum date record](#54-a-historians-minimum-date-record)
  - [5.5 Year numbering, day counts, and astronomical time](#55-year-numbering-day-counts-and-astronomical-time)
  - [5.6 Julian and Besselian epochs](#56-julian-and-besselian-epochs-are-not-calendars)
    - [5.6.1 Tropical, sidereal, and Besselian years](#561-tropical-sidereal-and-besselian-years)
  - [5.7 Present Wenu boundary and future support](#57-present-wenu-boundary-and-future-historical-date-support)
  - [5.8 Sources and limits](#58-sources-and-limits)
- [6. Transformation inventory and destination](#6-current-transformation-inventory-and-095-destination)
- [7. Proposed 0.9.5 contracts](#7-proposed-095-contracts)
  - [7.1 CoordinateSpec](#71-coordinatespec)
  - [7.2 ObservationContext](#72-observationcontext)
  - [7.3 PositionProvider](#73-positionprovider)
  - [7.4 CoordinateService](#74-coordinateservice)
- [8. Wenu object catalogue and provenance](#8-wenu-object-catalogue-and-provenance)
  - [8.1 Astronomical objects](#81-astronomical-objects)
  - [8.2 Constructed and cultural/reference objects](#82-constructed-and-culturalreference-objects)
  - [8.3 Provenance requirements](#83-provenance-requirements)
- [9. Verification requirements](#9-verification-requirements)
- [10. Minimal architecture 0.9.5 roadmap](#10-minimal-architecture-095-roadmap)
  - [10.1 Architecture 0.9.5 acceptance](#101-architecture-095-acceptance)
- [11. Review questions for Fernando](#11-review-questions-for-fernando)
- [12. Maintenance rule](#12-maintenance-rule)
- [13. Practical guide to reference systems, equinoxes, and epochs](#13-practical-guide-to-celestial-reference-systems-equinoxes-and-epochs)
  - [13.1 Public celestial reference policy](#public-celestial-reference-policy)
    - [13.1.1 Coordinate system versus reference frame](#coordinate-system-vs-reference-frame)
    - [13.1.2 Equinox versus position epoch and observation instant](#epoch-vs-equinox)
    - [13.1.3 Requesting a reference equinox](#requesting-reference-equinox)
    - [13.1.4 Julian and Besselian year labels](#julian-besselian-labels)
    - [13.1.5 Gaia position reference epoch is not an equinox](#gaia-epoch-not-equinox)
    - [13.1.6 Implementation and scientific acceptance](#reference-policy-acceptance)
  - [13.2 Scene dependencies and moving astronomical objects](#moving-object-architecture)
    - [13.2.1 49D.1 scientific and pedagogical acceptance](#49d1-acceptance)
    - [13.2.2 49D.2 minimal realization handoff](#49d2-handoff)
    - [13.2.3 49D.2 scientific and pedagogical acceptance](#49d2-acceptance)
    - [13.2.4 49E.1 ephemeris-provider design](#49e1-provider-design)
    - [13.2.5 49E.2 minimal runtime state contracts](#49e2-runtime-contracts)
    - [13.2.6 49E.3 borrowed Skyfield kernel adapter](#49e3-skyfield-adapter)
    - [13.2.7 NAIF and SPICE identifiers](#naif-spice-identifiers)
    - [13.2.8 49E.4 observer-relative direction audit](#49e4-direction-audit)
    - [13.2.9 49E.5 astrometric direction runtime](#49e5-astrometric-runtime)
    - [13.2.10 49E.6 apparent direction runtime](#49e6-apparent-runtime)
    - [13.2.11 49I.1 drawable Venus audit](#49i1-venus-audit)
    - [13.2.12 49I.1A ordinary realization context](#49i1a-realization-context)
    - [13.2.13 49I.1B first drawable Venus](#49i1b-venus-layer)
    - [13.2.14 49I.2 Moon and shared body pipeline](#49i2-moon-shared-pipeline)
    - [13.2.15 49I.2A numerical Moon direction](#49i2a-moon-direction)
    - [13.2.16 49I.2B shared Solar-System point layer](#49i2b-shared-point-layer)
    - [13.2.17 49I.2C first drawable Moon point](#49i2c-moon-point)
    - [13.2.18 49I.2D Solar-System trajectories](#49i2d-solar-system-tracks)
    - [13.2.19 49I.2D.1 scientific track curve](#49i2d1-track-curve)

<a id="status-and-purpose"></a>

# Status and purpose

**Status:** Living accepted edition; architecture 0.9.5 merged in `1a15076`; public celestial-reference policy implemented and scientifically accepted on its review branch.

This is the living scientific guide for Wenu's coordinate systems,
transformations, astronomical objects, and constructed celestial references.
It has four purposes:

1. state what every coordinate value means;
2. preserve the equations and conventions required to understand the system;
3. map every operation to its present and intended code owner;
4. record where Wenu's astronomical and reference objects come from.

The guide is normative about scientific meaning. Astropy/ERFA remains the
numerical authority for standards-based transformations; equations reproduced
here explain and audit those transformations and must not become competing
approximate production implementations.

<a id="how-to-read-the-depth-markers"></a>

## How to read the depth markers

This guide is both Wenu's scientific reference and a teaching document.
Coordinate material uses two complementary depth markers:

- **[Foundation]** gives the high-school-level physical picture and the
  vocabulary needed to request a scientifically meaningful chart.
- **[Undergraduate]** adds the astronomical definition, mathematical
  distinction, and Wenu implementation consequence.

The undergraduate explanation extends the foundation explanation; it does not
replace or contradict it. A reader may follow only the foundation paragraphs
on a first reading and return to the undergraduate material later.

<a id="1-scientific-vocabulary"></a>

# 1. Scientific vocabulary

<a id="11-a-position-is-more-than-two-angles"></a>

## 1.1 A position is more than two angles

Every astronomical coordinate record must identify, where applicable:

- coordinate system and representation;
- reference frame and its physical realization;
- coordinate origin;
- equinox, only for a frame whose axes are equinox-based;
- position reference epoch, only for a catalogue state or motion model;
- evaluation or observation instant and its time scale;
- observer location;
- geometric, astrometric, apparent, or observed status;
- angular units and representation;
- physical model and data provenance.

Two arrays called longitude and latitude are not interchangeable merely
because both are measured in degrees.

<a id="12-position-generation-versus-coordinate-transformation"></a>

## 1.2 Position generation versus coordinate transformation

A **PositionProvider** answers:

> Where is this astronomical object at this physical instant, according to
> this catalogue, ephemeris, or orbit model?

A **CoordinateService** answers:

> How is that explicit position represented in the requested coordinate
> system?

The provider does not project or render. The coordinate service does not
calculate an orbit or choose an ephemeris. Both return or consume existing
`Spherical*` geometry carrying an immutable `CoordinateSpec`.

Constructed references—grids, equators, ecliptics, planes, and poles—are not
astronomical objects. They are generated by a separate reference-geometry
boundary and enter the same geometry and coordinate service afterward.

<a id="2-coordinate-systems-used-or-reserved-by-wenu"></a>

# 2. Coordinate systems used or reserved by Wenu

<a id="21-icrs"></a>

## 2.1 ICRS

The International Celestial Reference System is the IAU-defined ideal
celestial coordinate system and Wenu's intended observer-independent
celestial interchange frame. Its origin is the Solar System barycentre. Its
axes are kinematically non-rotating with respect to the distant Universe and
are realized observationally by catalogued extragalactic sources. Right
ascension \(\alpha\) and declination \(\delta\) are spherical coordinates in
this system. ICRS is not simply “J2000 coordinates”: its axes are close to the
mean equator and equinox of J2000, but ICRS is not defined by Earth's equator,
equinox, or a caller-selected date.

More precisely, the ICRS origin of right ascension was chosen to lie close to
the dynamical mean equinox of J2000.0, in order to preserve continuity with
older catalogues. It is nevertheless an independently realized, fixed
direction and is measurably offset from that dynamical equinox by the frame
bias. Therefore ICRS does not have a **defining equinox**, fixed or selectable;
it has a fixed right-ascension origin whose historical alignment is near the
J2000.0 equinox. The IERS conventions report an offset of about 55.4
milliarcseconds between the ICRS right-ascension origin and the inertial mean
equinox of J2000.0 when compared on the ICRS reference plane.

A **system** is the ideal definition; a **reference frame** is a practical
realization of its axes from measured sources. ICRF3 is the third radio
realization of ICRS, based principally on VLBI positions of compact
extragalactic radio sources. Gaia-CRF3 is its optical realization from Gaia
EDR3/DR3 quasars. They realize the same ICRS at different wavelengths rather
than defining independent longitude/latitude systems.

Current uses include Hipparcos catalogue positions, non-stellar catalogue
centres and outlines, constellation data, Milky Way isophotes, and the
intermediate representation of several constructed references.

<a id="211-gaia-crf3"></a>

### 2.1.1 Gaia-CRF3

Gaia-CRF3 is the celestial reference frame for positions and proper motions
in Gaia EDR3 and DR3. Its non-rotating optical axes are established from
quasar-like extragalactic sources. Its orientation was aligned to the radio
ICRF3 through sources detected in common. Thus Gaia-CRF3 is a high-precision
optical realization of ICRS, not a new equatorial system with a Gaia
equinox.

Gaia catalogue stars are measured relative to this frame. Their five- or
six-parameter astrometric solutions carry a **position reference epoch**:
J2015.5 for Gaia DR2 and J2016.0 for Gaia EDR3/DR3. That epoch states when a
star's tabulated position and proper-motion model are referenced. It does not
orient the ICRS axes and is not an equinox.

Wenu currently represents Gaia-compatible celestial geometry as `icrs` and
would record a Gaia release, position reference epoch, and provider identity separately
in `CoordinateSpec`. It does not currently expose `gaia-crf3` as an independent
transformable frame or provide Gaia epoch propagation. Those require a future
Gaia position-provider milestone; merely changing a frame label would lose
the scientific distinction.

<a id="22-fk5-equatorial-coordinates"></a>

## 2.2 FK5 equatorial coordinates

FK5 is the Fifth Fundamental Catalogue and the older star-catalogue-based
equatorial reference frame that replaced FK4. Its conventional coordinates
are tied to a modeled mean equator and equinox and use an explicit precession
model. `FK5(equinox=J2000.0)` is close to ICRS but is not identical to it.
Unlike ICRS, FK5 may be represented for another equinox by precessing its
axes. Wenu currently permits ICRS or FK5 equatorial grids. An FK5 coordinate
must therefore carry its equinox; it must never be labelled only
“equatorial,” and an ICRS coordinate must not be given an FK5 equinox.

<a id="23-galactic-coordinates"></a>

## 2.3 Galactic coordinates

Galactic longitude \(l\) and latitude \(b\) use the IAU Galactic system as
realized by Astropy. The standard ICRS-to-Galactic direction-cosine matrix is
approximately

\[
R_{G\leftarrow I} =
\begin{bmatrix}
-0.0548755604 & -0.8734370902 & -0.4838350155\\
 0.4941094279 & -0.4448296300 &  0.7469822445\\
-0.8676661490 & -0.1980763734 &  0.4559837762
\end{bmatrix}.
\]

For an ICRS unit vector \(\mathbf r_I\),
\(\mathbf r_G=R_{G\leftarrow I}\mathbf r_I\), followed by the spherical
recovery equations in Section 4.1. Production code delegates the authoritative
realization to Astropy rather than embedding this rounded matrix.

<a id="24-ecliptic-coordinates"></a>

## 2.4 Ecliptic coordinates

Ecliptic longitude \(\lambda\) and latitude \(\beta\) require an explicit
ecliptic definition, origin, and equinox/date. Wenu currently uses:

- `BarycentricMeanEcliptic(equinox=...)` when a product explicitly requests
  the supported mean-ecliptic frame;
- `BarycentricTrueEcliptic(equinox=...)` for ecliptic reference geometry.

These are not interchangeable. Architecture 0.9.5 carries the choice in
`CoordinateSpec`; `Observer` no longer owns an implicit ecliptic frame. The
canonical celestial-reference furniture uses one coherent policy for the FK5
equatorial grid and equator, barycentric true ecliptic, and all four seasonal
keypoints. The public default is J2000; an explicit `of_date` or other
supported equinox changes the complete reference set coherently rather than
one component.

For the elementary mean-equator rotation with obliquity \(\epsilon\),

\[
\begin{aligned}
\cos\delta\cos\alpha &=
  \cos\beta\cos\lambda,\\
\cos\delta\sin\alpha &=
  \cos\beta\sin\lambda\cos\epsilon
  -\sin\beta\sin\epsilon,\\
\sin\delta &=
  \cos\beta\sin\lambda\sin\epsilon
  +\sin\beta\cos\epsilon.
\end{aligned}
\]

Thus

\[
\alpha=\operatorname{atan2}(y,x),\qquad
\delta=\arcsin(z).
\]

The inverse uses the transpose of the orthogonal rotation. Nutation and the
precise mean/true ecliptic definitions are delegated to Astropy/ERFA.

<a id="25-horizontal-altaz-coordinates"></a>

## 2.5 Horizontal AltAz coordinates

Horizontal coordinates are observer-local. Wenu stores azimuth \(A\) and
altitude \(a\), with Astropy's azimuth convention: zero at geographic north,
increasing eastward. A horizontal coordinate is incomplete without site,
instant, Earth-orientation information, and an atmospheric/refraction policy.

Let latitude be \(\phi\), local apparent or sidereal hour angle be
\(H=\theta_{L}-\alpha\), and declination be \(\delta\). The elementary
geometric transformation is

\[
\sin a =
  \sin\delta\sin\phi+
  \cos\delta\cos\phi\cos H,
\]

and, for the north-through-east azimuth convention used by the current
handwritten function,

\[
A=\operatorname{atan2}
\left(
 -\sin H\cos\delta,
 \sin\delta\cos\phi-
 \cos\delta\sin\phi\cos H
\right) \bmod 2\pi.
\]

The retired pre-49C.3 `radec_to_altaz()` used
\(\theta_L=15^\circ(\mathrm{GMST}+\mathrm{longitude}/15^\circ)\).
It omitted the fuller apparent-place and Earth-orientation chain. The equation
is retained here as historical audit evidence, not production authority.

<a id="26-teme-and-earth-fixed-frames-reserved-for-satellites"></a>

## 2.6 TEME and Earth-fixed frames reserved for satellites

Artificial-satellite providers may produce TEME states from SGP4. TEME is not
ICRS and must never be relabelled as ordinary equatorial coordinates. A
satellite path requires explicit TEME-to-Earth-fixed/celestial transformation,
UT1 and polar-motion information where required, and a topocentric observer
step. Architecture 0.9.5 reserves this through `CoordinateSpec`; it does not
implement satellite propagation.

<a id="27-equinox-applicability-by-system-and-frame"></a>

## 2.7 Equinox applicability by system and frame

**[Foundation]** An equinox is relevant only when a coordinate frame uses the
intersection of an equator and an ecliptic to define the zero direction of
longitude or right ascension. Other frames obtain their axes from distant
sources, the Milky Way, the observer's horizon, or Earth itself. For those
frames, “not applicable” is more accurate than supplying an invented equinox.

| System or frame | Defining equinox | Can a Wenu request select it? | What fixes the axes instead? |
| --- | --- | --- | --- |
| ICRS | None; its fixed RA origin is historically close to, but not identical with, the J2000.0 dynamical equinox | No | ICRS definition and its extragalactic realizations |
| ICRF3 | None | No | VLBI radio-source realization of ICRS |
| Gaia-CRF3 | None | No | Optical quasar realization of ICRS, aligned to ICRF3 |
| FK5 equatorial | Mean equator and equinox at a stated Julian date | Yes, for reference geometry | FK5 precession model at that equinox |
| FK4 equatorial | Mean equator and equinox at a stated Besselian date | Not in this public milestone | FK4 conventions and precession model |
| Barycentric mean/true ecliptic | A stated equinox/date defines the ecliptic orientation and longitude origin | Yes, through the coupled reference policy | Selected mean or true ecliptic definition |
| Galactic | None | No | Fixed IAU Galactic pole and longitude-zero direction |
| GCRS | None as a defining frame parameter | No | Geocentric relativistic system kinematically aligned to ICRS |
| Horizontal AltAz | None | No | Observer's local vertical, geographic north, site, and observation instant |
| TEME | Mean equinox associated with the state time; not an independently chosen publication equinox | No | SGP4/TEME state and its evaluation instant |
| Earth-fixed frames | None | No | Terrestrial pole, reference meridian, Earth rotation, and Earth-orientation data |

**[Undergraduate]** “Related to the J2000 equinox” does not mean “defined by
the J2000 equinox.” The ICRS axes were placed near the FK5 J2000 orientation
for continuity, but the ICRS right-ascension origin and pole are independent
fixed directions. The small rotation between ICRS/GCRS axes and the dynamical
mean equator and equinox of J2000.0 is the frame bias. FK5 and ecliptic frames,
by contrast, accept equinox as part of their frame construction. TEME is a
special case whose name includes “mean equinox,” but that equinox follows the
state time and SGP4 convention; it is not Wenu's selectable celestial-reference
equinox.

> ### Concept box — How an abstract celestial sphere becomes a measured frame
>
> **[Foundation]** A spherical coordinate system begins as a geometrical idea:
> choose a centre, a north pole, a zero-longitude direction, and an angular
> scale. That is not yet enough to point a telescope. The axes must be attached
> to observable directions in the real sky. Very distant quasars are especially
> useful because their transverse motions are normally negligible for this
> purpose. Stars can also transfer the frame to users, provided their positions
> and motions are measured and propagated to a stated epoch.
>
> The observatory does not directly read a perfect right ascension and
> declination. A radio interferometer measures signal-arrival delays between
> antennas. Gaia measures the times and angles at which source images cross its
> detectors while the spacecraft scans. A mathematical observation model asks:
> “For proposed source coordinates, observer position, instrument orientation,
> and calibration, what delay or detector angle should have been measured?”
> The parameters are adjusted until the predictions fit millions or billions
> of observations as well as possible.
>
> **[Undergraduate]** Schematically, the residual vector is
>
> \[
> \boldsymbol r = \boldsymbol y_{\rm observed}
> - \boldsymbol f(\boldsymbol s,\boldsymbol a,\boldsymbol c,
>                  \boldsymbol g,\boldsymbol t),
> \]
>
> where \(\boldsymbol s\) contains source positions, parallaxes, and proper
> motions; \(\boldsymbol a\) describes antenna geometry or spacecraft attitude;
> \(\boldsymbol c\) contains instrument and propagation calibrations;
> \(\boldsymbol g\) contains global physical parameters; and
> \(\boldsymbol t\) represents observation times and observer ephemerides. A
> weighted least-squares or iterative block solution minimizes
> \(\boldsymbol r^{T}W\boldsymbol r\), estimates covariances, rejects or
> downweights unsuitable observations, and repeats after calibration updates.
>
> A purely internal solution can be rotated without changing its predicted
> relative angles. Proper-motion solutions can similarly acquire a rigid spin.
> Least squares alone therefore does not determine the absolute orientation and
> non-rotation of the sphere. Datum constraints remove these null directions:
> for example, a **no-net-rotation** condition on defining quasars, or a fit of
> common optical/radio quasars to an existing frame. Coordinates of the
> reference sources and orientation of the axes are consequently solved as
> coupled parts of one global problem, not as two completely independent steps.
>
> The observation model must also remove effects that change the measured ray
> without representing source motion. Depending on the experiment these include
> the observer's barycentric velocity and **stellar aberration**; gravitational
> deflection by the Sun, planets, and sometimes higher multipoles; annual
> parallax; light-time; relativistic time transformations; spacecraft or Earth
> ephemerides; precession and nutation when moving equator/equinox frames are
> involved; Earth rotation and polar motion; atmospheric refraction for optical
> ground observations; and tropospheric, ionospheric, clock, and antenna effects
> for radio interferometry. The adopted corrections are part of the frame's provenance, not cosmetic plotting options.
>
> #### How the principal frames are realized or constructed
>
> | Frame/system | How its orientation is obtained in practice |
> | --- | --- |
> | ICRS/ICRF3 | **Very Long Baseline Interferometry (VLBI)** group delays from compact radio quasars are globally adjusted together with station, clock, atmosphere, and Earth-orientation parameters. Defining sources and no-net-rotation constraints maintain the ICRS axes. |
> | Gaia-CRF3 | Gaia's **Astrometric Global Iterative Solution (AGIS)** alternates least-squares blocks for source astrometry, spacecraft attitude, instrument calibration, and global parameters. Quasars suppress frame spin; optical sources common with ICRF3 set the orientation. Ordinary Gaia stars then carry this frame through their positions and proper motions at the catalogue epoch. |
> | FK5/FK4 | These historical fundamental frames were assembled from selected stars observed by meridian and other catalogues. Catalogue systematic corrections, proper motions, precession constants, and equator/equinox constraints produced the published fundamental-star realization. FK5 means **Fifth Fundamental Catalogue**; FK4 is its predecessor. |
> | Galactic | The modern Galactic axes are a conventional fixed rotation of ICRS. Wenu/Astropy applies that adopted rotation; it does not refit the Milky Way or a new beacon catalogue for each chart. |
> | Mean/true ecliptic | The axes are mathematically constructed from an adopted equatorial frame and modeled orbital/ecliptic orientation at the stated equinox. “True” additionally includes the applicable short-period orientation terms. This is a dynamical construction rather than a new least-squares beacon frame. |
> | GCRS | The **Geocentric Celestial Reference System** is defined relativistically with its origin at Earth's centre and spatial axes kinematically aligned to ICRS. It is computed from IAU/IERS conventions and ephemerides, not independently oriented from a new source fit. |
> | Horizontal AltAz | **Altitude–azimuth** axes are realized locally from the observer's gravity/vertical direction, geographic north, Earth orientation, and observation instant. Refraction determines whether coordinates are geometric or observed. |
> | TEME | **True Equator, Mean Equinox** is the Earth-centred frame conventionally returned by **Simplified General Perturbations 4 (SGP4)** satellite propagation. Its pole follows the true equator and its longitude origin follows the associated mean equinox. It is an operational orbit-model frame, not an IAU beacon realization; conversion to terrestrial or observer coordinates must follow a documented TEME convention. |
> | ITRS/ITRF | The **International Terrestrial Reference System (ITRS)** is Earth-fixed; an **International Terrestrial Reference Frame (ITRF)** realizes it from globally adjusted station positions and velocities measured by geodetic techniques. **Earth Orientation Parameters (EOP)** connect it to celestial systems through polar motion, Earth rotation, and precession-nutation. |
>
> #### Acronyms used in this box
>
> - **AGIS:** Astrometric Global Iterative Solution.
> - **AltAz:** altitude–azimuth.
> - **EOP:** Earth Orientation Parameters.
> - **EDR3:** Gaia Early Data Release 3.
> - **FK4/FK5:** Fourth/Fifth Fundamental Catalogue; `FK` comes from the German *Fundamentalkatalog*.
> - **GCRS:** Geocentric Celestial Reference System.
> - **IAU:** International Astronomical Union.
> - **ICRF3:** third realization of the International Celestial Reference Frame.
> - **ICRS:** International Celestial Reference System.
> - **IERS:** International Earth Rotation and Reference Systems Service.
> - **ITRF/ITRS:** International Terrestrial Reference Frame/System.
> - **SGP4:** Simplified General Perturbations 4.
> - **TEME:** True Equator, Mean Equinox.
> - **VLBI:** Very Long Baseline Interferometry.
>
> Further technical reading: the
> [Gaia EDR3 astrometric-solution paper](https://www.aanda.org/articles/aa/full_html/2021/05/aa39709-20/aa39709-20.html)
> describes the source, attitude, calibration, and global AGIS solution; the
> [ICRF3 paper](https://www.aanda.org/articles/aa/full_html/2020/12/aa38368-20/aa38368-20.html)
> describes the VLBI observations and global radio-frame construction; and the
> [IERS Conventions](https://iers-conventions.obspm.fr/archive/2003/chapter2/tn32_c2.pdf)
> define the conventional celestial system/frame relationship and Earth-orientation chain.
>
> ### Wenu implementation box — Where each responsibility lives
>
> **[Foundation]** Wenu does not rebuild ICRS, Gaia-CRF3, or FK5 from raw
> telescope measurements. Standards organizations and catalogue teams perform
> those global astrometric solutions. Wenu consumes their published frames and
> catalogues, preserves their scientific identity, transforms coordinates
> through Astropy or an approved specialist provider, and then projects the
> resulting spherical geometry onto a chart. This boundary prevents a plotting
> program from silently becoming a second astrometric authority.
>
> Status meanings in the table are: **implemented**—owned by current Wenu code;
> **delegated**—Wenu deliberately relies on a named external scientific
> authority; and **future**—the accepted architecture identifies an owner, but
> the operational provider or adapter has not yet been implemented.
>
> | Scientific responsibility | Wenu owner or external authority | Status and boundary |
> | --- | --- | --- |
> | Describe frame, origin, equinox, epoch, instant, status, corrections, model, and provenance | `coordinates.py::CoordinateSpec`, `PositionStatus`, and `ObservationContext` | **Implemented.** These immutable values carry meaning; they do not calculate positions. |
> | Define the structural source of astronomical positions | `positions.py::PositionProvider` | **Implemented protocol.** A provider generates native positions; it does not transform, project, or render them. |
> | Build ICRS/ICRF3 from raw VLBI observations | IAU/IERS and ICRF analysis centres, outside Wenu | **Delegated.** Wenu consumes the published ICRS realization through Astropy; it does not solve VLBI delays or no-net-rotation constraints. |
> | Build Gaia-CRF3 and solve Gaia source astrometry | Gaia Data Processing and Analysis Consortium AGIS, outside Wenu | **Delegated upstream.** Wenu does not solve Gaia CCD observations, attitude, calibration, or frame spin. |
> | Load current stellar positions | `objects/stars.py::Stars`; current Hipparcos/Skyfield path | **Implemented for the current catalogue.** Skyfield supplies the existing apparent topocentric stellar realization. |
> | Load Gaia stellar astrometry with release, J2016.0 epoch, covariance, and motion | A future Gaia implementation of `PositionProvider`, governed by Milestones 49D/49E | **Future.** Existing Gaia-derived Magellanic Cloud isophotes are morphology products, not a Gaia stellar position provider. |
> | Propagate stellar positions to another epoch | Future catalogue-provider method behind `PositionProvider.position(instant=...)` | **Future.** It must use proper motion, parallax, radial velocity, covariance, and provider provenance where applicable; `CelestialReferencePolicy` must not do this. |
> | Generate planet, Moon, and natural-satellite states | Future ephemeris providers under Milestones 49E/49I | **Future.** Expected owner is a JPL-or-equivalent provider returning explicit barycentric, geocentric, or planet-centred state. |
> | Generate artificial-satellite states | Future TLE/OMM plus SGP4 provider under Milestones 49E/49I | **Future.** It will return an explicit TEME state before any observer-local transformation. |
> | Record observer location, time, and Astropy/Skyfield compatibility state | `observer.py::Observer`; `coordinates.py::observation_context()` | **Implemented.** `Observer` constructs context but is not a competing transformation authority. |
> | Transform spherical geometry among ICRS, FK4, FK5, Galactic, GCRS, mean/true barycentric ecliptic, and AltAz | `coordinate_service.py::CoordinateService` | **Implemented and delegated numerically to Astropy/ERFA.** It preserves geometry topology and metadata and does not generate physical positions. |
> | Apply aberration, light deflection, light-time, and related apparent-place corrections | Current Skyfield stellar provider where already used; future object-specific providers and explicit `CoordinateSpec.corrections` | **Partly implemented/delegated.** These effects belong to the provider or declared transformation model, never to projection or rendering. |
> | Apply Earth orientation to observer-local AltAz | `CoordinateService` plus Astropy Earth-orientation data, using `ObservationContext.earth_orientation_policy` | **Implemented for the Astropy policy.** The current public transformation uses vacuum AltAz. |
> | Apply atmospheric refraction | `ObservationContext.refraction_policy` and the AltAz construction in `CoordinateService` | **Contract implemented; physical refraction future.** Only `vacuum` is currently accepted and Astropy receives zero pressure. |
> | Select J2000, `of_date`, or another supported equinox for coupled chart references | `charts/reference_policy.py::CelestialReferencePolicy`; CLI translation in `charts/chart_arguments.py`; TOML translation in `configuration/translation.py` | **Implemented and accepted.** It changes reference representation, not provider epoch. |
> | Construct equatorial, ecliptic, Galactic, and AltAz grid geometry | `sky/coordinate_grids.py::{EquatorialGrid,EclipticGrid,GalacticGrid,AltAzGrid}` | **Implemented.** Each grid creates typed spherical geometry and uses `CoordinateService` when another frame is requested. |
> | Apply a request's reference policy to ordinary grids | `charts/request_grids.py::configure_chart_request_grids()` | **Implemented and accepted.** Equatorial FK5 and true-ecliptic grids receive the same resolved equinox; `of_date` receives the authoritative chart-view observer explicitly. |
> | Construct celestial equator, ecliptic, seasonal keypoints, and poles | `charts/reference_furniture.py::build_celestial_reference_sky()` and `sky/points.py` | **Implemented and accepted.** Reference furniture uses the same equinox as request grids. |
> | Describe active grid/frame/equinox in chart furniture | `charts/legend_metadata.py::resolve_legend_metadata()` | **Implemented.** Metadata reports the selected representation; it does not infer a provider epoch. |
> | Convert a TEME satellite state to Earth-fixed, celestial, and topocentric coordinates | Future specialized TEME adapter owned beside `CoordinateService`, then the ordinary service for supported downstream frames | **Future, Milestone 49I.** TEME must not be relabelled ICRS or passed through an undocumented approximation. |
> | Represent ITRS/ITRF and explicit EOP provenance for satellite work | Future Earth-fixed state/adapter contract under Milestones 49E/49I | **Future.** Current Astropy AltAz transformations already consume its Earth-orientation authority internally, but Wenu does not yet expose a general ITRS product state. |
> | Rotate resolved spherical coordinates for chart centring and orientation | `geometry/frame.py::SphericalFrame` and chart-specific frame construction | **Implemented.** This is coordinate-neutral projection alignment after astronomical transformation; it is not ICRS/FK5/AltAz transformation. |
> | Project, clip, prepare, render, and export | `projections/`, `geometry/`, `charts/`, `rendering/`, and the canonical `CelestialSphere.draw_chart()` flow | **Implemented.** None of these owners may choose an astronomical frame or compute an orbit. |
> | Evolve observer time while retaining a fixed celestial scene | `charts/sequence.py`, `charts/fixed_sky_orientation.py`, and `charts/fixed_sky_sequence.py` | **Implemented reference behavior.** Scientifically keyed reuse remains a later optimization. |
>
> **[Undergraduate]** The intended future provider path is therefore:
>
> ```text
> external catalogue, ephemeris, or orbit observations
>     -> PositionProvider native state with CoordinateSpec
>     -> CoordinateService or documented specialized adapter
>     -> typed SphericalGeometry in the requested product frame
>     -> SphericalFrame projection alignment
>     -> projection, preparation, rendering, and export
> ```
>
> Wenu starts at the published catalogue/provider-state boundary. The VLBI and
> AGIS least-squares normal equations described in the preceding box remain
> provenance for the input frame; they are not planned as Wenu chart-generation
> modules. Future Gaia, planetary, and satellite work extends the provider side
> of this one pipeline rather than adding a second coordinate or rendering
> pipeline.

<a id="3-origins-and-position-status"></a>

# 3. Origins and position status

<a id="31-origins"></a>

## 3.1 Origins

- **Barycentric:** origin at the Solar System barycentre.
- **Geocentric:** origin at Earth's centre.
- **Topocentric:** origin at the observer.
- **Projection-aligned:** a Wenu-local rotated basis used only after the
  astronomical coordinates have been resolved; it is not an astronomical
  frame.

<a id="32-position-states"></a>

## 3.2 Position states

- **Geometric:** ideal spatial direction before light-time and apparent-place
  corrections.
- **Astrometric:** catalogue/model direction after the relevant reference
  conventions, but before all effects seen by a local observer.
- **Apparent:** includes the standards-defined apparent-place effects required
  by the selected engine, such as light-time, aberration, precession, and
  nutation as applicable.
- **Observed/topocentric:** direction at a site and instant, optionally
  including refraction.

These terms must be tied to the provider and transformation engine rather than
inferred from a method name.

<a id="4-mathematical-foundations"></a>

# 4. Mathematical foundations

<a id="41-spherical-and-cartesian-representation"></a>

## 4.1 Spherical and Cartesian representation

For longitude \(\ell\) and latitude \(b\),

\[
\mathbf r =
\begin{bmatrix}
\cos b\cos\ell\\
\cos b\sin\ell\\
\sin b
\end{bmatrix}.
\]

For a transformed unit vector \((x,y,z)\),

\[
\ell=\operatorname{atan2}(y,x)\bmod 2\pi,\qquad
b=\operatorname{atan2}\left(z,\sqrt{x^2+y^2}\right).
\]

These equations are implemented directly by
`geometry/frame.py::SphericalFrame._spherical_to_cartesian()` and
`_cartesian_to_spherical()`.

<a id="42-orthogonal-frame-rotations"></a>

## 4.2 Orthogonal frame rotations

An astronomical frame transformation or a projection-alignment rotation may
be represented as

\[
\mathbf r_2=R\mathbf r_1,\qquad R^{-1}=R^T,
\]

provided \(R\) is an orthogonal direction-cosine matrix. Wenu's
`SphericalFrame` performs this purely geometric rotation for projection
alignment. It must not decide epoch, equinox, precession, nutation, aberration,
parallax, or refraction.

<a id="43-local-sidereal-angle"></a>

## 4.3 Local sidereal angle

The current handwritten path takes GMST from Skyfield and applies longitude:

\[
\mathrm{LST}_{hours} =
\mathrm{GMST}_{hours}+\lambda_{east}/15^\circ.
\]

The hour angle is

\[
H = \mathrm{LST}-\alpha.
\]

Architecture 0.9.5 delegates authoritative Earth rotation, UT1 dependencies,
and apparent/mean distinctions to Astropy/ERFA.

<a id="44-topocentric-parallax"></a>

## 4.4 Topocentric parallax

Conceptually, if \(\mathbf r_{object}\) and \(\mathbf r_{observer}\) are
expressed in one compatible origin/frame/time system,

\[
\boldsymbol\rho =
\mathbf r_{object}-\mathbf r_{observer},\qquad
\hat{\boldsymbol\rho} =
\boldsymbol\rho/\lVert\boldsymbol\rho\rVert.
\]

The topocentric angles are recovered from
\(\hat{\boldsymbol\rho}\). This is significant for the Moon, planets, and
near-Earth objects and negligible for many deep-sky catalogue positions.
Production code must use the provider/coordinate engine's consistent units,
origins, light-time policy, and Earth ephemeris.

<a id="45-stellar-space-motion"></a>

## 4.5 Stellar space motion

A star provider begins from catalogue epoch, direction, proper motion,
parallax/distance, and radial velocity when available. Conceptually,

\[
\mathbf r(t)=\mathbf r(t_0)+\mathbf v(t-t_0),
\]

followed by normalization and the selected astrometric/apparent transformation
chain. The actual propagation must respect catalogue conventions; for
Hipparcos and future Gaia inputs it must not treat UTC chart times as catalogue
epochs or silently discard time-scale metadata.

<a id="5-time-vocabulary"></a>

# 5. Time vocabulary

Wenu must distinguish:

- **UTC:** civil timestamp and leap-second representation;
- **TAI:** continuous atomic time;
- **TT:** terrestrial dynamical arguments and geocentric ephemeris work;
- **UT1:** Earth rotation angle;
- **TDB:** barycentric dynamical ephemeris arguments;
- **TCB:** barycentric coordinate time; relevant to Gaia catalogue metadata;
- **catalogue position reference epoch:** such as Hipparcos J1991.25 or Gaia J2016.0;
- **provider evaluation instant:** when a moving-object state is requested;
- **display time:** human-facing civil label;
- **playback time:** media pacing, never an astronomical time scale.

The existing temporal sequence classes preserve physical versus playback time,
but coordinate architecture must additionally preserve catalogue position epoch and
provider evaluation instant.

<a id="51-calendars-are-historical-coordinate-systems-for-time"></a>

## 5.1 Calendars are historical coordinate systems for time

**[Foundation]** A written date is not yet a unique instant. Just as a pair of
sky angles needs a reference frame, a historical date needs a calendar, a
place, a rule for numbering years, and often the name of a ruler or official.
The same day can have different names in different calendars, and two records
with the same month and day words need not refer to the same season or even
begin their day at the same moment.

**[Undergraduate]** A calendar maps culturally defined years, months, and days
to a sequence of physical days. That map may depend on observations of the
Moon, an intercalation decision, a regnal-year convention, a local sunset or
sunrise, and a reform adopted on different dates in different jurisdictions.
A historian should therefore preserve the attested date and its provenance
separately from every converted date. Conversion is an interpretation with an
uncertainty, not a replacement for the source.

<a id="52-from-sumer-and-babylonia-to-egypt-and-greece"></a>

## 5.2 From Sumer and Babylonia to Egypt and Greece

The following table is a guide to the questions that must be asked, not a
universal conversion table. Ancient practice changed across cities and
centuries, and surviving evidence is uneven.

| Tradition | Broad structure | How events were commonly located | Principal conversion hazards |
| --- | --- | --- | --- |
| Sumerian and early Mesopotamian city calendars | Mostly lunisolar month systems, tied to visible lunar phases and the agricultural/cultic year; month names and year names could be local | Ruler's regnal year or a named year-event, local month, and day | There was no single timeless “Sumerian calendar.” Identify city, dynasty, king list, year-name sequence, intercalary decisions, and scholarly chronology. Competing High, Middle, Low, or Ultra-Low chronologies can move an absolute date by decades. |
| Babylonian and Assyrian | Twelve lunar months with an intercalary month when needed to keep months in the seasonal year; later practice became increasingly regular | Regnal year, Babylonian month name or number, and day; astronomical diaries may add observations | Month start depended on lunar visibility; intercalation was historically contingent before later regularization. Accession-year versus first-regnal-year counting, damaged tablets, and uncertain king-list synchronisms must remain explicit. |
| Ancient Egyptian civil | Twelve 30-day months plus five epagomenal days: a 365-day civil year without a leap day in its older form | Regnal year, season, month within season, and day; documents may also use lunar or religious reckonings | The 365-day civil year moved through the seasons—the “wandering year.” Conversion needs the ruler's chronology and synchronisms; a season name must not be treated as a fixed modern season. The later Alexandrian/Coptic calendar added a regular leap day. |
| Greek poleis | Usually local lunisolar civic and festival calendars, alongside seasonal, astronomical, and administrative reckonings | Eponymous archon or other magistrate, local month, day, festival, Olympiad, or synchronism | There was no single ancient Greek civil calendar. Month names, year starts, intercalation, and magistrate lists differed by polis; political authorities could adjust civic months. A modern “Attic date” is a reconstruction, not an original universal Greek timestamp. |

**[Foundation]** The shared astronomical problem was that a lunar month is
about 29.5 days, twelve lunar months are about eleven days shorter than a
seasonal year, and a solar year is not an integer number of days. Different
societies solved that mismatch differently: insert an extra month, allow the
calendar to wander through the seasons, or adopt a leap-day rule.

**[Undergraduate]** Mesopotamian astronomical observations are especially
valuable for chronology, but the circularity must be controlled: one should
not use a proposed chronology to identify an eclipse and then cite that same
eclipse as independent proof of the chronology. Preserve the tablet reading,
philological restoration, calendar reconstruction, astronomical model, and
candidate-event comparison as separate evidential layers.

<a id="53-roman-julian-and-gregorian-calendars"></a>

## 5.3 Roman, Julian, and Gregorian calendars

**[Foundation]** *Proleptic* means that a rule is extended to dates before the
rule was historically introduced. A “proleptic Gregorian” date therefore
answers the computational question “what date would the Gregorian rules assign
here?” It does not claim that people at that time used, knew, or named that
calendar.

**[Undergraduate]** The word comes through Greek *prolepsis*, “anticipation” or
“taking beforehand.” In chronology it marks a backward mathematical extension,
not a historical reconstruction. A proleptic date can be unambiguous within a
specified algorithm while still being anachronistic as a description of the
source culture's own date.

| System | Rule and historical role | Historian's caution |
| --- | --- | --- |
| Roman Republican calendar | A civic calendar preceding Caesar's reform, with months and politically administered intercalation | Dates require consular or other synchronisms and a reconstruction of irregular intercalations. Projecting the later Julian calendar backward silently is an anachronism. |
| Julian calendar | Caesar's reform established a 365-day common year and a leap day every fourth year; the reformed year began in 45 BCE | Early implementation of the leap rule was not perfectly regular. “Julian” must identify the calendar, not merely an old-looking European date. |
| Gregorian calendar | The 1582 reform retained the month system but changed the leap rule: century years are leap years only when divisible by 400 | The reform was adopted by jurisdiction, not by the whole world on one day. In the first adopting countries, Thursday 4 October 1582 Julian was followed by Friday 15 October Gregorian; Britain and its colonies changed in September 1752. Always record place and whether a source uses Old Style or New Style. |
| Proleptic Julian or Gregorian calendar | A modern calendar rule mathematically extended earlier than its historical introduction | Useful for computation, but it is not the calendar an ancient author used. Label it explicitly as proleptic. |

<a id="531-did-augustus-steal-a-day-from-february"></a>

### 5.3.1 Did Augustus steal a day from February?

**[Foundation]** The familiar story says that Julius Caesar gave July 31 days,
Augustus then demanded an equally long August, and a day was taken from
February to supply it. There is no reliable contemporary evidence that this
happened, so there is no historical year in which Augustus “stole” the day.
Sextilis was renamed *Augustus* in 8 BCE, but renaming the month is not evidence
that its length was changed then. February was already the exceptional short
month in the Roman calendar and had long been associated with intercalation.

**[Undergraduate]** The alternating month-length story is a late explanatory
tradition, not a secure record of Caesar's or Augustus's legislation. The
Julian arrangement of month lengths is generally understood to predate the
renaming of Sextilis. What Augustus did correct was a different error: Roman
officials initially applied Caesar's fourth-year leap rule too frequently,
apparently through inclusive counting. Augustus suspended intercalation until
the sequence was brought back into alignment. A historian should therefore
distinguish three claims: the Julian reform began in 45 BCE; Sextilis was
renamed Augustus in 8 BCE; and the supposed transfer of a day from February is
an unsupported legend. Wenu should never encode that legend as a calendar
conversion rule.

The Gregorian year averages 365.2425 days because it contains 97 leap days in
400 years. The Julian calendar averages 365.25 days. Neither number should be
confused with a measured ancient tropical year, whose value and definition
belong to astronomical modeling rather than civil calendar naming.

European records add further traps. The civil year did not always begin on
1 January; a year labelled in a source can therefore differ from a modern year
number for January, February, or March. Religious feasts may follow an
ecclesiastical rather than an observed astronomical Moon. “Old Style” can
refer to the Julian calendar, a non-January year start, or both, depending on
the editor and jurisdiction. A responsible conversion states the convention
used instead of silently correcting the document.

<a id="54-a-historians-minimum-date-record"></a>

## 5.4 A historian's minimum date record

For every date used to connect a text, inscription, observation, or event to a
Wenu chart, retain at least:

1. the source's date exactly as written, with damaged or restored characters
   marked;
2. source, edition, translation, document location, and scholarly citation;
3. polity or jurisdiction and geographic place;
4. calendar and local variant, including month name rather than only a number;
5. era, king, regnal year, eponymous official, Olympiad, indiction, or other
   year-counting authority;
6. accession-year/non-accession-year rule and civil new-year rule;
7. intercalary month or day and whether it was observed, decreed, inferred, or
   reconstructed;
8. day boundary—midnight, sunset, sunrise, noon, or unknown—and the local time
   convention if a clock time is given;
9. converted Julian/Gregorian date, explicitly labelled as historical or
   proleptic, together with the conversion authority;
10. earliest/latest possible instant or another uncertainty representation;
11. the astronomical time scale and Earth-rotation model used for a computed
    phenomenon;
12. every proposed synchronism and competing chronology, rather than only the
    preferred result.

A useful machine record therefore has separate fields such as
`source_date_text`, `calendar`, `calendar_variant`, `era`, `regnal_year`,
`month_name`, `intercalation_status`, `day_start`, `place`,
`converted_calendar`, `converted_interval`, `conversion_authority`, and
`uncertainty_note`. One ISO string cannot faithfully contain all of this.

<a id="55-year-numbering-day-counts-and-astronomical-time"></a>

## 5.5 Year numbering, day counts, and astronomical time

**No year zero in ordinary BCE/CE history.** The year 1 BCE is followed by
1 CE. Astronomical year numbering instead uses year 0 for 1 BCE, year -1 for
2 BCE, and so forth. Thus a numerical year must declare which numbering rule
it uses.

**Julian calendar is not Julian Date.** The Julian calendar is a civil calendar.
The Julian Date (JD) is a continuous day count whose integer changes at noon;
JD 2451545.0 is 2000-01-01 12:00 on the applicable astronomical time scale.
A calendar date converted to JD still needs a time scale. Modified Julian Date
is 

\[
\mathrm{MJD}=\mathrm{JD}-2\,400\,000.5,
\]

so its integer changes at midnight. Neither JD nor MJD tells the reader which
ancient calendar appeared in the source.

**UTC is not an ancient time scale.** UTC with leap seconds is a modern civil
scale. Ancient local time may instead be expressed by seasonal hours, watches,
or a solar phenomenon. To compare an ancient eclipse or occultation with a
calculation, the model must relate uniform dynamical time (usually TT) to Earth
rotation (UT1). The uncertain historical quantity is commonly summarized by

\[
\Delta T = \mathrm{TT}-\mathrm{UT1}.
\]

For remote antiquity, uncertainty in \(\Delta T\) can shift the reconstructed
terrestrial longitude or local clock time of a phenomenon substantially.
Wenu must not print a modern-looking second-precise UTC timestamp for an
ancient event unless the precision and time-scale conversion are genuinely
supported.

<a id="56-julian-and-besselian-epochs-are-not-calendars"></a>

## 5.6 Julian and Besselian epochs are not calendars

**[Foundation]** `J2000.0`, `J2016.0`, and `B1950.0` label astronomical
epochs. They identify instants or frame conventions used for positions and
coordinate axes; they do not supply month names, leap-day rules, or a civil
calendar for historians.

**[Undergraduate]** A Julian epoch advances in exact units of 365.25 days from
J2000.0. A Besselian epoch uses the older Newcomb mean-Sun convention related
to the tropical year. Consequently a Besselian label is not obtained by
applying the Julian calendar to an old date, and `B1950.0` is not another
spelling of either `J1950.0` or 1950-01-01. The epoch label must travel with
its reference-frame or catalogue meaning.

<a id="561-tropical-sidereal-and-besselian-years"></a>

### 5.6.1 Tropical, sidereal, and Besselian years

**[Foundation]** A tropical year follows the cycle of the seasons. It is the
time required for the Sun's ecliptic longitude, measured from the moving
equinox, to increase by 360 degrees. Near the modern era its mean length is
about 365 days, 5 hours, 48 minutes, and 45 seconds, or about 365.24219 days.
A sidereal year instead measures Earth's revolution relative to nearly fixed
background directions and is roughly 20 minutes longer. The difference arises
mainly because precession moves the equinox westward while Earth travels
around the Sun.

“Time from one observed March equinox to the next” is a useful first picture,
but not the full definition. Earth's orbital speed is not uniform, the
equinox itself moves, and perturbations change the orbit. Intervals beginning
at different seasonal longitudes are therefore not exactly equal. The
**mean tropical year** smooths those variations by using the mean Sun and mean
equinox, and its length also changes slowly with epoch. The Gregorian average
of 365.2425 days is a civil approximation, not a claim that every tropical
year has that duration.

**[Undergraduate]** Newcomb's **fictitious mean Sun** is an ideal point moving
uniformly so that irregular apparent solar motion can be replaced by a smooth
mean motion. The Besselian year is one complete revolution in right ascension
of that fictitious mean Sun. By convention its beginning occurs when the
fictitious mean Sun has mean right ascension 18h 40m. The conventional linear
Besselian epoch relation is

\[
B = 1900.0 +
    \frac{\mathrm{JD}-2415020.31352}{365.242198781},
\]

where the day argument must be supplied on the time-scale convention required
by the legacy reduction. The denominator is the conventional Besselian-year
length near B1900.0; it must not be treated as an immutable modern measurement
of every tropical year. The U.S. Naval Observatory notes that Newcomb's
Besselian year differs slightly from the tropical year as epoch changes.

Thus `B1950.0` denotes the instant obtained from this mean-Sun convention, not
midnight at the beginning of civil 1950. Besselian epochs belong especially to
legacy FK4-era catalogues and reductions. Modern work normally uses Julian
epochs,

\[
J = 2000.0 +
    \frac{\mathrm{JD}-2451545.0}{365.25},
\]

with the exact 365.25-day unit; `J2000.0` is JD 2451545.0 on the applicable
dynamical time scale. The exact unit makes the epoch label a transparent
linear coordinate in time rather than a changing model of the seasonal year.

The five expressions below answer different questions:

| Expression | What it is |
| --- | --- |
| Julian calendar date | A civil year-month-day under the Julian leap rule |
| Gregorian calendar date | A civil year-month-day under the Gregorian leap rule |
| Julian Date | A continuous astronomical day number |
| Julian epoch, such as J2000.0 | An astronomical epoch label based on exact 365.25-day Julian years |
| Besselian epoch, such as B1950.0 | An older astronomical epoch convention related to the tropical year and mean Sun |

<a id="57-present-wenu-boundary-and-future-historical-date-support"></a>

## 5.7 Present Wenu boundary and future historical-date support

> **Wenu implementation box — Calendars and historical chronology**
>
> Wenu currently accepts an ISO-format date/time through
> `observer.py::Observer._resolve_time()`, parsed by Python
> `datetime.fromisoformat()`. A naive time is interpreted in the declared IANA
> time zone; an offset-aware value is converted to UTC and then to
> `astropy.time.Time`. This is appropriate for current modern observing charts.
>
> It is **not** a general historical-calendar converter. The public observer
> path uses Python's proleptic Gregorian `datetime`, supports years 1–9999,
> has no BCE/year-zero input contract, and does not accept Sumerian,
> Babylonian, Egyptian, Greek, Roman Republican, historical Julian, regnal,
> or jurisdiction-specific Gregorian dates. `--reference-equinox` selects a
> coordinate reference orientation; it must never be used to smuggle a
> historical event date into the observer parser.
>
> Future historical support should introduce a separate provenance-rich
> `HistoricalDateSpec` or equivalent translation boundary. It should preserve
> the source date and uncertainty, use a specialist calendar/chronology
> authority, and produce an interval or distribution on a declared continuous
> time scale before calling the ordinary Wenu observer and coordinate
> machinery. Wenu should not invent ancient-calendar algorithms inside chart
> rendering code.

<a id="58-sources-and-limits"></a>

## 5.8 Sources and limits

Authoritative starting points include the [UCL Digital Egypt calendar guide](https://www.ucl.ac.uk/museums-static/digitalegypt/chronology/calendar.html)
for the Egyptian civil and Alexandrian/Coptic calendars; the
[ORACC Assyrian Empire Builders technical glossary](https://oracc.museum.upenn.edu/saao/aebp/Technicalterms/index.html)
for Mesopotamian intercalation terminology; and the U.S. Naval Observatory
pages on [Julian/Gregorian conversion](https://aa.usno.navy.mil/faq/JD_formula),
[historical calendar conversion and adoption](https://aa.usno.navy.mil/data/JulianDate),
[leap-year rules](https://aa.usno.navy.mil/faq/leap_years), and
[year numbering and calendrical eras](https://aa.usno.navy.mil/faq/millennium).
The [Encyclopaedia Romana discussion of Augustus and the calendar](https://penelope.uchicago.edu/encyclopaedia_romana/calendar/augustus.html)
is a useful entry point for separating the late month-length story from the
Roman evidence. The USNO [Astronomical Almanac glossary](https://aa.usno.navy.mil/faq/asa_glossary)
defines the tropical, sidereal, Julian, and Besselian years and the fictitious
mean Sun used in the Besselian convention.
For Greek material, specialist civic-calendar, epigraphic, and prosopographic
publications remain necessary; a general calendar table cannot replace the
local inscriptional evidence.

These sources explain conventions and supply starting points; they do not make
a disputed ancient chronology certain. Every conversion used in historical
argument should cite the specific edition, chronology, and algorithm actually
used.

<a id="6-current-transformation-inventory-and-095-destination"></a>

# 6. Current transformation inventory and 0.9.5 destination

| Present owner | Present operation | 0.9.5 destination |
|---|---|---|
| `coordinates.py::radec_to_altaz()` | Removed in 49C.3 | Historical equation retained only in this guide |
| `observer.py::Observer` | Location/time, Skyfield state, AltAz compatibility, immutable `observation_context` | Context/provider owner; no transform authority |
| `charts/coordinate_frames.py` | Removed in 49C.3 | Replaced by `CoordinateService` |
| `geometry/frame.py::SphericalFrame` | Pure spherical rotation for projection alignment | Retain unchanged |
| `objects/stars.py::Stars` | Hipparcos loading; Skyfield apparent topocentric AltAz | Native ICRS `PositionProvider`; Skyfield apparent realization remains provider work |
| `objects/nonstellar.py::NonStellar` | ICRS centres/outlines to AltAz via Astropy/cache | Provider for centres; morphology remains geometry; service transforms |
| `sky/coordinate_grids.py` | Native AltAz/equatorial/ecliptic/Galactic definitions and mixed conversion | Reference geometry with `CoordinateSpec`; service transforms |
| `sky/points.py::CelestialPoints` | Astropy native-to-ICRS then handwritten AltAz | Reference geometry; service transforms |
| `sky/observed_cache.py` | Observer-keyed Astropy ICRS-to-AltAz results | Scientifically complete keys after service boundary |
| `sky/milky_way.py` | ICRS GeoJSON rings to AltAz | ICRS polygons carrying provenance; service transforms |
| `sky/magellanic_clouds.py` | Gaia-derived ICRS rings to AltAz | ICRS polygons carrying provenance; service transforms |

<a id="7-proposed-095-contracts"></a>

# 7. Proposed 0.9.5 contracts

**Implementation note:** 49B.1 introduced the frozen vocabulary and structural
protocol. 49B.2 attached mandatory `CoordinateSpec` identity to all spherical
geometry records without changing numerical transformations. 49B.3 makes existing stellar and deep-sky centre catalogues implement
`PositionProvider`; morphology and constructed references remain separate.
The accepted 49C.1 milestone adds the central Astropy-backed transformation service. The merged 49C.2 milestone migrates production astronomical transformations while preserving Skyfield apparent stellar realization as provider work and native AltAz horizon construction as reference geometry. The accepted 49C.3 implementation removes the legacy function and chart wrapper module and exposes immutable context directly from `Observer`.

<a id="71-coordinatespec"></a>

## 7.1 CoordinateSpec

`CoordinateSpec` is immutable and includes coordinate frame and origin,
equinox where the frame requires one, position reference epoch where the state
requires one, evaluation instant and time scale where applicable, position status,
units/representation, and provenance/policy identity.

<a id="72-observationcontext"></a>

## 7.2 ObservationContext

`ObservationContext` is immutable and includes site, physical instant, time
scale, atmosphere/refraction policy, and Earth-orientation policy. It is
required only for observer-local transformations.

<a id="73-positionprovider"></a>

## 7.3 PositionProvider

The structural protocol is conceptually:

```python
class PositionProvider(Protocol):
    def position(self, instant) -> SphericalPoints:
        ...
```

The returned points carry their native `CoordinateSpec`. Existing star and
deep-sky sources implement the boundary; future ephemeris and orbit providers
use the same boundary.

<a id="74-coordinateservice"></a>

## 7.4 CoordinateService

```python
transform(
    geometry: SphericalGeometry,
    target_spec: CoordinateSpec,
    observation: ObservationContext | None = None,
) -> SphericalGeometry
```

The result has the same concrete geometry kind and preserves identifiers,
metadata, curve segmentation, polygon rings, and semantic topology.

<a id="8-wenu-object-catalogue-and-provenance"></a>

# 8. Wenu object catalogue and provenance

<a id="81-astronomical-objects"></a>

## 8.1 Astronomical objects

| Wenu object/layer | Scientific source or model | Packaged resource/current code | Coordinate provenance |
|---|---|---|---|
| Stars | ESA Hipparcos Catalogue I/239 (1997); parsed through Skyfield | `data/catalogs/hipparcos/hip_main.dat`; `objects/stars.py` | Catalogue RA/Dec and astrometric fields; current topocentric apparent path through Skyfield |
| Messier objects | HEASARC-derived ECSV snapshot | `data/catalogs/messier/`; `objects/nonstellar.py` | Normalized catalogue ICRS centres/dimensions |
| Galaxies | OpenNGC-derived ECSV snapshot | `data/catalogs/galaxies/galaxies_openngc.ecsv` | ICRS catalogue centres and sampled outlines |
| Open clusters | Dias/HEASARC-derived snapshot | `data/catalogs/open_clusters/` | Normalized catalogue ICRS |
| Globular clusters | Harris/HEASARC-derived snapshot | `data/catalogs/globular_clusters/` | Normalized catalogue ICRS |
| Supernova remnants | Green 2024-derived snapshot | `data/catalogs/supernova_remnants/` | Normalized catalogue ICRS |
| Planetary nebulae | Acker/HEASARC-derived snapshot | `data/catalogs/planetary_nebulae/` | Normalized catalogue ICRS |
| Milky Way isophotes | D3-Celestial GeoJSON snapshot | `data/isophotes/milky_way/milky_way_d3.json`; `sky/milky_way.py` | ICRS polygon rings with source path/revision |
| Large and Small Magellanic Clouds | Gaia DR3-derived isophote snapshots | `data/isophotes/magellanic_clouds/{lmc,smc}_gaia_dr3.json` | ICRS nested polygon rings with source path/revision |
| Moon and planets | Not implemented; future solar-system ephemeris provider | Reserved by architecture 0.9.5 | Provider must declare ephemeris, origin, instant/time scale and position status |
| Comets and asteroids | Not implemented; future orbit/ephemeris provider | Reserved | Provider must declare orbit solution/model and epoch |
| Artificial satellites | Not implemented; future SGP4/orbit provider | Reserved | TEME state, epoch, Earth-orientation and topocentric policy must remain explicit |

<a id="82-constructed-and-culturalreference-objects"></a>

## 8.2 Constructed and cultural/reference objects

| Wenu object/layer | Provenance | Current owner | Coordinate meaning |
|---|---|---|---|
| Western constellation lines | Packaged `const_aug.fab` line system | `resources.py`, constellation-line classes | Connections among Hipparcos identifiers; not IAU boundaries |
| Mapuche constellation lines | Packaged `mapuche.fab` | Same line-system boundary | Cultural line selection; provenance must remain distinct from Western system |
| IAU constellation boundaries | Packaged `bound_18.dat` | `resources.py`, boundary layer | Historical IAU boundary dataset; frame/equinox must remain explicit |
| Equatorial grid/equator | Analytic reference geometry | `sky/coordinate_grids.py::EquatorialGrid` | ICRS or FK5 with explicit equinox |
| Ecliptic grid/ecliptic | Analytic reference geometry | `EclipticGrid` | Current barycentric true-ecliptic definition with explicit equinox |
| Galactic grid/plane | Analytic reference geometry | `GalacticGrid` | Astropy Galactic frame |
| AltAz grid/horizon | Analytic observer-local reference geometry | `AltAzGrid` | Site/time-dependent horizontal frame |
| Celestial/ecliptic/Galactic poles and keypoints | Analytic frame definitions; antisolar point uses Astropy `get_sun()` | `sky/points.py::CelestialPoints` | Native frame must accompany every point |
| Physical planisphere horizon | Latitude/site-specific constructed local geometry | polar horizon/pouch owners | Separate observer-local layer over an observer-independent celestial disk |

<a id="83-provenance-requirements"></a>

## 8.3 Provenance requirements

Every packaged or generated object should eventually expose:

- source catalogue/dataset name and edition;
- original identifier;
- packaged snapshot path and revision/hash;
- native frame and catalogue epoch;
- provider model/version for moving objects;
- transformation engine/version and requested target specification;
- selection or sampling policy that changed representation without changing
  the scientific source.

<a id="9-verification-requirements"></a>

# 9. Verification requirements

Coordinate tests must cover:

1. round-trip transformations within documented tolerances;
2. agreement with direct Astropy reference transformations;
3. preservation of point IDs, curve segmentation, polygon rings, and metadata;
4. explicit failure for missing frame/origin/time/observer information;
5. invariance of observer-independent geometry across observers and instants;
6. correct observer-local variation of horizon and AltAz geometry;
7. equinox/ecliptic/equator intersection consistency;
8. cache separation by scientifically relevant identity;
9. provider substitution without projection or renderer changes;
10. the accepted fixed-sky/rotating-horizon visual reference.

<a id="10-minimal-architecture-095-roadmap"></a>

# 10. Minimal architecture 0.9.5 roadmap

1. **49B.1 — Freeze contracts:** `CoordinateSpec`,
   `ObservationContext`, `PositionProvider`, and the `SphericalGeometry`
   union.
2. **49B.2 — Type geometry:** attach mandatory coordinate identity to all
   `Spherical*` records.
3. **49B.3 — Establish providers:** make stars and non-stellar centres satisfy
   the provider boundary; keep morphology and constructed references distinct.
4. **49C.1 — Implement the service:** one Astropy-backed transformation for
   every geometry kind.
5. **49C.2 — Migrate incrementally:** references/grids, chart conversions,
   deep-sky geometry, stars, then horizon/furniture.
6. **49C.3 — Retire competing authorities:** remove
   `radec_to_altaz()` and chart-owned transformations; reduce `Observer` to
   context construction.
7. **49C.4 — Accept and close:** scientific comparisons, fixed-sky visual
   acceptance, routine suite below 30 seconds, full suite, and updated as-is
   diagrams.

<a id="101-architecture-095-acceptance"></a>

# 10.1 Architecture 0.9.5 acceptance

The as-is diagrams and scientific structure were reviewed. The corrected La
Ligua stereographic planisphere verified coincident J2000 equator/ecliptic
equinox markers. The final fixed-sky/rotating-horizon rendering was visually
accepted. The routine suite passed 1779 tests with 30 deselected in 27.31
seconds, and the complete suite passed 1809 tests in 84.99 seconds.

Public reference-equinox selection is implemented by the bounded reference
policy described in Section 13. Product-frame and provider position-epoch
selection remain later milestones. Public values translate to
`CoordinateSpec`; examples and tools do not create separate frame logic.

<a id="11-review-questions-for-fernando"></a>

# 11. Review questions for Fernando

1. Should the canonical celestial interchange frame always be ICRS, or may a
   product preserve another native celestial frame until projection?
2. Which apparent-place policy should be the ordinary default for stars?
3. Should physical refraction be disabled by default and enabled only by an
   explicit product policy?
4. Which ephemeris should be the first solar-system authority?
5. How much catalogue provenance should appear in exported SVG/PDF metadata?
6. Should cultural constellation systems be documented in this scientific
   guide or in a linked cultural-content guide with only their coordinate
   contract retained here?

<a id="12-maintenance-rule"></a>

# 12. Maintenance rule

This guide must change whenever Wenu changes a coordinate system, reference
frame, origin, equinox convention, position-epoch convention, time-scale
dependency, position provider,
transformation engine, object source, provenance field, or code owner. The
Markdown source is the only canonical guide; PDF, OpenDocument, Word, or
other review formats are generated from it on demand and are not maintained
as parallel repository authorities.

Every medium or major Wenu change must include an explicit review of this
guide, even when the milestone is not primarily described as coordinate work.
The change must either update the scientific explanations, implementation
ownership box, object/provenance inventory, and relevant roadmap statements,
or record in its acceptance evidence that the guide was reviewed and remains
accurate. A passing documentation test is not a substitute for Fernando's
scientific and pedagogical review.
<a id="13-practical-guide-to-celestial-reference-systems-equinoxes-and-epochs"></a>

# 13. Practical guide to celestial reference systems, equinoxes, and epochs

<a id="public-celestial-reference-policy"></a>

## 13.1 Public celestial reference policy

<a id="coordinate-system-vs-reference-frame"></a>

### 13.1.1 Coordinate system and reference frame

**[Foundation]** A coordinate system is a way of drawing an imaginary grid on
the sky. Equatorial coordinates use right ascension and declination, ecliptic
coordinates follow the apparent yearly path of the Sun, Galactic coordinates
are aligned with the Milky Way, and horizontal coordinates use altitude and
azimuth for a particular place and time. A reference frame states precisely
how such a grid is realized. Two grids may both be called equatorial while
using different precise frames.

**[Undergraduate]** A coordinate system supplies the coordinate variables and
their geometric meaning; a reference frame supplies the realized axes,
origin, and conventions. ICRS is a quasi-inertial celestial reference system
with a fixed realized pole and right-ascension origin; an equinox is not one
of its defining frame parameters. FK5 is an equatorial frame whose axes can
be represented at a stated equinox. Wenu therefore does not accept an equinox
as decoration on ICRS: the system/frame/equinox combination must be
semantically valid.

The three frequently confused names can be compared directly:

| Name | What it represents | Relationship to an equinox | Position epoch? |
| --- | --- | --- | --- |
| ICRS | IAU ideal barycentric celestial system, fixed relative to the distant Universe | No defining equinox; its fixed RA origin lies close to but not at the J2000.0 dynamical equinox | A catalogue expressed in ICRS may have one |
| FK5 | Older fundamental-catalogue equatorial frame with modeled mean equator, equinox, and precession | A stated equinox is part of the frame and may be selected | Its stellar data may also have one |
| Gaia-CRF3 | Optical quasar-based realization of ICRS used by Gaia EDR3/DR3 | No defining equinox; it realizes the fixed ICRS axes | Gaia EDR3/DR3 astrometry is referenced to J2016.0 |

**[Foundation]** One useful analogy is a surveying coordinate system. ICRS is
the agreed definition of the directions; Gaia-CRF3 is an exceptionally precise
set of observed optical markers that makes those directions usable. FK5 is an
older realization built from fundamental stars and an Earth-equator/equinox
model. The date attached to a moving star says when its listed position is
valid; it does not redefine the surveying axes.

**[Undergraduate]** ICRS is a barycentric, kinematically non-rotating system.
ICRF3 and Gaia-CRF3 are radio and optical realizations tied through common
extragalactic sources. FK5 is a dynamical equatorial frame with precession and
equinox semantics. A catalogue realization can additionally carry source
positions and proper motions at a position reference epoch. Consequently the complete
scientific identity is not a single name: it includes system/frame,
realization/provider, equinox where applicable, and position epoch where
applicable.

<a id="epoch-vs-equinox"></a>

### 13.1.2 Equinox, position epoch, and observation instant

> **Terminology contract — four different questions**
>
> - **Coordinate system:** Which coordinate variables and geometry are used?
> - **Reference frame:** Which physically realized axes, origin, and conventions
>   make that system operational?
> - **Equinox:** For an equinox-based frame such as FK5, which orientation of
>   the equator/ecliptic reference axes is used?
> - **Position epoch:** At what instant is a catalogue object's stated position
>   and motion model referenced?
>
> In Wenu, `CoordinateSpec.epoch` means a **position reference epoch**; it must
> never be used as a synonym for `CoordinateSpec.equinox`. The observation
> instant is a third time concept: it says when an observer-dependent physical
> realization is evaluated.

**[Foundation]** Earth's rotation axis slowly changes direction. Consequently,
the equatorial grid for J2000 and the grid "of date" are slightly rotated with
respect to each other. The equinox tells Wenu which orientation of the
celestial reference grid to draw. It does not say that the stars themselves
have been moved to that date. The observation instant tells Wenu when and from
where the local horizon is viewed.

**[Undergraduate]** Precession changes the orientation used to express
equatorial and ecliptic longitude and latitude. A requested equinox is thus a
coordinate-representation transformation. A position epoch is instead the
instant at which a catalogue state is realized; changing it can require proper
motion, parallax, and radial velocity. The observation instant enters
observer-local transformations such as AltAz. Wenu keeps these three time
concepts separate and rejects unsupported position propagation rather than
relabeling catalogue coordinates.

<a id="requesting-reference-equinox"></a>

### 13.1.3 Requesting a reference equinox

**[Foundation]** The default remains J2000. To draw coupled equatorial and
ecliptic references at another supported orientation, use for example:

```console
wenu_chart planisphere --equatorial-grid --ecliptic-grid \
  --reference-equinox J2050
```

`B1950`, an Astropy-readable date, and `of_date` are also accepted. `of_date`
uses the chart's declared observer time, never the computer clock.

The same default can be placed in a configuration overlay:

```toml
[coordinates.references]
equinox = "J2050"
```

An explicit command-line value overrides the TOML value.

**[Undergraduate]** This first public policy deliberately couples an FK5
equatorial grid and celestial equator to a barycentric true-ecliptic grid and
its seasonal keypoints at one resolved `astropy.time.Time`. Galactic references
remain in the IAU Galactic frame and AltAz remains tied to the observation
context. The policy controls reference geometry; it does not yet change the
chart family's projection frame or propagate provider positions to a requested
epoch.

<a id="julian-besselian-labels"></a>

### 13.1.4 Julian and Besselian year labels

Section 5 distinguishes civil calendars, continuous day counts, and
astronomical epoch labels and gives the historian's required provenance. This
subsection applies that distinction specifically to coordinate references.

**[Foundation]** The letter in `J2000.0` or `B1950.0` identifies the kind of
astronomical year used to name the date. `J` means a Julian epoch and `B` means
a Besselian epoch. They are not two names for exactly the same timeline, so
the letter must not be dropped. Besselian labels occur mainly with older FK4
material, especially `B1950.0`; modern FK5 and catalogue work normally uses
Julian labels such as `J2000.0`, `J2015.5`, or `J2016.0`.

**[Undergraduate]** A Julian year is exactly 365.25 days, and Julian epochs are
measured from the conventional instant J2000.0. A Besselian epoch belongs to
the older convention based on the Sun's mean longitude and the tropical year,
approximately 365.2422 days. Consequently `B1950.0` and `J1950.0` denote
slightly different instants. The usual association—FK4/Besselian and
FK5/Julian—is historically and scientifically meaningful, although the year
label alone never fully specifies a reference frame.

<a id="gaia-epoch-not-equinox"></a>

### 13.1.5 The Gaia position reference epoch is not an equinox

**[Foundation]** Gaia catalogue coordinates also carry a date, but it answers
a different question: when were the listed stellar positions defined? Gaia
DR2 positions use position reference epoch `J2015.5`; Gaia EDR3 and DR3 positions use
`J2016.0`. This is a **position epoch**, not an orientation of the coordinate
grid. There is therefore no Gaia `J2016.0` equinox that must be selected to
display Gaia positions correctly.

**[Undergraduate]** Gaia DR3 astrometry is expressed in ICRS at position reference
epoch J2016.0. ICRS has no defining equinox to select: its right-ascension
origin is a fixed realized direction, historically placed close to the
J2000.0 dynamical equinox. Propagating a Gaia source
from J2016.0 to another epoch is a provider operation using its astrometric
parameters, including proper motion and, where available and relevant,
parallax and radial velocity. By contrast, requesting
`--reference-equinox J2016.0` in this Wenu milestone rotates the coupled FK5
and true-ecliptic reference representation to that equinox; it neither
selects Gaia nor propagates any star to the Gaia position reference epoch.

Authoritative references: [ESA's Gaia DR3 documentation](https://www.cosmos.esa.int/web/gaia/dr3)
states the 2016.0 position reference epoch for EDR3/DR3; the
[IVOA Coordinates data model](https://www.ivoa.net/documents/Coords/20221004/Coords-v1.0.html)
defines epoch labels as `J` (Julian) or `B` (Besselian) followed by a decimal
year. The peer-reviewed
[Gaia-CRF3 reference-frame paper](https://www.aanda.org/articles/aa/full_html/2022/11/aa43483-22/aa43483-22.html)
describes Gaia-CRF3 as the celestial reference frame for Gaia EDR3/DR3
positions and proper motions and documents its alignment to ICRF3.
The [IERS Conventions](https://iers-conventions.obspm.fr/archive/2003/chapter2/tn32_c2.pdf)
document the ICRS right-ascension origin, its intended proximity to the
dynamical equinox at J2000.0, and the measured frame-bias offset between them.


<a id="reference-policy-acceptance"></a>

### 13.1.6 Implementation and scientific acceptance

The public reference policy was accepted on 2026-08-29 through the installed
`wenu_chart regional` command. Default `J2000` and explicit `J2000.0`
produced the same graphical SVG records after excluding timestamps,
provenance spelling, generated backend identifiers, and serialization order.
Charts at `J2016.0` and `of_date` visibly moved the coupled FK5 and
true-ecliptic grids while the apparent stellar directions and constellation
figures remained fixed. This is the expected physical result: changing the
reference axes changes the coordinates assigned to a direction, not the
observed direction itself.

The first `of_date` public render also supplied useful negative acceptance
evidence: it exposed that reusable chart views carried their authoritative
observer separately from the celestial-sphere fallback. Wenu now passes
`ChartView.observer` explicitly to
`configure_chart_request_grids(..., observer=...)`; regression tests cover
that handoff and both coupled grids.

Final acceptance evidence was 1,786 routine tests passed with 30 deselected in
25.26 seconds and 1,816 complete tests passed in 86.71 seconds. Independent
SVG runs may serialize equivalent same-style star markers in a different
order; the normalized graphical-record comparison was identical. That
reproducibility observation is separate from coordinate correctness and does
not alter the rendered chart.

<a id="moving-object-architecture"></a>

## 13.2 Scene dependencies and moving astronomical objects

**[Foundation]** A sky chart brings together things that change for different
reasons. Catalogue stars, constellation figures, and the Milky Way form a
celestial background. A planet or the Moon changes position because an
ephemeris predicts its motion at a stated time. The horizon and altitude–
azimuth grid change because the observer and Earth rotate. These are not three
drawing styles for the same object: they are three different scientific
dependencies.

Before Wenu flattens the sphere onto a page, every enabled layer must be
expressed in one common spherical product frame. A planet therefore does not
belong in the renderer or in the star catalogue. Its provider calculates its
state at the requested instant, Wenu transforms that state into the product
frame, and only then does the ordinary projection draw it together with the
background and observer-local references.

| Realization class | Typical members | What can change it? |
| --- | --- | --- |
| Celestial background | Stars, constellation geometry, deep-sky catalogues, Milky Way and Magellanic Cloud morphology | Catalogue or morphology source, provider epoch, physical propagation, content selection, and requested product frame |
| Dynamic astronomical objects | Sun, Moon, planets, natural satellites, minor bodies, and artificial satellites | Ephemeris or orbit model, evaluation instant, origin, position status, time scale, and sometimes observer |
| Observer-local geometry | Horizon, AltAz grid, cardinal directions, landscape, and visibility mask | Observer location, observation instant, Earth orientation, and refraction policy |

**[Undergraduate]** The observer-independent
`generate_celestial_sphere()` factory currently means that catalogue resources
and layer owners are loaded without selecting one observer. It does not yet
mean that every layer returns observer-independent coordinates during
rendering. The canonical
`CelestialSphere.draw_chart()` loop still resolves an observer and calls
`layer.spherical_geometry(observer, ...)`; most catalogue and morphology
layers then produce AltAz geometry for that observer and instant.

Milestone 49D.1 records this distinction and the dependency inventory without
changing numerical behavior. The future convergence is

```text
native catalogue/morphology geometry
provider-evaluated moving-object state
observer-local constructed geometry
              |
              v
       CoordinateService
              |
              v
 explicit spherical product frame
              |
              v
  projection, preparation, rendering
```

The planet-enabling insertion point is after provider evaluation and
`CoordinateService` transformation, but before projection. The returned value
remains typed `SphericalGeometry` carrying a complete `CoordinateSpec`,
semantic identifiers, topology, metadata, and provenance. Existing draw order,
projection, clipping, masking, styles, and export remain unchanged.

This boundary does not require every observer-independent-background migration
to finish before the first planet. It does require Wenu to establish which
inputs depend on catalogue epoch, provider instant, observer, reference
equinox, and product frame. That prevents an ephemeris calculation from leaking
into chart commands or rendering code and later permits safe time-sequence
reuse keyed by immutable scientific identity.

> **Wenu implementation box — 49D.1 dependency boundary**
>
> The documentation-only 49D.1 audit is maintained in
> `celestial_scene_dependency_audit_49d1.md`. Current orchestration remains in
> `sky/celestial_sphere.py::CelestialSphere.draw_chart()`; native position
> generation remains behind `positions.py::PositionProvider`; astronomical
> transformation remains solely in
> `coordinate_service.py::CoordinateService`; and projection and rendering
> remain downstream consumers. A controlled test provider may prove the future
> integration point in 49D.2. Selection of a real JPL-or-equivalent ephemeris
> and the first planet belong to later 49E/49I milestones.

<a id="49d1-acceptance"></a>

### 13.2.1 49D.1 scientific and pedagogical acceptance

Fernando accepted the scene-dependency explanation on 2026-08-29. In
particular, the accepted boundary distinguishes observer-independent catalogue
loading from observer-bound realization, keeps celestial background, dynamic
astronomical objects, and observer-local geometry scientifically separate, and
requires their convergence in one explicit spherical product frame before
projection. Verification passed 39 documentation tests, 1,789 routine tests
with 30 deselected, and all 1,819 tests. Because the milestone changes no
runtime geometry or appearance, no visual comparison was required.

<a id="49d2-handoff"></a>

### 13.2.2 49D.2 minimal realization handoff

**[Foundation]** Wenu now has a small sealed “instruction card” that can
accompany a sky layer before it is projected. The card can state the desired
coordinate identity, the observer when one is needed, the time at which a
moving object must be calculated, that time's scale, and the resolved reference
equinox. It contains no instructions about colour, page layout, projection, or
drawing.

Present charts do not yet issue this card. They continue through their existing
observer-based path. A controlled test object uses it to prove where a future
planet will enter, but that object is not an installed planet or ephemeris.

**[Undergraduate]** The frozen
`sky/realization.py::LayerRealizationContext` contains a product
`CoordinateSpec`, optional `ObservationContext`, paired provider evaluation
instant/time scale, and optional resolved reference equinox.
`SkyLayer.realize()` defaults to the established
`spherical_geometry(observer, ...)` method, so unmigrated layers retain their
current numerical realization. `CelestialSphere.draw_chart()` selects the
new hook only when a typed context is explicitly supplied.

The test-only dynamic layer asks its deterministic `PositionProvider` for an
ICRS point at the declared instant, transforms that point once through
`CoordinateService` into the requested Galactic product frame, and then
continues through the ordinary projection and renderer. This proves ownership
and ordering, not planetary accuracy. A real ephemeris still requires 49E to
define provider time arguments, origins, apparent-place policy, kernel
provenance, and target-`CoordinateSpec` composition.

> **Wenu implementation box — 49D.2 realization context**
>
> `LayerRealizationContext` is owned by `sky/realization.py`; compatibility
> adaptation is owned by `sky/sky_layer.py::SkyLayer.realize()`; conditional
> dispatch remains inside
> `sky/celestial_sphere.py::CelestialSphere.draw_chart()`; and the controlled
> provider proof exists only in `tests/test_layer_realization.py`. No current
> catalogue, reference, horizon, chart-request, CLI, renderer, or exporter is
> migrated by this milestone.
>
> Future Sun, Moon, and planet layers will declare their semantic identity
> before projection and use this same realization-to-export route for every
> format. SVG is not a second astronomy engine: the existing exporter only
> serializes the already projected records and their upstream identities under
> the reserved `solar-system/sun`, `solar-system/moon`, or
> `solar-system/planets` path. A separate SVG generator or post-export
> coordinate overlay would violate Wenu's architecture.

<a id="49d2-acceptance"></a>

### 13.2.3 49D.2 scientific and pedagogical acceptance

Fernando accepted the minimal realization handoff, exact compatibility branch,
deferred ephemeris-provider decisions, and shared SVG/export boundary on
2026-08-29. Verification passed 48 focused tests in 2.21 seconds, 1,798 routine
tests with 30 deselected in 27.61 seconds, and all 1,828 tests in 90.00
seconds. No visual comparison was required because production requests and
geometry are unchanged.


<a id="49e1-provider-design"></a>

### 13.2.4 49E.1 ephemeris-provider design

**[Foundation]** A planetary ephemeris is more like a precise moving map than
a list of points on the sky. It first tells us where a body is in three-dimensional
space relative to a named centre. To know where it appears in our sky, Wenu must
also know where and when we observe, allow for the time light needed to reach
us, and apply the explicitly chosen corrections. Only then is there a direction
that can be placed on a chart.

“Barycentric,” “geocentric,” and “topocentric” answer **where the origin is**.
ICRS, GCRS, ITRS, or a provider's J2000 convention answer **how the axes are
oriented**. Neither statement alone says whether the position is geometric,
astrometric, apparent, or affected by atmospheric refraction.

**[Undergraduate]** The proposed 49E.1 contract separates an ephemeris state
source from a solar-system direction realizer. The state source preserves the
target-minus-centre Cartesian position and velocity, frame, epoch/time scale,
units, kernel identity, coverage, and provenance. The direction realizer may
iterate the target state at retarded emission time and applies the declared
light-time, aberration, and gravitational-deflection policy for the selected
observer. `CoordinateService` then performs the coordinate-frame
representation transformation; it does not manufacture missing apparent-place
physics.

> **Wenu implementation box — 49E.1 provider boundary**
>
> The as-is generic protocol remains `positions.py::PositionProvider`.
> `observer.py::Observer` currently loads the configurable Skyfield kernel,
> whose default is `de440s.bsp`, but that compatibility ownership is not yet
> the final provider API. The proposed contract is documented in
> `ephemeris_provider_contract_49e1.md`; runtime request/state types are
> deferred to 49E.2, a real kernel adapter to 49E.3, and the first Sun, Moon,
> or planet layer to 49I.1. Every body must then use the existing semantic,
> projection, renderer, and PNG/PDF/SVG export route.
>
> Fernando accepted the design choices on 2026-08-30. A future
> `EphemerisState` is a complete position-velocity state. The resolved kernel
> identity records the scientific model (for example DE440), actual filename
> (for example `de440s.bsp`), SHA-256 fingerprint of the exact file bytes,
> coverage, and provider provenance. SHA-256 is computed once when the kernel
> resource is resolved, not for every planet position.
>
> Because Wenu has not released this interface, 49E.2 will remove
> `PositionStatus.TOPOCENTRIC` rather than preserve a misleading category:
> topocentric belongs to the origin, while astrometric, apparent, or observed
> describes physical realization. Venus is the first planned moving-body
> slice, with the Moon following as the stronger parallax test.
>
> The revised scientific and pedagogical review was accepted on 2026-08-30.
> All 41 documentation tests passed in 3.26 seconds. No visual comparison was
> required because this design audit changes no runtime geometry or output.

<a id="49e2-runtime-contracts"></a>

### 13.2.5 49E.2 minimal runtime state contracts

**[Foundation]** Wenu can now describe one ephemeris calculation without yet
performing it. The request says which body, relative to which centre, in which
three-dimensional frame, and at what instant. The result must contain three
position numbers and three velocity numbers, together with their units and the
identity of the exact ephemeris resource. It is still a state in space—not yet
the direction in which an observer sees Venus.

**[Undergraduate]** `ephemeris.py` implements frozen
`EphemerisResourceIdentity`, `EphemerisStateRequest`, and
`EphemerisState` contracts plus structural `EphemerisStateSource`. State
vectors require exactly three finite position and three finite velocity
components. Resource identity requires provider/model, filename, SHA-256,
coverage interval and scale, and provenance. A later owner calculates the
digest and opens the kernel; a later realizer owns retarded-time and
apparent-place physics.

The misleading `PositionStatus.TOPOCENTRIC` member has been removed.
Topocentricity remains explicit as `origin="observer"`.
`observer_altaz_spec()` deliberately has no status default: transformed
celestial directions must declare `APPARENT`; native horizon, zenith/cardinal,
and AltAz-grid references declare `GEOMETRIC`; and future refracted products
will declare `OBSERVED`. This separates where the coordinate begins from which
physical corrections its direction represents.

> **Wenu implementation box — 49E.2 runtime boundary**
>
> `src/wenu/ephemeris.py` owns the immutable types and source protocol.
> `src/wenu/coordinates.py::observer_altaz_spec()` owns the observer origin
> while requiring each caller to declare its physical status explicitly. `tests/test_ephemeris.py` owns the only
> deterministic Venus source. No installed code opens a new kernel, calculates
> a digest, realizes a planet direction, registers a Venus layer, or changes
> PNG/PDF/SVG output.


<a id="49e3-skyfield-adapter"></a>

### 13.2.6 49E.3 borrowed Skyfield kernel adapter

**[Foundation]** Wenu can now read a real planetary state from the ephemeris
file that an observer session already opened. A question must name the body,
the centre from which it is measured, the instant, and the three-dimensional
axes. For example, “Venus relative to the Solar-System barycentre” is a
different vector from “Venus relative to Earth.”

Wenu fingerprints the exact file with SHA-256. `DE440` identifies the
astronomical solution family; `de440s.bsp` identifies a particular
short-distribution filename; the digest identifies the exact bytes actually
used.

**[Undergraduate]** `SkyfieldEphemerisStateSource` borrows the open
`SpiceKernel` and `Timescale` from `Observer`. It converts the declared
instant through Astropy and `Timescale.from_astropy()`, resolves target and
centre to NAIF identifiers, and evaluates the simultaneous geometric
target-minus-centre state in ICRF axes. Position is returned in AU and velocity
in AU/day.

The recorded kernel coverage is the conservative common intersection of all
SPK segment intervals, not their potentially misleading union envelope.
Skyfield still checks the particular target-centre segment path. This state
contains no one-way light time, aberration, gravitational deflection,
topocentric displacement, or refraction; it is not yet the direction in which
an observer sees Venus.

> **Wenu implementation box — 49E.3 installed adapter**
>
> `src/wenu/skyfield_ephemeris.py` owns resource fingerprinting, the borrowed
> adapter, and deterministic adapter errors. `Observer` still owns and closes
> the kernel. `tools/validate_49e3_skyfield_adapter.py` refuses hidden
> downloads and validates Venus against direct Skyfield evaluation.
> `tests/test_skyfield_ephemeris.py` owns deterministic unit coverage. No
> planet layer, projection, renderer, or SVG-only path exists in this milestone.


> **49E.3 real-resource evidence**
>
> Fernando's installed `de440s.bsp` resolved as model `DE440`, with SHA-256
> `c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`
> and common coverage JD 2396752.5–2506352.5 TDB. At
> 2026-08-30T00:00:00 TDB, all six Venus/SSB adapter components matched direct
> Skyfield evaluation with zero residual within an absolute tolerance of
> (10^{-15}). This validates Wenu's adapter handoff, not the DE440 dynamical
> solution independently.


<a id="naif-spice-identifiers"></a>

### 13.2.7 NAIF and SPICE identifiers

**[Foundation]** **NAIF** is an acronym for NASA's **Navigation and Ancillary
Information Facility**, a group at the Jet Propulsion Laboratory. NAIF leads
the development and distribution of **SPICE**, whose name expands to
**Spacecraft, Planet, Instrument, C-matrix, Events**. SPICE organizes the
geometric information needed to interpret planetary and spacecraft
observations.

A **NAIF ID** is a stable integer used by SPICE to identify a body or
barycentre. In the 49E.3 Venus check, 299 identifies Venus and 0 identifies the
Solar-System barycentre. The integer identifies the object; it does not by
itself specify a coordinate system, reference frame, centre, epoch, equinox,
time scale, or correction policy.

**[Undergraduate]** NAIF body codes are provider-native identifiers retained as
provenance alongside Wenu's stable object keys. An `EphemerisStateRequest`
separately declares target, centre, frame, instant, and time scale. Thus
“target NAIF 299, centre NAIF 0, ICRF, 2026-08-30 TDB” is scientifically
meaningful, whereas “NAIF 299 coordinates” is incomplete.

Official background: [NASA/JPL About NAIF](https://naif.jpl.nasa.gov/naif/about.html)
and [The SPICE concept](https://naif.jpl.nasa.gov/naif/spiceconcept.html).


<a id="49e4-direction-audit"></a>

### 13.2.8 49E.4 observer-relative direction audit

**[Foundation]** The geometric ephemeris state answers where Venus and the
observer are in space. It is not yet what reaches the eye. Light takes time to
travel, so the Venus we receive at an observation instant left Venus at an
earlier emission instant. Wenu must keep both instants, the travel time, and
the distance rather than reducing the answer immediately to two angles.

An **astrometric direction** includes that one-way light-time solution. An
**apparent direction** starts with the astrometric direction and additionally
accounts for aberration caused by observer motion and gravitational bending of
light. Atmospheric refraction is a later observed-AltAz correction, not part
of either fixed-axis ICRS direction.

**[Undergraduate]** At reception time \(t_r\), the astrometric line-of-sight
vector is

\[
\boldsymbol\rho = \boldsymbol r_t(t_e)-\boldsymbol r_o(t_r),
\qquad
t_e=t_r-\lVert\boldsymbol\rho\rVert/c.
\]

The target's retarded emission time \(t_e\) is solved iteratively. The
terrestrial observer state is barycentric and includes the Earth's state plus
the site's displacement and velocity; it is not interchangeable with the
geocentre. This explicit state is needed so the later Moon test preserves
topocentric parallax and diurnal effects.

Skyfield's `observe()` corresponds to the astrometric light-time stage;
`apparent()` is the distinct aberration and gravitational-deflection stage.
The proposed Wenu result retains ICRS-oriented spherical geometry, distance,
light time, emission and reception instants, iteration policy, observer
identity, and the exact DE model/filename/SHA-256 provenance.

The reception instant is neither a position reference epoch nor an equinox.
The native direction uses fixed ICRS axes, so `CoordinateSpec.epoch` and
`CoordinateSpec.equinox` remain absent. If a product later requests FK5 or
ecliptic coordinates with an equinox, `CoordinateService` performs that
representation change after the physical direction has been realized.

> **Wenu implementation box — 49E.4 direction boundary**
>
> `docs/developer/solar_system_direction_realizer_49e4.md` owns the proposed
> scientific contract. It adds no runtime realizer. Proposed 49E.5 supplies
> the typed observer state and astrometric Venus direction; proposed 49E.6
> adds apparent-place corrections. The later 49I.1 Venus layer transforms the
> result once into the product frame and enters the existing projection,
> Matplotlib renderer, and shared PNG/PDF/SVG exporter. No separate SVG
> generator or post-export planetary overlay is permitted.

> **49E.4 scientific acceptance**
>
> Fernando accepted the astrometric/apparent separation, explicit observer
> state, retained distance and light-time evidence, and the distinctions among
> position reference epoch, equinox, and observation instant. He also accepted
> the Venus-first sequence and shared output path on 2026-08-30.
> All 45 current-documentation tests passed in 2.03 seconds. This accepts the
> design boundary, not the future 49E.5 runtime implementation or its
> numerical results.


<a id="49e5-astrometric-runtime"></a>

### 13.2.9 49E.5 astrometric direction runtime

**[Foundation]** Wenu can now calculate the direction from a named observer to
a Solar-System body after allowing for the time its light needed to arrive.
The observer is located once at the reception instant. Venus is then located
at an earlier trial emission instant; the distance supplies a better travel
time, and the calculation repeats until the travel time stops changing by more
than the declared tolerance.

The answer keeps more than two angles. It also keeps the distance, light time,
reception instant, emission instant, observer, Venus identity, iteration count,
and exact ephemeris fingerprint. This makes it possible to explain and
reproduce how the plotted direction was obtained.

**[Undergraduate]** `AstrometricDirectionRealizer` evaluates

\[
\boldsymbol\rho_n =
\boldsymbol r_t(t_r-\tau_{n-1})-\boldsymbol r_o(t_r),
\qquad
\tau_n=\lVert\boldsymbol\rho_n\rVert/c,
\]

with a default convergence tolerance of `1e-12` day and a maximum of ten
iterations. The observer state includes Earth plus the WGS84 terrestrial site
and uses ICRF-oriented barycentric position and velocity. Each target state is
requested from the already-resolved `EphemerisStateSource`; coverage failures
therefore remain explicit at every trial emission instant.

The spherical result uses fixed ICRS axes, observer origin, and astrometric
status. `one-way-light-time` is its only declared correction. Aberration and
gravitational deflection are deliberately absent until 49E.6; atmospheric
refraction belongs to a later observed AltAz product.

Reception and emission are observation-related physical instants. Neither is
a position reference epoch, and neither is an equinox. Consequently the
native `CoordinateSpec` has no `epoch` and no `equinox`. A later
`CoordinateService` transformation may express the realized direction in an
equinox-based product frame without changing the light-time solution.

> **Wenu implementation box — 49E.5 astrometric runtime**
>
> `src/wenu/solar_system_directions.py` owns the frozen observer-state,
> request, result, errors, and numerical realizer.
> `src/wenu/skyfield_ephemeris.py::skyfield_observer_barycentric_state()`
> borrows the same kernel as the 49E.3 source and evaluates the terrestrial
> site at reception. `tests/test_solar_system_directions.py` protects the
> deterministic physics and identities.
> `tools/validate_49e5_astrometric_direction.py` performs the no-download
> installed-DE440 Venus comparison with direct Skyfield `observe()`.
>
> No sky layer consumes this result yet. Future Venus, Moon, Sun, and planet
> geometry must still transform once into the product frame and use the shared
> projection, Matplotlib renderer, and PNG/PDF/SVG exporter. There is no
> SVG-only astronomical path or post-export overlay.

> **49E.5 scientific acceptance**
>
> Fernando accepted the observer-state, light-time, ICRS identity, retained
> evidence, and output-boundary decisions on 2026-08-30. The installed DE440
> Venus comparison converged in four iterations. Its absolute residuals from
> direct Skyfield were `3.149e-11` degree in right ascension,
> `1.544e-12` degree in declination, `1.348e-12` AU in distance,
> `7.783e-15` day in light time, and `7.994e-15` day in emission time.
> Verification passed 111 focused tests, 1,848 routine tests with 30
> deselected, and all 1,878 tests. No visual render was required because the
> result is not connected to a production layer.

<a id="49e6-apparent-runtime"></a>

### 13.2.10 49E.6 apparent direction runtime

**[Foundation]** Light-time correction tells Wenu where Venus was when the
light now reaching the observer left it. Two further effects slightly change
the direction in which that light appears to arrive. Gravity bends the ray,
especially near the Sun, and the observer's motion changes the apparent
direction through aberration. Wenu applies these effects to the already-solved
astrometric direction; it does not ask a second calculation to decide again
when the light left Venus.

The word *apparent* describes which physical corrections have been applied.
It does not name a coordinate system or reference frame, and it does not mean
that an equinox of date has been selected. The answer remains expressed on
fixed ICRS-oriented axes unless a later, explicit product-frame transformation
requests something else.

**[Undergraduate]** `AstrometricDirection` now retains
\(\boldsymbol v_t(t_e)-\boldsymbol v_o(t_r)\) as well as
\(\boldsymbol r_t(t_e)-\boldsymbol r_o(t_r)\). The retained position,
velocity, reception time, light time, observer barycentric state, and kernel
identity are sufficient to reconstruct Skyfield's astrometric value.
`SkyfieldApparentDirectionRealizer` then calls `apparent()` with explicit
deflectors: NAIF 10, 599, and 699 (Sun, Jupiter, Saturn). Skyfield applies
gravitational deflection and then special-relativistic aberration using the
observer's barycentric velocity. Near-Earth deflection is also declared.

The resulting `CoordinateSpec` uses `frame="icrs"`, `origin="observer"`, and
`PositionStatus.APPARENT`, and records `one-way-light-time`, `aberration`, and
gravitational-deflection corrections. The reception instant remains an
observation instant. There is no position reference epoch and no equinox in
the native result. These distinct fields must not be collapsed into one
generic date.

> **Wenu implementation box — 49E.6 apparent runtime**
>
> `src/wenu/solar_system_directions.py` owns the correction policy and result.
> `src/wenu/skyfield_ephemeris.py::SkyfieldApparentDirectionRealizer` verifies
> kernel, resource, observer state, and reception instant before consuming the
> accepted 49E.5 vector. `tests/test_apparent_directions.py` protects the
> deterministic handoff, and
> `tools/validate_49e6_apparent_direction.py` compares installed-DE440 Venus
> with direct Skyfield `observe().apparent()` without permitting a download.
>
> No planet is drawable yet. 49I.1 must transform Venus once into the selected
> product frame and then use the existing projection, Matplotlib renderer, and
> shared PNG/PDF/SVG exporter. A separate planetary SVG generator or
> post-export overlay is forbidden.

> **49E.6 scientific acceptance**
>
> Fernando accepted the single light-time authority, explicit deflection and
> aberration policy, ICRS/status/time distinctions, retained evidence, and
> canonical output boundary on 2026-08-30. Installed-DE440 Venus agreed with
> direct Skyfield to `3.152e-11` degree in right ascension and `1.544e-12`
> degree in declination. Verification passed 95 focused tests and all 1,883
> tests. No visual render was required because no production layer consumes
> the result.

<a id="49i1-venus-audit"></a>

### 13.2.11 49I.1 drawable Venus audit

**[Foundation]** Wenu can now calculate where Venus appears, but calculation
and drawing are deliberately separate. Before Venus can become a mark on a
chart, its apparent direction must be expressed in the coordinate system and
reference frame selected for that chart. Only then may the ordinary projection
turn it into a position on the page.

The first Venus will be a symbol and optional label, not a tiny physical
picture of the planet. Its phase, illuminated fraction, brightness, apparent
diameter, and orientation require later models. Calling the symbol “Venus”
does not license Wenu to invent those quantities.

**[Undergraduate]** The accepted apparent direction is observer-origin,
`PositionStatus.APPARENT`, and ICRS-oriented at the reception instant. 49I.1A
will pass a `LayerRealizationContext` containing the product
`CoordinateSpec`, observation, provider evaluation instant/scale, and any
applicable reference equinox. These are separate fields: the reception instant
is neither a position reference epoch nor an equinox.

49I.1B will transform the apparent `SphericalPoints` exactly once through
`CoordinateService` into that product specification. Projection-domain guards,
viewport culling, horizon masks, preparation, and rendering then remain the
same as for other sky layers. The layer does not perform its own below-horizon
test.

> **Wenu implementation box — proposed 49I.1 Venus path**
>
> `docs/developer/venus_vertical_slice_audit_49i1.md` owns the review
> contract. Proposed 49I.1A closes the ordinary chart-to-layer realization
> context handoff. Proposed 49I.1B adds one opt-in `VenusLayer` and public
> selector `--planet venus`. Its upstream semantic identity is
> `sky/solar_system/planets/venus`.
>
> PNG, PDF, and semantic SVG must consume the same projected Venus record
> through the existing Matplotlib renderer and shared exporter. No separate
> planetary SVG generator or post-export overlay is permitted.

> **49I.1 audit acceptance**
>
> Fernando accepted the context-first sequence, one product-frame transform,
> `--planet venus` request, symbolic marker and optional label, existing
> visibility ownership, semantic identity, shared output path, and deferred
> physical-appearance models on 2026-08-30. All 48 current-documentation tests
> passed in 3.30 seconds. This accepts the design, not the future runtime or
> visual result.

<a id="49i1a-realization-context"></a>

### 13.2.12 49I.1A ordinary realization context

**[Foundation]** Before any sky object is projected onto a page, Wenu now
hands its layer a small description of the chart's astronomical setting. It
says which spherical coordinates the projection expects, who and where the
observer is, and at what instant a moving object must be evaluated. Existing
stars and deep-sky objects ignore this new envelope and are drawn exactly as
before. Venus will use it in the next milestone.

**[Undergraduate]** `chart_request_realization_context()` constructs one
`LayerRealizationContext` per ordinary request export. Current ordinary
planisphere, regional, circumpolar, and binocular charts project apparent
observer-local AltAz geometry. The all-sky Mollweide chart projects apparent
observer-origin Galactic geometry. Those are the actual pre-projection frames
in the current public request contract.

The product `CoordinateSpec` carries observer origin, apparent status,
reception instant, and time scale. It has no position reference epoch and no
equinox. The reference equinox requested for equatorial/ecliptic furniture is
stored separately as `reference_equinox`; it does not define AltAz or Galactic
axes. Thus position reference epoch, equinox, and observation instant remain
distinct even though one request carries all three kinds of information.

> **Wenu implementation box — 49I.1A context handoff**
>
> `src/wenu/charts/request_realization.py` builds the scientific context.
> `request_generation.py` constructs it once before exporting products;
> `export_workflow.py` and each chart facade pass it to
> `CelestialSphere.draw_chart()`. Existing layers inherit
> `SkyLayer.realize()`, which calls their unchanged spherical method.
>
> No planet, marker, label, or output change is installed. 49I.1B will be the
> first consumer that evaluates and transforms Venus before the existing
> projection, renderer, and shared PNG/PDF/SVG exporter.

> **49I.1A scientific and architectural acceptance**
>
> Fernando accepted the output-neutral context handoff on 2026-08-30 after
> 166 focused tests, 1,859 routine tests with 30 deselected, and all 1,890
> tests passed. The complete suite verified that a chart-view `utc_datetime`
> is normalized consistently with `t_astropy` and AltAz `obstime`. This does
> not pre-accept the 49I.1B Venus layer or its visual result.

<a id="49i1b-venus-layer"></a>

### 13.2.13 49I.1B first drawable Venus

**[Foundation]** Wenu can now be asked to draw Venus with `--planet venus`.
The mark is deliberately a symbol, not a miniature picture: Wenu determines
where Venus appears but does not yet claim its brightness, phase, size, or
orientation. If Venus lies outside the chart or behind an existing mask, the
same chart rules used for every other point decide whether it is visible.

**[Undergraduate]** `VenusLayer` borrows the observer's already-open JPL
kernel. It computes the retarded astrometric direction, applies the accepted
gravitational-deflection and aberration policy once, and transforms the
observer-origin apparent ICRS `SphericalPoints` once through
`CoordinateService` into the request's product frame. The reception instant
is an observation instant, not a position reference epoch and not an equinox.
The AltAz or Galactic product specification itself has no equinox; a requested
reference equinox remains separate chart-furniture metadata.

> **Wenu implementation box — 49I.1B Venus layer**
>
> `src/wenu/sky/venus.py` owns realization but no projection or appearance.
> Chart detail owns opt-in selection, chart style owns the hollow marker and
> label, and the canonical renderer plus shared exporter produce PNG, PDF, and
> semantic SVG from the same projected point. The stable semantic path is
> `sky/solar_system/planets/venus`.
>
> Fernando scientifically and visually accepted this first Venus on
> 2026-08-30. An installed-DE440 regional chart placed Venus at the same
> position shown by Stellarium for La Ligua at the declared observation
> instant; PNG, PDF, and semantic SVG looked the same. The 148-test
> implementation review, 35 focused post-correction tests, and all 1,898 tests
> in 82.01 seconds passed. The SVG review also corrected two Green-catalogue
> remnants whose signed Galactic latitudes had previously collapsed to one
> semantic key; their displayed scientific designations did not change.

<a id="49i2-moon-shared-pipeline"></a>

### 13.2.14 49I.2 Moon and shared body pipeline

**[Foundation]** Wenu should not need a different kind of chart for Venus,
the Moon, Mars, an asteroid, or a comet. Each object supplies a position from
an appropriate astronomical model; after Wenu has obtained the apparent
direction for the declared observer and time, every object enters the same
coordinate transformation, projection, visibility, drawing, and file-output
path. “One pipeline” does not mean that all objects move in the same way.

**[Undergraduate]** The invariant contract begins with a typed geometric
position-velocity state, resource identity, centre, frame, instant, and time
scale. A JPL SPK adapter can supply major-planet and Moon states, while a
future minor-body or comet provider may propagate orbital elements. Once each
provider returns the common state contract, the observer-relative light-time
and apparent-place services can converge on observer-origin apparent ICRS
geometry, which is transformed exactly once into the product coordinate
system. Provider realization, reference frame, position reference epoch,
observation instant, and equinox remain distinct concepts.

> **Wenu implementation box — proposed 49I.2 shared pipeline**
>
> `ephemeris.py::EphemerisStateSource` is the provider-neutral state boundary;
> `solar_system_directions.py` owns light time and typed direction results;
> `skyfield_ephemeris.py` is the installed JPL/Skyfield adapter and apparent
> realizer; and `sky/venus.py` is the first concrete chart consumer. The Moon
> audit will validate NAIF target 301, strong topocentric parallax, observer
> height, and a Moon-appropriate apparent correction policy before extracting
> shared `SolarSystemPointLayer` machinery. Phase, angular diameter,
> illuminated limb, and physical disk geometry remain a later milestone.
>
> Fernando scientifically and architecturally accepted this boundary on
> 2026-08-30 after all 51 current-documentation tests passed in 1.88 seconds.
> The accepted first Moon is a symbolic point; public `--moon` adapts into a
> general internal solar-system selection; and physical disk/phase geometry
> remains 49I.3. Acceptance changes no runtime or output.

<a id="49i2a-moon-direction"></a>

### 13.2.15 49I.2A numerical Moon direction

**[Foundation]** The Moon is close enough that two observers at different
places on Earth see it against slightly different background stars. This is
parallax. Wenu therefore checks the Moon from La Ligua against both the centre
of Earth and a direct Skyfield calculation before it attempts to draw a Moon
symbol. Even the observer's height is carried through the calculation,
although changing 52 metres is far too small to matter visually on an ordinary
chart.

**[Undergraduate]** The validation requests geometric ICRF state for target
NAIF 301 relative to the solar-system barycentre, combines it with the WGS84
observer barycentric state at reception, iterates the target at retarded
emission time, and applies the explicit apparent-place policy. The result is
observer-origin apparent ICRS at the observation instant, with no position
reference epoch and no equinox. Direct Skyfield `observe(moon).apparent()` is
the numerical authority; a separate geocentric comparison measures
topocentric parallax rather than confusing origin with reference frame.

> **Wenu implementation box — 49I.2A Moon validation**
>
> `tests/test_moon_direction_validation.py` proves that NAIF 301 uses the
> existing provider-neutral contracts. `tools/validate_49i2a_moon_direction.py`
> records kernel identity, observer coordinates and height, reception and
> emission instants, light time, corrections, direct residuals, parallax, and
> the 52 m minus 0 m displacement. It installs no Moon layer, `--moon` option,
> marker, physical disk, or output change.
>
> Fernando scientifically accepted 49I.2A on 2026-08-30. With installed
> DE440, Wenu agreed with direct Skyfield to `0.1503` mas in right ascension
> and `0.0624` mas in declination; topocentric-geocentric parallax was
> `0.9500231004` degree, and the 52 m minus 0 m displacement was `27.91` mas.
> The complete suite then passed all 1,902 tests in 89.59 seconds.


<a id="49i2b-shared-point-layer"></a>

### 13.2.16 49I.2B shared Solar-System point layer

**[Foundation]** Venus and the Moon need different names and may later need
different physical drawings, but locating either symbolic point follows the
same route: identify the body, determine its observer-relative direction, and
then place that direction on the requested chart. Wenu now keeps that common
route in one component while leaving each body's identity and correction
policy explicit.

**[Undergraduate]** `SolarSystemPointDescriptor` freezes target, centre,
entity key, display name, selection key, and `ApparentCorrectionPolicy`.
`SolarSystemPointLayer` composes the accepted state source, reception-time
observer state, retarded astrometric direction, apparent correction, semantic
point metadata, and exactly one `CoordinateService` transformation into the
product frame. It owns no projection, visibility, appearance, renderer, or
export policy.

> **Wenu implementation box — 49I.2B shared symbolic point**
>
> `src/wenu/sky/solar_system_points.py` owns the shared pre-projection
> orchestration. `src/wenu/sky/venus.py` now supplies only the frozen Venus
> descriptor and thin layer specialization. A test-only Moon descriptor proves
> reuse without installing Moon chart content; `--moon` remains 49I.2C.
>
> Fernando scientifically and architecturally accepted 49I.2B on 2026-08-30
> after all 1,912 tests passed and PNG, rendered-PDF, and normalized semantic-SVG
> Venus parity against `main` was exact.


<a id="49i2c-moon-point"></a>

### 13.2.17 49I.2C first drawable Moon point

**[Foundation]** The first drawable Moon deliberately appears as a named
symbol, not a miniature photograph. Wenu now places that symbol through the
same observer-relative path as Venus while retaining the scientific fact that
the Moon is a natural satellite rather than a planet.

**[Undergraduate]** `--planet venus` and `--moon` remain clear public
vocabulary but adapt into one
`SkyContentSelection.solar_system_objects` request field.
`MoonLayer` supplies frozen Moon identity to `SolarSystemPointLayer`, which
performs the accepted light-time, apparent-place, provenance, and one
product-frame transformation sequence before ordinary projection.

> **Wenu implementation box — 49I.2C symbolic Moon**
>
> The semantic path is
> `sky/solar_system/natural_satellites/moon`. The hollow marker is
> style-owned and has no angular-size meaning. At
> `2026-08-30T00:00:00Z`—2026-08-29 20:00 in La Ligua—PNG, PDF, and semantic
> SVG agreed visually, and comparison with Stellarium placed the Moon closely
> against the same nearby Pisces stars. Physical disk and phase remain 49I.3.
>
> Fernando scientifically, architecturally, and visually accepted this first
> symbolic Moon slice on 2026-08-30 after all 1,917 tests and 54 documentation
> tests passed.

<a id="49i2d-solar-system-tracks"></a>

### 13.2.18 49I.2D Solar-System trajectories

**[Foundation]** A planetary path on a static star chart answers: “Where will
the planet appear against this fixed map of the stars at several dates?” The
planet must therefore be recalculated at every date while the map itself stays
fixed. If Wenu rotated the regional chart to the local sky at every sample
time, the curve would mostly show the daily rotation of the Earth rather than
the slower motion of the planet among the stars.

**[Undergraduate]** The proposed track retains two distinct temporal roles.
Every vertex has its own physical reception instant and a newly evaluated
topocentric apparent direction. The chart has one separate observation instant
that fixes its product coordinate frame, projection orientation, viewport, and
background. Apparent directions on fixed ICRS-oriented axes are assembled in
time order and transformed into that one product frame.

The requested sample cadence controls the piecewise approximation of the
ephemeris-defined path. Major tick instants are evaluated exactly even when
they do not fall on the regular cadence. Longitude/latitude splines are not
scientific authorities because they can overshoot at seams, poles, stationary
points, and retrograde loops.

> **Wenu design box — proposed 49I.2D track**
>
> The completed path becomes one ordinary `SphericalCurves` value before
> projection. `CoordinateService` already transforms complete curve arrays,
> and every current projection already accepts that geometry. Existing
> projection-domain guarding, clipping, preparation, rendering, and PNG/PDF/SVG
> export therefore remain unchanged.
>
> Exact tick times and anchors belong to the scientific track. The visible
> short tick is made perpendicular to the projected local tangent because map
> projections do not generally preserve a perpendicular direction constructed
> on the sphere. Tick length and line/date appearance remain style policy.
>
> The audit proposes
> `--planet-track venus --track-start ... --track-sample-step 1h
> --track-tick-step 7d --track-tick-count 4` for the first regional/binocular
> Venus slice. It changes no current runtime or chart. Physical disks remain
> 49I.3.
>
> **49I.2D scientific and architectural acceptance**
>
> Fernando accepted the two temporal roles, fixed static-chart frame, complete
> spherical-curve handoff, exact major-time anchors, projected perpendicular
> ticks, regional/binocular first scope, proposed command vocabulary, and
> deferred runtime on 2026-08-31. Verification passed 55 documentation tests,
> 1,889 routine tests with 30 deselected, and all 1,919 tests. No visual
> comparison was required because this audit changes no runtime or output.

<a id="49i2d1-track-curve"></a>

### 13.2.19 49I.2D.1 scientific track curve

**[Foundation]** Wenu now has a candidate scientific representation of a
planet's future path, but it does not draw that path yet. It calculates the
planet anew at every requested date, keeps those dated positions together as
one curve on the celestial sphere, and only then expresses the whole curve in
the fixed coordinate frame of the chart.

**[Undergraduate]** Each apparent direction has its own reception instant,
observer barycentric state, retarded emission instant, light time, correction
policy, and ephemeris evidence. Since those vertices do not share one physical
instant, the native curve does not claim a false common instant in its source
`CoordinateSpec`. Instead, the common specification declares fixed
ICRS-oriented axes, observer origin, apparent status, provider, model, and
corrections; exact reception times remain per-vertex evidence.

Regular cadence vertices and exact major-time anchors are merged before
realization. The accepted scalar direction chain remains the correctness
authority. After all directions are available, Wenu assembles exactly one open
`SphericalCurves` and performs exactly one transformation into the chart's
fixed product frame.

> **Wenu implementation box — 49I.2D.1 curve**
>
> `src/wenu/sky/solar_system_tracks.py` owns the frozen request/result and
> renderer-neutral realizer. `tests/test_solar_system_tracks.py` proves
> non-commensurate anchor insertion, per-sample observer evaluation, complete
> apparent evidence, and one curve transformation.
>
> `tools/validate_49i2d1_venus_track.py` requires installed DE440 and compares
> a 28-day La Ligua Venus path with direct Skyfield. No CLI, layer, projected
> tick, label, style, or visible output is added. Drawable tracks remain
> 49I.2D.2.
>
> **49I.2D.1 scientific and architectural acceptance**
>
> Fernando accepted the scalar per-vertex authority, one resource, exact
> anchors, complete apparent evidence, multi-instant source identity, one curve
> assembly, one fixed-frame transformation, numerical tolerance, and non-goals
> on 2026-08-31. Installed DE440 agreed with direct Skyfield to
> `4.293e-10` degree in right ascension and `8.471e-11` degree in
> declination. Verification passed 40 focused tests, 56 documentation tests,
> 1,899 routine tests with 30 deselected, and all 1,929 tests. The slice has no
> visible output; 49I.2D.2 remains separately authorized.

<a id="49i2d2-drawable-track"></a>

### 13.2.20 49I.2D.2 drawable Venus track

**[Foundation]** Wenu can now draw the future path of Venus across a fixed
regional or binocular star chart. Each point is calculated for its own date,
but the stellar map, orientation, and viewpoint remain fixed at the chart
observation instant. The result therefore shows Venus moving among the stars,
not the daily turning of the local sky.

**[Undergraduate]** The accepted multi-instant apparent directions still form
one fixed-product-frame `SphericalCurves` before projection. Major-time
anchors become short segments perpendicular to the local projected tangent.
Optional dates remain at one of the two ends of that perpendicular tick. Wenu
evaluates chronological layouts beginning from both sides and retains a side
until the nonlocal curve, an earlier date, or the viewport justifies switching.

> **Wenu implementation box — 49I.2D.2 visible track**
>
> `SolarSystemTrackLayer` owns only scientific realization.
> `charts/solar_system_track_annotations.py` owns projected ticks and date
> layout. Style owns the accepted amber-orange `#FFB000` appearance. Regional
> and binocular requests use `--planet-track venus` plus the track time
> controls; `--track-tick-labels` is optional. The semantic path is
> `sky/solar_system/planets/venus/track`.
>
> Fernando accepted the scientific, architectural, and visual result on
> 2026-08-31 after eight- and sixteen-week La Ligua reviews, including the
> retrograde loop and crowded perpendicular labels. Verification passed 127
> focused tests, 1,924 routine tests with 30 deselected, and all 1,955 tests.
> Physical apparent disks, phase, illumination, angular diameter, and
> planisphere/all-sky tracks remain deferred.
