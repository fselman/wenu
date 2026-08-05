# Wenu target architecture v0.8

**Status:** Proposed
**Source:** `current_architecture_v0.7.md`
**Migration plan:** `wenu_migration_0.7_to_0.8.md`

Version 0.8 begins by completing the semantic coordinate-grid family with an
observer-local `AltAzGrid`. Its semantic detail name is `altaz_grid`, its
public controls are `--altaz-grid` and `--altaz-grid-labels`. Its base
semantic line and label colors are black; print modes realize both as gray
`#707070` so the observer grid remains subordinate to black stars.

AltAz geometry enters the existing spherical-geometry pipeline directly as
azimuth meridians and altitude parallels. It does not create a second grid,
projection, clipping, rendering, or export pipeline. The altitude-zero circle
is excluded by default because the horizon is chart-owned geometry and must
remain visible independently of optional content. AltAz therefore adds no
value to `--grid-references`.

Canonical examples configure the fourth grid declaratively without enabling
it by default. Detail owns selection, style owns appearance, and label
selection remains render-local and grid-specific.
