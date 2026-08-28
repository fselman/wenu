# Wenu current architecture v0.9

**Status:** Implemented current architecture
**Previous baseline:** `archive/architecture_history/current_architecture_v0.8.md`
**Completed migration:** `archive/migration_history/wenu_migration_0.8_to_0.9.md`
**Accepted design:** `archive/architecture_history/target_architecture_v0.9.md`
**Baseline commit:** `5da93cc`
**Closure date:** 2026-08-28

## Purpose

This document is the current architectural authority for Wenu v0.9. It
records the implemented physical-planisphere baseline and the responsibility
boundaries that current and post-v0.9 work must preserve. Detailed public APIs
and file ownership remain in `implementation_reference.md` and
`source_tree.md`. The reviewable as-is structure and coordinate-rationalization
seams are rendered in `diagrams/current_architecture_v0.9_overview.svg` and
`diagrams/coordinate_transformation_as_is_v0.9.svg`. The intended result after
49B/49C is rendered separately in
`diagrams/coordinate_transformation_target_49bc.svg`. Source-level as-is and
proposed structures plus the target runtime call sequence are indexed in
`diagrams/README.md`.

The v0.9 architecture is closed around the accepted canonical physical
polar-planisphere product: paired celestial disks, civil calendar and page
furniture, the latitude-specific folded horizon pouch, reviewed physical
appearance, curated bright and deep-sky content, and shared localization.
The optional night edition remains a later appearance experiment and is not a
condition of the canonical v0.9 architecture.

This closure records architecture and implementation state. It does not claim
that a `v0.9.0` Git tag or distribution release exists; package versions
remain governed by Git tags and setuptools-scm.

## Canonical pipeline

Wenu retains one astronomical and rendering flow:

```text
catalogues or provider state
    -> observer-independent celestial content
    -> explicitly framed spherical geometry
    -> projection-domain guard
    -> coordinate-neutral projection
    -> projected geometry and clipping
    -> chart preparation
    -> canonical renderer
    -> resolved furniture and export
```

Examples, command adapters, physical furniture, and renderers do not acquire
catalogue loading, astronomical transformation, projection selection, or chart
policy. Style and output mode change appearance, not astronomical geometry.

## Ordinary chart architecture

The implemented ordinary workflow separates:

- chart type: projection, framing, viewport, and final boundary;
- style: semantic visual appearance;
- output mode: medium, dimensions, DPI, and presentation scaling;
- detail policy: astronomical selection and density;
- observer: site and observation-time context;
- renderer: realization of prepared graphical records;
- export: one final save per declared product.

One observer-independent `CelestialSphere` may serve multiple chart families,
observers, and instants. Observer-bound realizations use explicit immutable
keys; render-local requests and configuration overlays do not leak state
between commands or products.

Regional, full-sky, all-sky, circumpolar, binocular, and polar-planisphere
products share this pipeline. PNG, PDF, and semantic SVG are output products
of the same resolved geometry and preparation path.

## Physical polar-planisphere product

The canonical v0.9 physical product contains:

- matched north and south celestial disks with independently declared
  declination limits and validated common physical scale;
- opposite face handedness implemented in geometry, never by mirroring a
  finished image or reversing text;
- a 365-day standard-time civil calendar with immutable daily, monthly, and
  label furniture;
- actual-size A4 disk pages with centre, registration, scale, face, and
  assembly records;
- a separate latitude-specific altitude-zero horizon pair;
- an accepted folded A4 pouch with cut window, cardinal furniture, hour scale,
  registration, and assembly geometry;
- deterministic page, pouch, preview, manifest, and command/export ownership.

The celestial disks remain observer-independent. Site and standard UTC offset
calibrate the civil-time relationship and the separate horizon product.
Daylight-saving behavior is instruction policy, not a second astronomical
scale.

Polar projection, calendar geometry, page furniture, horizon transformation,
pouch furniture, rendering, preview, and export remain distinct owners.
Physical millimetre geometry is resolved before Matplotlib realization and is
not inferred from display pixels.

## Content, appearance, and localization

One packaged polar detail policy owns the reviewed stellar, constellation,
Milky Way, Magellanic Cloud, and curated binocular/deep-sky selection. The
canonical physical appearance uses the accepted white-background palette and
reviewed magnitude mapping, including its configured bright-star treatment.

Semantic label keys and packaged language catalogues provide shared English
and Spanish generated text across chart families. Unknown caller text remains
unchanged, and unsupported language identifiers fail explicitly. Localization
does not own geometry, catalogue identifiers, or caller titles.

The optional dark night edition remains deferred until it receives physical
review under red observing light. It must reuse the same geometry and product
pipeline when undertaken.

## Coordinate and temporal boundaries

Every astronomical value must retain explicit frame, origin, epoch, observation
instant, time scale, observer, and apparent/geometric status where applicable.
Projection code remains coordinate-neutral and may not select or relabel an
astronomical frame.

The implemented temporal sequence contracts distinguish physical instants,
civil/display time, sampling cadence, and playback cadence. The accepted
fixed-sky reference keeps the celestial scene and equatorial grid anchored
while the observer-local horizon and AltAz grid rotate. Complete independent
renders remain the correctness oracle for later reuse optimization.

Future typed-state, coordinate-service, provider, moving-object, and reuse
work is governed by `post_v0.9_architecture_roadmap.md` and must preserve this
v0.9 pipeline.

## Configuration and public boundaries

Packaged defaults and schema-version-1 configuration resolve into immutable
typed contracts. User overlays merge non-mutatingly; explicit command values
override overlays; sequential invocations share no active configuration
singleton.

The installed `wenu_chart` interface and canonical examples are adapters over
the same public drawing and export workflow. They do not import one another or
create alternative astronomical, rendering, or physical-product paths.

## Acceptance and regression authority

Automated tests protect scientific geometry, ownership, configuration,
localization, output, and physical-size contracts. Atlas-print remains the
visual regression baseline for ordinary pre-v0.9 families. The accepted
white-background polar disks and folded pouch are the physical v0.9 baseline.

Human inspection remains authoritative for paper scale, readability,
registration, cutting, assembly, classroom use, and appearance. The accepted
49H.3 reference additionally establishes the fixed-celestial-scene and
rotating-observer-horizon behavior.

The routine regression gate is expected to complete in less than 30 seconds on
Fernando's Intel Mac. The complete suite plus any milestone-specific
scientific, SVG, visual, print, sequence, or classroom acceptance remains
mandatory before milestone closure.

## Active authority after v0.9

Current work reads this document together with:

- `implementation_reference.md` for public and advanced API contracts;
- `source_tree.md` for responsibility ownership;
- `post_v0.9_architecture_roadmap.md` for active milestone sequencing;
- `coordinate_transformation_audit_09a2afd.md` for scientific coordinate
  evidence;
- `archive/milestone_history/49f_svg/svg_output_audit_and_plan.md` for SVG product evidence.

The v0.8 architecture, v0.9 target, and v0.8-to-v0.9 migration documents are
provenance. They do not override this implemented baseline.
