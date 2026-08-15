# Wenu migration roadmap: v0.8 to v0.9

**Status:** Active
**Source:** `current_architecture_v0.8.md`
**Target:** `target_architecture_v0.9.md`
**Base commit:** `c169162`

## 1. Objective and delivery order

Deliver a working, printable paired polar planisphere quickly, then refine it
without destabilizing the existing Wenu pipeline. The immediate classroom
goal is a north/south disk mock-up before Wednesday, 2026-08-19. Horizon,
deep-sky, typography, night appearance, and translation follow in separately
reviewable stages.

The migration order is deliberately:

1. architecture and projection;
2. paired disk and calendar mechanics;
3. essential astronomical content and actual-size print;
4. physical disk approval;
5. horizon overlay;
6. optional content and appearance refinement;
7. general localization;
8. v0.9 closure.

## 2. Migration rules

- preserve `CelestialSphere.draw_chart()` as the execution core;
- add projection mathematics under `wenu.projections` only;
- keep physical-disk framing in a chart owner;
- keep calendar, registration, and assembly marks in furniture/export owners;
- keep magnitude limits and curated objects in detail/selection owners;
- keep colors, symbols, and typography in style/mode owners;
- use one paired request to prevent north/south configuration drift;
- never mirror rendered text or a completed raster;
- do not design the horizon overlay before the disk geometry is approved;
- retain English generated labels until the final localization milestone;
- preserve all v0.8 chart behavior and atlas-print regressions.

## 3. Milestone 48A - Define the v0.9 architecture

### Goal

Freeze the implemented v0.8 baseline, proposed physical-planisphere target,
and incremental roadmap before runtime changes.

### Work

- add `current_architecture_v0.8.md`;
- add `target_architecture_v0.9.md`;
- add this roadmap;
- update assistant authority and documentation contracts;
- record the urgent disk-first sequence and the deferred horizon decision.

### Verification

- documents agree on projection, handedness, date calibration, ownership, and
  delivery order;
- no step introduces a parallel renderer or export path;
- current source and implementation references remain at version 0.8;
- full suite passes without runtime changes.

### Commit

```text
Milestone 48A: Define the Wenu v0.9 polar-planisphere architecture
```

## 4. Milestone 48B - Add polar-equidistant projection

### Milestone 48B.1 - Projection mathematics

- implement backend-neutral north/south polar azimuthal-equidistant forward
  and inverse projection;
- support explicit scale, position angle, handedness, and selected pole;
- implement projected-radius and angular-radius conversions;
- reject non-finite values and invalid radii;
- retain ordinary spherical geometry dispatch.

Tests cover poles, equator, representative RA quadrants, round trips,
declination-linear radial spacing, and north/south handedness.

**Status:** Implemented. The backend-neutral projection owns selected-pole
linear radial mathematics, inverse mapping, position angle, handedness,
radius conversion, viewport construction, and established geometry dispatch.
No chart or request selects it before Milestone 48B.2.

### Milestone 48B.2 - Projection selection boundary

- register the polar projection and equatorial frame identities at the
  immutable request/view boundary;
- add one immutable projection/frame selection that constructs projections
  lazily from chart-owned geometry;
- add the canonical AltAz-to-ICRS geometry transformation required by a
  static polar disk;
- preserve stereographic and Mollweide behavior;
- expose no calendar, physical size, or style values from the projection;
- prove lazy projection and selection isolation on the reusable sphere.

Existing chart families continue to reject the polar/equatorial pair until
Milestone 48C.1 supplies a chart that actually renders it. This prevents a
request from claiming polar geometry while constructing a stereographic
chart.

**Status:** Implemented. `ProjectionSelection` pairs every registered
projection with an accepted spherical frame, builds a fresh backend-neutral
projection only when requested, and is exposed by `ChartView`. The canonical
coordinate-frame adapter now preserves spherical structure and metadata when
recovering observer-independent ICRS geometry from canonical AltAz layers.
The five v0.8 families retain their exact implemented projection/frame pairs;
the first selectable polar chart remains Milestone 48C.1.

## 5. Milestone 48C - Add paired polar disk geometry

### Milestone 48C.1 - One face contract

- add a polar-planisphere disk chart owner with pole, limiting declination,
  position angle, projected radius, physical diameter, and face handedness;
- default south coverage to -90 through +10 degrees;
- default north coverage to +90 through -10 degrees;
- allow both limits to be configured independently;
- retain circular clipping and an exact centre.

The physical-product default is polar azimuthal-equidistant. The same chart
owner also accepts stereographic projection in the equatorial frame so the
two radial laws can be compared without changing disk framing or content.

**Status:** Implemented. `PolarPlanisphereChart` owns one immutable north or
south face, resolves the +10/-10 degree default limits, constructs either
equidistant or stereographic equatorial projection, and exposes an exact
circular boundary, square viewport, physical diameter, handedness, chart
context, canonical render, and export seams. Paired resolution, registration,
calendar furniture, and the public paired request remain later milestones.

### Milestone 48C.2 - Paired request and registration

- add one immutable paired-product request that resolves both faces from the
  same content, scale, site, calendar, and physical settings;
- reverse angular handedness between faces while keeping text readable;
- generate identical outer, calendar, and pivot radii;
- add asymmetric back-to-back registration metadata;
- reject incompatible north/south physical sizes or centres.

Tests fold paper-coordinate samples through the two faces and prove opposite
apparent rotation, RA quadrant order, shared centre, matching radii, and the
20-degree default overlap.

**Status:** Implemented. `PolarPlanispherePairRequest` resolves both immutable
faces from one projection, scale, physical diameter, position angle, sample
count, and compatible independent declination limits. It verifies equal polar
and projected radii, derives projection-aware opposite paper RA direction,
shares centre and optional calendar/pivot radii, and supplies corresponding
asymmetric registration metadata without mirroring text. Calendar geometry,
site/time calibration, and rendered assembly furniture remain later owners.

## 6. Milestone 48D - Add the civil calendar ring

### Milestone 48D.1 - Calendar model

- define one immutable 365-day common-year calendar;
- preserve ordinary month lengths and omit February 29;
- compute daily scale angles from the documented sidereal-midnight model;
- configure longitude, standard UTC offset, and a deterministic reference
  common year or equivalent mean-year convention;
- keep daylight saving out of the calculation;
- produce semantic day, month, and boundary records without Matplotlib.

Tests cover 365 unique days, month lengths, month boundaries, wraparound,
La Ligua standard-time calibration, and several equinox/solstice dates.

**Status:** Implemented. `CommonYearCalendarRequest` anchors January 1 to
local mean sidereal time at standard-time midnight for a configurable
longitude, UTC offset, and deterministic non-leap reference year. The neutral
ring advances by exactly `360 / 365` degrees per civil day, closes without a
special New Year gap, retains the corresponding midnight RA, and exposes
frozen day, true-month-arc, month-boundary, and semantic month-label records.
Handedness and drawing remain furniture responsibilities of Milestone 48D.2.

### Milestone 48D.2 - Calendar furniture

- draw one tick per day and stronger month boundaries;
- label only days 5, 10, 15, 20, 25, and 30 when present;
- centre month names on their actual arcs;
- orient day numbers radially with bases outside;
- place the face-appropriate scale in reversed handedness;
- reserve the central star-disk aperture from calendar furniture.

When a date is placed at the future bottom `00:00` mark, tests prove that the
correct RA lies on the implicit upward midnight meridian.

**Status:** Implemented. `PolarCalendarFurnitureRequest` maps the immutable
common-year scale onto both resolved disk projections. Each face receives 365
physical tick segments, 12 longer month-boundary ticks, 71 selected numeric
day labels, and 12 semantic month-label anchors at true arc centres. Label
rotation records keep typographic bases outward without mirroring text. The
calendar begins outside an explicit star-disk radius, and each date lies
exactly opposite its projected midnight RA; face-specific projection geometry
therefore produces the required reversed handedness and proves the future
bottom-midnight alignment. Backend realization and localized month text remain
later presentation work.

## 7. Milestone 48E - Produce the first classroom disks

This is the urgent minimum printable product.

### Milestone 48E.1 - Essential content policy

- select stars through magnitude 5.0;
- include constellation figures and labels;
- omit constellation boundaries and deep-sky symbols;
- resolve one clean physical-print detail policy for both faces;
- prove overlap-region content is identical before projection.

### Milestone 48E.2 - Canonical appearance

- add a physical-planisphere style derived through normal style composition;
- use white paper and configurable provisional ESO-blue stars;
- keep ordinary circular magnitude symbols for the first print;
- render Milky Way levels as translucent filled shading with zero contour
  linewidth;
- keep labels and constellation figures subordinate and legible;
- leave final font curation explicitly deferred.

### Milestone 48E.3 - Essential references

- add RA meridians at 0h, 6h, 12h, and 18h;
- add declination ticks every 20 degrees along those meridians;
- label the celestial equator, ecliptic, and Galactic plane;
- mark and label equinoxes and solstices;
- mark the relevant ecliptic and Galactic poles within each disk;
- prevent labels from entering the date ring.

References use existing spherical/reference preparation wherever possible.
Disk-only ticks and physical-scale labels remain chart furniture rather than
new sky catalogues.

### Milestone 48E.4 - Actual-size A4 export

- export deterministic north and south pages at an explicit physical size;
- target an initial 190-200 mm common disk diameter on A4;
- add pivot, face identity, asymmetric registration marks, scale ruler, and
  minimal glue/print instructions;
- retain one final save per page;
- document 100 percent / Actual Size printing.

### Urgent acceptance

- focused and full tests pass;
- both pages print without clipping at actual size;
- measured diameter agrees with the request;
- a paper mock-up aligns and glues back to back;
- dates, RA handedness, and face rotation are correct;
- magnitude-5 stars, constellations, Milky Way, and references remain clean;
- Fernando Selman approves the classroom print or records only the smallest
  corrections needed before Wednesday.

## 8. Milestone 48F - Refine and approve the paired disk

- correct defects found in the real paper mock-up;
- tune disk diameter, ring spacing, label density, and reference hierarchy;
- make site, pole limits, physical dimensions, and output paths configurable
  through the ordinary request/configuration boundary;
- add one short canonical example and one `wenu_chart polar-planisphere`
  command path that share the same paired request;
- record reproducible PDF/PNG dimensions, source revision, and checksums;
- freeze the accepted disk geometry before horizon implementation.

The example declares a product; it does not assemble artists, calculate
calendar angles, mirror geometry, or save pages directly.

## 9. Milestone 48G - Add the separate horizon overlay

### Milestone 48G.1 - Freeze the physical interaction

After disk review, document whether the ordinary assembly rotates the disk,
the overlay, or supports either operation. The choice may alter instructions
and tabs but must not alter celestial or horizon geometry.

### Milestone 48G.2 - Observer-latitude window geometry

- derive the La Ligua/Papudo altitude-zero curve from canonical observer
  geometry;
- transform it into each face's polar projection and physical coordinates;
- produce a cuttable visible-sky window without engraving a fixed horizon on
  the celestial disk;
- make latitude and physical radii configurable;
- prove cardinal orientation and polar visibility limits.

### Milestone 48G.3 - Hour scale and instructions

- place fixed `00:00` at the bottom;
- draw one tick per hour;
- label only 20:00 through 04:00;
- use standard time and provide a daylight-saving adjustment instruction;
- add N, E, S, W, centre, registration, cut, and assembly marks;
- preserve the disk's date-to-upward-midnight-meridian contract.

### Milestone 48G.4 - Physical acceptance

Print, cut, assemble, rotate, and verify representative dates and times. Check
objects near all cardinal horizons and the overlap between disk faces.

## 10. Milestone 48H - Curate astronomical symbols and content

### Milestone 48H.1 - Bright-star experiment

- compare ordinary circles with filled five-point symbols below magnitude
  1.5;
- keep the star-marker footprint near the 1.5-to-2.0 circular size;
- configure threshold, shape, fill, edge, and size through style;
- accept only after side-by-side paper review.

### Milestone 48H.2 - Deep-sky curation

- prepare a review list of bright or educational globular clusters, open
  clusters, SNRs, planetary nebulae, and galaxies;
- record catalogue provenance and visibility from 33 degrees south;
- let Fernando Selman curate the final packaged selection;
- use existing semantic symbols and render-local selection;
- reject crowding that weakens constellation teaching.

## 11. Milestone 48I - Curate typography and night appearance

### Milestone 48I.1 - Typography

- inventory every physical-planisphere text role;
- compare practical print fonts, weights, and styles at actual size;
- configure the accepted semantic hierarchy without changing geometry;
- verify accents and Spanish glyph coverage before localization.

### Milestone 48I.2 - Night edition

- add a dark-blue/white-star appearance over identical geometry;
- tune labels, references, Milky Way, and symbols for hierarchy;
- test a physical sample under an actual red observing light;
- retain the white-background ESO-blue edition as canonical.

## 12. Milestone 48J - Add general visual-label localization

This is deliberately the last feature stage.

### Milestone 48J.1 - Inventory and semantic keys

- inventory every generated visual label in every chart family;
- separate proper names, catalogue identifiers, and caller text;
- define stable semantic keys by meaning rather than English spelling;
- remove scattered generated-label literals only when their replacement is
  covered by tests.

### Milestone 48J.2 - Shared dictionary and validation

- package one complete English source dictionary;
- generate an initial complete Spanish dictionary for later human curation;
- validate required keys, value types, and deterministic fallback;
- resolve labels through the existing request language and configuration;
- preserve caller-supplied labels verbatim.

### Milestone 48J.3 - Apply across all charts

- route coordinate/reference labels, cardinal directions, months, calendar,
  hours, legends, furniture, and instructions through the shared catalogue;
- prove English parity for every pre-v0.9 chart;
- let Fernando Selman curate Spanish wording after the complete draft exists;
- visually approve both languages on the physical product.

## 13. Milestone 48K - Documentation and v0.9 closure

- update implementation reference, source tree, defaults/schema, user guide,
  README, examples, and command documentation;
- record paired-disk and horizon physical dimensions and accepted assembly;
- run fast, integration, visual, and full suites;
- approve the existing atlas-print regression matrix;
- approve canonical north/south disks, horizon overlay, optional bright-star
  result, curated deep-sky content, typography, night test, and English/Spanish
  products according to their completed scopes;
- mark `target_architecture_v0.9.md` implemented and this roadmap complete;
- assign the release version through the existing Git-tag/setuptools-scm
  authority.

Suggested commit:

```text
Milestone 48K: Close the Wenu v0.9 architecture migration
```

## 14. Stop conditions

Pause and review if a proposed change requires:

- observer-specific stellar coordinates engraved separately from the
  equatorial disk;
- a calendar or horizon module loading catalogues;
- a second renderer or direct artist assembly in an example;
- mirroring a finished image and reversing text;
- embedding a fixed horizon on the rotating celestial disk;
- style changing projection, declination limits, calendar angles, or physical
  dimensions;
- translation keys encoding geometry or executable behavior;
- accepting a measured print-scale, date/RA, handedness, or horizon error for
  visual convenience;
- delaying the first usable disk for optional deep-sky, typography, night, or
  translation work.

## 15. Completion definition

Version 0.9 is complete when Wenu can reproducibly generate, print, assemble,
and use the accepted paired polar disk and latitude-specific horizon product
through the canonical pipeline; configuration and language remain isolated;
existing charts retain their accepted behavior; the full suite passes; and
the architecture, implementation, physical instructions, and reviewed paper
products agree.
