# Observer-dependent comet model-magnitude audit (Milestone 50A.5D.1B)

**Status:** Accepted by Fernando on 2026-09-14; documentation only. This audit
authorizes only the bounded 50A.5D.1B implementation.

**Exact base:** `15c77d95653d24f37ef6140385eef52702f0720d`

## 1. Purpose

Extend the explicit network command `wenu_retrieve_comets` with an optional
observer-dependent Horizons characterization. For every exact SBDB comet
solution selected by the accepted perihelion-time and perihelion-distance
filter, Wenu may request sampled Horizons observer-table magnitude values and
report the brightest sampled model value and its epoch.

This remains a characterization of a provider model. It is not a visibility
forecast and makes no claim about altitude, solar elongation, twilight, weather,
coma activity departures, angular extent, sky background, telescope aperture,
exposure, detector response, saturation, or detectability.

## 2. As-is assessment

The accepted 50A.5D.1A path has a narrow ownership boundary:

- `src/wenu/comet_discovery.py` owns the deterministic SBDB query, typed
  discovery records, time-scale conversion, sorting, and provider provenance;
- `src/wenu/cli/comets.py` owns table and JSON serialization;
- `tests/test_comet_discovery.py` owns the closest stable public-route and
  parser responsibility and currently proves that `--observer-location` is
  rejected;
- the command performs explicit network discovery and is not called by import,
  chart construction, preflight, rendering, or export;
- discovery records already retain `M1`, `M2`, `K1`, and `K2` as
  photometric-model parameters, not apparent magnitudes.

No current component queries a Horizons observer table for discovery
photometry. The accepted minor-body SPK provider contains dynamical state and
must not become the owner of this network characterization. The chart CLI,
projection, preparation, renderer, exporters, and immutable SPK cache require
no change.

The coordinate-system guide was reviewed. Model magnitude adds no coordinate
or product frame. Observation UTC, Horizons integration time, perihelion TDB,
and the epoch attached to a sampled magnitude remain distinct.

## 3. Provider evidence

The JPL Horizons observer table's selectable quantity 9 is “Visual magnitude &
surface brightness.” For comets its columns are `T-mag` and `N-mag`, with
the documented laws

```text
T-mag = M1 + 5 log10(delta) + k1 log10(r)
N-mag = M2 + 5 log10(delta) + k2 log10(r) + phcof beta
```

where `delta` is observer distance, `r` is heliocentric distance, and
`beta` is phase angle. Some comets use custom laws described in the returned
ephemeris. Horizons can return `n.a.` outside a model's applicable range or
when a quantity is unavailable.

Horizons describes small-body magnitudes as approximately accurate to
0.1 magnitude in principle but advises treating them as uncertain at roughly
1 magnitude in practice; errors may exceed 1 magnitude above 90 degrees phase,
and values above 120 degrees have reduced precision. Wenu must preserve that
warning and must not manufacture a tighter uncertainty.

The JPL SSD API fair-use policy requires reasonably necessary requests,
sequential rather than simultaneous API calls, reuse of unchanged results,
handling rate limits and service failure with backoff, and checking the API
version.

Primary references:

- JPL Horizons System manual,
  <https://ssd.jpl.nasa.gov/horizons/manual.html>;
- JPL Horizons API documentation,
  <https://ssd-api.jpl.nasa.gov/doc/horizons.html>;
- JPL SSD/CNEOS API fair-use policy,
  <https://ssd-api.jpl.nasa.gov/>.

## 4. Proposed public contract

```text
wenu_retrieve_comets START STOP
    [--max-perihelion-distance AU]
    [--observer-location NAME]
    [--magnitude-step DURATION]
    [--format table|json]
    [--output PATH]
```

Without `--observer-location`, output and network behavior remain exactly the
accepted 50A.5D.1A contract.

With `--observer-location`:

1. `START` and `STOP` retain their existing meaning as complete inclusive
   UTC civil days for both SBDB selection and the bounded magnitude sampling
   interval.
2. The location must resolve through Wenu's existing governed observer
   registry. Wenu sends explicit longitude, latitude, and height to Horizons;
   a display name alone is not provider geometry.
3. `--magnitude-step` is a positive whole number of hours or days. The
   proposed default is `1d`. Samples include the start boundary, regular
   interior steps, and the stop boundary if it is not already a regular sample.
4. Wenu makes at most one sequential Horizons observer-table request per exact
   selected solution, requesting quantity 9 in machine-readable form.
5. Each request uses the same exact solution/apparition identity rules already
   accepted for comet acquisition. A record number is never derived
   arithmetically and a provider ambiguity fails closed.
6. Wenu reports the numerically smallest valid sampled `T-mag` as
   `brightest sampled total model magnitude` and its UTC epoch. It may also
   report the corresponding `N-mag` independently, but nuclear magnitude is
   not substituted for missing total magnitude.
7. Every `n.a.`, blank, non-finite, or absent series becomes `unknown`.
   Unknown values sort after all known values and never become zero.
8. The result retains the observer coordinates and height, sampling interval,
   cadence, exact sample epochs, Horizons API version, target/solution
   identity, requested quantity, raw-response SHA-256 digest, retrieval time,
   and any custom-law or reduced-precision notice supplied by Horizons.
9. Table output labels the value `brightest sampled T-mag model`; JSON uses a
   typed structure with value, unit `mag`, quantity `T-mag`, epoch and time
   scale, model/provider identity, and warning text.
10. This command remains explicit and networked. It is not a chart preflight
    action and it does not write or alter a minor-body SPK resource collection.

## 5. Bounded-load and failure policy

Before implementation Fernando must accept a finite request budget. The
recommended first bound is:

- at most 50 selected comet solutions in a magnitude-enabled invocation;
- at most 367 sample epochs per comet;
- sequential provider calls only;
- no automatic retry loop beyond one bounded retry after a provider-indicated
  wait;
- fail before the first Horizons request if the requested row/sample budget is
  exceeded, explaining how to narrow the date range, perihelion-distance
  filter, or cadence.

An implementation may use an immutable content-addressed response cache keyed
by exact target solution, observer coordinates and height, inclusive sampling
bounds, cadence, requested quantity, and provider/API version. Such a cache is
discovery-photometry evidence, not the minor-body SPK cache and not the future
50A.5E distributable database.

SBDB success followed by partial Horizons failure must not silently produce an
apparently complete ranked list. The result either fails as a whole with a
clean diagnostic or, if Fernando explicitly chooses partial-results semantics
during review, identifies every failed row and marks the entire result
incomplete. The recommended first implementation is fail-whole.

## 6. Adopt / adapt / reject / defer ledger

| Topic | Decision proposed for review | Reason |
|---|---|---|
| Horizons quantity 9 | Adopt | It is the authoritative realized provider value. |
| Provider `T-mag` | Adopt as the primary summary | It is the comet total-magnitude model. |
| Provider `N-mag` | Preserve separately when present | Nuclear and total models are scientifically distinct. |
| Local recomputation from M1/M2/K1/K2 | Reject | It can omit custom laws and provider applicability rules. |
| Daily default cadence | Adapt with explicit endpoint inclusion and budget | Reproducible and bounded, but not a proof of the continuous minimum. |
| “Minimum magnitude” wording | Reject | It falsely suggests a continuous extremum. |
| “Brightest sampled model magnitude” wording | Adopt | It states exactly what was evaluated. |
| Visibility ranking | Reject | Magnitude alone omits altitude, twilight, atmosphere and instrument response. |
| Parallel Horizons requests | Reject | Conflicts with the provider fair-use policy. |
| Partial silent results | Reject | They make ordering and completeness ambiguous. |
| Chart integration | Defer | Discovery characterization is not rendering or chart preflight. |
| Empirical comet-activity correction | Defer | Requires a separate photometric/scientific model and validation. |

## 7. Implementation seam after acceptance

The smallest implementation may add one typed Horizons photometry request and
result beside `comet_discovery.py`, or in a narrowly named provider module if
the HTTP/parser responsibility would otherwise obscure SBDB ownership.
`cli/comets.py` composes the accepted discovery records with those typed
results. It must not import chart, renderer, projection, or minor-body SPK
acquisition owners.

The closest test file is `tests/test_comet_discovery.py`. Extend it rather
than creating a milestone-named test file. Protect only the new seam and fault
models: option validation, endpoint sampling, exact solution binding,
`T-mag`/`N-mag` distinction, `n.a.`, provider notices, provenance,
request budgeting, sequential behavior, and clean failure. Do not repeat the
existing SBDB parser and sorting matrix.

A frozen, exact provider response owns ordinary tests. One deliberate live
smoke test may be marked according to the existing network/integration policy;
it is not part of the routine gate.

## 8. Accepted decisions and implementation authorization

Fernando accepted all five proposed decisions on 2026-09-14:

1. the default cadence is `1d`, with the start and stop endpoints included;
2. the first implementation is limited to 367 sample epochs per comet and 50
   selected comet solutions per invocation;
3. the brightest sampled `T-mag` is the public summary while `N-mag` is
   retained separately when available;
4. any Horizons failure fails the whole result rather than silently producing
   a partial ranking;
5. the same inclusive `START`/`STOP` interval owns perihelion selection and
   magnitude sampling.

This acceptance authorizes only the bounded 50A.5D.1B implementation described
here. It does not authorize visibility prediction, chart integration, altered
SPK acquisition, empirical activity correction, or any 50A.5D.3 report work.
