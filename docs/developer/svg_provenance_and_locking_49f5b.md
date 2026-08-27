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

Locking is layered from a supplied semantic owner through its entity groups
and drawing primitives. A merely organizational ancestor is never locked just
because all the content enabled in one chart happens to share a policy. For
example:

The renderer-neutral `data-wenu-lock-owner-path` records that supplied owner
explicitly. Entity subdivision does not change it: individual constellation
artists may live below `.../lines_western/cru`, while their lock owner remains
`.../lines_western`. The SVG serializer therefore does not infer ownership
from astronomy names or from the accidental shape of a particular export.

- `Constellations` remains unlocked because it is organizational, regardless
  of which constellation components are enabled;
- `Lines-Western`, its individual constellation groups, and their drawing
  primitives are locked;
- `Labels-Western` remains unlocked because label placement is a layout edit.

This rule also applies to grids: the coordinate-system parent is mixed, its
line branch and line primitives are locked, and its label branch is unlocked.

The layered physical locks reflect an Inkscape 1.4.4 acceptance finding:
locking only an owning group blocked translation but still left descendants
shown as unlocked and allowed their geometry to be resized. With layered
locks, a designer unlocks only the level required by the intended operation:

- unlock the owner for class-level appearance changes;
- unlock one entity group for entity-level appearance changes; or
- unlock one primitive only for a deliberate individual edit.

## Acceptance

Automated verification covers one metadata element, preservation of existing
Dublin Core content, canonical parameter JSON, reproducible UTC dates, source
revision recording, provenance without semantic artists, homogeneous branch
locking, mixed-parent behavior, and layered descendant protection.

Mac acceptance must additionally confirm in Inkscape 1.4.4 that locks appear
in Layers and Objects, locked line geometry cannot be moved or resized, an
unlocked label remains movable, unlocking one line branch enables style work,
and an Inkscape Save As round trip preserves both provenance and Wenu policy.
