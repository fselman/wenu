# Resolved apparent Moon and fixed-chart multi-epoch sequence plan

**Proposed milestone:** 49I.3E  
**Status:** Accepted and closed on 2026-09-02  
**Prerequisite:** 49I.3D.1 apparent major-planet symbolic points, merged in PR #69 at `926d17b`

## 1. Objective

Replace the Moon's provisional large hollow symbolic point with a physically meaningful illuminated lunar disk while reusing the accepted moving-body appearance and multi-epoch machinery already used by Venus and Mercury.

The resolved Moon is the default whenever `--moon` is selected. An explicit symbolic mode remains available for compatibility and diagnostic use.

The resolved Moon must be drawable in every ordinary chart family:

- regional
- binocular
- circumpolar
- planisphere
- Mollweide all-sky

This milestone includes explicit display magnification and an observed multi-epoch lunar disk sequence.

## 2. Governing time rule

Two different time roles must remain explicit.

### 2.1 Chart epoch

The ordinary chart observer time defines one fixed product reference:

- star positions and proper-motion evaluation
- coordinate grids
- horizon and viewport
- chart projection
- projection tangent plane and its orientation
- labels and other chart furniture

The chart reference is not rebuilt for every Moon sample.

### 2.2 Lunar sample epochs

For a sequence, the physical epochs are defined by:

```text
--disk-sequence-start ISO_TIME
--disk-sequence-step DURATION
--disk-sequence-n-steps COUNT
```

At every sample epoch Wenu must independently realize:

- apparent lunar centre direction
- observer–Moon distance
- physical angular diameter
- Sun–Moon–observer phase angle
- illuminated fraction
- bright-limb position angle
- the resolved illuminated-disk boundary

The sample's centre and appearance are then transported into and projected through the single chart reference defined at the chart epoch.

Consequently, the result is a genuine changing lunar path and phase sequence superimposed on one fixed chart. It is not a sequence of independently rotated charts.

For an observer-bound fixed AltAz chart, this means preserving the sample-epoch apparent direction in the inertial/apparent direction representation and evaluating it in the chart epoch's fixed product frame. The implementation must not mistake a sample epoch's instantaneous AltAz frame for the frozen chart frame.

## 3. Physical model

The numerical audit must select, cite, and freeze the lunar physical constants and models before drawable implementation.

The first model requires:

1. The accepted apparent lunar centre from the shared astrometric/apparent correction chain.
2. Observer–Moon distance from the same accepted state.
3. A documented lunar physical radius and physical angular diameter.
4. Sun–Moon–observer phase angle.
5. Illuminated fraction for a spherical Moon.
6. Bright-limb direction measured in the apparent ICRS tangent plane from celestial north toward east.
7. Explicit transport of that tangent direction into the fixed chart tangent-plane basis.

The physical state must be renderer-neutral and immutable. Display magnification must never change its recorded distance, physical angular diameter, phase angle, illuminated fraction, or position angle.

## 4. Reuse requirements

No Moon-specific parallel rendering pipeline is authorized.

The implementation must reuse or generalize the accepted machinery for:

- body descriptors and catalog capabilities
- observer and ephemeris ownership
- apparent centre realization
- `SolarSystemApparentDisk` or its accepted generic successor
- illuminated spherical-disk geometry
- tangent-plane orientation
- display magnification
- generic single-disk factories
- generic multi-epoch sequence requests and realization
- ordinary projection, clipping, rendering, semantic identity, and export
- PNG, PDF, and semantic SVG output

Moon-specific code should be limited to descriptor/catalog data, physical constants whose ownership genuinely belongs to the Moon, and validated model selection. It must not duplicate the Venus/Mercury sequence renderer.

## 5. Public interface

### 5.1 Single Moon

```text
--moon
--moon-appearance resolved|symbolic
--moon-disk-magnification FACTOR
```

Policy:

- Supplying `--moon` defaults to `resolved`.
- `--moon-appearance symbolic` explicitly requests the compatibility symbol.
- Magnification is positive, finite, bounded, Moon-specific, and presentation-only.
- A resolved disk is permitted in every chart family, including planisphere and all-sky.
- Omitting `--moon` continues to omit the Moon.

### 5.2 Multi-epoch Moon

```text
--moon-disk-sequence
--disk-sequence-model observed
--disk-sequence-start ISO_TIME
--disk-sequence-step DURATION
--disk-sequence-n-steps COUNT
--disk-sequence-labels
--moon-disk-magnification FACTOR
```

The public Moon selector adapts into the same internal descriptor-driven sequence request used by planetary sequences.

Only the observed model belongs to the first milestone. A frozen-Earth lunar model is scientifically distinct because the Moon orbits Earth and requires a separate definition and validation.

## 6. Rendering policy

- The physical disk centre is always the accepted apparent lunar centre.
- The terminator and bright limb follow the sample epoch's actual illumination geometry.
- Magnification enlarges the disk around its own projected physical centre.
- Magnification must not move the centre or modify the physical state.
- Planisphere and all-sky products use the same resolved geometry, not a fixed crescent glyph.
- Clipping uses the fixed chart viewport and product boundary.
- Sequence labels, when requested, use the shared sequence labeling policy.
- The Moon retains stable semantic identity under `sky/solar_system/natural_satellites/moon`.
- Full names remain available in semantic metadata even when symbolic compatibility mode is selected.

## 7. Explicit non-goals

The first resolved-Moon milestone does not include:

- lunar surface texture or albedo maps
- craters or named features
- topographic terminator relief
- optical or physical libration rendering
- axis or prime-meridian orientation
- Earth shadow or lunar-eclipse rendering
- atmospheric refraction across the resolved disk
- occultation contact prediction
- frozen-Earth lunar sequences
- animation-specific interpolation

These require separately bounded capabilities.

## 8. Implementation slices

### 49I.3E.0 — Scientific and architecture audit

Output only documentation and validation design.

- Select authoritative lunar radius and ephemeris quantities.
- Define the apparent centre, distance, phase, illumination, and bright-limb equations.
- Specify tangent-basis transport from sample epoch to chart epoch.
- Audit the generic Venus/Mercury appearance and sequence seams.
- Identify any remaining planet-specific names that must become descriptor-driven.
- Freeze CLI vocabulary, defaults, magnification bounds, tolerances, and non-goals.

No runtime or visible output changes.

### 49I.3E.1 — Numerical lunar appearance state

- Add lunar catalog appearance capability and immutable physical state.
- Implement the Moon through the generic appearance realizer.
- Add an installed-ephemeris validator that refuses downloads.
- Compare centre, distance, angular diameter, phase angle, illuminated fraction, and bright-limb angle with an independent calculation.
- Change no chart output.

### 49I.3E.2 — Resolved single-epoch Moon

- Make resolved appearance the default for `--moon`.
- Add explicit symbolic compatibility mode.
- Add Moon-specific display magnification.
- Enable resolved drawing in all five chart families.
- Preserve one shared projected centre and semantic entity across PNG/PDF/SVG.

### 49I.3E.3 — Fixed-chart multi-epoch Moon

- Add `--moon-disk-sequence`.
- Reuse the generic observed sequence realization and renderer.
- Compute physical centre and appearance at every requested sample epoch.
- Project every sample through the chart epoch's fixed frame and tangent plane.
- Support labels and shared export formats.
- Reject unsupported frozen-Earth lunar requests clearly.

Each slice requires separate numerical, automated, and—where drawable—visual acceptance before the next slice begins.

## 9. Automated contracts

Tests must cover at least:

- default-off Moon selection
- resolved default after `--moon`
- explicit symbolic compatibility mode
- CLI parsing and invalid combinations
- finite positive magnification and bounds
- unchanged physical metadata under magnification
- shared descriptor/factory ownership
- no Moon-specific renderer
- independent state at every sequence epoch
- chart epoch distinct from every sample epoch
- fixed projection/tangent frame across all sequence samples
- transported bright-limb orientation
- stable centre under magnification
- planisphere/all-sky/regional/circumpolar/binocular enablement
- viewport and horizon clipping
- semantic identity and localized full name
- PNG/PDF/SVG projected-record parity
- no ephemeris download in the validator
- compatibility behavior for `--moon-appearance symbolic`
- rejection of unsupported sequence models

## 10. Numerical validation

Use an installed DE440-family kernel already accepted by Wenu and refuse network downloads.

Validate representative cases covering:

- new, crescent, quarter, gibbous, and full phases
- near perigee and apogee
- northern and southern bright-limb orientations
- Moon near a chart boundary
- sequence samples on both sides of the chart epoch
- at least one sample below the fixed chart horizon
- phase-angle wrap and position-angle wrap

Declare component tolerances before inspecting residuals.

## 11. Visual acceptance matrix

For La Ligua, produce:

1. Regional resolved Moon at several phases.
2. Binocular resolved Moon at physical and magnified scales.
3. Circumpolar or suitable regional boundary-clipping case.
4. Planisphere resolved Moon with and without magnification.
5. Mollweide all-sky resolved Moon with and without magnification.
6. Observed multi-epoch sequence on a fixed chart, showing changing position, size, phase, and orientation.
7. The same sequence with labels.
8. PNG/PDF/SVG comparison from the same projected records.
9. Explicit symbolic compatibility render.

Visual review must confirm:

- centre positions are unchanged by magnification
- phases and bright-limb directions are plausible and evolve continuously
- the background and projection do not rotate between samples
- the sequence is readable without implying false physical disk sizes
- clipping creates no folds, chords, inverted fills, or seam artifacts
- planisphere and all-sky output remain legible

## 12. Documentation closure

After acceptance:

- update the user guide with resolved/symbolic Moon examples
- document magnification as nonphysical display scaling
- document the fixed-chart/sample-epoch distinction
- update the implementation reference, roadmap, source tree, and assistant instructions
- record numerical validator results, focused/full suites, and visual acceptance
- mark 49I.3E accepted only after all authorized slices pass

## 13. Closure

All four authorized slices are complete:

- 49I.3E.0 froze the scientific and architectural contract without runtime
  changes.
- 49I.3E.1 added and independently validated output-neutral lunar appearance
  state.
- 49I.3E.2 made the resolved single-epoch Moon drawable in all five ordinary
  chart families while preserving symbolic compatibility.
- 49I.3E.3 added the observed fixed-chart Moon sequence through the shared
  descriptor-driven sequence machinery.

Fernando scientifically and visually accepted the completed program on
2026-09-02. Final 49I.3E.3 closure passed 75 documentation tests, 161 expanded
focused tests, 2,088 routine tests with 30 deselected, and all 2,118 tests.
PRs #70 through #73 are merged; the final merge is `bc45cc0`. Parent-closure verification passed 76 documentation tests in 9.55 seconds, 2,089 routine tests with 30 deselected in 31.89 seconds, and all 2,119 tests in 87.44 seconds.

The parent milestone adds no capability beyond its accepted slices. Frozen-Earth lunar sequences, interpolation, animation, surface texture, libration,
eclipses, refraction across the disk, and occultation prediction remain
separately governed non-goals.
