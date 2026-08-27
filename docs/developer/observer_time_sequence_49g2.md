# Observer-time chart sequences

**Milestone:** 49G.2  
**Status:** implemented; focused verification complete  
**Base:** `c70cb29`

## Purpose

49G.2 pairs one existing immutable `ChartRequest` with one
`TemporalTimeline` and executes every frame through Wenu's canonical static
request generator.

The API is deliberately named for observer time. It does not claim to
represent every kind of temporal astronomical change.

## Public contracts

`wenu.charts.sequence` defines:

- `ObserverTimeChartSequenceRequest`;
- `ObserverTimeChartSequenceFrame`;
- `ObserverTimeChartSequenceFrameResult`;
- `ObserverTimeChartSequenceGeneration`;
- `generate_observer_time_chart_sequence()`.

The request contains one ordinary `ChartRequest`, one `TemporalTimeline`,
and optional `PlaybackSpec` metadata. The current bounded slice requires one
explicitly formatted chart product and a directory output.

For each timeline instant, planning:

1. preserves the complete chart definition;
2. replaces only `ChartObserverRequest.time`;
3. replaces only the static output path;
4. assigns a deterministic name such as `frame-0000.png`;
5. retains both UTC simulation time and civil display time in frame metadata.

Generation then calls `generate_chart_request()` directly for every planned
frame. The public API accepts no alternate generator. Each returned static
output must equal the planned path or the sequence fails.

## Scientific time roles

Future Wenu products may contain several times that must never be conflated.

| Time role | Meaning | Example use |
| --- | --- | --- |
| catalogue reference epoch | epoch at which source astrometry is measured | Gaia DR3 J2016.0 TCB |
| celestial realization epoch | target epoch for propagation and frame realization | proper-motion or precession sequence |
| provider evaluation instant | instant supplied to a moving-object ephemeris or orbit model | Moon, planet, or satellite |
| observer instant | Earth rotation, horizon, local visibility, and AltAz | rotating local sky |
| civil display time | localized label for a physical instant | America/Santiago title text |
| playback time | presentation cadence only | 15-second video |

49G.2 implements only observer-instant variation. A proper-motion sequence
must use a future celestial-realization-epoch contract backed by the
astrometry architecture. It must carry source catalogue and reference epoch,
target epoch, time scale, frame/equinox policy, propagation model, available
proper motion, parallax and radial velocity, uncertainty/quality policy, and
provenance.

Gaia catalogue epochs must not be forced into UTC datetimes. An observer-time
sequence must not be repurposed by pretending its local observation instant
is a catalogue propagation epoch.

## Output and execution boundary

The current sequence requires:

- `all_products=False`;
- explicit `png`, `pdf`, or `svg` output format;
- an output directory rather than a single filename.

Frame results contain the complete ordinary `ChartRequestGeneration`.
`ObserverTimeChartSequenceGeneration.outputs` returns the ordered static paths.

No sequence code:

- constructs a celestial sphere independently;
- chooses or applies projection;
- performs astronomical transformation;
- clips, styles, renders, or saves directly;
- invokes FFmpeg;
- caches state between frames.

## Non-goals and next work

49G.2 does not yet add:

- CLI or configuration;
- a frame manifest;
- title-time templating;
- restart/resume policy;
- multi-product sequences;
- real-frame integration acceptance;
- scientific reuse or caching;
- celestial-epoch or moving-provider sequences.

The complete independent-frame path remains the correctness oracle for later
optimization.

## Verification

The focused temporal, observer-time sequence, reference adapter, request
generation, renderer-boundary, and package-boundary suite passed:

```text
45 passed in 3.47s
```
