# Fixed-sky reuse equivalence (Milestone 49J.5B)

**Status:** Accepted and merged in `a028e89` through PR #89.

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
`pdftoppm` at 150 DPI or the built-in macOS `sips` fallback and compared in the
same exact RGBA space. Renderer availability is checked before the expensive
sequences begin. Different
output parent directories normalize to their common frame name.

The report fails closed on unsupported scientific evidence or any difference.
Cold remains the default and independently selectable oracle.

On Linux, all three frames matched exactly across scientific, projected,
clipping, furniture, PNG, normalized semantic-SVG, and rendered-PDF evidence.
At commit `de78e14` with Python 3.12.14, cold versus reused sequence times were
19.004 versus 14.603 seconds for PNG (1.301x speedup), 27.659 versus 23.358
seconds for SVG, and 20.938 versus 16.591 seconds for PDF. Final Mac measurement
and visual acceptance remained pending at that checkpoint.

Fernando's final Mac run at commit `167d379` used Python 3.11.7 on
macOS-10.16-x86_64-i386-64bit. All three frames matched exactly for scientific
evidence and for PNG, normalized semantic SVG, and rendered PDF; PDF comparison
used the built-in macOS `sips` renderer. Cold execution built three canonical
spheres and reuse execution built one. Cold versus reused sequence times were
35.897 versus 25.267 seconds for PNG (1.421x), 55.511 versus 49.019 seconds for
SVG (1.132x), and 34.934 versus 28.094 seconds for PDF (1.243x). Fernando also
visually accepted the six paired PNG frames. These values are characterization
evidence, not enforced thresholds.

**Runtime effect:** None; the 49J.5A execution modes are unchanged.

**Test behavior effect:** Existing baseline tests gain SVG normalization and
rendered-PDF contracts; no marker, fixture scope, or gate changes.
