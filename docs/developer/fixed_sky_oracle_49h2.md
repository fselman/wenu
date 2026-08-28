# Fixed-sky complete-render oracle

**Milestone:** 49H.2  
**Status:** Oracle planning and PNG comparison implemented; optimized rendering pending  
**Base:** 49H.1 on `feature/fixed-sky-rotating-horizon`

## Purpose

The fixed-sky implementation needs an authority that does not share its future
reuse or caching decisions. For the first circumpolar product, that authority
is the established observer-time sequence: each frame enters the canonical
static request pipeline and completely rebuilds, prepares, projects, renders,
furnishes, and exports the chart at its own observer instant.

Pole-centred circumpolar rendering is the accepted first equivalence domain.
Its celestial geometry is stationary relative to the celestial pole while the
observer-local horizon changes. Other chart families are rejected until their
stable-camera equivalence is independently proved.

## Separate oracle products

`fixed_sky_full_render_oracle_request()` derives an ordinary
`ObserverTimeChartSequenceRequest` from the 49H.1 request but requires a
separate output directory. Candidate frames and oracle frames therefore cannot
silently overwrite or reuse each other.

`generate_fixed_sky_full_render_oracle()` delegates only to
`generate_observer_time_chart_sequence()`. It does not call a fixed-sky
renderer, share prepared candidate geometry, or introduce another export path.
The existing sequence manifest and restart/resume verification remain in
force.

The full-render oracle uses each timeline simulation instant as the ordinary
chart observer time. The explicit celestial anchor remains candidate policy;
it is not substituted into the oracle and is not confused with a catalogue
reference epoch.

## Graphical comparison

`compare_png_frames()` converts both images to RGBA and records:

- dimensions;
- total and changed pixels;
- changed-pixel fraction;
- maximum absolute channel difference;
- mean absolute channel difference.

`PngFrameComparisonTolerance` makes every accepted graphical tolerance
explicit. Its default is exact pixel equality. Dimension mismatches are
errors, not tolerances.

These measurements test final graphical equivalence. Later scientific
comparisons must also inspect renderer-neutral celestial and observer-local
geometry before projection. Pixel agreement alone cannot prove astronomical
correctness.

## Next increment

49H.3 may implement the first fixed-sky circumpolar frame through the canonical
prepared-request/export boundaries. Before caching is added, it must:

1. produce candidate frames in a directory separate from this oracle;
2. compare all candidate frames against complete oracle frames;
3. demonstrate that celestial geometry is anchor-stable;
4. demonstrate that horizon/local geometry follows every simulation instant;
5. retain ordinary furniture, output, and manifest behavior.

Caching remains prohibited until these comparisons pass without shared
candidate/oracle preparation.
