# Wenu migration roadmap: v0.7 to v0.8

**Status:** Active
**Source:** `current_architecture_v0.7.md`
**Target:** `target_architecture_v0.8.md`
**Base commit:** `b72eef8`

## Milestone 46A — Add the semantic AltAz grid

- add native observer-local `AltAzGrid` geometry;
- add `CelestialSphere.add_altaz_grid()` and public exports;
- add independent `altaz_grid` detail and label selection;
- add `--altaz-grid` and `--altaz-grid-labels`;
- retain black semantic AltAz colors and adapt print lines and labels to
  gray `#707070`;
- keep the horizon excluded and chart-owned by default;
- configure all canonical and packaged examples declaratively;
- test geometry, identity, opt-in controls, styling, isolation, and parity;
- compile, run focused and full suites, and visually approve affected charts.

The milestone must preserve `CelestialSphere.draw_chart()` and every v0.7
ownership boundary.
