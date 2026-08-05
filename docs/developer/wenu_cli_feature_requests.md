# Wenu CLI feature requests from the La Ligua chart workflow

These requests are based on the current `main` implementation of:

- `examples/planisphere.py`
- `examples/regional_constellation.py`
- `examples/regional_constellation_group.py`
- `examples/binocular_object.py`
- `src/wenu/charts/chart_arguments.py`
- `src/wenu/charts/style_overrides.py`

Each section below is intended to become one independent GitHub issue with the
`feature` label.

---

## 1. Feature: Add observer location and observing-time CLI arguments

### Problem

The canonical examples hard-code the observer location and time. For example,
the planisphere uses La Ligua and `2026-08-15 21:00`. The existing
`--location`, `--date`, and `--local-time` switches only control context text;
they do not set the observer.

Producing the 22:00 charts therefore required editing or wrapping the examples.

### Proposed interface

```text
--observer-location "La Ligua"
--observer-time "2026-08-15 22:00"
```

Optionally support explicit coordinates when the location is not registered:

```text
--observer-latitude -32.452
--observer-longitude -71.231
--observer-height 52
```

### Acceptance criteria

- All canonical examples accept the same observer arguments.
- Named locations and explicit coordinates are supported.
- Existing hard-coded values remain the defaults, preserving current output.
- Date/time parsing reports a clear error for invalid values.
- Context legends reflect the resolved observer rather than the defaults.
- Tests cover planisphere, regional, and binocular examples.

---

## 2. Feature: Add a common chart-title override

### Problem

Titles are hard-coded in the examples or stored in `GROUPS`. Creating titles
such as `Triángulo del Verano` currently requires changing Python data.

### Proposed interface

```text
--title "Triángulo del Verano"
```

The default title should remain the canonical generated title.

### Acceptance criteria

- `--title` is available to planisphere, regional, group, and binocular charts.
- Unicode titles and accents render correctly.
- Omitting the option produces byte-compatible title text with the current
  examples.
- The output filename stem remains independent of the displayed title.

---

## 3. Feature: Allow arbitrary constellation groups from the command line

### Problem

`regional_constellation_group.py` only accepts keys defined in its hard-coded
`GROUPS` dictionary. Today this required separate wrappers for:

- Libra, Scorpius, Sagittarius, Ophiuchus, and Serpens;
- Centaurus, Crux, and Musca;
- Grus and Piscis Austrinus;
- other teaching groups.

### Proposed interface

```text
--constellations Gru,PsA
```

The same selection should normally drive line figures, boundaries, labels,
centering, and masking. Advanced users should be able to override each role:

```text
--line-constellations Cen,Cru
--boundary-constellations Cen,Cru,Mus
--label-constellations Cen,Cru,Mus
```

### Acceptance criteria

- A user can create a group without editing `GROUPS`.
- The field center is derived robustly across the RA=0/24 h seam.
- `--field-width`, `--field-height`, `--position-angle`, and `--mask` continue
  to work.
- IAU abbreviations are validated with useful errors.
- Serpens can be requested semantically as `Ser` while rendering both line
  components.
- Existing named groups remain supported as convenient presets.

---

## 4. Feature: Add selective constellation rendering and masking to planisphere

### Problem

The shared CLI can turn all constellation lines, labels, or boundaries on and
off, but a full-sky chart cannot select a subset. The requested planisphere
needed figures for a chosen set of constellations, no constellation labels,
and masks for those regions only.

### Proposed interface

```text
--constellations Cyg,Lyr,Aql,Sco,Sgr,Oph,Lib,Ser,Vir,Her,Gru,Cru,Cen
--mask-constellations Cyg,Lyr,Aql,Sco,Sgr,Oph,Lib,Ser,Vir,Her,Gru,Cru,Cen
```

These selections should combine with the existing visibility switches:

```text
--constellation-lines
--constellation-boundaries
```

### Acceptance criteria

- Full-sky charts can select constellation figures independently of labels.
- Selected IAU regions can remain unmasked while the rest of the visible sky
  is dimmed.
- Selection supports Serpens as one semantic constellation.
- Masking remains clipped to the horizon circle.
- `compose_chart()` can infer the normal full-sky legend plan; no custom chart
  subclass is required.
- Tests cover masks crossing the horizon and the RA seam.

---

## 5. Feature: Add common deep-sky layer switches

### Problem

Deep-sky layers are added directly by each example. Users cannot consistently
enable or suppress galaxies, open clusters, globular clusters, planetary
nebulae, supernova remnants, or Milky Way isophotes from the command line.

### Proposed interface

```text
--galaxies
--open-clusters
--globular-clusters
--planetary-nebulae
--supernova-remnants
--milky-way
```

Complementary `--no-*` forms may be useful where an example enables a layer by
default.

### Acceptance criteria

- The switches are shared by all applicable canonical examples.
- Requested layers are loaded and enabled; suppressed layers are neither
  rendered nor included in the object legend.
- Defaults preserve current canonical outputs.
- Cartoon, atlas, print, and presentation policies remain respected.

---

## 6. Feature: Add CLI selection and magnitude limits for deep-sky objects

### Problem

The examples hard-code curated object tuples and catalogue magnitude limits.
Preparing a lesson currently requires editing Python to choose particular
clusters, nebulae, remnants, or galaxies.

### Proposed interface

```text
--open-cluster-objects "NGC 4755,NGC 3766"
--globular-cluster-objects "NGC 5139,NGC 6205"
--galaxy-objects "NGC 5128"
--planetary-nebula-objects "NGC 7293"
--supernova-remnant-objects "G074.0-08.5"

--galaxy-magnitude-limit 11
--open-cluster-magnitude-limit 10
--globular-cluster-magnitude-limit 11
```

### Acceptance criteria

- Explicit object lists and catalogue limits are supported independently.
- Identifiers are resolved through Wenu's catalogues with actionable errors.
- Explicitly selected objects are retained even when the general catalogue
  limit would exclude them.
- Object legends include only enabled classes actually present in the chart.
- Existing curated tuples remain the default presets.

---

## 7. Feature: Add command-line symbol-size overrides

### Problem

Object and stellar symbol sizes are determined by style internals. Enlarging
globular- or open-cluster symbols currently cannot be done with a command-line
option. `ChartStyleOverrides` only exposes constellation and boundary styling;
stellar sizing is set programmatically.

### Proposed interface

```text
--star-symbol-scale 1.3
--galaxy-symbol-scale 1.5
--open-cluster-symbol-scale 1.8
--globular-cluster-symbol-scale 1.8
--planetary-nebula-symbol-scale 1.5
--supernova-remnant-symbol-scale 1.5
```

### Acceptance criteria

- Each scale multiplies the resolved style/mode size rather than replacing
  unrelated style policy.
- The rendered chart and its object/magnitude legends use matching sizes.
- Values must be finite and greater than zero.
- Defaults of `1.0` preserve existing output.
- Overrides work in atlas/cartoon and print/presentation modes.

---

## 8. Feature: Allow arbitrary catalogue or coordinate targets in binocular charts

### Problem

`binocular_object.py --target` currently accepts only `centaurus-a` and
`omega-centauri`. Generating M13 required a Python wrapper that inserted a new
entry into `TARGETS`.

### Proposed interface

Catalogue-name form:

```text
--target "M13"
```

Coordinate fallback:

```text
--target-ra 16:41:41.24
--target-dec +36:27:35.5
--target-title "M13 — Great Globular Cluster in Hercules"
--target-identifier "NGC 6205"
```

### Acceptance criteria

- `--target` resolves common Messier, NGC, IC, and supported Wenu identifiers.
- Coordinate input works without network access.
- Catalogue and coordinate forms are mutually exclusive and validated.
- The target is centered and the title uses the resolved name and identifier.
- `--field-diameter`, style, mode, legends, and output controls continue to
  work unchanged.
- Existing target keys remain valid aliases.
- Tests include M13/NGC 6205.

---

## 9. Feature: Add configurable cardinal labels on full-sky chart borders

### Problem

The planisphere lesson requires only `N`, `S`, `E`, and `O` on the horizon
border. Cardinal-label visibility and language are not represented in the
shared command-line content options.

### Proposed interface

```text
--cardinal-labels
--west-label O
```

Alternatively, a locale-aware form could be:

```text
--cardinal-labels --language es
```

### Acceptance criteria

- Cardinal labels can be enabled independently of AltAz grid lines and labels.
- Labels lie on or just outside the horizon border and remain unclipped.
- East/west orientation follows the chart projection and flip policy.
- Spanish uses `O`; English uses `W`.
- Styling follows the resolved style and output mode.

---

## 10. Feature: Add localization and explicit overrides for semantic labels

### Problem

Reference labels and object-legend labels are hard-coded separately in each
example. Regional charts currently use English labels while the planisphere
uses Spanish. Course charts should not require Python edits to change language.

### Proposed interface

```text
--language es
```

This language selection should apply consistently to constellation labels,
cardinal directions, coordinate references, object legends, magnitude legends,
and automatically generated titles. Constellation labels should retain an
option to use invariant IAU abbreviations:

```text
--constellation-label-format abbreviation
--constellation-label-format localized-name
```

Optional explicit overrides:

```text
--celestial-equator-label "Ecuador celeste"
--ecliptic-label "Eclíptica"
--galactic-plane-label "Plano galáctico"
--stellar-legend-title "Estrellas"
```

### Acceptance criteria

- A shared locale controls reference, cardinal, legend, and standard title
  vocabulary.
- The locale also controls full constellation names when
  `--constellation-label-format localized-name` is selected.
- IAU three-letter abbreviations remain invariant and available in every
  locale.
- At minimum, `en` and `es` are provided.
- Explicit label arguments take precedence over the selected locale.
- Astronomical identifiers and catalogue names are not translated.
- Defaults preserve the current output until a deliberate locale migration.

---

## 11. Feature: Add bright-star names from a curated star-name catalogue

### Problem

Wenu renders stellar positions and magnitudes, but the canonical command-line
interface has no way to label the bright stars needed for teaching and visual
orientation. Adding names manually is error-prone and separates the annotation
from the catalogue identity of the star.

### Proposed interface

```text
--star-names
--star-name-magnitude-limit 2.0
```

Optional controls:

```text
--star-name-catalog iau
--star-name-max-count 25
--star-name-objects Vega,Altair,Deneb
```

The default catalogue should be a curated, versioned catalogue of official IAU
proper star names joined to stable stellar identifiers such as HIP numbers.

### Acceptance criteria

- Bright-star names are joined to stars through stable catalogue identifiers,
  not coordinate proximity alone.
- Labels can be selected by magnitude limit, maximum count, or explicit name.
- Explicit selections remain labeled even when fainter than the general label
  limit, provided the star is present in the chart.
- Automatic label placement avoids the star symbol, chart border, legends, and
  other star labels as far as practical.
- Label visibility is clipped consistently for full-sky, regional, and
  binocular charts.
- Proper names use the official catalogue spelling; `--language` affects
  surrounding semantic text but does not silently translate official names.
- The feature is disabled by default, preserving current output.
- Tests cover Vega, Altair, Deneb, Antares, Achernar, and Canopus.

---

## 12. Feature: Add an angular scale bar to regional and binocular charts

### Problem

Regional and binocular charts state their field size, but do not provide a
direct visual measure of angular separation. For teaching, an angular ruler
near the bottom or side of the chart is more useful than requiring the reader
to infer scale from the total field.

### Proposed interface

```text
--angular-scale
```

Optional controls:

```text
--angular-scale-size 5deg
--angular-scale-position bottom
--angular-scale-label "5°"
```

Supported positions could initially be `bottom`, `left`, and `right`, with an
automatic default chosen by chart family.

### Acceptance criteria

- The scale bar represents a true great-circle angular separation at its
  plotted location under the chart projection.
- Automatic sizing chooses a useful round value such as 30 arcmin, 1°, 2°, 5°,
  or 10° according to the field size.
- Explicit values support degrees and arcminutes.
- The bar and label remain inside the usable chart area and avoid legends.
- Placement works for rotated regional charts and north-up binocular charts.
- Styling follows atlas/cartoon and print/presentation modes.
- The feature is disabled by default, preserving current output.
- Tests verify projected scale accuracy at more than one field size and
  position.

---

## Existing CLI features observed today — no new issue required

The current shared interface already provides:

- `--style` and `--mode`, including presentation output;
- `--magnitude-limit`;
- `--constellation-lines`, `--constellation-labels`, and
  `--constellation-boundaries`;
- AltAz, equatorial, ecliptic, and Galactic grid visibility and labels;
- `--grid-references equatorial,ecliptic,galactic` or `all`;
- `--legends`, `--object-legend`, and `--magnitude-legend`;
- constellation/boundary width and color overrides;
- `--field-width`, `--field-height`, `--position-angle`, and `--mask` in the
  regional examples;
- `--field-diameter` in the binocular example;
- output-path and product-matrix controls.

These controls may need documentation and integration tests, but their basic
feature capability already exists on `main`.
