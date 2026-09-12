# Object-centered regional charts (Milestone 50A.3E)

**Status:** Candidate implementation; Mac and visual acceptance pending

**Base:** `cadda4c6b609558a98c2b75e4c72dc026c962958`

## Contract

Regional charts may be framed by one constellation set, one packaged target,
one explicit ICRS or horizontal coordinate, or one unambiguous selected moving
object. Fixed targets include stars and every supported deep-sky catalogue
family. Moving targets include catalog-backed planets and the Moon plus
manifest-backed numbered asteroids; comets can later enter through the same
descriptor overload.

`get_object_center()` receives a resolved typed identity, never an ambiguous
text name. The fixed-target overload uses `CoordinateService`; the moving-body
overload uses `SolarSystemPointLayer` and its accepted provider, light-time,
apparent-correction, and product-frame machinery. Its immutable result retains
identity, display name, coordinate specification, and provenance. It owns no
projection, viewport, field size, style, renderer, or exporter.

## CLI behavior

- This milestone's original spelling is superseded by
  `chart_cli_semantics_audit_50a3f.md`.
- `regional --center-on IDENTIFIER` resolves one uniquely named center;
- `--center-icrs-ra` and `--center-icrs-dec` supply an explicit ICRS point;
- the existing horizontal pair works without a constellation;
- a planet, Moon, or asteroid becomes the center only through `--center-on`;
- selecting one or several bodies for drawing never changes the center;
- observer-time sequences retain the center at the initial chart epoch.

The object remains ordinary selected chart content. Request-owned asteroid
identity is resolved before the chart view and transported into subsequent
drawing adaptation rather than being rediscovered to decide the center.

## Non-goals

This slice adds no fuzzy or networked name lookup, moving camera, comet,
provider fallback, new projection, new spatial selector, or new renderer. It
does not treat an extended constellation as a point object.

## Acceptance

Focused contracts must cover fixed target, explicit ICRS and horizontal
centers, stellar inclusion beyond a magnitude threshold, a unique moving-body
center, ambiguous moving selections, and reuse of a pre-resolved asteroid
descriptor. Fernando must then run the complete Mac suite and inspect one
planet-centered and one `(79989)`-centered regional PNG.
