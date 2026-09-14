# Discovering comets by perihelion

`wenu_retrieve_comets` queries NASA/JPL SBDB explicitly and lists current
comet solutions selected by perihelion date and distance:

```bash
wenu_retrieve_comets 2026-01-01 2026-12-31
```

The two dates are complete inclusive UTC civil days. Wenu converts their
boundaries to the provider's TDB perihelion scale. The default maximum
perihelion distance is 5 au; change it explicitly when required:

```bash
wenu_retrieve_comets 2026-01-01 2026-12-31 \
  --max-perihelion-distance 3
```

Write complete machine-readable output with units and provenance:

```bash
wenu_retrieve_comets 2026-01-01 2026-12-31 \
  --format json \
  --output output/comets-2026.json
```

This command performs network access. It is separate from `wenu_chart` and
does not install a comet or render a chart.

The `1st obs.` column is SBDB `first_obs`: the earliest observation used by
the current orbit solution. It is not necessarily the historical discovery
date.

The table ends with a `Header key` defining its orbital symbols, provider
codes, photometric parameters, time scale, and units. In particular, `q` is
perihelion distance, `e` eccentricity, `i` inclination, and Earth `MOID`
the minimum orbit intersection distance from Earth. The key also decodes the
designation prefixes `P` (periodic), `C` (non-periodic), `D`
(disappeared), `X` (orbit not meaningfully computable), `A` (found to be a
minor planet), and `I` (interstellar), as well as permanent periodic-comet
numbers such as `2P`.

The result means only that SBDB reports a perihelion instant inside the chosen
interval and a perihelion distance inside the chosen bound. It is **not a
visibility forecast**: it does not evaluate altitude, solar elongation, sky
brightness, weather, coma activity, or detectability.

`M1`, `M2`, `K1`, and `K2`, when present, are labelled as provider model
parameters. They are not synthesized or presented as an expected apparent
magnitude.

## Photometric model parameters

For observer-comet distance \(\Delta\) and heliocentric distance \(r\), both
in au, the standard total-magnitude model is

\[
m_1 = M_1 + 5\log_{10}(\Delta) + K_1\log_{10}(r).
\]

`M1` is therefore the reference total magnitude (nucleus plus coma) at
\(r=1\) au and \(\Delta=1\) au. `K1` is not a magnitude: it controls how
strongly total brightness changes with heliocentric distance. If flux is
written as \(F\propto r^{-n}\), then \(n=K_1/2.5\).

The corresponding nuclear-magnitude model is

\[
m_2 = M_2 + 5\log_{10}(\Delta) + K_2\log_{10}(r) + \Phi(\alpha),
\]

where `M2` is the nuclear reference magnitude, `K2` is its heliocentric
slope parameter, and \(\Phi(\alpha)\) is a possible phase-angle correction.
These are Solar System reference magnitudes at unit distances, not stellar
absolute magnitudes defined at 10 parsecs.

A numerical estimate also requires observer-dependent \(r\), \(\Delta\),
phase geometry, and an evaluation instant. Comets can depart substantially
from the model through outbursts, fading, fragmentation, asymmetric activity,
and observational-aperture effects. Observer-dependent model magnitude is available only when
`--observer-location` is supplied:

```bash
wenu_retrieve_comets 2026-09-01 2026-09-30 \
  --observer-location "La Ligua"
```

The magnitude step, when explicit, must be a positive whole number of hours or
days. When it is omitted Wenu selects a reproducible cadence, normally `1d`,
that stays within the sample budget. For each selected comet Wenu samples both
endpoints of a separate interval extending 30 days before and after that
comet's perihelion, and makes one Horizons request per selected comet,
and reports the numerically smallest valid sampled `T-mag` as the brightest
sampled total model magnitude. `N-mag` is reported independently and is
never substituted for a missing `T-mag`.

These sampled provider values are not continuous minima, visibility forecasts,
or detectability estimates. Unknown provider values remain unknown. Horizons
advises treating small-body model magnitudes as uncertain at roughly 1
magnitude in practice, potentially worse at large phase angle. The command
retains the observer coordinates, sampling epochs, provider version, exact
target and orbit solution, request parameters, retrieval time, raw-response
digest, and provider notices in JSON output.

The observer mode defaults to at most 50 selected comet solutions and remains
bounded to 367 epochs per comet. Use `--max-photometry-comets COUNT` to
authorize a larger complete workload; Wenu never truncates the
result silently. If an explicit cadence is too fine, the error reports the
minimum usable cadence. Discrete epochs travel through the official Horizons
file API POST route rather than a length-limited GET URL. JPL requires one API
request at a time, so Wenu keeps provider access sequential. Validated responses are cached under
`~/.cache/wenu/comet_photometry`, so repeated and interrupted workloads reuse
completed requests. `--refresh-photometry` replaces matching cache entries.

An interactive terminal shows progress on stderr without contaminating table
or JSON output. Use `--progress` to force progress in a log or `--no-progress`
to suppress it. Any Horizons failure fails the complete result. Expected
failures are concise; `--debug` restores their traceback. `--magnitude-step`
and a non-default
`--max-photometry-comets`, progress controls, and `--refresh-photometry`
require `--observer-location`.
