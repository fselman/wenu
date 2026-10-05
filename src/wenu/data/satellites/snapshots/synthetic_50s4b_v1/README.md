# Wenu synthetic 50S.4B satellite snapshot

This installed resource contains three hand-authored, non-operational,
OMM-compatible element records spanning LEO-like, MEO-like, and
geosynchronous-like geometry.

The names, identifiers, epochs, and elements are synthetic. They were not
copied from CelesTrak, Space-Track, SatChecker, or any tracked object. They are
only deterministic inputs for Wenu development and tests.

`records.json` is canonical UTF-8 JSON: sorted keys, compact separators, and
one trailing newline. `manifest.json` records its SHA-256 digest and
provenance. Never edit either file without regenerating and reviewing both
record-level and snapshot-level digests.

The six-digit identifiers 300001–300003 were selected below the upstream
`Satrec` maximum of 339999. Earlier candidate identifiers 900001–900003 were
replaced before the first propagation implementation because the upstream
Vallado-compatible API rejects them; Wenu never substitutes a hidden internal
identity.
