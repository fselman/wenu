# Wenu target architecture v0.9

**Status:** Proposed
**Source:** `current_architecture_v0.8.md`
**Migration plan:** `wenu_migration_0.8_to_0.9.md`

## 1. Objective

Version 0.9 adds a publication-quality physical polar planisphere as a normal
Wenu chart product. Its first canonical edition is calibrated for La
Ligua/Papudo, Chile, but latitude, longitude, standard UTC offset, pole limits,
physical dimensions, language, and appearance remain configurable.

The first usable product is a matched pair of north and south polar star
disks. They are printed separately, glued back to back, and later used with
one or more cuttable horizon overlays. Disk acceptance precedes overlay
design; the architecture does not require an early decision about whether the
disk or overlay is the part a user rotates.

## 2. Canonical physical product

The paired product consists of:

1. a south-polar face centred on the South Celestial Pole, extending by
   default from declination -90 degrees through +10 degrees;
2. a north-polar face centred on the North Celestial Pole, extending by
   default from +90 degrees through -10 degrees;
3. a 20-degree overlap around the celestial equator;
4. identical physical disk and calendar-ring radii;
5. a common centre punch and unambiguous back-to-back registration marks;
6. later, a separate latitude-specific horizon overlay with its own hour
   scale and cut path.

Both limiting declinations are independent configurable values. They are
validated as coverage limits, not inferred from the observer horizon. The
overlap may therefore be changed for another physical edition.
When one paired edition requires a common angular scale and disk radius, its
independent limits must produce equal polar angular radii; incompatible
asymmetric coverage is rejected rather than silently rescaled.

The north and south disk faces share one physical rotation axis but are viewed
from opposite normals. Their apparent rotation directions must consequently
be opposite. Wenu reverses angular handedness in geometry and scale placement
for one face; it never mirrors a finished raster or produces reversed text.
Because north/south spherical rotation already reverses stereographic RA
orientation while the direct equidistant convention does not, the paired
resolver verifies paper-coordinate direction rather than assuming that one
identical `flip_ew` rule applies to both projection classes.

## 3. Polar azimuthal-equidistant projection

The physical disks use a backend-neutral polar azimuthal-equidistant
projection by default. Radial distance is proportional to angular distance
from the selected celestial pole:

```text
r = scale * polar_distance
```

For the north face, polar distance is `90 deg - declination`; for the south
face it is `90 deg + declination`. Right ascension supplies the azimuth, with
face handedness and an explicit position angle applied as projection
configuration.

The projection must provide forward and inverse spherical transforms,
projected-radius conversion, viewport construction, and ordinary geometry
dispatch equivalent to existing projections. Projection classes contain no
calendar, horizon, typography, catalogue, or renderer policy.

The same polar-disk chart owner may select stereographic projection for
comparison or specialized editions. That alternative uses the same
equatorial input, selected pole, limiting declination, position angle,
handedness, circular boundary, and physical-size contract; only its radial
projection law changes. The paired classroom product remains equidistant by
default because its declination scale is linear.

The celestial disk uses an equatorial celestial frame suitable for a static
printed atlas. Observer location does not change stellar or constellation
positions on the disk. Site values affect calendar/time calibration and the
later horizon overlay.

## 4. Date ring and midnight convention

Each face carries the same civil-calendar information in the appropriate
handedness:

- exactly 365 daily ticks;
- ordinary non-leap month lengths;
- one closed mean-common-year step of exactly `360 / 365` degrees per day,
  anchored to standard-time local midnight at configurable longitude;
- stronger month-boundary ticks;
- month names centred on their actual month arcs;
- numeric labels only on days 5, 10, 15, 20, 25, and 30 when present;
- day numbers placed radially with their bases toward the outside;
- no leap-day branch or second leap-year scale.

The date scale is astronomical rather than decorative. The eventual horizon
overlay has a fixed `00:00` mark at the bottom. When the observation date on a
disk is aligned with that mark, the implicit midnight meridian runs from the
face's celestial pole vertically upward, even when no continuous meridian is
drawn. The RA on that upward radius is the local sidereal time at civil
standard-time midnight for the configured longitude and UTC offset.

The canonical site uses La Ligua/Papudo coordinates and Chilean standard time
UTC-4. Daylight saving is not encoded in the scale. Printed instructions will
state the one-hour operational correction. A documented common-year
calibration owns the small approximation inherent in ignoring leap years; it
must not silently vary with the machine clock.

Calendar computation produces immutable scale geometry and semantic label
records. Matplotlib only realizes already-resolved lines and text.
The resolved physical furniture reserves a central star-disk radius and keeps
all ticks and label anchors between that radius and the printable disk edge.
Its north/south handedness follows the selected projections rather than a
second independently maintained calendar sign convention.

## 5. Disk astronomical content

The first printable disks contain:

- stars through visual magnitude 5.0;
- magnitude-dependent stellar symbols;
- constellation figures and constellation labels;
- the Milky Way as filled, translucent shading without contour strokes;
- RA meridians at 0h, 6h, 12h, and 18h;
- declination ticks every 20 degrees on those meridians;
- the labelled celestial equator;
- the labelled ecliptic with equinox and solstice points;
- the labelled Galactic plane;
- the relevant ecliptic pole and Galactic pole annotations within each face.

One packaged polar-planisphere detail policy owns this selection for both
faces. Its initial layer set is limited to magnitude-5 stars, constellation
figures and labels, and the Milky Way; projection and face do not alter the
pre-projection catalogue selection.

Constellation boundaries are absent by default. Structural reference features
remain subordinate to stars and constellation figures. Labels must remain
inside the usable disk and avoid the date ring.

The initial classroom edition omits curated deep-sky objects and uses ordinary
circular star symbols. This protects the schedule and establishes a readable
baseline before optional symbol and catalogue curation.

## 6. Bright-star and deep-sky refinement

After the first physical print, v0.9 may select a filled five-point marker for
stars brighter than magnitude 1.5. Its footprint should approximate the
ordinary circular symbols used for stars between magnitude 1.5 and 2.0, so
symbol kind rather than excessive area carries the distinction. Threshold,
marker, and sizing remain style values. A side-by-side print comparison is
required before the treatment becomes canonical.

A later curated content selection may add a deliberately small set of:

- globular clusters;
- open clusters;
- supernova remnants;
- planetary nebulae;
- galaxies.

Selection is explicit packaged data reviewed for naked-eye or binocular
relevance, visibility from about 33 degrees south, educational value, and
crowding. It is not a new hard-coded branch in the renderer or example.

## 7. Canonical and night appearance

The canonical physical edition uses a white background with ESO-blue stars.
Constellation figures, labels, Milky Way fill, reference curves, and
calendar furniture use a restrained related hierarchy. The exact color values
are configuration-owned and visually curated; the architecture does not
embed an unaudited institutional-color literal.

The initial implementation therefore names its blue values provisional and
keeps them in packaged configuration. Visual print review precedes any claim
that the exact color is an approved institutional value.

An optional night edition may use a dark-blue background, white stars, and
high-contrast light structure. It is another style/mode resolution over the
same geometry and content, not another chart type or rendering pipeline. It
must be evaluated under an actual red observing light before acceptance.

## 8. Physical page and assembly contract

The first edition targets two A4 pages and a disk approximately 190-200 mm in
diameter. Exact dimensions remain explicit configuration. Export must support:

- actual-size output with no implicit fit-to-page scaling;
- a physical scale-verification ruler;
- centre-punch marks;
- matching but asymmetric registration marks;
- north/south face identity;
- glue orientation and alignment guidance;
- safe printable margins;
- separate deterministic north and south destinations.

The two faces are initially printed separately and glued blank-side to
blank-side. Duplex-printer support is deferred until manual registration is
proven. Physical furniture is resolved before final save and does not alter
astronomical projection geometry.

## 9. Horizon overlay boundary

Horizon work begins only after both disk faces are physically accepted. A
horizon overlay is an observer-latitude physical template derived from the
canonical altitude-zero geometry. It is not engraved as a fixed curve on the
celestial disk because its orientation relative to RA changes with date and
time.

The canonical overlay is configured for La Ligua/Papudo. It will eventually
provide:

- a cuttable horizon window;
- N, E, S, and W labels;
- a fixed `00:00` mark at the bottom;
- one mark for every hour;
- numeric labels only from 20:00 through 04:00;
- standard time only;
- daylight-saving instructions rather than a second crowded scale;
- centre, registration, cutting, and assembly marks.

The implementation must remain neutral about whether a user rotates the disk
under a fixed overlay or rotates the overlay over a fixed disk. That is an
assembly decision, not astronomical geometry.

## 10. Typography and general localization

Final font-family, font-weight, font-style, and semantic hierarchy curation
occurs only after disk, overlay, and content density are stable. Typography is
configured by semantic role: title, constellation, reference, calendar day,
month, hour, legend, and instruction.

Localization is the last v0.9 implementation stage. It is Wenu-wide rather
than planisphere-specific. One packaged semantic label catalogue covers all
generated visual labels for every chart family. English is the complete source
language and the initial Spanish dictionary is generated for later human
curation. Stable keys, completeness validation, explicit fallback, and
caller-supplied-text preservation replace scattered generated literals.

Proper names, catalogue identifiers, and caller titles remain separate from
interface translation unless an explicit curated astronomical-name mapping
owns them.

## 11. Canonical pipeline

The v0.9 product retains one flow:

```text
catalogues and packaged curated selections
    -> spherical geometry
    -> polar azimuthal-equidistant projection
    -> projected geometry and disk clipping
    -> chart preparation
    -> canonical renderer
    -> calendar/reference/physical furniture
    -> one export per physical page
```

No milestone may put catalogue loading, coordinate transformation,
projection, clipping, or renderer dispatch into an example, calendar module,
horizon template, or translation dictionary.

## 12. Acceptance authority

The first acceptance authority is a real, actual-size La Ligua/Papudo paper
mock-up of both faces. Tests prove scientific geometry and scale contracts;
human review proves readability, registration, gluing, and classroom utility.

Existing atlas print remains the regression baseline for pre-v0.9 chart
families. The new white-background ESO-blue polar edition becomes the visual
baseline only for physical polar-planisphere products.
