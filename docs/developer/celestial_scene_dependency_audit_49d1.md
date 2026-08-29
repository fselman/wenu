# Milestone 49D.1 — Celestial-scene dependency and ownership audit

**Status:** Scientifically and pedagogically accepted on the dedicated 49D.1 branch; merge pending

**Audit baseline:** `b4af627`

**Date:** 2026-08-29

## 1. Purpose

This audit defines the smallest scene boundary that will make planets and the
Moon clean additions to Wenu. It classifies existing layers by the scientific
state that may change them and locates the one future dynamic-object insertion
point in the canonical pipeline.

The milestone changes no numerical coordinates, catalogue selection,
projection, clipping, rendering, appearance, public command, or output. It
does not introduce a scene graph, cache, planet, Moon, or ephemeris provider.

## 2. As-is finding

`generate_celestial_sphere()` correctly loads catalogues and source geometry
without binding the resulting `CelestialSphere` to an observer. This is a
**load-time ownership** property: the sphere can be reused by more than one
observer.

It does not yet mean that rendered spherical geometry is
observer-independent. The canonical execution loop in
`sky/celestial_sphere.py::CelestialSphere.draw_chart()`:

1. resolves one observer;
2. calls `layer.spherical_geometry(resolved_observer, ...)` for every enabled
   layer;
3. projects that returned geometry;
4. prepares it where requested;
5. delegates drawing to the renderer.

`draw_chart()` rejects an absent observer. Most catalogue and morphology
layers currently transform their native celestial data to apparent or
observer-local AltAz inside `spherical_geometry()`. Their cached realization
keys include observer/time identity where applicable. Thus an
observer-independent loaded sphere currently produces an observer-dependent
render realization.

This distinction is essential:

| Boundary | Meaning today |
| --- | --- |
| Loaded sphere | Catalogue resources and layer owners are reusable and are not selected by an observer |
| Spherical layer realization | Usually evaluated for a particular observer and instant |
| Projected chart geometry | Depends on the realized spherical coordinates, projection, framing, and clipping |
| Rendered artists | Depend additionally on detail, style, mode, furniture, and backend |

## 3. Dependency vocabulary

A future layer realization must make the following dependencies reviewable
without inferring them from a method name or cache key:

| Dependency | Meaning |
| --- | --- |
| Source identity | Catalogue, morphology file, ephemeris, orbit elements, revision, and provenance |
| Provider epoch | Epoch at which a catalogue state is defined or to which it has been physically propagated |
| Evaluation instant | Instant at which a moving object or apparent place is evaluated |
| Observer | Site and observer state required for topocentric or horizontal coordinates |
| Reference policy | Frame orientation or equinox used by constructed reference geometry |
| Product frame | Explicit spherical frame in which all layers meet before projection |
| Content selection | Magnitude, identity, morphology level, sampling, and enabled-layer choices |
| Appearance | Style, output mode, marker, colour, line, label, and z-order choices; never an astronomical dependency |

An epoch, instant, and equinox are not interchangeable. A provider generates or
propagates an astronomical state. `CoordinateService` transforms that explicit
state. A reference policy constructs coordinate furniture. Projection consumes
geometry already expressed in the product frame.

## 4. Current layer inventory

### 4.1 Catalogue and morphology background

| Layer owner | Native or source state | Current `spherical_geometry()` result | Scientific dependencies |
| --- | --- | --- | --- |
| `objects/stars.py::Stars` | Hipparcos catalogue state expressed through Skyfield | Apparent topocentric AltAz points | Catalogue selection, observer, evaluation instant, Skyfield model |
| `sky/constellation_lines.py` | HIP identifiers and packaged cultural line records | Curves assembled from the same realized stellar vertices | Stellar realization, selected system and figures |
| `sky/constellation_labels.py` | Catalogue/constellation anchors and optional boundaries | Labels in the current realized chart geometry | Stellar/boundary realization, selection and placement policy |
| `objects/nonstellar.py::NonStellar` | ICRS catalogue centres and sampled outlines | AltAz curves | Source revision, sampling, selection, observer and instant |
| Galaxy and extended-object subclasses | Catalogue centres, sizes, position angles, or fixed-symbol metadata | AltAz polygons, curves, or points | Source revision, selection, sampling where applicable, observer and instant |
| `sky/milky_way.py::MilkyWayIsophotes` | Packaged ICRS GeoJSON rings | AltAz polygons | Source revision, selected levels, observer and instant |
| `sky/magellanic_clouds.py::MagellanicCloudIsophotes` | Packaged Gaia-derived ICRS morphology rings | AltAz polygons | Source revision, cloud/levels, observer and instant |
| `sky/constellation_boundaries.py` | Packaged IAU boundary geometry with its historical frame provenance | Geometry transformed for the observer-bound chart path | Boundary source, selection, observer and instant |

Several catalogue owners already expose native ICRS `position(instant=None)`
records through the accepted structural `PositionProvider` boundary. Their
legacy `spherical_geometry(observer)` path nevertheless remains the ordinary
rendering path. The structural provider contract must not be confused with a
completed observer-independent product realization.

### 4.2 Constructed references and local geometry

| Layer owner | Construction | Dependency class |
| --- | --- | --- |
| FK5 equatorial grid/equator | Constructed for the selected reference equinox, then transformed as required | Reference policy; observer only when the product frame requires it |
| True-ecliptic grid/ecliptic/keypoints | Constructed for the same selected equinox | Reference policy; observer only when the product frame requires it |
| Galactic grid/plane | Fixed Galactic construction | Product-frame transformation |
| `sky/horizon.py::HorizonReference` | Native altitude-zero AltAz curve | Observer-local by definition |
| AltAz grid and cardinal context | Native horizontal construction | Observer, evaluation instant, Earth-orientation policy |
| `sky/points.py::CelestialPoints` | Explicit input frames normalized through `CoordinateService` | Source frame plus observer/instant for its current AltAz result |

The public `CelestialReferencePolicy` owns reference orientation only. It must
not acquire catalogue propagation, ephemeris evaluation, observer ownership,
or product-frame selection.

## 5. Three scientific realization classes

The minimum useful separation for planets is semantic rather than graphical.

### 5.1 Celestial background

Catalogue stars, constellations, deep-sky catalogues, Milky Way morphology, and
Magellanic Cloud morphology belong to the celestial background. Their native
catalogue or morphology state is not generated by a planetary ephemeris.

A particular product may request either:

- a catalogue/astrometric celestial realization in an explicit celestial
  product frame; or
- an observer-bound apparent realization for an observing chart.

The product decides which scientifically valid realization is required. A
layer, projection, or renderer must not guess.

### 5.2 Dynamic astronomical objects

The Sun, Moon, planets, natural satellites, minor bodies, and artificial
satellites belong to dynamic astronomical layers. A provider evaluates their
state at an explicit instant and returns a state with frame, origin, time
scale, position status, model, and provenance.

The provider does not select the chart or project the result. Its returned
geometry passes through `CoordinateService` into the same product frame used
by the other enabled layers.

### 5.3 Observer-local geometry

The horizon, AltAz grid, cardinal directions, landscape, and visibility mask
are constructed from an explicit observer and instant. They do not become
celestial catalogue objects merely because Wenu transforms them into a
celestial product frame for projection.

## 6. One future convergence point

Every enabled layer must meet in one explicit spherical product frame before
projection:

```text
catalogue or morphology state ───────┐
ephemeris/orbit provider state ──────┼─> CoordinateService
observer-local reference geometry ───┘         |
constructed celestial references ──────────────┤
                                               v
                                    spherical product frame
                                               |
                                               v
                                canonical projection/preparation
                                               |
                                               v
                                      renderer and export
```

The insertion point for a planet is therefore **before projection and after
provider evaluation**. It is another registered semantic sky layer in
`CelestialSphere.draw_chart()`; it is not a special renderer call, furniture
item, catalogue row, or command-owned overlay.

## 7. Minimum contract for 49D.2

The next implementation slice may add only the information required to resolve
a registered layer honestly. The exact public type name remains a design
decision, but the immutable input must be able to provide:

- requested product `CoordinateSpec`;
- explicit `ObservationContext` when required;
- provider evaluation instant when required;
- reference policy for constructed furniture;
- content-selection values already owned by the request;
- no style, renderer, projection, viewport, or output backend.

The result remains an existing typed `SphericalGeometry` value. It carries
the coordinate specification of the product-frame geometry and retains
semantic identifiers, metadata, topology, and provenance.

A controlled test provider should prove the dynamic-layer insertion point
before a real ephemeris is added. It should return a deterministic native
point, record its evaluation instant, be transformed once through
`CoordinateService`, and enter the ordinary draw order. This test provider
belongs in tests, not in the installed package.

## 8. Compatibility rule

49D.2 must preserve the current call:

```python
layer.spherical_geometry(observer, **geometry_options)
```

until every affected production layer has a deliberate migration. The first
implementation must not change existing numerical geometry or rendered
products. Any richer realization context must be added through the current
request and layer pipeline, with compatibility behavior characterized by tests.

The existing observer-bound stellar path remains authoritative for present
charts until a separate migration proves a direct celestial and an apparent
local realization against their appropriate scientific references.

## 9. Reuse and cadence implications

This audit classifies dependencies; it does not authorize caching.

Once the realization boundary exists, a sequence may prove separately that:

- static catalogue/morphology geometry is reusable when its source, provider
  epoch, selected product frame, and content selection are unchanged;
- a planet or Moon state must be reevaluated at each requested provider
  instant;
- horizon and AltAz geometry must be reevaluated for each observer instant;
- reference geometry changes only when its reference policy or required
  product-frame transformation changes;
- appearance-only changes do not invalidate astronomical geometry.

Cache keys must be derived from immutable scientific identity. The complete
independent-render path remains the correctness oracle.

## 10. Explicit non-goals

This milestone does not:

- implement the Sun, Moon, a planet, or any ephemeris lookup;
- select a JPL kernel;
- introduce public product-system or product-frame switches;
- propagate Hipparcos or Gaia stars to an arbitrary epoch;
- replace Skyfield stellar apparent-place calculations;
- migrate all catalogue or morphology layers;
- add a generic scene graph or renderer-specific object hierarchy;
- add caching or performance thresholds;
- change draw order, clipping, masking, labels, styles, or output;
- make an observer optional for the current `draw_chart()` path.

## 11. Acceptance requirements

49D.1 is accepted when:

1. the inventory is checked against the implementation at baseline
   `b4af627`;
2. Fernando accepts the three realization classes and the single convergence
   point;
3. the coordinate guide explains the distinction at foundation and
   undergraduate depth;
4. the roadmap, implementation reference, and source tree identify 49D.1 as
   documentation-only;
5. documentation tests protect the dependency vocabulary, insertion point,
   compatibility rule, and non-goals;
6. the focused documentation suite and the complete test suite pass on
   Fernando's Mac.

After acceptance, 49D.2 may design and implement the smallest typed realization
context and controlled dynamic-layer test. A real planet remains a later
49E/49I vertical slice.

## 12. Acceptance evidence

Fernando accepted the three realization classes, the single spherical
product-frame convergence point, the planet insertion point, and the explicit
49D.1 non-goals on 2026-08-29.

Mac verification on the accepted branch passed:

- 39 documentation tests in 2.78 seconds;
- 1,789 routine tests with 30 deselected in 26.62 seconds;
- all 1,819 tests in 84.41 seconds.

No visual comparison was required because 49D.1 changes no production source,
numerical geometry, rendering, appearance, or output. The next authorized work
after merge is a separately bounded 49D.2 design and implementation milestone;
this acceptance does not itself authorize that runtime change.
