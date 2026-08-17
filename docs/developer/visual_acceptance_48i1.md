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

## Milestone 48I.1B follow-up

The follow-up print candidate uses filled five-point symbols through a
configurable magnitude-0.05 cutoff. With the packaged Hipparcos catalogue this
selects Sirius, Canopus, Arcturus, Rigil Kentaurus, and Vega, but not Capella.
Their magnitudes from -1.5 through 0 are shifted by +1.5 before applying the
48I.1A area law, reproducing the former magnitude-0 through 1.5 areas.
Ordinary circles from magnitude 1.5 through 5.5 are shifted by -1.5 and thus
reproduce the former magnitude-0 through 4 areas. The circular base markers
under the selected five-point symbols are suppressed.

Constellation strokes and the shared right-ascension/equator/ecliptic/Galactic
reference stroke are exactly 50 percent wider than in 48I.1A. Confirm on paper
that the five symbols remain compact, the faint-star field remains legible,
and reference structure does not dominate constellation figures.
