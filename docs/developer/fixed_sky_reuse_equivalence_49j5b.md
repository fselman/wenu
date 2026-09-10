# Fixed-sky reuse equivalence (Milestone 49J.5B)

**Status:** Linux characterized; awaiting Mac acceptance and visual review.

49J.5B measures `reuse_loaded_sphere` against the retained `cold` oracle on
the accepted three-frame La Ligua circumpolar workload.
`tools/benchmark_fixed_sky_reuse.py` invokes the same sequence orchestrator in
both explicit modes; it is a diagnostic, not an installed interface or second
executor. It emits progress for cold and reused PNG, semantic SVG, and PDF.
Outputs and its JSON report must live outside the repository. Raw sequence
durations and ratios are characterization evidence, with no timing threshold.

Acceptance is exact per frame for requests and orientation provenance;
spherical and projected records; semantic identities; composition, clipping,
export policy, and furniture records; and PNG pixels in RGBA space. SVG
comparison removes only non-graphical metadata and deterministically renames
Matplotlib's volatile marker and clip identifiers, preserving Wenu semantic
identifiers and every graphical attribute. PDF pages are rasterized by Poppler
`pdftoppm` at 150 DPI and compared in the same exact RGBA space. Different
output parent directories normalize to their common frame name.

The report fails closed on unsupported scientific evidence or any difference.
Cold remains the default and independently selectable oracle.

On Linux, all three frames matched exactly across scientific, projected,
clipping, furniture, PNG, normalized semantic-SVG, and rendered-PDF evidence.
At commit `de78e14` with Python 3.12.14, cold versus reused sequence times were
19.004 versus 14.603 seconds for PNG (1.301x speedup), 27.659 versus 23.358
seconds for SVG, and 20.938 versus 16.591 seconds for PDF. Final Mac measurement
and visual acceptance remain pending.

**Runtime effect:** None; the 49J.5A execution modes are unchanged.

**Test behavior effect:** Existing baseline tests gain SVG normalization and
rendered-PDF contracts; no marker, fixture scope, or gate changes.
