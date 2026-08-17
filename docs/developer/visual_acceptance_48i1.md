# Visual acceptance — Milestones 48I.1A–B

**Status:** Pending physical printer review

## Scope

This checkpoint calibrates the canonical white-paper polar planisphere for
ordinary color printing. It changes appearance and the stellar aperture inside
the existing disk; it does not change celestial coordinates, projection,
coverage limits, calendar angles, handedness, or the 195 mm cut diameter.

## Expected physical differences

- darker blue stars and text;
- stronger constellation, reference, and boundary strokes;
- a revised stellar curve that preserves magnitude 1, enlarges magnitudes
  2 through 4, and reserves the 1.25 pt² floor for magnitude 5 and fainter;
- day numerals enlarged from 4.3 to 6.45 pt;
- month names set to 11.5 pt and moved slightly closer to the cut edge;
- day values, day ticks, and month names use the same dark ink hierarchy;
- thicker right-ascension and principal reference-plane strokes;
- darker Milky Way and Magellanic Cloud fills;
- an 86 mm stellar-aperture radius instead of 82 mm;
- all month names retained inside the circular cut line.

## Print procedure

Render the two actual-size pages with `tools/render_48e4_polar_pages.py` and
print one representative face using A4, color, normal or high quality, and
100 percent / Actual Size. Disable Fit, Shrink, Economode, Toner Save, and
Draft. Verify the printed 50 mm scale ruler before judging density or size.

## Acceptance checks

- faint magnitude-5.5 stars remain distinct but subordinate;
- bright-star magnitude hierarchy remains readable;
- no Spanish month name touches or crosses the cut line;
- day values and month names can be read through the pouch windows;
- the Milky Way remains subordinate to stars and constellation figures;
- no required blue channel is broken or visibly banded on the printer test;
- the measured ruler is 50 mm and the disk diameter is 195 mm.

Record Fernando Selman's physical-print disposition here after inspection.

## Milestone 48I.1B follow-up and 48I.1C correction

The corrected print candidate uses filled five-point symbols through a
configurable magnitude-0.18 cutoff. With the packaged Hipparcos catalogue this
selects Rigel and every brighter star: Rigel, Capella, Canopus, Sirius,
Arcturus, Rigil Kentaurus, and Vega. The source interval -1.44 through 0.18 is
mapped affinely onto the former magnitude -1 through 0 size interval. Ordinary
circles in the source interval 0.18 through 5.5 are mapped affinely onto the
former magnitude 0 through 4 size interval. The circular base markers under
the selected five-point symbols are suppressed, and the five-point path uses
a compact 0.38 inner radius so its silhouette remains distinct in print.
Milestone 48I.1E scales the five-point marker areas by `1 / 0.38^2`; therefore
the inner pentagon, rather than the complete outer star, carries the former
magnitude -1 through 0 linear scale.

Constellation strokes and the shared right-ascension/equator/ecliptic/Galactic
reference stroke are exactly 50 percent wider than in 48I.1A. Confirm on paper
that the seven symbols remain compact, the faint-star field remains legible,
and reference structure does not dominate constellation figures.
