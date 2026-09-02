# Drawable observed Venus disk sequence — Milestone 49I.3C.3.1B

**Status:** Scientifically, architecturally, visually, and operationally accepted  
**Implementation baseline:** `7fd2a6a`  
**Acceptance date:** 2026-08-31

## Accepted capability

Regional and binocular charts can draw Venus at exact major epochs with
`--planet-disk-sequence venus`, `--disk-sequence-model observed`, a start,
one major step, an interval count, optional `--disk-sequence-labels`, and one
object-specific `--planet-disk-magnification venus=FACTOR`.

The start is included, so `n_steps = 3` draws four disks. There is no minor
cadence and no interpolated track curve. Magnification alone cannot enable a
sequence. Single resolved Venus, symbolic Venus, and a Venus disk sequence are
mutually exclusive representations.

## Fixed-frame scientific handoff

Every accepted 49I.3C.3.1A physical sample retains its own apparent instant.
`ObservedVenusDiskSequenceRealization` therefore transforms each centre, limb,
terminator, and illuminated face independently into the chart's one fixed
product frame. Only those transformed samples are aggregated. Native
multi-instant geometry is never assigned a false common coordinate instant.

The aggregate retains sample instants, time scale, observer/AU distances, and
provenance for possible separately governed future 3D use.

## Display and semantics

Four request-owned layers share one sequence realization: illuminated faces,
limbs, terminators, and optional date-label centres. The ordinary spherical
guard, projector, projected geometry, renderer, and PNG/PDF/SVG exporter remain
authoritative.

`MagnifyProjectedDiskSequence` separately projects every physical centre and
scales only the corresponding projected component offsets around that centre.
Factor `1` remains physical angular scale. Semantic paths are rooted at
`sky/solar_system/planets/venus/disk_sequence` with independent
`illuminated`, `limb`, `terminator`, and `labels` children.

## Accepted visual calibration

Fernando accepted a La Ligua regional Virgo chart beginning
`2026-08-30T00:00:00Z`, with 28-day steps, three intervals, date labels, and
magnification 200. It suppressed the default equatorial grid with
`--no-equatorial-grid` and drew only the ecliptic reference with
`--grid-references ecliptic`.

The accepted dates are `2026-08-30`, `2026-09-27`, `2026-10-25`, and
`2026-11-22`. Independently changing position, angular diameter, illumination,
and bright-limb orientation were clear; the very thin 2026-10-25 crescent
remained legible. Labels approached other content but remained readable.

## Verification and boundary

All 211 focused tests passed in 5.74 seconds. The routine suite passed 1,988
tests with 30 deselected in 25.91 seconds. The complete suite passed all 2,018
tests in 85.27 seconds.

Frozen-Earth ecliptic mode, the central six-point Sun, restricted frozen-mode
scene policy, and Mercury remain 49I.3C.3.2 and 49I.3C.3.3.
