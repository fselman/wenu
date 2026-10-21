"""Ceres descriptor and manifest-backed solution identity."""

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


def _load_solution():
    """Read the preserved source facts; keep the legacy public constant."""
    import json
    from importlib.resources import files

    document = json.loads(
        files("wenu.data").joinpath("ceres_solution_v1.json").read_text(encoding="utf-8")
    )
    if (
        not isinstance(document, dict)
        or set(document) != {"schema_version", "solution"}
        or type(document["schema_version"]) is not int
        or document["schema_version"] != 1
    ):
        raise ValueError("unsupported Ceres solution manifest schema")
    solution = MinorBodySolutionIdentity(**document["solution"])
    if (
        solution.wenu_target, solution.object_class,
        solution.provider_spk_id, solution.iau_number,
    ) != (
        CERES_BODY.target, CERES_BODY.body_class,
        CERES_BODY.physical_body_id, CERES_BODY.iau_number,
    ):
        raise ValueError("Ceres solution manifest differs from body identity")
    return solution


CERES_SOLUTION = _load_solution()
