# Comet numerical validation (Milestone 50A.4)

**Status:** Candidate implementation; raw evidence acquisition pending

**Base:** `1049134`

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

The tool refuses to overwrite any existing evidence directory. No automated
test invokes the network. Once the raw response format and solution identity
are inspected, the next commit will derive the compact frozen oracle and add
the offline validator without duplicating coordinate mathematics.

Run the acquisition from the repository root:

```bash
python tools/acquire_50a4_comet_evidence.py \
  --output-directory ~/.cache/wenu/minor_bodies/50a4-raw
```

The acquisition report is safe to inspect as text. The SPK and four raw JSON
responses remain local until their identities and redistribution boundary are
reviewed; only the compact numerical fixture is expected to enter the
repository.
