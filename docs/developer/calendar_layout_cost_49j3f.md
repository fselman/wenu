# Calendar layout cost (Milestone 49J.3F)

**Status:** Implementation complete; awaiting Mac regression evidence.

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

**Runtime effect:** None.

**Test behavior effect:** None; the same physical fault model, artists,
measurements, assertion, and markers remain.

## Non-goals

49J.3F does not reduce dpi, sample labels, replace renderer measurements with
nominal font sizes, relax the disk radius, alter typography or furniture,
remove `visual` or `slow`, cache a figure, or change application rendering.
