# Loaded-sphere reuse seam (Milestone 49J.5A)

**Status:** Implemented on the task branch; awaiting Mac verification and Fernando's review.

## Scope

49J.5A installs the smallest scientifically safe reuse seam for the fixed-sky
circumpolar sequence. `FixedSkySequenceExecution` makes the choice explicit:
`cold` remains the independent complete-render oracle, while
`reuse_loaded_sphere` loads one observer-independent canonical celestial sphere
and supplies a fresh scientific observer to every canonical frame request.

The reused object contains canonical catalogue resources and the immutable
`CelestialSphereLoadProfile`. It contains no bound observer and is not a cache
of observed coordinates, horizon state, projection, prepared geometry,
renderer state, or exported products. Every reused-mode frame independently
resolves its simulation time, creates and closes an `Observer`, evaluates
observer-local and moving-object state, transforms, projects, prepares,
renders, and exports through `generate_chart_request()`.

## Ownership and evidence

`generate_fixed_sky_rotating_horizon_sequence()` remains the only sequence
orchestrator and `generate_chart_request()` remains the complete static route.
The latter now accepts an explicit observer only when paired with an
observer-independent supplied sphere. It rejects an unbound sphere without an
observer, an observer supplied without a sphere, and an explicit observer
paired with an already bound sphere.

`FixedSkyRotatingHorizonGeneration` records the execution mode, canonical
sphere build count, and the exact immutable reused load profile. Cold execution
reports one build per frame and cannot claim a reused profile; loaded-sphere
execution reports exactly one build and requires the profile. Tests extend the
existing request-generation and fixed-sky sequence owners; no milestone-named
test file, global cache, session fixture, timing threshold, or parallel
astronomical/rendering pipeline is introduced.

## Non-goals and next acceptance

This slice establishes ownership, lifecycle, rejection boundaries, and
observable identity only. It does not yet claim performance improvement or
candidate-versus-oracle scientific, semantic, normalized-SVG, PNG, PDF,
clipping, furniture, or visual equivalence. Those comparisons and the Mac
measurement belong to 49J.5B before 49J.5 can be accepted as a whole.

The coordinate-system guide was reviewed and remains current. The seam changes
no coordinate meaning, reference epoch, equinox, product frame, projection,
provenance, or output semantics.

**Runtime effect:** Opt-in fixed-sky sequences may reuse one observer-independent
loaded canonical sphere; the default cold route is unchanged.

**Test behavior effect:** Existing test modules gain seam, lifecycle, and
rejection-boundary contracts; no marker, fixture scope, or gate changes.
