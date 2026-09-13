# Solar-System temporal components audit (Milestone 50A.5B.1)

**Status:** Architecture and Encke track presentations accepted by Fernando on
2026-09-13; shared phase-sequence reuse implemented, Mac verification pending

**Supersedes:** The provisional 50A.5B implementation choice that realizes
each comet track symbol through a second `SolarSystemPointLayer` evaluation.

## 1. Reason for the corrective audit

The accepted 50A.5A boundary requires the first drawable comet to reuse the
shared Solar-System point and track pipeline. During visual review, the
provisional implementation made comet symbols visible at major track epochs,
but evaluated those points again in separate layers. That duplicates work
already owned by `SolarSystemTrackRealizer` and is not the intended reuse.

Fernando additionally requires one temporal presentation model that can:

- draw or suppress the sampled path;
- draw or suppress perpendicular major ticks;
- place symbols at no epochs, only the start, or every major epoch;
- place date labels at no epochs, only the start, or every major epoch; and
- evaluate orientation or physical appearance independently at every displayed
  epoch.

The same presentation contract must be usable by symbolic comet, planet, and
minor-body tracks and, at the appropriate seam, by the already shared observed
phase sequences for Venus, Mercury, and the Moon.

## 2. Reuse boundary

Scientific realization and temporal presentation remain distinct.

`SolarSystemTrackRealizer` continues to own apparent directions, the dense
curve cadence, exact major anchors, per-sample provenance, and one transform to
the fixed chart product frame. It evaluates each target direction once. Path,
ticks, symbols, and labels consume that one immutable result.

Observed disk-sequence realizers continue to own physical phase, angular size,
limb, terminator, illuminated face, distance, and independently observed
centre direction. A comet track must not acquire disk physics, and a planetary
phase sequence must not be reduced to a symbolic track.

The common seam is an immutable temporal-component policy applied to exact
start-inclusive major anchors. Both track results and observed disk-sequence
results expose those anchors to the shared presentation orchestration. Their
capability-specific payloads remain distinct.

## 3. Temporal component policy

The request-level policy has four independent fields:

| Component | Values | Meaning |
|---|---|---|
| path | on/off | draw the dense sampled curve |
| ticks | on/off | draw projected perpendicular marks at major anchors |
| symbols | `none`, `start`, `major` | place no symbols, the start symbol, or start plus all major symbols |
| labels | `none`, `start`, `major` | place no dates, the start date, or dates at all major anchors |

`major` is start-inclusive. No combination changes physical sample times,
target evaluation, product frame, resource identity, or provenance.

The accepted CLI adapter is:

```text
--track-path / --no-track-path
--track-ticks / --no-track-ticks
--track-symbols {none,start,major}
--track-labels {none,start,major}
```

Compatibility defaults preserve accepted existing planet and asteroid track
output. The accepted final default for comet symbols remains subject to visual
review. The old `--track-tick-labels` spelling may remain as a compatibility
alias for `--track-labels major`, but conflicting simultaneous forms fail
closed.

## 4. Shared realization object

Track component layers share one request-owned realization object, following
the established `ObservedSolarSystemDiskSequenceRealization` pattern. The
first component realizes and caches the typed result for one realization
context and observer. Later components reuse that exact object. A context or
observer change invalidates the cache deterministically.

The component layers are renderer-neutral views:

- path view: the complete `SphericalCurves`;
- tick view: exact major indices retained for projected annotation;
- symbolic view: centre directions selected from already-realized samples;
- label view: exact ISO dates attached to the selected anchors.

No component reopens a kernel, re-evaluates a target direction, rebuilds the
canonical symbol, or creates a second projection/export route.

## 5. Per-epoch orientation and appearance

Every displayed epoch owns its own appearance payload.

For 2P/Encke, the canonical symbol is placed at an already-realized comet
direction. Its central fan spoke uses provider `PsAng` at that epoch when an
installed provider supplies it; otherwise Wenu evaluates the apparent Sun for
that epoch and derives the antisolar tangent. The comet target direction is
not evaluated again. The documented conjunction/opposition exclusion still
selects the canonical head-only symbol.

Ordinary symmetric point markers require no orientation payload. A future
oriented asteroid or planetary symbol may provide a descriptor-selected
appearance adapter without changing temporal sampling, projection, or
rendering ownership.

For Venus and the Moon, an observed phase display uses the physical disk sample
already produced for that epoch. Mercury retains its separately accepted
frozen-Earth-ecliptic phase model. The common temporal policy chooses which
major samples and dates are visible in both models; it does not recompute or
approximate phase from the track curve. Thus temporal orchestration is shared
while disk physics remains in its accepted owner.

## 6. Required behavior

The following presentations must be expressible from one sampled request:

1. path and ticks, with no symbols or dates;
2. path with only the start symbol and start date;
3. path, ticks, symbols, and dates at every major epoch;
4. symbols and dates at every major epoch, with no path or ticks;
5. only the start symbol, with no path, ticks, or dates; and
6. phase disks and dates at selected major epochs through the same temporal
   component policy, using the existing physical sequence payload.

An explicitly selected instantaneous point remains independent. If it matches
the track start and the temporal policy also requests a start symbol or label,
the request boundary suppresses the duplicate deterministically.

## 7. Tests

Responsibility-owned tests must prove:

- one target-direction evaluation per scientific track sample regardless of
  the visible component combination;
- one shared realization across all track component layers;
- exact `none`, `start`, and start-inclusive `major` selection;
- independent path and tick suppression;
- independent orientation at every displayed comet epoch;
- canonical full versus head-only comet symbol selection;
- provider orientation precedence without target reevaluation;
- no duplicate start symbol or label when an instantaneous point coincides;
- unchanged accepted legacy planet and asteroid track defaults; and
- reuse of the temporal policy by observed Venus, Mercury, and Moon phase
  sequences without moving their physical calculations into track code.

Do not repeat generic projection, renderer, exporter, disk-geometry, phase, or
50A.4 comet numerical-validation tests.

## 8. Stop conditions

Stop if implementation would:

- keep one independently realized point layer per comet track symbol;
- evaluate the target twice at a shared sample epoch;
- make visibility choices change scientific sampling;
- move phase or disk geometry into the track realizer;
- make comet orientation a renderer concern;
- reconstruct the canonical comet symbol per epoch;
- conflate a fixed chart-frame track with an observer-time animation; or
- change an accepted Venus, Mercury, Moon, asteroid, or planet output without
  an explicit compatibility test and visual review.

Fernando accepted this corrective architecture on 2026-09-13. The first
implementation shares one cached `SolarSystemTrackResult` among path and
symbol layers, retains the existing generic observed and frozen-Earth sequence
owners for Venus, Mercury, and Moon phase payloads, and adds the independent path, tick,
symbol-cadence, and label-cadence controls above. Complete Mac regression
remains required before this corrective slice is complete.

Track-owned symbol layers are enabled by the explicit track request and do
not inherit the independent instantaneous-point selection filter. Comet CLI
selection admits the installed exact aliases authorized by 50A.5A, including
`2P`, `2P/Encke`, and `Encke`; the resource collection remains the authority
that resolves any accepted spelling to one installed descriptor and solution.

Fernando visually accepted both requested Encke presentations on 2026-09-13:
independently oriented major-epoch symbols and dates without path or ticks,
and the complete path-plus-ticks presentation using the same symbols and
labels. The focused Mac gate passed all 170 tests in 4.28 seconds before the
canonical-alias and request-owned-symbol corrections; those corrections still
require the final focused and complete Mac gates.

The shared immutable `TemporalComponentPolicy` now owns start-inclusive
`none`, `start`, and `major` selection. Track presentation and the existing
generic observed and frozen-Earth disk-sequence layers all consume it. Venus
and Moon observed geometry and Mercury frozen-Earth geometry remain wholly
owned and fully sampled by their accepted scientific realizers; the policy
filters only the already realized drawable components. Existing defaults and
`--disk-sequence-labels` remain compatible. The optional
`--disk-sequence-symbols` and `--disk-sequence-label-cadence` adapters expose
independent phase-symbol and date selection without moving phase physics into
track code.

Post-projection disk magnification consumes the same selected sample indices
as the phase component layer. It still projects the realization's physical
centres through the accepted shared preparation owner, then selects matching
centres before scaling. This keeps start-only and major-epoch component counts
aligned without a second scientific realization.
