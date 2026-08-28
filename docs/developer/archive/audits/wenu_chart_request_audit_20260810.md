# Wenu chart-request usability audit

**Status:** Architectural input for Milestone 46C
**Date:** 2026-08-10
**Scope:** Recent user-produced regional, binocular, and masked-planisphere
scripts compared with the canonical v0.7 examples

## Purpose

This audit identifies work that users currently perform in Python merely to
request another chart of an already supported family. It defines requirements
for the declarative chart-request facade in the v0.8 migration. It does not
make the reviewed scripts permanent examples or authorize another chart
pipeline.

## Reviewed scripts

The review covered thirteen scripts totaling 1,903 lines:

- binocular fields for M13, M16, M17, M57, Omega Centauri, Ptolemy's Cluster,
  and the Veil Nebula;
- regional charts for Centaurus–Crux–Musca, Grus–Piscis Austrinus,
  Libra–Scorpius–Sagittarius–Ophiuchus–Serpens, and the Summer Triangle;
- a copied regional-group generator;
- a masked planisphere.

These are usage evidence, not proposed supported examples.

## As-is adaptation patterns

### Binocular targets

A new target is not currently a parameter-only request. The scripts use one
or more of these procedures:

- copy approximately 250–300 lines of canonical build, composition,
  furniture, Matplotlib, and export code;
- define a new `BinocularTarget` with manually supplied ICRS coordinates and
  aliases;
- determine which physical catalogue represents the object;
- add a target-specific open-cluster, planetary-nebula, supernova-remnant, or
  generic Messier layer;
- extend cartoon enabled-layer policy to include that object family;
- choose a catalogue load limit deeper than the displayed stellar limit;
- mutate the canonical example's target dictionary and parser choices;
- replace its `build_chart()` function or load the installed script through
  `runpy`.

The relevant object-family differences are scientifically meaningful but
should be resolved by Wenu rather than by the ordinary user:

| Requested target | Packaged representation used by the scripts |
|---|---|
| M13 / NGC 6205 | globular-cluster catalogue |
| M16 / NGC 6611 | open-cluster catalogue |
| M17 / NGC 6618 | generic Messier non-stellar catalogue |
| M57 / NGC 6720 | planetary-nebula catalogue under a Galactic PN identifier |
| Omega Centauri / NGC 5139 | globular-cluster catalogue |
| M7 / NGC 6475 | open-cluster catalogue |
| Veil Nebula / Cygnus Loop | supernova-remnant catalogue under a Galactic SNR identifier |

Without that mapping, a chart may be correctly centered yet appear empty or
omit the requested object. Successful export is therefore not sufficient
validation of a target request.

### Regional constellation sets

New regional groups currently require Python dictionaries containing separate
line, boundary, and label identifiers; hand-chosen width and height; a title;
and explicit open-cluster, planetary-nebula, and supernova-remnant lists.
Serpens additionally exposes internal distinctions among `Ser`, `Ser1`,
`Ser2`, `SerCap`, and `SerCau` that an ordinary user should not have to
coordinate.

The specialization scripts load installed examples with `runpy`, mutate their
global group dictionaries, and replace `Observer` to change 21:00 to 22:00.
This demonstrates that location and observation time are scientific request
inputs, not example implementation constants. Current `--location`, `--date`,
and `--local-time` switches control displayed context lines; they do not set
the observer and should not be mistaken for observer inputs.

### Masked planisphere

The reviewed masked planisphere defined a new `FullSkyChart` subclass and
imported a private masking function. Milestone 46C.7I moved that operation
into the ordinary full-sky chart, so mask selection is now a chart request
implemented through chart-owned public behavior for both full-sky and
regional charts rather than copied into user scripts.

## Required public behavior

### Target resolution

Wenu needs one offline, provenance-controlled target resolver that:

- accepts common names, Messier identifiers, NGC identifiers, packaged
  catalogue identifiers, or explicit coordinates;
- resolves aliases to one canonical target identity and coordinate;
- reports ambiguity and unknown names explicitly;
- identifies every packaged object component needed to depict the target;
- retains the requested display name independently of the underlying
  catalogue identifier;
- verifies that the selected load profile can represent the target.

Resolver metadata belongs with packaged catalogue data or a small packaged
cross-identification resource, not in each example script.

### Automatic field content

A maximal sphere makes it possible to select objects by chart footprint and
resolved detail. Ordinary regional and binocular requests should not require
curated lists of every open cluster, planetary nebula, or remnant in the
field. Explicit inclusion and exclusion remain available for publication
control, but automatic spatial selection is the default.

The requested central target must be retained even when it falls below a
general magnitude or size threshold. Wenu must diagnose a central target that
has no drawable packaged representation instead of silently exporting an
apparently empty field.

### Regional identity and framing

A regional request accepts ordinary IAU abbreviations and expands internal
line, boundary, and label identities consistently, including both parts of
Serpens. It computes a useful center and field from the selected authoritative
regions plus configurable padding. Explicit width, height, and position angle
remain overrides, not prerequisites.

Named teaching groups such as the Summer Triangle are immutable data presets
consumed by the same request resolver. Adding a preset does not require a new
generator implementation.

### Observer inputs

The request contract distinguishes values that set the observation from
switches that display metadata. It accepts location and local or timezone-aware
time directly. Existing context-display switches remain compatible but should
eventually use unambiguous names such as `show_location`, `show_date`, and
`show_local_time` in the immutable request model.

### One public generation facade

Python and command-line adapters share one immutable request contract. The
ordinary procedure should be conceptually equivalent to:

```text
resolve request
    -> obtain compatible maximal sphere
    -> resolve target, content, and chart geometry
    -> compose style, mode, detail, and furniture
    -> render and export once
```

The facade delegates to `CelestialSphere.draw_chart()` and established chart
export. It does not reproduce their work.

Representative user requests should eventually be expressible without a new
script, for example:

```text
wenu chart binocular --target M57 --location "La Ligua" \
    --time "2026-08-15 22:00" --field-diameter 6.5 \
    --magnitude-limit 11 --style atlas --mode presentation

wenu chart regional --constellations Cen,Cru,Mus --mask \
    --location "La Ligua" --time "2026-08-15 22:00" \
    --style atlas --mode presentation
```

The final command spelling is chosen when the immutable request contract is
implemented. These examples define usability, not a prematurely frozen CLI.

## Migration consequences

- Milestone 46C.3 must model named object and constellation selection in a
  form usable by the public request facade.
- Milestone 46C.4 must complete late selection and automatic spatial
  filtering across all relevant catalogue families.
- Milestone 46C.5's maximal profile must contain enough catalogue families and
  cross-identification metadata to depict resolved targets.
- Milestone 46C.7 must implement target resolution, observer inputs, automatic
  framing, automatic field content, and non-empty target validation.
- Milestone 46C.8 must replace example-specific target/group construction with
  short declarations over that facade.

Until those milestones are complete, the existing canonical examples remain
the supported public examples and the reviewed scripts remain external usage
evidence.
