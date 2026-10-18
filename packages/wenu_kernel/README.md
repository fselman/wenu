# Wenu kernel: foundation candidate

This separately installable project implements the first bounded part of K2.
It is not the K5 frozen SDK. Existing Wenu continues to use its current code;
no chart, report, catalogue, snapshot or numerical backend is rerouted yet.

## Implemented scope

- Immutable, recursively typed identity/catalogue/model/reference/time and
  direction-state records, with defensive copies of accepted list inputs.
- Explicit registration of application-admitted references and provider instances.
- Synchronous registry/session lifetime, fixed bindings, owned/borrowed closing,
  busy guards and atomic session admission.
- One-catalogue direction queries, time-major ordered results, exact-query
  session-local caching only after every row validates, and explicit numerical
  accuracy admission. Unknown physical uncertainty remains unknown.
- Standard-library tests with two constructed providers: fixed directions and
  circularly moving directions. These are not Gaia fixtures or science oracles.

`TimePoint` requires canonical integer-valued `jd1` and `jd2` in [-0.5, 0.5).
It rejects noncanonical input instead of silently losing precision while
normalizing. It never adds the large and small date parts for identity or
interval comparison. Scales must already match; no conversion is implemented.
`TimeSpan` is closed. Unbounded model coverage is an explicit value with a scale.
All model and bound resource coverages must admit each requested sample.

Reference registration is an explicit application allowlist, not a transform
engine. Only direction/radian output and native/epoch direction plus batch
capabilities are implemented. Catalogue/model references retain resource and
membership digests. `StateBatch.query` carries that immutable provenance;
rows carry source epochs and actual anchors. A provider is responsible for
returning deterministic results from its admitted immutable sources.

Bounded temporal reuse/certificates, Cartesian states, time conversion,
observation services, real provider adapters, Gaia and persistent envelopes
remain later slices. Requests outside the implemented subset fail explicitly.
The `certify` protocol return is deliberately provisional `object` until the
typed certificate is implemented; no certificate can be consumed by this slice.
The shared provider gate is currently a test-side mixin; the distributable
complete conformance kit remains a K2/K5 deliverable.

## Ownership and failure behavior

Registration transfers ownership only on success. Failed registration leaves
the provider caller-owned. Session opening reads immutable catalogues and
publishes its leases only after all bindings validate; it allocates no provider
session handles. Evaluation publishes no partial batch or partial cache entry.
The core does not promise to roll back a provider's prohibited side effects.

Owned providers close at successful unregister or kernel closure. Borrowed
providers never close through the kernel. Close with active sessions fails.
A provider close failure remains registered and is explicit/retryable; earlier
successful closes in a multi-provider kernel shutdown remain completed.
Session/kernel close is idempotent after successful cleanup. Published values
remain usable after all owners close. K2 is synchronous, without reentrant or
thread-safe provider callbacks.

## Independent gate

From the repository root, without installing the existing Wenu project:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/packages/wenu_kernel/src" python -m unittest discover -s packages/wenu_kernel/tests -v
```

The same gate works against an installed wheel with `PYTHONPATH` unset.
The isolation test also imports the SDK with `-I -S`, disabling site packages.
Root Wenu pytest discovery is restricted to its existing `tests` owner;
this package has its own gate and no runtime dependencies.
The [selection manifest](test_selection_v1.json) records scope and exclusions.
These new tests protect a new enduring owner; no legacy test is moved, removed
or replaced by this foundation. Later provider extractions must record their
old/new test mapping and retain their actual science oracles.
