# Date-oriented atlas pre-implementation assessment, 2026-10-27

Historical assessment from main `d01248376d9f5e8400575f83053499549604817f`,
`docs/developer/kernel_migration_audit_v1.md`. Its reviewed code base was
`07a03aece766c86f316722200a03253550fbdfb7`; it does not describe current
implementation status. The active audit records #354 acceptance and remaining obligations.

Reviewed main `07a03aece766c86f316722200a03253550fbdfb7`, after PR #351
merge/cleanup and Fernando's clean synchronized Mac report. This is an assessment
and [proposed K4b.06 scope](../../kernel_roadmap_v0.9.5.md#k4b06-proposed-date-oriented-atlas-view-scope),
not an as-built date-oriented atlas claim.

| Current owner | Observed implementation | Integration consequence |
|---|---|---|
| `astrometric_coordinates.LongTermFrame` | Corrected VCW2011/2012 ERFA mean-equatorial/ecliptic orientation; explicit TT equinox/domain, exact matrix/backend identity; unknown physical error | Reuse the admitted model within J-198000..J202000; do not replace it with an Astropy FK5/ecliptic date shortcut |
| `orient_direction_batch` | Validates native nominal astrometric SDK batches/admission, preserves original states and returns an oriented view | This is not an arbitrary contour/grid adapter or persisted catalogue; do not fabricate SDK states for geometry |
| `CoordinateService.transform` | Existing Astropy frame routes preserve spherical carrier kinds/semantics; no `LongTermFrame` route | A common astronomical geometry handoff is missing |
| `CelestialSphere.draw_chart` / layer realization | Native/observer/reception routing, then domain/projection/preparation/rendering; no common dated mean-axis stage | Add the proposed seam before guarding/projection, preserving native source realization; changing projection output alone leaves preparation and recorded spherical data inconsistent |
| `AtlasSheetGeometry` / atlas requests | Design is explicitly ICRS-centred; `SphericalFrame` aligns the projection | A dated numerical tiling needs an explicit derived-view binding; projection alignment cannot stand in for precession |
| `AtlasSheetChart` / `_render_atlas_sheet` | Native-ICRS guard/context; ICRS centre reporting and equatorial grid/furniture conventions | Frame input, truthful centres and ecliptic longitude labels require product work |
| `stellar_realization_sky`, lines and labels | Bound star view exposes native positions; copied dependent layers follow it | Keep stellar TCB evaluation and ownership; orient the resulting geometry coherently without line/label epoch policies |
| Coordinate grids and celestial points | Fixed native grids are supported; other paths use Astropy/date or observer context; equatorial poles are constructed as ICRS points | Distinguish explicitly fixed references from TT mean references; a rotated old grid/pole is not a newly dated reference |
| Boundaries, shapes and source snapshots | Source-defined membership/shapes and source-only snapshot restoration | Preserve source meaning; orientation is coordinate re-expression, not physical evolution or snapshot conversion |
| Atlas publication/workers | Exact scientific input capture, per-process stellar binding, report checks, cleanup and completion last | Extend the same owner with immutable frame capture and worker validation; retain accepted native defaults and static-index disclosure |

The two distinct events are not interchangeable: stellar TCB evaluation determines
positions under admitted motion; TT equinox determines mean-axis orientation.
Frame orientation adds no observer, light-time, parallax, aberration, nutation or
Solar System state. Source-fixed geometry can share target axes without gaining
a new physical propagation model. The finite frame domain does not qualify
stellar accuracy throughout that domain.

The design alternatives are an explicit derived target-axis layout, fixed-ICRS
footprints expressed in new axes, or a new framed-design format. They produce
different product semantics. The proposal selects the first for review and
retains exact source design identity; it does not silently choose it in runtime.
Grids, poles, ticks and reports must agree with that choice. The corrected
first-order-bias matrices require normalization and are not exact orthogonal
rotations; any inverse reference construction needs its own seam verification.

Existing focused gates were run against the pinned source materialization:
52 long-frame cases, 12 coordinate-service cases excluding unrelated zodiac-tool
consumers, 30 atlas sheet footprint/pole/convention/validation cases, and four
native coordinate-grid cases passed. Their times were 1.04, 1.80, 1.10 and
1.13 s respectively. These establish current owner behavior, not acceptance
of the proposed integration. Local source comparisons for frame, coordinate,
sphere, atlas-sheet and design owners matched the pinned GitHub files.
Review log/provenance: scratch `frame-scope-review-v1`, disposable.
No production/resource/dependency/build/test-collection change was made.

