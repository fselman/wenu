# Milestone 49F.5B: SVG provenance and advisory-editor locking

## Purpose

Wenu SVG products arrive ready for a graphic designer. Their hierarchy exposes
meaningful objects, their metadata records how the chart was made, and their
initial Inkscape lock state prevents accidental scientific-geometry movement.
The portable Wenu edit policy remains authoritative; the editor lock is a
convenience representation of that policy.

## Provenance contract

An SVG contains at most one standard `<metadata>` element. Wenu preserves the
RDF/Dublin Core metadata written by Matplotlib and adds:

- Dublin Core title, creator, UTC date, MIME format, rights, and description;
- one versioned `wenu:provenance` record;
- product/chart family and Wenu package version;
- source revision (explicit, installed VCS revision, or `unknown`);
- UTC creation time;
- credit, copyright, and optional license as distinct values; and
- the immutable resolved `ChartRequest` as canonical JSON.

The parameter JSON is sorted and compact. Enumerations, paths, tuples, sets,
and nested mappings are converted deterministically. It records chart inputs
and resolved product choices, not credentials, environment variables,
hostnames, temporary paths, or unrelated process state. Output paths remain
part of the resolved product request because they identify the requested
artifact.

Normal exports use the current UTC time with second precision. When
`SOURCE_DATE_EPOCH` is set, its UTC instant is used instead so archival builds
can be reproducible. `WENU_SOURCE_REVISION` may explicitly identify a source
revision. Otherwise Wenu checks installed VCS metadata, the current Git working
copy, and the package-version local segment in that order before reporting
`unknown`.

## Initial editor-lock contract

The existing portable policy has three values:

| `data-wenu-edit` | Meaning | Initial Inkscape state |
|---|---|---|
| `style` | Appearance may change; geometry must remain fixed | locked |
| `layout` | Appearance and placement may change | unlocked |
| `none` | No designer edit is supported | locked |

Physical locking uses Inkscape's `sodipodi:insensitive="true"`. This is an
editor convenience, not access control, and another SVG editor may ignore it.
The `data-wenu-edit` value is therefore still the cross-editor contract.

One physical lock is placed on each supplied semantic owner. A merely
organizational ancestor is never locked just because all the content enabled
in one chart happens to share a policy. For example:

The renderer-neutral `data-wenu-lock-owner-path` records that supplied owner
explicitly. Entity subdivision does not change it: individual constellation
artists may live below `.../lines_western/cru`, while their lock owner remains
`.../lines_western`. The SVG serializer therefore does not infer ownership
from astronomy names or from the accidental shape of a particular export.

- `Constellations` remains unlocked because it is organizational, regardless
  of which constellation components are enabled;
- `Lines-Western` is locked, while its descendant objects are not redundantly
  locked;
- `Labels-Western` remains unlocked because label placement is a layout edit.

This rule also applies to grids: the coordinate-system parent is mixed, its
line-owner branch is locked, and its label branch is unlocked.

Inkscape 1.4.4 acceptance established an important limitation. Its lock is a
selection lock, not a geometry constraint. It prevents ordinary canvas-tool
selection, but an object selected through Layers and Objects or the XML editor
can still be transformed. Applying the same lock redundantly to descendants
does not change that behavior and only makes editing more cumbersome.

Therefore `data-wenu-edit` remains the authoritative workflow contract:

- `style` means appearance changes are supported but transforms are not;
- `layout` means appearance and placement changes are supported; and
- `none` means no edit is supported.

The Inkscape lock reduces accidental canvas edits but cannot enforce that
contract. A future Wenu round-trip validator should compare edited SVG
geometry with the exported source, reject geometry changes to `style` and
`none` content, and permit style-only and declared `layout` changes.

The physical lock is also editor-specific. Illustrator must not be expected
to translate `sodipodi:insensitive` into a native Illustrator lock. Illustrator
can lock native objects and layers, but direct appearance editing requires an
editable selection that can also be transformed. Shared or global colors can
change some appearance indirectly while artwork remains locked, but they do
not provide the complete Wenu `style` contract for strokes, opacity, fonts,
and individual refinements.

## Acceptance

Automated verification covers one metadata element, preservation of existing
Dublin Core content, canonical parameter JSON, reproducible UTC dates, source
revision recording, provenance without semantic artists, owner-branch
locking, mixed-parent behavior, and absence of redundant descendant locks.

Mac acceptance must additionally confirm in Inkscape 1.4.4 that locks appear
in Layers and Objects, ordinary canvas selection respects an owner lock, an
unlocked label remains movable, owner-level styling remains practical, and an
Inkscape Save As round trip preserves provenance, locks, and Wenu policy. The
acceptance record must not claim that Inkscape enforces geometry immutability.
