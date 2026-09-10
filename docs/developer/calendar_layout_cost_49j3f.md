# Calendar layout cost (Milestone 49J.3F)

**Status:** Mac regression-verified; awaiting Fernando's review.

## Scope and retained oracle

49J.3F examines the complete-suite calendar-layout cost identified by D23
without weakening the physical-containment contract. The visual/slow test
still constructs the real A4 south-face calendar at 300 dpi, realizes the
figure, measures all 83 day and month labels with Matplotlib's canvas renderer,
converts pixel extents to millimetres, and requires every outer text corner to
remain within the 97.5 mm physical disk.

The only removed work was 83 redundant full-canvas redraws. After the initial
draw establishes the renderer, `Text.get_window_extent(renderer=...)`
recalculates each temporarily unrotated text artist directly. Rotation is
restored immediately, and the anchors, font metrics, tangential/outward
extents, physical-unit conversion, corner calculation, assertion, markers,
and gate membership are unchanged. No rendered product or runtime code changes.

## Measurement and fault evidence

At base `6db2272` in the Linux review environment, three isolated cold runs
passed in 6.77, 6.76, and 7.02 seconds; the test call itself took 5.91, 5.98,
and 6.17 seconds. After removing the repeated redraw, three isolated runs
passed in 1.79, 1.88, and 2.14 seconds; calls took 0.86, 0.90, and 1.12
seconds. Median elapsed time fell from 6.77 to 1.88 seconds, about 72 percent,
while median call time fell from 5.98 to 0.90 seconds, about 85 percent.

The full five-test page-rendering module passed in 2.30 seconds. A deliberate
temporary mutation from the accepted 11.5-point month-label size to 40 points
still failed the same physical assertion, reporting an outer corner of 106.64
mm against the 97.5 mm disk radius. The mutation was reverted before commit.

## Acceptance and effects

Acceptance requires three Mac runs of the isolated visual/slow test, the full
page-rendering module, the routine gate, and the complete gate with unchanged
counts. The coordinate-system guide was reviewed and remains current because
the change affects only how a test queries already-realized text extents.

Fernando's Mac baseline passed three isolated runs in 15.47, 15.27, and 14.72
seconds (median 15.27 seconds), with call times of 14.00, 13.86, and 13.33
seconds (median 13.86 seconds). The branch passed in 3.91, 3.14, and 3.09
seconds (median 3.14 seconds), with calls of 1.83, 1.67, and 1.59 seconds
(median 1.67 seconds). The comparable median reductions are 79.4 percent in
elapsed time and 88.0 percent in call time.

Mac regression verification passed 93 focused documentation and page-rendering
tests in 4.77 seconds, 2,108 routine tests with 24 deselected in 27.45 seconds,
and all 2,132 tests in 77.94 seconds. In the complete suite the retained
calendar-containment oracle took 0.41 seconds rather than the baseline
13--14-second call range. The complete total was 7.64 seconds below the prior
49J.3E acceptance run of 85.58 seconds; that single-run difference is
characterization evidence, not a threshold.

**Runtime effect:** None.

**Test behavior effect:** None; the same physical fault model, artists,
measurements, assertion, and markers remain.

## Non-goals

49J.3F does not reduce dpi, sample labels, replace renderer measurements with
nominal font sizes, relax the disk radius, alter typography or furniture,
remove `visual` or `slow`, cache a figure, or change application rendering.
