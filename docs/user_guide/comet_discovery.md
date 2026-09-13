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

For observer-comet distance \\(\\Delta\\) and heliocentric distance \\(r\\), both
in au, the standard total-magnitude model is

\\[
m_1 = M_1 + 5\\log_{10}(\\Delta) + K_1\\log_{10}(r).
\\]

`M1` is therefore the reference total magnitude (nucleus plus coma) at
\\(r=1\\) au and \\(\\Delta=1\\) au. `K1` is not a magnitude: it controls how
strongly total brightness changes with heliocentric distance. If flux is
written as \\(F\\propto r^{-n}\\), then \\(n=K_1/2.5\\).

The corresponding nuclear-magnitude model is

\\[
m_2 = M_2 + 5\\log_{10}(\\Delta) + K_2\\log_{10}(r) + \\Phi(\\alpha),
\\]

where `M2` is the nuclear reference magnitude, `K2` is its heliocentric
slope parameter, and \\(\\Phi(\\alpha)\\) is a possible phase-angle correction.
These are Solar System reference magnitudes at unit distances, not stellar
absolute magnitudes defined at 10 parsecs.

A numerical estimate also requires observer-dependent \\(r\\), \\(\\Delta\\),
phase geometry, and an evaluation instant. Comets can depart substantially
from the model through outbursts, fading, fragmentation, asymmetric activity,
and observational-aperture effects. Observer-dependent model magnitude remains
deferred to the separately reviewed 50A.5D.1B.
