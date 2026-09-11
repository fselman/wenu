"""Catalog-owned identity for the first drawable asteroid."""

from wenu.minor_body_ephemeris import MinorBodySolutionIdentity
from wenu.sky.solar_system_bodies import (
    APPARENT_TRACK,
    SYMBOLIC_POINT,
    SolarSystemBodyDescriptor,
)


CERES_BODY = SolarSystemBodyDescriptor(
    target="ceres",
    entity_key="ceres",
    display_name="Ceres",
    selection_key="ceres",
    body_class="asteroid",
    physical_body_id="20000001",
    canonical_designation="(1) Ceres",
    iau_number=1,
    classifications=frozenset({"asteroid", "dwarf_planet"}),
    capabilities=frozenset({SYMBOLIC_POINT, APPARENT_TRACK}),
    localized_display_names=(("en", "Ceres"), ("es", "Ceres")),
    ephemeris_source_key="minor_body_spk",
)

CERES_SOLUTION = MinorBodySolutionIdentity(
    provider="NASA/JPL Horizons API",
    service_version="1.2",
    wenu_target="ceres",
    object_class="asteroid",
    primary_designation="1 Ceres",
    horizons_command="1;",
    provider_spk_id="20000001",
    orbit_solution_id="JPL#48",
    solution_date="2021-Apr-13_11:04:44",
    osculating_epoch="2458849.5 TDB",
    reference_system="ICRF/J2000",
    iau_number=1,
    name="Ceres",
    quality_fields=(
        ("observations", "1075 (1995-2021)"),
        ("residual_rms_arcsec", "0.24563"),
        ("condition_code", "0"),
        ("radar", "60 delay, 0 Doppler"),
    ),
    provenance=("accepted 50A.2 Ceres solution identity",),
)
