# Comet numerical validation (Milestone 50A.4)

**Status:** Scientifically, operationally, and regression accepted on 2026-09-12

**Base:** `5aec1fe`

The accepted audit selects 2P/Encke and requires an evidence-first numerical
validation. `tools/acquire_50a4_comet_evidence.py` is the only networked step.
It resolves exact numbered comet `2P` through SBDB, requires at least one
declared `A1`, `A2`, `A3`, or `DT` model parameter, derives three epochs around
the returned perihelion epoch, selects the explicit Horizons apparition record
`90000091`, and freezes:

- the complete SBDB response, including covariance and alternate orbits;
- one bounded Horizons type-21 SPK;
- geometric barycentric ICRF state-vector output;
- geocentric and La Ligua observer tables;
- exact request URLs, response signatures, byte counts, and SHA-256 digests.

Horizons distinguishes the apparition record `90000091` from the permanent
NAIF SPK target `1000025`. The acquisition requires the generated kernel to
contain exactly one segment for `1000025`; it does not silently select a newer
apparition record.

The SBDB solution retains its 2023 perihelion passage. The validation epochs
advance that passage by the returned sidereal period to the first recurrence
in 2027, then sample 90 days before, the derived perihelion day, and 90 days
after. Direct-table requests transmit numeric Julian dates with an explicit
time scale and are rejected unless Horizons returns one unique
`$$SOE`/`$$EOE` data block.

The tool refuses to overwrite any existing evidence directory. No automated
test invokes the network.

`tools/build_50a4_comet_fixture.py` parses the inspected raw directory without
network access. It rejects wrong SBDB, Horizons, solution, SPK, digest, model,
or epoch identities and writes the compact direct-Horizons oracle at
`tests/fixtures/horizons_comet_validation_50a4.json`. The parser explicitly
handles Horizons' whitespace between a minus sign and some negative apparent
declinations.

`tools/validate_50a4_comet.py` delegates state and direction comparison to the
existing 50A.2 validator machinery. The shared validator now evaluates each
geometric vector at its explicit JD TDB while the observer tables remain at
their stated UTC instants. This distinction is material here because midnight
UTC is approximately `00:01:09` TDB. The result retains the typed comet
solution, complete `A1` and `A2` records, quality fields, SPK segment, resource
chain, and per-product time provenance.

Fernando accepted the characterized tolerance matrix on 2026-09-12. The
ordinary entry point now enforces it and returns `"accepted": true` only when
every comparison passes. `--characterize` remains available, returns
`"accepted": false`, and reports `"tolerances": null` so that a diagnostic run
cannot be mistaken for acceptance.

The initial run against the inspected `50a4-raw-v2` SPK and DE440 records
these maxima without accepting them as thresholds:

| Quantity | Maximum absolute residual |
|---|---:|
| position | `5.218470100487593e-11 au` |
| velocity | `2.307827540182217e-12 au/day` |
| astrometric RA | `3.517478546655184e-6 deg` |
| astrometric Dec | `4.541090646625889e-6 deg` |
| apparent RA | `2.8297264407228795e-6 deg` |
| apparent Dec | `4.503201424199688e-6 deg` |
| distance | `2.968685297588536e-10 au` |
| light time | `7.085011688445775e-9 min` |
| parallax | `7.287428584896007e-6 deg` |

The direct observer tables contain angular coordinates to five decimal
degrees, so their printed precision is material to the directional and
parallax characterization. The realized topocentric parallax spans
`0.001112315` through `0.003469527 deg` across the three epochs.

The accepted enforcement matrix is:

| Quantity | Tolerance |
|---|---:|
| position | `1e-10 au` |
| velocity | `5e-12 au/day` |
| astrometric/apparent RA or Dec | `5e-6 deg` |
| distance | `1e-9 au` |
| light time | `1e-7 min` |
| parallax | `1e-5 deg` |

The direction, distance, and light-time bounds preserve the accepted 50A.2
values. Position and velocity receive comet-specific envelopes around the
type-21 characterization. Parallax uses a `1e-5 deg` envelope because it is
derived from two directions independently rounded by Horizons to five decimal
degrees. These are reproduction tolerances for the frozen provider products,
not an estimate of the physical orbit uncertainty.

Run the acquisition from the repository root:

```bash
python tools/acquire_50a4_comet_evidence.py \
  --output-directory ~/.cache/wenu/minor_bodies/50a4-raw-v2
```

Build the compact oracle from that exact inspected directory:

```bash
python tools/build_50a4_comet_fixture.py \
  --raw-directory ~/.cache/wenu/minor_bodies/50a4-raw-v2 \
  --output /tmp/horizons_comet_validation_50a4.json
```

Run the initial numerical comparison without acceptance thresholds:

```bash
python tools/validate_50a4_comet.py --characterize \
  --resource-directory ~/.cache/wenu/minor_bodies/50a4-raw-v2 \
  --planetary-ephemeris-path ~/.cache/wenu/de440s.bsp \
  --output /tmp/wenu-50a4-characterization.json
```

Run the enforcing comparison by omitting `--characterize`:

```bash
python tools/validate_50a4_comet.py \
  --resource-directory ~/.cache/wenu/minor_bodies/50a4-raw-v2 \
  --planetary-ephemeris-path ~/.cache/wenu/de440s.bsp \
  --output /tmp/wenu-50a4-validation.json
```

The acquisition report is safe to inspect as text. The SPK and raw JSON
responses remain local; only the compact numerical fixture enters the
repository. No descriptor, chart request, CLI selector, drawing, or exporter
behavior is added by this implementation.

Final Mac verification reproduced the compact fixture byte for byte, returned
`"accepted": true` from the enforcing validator, passed all 151 focused tests
in 4.99 seconds, and passed the complete 2,262-test suite in 84.96 seconds.
