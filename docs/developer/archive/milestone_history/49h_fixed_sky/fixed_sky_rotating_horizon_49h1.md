# Fixed sky and rotating horizon planning contract

**Milestone:** 49H.1
**Status:** Planning contract implemented; rendering and caching pending
**Base:** `f4832dc`

## Purpose

The Earth-rotation presentation must keep a celestial scene and its camera
fixed while recomputing observer-local geometry at each simulation instant.
The ordinary observer-time sequence remains the independent-render oracle.

49H.1 makes the two time owners explicit before any optimization:

| Owner | Time input | Expected frame behavior |
| --- | --- | --- |
| celestial scene and camera | `celestial_anchor_time` | fixed for every frame |
| local observer realization | timeline simulation instant | changes per frame |
| displayed civil time | timeline display instant | changes per frame |
| catalogue astrometry | provider reference epoch and motion policy | separate future scientific input |
| playback | `PlaybackSpec` | presentation only; never physical time |

The celestial anchor is an aware datetime normalized to UTC. It is not inferred
from the first frame, the chart request, a catalogue epoch, or playback.

## Public planning values

`FixedSkyRotatingHorizonSequenceRequest` pairs:

- one immutable `ChartRequest`;
- one `TemporalTimeline`;
- one explicit `celestial_anchor_time`;
- optional playback and effective configuration.

Each `FixedSkyRotatingHorizonFrame` contains:

- a `celestial_request` whose observer location is unchanged and whose time
  is the fixed anchor;
- a `local_observer` with the same location and the frame simulation time;
- the display time, deterministic name, and expected output path.

These values plan ownership only. They do not yet render, cache, write a
manifest, or claim that two pieces of geometry are scientifically reusable.

## Intended canonical execution

A later increment may evolve the established prepared-request boundary so one
canonical export can consume fixed celestial preparation and frame-local
observer geometry. It must not introduce a second sky, projection, renderer,
furniture, or export pipeline.

The frame-local set includes at least:

- semantic horizon;
- cardinal directions;
- AltAz grid and labels;
- above-horizon visibility;
- landscape or Earth mask;
- any future topocentric moving-object realization.

The fixed set may include stars, constellation geometry, deep-sky objects, and
celestial grids only after their frame and realization policies prove this.
The projection and camera remain anchored unless the product explicitly asks
for motion.

## Proper-motion reservation

`celestial_anchor_time` is not a catalogue reference epoch. A future star
provider may realize Gaia or another catalogue from its native epoch under an
explicit space-motion policy and then anchor that realized scene for the
sequence. Long sequences or products that request evolving proper motion must
use a different realization policy rather than silently reusing fixed stars.

## Verification and stop conditions

Before optimized generation is accepted:

1. generate the same instants with complete canonical static renders;
2. define the intended fixed-sky transformation independently;
3. compare astronomical geometry and final pixels within declared tolerances;
4. key every reusable value by frame, epoch/realization policy, anchor,
   observer, projection/camera, selection, and relevant product policy;
5. reject reuse whenever a required key is absent or differs.

Do not add caching before the independent oracle and comparison are executable.
