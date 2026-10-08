# Named Chilean locations

Wenu's offline version-1 location catalogue contains one approximate reference
point for each of Chile's 345 municipal administrations, plus 14 observatory
and telescope-site reference points. A municipal reference represents its
cabecera or an urban district, not a surveyed municipal building, the centre
of the commune polygon, or the user's actual observing position.

## Choosing a location

The existing `--observer-location` option accepts a unique short name:

```bash
wenu_chart planisphere --observer-location "La Ligua" \
  --observer-time "2026-10-15T21:00:00" --format png \
  --output la_ligua_location_v1.png
```

Qualification is optional. These names identify the same registered point:

```text
La Ligua
La Ligua:La Ligua
Petorca:La Ligua:La Ligua
Valparaíso:Petorca:La Ligua:La Ligua
Chile:Valparaíso:Petorca:La Ligua:La Ligua
```

The order is `Country:Region:Province:Comune:City`. Every current record has
`country = "Chile"` and `country_code = "CL"`; future country catalogues can
use the same hierarchy and ambiguity policy. Country is optional when a
shorter suffix is unique. A wrong country never resolves a Chilean record.
Shorter qualified names are
contiguous suffixes of this hierarchy. The last component can be the
observatory name, for example:

```text
Chile:Antofagasta:Antofagasta:Taltal:Paranal
```

Lookup ignores capitalization, accents and repeated whitespace, while output
preserves the catalogue's spelling. The table's stable `id` also resolves a
location. Official commune names can be aliases for their municipal reference:
`Camarones` resolves Cuya and `Cabo de Hornos` resolves Puerto Williams.
Ambiguous names produce an error listing the qualified alternatives. Wenu
never chooses the first match, the closest location or the largest population.
Wrong qualifiers and empty hierarchy components produce errors.

The CSV table is `src/wenu/data/chile_locations_v1.csv` in a source checkout.
Its `qualified_name` column is directly usable with `--observer-location`.
The packaged JSON and manifest carry the same version. Catalogue revisions
retain stable IDs and receive new versioned filenames.

## Coordinates, heights and timezones

Latitude and longitude are WGS84 decimal degrees: south and west are negative.
Coordinates are approximate settlement or site references. Printed decimal
places do not establish survey accuracy. For an actual observing site, supply
explicit latitude, longitude and ellipsoidal height through the existing
observer options.

The table separates the physical elevation `height_m` from Wenu's runtime
`elevation_m`. NASADEM HGT V001 estimates a radar-derived surface with roughly
one-arcsecond horizontal sampling, mainly observed in February 2000. It may
include buildings or vegetation. Neither its pixel spacing nor an integer
height implies metre-level accuracy or contemporary ground surveying.

`height_m` is a nearest-post NASADEM estimate relative to the EGM96 geoid.
`geoid_undulation_m` is bilinearly interpolated from NGA's public-domain EGM96
15-minute grid distributed by PROJ. New sites use:

```text
WGS84 ellipsoidal height h = EGM96 elevation H + geoid undulation N
```

Conversion takes place when compiling the snapshot, never during chart
rendering. Per-site source tile and row/column, geoid grid digest and sampled
byte-range checksums are retained in the provenance receipt. The conversion
was cross-checked against PROJ's independent vertical-grid transformation.
Unknown heights remain unknown and require an explicit `--observer-height`;
they are never silently replaced by zero for named locations.

Existing La Ligua and Papudo latitude, longitude and runtime heights (52 m
and 15 m) are preserved exactly for compatibility. Their historical height
reference was unspecified; they are marked `legacy_wenu_unspecified` and the
new DEM estimate is stored separately. No conversion is claimed for those
legacy runtime heights. Explicit named-location height and timezone overrides
retain their existing meaning.

Where available, `reported_heights_m` retains published observatory height
claims separately, with their source and reference. An unspecified sea-level
datum is not assumed to be EGM96 or WGS84. These comparison values do not
replace the referenced DEM conversion used for the runtime observer height.

Defaults use `America/Santiago`, `America/Coyhaique` for Aysén,
`America/Punta_Arenas` for Magallanes, and `Pacific/Easter` for Rapa Nui.
`tzdata>=2025.2` supplies the Coyhaique zone when it is missing from the system
zone database. Timezone rules come from the installed IANA database, not a
fixed UTC offset. Explicit `--observer-timezone` overrides still win.

## Coverage and provenance

Municipal seats were cross-referenced against MOP administrative CUT names and
codes and BCN's urban-cabecera inventory. BCN returned 343 distinct codes;
Los Andes and Chonchi were added from GeoNames. Camarones uses Cuya according
to SUBDERE rather than the Caleta Camarones entry in that inventory. Corrected
spelling and name crosswalks are recorded per entry. GeoNames administrative
codes are not used as authoritative Chilean CUT codes.

There are 346 communes but 345 municipal administrations: Antártica shares
administration with Cabo de Hornos. The municipal record represents Puerto
Williams; it does not supply a fictional Antarctic observing point.

The observatory subset includes ALMA, APEX, Paranal, La Silla, Las Campanas,
Tololo, Gemini Sur, SOAR, Rubin, ELT, GMT, Cerro Calán, Cerro Morado and Lynch.
These are site references; ALMA denotes the high array site, not its lower
operations facility. Registration does not assert operational status or
surveyed telescope phase-centre coordinates. Additional small and outreach
observatories remain an extension of this catalogue, not asserted complete
coverage of every observatory in Chile.

GeoNames coordinate data require CC BY 4.0 attribution. Wikidata structured
coordinates are CC0. NASA-produced elevation data permit reuse, and the NGA
geoid grid is public domain. Acknowledge NASA/JPL, OpenTopography, NGA/PROJ,
GeoNames and Wikidata as specified in the manifest. Administrative inventories
are cross-check evidence; their geometry is not redistributed. The separate
34-entry MinCiencia catalogue was inspected but not bulk-vendored: its
redistribution terms and site-specific conventions need further verification.

The immutable snapshot is loaded by `observer.py`, the existing observer
context owner. It makes no network calls, adds no geospatial runtime library,
and uses the existing CLI, TOML, chart and coordinate-service routes.
