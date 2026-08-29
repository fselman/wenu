# Wenu public-interface audit after architecture v0.9.5

**Status:** Review candidate for the as-is audit and follow-up contract

**Audit baseline:** `1a15076`

**Date:** 2026-08-29

## 1. Purpose and scope

Architecture 0.9.5 established `CoordinateSpec` on spherical geometry and made
`CoordinateService` the sole production astronomical transformation authority.
This audit records what the installed command, canonical examples, and
developer tools expose after that closure. It defines the public-interface
work that must precede new astronomical-object providers without changing
runtime behavior, numerical transformations, or chart appearance.

The audit preserves two distinct public routes:

- `wenu_chart` is the ordinary installed command for reproducible chart
  production;
- the six canonical Python examples are short declarations demonstrating the
  library facade and delegating construction, drawing, and export to Wenu.

An example must not reproduce the installed command or implement projection,
clipping, catalogue joins, astronomical transformations, rendering, furniture,
or repeated saving.

## 2. As-is public chart interfaces

`wenu_chart` provides `all-sky`, `planisphere`, `regional`, `circumpolar`,
`binocular`, and `defaults` commands. The five chart-family commands share
observer, subject, product, content, grid, furniture, style, output,
configuration, and observer-time-sequence controls.

The six canonical Python examples are:

| Example | Declared product |
| --- | --- |
| `examples/all_sky.py` | Galactic Mollweide all-sky chart |
| `examples/planisphere.py` | observer-visible stereographic sky |
| `examples/regional_constellation.py` | one IAU constellation |
| `examples/regional_constellation_group.py` | one constellation group |
| `examples/circumpolar.py` | one declination-bounded polar field |
| `examples/binocular_object.py` | one target-centred binocular field |

All six are shorter than 70 lines, have byte-identical installed resources,
and have resolved-view parity tests against equivalent `wenu_chart` requests.
The installed command and examples are independent adapters over the same
library machinery; neither imports or executes the other.

## 3. Executable inventory and disposition

### 3.1 Supported public examples

Only the six files under `examples/` are supported Python examples. Their role
is to teach concise use of Wenu's public machinery, not to preserve every
useful command invocation as a program.

### 3.2 Reproducible user recipes currently under `tools/`

| Executable | As-is role | Public disposition |
| --- | --- | --- |
| `render_la_ligua_21_agosto.sh` | one ordinary configured `wenu_chart planisphere` request | document as a command/TOML recipe; do not turn into another Python example |
| `render_virgo_setting.sh` | one ordinary configured `wenu_chart regional` request | document as a command/TOML recipe; do not turn into another Python example |
| `render_circumpolar_movie_example.sh` | wrapper around the external movie adapter | retain only as diagnostic invocation until installed media assembly is deliberately supported |
| `render_zodiac_constellations.py` | specialized multi-chart publication batch | retain as a review tool until its batch, title, orientation, and reference-furniture requirements have an approved public contract |

The La Ligua and Virgo recipes already use the correct public command. Their
placement does not indicate missing rendering architecture. A future examples
guide should present such requests directly and identify the required profile
values without depending on Fernando's `$HOME/Documents` paths.

### 3.3 Diagnostics, acceptance, and benchmarks

The following remain developer tools rather than ordinary user workflows:

- `benchmark_reusable_sphere.py`;
- `render_46d8_visual_matrix.py`;
- `render_48e2_polar_preview.py`;
- `render_48e4_polar_pages.py`;
- `render_48g2_polar_pouch.py`;
- `render_49f6_svg_matrix.py`;
- `render_49h2_complete_render_baseline.py`;
- `render_49h3_fixed_sky_reference.py`;
- `render_circumpolar_movie.py`.

The installed `wenu_chart planisphere` command produces the observer-visible
sky. It does not yet reproduce the physical paired polar disks, actual-size A4
pages, or folded horizon pouch. Those physical demonstrations must remain
diagnostic/acceptance tools until a separate public product milestone exposes
their complete request and export contract.

### 3.4 Catalogue and repository maintenance

The `query_*` programs are catalogue-maintenance utilities. They may use
Astropy to interpret and normalize upstream catalogue coordinates because
they do not render charts or create a competing production transformation
path. `translate_notebook.py`, `openai_model.py`, and `cleanup.sh` are
repository utilities rather than Wenu chart interfaces.

## 4. As-is coordinate exposure

The internal vocabulary is richer than the public interface:

- `CoordinateSpec` records frame, origin, position status, epoch, equinox,
  instant, time scale, representation, provider, model, provenance, and
  corrections;
- `CoordinateService` supports governed transformations among ICRS, FK4, FK5,
  Galactic, GCRS, mean and true barycentric ecliptic, and observer-local AltAz
  where the required context is present;
- each `Spherical*` geometry record carries its source coordinate identity.

The public chart interface does not yet expose that vocabulary:

- each family configuration has a `coordinate_frame` string, but validation
  currently permits only its single implemented value;
- there is no installed CLI option for coordinate system, astronomical frame,
  equinox, or catalogue realization epoch;
- ordinary request-time equatorial and ecliptic grids currently select J2000
  in `charts/request_grids.py`;
- the packaged `grids_references.coordinate_grid` table still declares
  `frame = "fk5"` and `equinox = "of_date"`, but those values are not
  translated into the ordinary request-grid path;
- the accepted celestial equator, ecliptic, and four seasonal keypoints use
  one coherent J2000 reference policy.

The public `coordinate_frame` name must not be expanded merely as another
projection option. A chart product frame, a displayed reference grid, and the
native frame and epoch of an astronomical provider are different contracts.

## 5. Required public scientific vocabulary

A future request must distinguish:

| Public concept | Meaning |
| --- | --- |
| coordinate system | semantic longitude/latitude system, such as equatorial, ecliptic, Galactic, or horizontal |
| reference frame | precise realization, such as ICRS, FK5, FK4, Galactic, barycentric true/mean ecliptic, or AltAz |
| equinox | orientation date of axes when the selected frame defines one |
| position epoch | instant at which provider positions are realized or propagated |
| observation instant | observer-local transformation time, not a catalogue epoch |

CLI and TOML values must translate once into validated `CoordinateSpec`
instances or into an immutable public request that resolves them. They must
not construct Astropy frames or a second transformation service in a command,
example, or tool.

Conceptually, the future TOML boundary should separate product and reference
requests:

```toml
[coordinates.product]
system = "equatorial"
frame = "fk5"
equinox = "J2000"
epoch = "native"

[coordinates.grids.equatorial]
frame = "fk5"
equinox = "J2000"
```

The exact schema and switch names remain implementation-milestone decisions.
This audit does not activate these illustrative keys.

## 6. Validation and scientific constraints

The public interface may permit arbitrary supported values, but not arbitrary
combinations. Validation must be semantic and fail before catalogue loading or
rendering. In particular:

- an equatorial system may select an applicable equatorial frame, but a
  Galactic system cannot be relabelled as FK5;
- ICRS has no caller-selected equinox;
- FK4, FK5, and ecliptic frames require coherent equinox handling;
- `of_date` resolves from the declared product or observation time, never the
  computer clock;
- product geometry and all coupled reference furniture must change coherently
  under one requested reference policy;
- AltAz requires an explicit observer, instant, time scale, Earth-orientation
  policy, and refraction policy;
- unsupported combinations must be rejected rather than silently normalized.

An arbitrary equinox is primarily a coordinate-representation transformation
and is implementable through the accepted coordinate service. An arbitrary
position epoch is a provider operation. Properly changing stellar positions
from one epoch to another may require proper motion, parallax, and radial
velocity. Until a provider supports that propagation, Wenu must retain its
declared native epoch and reject an unsupported requested epoch. It must never
relabel native catalogue coordinates with a different epoch.

## 7. Recommended implementation slices

Public coordinate selection should proceed in independently accepted slices:

1. **Reference-policy contract.** Define and validate system, frame, and
   equinox values; translate them to `CoordinateSpec`; expose a coherent
   J2000, `of_date`, or explicit-equinox selection for the equatorial grid,
   celestial equator, ecliptic, and seasonal keypoints.
2. **Product-frame selection.** Generalize only chart families whose
   projection and framing semantics are proven valid for the selected
   celestial product frames. Preserve family-specific constraints.
3. **Provider realization epoch.** Add arbitrary epochs only after the relevant
   catalogue or ephemeris provider implements and proves physical propagation.
4. **Physical-product command.** Independently expose the paired polar disks,
   page furniture, and pouch only through the existing canonical physical
   pipeline.

The first implementation slice must include a compatibility matrix, CLI and
TOML validation, `CoordinateSpec` translation tests, Astropy coincidence
tests, rejection tests, metadata inspection, and human comparison of at least
J2000 and one `of_date` or explicit-equinox chart. It must not reopen internal
architecture 0.9.5 ownership.

## 8. Closure and next safe start

This audit closes the documentation drift after merge `1a15076`: architecture
0.9.5 is accepted and merged, and Wenu has six canonical examples. It does not
claim a package release or `v0.9.5` tag.

The next safe implementation start is the reference-policy contract described
above. Milestone 49D observer-independent celestial realization remains after
this public-interface contract; new moving-object providers remain later work.
