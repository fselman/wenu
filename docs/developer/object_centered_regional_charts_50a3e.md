# Object-centered regional charts (Milestone 50A.3E)

**Status:** Implemented and merged by PR 98; explicit CLI visual acceptance is
tracked by Milestone 50A.3G.

**Base:** `cadda4c6b609558a98c2b75e4c72dc026c962958`

## Contract

Regional charts may be framed by one explicitly selected constellation set,
packaged target, moving object, or ICRS or horizontal coordinate. Fixed
targets include stars and every supported deep-sky catalogue family. Moving
targets include catalog-backed planets and the Moon plus
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

If independently selected for drawing, the object remains ordinary chart
content. Request-owned asteroid identity is resolved before the chart view and
transported into subsequent drawing adaptation rather than being rediscovered
to decide the center.

## Non-goals

This slice adds no fuzzy or networked name lookup, moving camera, comet,
provider fallback, new projection, new spatial selector, or new renderer. It
does not treat an extended constellation as a point object.

## Acceptance

The focused implementation contracts and the complete macOS gate passed; the
final run reported 2,231 tests. Milestone 50A.3G expands the human inspection
from the two original point-center products to the complete explicit
center/content/mask/orientation matrix.
