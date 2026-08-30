"""Current public-documentation and architecture-authority contracts."""

from pathlib import Path
import ast
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs" / "developer"
ARCHIVE = DEVELOPER / "archive"
CURRENT = ARCHIVE / "architecture_history" / "current_architecture_v0.7.md"
IMPLEMENTED = ARCHIVE / "architecture_history" / "target_architecture_v0.7.md"
V08_CURRENT = ARCHIVE / "architecture_history/current_architecture_v0.8.md"
TARGET = ARCHIVE / "architecture_history/target_architecture_v0.8.md"
ROADMAP = ARCHIVE / "migration_history/wenu_migration_0.7_to_0.8.md"
V09_CURRENT = DEVELOPER / "current_architecture_v0.9.md"
V09_TARGET = ARCHIVE / "architecture_history/target_architecture_v0.9.md"
V09_ROADMAP = ARCHIVE / "migration_history/wenu_migration_0.8_to_0.9.md"
FUTURE_ROADMAP = DEVELOPER / "post_v0.9_architecture_roadmap.md"
V095_TARGET = DEVELOPER / "target_architecture_v0.9.5.md"
COORDINATE_GUIDE = DEVELOPER / "coordinate_system_guide_v0.9.5.md"
PUBLIC_INTERFACE_AUDIT = DEVELOPER / "public_interface_audit_v0.9.5.md"
SCENE_DEPENDENCY_AUDIT = (
    DEVELOPER / "celestial_scene_dependency_audit_49d1.md"
)
LAYER_REALIZATION_CONTRACT = (
    DEVELOPER / "layer_realization_context_49d2.md"
)
EPHEMERIS_PROVIDER_CONTRACT = (
    DEVELOPER / "ephemeris_provider_contract_49e1.md"
)
EPHEMERIS_RUNTIME_CONTRACT = (
    DEVELOPER / "ephemeris_runtime_contracts_49e2.md"
)
SKYFIELD_EPHEMERIS_CONTRACT = (
    DEVELOPER / "skyfield_ephemeris_adapter_49e3.md"
)
SOLAR_SYSTEM_DIRECTION_CONTRACT = (
    DEVELOPER / "solar_system_direction_realizer_49e4.md"
)
ASTROMETRIC_DIRECTION_CONTRACT = (
    DEVELOPER / "astrometric_direction_runtime_49e5.md"
)
APPARENT_DIRECTION_CONTRACT = (
    DEVELOPER / "apparent_direction_runtime_49e6.md"
)
VENUS_VERTICAL_SLICE_AUDIT = (
    DEVELOPER / "venus_vertical_slice_audit_49i1.md"
)
ORDINARY_REALIZATION_CONTEXT = (
    DEVELOPER / "ordinary_realization_context_49i1a.md"
)
VENUS_LAYER_CONTRACT = DEVELOPER / "venus_layer_49i1b.md"
MOON_SHARED_PIPELINE_AUDIT = (
    DEVELOPER / "moon_shared_body_pipeline_audit_49i2.md"
)
MOON_DIRECTION_VALIDATION = (
    DEVELOPER / "moon_direction_validation_49i2a.md"
)
SHARED_SOLAR_SYSTEM_POINT_LAYER = (
    DEVELOPER / "shared_solar_system_point_layer_49i2b.md"
)
INSTRUCTIONS = DEVELOPER / "assistant_instructions.md"
CONFIGURATION_AUDIT = ARCHIVE / "audits/configuration_default_audit.md"
CONFIGURATION_SCHEMA = DEVELOPER / "configuration_schema_v1.md"
DIAGRAMS = DEVELOPER / "diagrams"
PUBLIC_DOCUMENTS = (
    ROOT / "README.md",
    ROOT / "README.es.md",
    DEVELOPER / "implementation_reference.md",
    DEVELOPER / "source_tree.md",
    *sorted((ROOT / "docs" / "user_guide").glob("*.md")),
)
OBSOLETE_IMPORTS = (
    "wenu.spherical",
    "wenu.projected",
    "wenu.spherical_frame",
    "wenu.clipping",
    "wenu.viewport",
    "wenu.projection",
    "wenu.chart",
    "wenu.regional",
    "wenu.styles",
    "wenu.renderers",
)


def read(path):
    return path.read_text(encoding="utf-8")


def test_49e4_audits_the_observer_relative_direction_boundary():
    contract = " ".join(read(SOLAR_SYSTEM_DIRECTION_CONTRACT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**As-is baseline:** `644bac7`",
        "astrometric Venus direction",
        "observer state at reception",
        "target state at retarded emission time",
        "one-way light time",
        "Distance and timing data",
        "The observer is not synonymous with Earth",
        "Astrometric and apparent are separate statuses",
        "`frame=\"icrs\"`",
        "`epoch` remains absent",
        "`equinox` remains absent",
        "49E.5 — Astrometric direction runtime",
        "49E.6 — Apparent direction runtime",
        "49I.1 — Venus vertical slice",
        "No future Sun, Moon, or planet",
    ):
        assert phrase in contract

    assert "Milestone 49E.4 — Solar-System direction-realizer audit" in roadmap
    assert "49E.4 changes no runtime type or output" in roadmap
    assert "The accepted 49E.4 audit" in architecture
    assert "13.2.8 49E.4 observer-relative direction audit" in guide
    assert "Skyfield's `observe()` corresponds to the astrometric" in guide
    assert "reception instant is neither a position reference epoch" in guide
    assert "Guide version:** `0.9.5.20260830.23`" in guide
    assert "49E.4 scientific acceptance" in guide
    assert "All 45 current-documentation tests passed in 2.03 seconds" in guide
    assert "45 current-documentation tests in 2.03" in contract


def test_49e5_records_astrometric_runtime_and_output_boundary():
    contract = " ".join(read(ASTROMETRIC_DIRECTION_CONTRACT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**Implementation baseline:** `888ca2c`",
        "ObserverBarycentricState",
        "AstrometricDirectionRequest",
        "AstrometricDirection",
        "AstrometricDirectionRealizer",
        "Earth-plus-WGS84-site",
        "same `Observer.ephemeris` object",
        "observer state is evaluated exactly once at reception",
        "target is evaluated repeatedly at emission times",
        "default is `1e-12` day with at most 10 iterations",
        "nanosecond decimal precision",
        "AstrometricDirectionConvergenceError",
        "AstrometricDirectionIdentityError",
        "not position reference epochs and not equinoxes",
        "one-way-light-time",
        "direct Skyfield `observe()`",
        "No future Venus, Moon, Sun, or planet",
        "Apparent-place realization remains 49E.6",
    ):
        assert phrase in contract

    assert "Milestone 49E.5 — Astrometric direction runtime" in roadmap
    assert "The accepted 49E.5 implementation" in architecture
    assert "13.2.9 49E.5 astrometric direction runtime" in guide
    assert "Neither is a position reference epoch" in guide
    assert "neither is an equinox" in guide
    assert "Guide version:** `0.9.5.20260830.23`" in guide
    assert "49E.5 scientific acceptance" in guide
    assert "converged in four iterations" in contract
    assert "`3.149e-11` degree" in contract
    assert "`1.348e-12` AU" in contract
    assert "111 focused tests in 4.33 seconds" in contract
    assert "all 1,878 tests in 85.55 seconds" in contract
    assert "Astrometric direction runtime (Milestone 49E.5)" in implementation
    assert "same-kernel Skyfield observer-state adapter" in source_tree
    assert "Solar-System direction-realizer audit" in implementation
    assert "documentation-only: no runtime realizer" in source_tree


def test_49e6_records_apparent_runtime_and_single_light_time_authority():
    contract = " ".join(read(APPARENT_DIRECTION_CONTRACT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**Implementation baseline:** `3752142`",
        "does not solve light time again",
        "calls Skyfield `apparent()`—never `observe()`",
        "Sun, Jupiter, and Saturn",
        "apparent status does not mean “equinox of date”",
        "relative velocity in AU/day",
        "shared PNG/PDF/SVG exporter",
    ):
        assert phrase in contract

    assert "Milestone 49E.6 — Apparent direction runtime" in roadmap
    assert "The accepted 49E.6 implementation" in architecture
    assert "13.2.10 49E.6 apparent direction runtime" in guide
    assert "Apparent direction runtime (Milestone 49E.6)" in implementation
    assert "without a second `observe()` call" in source_tree
    assert "Guide version:** `0.9.5.20260830.23`" in guide
    assert "Scientifically accepted by Fernando on 2026-08-30" in contract
    assert "`-3.152e-11` degree" in contract
    assert "95 focused tests in 3.79 seconds" in contract
    assert "all 1,883 tests in 91.21 seconds" in contract
    assert "49E.6 scientific acceptance" in guide


def test_49i1_audits_the_first_drawable_venus_vertical_slice():
    audit = " ".join(read(VENUS_VERTICAL_SLICE_AUDIT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**As-is baseline:** `17f5c10`",
        "Ordinary chart facades, however, do not construct",
        "49I.1A — Ordinary realization-context handoff",
        "49I.1B — One Venus layer",
        "transform the resulting `SphericalPoints` exactly once",
        "sky/solar_system/planets/venus",
        "must not implement a second altitude test",
        "one fixed Venus marker plus an optional `Venus` label",
        "`--planet venus`",
        "not a physical disk",
        "same projected record",
    ):
        assert phrase in audit

    assert "Milestone 49I.1 — Drawable Venus vertical slice" in roadmap
    assert "The 49I.1 audit identifies" in architecture
    assert "13.2.11 49I.1 drawable Venus audit" in guide
    assert "Guide version:** `0.9.5.20260830.23`" in guide
    assert "adds no runtime layer" in source_tree
    assert "Scientifically and architecturally accepted by Fernando" in audit
    assert "all 48 current-documentation tests in 3.30" in audit
    assert "49I.1 audit acceptance" in guide


def test_49i1a_records_the_output_neutral_ordinary_context_handoff():
    contract = " ".join(read(ORDINARY_REALIZATION_CONTEXT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**Implementation baseline:** `62da7b9`",
        "constructs it once before the product loop",
        "observer-local vacuum AltAz",
        "observer-origin Galactic",
        "position reference epoch and equinox are absent",
        "does not currently expose equatorial",
        "unchanged `spherical_geometry",
        "Final Mac acceptance verification passed 166 focused tests",
        "all 1,890 tests in 88.37 seconds",
        "Scientifically and architecturally accepted by Fernando",
        "adds no Venus layer",
    ):
        assert phrase in contract

    assert "Milestone 49I.1A — Ordinary realization-context handoff" in roadmap
    assert "The accepted 49I.1A implementation" in architecture
    assert "Ordinary realization-context handoff (Milestone 49I.1A)" in implementation
    assert "request_realization.py` owns the 49I.1A" in source_tree
    assert "13.2.12 49I.1A ordinary realization context" in guide
    assert "Guide version:** `0.9.5.20260830.23`" in guide
    assert "49I.1A scientific and architectural acceptance" in guide


def test_49i1b_records_the_first_drawable_venus_boundary():
    contract = " ".join(read(VENUS_LAYER_CONTRACT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())

    for phrase in (
        "**Implementation baseline:** `94d5e99`",
        "`--planet venus`",
        "transforms the resulting apparent ICRS point exactly once",
        "sky/solar_system/planets/venus",
        "fixed hollow circular marker",
        "no magnitude, phase, illuminated fraction",
        "Scientifically and visually accepted by Fernando",
        "all 1,898 tests in 82.01 seconds",
        "same position shown by Stellarium",
        "G024.7-00.6",
        "G024.7+00.6",
    ):
        assert phrase in contract
    assert "Milestone 49I.1B — First drawable Venus layer" in roadmap
    assert "The accepted 49I.1B implementation" in architecture
    assert "all 1,898 tests in 82.01 seconds" in roadmap
    assert "PNG, PDF, and semantic SVG looked the same" in architecture
    assert "13.2.13 49I.1B first drawable Venus" in guide
    assert "Guide version:** `0.9.5.20260830.23`" in guide
    assert "not a position reference epoch and not an equinox" in guide
    assert "Fernando scientifically and visually accepted" in guide


def test_49i2_audits_one_pipeline_without_flattening_body_science():
    audit = " ".join(read(MOON_SHARED_PIPELINE_AUDIT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())

    for phrase in (
        "**As-is baseline:** `e7fa6ab`",
        "one canonical moving-body chart pipeline",
        "interchangeable state source",
        "different physical-appearance strategies",
        "does not mean relabelling every orbit source as a JPL kernel",
        "Major planet",
        "Minor planet",
        "Comet",
        "Artificial satellite",
        "target provider identity `moon`, expected NAIF ID `301`",
        "common state centre `solar system barycenter`, NAIF ID `0`",
        "strong topocentric parallax",
        "observer geodetic location and height",
        "direct Skyfield `observe(...).apparent()`",
        "The Moon must not be implemented by copying `VenusLayer`",
        "CLI ergonomics may remain class-aware",
        "49I.2A — Moon numerical direction validation",
        "49I.2B — Shared solar-system point layer",
        "49I.2C — First drawable Moon point",
        "49I.3 — Physical apparent-disk contract",
        "adds no runtime type, Moon layer, public option",
        "Scientifically and architecturally accepted by Fernando",
        "51 current-documentation tests passed in 1.88 seconds",
        "The answers are yes",
    ):
        assert phrase in audit

    assert (
        "Milestone 49I.2 — Moon and shared solar-system-body pipeline"
        in roadmap
    )
    assert "The proposed 49I.2 audit" in architecture
    assert "Fernando scientifically and architecturally accepted" in architecture
    assert "13.2.14 49I.2 Moon and shared body pipeline" in guide
    assert "Guide version:** `0.9.5.20260830.23`" in guide
    assert (
        "One pipeline” does not mean that all objects move in the same way"
        in guide
    )
    assert "position reference epoch" in guide
    assert "observation instant" in guide
    assert "equinox remain distinct concepts" in guide
    assert "accepted first Moon is a symbolic point" in guide


def test_49i2a_validates_moon_direction_without_installing_a_layer():
    contract = " ".join(read(MOON_DIRECTION_VALIDATION).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**Implementation baseline:** `fbf4dd9`",
        "target `moon`, expected NAIF ID `301`",
        "centre `solar system barycenter`, expected NAIF ID `0`",
        "direct Skyfield `observer.skyfield.at(t).observe(moon).apparent()`",
        "topocentric and geocentric apparent directions",
        "registered 52 m La Ligua observer",
        "same latitude/longitude at zero elevation",
        "requires a non-zero height effect",
        "does not accept this policy for the Moon by analogy with Venus",
        "within `1e-7` degree (`0.36` milliarcsecond)",
        "observation instant is neither a position reference epoch nor an equinox",
        "test-only NAIF-301 state",
        "without invoking a second `observe()`",
        "102 focused tests passed in 1.99 seconds",
        "all 1,902 tests passed in 89.59 seconds",
        "`0.9500231004` degree",
        "`27.91` mas",
        "does not extract `SolarSystemPointLayer`",
    ):
        assert phrase in contract

    assert "Milestone 49I.1 — Drawable Venus vertical slice" in roadmap
    assert "merged in `e7fa6ab`" in roadmap
    assert "Milestone 49I.2 — Moon and shared solar-system-body pipeline" in roadmap
    assert "in `fbf4dd9`" in roadmap
    assert "Milestone 49I.2A — Numerical Moon-direction validation" in roadmap
    assert "Scientifically accepted and full-suite verified" in roadmap
    assert "all 1,902 tests passed in 89.59 seconds" in roadmap
    assert "Fernando scientifically accepted 49I.2A" in architecture
    assert "Numerical Moon-direction validation (Milestone 49I.2A)" in implementation
    assert "No `sky/moon.py` exists in 49I.2A" in source_tree
    assert "13.2.15 49I.2A numerical Moon direction" in guide
    assert "Guide version:** `0.9.5.20260830.23`" in guide
    assert "topocentric parallax rather than confusing origin with reference frame" in guide


def test_49i2b_extracts_shared_point_orchestration_without_moon_content():
    contract = " ".join(read(SHARED_SOLAR_SYSTEM_POINT_LAYER).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**Implementation baseline:** `b0d1dd4`",
        "`SolarSystemPointDescriptor`",
        "`SolarSystemPointLayer`",
        "transform exactly once into the product coordinate specification",
        "`layer_name = \"venus\"`",
        "sky/solar_system/planets/venus",
        "test-only Moon descriptor",
        "does not add `sky/moon.py`",
        "13 direct shared-layer and Venus parity tests in 1.86 seconds",
        "82 focused scientific and integration tests in 1.82 seconds",
        "1,881 routine tests with 30 deselected in 27.67 seconds",
        "53 current-documentation tests in 2.16 seconds",
        "all 1,912 tests in 91.04 seconds",
        "The PNG files were byte-identical",
        "zero differing pixels or channel values",
        "SVG semantic and graphical content was byte-identical",
        "Fernando accepted the frozen descriptor",
        "does not authorize a production Moon layer",
        "adds no Moon layer, `--moon`",
    ):
        assert phrase in contract

    assert "Milestone 49I.2B — Shared Solar-System point layer" in roadmap
    assert "Fernando scientifically and architecturally accepted 49I.2B" in roadmap
    assert "The accepted 49I.2B implementation extracts" in architecture
    assert "Shared Solar-System point layer (Milestone 49I.2B)" in implementation
    assert "tests/test_solar_system_point_layer.py" in source_tree
    assert "13.2.16 49I.2B shared Solar-System point layer" in guide
    assert "Guide version:** `0.9.5.20260830.23`" in guide
    assert "`--moon` remains 49I.2C" in guide
    assert "Fernando scientifically and architecturally accepted 49I.2B" in guide


def fenced_python(path):
    """Return Python code blocks from one Markdown document."""
    blocks = []
    current = None
    for line in read(path).splitlines():
        if line == "```python":
            current = []
        elif line == "```" and current is not None:
            blocks.append("\n".join(current))
            current = None
        elif current is not None:
            current.append(line)
    return blocks


def test_current_architecture_authorities_exist_and_cross_reference():
    assert [
        path
        for path in (
            CURRENT,
            IMPLEMENTED,
            V08_CURRENT,
            TARGET,
            ROADMAP,
            V09_CURRENT,
            V09_TARGET,
            V09_ROADMAP,
            FUTURE_ROADMAP,
            PUBLIC_INTERFACE_AUDIT,
            SCENE_DEPENDENCY_AUDIT,
            LAYER_REALIZATION_CONTRACT,
            V095_TARGET,
            COORDINATE_GUIDE,
            INSTRUCTIONS,
        )
        if not path.is_file()
    ] == []

    current = read(CURRENT)
    target = read(V09_TARGET)
    roadmap = read(V09_ROADMAP)

    assert "target_architecture_v0.7.md" in current
    assert "archive/architecture_history/current_architecture_v0.8.md" in target
    assert "archive/migration_history/wenu_migration_0.8_to_0.9.md" in target
    assert "archive/architecture_history/current_architecture_v0.8.md" in roadmap
    assert "archive/architecture_history/target_architecture_v0.9.md" in roadmap


def test_historical_documents_are_archived_and_not_active_authorities():
    assert (ARCHIVE / "README.md").is_file()
    assert not (ROOT / "docs" / "obsolete").exists()
    for name in (
        "current_architecture_v0.4.md",
        "current_architecture_v0.5.md",
        "current_architecture_v0.6.md",
        "current_architecture_v0.7.md",
        "target_architecture_v0.5.md",
        "target_architecture_v0.6.md",
        "target_architecture_v0.7.md",
        "current_architecture_v0.8.md",
        "target_architecture_v0.8.md",
        "target_architecture_v0.9.md",
    ):
        assert (ARCHIVE / "architecture_history" / name).is_file()
        assert not (DEVELOPER / name).exists()
    for name in (
        "wenu_migration_0.4_to_0.5.md",
        "wenu_migration_0.5_to_0.6.md",
        "wenu_migration_0.6_to_0.7.md",
        "wenu_migration_0.7_to_0.8.md",
        "wenu_migration_0.8_to_0.9.md",
    ):
        assert (ARCHIVE / "migration_history" / name).is_file()
        assert not (DEVELOPER / name).exists()
    assert (ARCHIVE / "pre_versioned" / "architecture.md").is_file()


def test_current_diagrams_are_an_inspection_interface():
    readme = read(DIAGRAMS / "README.md")
    normalized = " ".join(readme.split())

    for name in (
        "current_architecture_v0.9_overview",
        "coordinate_transformation_as_is_v0.9",
        "coordinate_transformation_target_49bc",
        "coordinate_static_structure_as_is_v0.9",
        "coordinate_static_structure_target_49bc",
        "coordinate_runtime_sequence_target_49bc",
        "coordinate_transformation_as_is_v0.9.5",
        "coordinate_static_structure_as_is_v0.9.5",
        "coordinate_runtime_sequence_as_is_v0.9.5",
    ):
        assert (DIAGRAMS / f"{name}.dot").is_file()
        assert (DIAGRAMS / f"{name}.svg").is_file()
        assert name in readme

    assert "human inspection interface" in readme
    assert "49B introduces typed astronomical-state vocabulary" in readme
    assert "49C introduces one coordinate service" in readme
    assert "every astronomical object obtains its native position" in readme
    assert "`ObservationContext` enters only" in readme
    assert "actual classes" in readme
    assert "inherits" in readme
    assert "runtime calls or returns" in normalized
    assert "No parallel astronomical state hierarchy is proposed" in normalized
    assert "direct counterpart to the current static-structure" in readme
    assert "retains the same `SkyLayer` inheritance hierarchy" in readme
    assert "`PositionProvider` is the boundary for all astronomical objects" in readme
    assert "requires only another provider implementation" in normalized
    assert "deliberately large canvas" in readme
    assert "sole production astronomical transformation owner" in normalized
    assert "fictitious protocol" in readme
    assert "The retired handwritten and chart-owned authorities are absent" in normalized
    assert "does not modify `CoordinateService`" in normalized
    assert (
        ARCHIVE / "diagram_history" / "target_architecture_v0.5_combined.dot"
    ).is_file()
    assert (
        ARCHIVE / "diagram_history" / "target_architecture_v0.5_combined.svg"
    ).is_file()
    assert not (DIAGRAMS / "target_architecture_v0.5_combined.dot").exists()
    assert not (DIAGRAMS / "target_architecture_v0.5_combined.svg").exists()



def test_v095_coordinate_target_and_living_guide_are_reviewable():
    target = read(V095_TARGET)
    guide = read(COORDINATE_GUIDE)

    assert "**Status:** Implemented and accepted; 49C.4 merged in `1a15076`" in target
    assert "PositionProvider" in target
    assert "CoordinateService" in target
    assert "49B.1" in target
    assert "49C.4" in target
    assert "does not claim a\n`v0.9.5` Git tag" in target
    assert "Skyfield apparent stellar realization as provider work" in target
    assert "native AltAz horizon construction" in target
    assert "Removed in 49C.3" in guide
    assert "Observer.observation_context" in target
    assert "1779 tests with 30 deselected in 27.31 seconds" in target
    assert "1809 tests in 84.99 seconds" in target
    assert "mixed\nJ2000-equator/ecliptic-of-date policy" in target

    for phrase in (
        "Position generation versus coordinate transformation",
        "International Celestial Reference System",
        "FK5 equatorial coordinates",
        "Galactic coordinates",
        "Ecliptic coordinates",
        "Horizontal AltAz coordinates",
        "TEME",
        "Current transformation inventory and 0.9.5 destination",
        "Wenu object catalogue and provenance",
        "ESA Hipparcos Catalogue I/239",
        "OpenNGC",
        "Gaia DR3",
        "Minimal architecture 0.9.5 roadmap",
        "canonical celestial-reference furniture uses one coherent policy",
        "Architecture 0.9.5 acceptance",
    ):
        assert phrase in guide


def test_v08_release_evidence_remains_closed():
    target = read(TARGET)
    roadmap = read(ROADMAP)
    readme = read(ROOT / "README.md")

    assert "**Status:** Implemented" in target
    assert "**Release:** 0.8.0" in target
    assert "**Status:** Complete" in roadmap
    assert "Milestone 46E" in roadmap
    assert "annotated Git tag `v0.8.0`" in roadmap
    assert "Version 0.8.0 remains the latest tagged" in readme


def test_v09_architecture_is_closed_and_current():
    current = read(V09_CURRENT)
    target = read(V09_TARGET)
    roadmap = read(V09_ROADMAP)
    implementation = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")
    readme = read(ROOT / "README.md")
    instructions = read(INSTRUCTIONS)

    assert "**Status:** Implemented current architecture" in current
    assert "**Baseline commit:** `5da93cc`" in current
    assert "optional night edition remains a later appearance experiment" in current.lower()
    assert "**Status:** Implemented; retained as the accepted design record" in target
    assert "**Status:** Complete" in roadmap
    assert "**Current authority:** `current_architecture_v0.9.md`" in roadmap
    assert "**Architecture version:** 0.9" in implementation
    assert "**Architecture version:** 0.9" in source_tree
    assert "v0.9 architecture is complete" in readme
    assert "current_architecture_v0.9.md" in instructions


def test_v09_plan_records_paired_physical_planisphere_contract():
    current = read(V08_CURRENT)
    target = read(V09_TARGET)
    roadmap = read(V09_ROADMAP)

    for phrase in (
        "**Baseline commit:** `c169162`",
        "Projection gap",
        "Physical-product gap",
    ):
        assert phrase in current
    for phrase in (
        "polar azimuthal-equidistant projection",
        "-90 degrees through +20 degrees",
        "+90 degrees through -20 degrees",
        "glued back to back",
        "opposite",
        "365 daily ticks",
        "20:00 through 04:00",
        "Localization is the last",
    ):
        assert phrase in target
    for phrase in (
        "Milestone 48B",
        "Milestone 48C",
        "Milestone 48D",
        "Milestone 48E",
        "Wednesday, 2026-08-19",
        "Milestone 48G",
        "Milestone 48J",
        "Milestone 48K",
    ):
        assert phrase in roadmap


def test_release_version_comes_from_scm_with_v08_archive_fallback():
    project = tomllib.loads(read(ROOT / "pyproject.toml"))

    assert project["project"]["dynamic"] == ["version"]
    assert project["tool"]["setuptools_scm"]["fallback_version"] == "0.8.0"


def test_assistant_instructions_name_current_architecture_authorities():
    instructions = read(INSTRUCTIONS)
    for name in (
        "current_architecture_v0.9.md",
        "archive/architecture_history/target_architecture_v0.9.md",
        "archive/migration_history/wenu_migration_0.8_to_0.9.md",
        "implementation_reference.md",
        "source_tree.md",
        "coordinate_transformation_audit_09a2afd.md",
        "post_v0.9_architecture_roadmap.md",
    ):
        assert name in instructions
    assert "historical evidence, not active" in instructions


def test_post_v09_roadmap_records_coordinate_svg_and_temporal_direction():
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    for phrase in (
        "Two independent development tracks",
        "One astronomical coordinate service",
        "Position-provider boundary",
        "SVG product verification",
        "Temporal sequence contract",
        "Fixed sky and rotating horizon",
        "tools/render_circumpolar_movie.py",
        "simulation time",
        "time scale",
        "TEME",
        "SGP4",
        "complete-render path as a correctness oracle",
        "Milestone 49C.2 — Migrate production transformations",
        "1809 tests in 86.11 seconds",
        "visually accepted by Fernando on 2026-08-28",
        "1805 tests in 86.29 seconds",
        "1779 tests with 30 deselected in 27.31 seconds",
        "1809 tests in 84.99 seconds",
        "Immediate post-v0.9.5 public-interface follow-up",
        "make the installed `wenu_chart` command the ordinary public route",
        "reserve `tools/` for diagnostics",
        "coordinate system, frame, epoch/equinox",
    ):
        assert phrase in roadmap


def test_49d1_audits_scene_dependencies_without_runtime_change():
    audit = " ".join(read(SCENE_DEPENDENCY_AUDIT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(
        read(DEVELOPER / "source_tree.md").split()
    )

    for phrase in (
        "**Audit baseline:** `b4af627`",
        "load-time ownership",
        "observer-independent loaded sphere currently produces an "
        "observer-dependent render realization",
        "Source identity",
        "Provider epoch",
        "Evaluation instant",
        "Reference policy",
        "Product frame",
        "Celestial background",
        "Dynamic astronomical objects",
        "Observer-local geometry",
        "before projection and after provider evaluation",
        "one explicit spherical product frame",
        "controlled test provider",
        "must preserve the current call",
        "This audit classifies dependencies; it does not authorize caching",
        "does not introduce a scene graph",
    ):
        assert phrase in audit

    for phrase in (
        "Milestone 49D.1 — Celestial-scene dependency and ownership audit",
        "Completing every 49D migration is not a prerequisite",
        "real ephemeris provider remains Milestone 49E",
    ):
        assert phrase in roadmap

    for phrase in (
        "Scene dependencies and moving astronomical objects",
        "A planet therefore does not belong in the renderer",
        "The planet-enabling insertion point is after provider evaluation",
        "Wenu implementation box — 49D.1 dependency boundary",
    ):
        assert phrase in guide

    assert "Celestial-scene dependencies (Milestone 49D.1)" in implementation
    assert "does not enter through the renderer, furniture, command" in (
        implementation
    )
    assert "Milestone 49D.1 adds no runtime module" in source_tree
    for phrase in (
        "Scientifically and pedagogically accepted",
        "39 documentation tests in 2.78 seconds",
        "1,789 routine tests with 30 deselected in 26.62 seconds",
        "all 1,819 tests in 84.41 seconds",
        "this acceptance does not itself authorize that runtime change",
    ):
        assert phrase in audit
    assert "49D.1 scientific and pedagogical acceptance" in guide
    assert "accepted the scene-dependency explanation" in guide
    assert "No visual comparison was required" in roadmap


def test_49d2_records_minimal_realization_context_and_non_goals():
    contract = " ".join(read(LAYER_REALIZATION_CONTRACT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(
        read(DEVELOPER / "source_tree.md").split()
    )

    for phrase in (
        "**Implementation baseline:** `9e16ed2`",
        "product_coordinate_spec",
        "evaluation_instant",
        "evaluation_time_scale",
        "reference_equinox",
        "contains no projection, viewport, renderer, style",
        "Context omitted",
        "Typed context supplied",
        "exact legacy branch",
        "deterministic test-only provider",
        "transforms it exactly once through `CoordinateService`",
        "A chart-wide frame choice alone cannot replace",
        "does not add or choose a JPL ephemeris",
        "does not thread the context through ordinary",
        "Scientifically, pedagogically, and technically accepted",
        "all 1,828 tests in 90.00 seconds",
        "Output-neutral and SVG contract",
        "`solar-system/sun`",
        "No future moving object may be drawn by a separate SVG generator",
    ):
        assert phrase in contract

    for phrase in (
        "Milestone 49D.2 — Minimal layer-realization context",
        "Ordinary chart requests do not supply one in 49D.2",
        "Real ephemerides, installed moving-object layers",
        "SVG product may serialize the reserved",
        "no post-export overlay is acceptable",
        "Acceptance evidence is 48 focused tests",
    ):
        assert phrase in roadmap

    for phrase in (
        "optional immutable `LayerRealizationContext` before projection",
        "no current astronomical layer",
        "single export path",
        "must not infer astronomical identity",
        "accepted by Fernando on",
    ):
        assert phrase in architecture

    for phrase in (
        "49D.2 minimal realization handoff",
        "small sealed “instruction card”",
        "controlled test object",
        "This proves ownership and ordering, not planetary accuracy",
        "Wenu implementation box — 49D.2 realization context",
        "SVG is not a second astronomy engine",
        "13.2.3 49D.2 scientific and pedagogical acceptance",
    ):
        assert phrase in guide

    assert "Minimal layer-realization context (Milestone 49D.2)" in (
        implementation
    )
    assert "Supplying no `realization_context`" in implementation
    assert "downstream annotator serializes the reserved" in implementation
    assert "No separate SVG astronomy generator" in source_tree
    assert "`sky/realization.py` owns the frozen 49D.2" in source_tree
    assert "exist only in `tests/test_layer_realization.py`" in source_tree


def test_49e1_records_ephemeris_source_and_direction_realizer_boundary():
    contract = " ".join(read(EPHEMERIS_PROVIDER_CONTRACT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**As-is baseline:** `85c7392`",
        "Required two-stage boundary",
        "ephemeris state source",
        "solar-system direction realization",
        "Centre and frame are not synonyms",
        "retarded emission times",
        "one-way light time",
        "kernel identity",
        "`PositionStatus.TOPOCENTRIC` is scientifically misplaced",
        "No correction may be implied",
        "no hidden network access during rendering",
        "A raw ephemeris state is not `SphericalGeometry`",
        "Body geometry deliberately deferred",
        "49E.2 — minimal runtime contracts",
        "49E.3 — installed kernel adapter",
        "six-component position-velocity",
        "SHA-256 content fingerprint",
        "use Venus for 49I.1",
        "all 41 current-documentation tests in 3.26",
        "49I.1 — Venus vertical slice",
    ):
        assert phrase in contract

    for phrase in (
        "Milestone 49E.1 — Ephemeris-provider contract audit",
        "Cartesian state source",
        "retarded emission-time evaluation",
        "49E.1 changed no runtime type or output",
        "Venus is the first 49I.1 body",
        "Acceptance verification passed all 41 documentation",
    ):
        assert phrase in roadmap

    assert "proposed 49E.1 ephemeris boundary" in architecture
    assert "raw barycentric vector must never be relabelled" in architecture
    assert "`PositionStatus.TOPOCENTRIC` is removed atomically" in architecture
    assert "Venus is the first planned 49I.1 body" in architecture
    assert "13.2.4 49E.1 ephemeris-provider design" in guide
    assert "more like a precise moving map" in guide
    assert "Wenu implementation box — 49E.1 provider boundary" in guide
    assert "SHA-256 is computed once" in guide
    assert "Venus is the first planned moving-body" in guide
    assert "All 41 documentation tests passed in 3.26 seconds" in guide
    assert "Proposed ephemeris-provider boundary" in implementation
    assert "first later vertical slice is Venus" in implementation
    assert "`skyfield_ephemeris.py` now owns the first real" in source_tree


def test_49e2_records_minimal_runtime_contracts_and_non_goals():
    contract = " ".join(read(EPHEMERIS_RUNTIME_CONTRACT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**Implementation baseline:** `d14ca52`",
        "EphemerisResourceIdentity",
        "EphemerisStateRequest",
        "EphemerisState",
        "EphemerisStateSource",
        "There is no default or optional velocity",
        "This is an atomic internal correction",
        "`observer_altaz_spec()` now requires an explicit `position_status`",
        "Native observer-local horizon",
        "The new state is geometric Cartesian provider output",
        "deterministic Venus state",
        "solar-system/planets/venus",
        "This proves contract shape and ownership, not ephemeris accuracy",
        "does not create it",
        "calculate a SHA-256 digest from a file",
        "No new visual render was required",
        "scientifically accepted 49E.2 on 2026-08-30",
        "92 focused tests in 2.72 seconds",
        "1,821 routine tests",
        "all 1,851 tests in 84.12 seconds",
        "future Venus, Moon, planet, and Sun products",
    ):
        assert phrase in contract

    for phrase in (
        "Milestone 49E.2 — Minimal ephemeris runtime contracts",
        "complete six-component `EphemerisState`",
        "No real file is opened or hashed",
        "`PositionStatus.TOPOCENTRIC` member is removed atomically",
        "test-only Venus source",
        "requires every caller to declare `position_status`",
        "Scientifically accepted by Fernando on 2026-08-30",
        "1,821 routine tests with 30 deselected",
        "all 1,851 tests in 84.12 seconds",
    ):
        assert phrase in roadmap

    assert "49E.2 installs only renderer-neutral" in architecture
    assert "13.2.5 49E.2 minimal runtime state contracts" in guide
    assert "state in space—not yet the direction" in guide
    assert "Wenu implementation box — 49E.2 runtime boundary" in guide
    assert "deliberately has no status default" in guide
    assert "future refracted products" in guide
    assert "Minimal ephemeris runtime contracts (Milestone 49E.2)" in implementation
    assert "requires an explicit `position_status`" in implementation
    assert "native horizon" in implementation
    assert "`ephemeris.py` owns the frozen 49E.2" in source_tree
    assert "requires explicit status at every" in source_tree
    assert "deterministic contract source remains in `tests/test_ephemeris.py`" in source_tree



def test_49e3_records_borrowed_skyfield_adapter_and_non_goals():
    contract = " ".join(read(SKYFIELD_EPHEMERIS_CONTRACT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**Implementation baseline:** `7a978a0`",
        "Borrowed Skyfield ephemeris adapter",
        "relative to what?",
        "three for position and three for velocity",
        "simultaneous geometric difference",
        "opens no second kernel",
        "conservative common intersection",
        "only `frame=\"icrf\"`",
        "position in AU",
        "velocity in AU/day",
        "separate deterministic Wenu exceptions",
        "refuses to download a missing kernel",
        "does not independently revalidate the DE440 dynamical solution",
        "not a sky direction and is not drawable",
        "Venus rendering remains 49I.1",
        "c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2",
        "common coverage JD 2396752.5 through JD 2506352.5 TDB",
        "residual was zero within that tolerance",
        "Scientifically accepted by Fernando on 2026-08-30",
        "72 focused tests in 1.73 seconds",
        "1,830 routine tests",
        "all 1,860 tests in 84.78 seconds",
        "explicit stable HTML anchors",
        "Accepted living-guide revision",
        "coordinate guide version `0.9.5.20260830.3`",
        "All 44 current-documentation tests passed in 1.70 seconds",
    ):
        assert phrase in contract

    for phrase in (
        "Milestone 49E.3 — Borrowed Skyfield ephemeris adapter",
        "fingerprints the exact BSP bytes once",
        "Venus-relative-to-SSB",
        "adds no direction realizer",
    ):
        assert phrase in roadmap

    assert "49E.3 installs `SkyfieldEphemerisStateSource`" in architecture
    assert "13.2.6 49E.3 borrowed Skyfield kernel adapter" in guide
    assert "DE440` identifies the astronomical solution family" in guide
    assert "common intersection of all SPK segment intervals" in guide
    assert "Wenu implementation box — 49E.3 installed adapter" in guide
    assert "49E.3 real-resource evidence" in guide
    assert "zero residual within an absolute tolerance" in guide
    assert "Terminology contract — four different questions" in guide
    assert "`CoordinateSpec.epoch` means a **position reference epoch**" in guide
    assert "NAIF and SPICE identifiers" in guide
    assert "Navigation and Ancillary Information Facility" in guide
    assert "Spacecraft, Planet, Instrument, C-matrix, Events" in guide
    for anchor in (
        "#coordinate-system-vs-reference-frame",
        "#epoch-vs-equinox",
        "#49e3-skyfield-adapter",
        "#naif-spice-identifiers",
    ):
        assert anchor in guide
        assert f'<a id="{anchor[1:]}"></a>' in guide
    assert "Borrowed Skyfield ephemeris adapter (Milestone 49E.3)" in implementation
    assert "The adapter has no `close()`" in implementation
    assert "`skyfield_ephemeris.py` now owns the first real" in source_tree
    assert "no-download installed-kernel Venus/SSB acceptance check" in source_tree

def test_public_interface_audit_records_as_is_and_scientific_boundary():
    audit = " ".join(read(PUBLIC_INTERFACE_AUDIT).split())
    for phrase in (
        "**Audit baseline:** `1a15076`",
        "The six canonical Python examples",
        "Reproducible user recipes currently under `tools/`",
        "Diagnostics, acceptance, and benchmarks",
        "Catalogue and repository maintenance",
        "The first bounded part of that vocabulary is now public",
        "coordinate system",
        "reference frame",
        "equinox",
        "position epoch",
        "observation instant",
        "an equinox is not a defining parameter of ICRS",
        "`of_date` resolves from the declared product or observation time",
        "It must never relabel native catalogue coordinates",
        "Reference-policy contract",
        "Product-frame selection",
        "Provider realization epoch",
        "Physical-product command",
    ):
        assert phrase in audit


def test_coordinate_guide_has_a_navigable_table_of_contents():
    guide = read(COORDINATE_GUIDE)
    toc_position = guide.index("# Table of contents")
    status_position = guide.index("# Status and purpose")
    assert toc_position < status_position

    for link in (
        "[1. Scientific vocabulary](#1-scientific-vocabulary)",
        "[2. Coordinate systems used or reserved by Wenu]",
        "[4. Mathematical foundations](#4-mathematical-foundations)",
        "[5. Time vocabulary](#5-time-vocabulary)",
        "[5.6 Julian and Besselian epochs]",
        "[8. Wenu object catalogue and provenance]",
        "[12. Maintenance rule](#12-maintenance-rule)",
        "[13. Practical guide to reference systems, equinoxes, and epochs]",
    ):
        assert link in guide



def test_coordinate_guide_toc_uses_explicit_portable_anchors():
    guide = read(COORDINATE_GUIDE)
    toc = guide[
        guide.index("# Table of contents"):
        guide.index("# Status and purpose")
    ]
    targets = re.findall(r"\]\(#([^)]+)\)", toc)

    assert len(targets) >= 60
    assert len(targets) == len(set(targets))
    for target in targets:
        assert f'<a id="{target}"></a>' in guide

    assert "**Guide version:** `0.9.5.20260830.23`" in guide
    assert "**Last updated:** `2026-08-30T23:47:41Z`" in guide
    assert "reference epoch or equinox" not in guide
    assert "epoch/equinox" not in guide
    assert "- coordinate system and representation;" in guide
    assert "- reference frame and its physical realization;" in guide
    assert "equinox, only for a frame whose axes are equinox-based" in guide
    assert "position reference epoch, only for a catalogue state" in guide
    header = guide[:guide.index("# Table of contents")]
    assert header.splitlines()[:8] == [
        "# Wenu Coordinate Systems and Astronomical Objects",
        "",
        "**Subtitle:** Living scientific and implementation guide for architecture 0.9.5  ",
        "**Author:** Wenu project  ",
        "**Architecture version:** `0.9.5`  ",
        "**Guide version:** `0.9.5.20260830.23`  ",
        "**Last updated:** `2026-08-30T23:47:41Z`  ",
        "**Language:** English",
    ]


def test_coordinate_guide_teaches_calendars_for_historical_use():
    guide = " ".join(read(COORDINATE_GUIDE).split())
    for phrase in (
        "Calendars are historical coordinate systems for time",
        "There was no single timeless “Sumerian calendar.”",
        "Babylonian and Assyrian",
        "five epagomenal days",
        "There was no single ancient Greek civil calendar",
        "Roman Republican calendar",
        "*Proleptic* means that a rule is extended to dates before the rule was historically introduced",
        "Greek *prolepsis*, “anticipation” or “taking beforehand.”",
        "not a historical reconstruction",
        "Did Augustus steal a day from February?",
        "there is no historical year in which Augustus “stole” the day",
        "Sextilis was renamed *Augustus* in 8 BCE",
        "February was already the exceptional short month",
        "supposed transfer of a day from February is an unsupported legend",
        "Britain and its colonies changed in September 1752",
        "A historian's minimum date record",
        "No year zero in ordinary BCE/CE history",
        "Julian calendar is not Julian Date",
        "UTC is not an ancient time scale",
        "Delta T = \\mathrm{TT}-\\mathrm{UT1}",
        "Julian and Besselian epochs are not calendars",
        "Tropical, sidereal, and Besselian years",
        "measured from the moving equinox",
        "roughly 20 minutes longer",
        "fictitious mean Sun",
        "mean right ascension 18h 40m",
        "365.242198781",
        "must not be treated as an immutable modern measurement",
        "`B1950.0` denotes the instant obtained from this mean-Sun convention",
        "Wenu implementation box — Calendars and historical chronology",
        "It is **not** a general historical-calendar converter",
        "HistoricalDateSpec",
        "years 1–9999",
    ):
        assert phrase in guide


def test_coordinate_guide_teaches_reference_policy_at_two_depths():
    guide = " ".join(read(COORDINATE_GUIDE).split())
    for phrase in (
        "**[Foundation]**",
        "**[Undergraduate]**",
        "Julian and Besselian year labels",
        "A Julian year is exactly 365.25 days",
        "Gaia DR2 positions use position reference epoch `J2015.5`",
        "Gaia EDR3 and DR3 positions use `J2016.0`",
        "The Gaia position reference epoch is not an equinox",
        "an equinox is not one of its defining frame parameters",
        "Gaia-CRF3 is a high-precision optical realization of ICRS",
        "ICRF3 is the third radio realization of ICRS",
        "`FK5(equinox=J2000.0)` is close to ICRS but is not identical",
        "Wenu currently represents Gaia-compatible celestial geometry as `icrs`",
        "Equinox applicability by system and frame",
        "ICRS does not have a **defining equinox**, fixed or selectable",
        "The small rotation between ICRS/GCRS axes and the dynamical mean equator",
        "TEME is a special case whose name includes “mean equinox,”",
        "Concept box — How an abstract celestial sphere becomes a measured frame",
        "Least squares alone therefore does not determine the absolute orientation",
        "Astrometric Global Iterative Solution (AGIS)",
        "True Equator, Mean Equinox",
        "Simplified General Perturbations 4 (SGP4)",
        "`FK` comes from the German *Fundamentalkatalog*",
        "The adopted corrections are part of the frame's provenance",
        "Wenu implementation box — Where each responsibility lives",
        "Wenu does not rebuild ICRS, Gaia-CRF3, or FK5",
        "`coordinates.py::CoordinateSpec`",
        "`coordinate_service.py::CoordinateService`",
        "`charts/reference_policy.py::CelestialReferencePolicy`",
        "Existing Gaia-derived Magellanic Cloud isophotes are morphology products",
        "Only `vacuum` is currently accepted",
        "Future specialized TEME adapter",
        "Wenu starts at the published catalogue/provider-state boundary",
        "Every medium or major Wenu change must include an explicit review",
        "A passing documentation test is not a substitute for Fernando's",
    ):
        assert phrase in guide


def test_architecture_v095_closure_and_example_count_are_current():
    roadmap = read(FUTURE_ROADMAP)
    target = read(V095_TARGET)
    guide = read(COORDINATE_GUIDE)
    diagrams = read(DIAGRAMS / "README.md")
    implementation = read(DEVELOPER / "implementation_reference.md")

    for text in (roadmap, target, guide, diagrams):
        assert "merge pending" not in text
        assert "1a15076" in text
    normalized = " ".join(implementation.split())
    assert "installs these six scripts" in normalized
    assert "- `all_sky.py`;" in implementation


def test_v08_roadmap_records_ordinary_interface_and_static_sequences():
    target = read(TARGET)
    roadmap = read(ROADMAP)

    for phrase in (
        "Three-stage ordinary Python interface",
        "observer-independent loaded-content container",
        "Defining a projection and applying it are separate operations",
        "fewer than 70 lines",
        "Reproducible image-frame sequences",
        "does not encode movies",
    ):
        assert phrase in target

    for phrase in (
        "Milestone 46C.8G",
        "Milestone 46C.8O",
        "Pass observer explicitly through canonical execution",
        "Decouple maximal-sphere construction",
        "one observer-independent canonical maximal sphere",
        "fewer-than-70-line declarative examples",
        "movie encoding",
        "Hawaii-to-Tahiti",
        "coordinate-epoch precession",
    ):
        assert phrase in roadmap


def test_horizon_roadmap_separates_boundary_reference_and_mask_roles():
    target = read(TARGET)
    roadmap = read(ROADMAP)

    for phrase in (
        "Observer-horizon roles",
        "`--horizon`",
        "`--horizon-mask`",
        "deliberately not opaque",
        "paints one effective outside mask exactly once",
        "idempotent no-ops for a planisphere",
    ):
        assert phrase in target
    for phrase in (
        "Milestone 46C.8Q.1",
        "Milestone 46C.8Q.3",
        "Milestone 46C.8Q.4",
        "Milestone 46C.8Q.5",
        "Milestone 46C.8Q.9",
        "preventing accumulated opacity",
        "runtime behavior remains",
        "declaration and adapter plumbing",
        "reference appearance and mask behavior remain",
        "mask-opening geometry preparation",
    ):
        assert phrase in roadmap


def test_configuration_default_audit_covers_every_public_responsibility():
    audit = read(CONFIGURATION_AUDIT)
    roadmap = read(ROADMAP)

    for phrase in (
        "public default",
        "derived value",
        "invariant",
        "implementation detail",
        "observer",
        "subject",
        "family geometry",
        "detail",
        "style",
        "output mode",
        "grids/references",
        "furniture",
        "product",
        "export",
        "line_width",
        "line_style",
        "Duplication and conflict register",
        "Output-mode transformation inventory",
    ):
        assert phrase in audit
    assert "Milestone 46D.1A" in roadmap
    assert "Milestone 46D.1B" in roadmap
    for phrase in (
        "Exact ordered value inventory",
        "Atlas-print semantic style",
        "Mode palettes and transformations",
        "Furniture, legends, grids, and implementation constants",
        "minimum area `1.0`, maximum area `40.0`",
        "style `dotted`",
        "style `solid`",
        "style `dashed`",
    ):
        assert phrase in audit
    assert "**Final status:** Implemented" in roadmap


def test_user_overlay_boundary_is_currently_documented():
    current = read(CURRENT)
    roadmap = read(ROADMAP)
    implementation = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Milestone 46D.5A",
        "strict partial-user-document boundary",
        "Sequential loads share no mutable",
        "Milestone 46D.5B",
    ):
        assert phrase in current
    for phrase in (
        "Milestone 46D.5A",
        "recursive non-mutating merge",
        "omitted-versus-explicit argument precedence",
    ):
        assert phrase in roadmap
    for phrase in (
        "load_configuration(path=None)",
        "load_configuration_defaults(path=None)",
        "ConfigurationDefaults",
    ):
        assert phrase in implementation
    assert "src/wenu/configuration/translation.py" in source_tree


def test_user_overlay_runtime_precedence_is_currently_documented():
    current = read(CURRENT)
    roadmap = read(ROADMAP)
    implementation = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Milestone 46D.5B",
        "one frozen aggregate",
        "`--config PATH`",
        "before maximal-sphere construction",
    ):
        assert phrase in current
    for phrase in (
        "**Final status:** Implemented",
        "product arguments retain `None` as the omission sentinel",
        "packaged-only behavior is unchanged",
    ):
        assert phrase in roadmap
    for phrase in (
        "load_configuration_defaults(\"my-wenu.toml\")",
        "configuration=configuration",
        "explicitly present on the command line override it",
    ):
        assert phrase in implementation
    for phrase in (
        "Milestone 46D.5B",
        "no active-configuration singleton exists",
    ):
        assert phrase in source_tree


def test_installed_wenu_chart_boundary_is_currently_documented():
    current = read(CURRENT)
    roadmap = read(ROADMAP)
    implementation = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Milestone 46D.6",
        "one `wenu_chart` command",
        "never imports\nexample modules",
    ):
        assert phrase in current
    for phrase in (
        "**Final status:** Implemented",
        "all five chart-family subcommands plus `defaults`",
        "deterministic `--write` output remains Milestone 46D.7",
    ):
        assert phrase in roadmap
    for phrase in (
        "wenu_chart regional --constellations Cen,Cru,Mus",
        "`--observer-location`",
        "does not import or execute example scripts",
    ):
        assert phrase in implementation
    for phrase in (
        "src/wenu/cli/chart.py",
        "`generate_celestial_sphere()`",
        "do not import `example_scripts`",
    ):
        assert phrase in source_tree


def test_editable_configuration_template_is_currently_documented():
    current = read(CURRENT)
    roadmap = read(ROADMAP)
    implementation = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Milestone 46D.7",
        "exact UTF-8 bytes",
        "profile inheritance is deliberately deferred",
    ):
        assert phrase in current
    for phrase in (
        "**Final status:** Implemented",
        "`wenu_chart defaults --write PATH`",
        "overlay per invocation and no inheritance",
    ):
        assert phrase in roadmap
    for phrase in (
        "`dashed`, `dotted`, `dash_dot`, and `none`",
        "deterministically replaced",
        "One invocation accepts one overlay",
    ):
        assert phrase in implementation
    for phrase in (
        "`write_defaults_template()`",
        "exact UTF-8 bytes",
        "does not\nserialize typed translations",
    ):
        assert phrase in source_tree


def test_configuration_schema_v1_freezes_structure_and_validation():
    schema = read(CONFIGURATION_SCHEMA)
    roadmap = read(ROADMAP)

    assert "**Schema version:** `1`" in schema
    ordered_sections = (
        "`observer`",
        "`subjects`",
        "`families`",
        "`detail`",
        "`styles`",
        "`modes`",
        "`grids_references`",
        "`furniture`",
        "`products`",
        "`export`",
    )
    positions = [schema.index(f"### {section}") for section in ordered_sections]
    assert positions == sorted(positions)

    for phrase in (
        "schema_version = 1",
        "color`, `line_width`, and `line_style`",
        "`solid`, `dashed`, `dotted`, `dash_dot`, or `none`",
        "Unknown sections and keys are errors",
        "complete configuration path",
        "invalid colors",
        "contradictory combinations",
        "executable expressions",
        "Python class names",
        "renderer operations",
        "catalogue joins",
        "imports",
        "arbitrary code",
        "styles.atlas.horizon.line_style",
    ):
        assert phrase in schema

    assert "### Milestone 46D.2" in roadmap
    assert "configuration_schema_v1.md" in roadmap
    assert "This milestone adds no parser" in roadmap


def test_configuration_runtime_migration_is_closed_before_user_overlays():
    roadmap = read(ROADMAP)
    architecture = read(CURRENT)

    for phrase in (
        "Milestone 46D.4D",
        "[products.default]",
        "compatibility API",
        "canonical runtime",
        "Explicit values retain precedence",
    ):
        assert phrase in roadmap
        assert phrase in architecture
    assert "**Final status:** Implemented" in roadmap


def test_documented_python_is_syntactically_valid():
    for document in (
        ROOT / "README.md",
        DEVELOPER / "implementation_reference.md",
    ):
        for block in fenced_python(document):
            ast.parse(block, filename=str(document))


def test_documented_canonical_public_imports_execute():
    namespace = {}
    import_block = fenced_python(
        DEVELOPER / "implementation_reference.md"
    )[0]
    exec(import_block, namespace)
    for name in (
        "AllSkyChart",
        "compose_chart",
        "LegendOptions",
        "RegionalChart",
        "FullSkyChart",
        "CircumpolarChart",
        "BinocularChart",
    ):
        assert name in namespace


def test_public_documents_do_not_recommend_obsolete_imports():
    violations = []
    for path in PUBLIC_DOCUMENTS:
        text = read(path)
        for obsolete in OBSOLETE_IMPORTS:
            pattern = re.compile(
                rf"\b(?:from|import)\s+{re.escape(obsolete)}(?=\s|$)"
            )
            if pattern.search(text):
                violations.append(f"{path.relative_to(ROOT)}: {obsolete}")
    assert violations == []


def test_polar_physical_style_checkpoint_is_documented():
    roadmap = read(ARCHIVE / "migration_history/wenu_migration_0.8_to_0.9.md")
    architecture = read(ARCHIVE / "architecture_history/current_architecture_v0.8.md")
    reference = read(DEVELOPER / "implementation_reference.md")
    acceptance = read(ARCHIVE / "acceptance_history/visual_acceptance_48e2.md")

    for phrase in (
        "Milestone 48E.2",
        "PolarPlanisphereStylePalette",
        "render_48e2_polar_preview.py",
    ):
        assert (
            phrase in roadmap
            or phrase in architecture
            or phrase in reference
        )
    assert "polar-planisphere-south.png" in acceptance
    assert "polar-planisphere-north.png" in acceptance
    assert "--projection stereographic" in acceptance


def test_polar_reference_review_corrections_are_documented():
    roadmap = read(ARCHIVE / "migration_history/wenu_migration_0.8_to_0.9.md")
    target = read(ARCHIVE / "architecture_history/target_architecture_v0.9.md")
    acceptance = read(ARCHIVE / "acceptance_history/visual_acceptance_48e3.md")

    for phrase in (
        "Milestone 48E.3",
        "+20/-20-degree overlap",
        "0h/6h/12h/18h meridians",
        "short declination ticks",
        "corrected stereographic handedness",
    ):
        assert phrase in roadmap or phrase in target or phrase in acceptance


def test_current_svg_documents_use_one_editable_text_contract():
    roadmap = " ".join(
        (ARCHIVE / "milestone_history/49f_svg/svg_output_audit_and_plan.md")
        .read_text(encoding="utf-8")
        .split()
    )
    implementation = (DEVELOPER / "implementation_reference.md").read_text(
        encoding="utf-8"
    )
    source_tree = (DEVELOPER / "source_tree.md").read_text(encoding="utf-8")

    for value in (
        "SVG has one public text contract",
        "--format {png,pdf,svg}",
        "PDF is the publication product",
        "SVG is the editable vector product",
    ):
        assert value in roadmap

    assert "support two explicit SVG font policies" not in roadmap
    assert "wenu.output_policy.OutputFormat" in implementation
    assert "wenu.svg_document.annotate_semantic_svg()" in implementation
    assert "src/wenu/output_policy.py" in source_tree
    assert "src/wenu/svg_document.py" in source_tree


def test_readmes_advertise_the_svg_user_contract():
    for filename in ("README.md", "README.es.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "--format svg" in text
        assert "docs/user_guide/svg_output.md" in text


def test_svg_paint_order_record_rejects_semantic_inference():
    record = (
        ARCHIVE / "milestone_history/49f_svg/svg_exact_paint_order_49f4a.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(record.split())

    for value in (
        "What is the object?",
        "When is it drawn?",
        "does not classify the object",
        "must never be inferred to be a star",
        "does not contain or reconstruct astronomical knowledge",
        "Hierarchical grouping remains a later",
    ):
        assert value in normalized


def test_svg_semantic_naming_ledger_records_designer_contract():
    ledger = (
        ARCHIVE / "milestone_history/49f_svg/svg_semantic_naming_ledger_49f5a.md"
    ).read_text(encoding="utf-8")

    for value in (
        "unique among its siblings",
        "does not repeat information",
        "only when a designer can usefully style",
        "Lines-Western",
        "system agnostic",
        "mag-minus-1",
        "count does not change identity",
        "unexpected generic editable Matplotlib objects",
    ):
        assert value in ledger


def test_svg_cross_product_acceptance_records_all_products():
    text = (
        ARCHIVE / "milestone_history/49f_svg/svg_cross_product_acceptance_49f6.md"
    ).read_text(encoding="utf-8")

    for value in (
        "Milestone 49F.6",
        "all-sky",
        "planisphere",
        "regional",
        "circumpolar",
        "binocular",
        "polar page, south",
        "polar page, north",
        "polar pouch",
        "catalog_1636_283",
        "Inkscape 1.4.4",
        "1688 passed in 58.90s",
    ):
        assert value in text


def test_temporal_sequence_contract_separates_physical_and_playback_time():
    contract = (
        ARCHIVE / "milestone_history/49g_temporal/temporal_sequence_contract_49g1.md"
    ).read_text(encoding="utf-8")
    roadmap = (
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).read_text(encoding="utf-8")
    legacy = (
        ARCHIVE / "roadmap_history/polar_delivery_and_astrometry_roadmap.md"
    ).read_text(encoding="utf-8")
    implementation = (
        DEVELOPER / "implementation_reference.md"
    ).read_text(encoding="utf-8")
    source_tree = (
        DEVELOPER / "source_tree.md"
    ).read_text(encoding="utf-8")

    for value in (
        "TemporalTimeline",
        "PlaybackSpec",
        "simulation duration",
        "Playback speed must never be interpreted as physical time",
        "CelestialSphere.draw_chart()",
        "29 passed in 3.42s",
    ):
        assert value in contract

    assert "49G.1 immutable timeline and playback vocabulary" in roadmap
    assert "does not compete" in legacy
    assert "Temporal sequence vocabulary (Milestone 49G.1)" in implementation
    assert "Temporal sequence modules (Milestone 49G.1)" in source_tree


def test_observer_time_sequence_reserves_astrometric_epoch_ownership():
    contract = (
        ARCHIVE / "milestone_history/49g_temporal/observer_time_sequence_49g2.md"
    ).read_text(encoding="utf-8")
    timeline = (
        ARCHIVE / "milestone_history/49g_temporal/temporal_sequence_contract_49g1.md"
    ).read_text(encoding="utf-8")
    roadmap = (
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).read_text(encoding="utf-8")
    implementation = (
        DEVELOPER / "implementation_reference.md"
    ).read_text(encoding="utf-8")
    source_tree = (
        DEVELOPER / "source_tree.md"
    ).read_text(encoding="utf-8")

    for value in (
        "ObserverTimeChartSequenceRequest",
        "generate_observer_time_chart_sequence()",
        "catalogue reference epoch",
        "celestial realization epoch",
        "provider evaluation instant",
        "Gaia DR3 J2016.0 TCB",
        "must not be forced into UTC datetimes",
        "Real-render acceptance",
        "894 × 927",
        "expected six-hour sky",
        "permanent integration test",
        "74 passed in 26.69s",
        "1708 passed in 81.99s",
    ):
        assert value in contract

    assert "Proper motion must not be expressed" in timeline
    assert "49G.2 observer-time" in roadmap
    assert "Observer-time chart sequence (Milestone 49G.2)" in implementation
    assert "Observer-time sequence orchestration" in source_tree



def test_sequence_manifest_documents_safe_restart_and_resume():
    contract = (
        ARCHIVE / "milestone_history/49g_temporal/sequence_manifest_49g3.md"
    ).read_text(encoding="utf-8")
    roadmap = (
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).read_text(encoding="utf-8")
    implementation = (
        DEVELOPER / "implementation_reference.md"
    ).read_text(encoding="utf-8")
    source_tree = (
        DEVELOPER / "source_tree.md"
    ).read_text(encoding="utf-8")

    for value in (
        "ObserverTimeSequenceManifest",
        "SequenceRestartPolicy",
        "restart_policy=\"restart\"",
        "recorded filename, byte count, and SHA-256",
        "incompatible manifest before rendering",
        "real canonical PNG generation",
        "CLI/configuration exposure is implemented downstream in Milestone 49G.4",
        "real restart/resume acceptance complete",
        "selective resume",
        "82 passed in 27.29s",
        "1721 passed in 83.03s",
    ):
        assert value in contract

    assert "49G.3 deterministic manifest" in roadmap
    assert "acceptance complete" in roadmap
    assert "Deterministic sequence manifests (Milestone 49G.3)" in (
        implementation
    )
    assert "Sequence manifest and resume (Milestone 49G.3)" in source_tree


def test_temporal_sequence_cli_documents_shared_translation_and_acceptance():
    contract = (
        ARCHIVE / "milestone_history/49g_temporal/temporal_sequence_cli_49g4.md"
    ).read_text(encoding="utf-8")
    roadmap = (
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).read_text(encoding="utf-8")
    implementation = (
        DEVELOPER / "implementation_reference.md"
    ).read_text(encoding="utf-8")
    source_tree = (
        DEVELOPER / "source_tree.md"
    ).read_text(encoding="utf-8")
    schema = (
        DEVELOPER / "configuration_schema_v1.md"
    ).read_text(encoding="utf-8")

    for value in (
        "49G.4",
        "--sequence-stop",
        "--sequence-frames",
        "same immutable `ChartRequest`",
        "complete translated effective configuration",
        "eaf7f6d8cfbfb27376baf85bfb80613a86b67f0f0a40458961386299efac2f68",
        "pixel-identical decoded RGBA",
        "compressed PNG bytes differed",
        "163 passed in 28.30s",
        "1744 passed in 80.10s",
    ):
        assert value in contract

    assert "49G.4 installed CLI" in roadmap
    assert "implemented and accepted" in roadmap
    assert "Temporal sequence CLI and configuration (Milestone 49G.4)" in (
        implementation
    )
    assert "Temporal sequence CLI modules (Milestone 49G.4)" in source_tree

    assert "### `sequence`" in schema
    assert "playback_duration" in schema
