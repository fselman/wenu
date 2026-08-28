# Wenu polar delivery and astrometry roadmap

**Status:** Historical sequencing and scientific background

**Repository baseline:** `0235a0d0824f8b0b434a50a54015b3afaddc68b8`

**Decision date:** 2026-08-16

**Immediate print date:** Tuesday, 2026-08-18

**Related migration:** `archive/migration_history/wenu_migration_0.8_to_0.9.md`

**Committed audit:** `coordinate_transformation_audit_09a2afd.md`

**Current post-v0.9 numbering authority:**
`post_v0.9_architecture_roadmap.md`

The 49A-49I labels in section 6 predate the consolidated post-v0.9 roadmap.
They remain here for scientific provenance but are not active milestone
numbers. In particular, this document's older “49G” label does not compete
with the active Milestone 49G temporal-sequence contract.

## 1. Purpose and authority

This roadmap separates two valid but differently timed goals:

1. deliver the current north/south physical polar planisphere, horizon
   overlays, and assembly information for the upcoming class;
2. after that delivery, establish one permanent package-level astrometry
   architecture incorporating Gaia, Hipparcos, Astropy, Skyfield, JPL
   ephemerides, and future satellite providers.

Where delivery order conflicts with the older v0.9 roadmap, this addendum is
the sequencing authority. Existing target architecture and responsibility
boundaries remain authoritative unless a later reviewed architecture
milestone explicitly replaces them.

The committed Milestone 48F.0 audit remains the as-is scientific diagnosis.
Its implementation sequence is deferred until after the classroom product;
it is not reverted. Milestones 49A-49I below refine that future sequence with
the Gaia, bright-star, photometric, provider, and state-model requirements
identified after the audit was committed.

Urgent physical-product work must not begin the astrometry migration. The
astrometry migration must not delay the Tuesday print.

## 2. Accepted classroom-disk baseline

The north and south star disks at commit `09a2afd` are accepted as the
classroom astronomical baseline. The following known issues are recorded and
accepted for this print rather than repaired under deadline pressure:

- the south-face ecliptic label orientation is not yet final;
- the vernal-equinox marker and the displayed ecliptic/equatorial intersection
  reveal inconsistent upstream reference-frame definitions;
- ICRS, FK5 J2000, equinox-of-date, mean-ecliptic, and true-ecliptic paths are
  not yet governed by one package transformation contract;
- some observer-independent celestial geometry still takes an AltAz round
  trip before returning to an equatorial polar projection;
- final reference-label placement and pole-label curation remain deferred.

These are scientific-architecture debt, not page-registration or usability
errors. No projected-coordinate nudge, special marker offset, or one-face
exception may be added merely to hide them.

The accepted disk content remains:

- magnitude-5.5 stars;
- constellation figures and labels;
- filled Milky Way without contour outlines;
- both Magellanic Clouds where their geometry falls within a face;
- four principal RA meridians and short 20-degree declination ticks;
- celestial equator, ecliptic, Galactic plane, reference markers, and ecliptic
  keypoint labels in their current reviewed state;
- paired +20/-20 degree limits and the current opposite-face handedness;
- the current common-year calendar geometry and midnight convention.

## 3. Immediate delivery sequence

### Milestone 48E.4A - Freeze the class disk candidate

**Goal:** Prevent visual or astronomical refinements from destabilizing the
physical-product work.

- record `09a2afd` as the accepted pre-furniture disk checkpoint;
- add regression assertions that urgent furniture does not change projected
  stellar, constellation, Milky Way, Cloud, or reference geometry;
- retain the current projection, limits, scale, calendar, style, and detail
  policy;
- create no new catalogue or coordinate path;
- make no repair to the accepted reference-frame issues.

**Acceptance:** North and south astronomical layers are identical before and
after adding physical furniture.

### Milestone 48E.4B - Actual-size face pages and information

**Goal:** Produce self-identifying, measurable, printable north and south A4
pages through the canonical export path.

Each page must contain resolved physical furniture outside the stellar
aperture and calendar band:

- face identity: `NORTH / NORTE` or `SOUTH / SUR`;
- common disk diameter and a labelled physical scale-verification ruler;
- centre-punch mark;
- asymmetric back-to-back registration marks;
- face-orientation or glue-alignment cue;
- site edition: La Ligua/Papudo;
- site latitude and longitude used for the overlay/calibration;
- standard-time statement: UTC-4;
- explicit statement that daylight-saving time is not encoded;
- projection name and north/south declination coverage;
- magnitude limit 5.5;
- product/version identifier and source revision;
- `Print at 100% / Actual Size; do not Fit to Page`;
- minimal cut, glue, and face-use instructions.

Generated wording may be bilingual locally for this product. It must remain
semantic furniture data, not arbitrary Matplotlib text assembled by the
diagnostic script.

**Acceptance:** Measured printed diameter and scale ruler agree with the
request; no furniture overlaps the star aperture or calendar; both outputs
come from one paired request and one final save per page.

### Milestone 48E.4C - Render existing registration metadata

**Goal:** Complete physical alignment without redesigning celestial geometry.

- render the centre shared by both faces;
- realize the existing asymmetric registration metadata on both pages;
- use at least one unambiguous orientation cue that cannot be satisfied after
  an accidental 180-degree reversal;
- prove the face-fold/back-to-back mapping numerically in paper coordinates;
- keep every text string readable on its own face;
- never mirror a completed raster or text artist;
- document how the printed marks are transferred or inspected during gluing.

**Acceptance:** A paper mock-up can be pierced, aligned, and glued without
guessing rotational orientation. The registration test is independent of
printer margins.

### Milestone 48G.0 - Freeze the classroom interaction

For this edition, the ordinary operating convention is:

- the horizon overlay remains fixed in the user's hand;
- the celestial disk rotates beneath it;
- the date on the disk is aligned with the desired hour on the overlay;
- `00:00` is at the bottom;
- the midnight meridian from the active celestial pole points vertically up;
- the device is flipped to use the opposite celestial face and its matching
  overlay.

This convention governs tabs and instructions only. Horizon geometry is
derived astronomically and does not depend on which paper part the user moves.

### Milestone 48G.1 - Paired observer-latitude horizon geometry

**Goal:** Resolve separate south-face and north-face overlay windows for the
La Ligua/Papudo classroom edition.

- derive the altitude-zero great circle for the configured site latitude;
- use the existing observer and canonical spherical/projection boundaries;
- transform the horizon into each face's selected polar projection;
- clip and continue the usable window consistently across the two disk caps;
- preserve the +20/-20 overlap rather than inventing a face-specific sky;
- expose latitude, overlay radius, centre, and cut clearance as immutable
  physical-product geometry;
- mark which side/face each overlay belongs to;
- keep the horizon overlay separate from the rotating celestial disks.

**Acceptance:** Cardinal horizon points and polar visibility limits agree with
independent spherical checks. Both faces share the same observer latitude and
physical centre. No overlay module loads or selects astronomical catalogues.

The accepted classroom construction additionally fixes these physical-product
constraints for the following furniture milestone:

- the rotating disk rests against the one-millimetre folding spine and
  protrudes 47 mm from the open edge for insertion after assembly;
- both faces use three identical 37.5-degree date windows separated by
  5 degrees;
- the hour numerals remain upright and their short radial marks lie outside
  the numerals;
- N, E, S, W and `HORIZONTE` belong to the fixed overlay, never the disk;
- the south-facing overlay title is `Muchos cielos, un firmamento`.

### Milestone 48G.2 - Hour ring, cardinal marks, and instructions

Each face-specific overlay must include:

- an hour tick every hour;
- numeric hour labels only from 20:00 through 04:00;
- fixed `00:00` at the bottom;
- N, E, S, and W in the correct physical directions;
- centre-punch and overlay-to-disk registration marks;
- cut line, retained-paper region, and safe handling/tab cues;
- face identity matching the corresponding star disk;
- standard-time UTC-4 statement;
- daylight-saving instruction: when civil clocks use UTC-3, apply the stated
  one-hour correction rather than shifting the printed calendar astronomy;
- a concise date/hour alignment instruction.

The hour scale and text are furniture over already-resolved physical overlay
geometry. They do not belong to projection classes or the renderer.

Milestone 48G.2B freezes that furniture as immutable millimetre records. The
compass letters are explicitly manual geographic cues on the fixed pouch, not
positions derived from Wenu's projected sky. During use, the observer rotates
the disk so the selected date and hour agree with the pouch; the labels then
show how to hold the assembled device toward the corresponding horizon.

Milestone 48G.2C realizes those records as black actual-size construction
artwork. The front is the south-facing overlay and the back is the north-facing
overlay. Print the imposed sheet one-sided at 100 percent / Actual Size,
verify the 195 mm disk guide and fold lines at 148 and 149 mm, then cut only
the dashed sky and date-window paths before folding and gluing.

### Milestone 48G.3 - Deterministic print package

**Goal:** Generate the complete classroom print candidate reproducibly.

Required outputs:

1. south celestial disk page;
2. north celestial disk page;
3. south-face horizon-overlay page;
4. north-face horizon-overlay page;
5. concise assembly/use instructions, either on reserved page areas or one
   additional instructions page if required for legibility.

Record output dimensions, requested physical scale, source revision, product
configuration, and file checksums. Prefer PDF for actual-size printing when
the existing export contract can support it without creating another path;
retain deterministic PNG diagnostics for visual review.

### Milestone 48G.4 - Monday physical acceptance

Before Tuesday printing:

- print one complete set at 100% / Actual Size;
- measure both disk diameters and both scale rulers;
- pierce and align the centres;
- verify asymmetric face registration;
- cut both overlay windows;
- test representative dates at 20:00, 00:00, and 04:00;
- verify N/E/S/W using bright stars near the horizon;
- verify the Southern Celestial Pole visibility from latitude about -32.5
  degrees;
- flip the assembly and confirm that the north face and overlay are not
  reversed;
- record only blockers to printing; accept cosmetic refinements for the
  post-class backlog.

## 4. Tuesday print gate

The classroom product is printable when:

- every page is self-identifying;
- actual-size dimensions are verified physically;
- date/hour handedness works on both faces;
- registration and glue orientation are unambiguous;
- overlays correspond to the same configured site and centre as the disks;
- daylight-saving use is explained;
- all focused and full tests pass;
- known 48E.3 reference-frame issues remain documented and unchanged.

Optional bright-star symbols, curated deep-sky content, final typography,
night appearance, general localization, and astrometry modernization are not
Tuesday blockers.

## 5. Post-class v0.9 stabilization

After the class:

1. record feedback from physical use;
2. correct measured scale, registration, handedness, or horizon defects first;
3. finish ordinary request/configuration and CLI exposure;
4. decide whether optional bright-star and deep-sky refinements belong in
   v0.9;
5. complete typography, night-mode, and localization milestones only through
   their existing owners;
6. update user/assembly documentation and close v0.9;
7. preserve the accepted classroom edition as a reproducible product profile.

The deferred celestial-reference mismatch is not repaired piecemeal during
v0.9 closure. It enters the astrometry roadmap below.

## 6. Post-planisphere astrometry and Gaia roadmap

This work begins only after the physical polar planisphere is delivered and
v0.9 is stable. It is a package-wide architecture program, not another polar
chart patch.

### Milestone 49A - Audit and target architecture

- inventory every Astropy, Skyfield, hand-written, FK4/FK5, ICRS, ecliptic,
  Galactic, AltAz, time, ephemeris, and observer transformation path;
- define a new package-level `wenu.astrometry` responsibility boundary;
- keep `wenu.geometry` coordinate-neutral;
- keep projection alignment separate from astronomical frames;
- distinguish catalogue measurement, state propagation, apparent-place
  computation, frame transformation, projection, and rendering;
- choose and document the fixed atlas equator/equinox/ecliptic policy;
- include Gaia/Hipparcos catalogue fusion in the initial design rather than as
  a later retrofit.

No production behavior changes in 49A.

### Milestone 49B - Core astrometry vocabulary

Introduce immutable, tested concepts before migrating any chart:

- `FrameSpec`;
- `OriginSpec`;
- `TimeSpec` and time-scale provenance;
- `PositionKind` distinguishing catalogue, geometric, astrometric, apparent,
  and observed states;
- Cartesian position and optional velocity with units;
- `AstrometricState`;
- `StellarAstrometricState`;
- `FramedSphericalGeometry`, wrapping rather than contaminating neutral Wenu
  spherical geometry;
- `CatalogueProvider` protocol;
- `PositionProvider` protocol;
- `TransformationGateway` protocol;
- provider/model/catalogue provenance and reproducibility metadata.

These types must support vectorized catalogues and incomplete measurements.
They must not require every physical state to pass through ICRS when a
different standards-defined transformation path is correct.

### Milestone 49C - Gaia and bright-star catalogue foundation

Gaia is the primary modern stellar-astrometry source, not a coordinate
transformation library. The first provider must preserve:

- Gaia release and `source_id`;
- ICRS position;
- Gaia reference epoch, including J2016.0 TCB for DR3;
- `pm_ra_cosdec` and `pm_dec`;
- parallax;
- radial velocity when available;
- covariance/uncertainty data required for later propagation;
- solution type and quality indicators, including RUWE where used;
- Gaia G, BP, and RP photometry as their own passbands;
- missing, negative, or unreliable values without silently inventing physical
  distances or velocities.

Gaia does not replace every current source. Define a reviewed fusion policy:

- Gaia for modern astrometry where reliable;
- Hipparcos or another curated bright-star supplement for the brightest stars
  and Gaia bright-end gaps;
- an explicit visual-V photometry authority for magnitude-sized naked-eye
  charts, never silently treating Gaia G as Johnson V;
- separate curated names and cultural identifiers;
- stable cross-identifiers and provenance for every merged field;
- source-quality policy that does not remove essential naked-eye stars merely
  because a Gaia solution is incomplete.

Build a packaged, reproducible chart subset rather than querying the network
during ordinary rendering.

### Milestone 49D - Stellar propagation and transformation gateway

- propagate Gaia/Hipparcos space motion from each catalogue reference epoch;
- support proper motion, parallax, radial velocity, and perspective effects
  when the data justify them;
- use Astropy/ERFA as the principal standards-based frame transformation
  engine behind the Wenu gateway;
- retain explicit adapters for specialized providers;
- add fixed reference cases, round trips, topology/metadata preservation, and
  cross-catalogue epoch tests;
- make tolerances scientific and frame-specific rather than pixel-derived.

### Milestone 49E - Celestial-reference vertical slice

Migrate only the equator, ecliptic, Galactic plane, poles, equinoxes, and
solstices first. Resolve the currently accepted polar mismatch through one
fixed atlas policy and spherical coincidence tests. Do not use projected
offsets. Validate the vertical slice on polar, all-sky, regional, binocular,
and ordinary planisphere charts before migrating further layers.

### Milestone 49F - Observer-independent celestial layers

Migrate stars, constellation lines and labels, FK4 B1875 boundaries, Milky
Way, Magellanic Clouds, and nonstellar catalogues to direct framed celestial
geometry. Remove observer-dependent AltAz round trips from static atlas and
polar products. Preserve catalogue selection and visual baselines unless a
scientific correction is explicitly accepted.

### Milestone 49G - Observer-local realization and Skyfield boundary

- migrate horizons, AltAz grids, visibility, and local-sky products through
  the same gateway;
- retire the independent `radec_to_altaz()` mathematics;
- make Skyfield's current stellar apparent-place responsibility explicit;
- distinguish astrometric, apparent, and refracted positions;
- split observer site/time policy from ephemeris-resource ownership while
  preserving the public `Observer` facade during migration;
- record IERS/Earth-orientation, leap-second, atmosphere, dependency, and
  resource provenance needed for reproducible charts.

### Milestone 49H - Solar System and satellite providers

Only after the common state and transformation contracts are proven:

- add Moon and planet states through one explicit JPL ephemeris policy,
  initially reusing Wenu's existing Skyfield/JPL investment where suitable;
- add asteroid/comet providers through the same state contract;
- add TLE/OMM plus SGP4 artificial-satellite propagation;
- preserve TEME as TEME and transform it through a validated TEME-to-ITRS or
  observer-local path rather than relabelling it as ICRS;
- support barycentric, geocentric, planet-centred, Earth-fixed, and
  topocentric origins explicitly;
- record light-time, aberration, deflection, Earth orientation, and refraction
  policy;
- validate against independent authoritative reference cases.

### Milestone 49I - Performance, animation, and closure

- cache maximal catalogue states and reusable epoch realizations;
- let animations update time-dependent realization/visibility without
  rebuilding immutable catalogues or the entire celestial sphere;
- benchmark Gaia-scale subsets, observer changes, and time sequences;
- enforce that charts and sky layers no longer own frame conversions;
- update architecture, source tree, implementation reference, configuration,
  user documentation, and catalogue provenance;
- run the full numerical and visual regression matrices;
- deprecate compatibility paths only after every consumer has migrated.

## 7. Rules that prevent repeated rewrites

- Define state and provider contracts before adding Gaia, planets, or
  satellites.
- Prove one reference-geometry vertical slice before migrating all layers.
- Do not alter neutral geometry or projection APIs to carry hidden
  astronomical meaning.
- Do not let charts choose undocumented frame/equinox defaults.
- Do not duplicate ephemeris or catalogue data access in chart families.
- Preserve provider-native frame, origin, epoch, time scale, units, and
  provenance until a real transformation occurs.
- Preserve Gaia G/BP/RP and visual V as distinct photometric quantities.
- Keep catalogue fusion declarative and reproducible.
- Keep public compatibility facades during staged migration.
- Add architectural enforcement only after the canonical replacement exists.
- Require focused numerical, cross-product, full, and visual tests at every
  migration boundary.

## 8. Completion definitions

### Classroom delivery complete

The paired disks and paired horizon overlays print at actual size, align,
assemble, and operate correctly for La Ligua/Papudo; every face is identified;
UTC-4/daylight-saving use is explained; tests pass; and the accepted 48E.3
issues are recorded without deadline-driven scientific hacks.

### Astrometry modernization complete

Wenu has one package-level astrometry gateway; Gaia and bright-star catalogues
are fused with explicit astrometric and photometric provenance; static and
observer-local geometry use declared frame policies; Skyfield and specialized
providers have non-overlapping roles; Moon, planet, and satellite states fit
the same model; no chart family owns independent coordinate mathematics; and
the full numerical, visual, documentation, and reproducibility contracts pass.
