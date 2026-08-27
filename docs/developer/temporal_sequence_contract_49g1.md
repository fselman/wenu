# Temporal sequence contract

**Milestone:** 49G.1  
**Status:** implemented; focused verification complete  
**Base:** `c70cb29`

## Purpose

Wenu needs reproducible time sequences without creating a second chart,
astronomy, projection, rendering, or export pipeline. A sequence therefore
remains an ordered orchestration of ordinary canonical static renders.

Milestone 49G.1 defines time vocabulary before adding a package sequence
request, CLI, frame manifest, or optimized reuse.

## Public vocabulary

`wenu.temporal` contains two immutable contracts.

### `TemporalTimeline`

A timeline owns:

- one or more explicit, strictly increasing physical instants;
- the physical time scale, currently UTC;
- an IANA civil/display time zone;
- deterministic frame numbering.

Input datetimes must be offset-aware. They are normalized to UTC and retained
as the physical simulation instants. `display_instants` represents those
same instants in the requested civil time zone; it never changes the
astronomical instant.

`TemporalTimeline.uniform(start, stop, count)` constructs an inclusive
uniform sample. Direct construction supports explicitly irregular sampling.
The contract exposes:

- frame count;
- physical simulation duration;
- uniform sampling interval when one exists;
- `uniform` or `explicit` sampling kind;
- deterministic names such as `frame-0000.png`.

The first contract supports UTC only. Additional scientific time scales must
not be added merely as enum values: they require a representation and
transformation policy that preserves their meaning.

### `PlaybackSpec`

Playback owns:

- presentation duration;
- frames per second;
- the implied frame count.

It does not own simulation start, stop, time scale, observer time, or sampling
interval. It may validate that its implied frame count matches a timeline.

For example, twelve physical hours sampled into 180 instants and shown as a
15-second movie at 12 frames per second remain three separate facts:

| Concern | Value |
| --- | --- |
| simulation duration | 12 hours |
| explicit physical instants | 180 |
| playback | 15 seconds at 12 fps |

Playback speed must never be interpreted as physical time.

## Reference adapter

`tools/render_circumpolar_movie.py` is the first contract consumer. It now:

1. resolves one `TemporalTimeline`;
2. resolves one separate `PlaybackSpec`;
3. invokes the ordinary `wenu_chart circumpolar` command for every instant;
4. names PNG frames deterministically;
5. displays civil time using `America/Santiago` by default;
6. passes the physical instant to Wenu;
7. invokes FFmpeg only after all ordinary frames exist.

The adapter remains a correctness reference, not a second renderer. Its
default scientific and playback behavior is unchanged: twelve simulated
hours, fifteen playback seconds, twelve frames per second, and 180 frames.

## Architectural boundaries

49G.1 does not:

- change a chart request or the public `wenu_chart` CLI;
- add a package sequence renderer;
- encode video inside Wenu;
- change observer, ephemeris, projection, clipping, style, or export behavior;
- introduce temporal caching;
- claim that UTC instants solve later epoch, TT, TDB, TAI, UT1, or provider
  requirements;
- add planets, the Moon, satellites, trails, or moving-object layers.

`CelestialSphere.draw_chart()` remains the canonical execution core.

## Next increments

49G.2 now adds the first deliberately narrow consumer: an observer-time
chart sequence pairing one existing `ChartRequest` with one timeline and
repeated canonical static generation.

Later slices may add:

1. deterministic frame manifests;
2. CLI/configuration exposure;
3. complete-render equivalence and cross-product sequence tests;
4. scientifically keyed reuse after independent-frame validation;
5. separate celestial-realization-epoch and provider-time contracts after
   their astrometry and position-provider foundations exist.

Proper motion must not be expressed by changing observer time. Catalogue
reference epoch, celestial realization epoch, provider evaluation instant,
observer instant, civil display time, and playback time are distinct roles.

Reuse or caching begins only after complete independent frames provide a
correctness oracle and scientific cache keys are explicit.

## Verification

The first focused contract and adapter suite passed:

```text
29 passed in 3.42s
```
