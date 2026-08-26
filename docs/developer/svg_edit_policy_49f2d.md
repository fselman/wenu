# Milestone 49F.2D SVG editing classification

**Status:** Implemented; full-suite and Mac editor acceptance complete  
**Base:** `b4b95e2`  
**Branch:** `feature/svg-edit-policy`  
**Acceptance date:** 2026-08-26

## Purpose

49F.2D defines which external edits preserve Wenu's supported meaning. The
classification is renderer-neutral, travels with semantic layer identity, and
is serialized as standard SVG metadata. It describes the product contract; it
does not claim editor-independent enforcement.

## Typed policy

The neutral `wenu.chart_document.EditPolicy` vocabulary contains:

| Policy | Supported external edits | Unsupported edits |
| --- | --- | --- |
| `style` | appearance and visibility | position and geometry |
| `layout` | appearance, visibility, and layout position | scientific source geometry |
| `none` | no supported external edit | all editing operations |

Ordinary scientific layers resolve to `style`. Semantic layer names ending in
`_labels` resolve to `layout`. A layer may explicitly declare
`semantic_edit_policy="none"` or another valid policy. Unsupported declared
values are rejected rather than silently downgraded.

This initial rule is deliberately narrow. Future semantic categories must add
an explicit policy instead of relying on translated text, Matplotlib artist
type, or SVG position.

## SVG representation

Each annotated semantic artist includes a composable policy class and data
attribute:

```xml
class="... wenu-edit-style ..."
data-wenu-edit="style"
```

or:

```xml
class="... wenu-edit-layout ..."
data-wenu-edit="layout"
```

The data attribute is the authoritative editing classification. The class is a
standard SVG selection hook for future shared styling and editor workflows.
Neither value changes geometry, clipping, style, visibility, or paint order.

## Meaning of protection

The policy is a workflow guard, not tamper-proof protection. Standard SVG has
no universal lock mechanism enforced by every editor. A user can still move a
`style` artist in a general-purpose editor, but that produces a scientifically
modified derivative outside Wenu's certified editing contract.

Advisory Inkscape locking metadata remains deferred. It may later improve the
editing experience, but it must not replace the standard `data-wenu-edit`
classification or become authoritative.

## Regional acceptance

The accepted Centaurus, Crux, and Musca regional SVG contained 232 semantic
artists with this distribution:

| Policy | Artists | Semantic ownership |
| --- | ---: | --- |
| `layout` | 4 | constellation labels |
| `style` | 228 | constellation lines, equatorial grid, Milky Way, stars, galaxies, clusters, and remnants |
| Missing or unexpected | 0 | none |

The SVG opened normally in Inkscape and remained visually identical. Fit
behavior and individual selection were unchanged. The XML Editor exposed
`wenu-edit-layout` and `data-wenu-edit="layout"` on constellation-label
artists, and `wenu-edit-style` with `data-wenu-edit="style"` on scientific
artists. A label remained movable as expected.

A separate Inkscape Save As round trip preserved all 232 semantic artists and
the complete 4-layout / 228-style classification.

## Font capability completed by 49F.3

At 49F.2D acceptance, Matplotlib still converted visible text to paths and this
section recorded font editing as deferred. Milestone 49F.3 subsequently
established one SVG contract with genuine text elements and verified
font-family, size, weight, color, wording, and label-position edits in Inkscape.
The authoritative current user contract is
`docs/user_guide/svg_output.md`.

## Contracts and deferred work

49F.2D establishes:

- a typed renderer-neutral editing-policy vocabulary;
- deterministic default policy resolution from semantic ownership;
- explicit policy overrides and validation;
- standard SVG policy classes and data attributes;
- representative Inkscape visibility and round-trip preservation.

It deliberately defers:

- editor-specific advisory locks;
- shared class-level style rules;
- parent semantic and semantic-fragment groups;
- editable SVG text and font policy;
- explicit output-format selection;
- dense binocular SVG optimization.

## Verification

The final complete suite passed 1,601 tests in 57.71 seconds. The working tree
was clean and `git diff --check` reported no whitespace errors.
