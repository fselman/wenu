"""Current public-documentation and architecture-authority contracts."""

import ast
import html
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs" / "developer"
ARCHIVE = DEVELOPER / "archive"
MINOR_BODY_HISTORY = ARCHIVE / "milestone_history" / "50a_minor_bodies"
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
SATELLITE_PROGRAM_LOG = DEVELOPER / "satellite_program_log.md"
PUBLIC_INTERFACE_AUDIT = DEVELOPER / "archive/audits/public_interface_audit_v0.9.5.md"
SCENE_DEPENDENCY_AUDIT = (
    DEVELOPER / "archive/milestone_history/49d_scene/celestial_scene_dependency_audit_49d1.md"
)
LAYER_REALIZATION_CONTRACT = (
    DEVELOPER / "archive/milestone_history/49d_scene/layer_realization_context_49d2.md"
)
EPHEMERIS_PROVIDER_CONTRACT = (
    DEVELOPER / "archive/milestone_history/49e_ephemeris/ephemeris_provider_contract_49e1.md"
)
EPHEMERIS_RUNTIME_CONTRACT = (
    DEVELOPER / "archive/milestone_history/49e_ephemeris/ephemeris_runtime_contracts_49e2.md"
)
SKYFIELD_EPHEMERIS_CONTRACT = (
    DEVELOPER / "archive/milestone_history/49e_ephemeris/skyfield_ephemeris_adapter_49e3.md"
)
SOLAR_SYSTEM_DIRECTION_CONTRACT = (
    DEVELOPER / "archive/milestone_history/49e_ephemeris/solar_system_direction_realizer_49e4.md"
)
ASTROMETRIC_DIRECTION_CONTRACT = (
    DEVELOPER / "archive/milestone_history/49e_ephemeris/astrometric_direction_runtime_49e5.md"
)
APPARENT_DIRECTION_CONTRACT = (
    DEVELOPER / "archive/milestone_history/49e_ephemeris/apparent_direction_runtime_49e6.md"
)
VENUS_VERTICAL_SLICE_AUDIT = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/venus_vertical_slice_audit_49i1.md"
)
ORDINARY_REALIZATION_CONTEXT = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/ordinary_realization_context_49i1a.md"
)
VENUS_LAYER_CONTRACT = DEVELOPER / "archive/milestone_history/49i_solar_system/venus_layer_49i1b.md"
MOON_SHARED_PIPELINE_AUDIT = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/moon_shared_body_pipeline_audit_49i2.md"
)
MOON_DIRECTION_VALIDATION = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/moon_direction_validation_49i2a.md"
)
SHARED_SOLAR_SYSTEM_POINT_LAYER = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/shared_solar_system_point_layer_49i2b.md"
)
MOON_LAYER = DEVELOPER / "archive/milestone_history/49i_solar_system/moon_layer_49i2c.md"
SOLAR_SYSTEM_TRACK_AUDIT = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/solar_system_track_audit_49i2d.md"
)
SOLAR_SYSTEM_TRACK_CURVE = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/solar_system_track_curve_49i2d1.md"
)
DRAWABLE_VENUS_TRACK = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/drawable_venus_track_49i2d2.md"
)
PHYSICAL_APPARENT_DISK_AUDIT = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/physical_apparent_disk_audit_49i3a.md"
)
VENUS_PHYSICAL_APPEARANCE = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/venus_physical_appearance_49i3b.md"
)
RESOLVED_VENUS_DISK_AUDIT = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/resolved_venus_disk_audit_49i3c.md"
)
VENUS_DISK_SPHERICAL_GEOMETRY = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/venus_disk_spherical_geometry_49i3c1.md"
)
DRAWABLE_VENUS_DISK = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/drawable_venus_disk_49i3c2.md"
)
DRAWABLE_OBSERVED_VENUS_SEQUENCE = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/drawable_observed_venus_sequence_49i3c31b.md"
)
FROZEN_EARTH_VENUS_SEQUENCE = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/frozen_earth_venus_sequence_49i3c32a.md"
)
DRAWABLE_FROZEN_EARTH_VENUS_SEQUENCE = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/drawable_frozen_earth_venus_sequence_49i3c32b.md"
)
MERCURY_DISK_SEQUENCE_AUDIT = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/mercury_disk_sequence_audit_49i3c33.md"
)
MOVING_BODY_ARCHITECTURE = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/moving_body_architecture_49i3c33a.md"
)
DRAWABLE_FROZEN_EARTH_MERCURY_SEQUENCE = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/drawable_frozen_earth_mercury_sequence_49i3c33c.md"
)
APPARENT_MAJOR_PLANETS = DEVELOPER / "archive/milestone_history/49i_solar_system/apparent_major_planets_49i3d1.md"
RESOLVED_MOON_PLAN = DEVELOPER / "archive/milestone_history/49i_solar_system/resolved_moon_plan_49i3e.md"
RESOLVED_MOON_AUDIT = DEVELOPER / "archive/milestone_history/49i_solar_system/resolved_moon_audit_49i3e0.md"
LUNAR_PHYSICAL_APPEARANCE = (
    DEVELOPER / "archive/milestone_history/49i_solar_system/lunar_physical_appearance_49i3e1.md"
)
DRAWABLE_RESOLVED_MOON = DEVELOPER / "archive/milestone_history/49i_solar_system/drawable_resolved_moon_49i3e2.md"
OBSERVED_MOON_SEQUENCE = DEVELOPER / "archive/milestone_history/49i_solar_system/observed_moon_disk_sequence_49i3e3.md"
PERFORMANCE_CLOSURE_AUDIT = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/performance_and_closure_audit_49j0.md"
)
TEST_PERFORMANCE_PROGRAM = (
    ARCHIVE / "roadmap_history" / "test_performance_and_future_program_49j_50.md"
)
MINOR_BODY_PROVIDER_AUDIT = (
    DEVELOPER
    / "archive/milestone_history/50a_minor_bodies/minor_body_scientific_provider_audit_50a0.md"
)
MINOR_BODY_STATE_PROVIDER = (
    DEVELOPER
    / "archive/milestone_history/50a_minor_bodies/minor_body_state_provider_50a1.md"
)
ASTEROID_NUMERICAL_VALIDATION = (
    DEVELOPER
    / "archive/milestone_history/50a_minor_bodies/asteroid_numerical_validation_50a2.md"
)
FIRST_DRAWABLE_ASTEROID_AUDIT = (
    DEVELOPER
    / "archive/milestone_history/50a_minor_bodies"
    / "first_drawable_asteroid_audit_50a3a.md"
)
DRAWABLE_CERES = (
    DEVELOPER
    / "archive/milestone_history/50a_minor_bodies/drawable_ceres_50a3b.md"
)
TEST_PRACTICE_AUDIT = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/test_architecture_and_accepted_practice_audit_49j1.md"
)
TEST_PRACTICE_DECISIONS = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/test_practice_decisions_49j2.md"
)
TEST_ENTRY_ADMISSION = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/test_entry_and_admission_49j3a.md"
)
MARKER_TRUTHFULNESS = (
    DEVELOPER / "archive/milestone_history/49j_performance/marker_truthfulness_49j3b.md"
)
REPOSITORY_SOURCE_INDEX = (
    DEVELOPER / "archive/milestone_history/49j_performance/repository_source_index_49j3c.md"
)
IMMUTABLE_CATALOGUE_FIXTURE = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/immutable_catalogue_fixture_49j3d.md"
)
COLD_BUILDER_KERNEL_ORACLES = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/cold_builder_kernel_oracles_49j3e.md"
)
CALENDAR_LAYOUT_COST = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/calendar_layout_cost_49j3f.md"
)
OBSERVER_TIME_SEQUENCE_ORACLE = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/observer_time_sequence_oracle_49j3g.md"
)
TEST_SUITE_OPTIMIZATION_CLOSURE = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/test_suite_optimization_closure_49j3h.md"
)
COLD_FRAME_PERFORMANCE_BASELINE = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/cold_frame_performance_baseline_49j4.md"
)
LOADED_SPHERE_REUSE = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/loaded_sphere_reuse_49j5a.md"
)
FIXED_SKY_REUSE_EQUIVALENCE = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/fixed_sky_reuse_equivalence_49j5b.md"
)
PERFORMANCE_CLOSURE = (
    DEVELOPER
    / "archive/milestone_history/49j_performance/performance_closure_49j6.md"
)
INSTRUCTIONS = DEVELOPER / "assistant_instructions.md"
CONFIGURATION_AUDIT = ARCHIVE / "audits/configuration_default_audit.md"
CONFIGURATION_SCHEMA = DEVELOPER / "configuration_schema_v2.md"
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
    assert "Guide version:** `0.9.5.20260902.54`" in guide
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
    assert "Guide version:** `0.9.5.20260902.54`" in guide
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
    assert "Guide version:** `0.9.5.20260902.54`" in guide
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
    assert "Guide version:** `0.9.5.20260902.54`" in guide
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
    assert "Guide version:** `0.9.5.20260902.54`" in guide
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
    assert "Guide version:** `0.9.5.20260902.54`" in guide
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
    assert "Guide version:** `0.9.5.20260902.54`" in guide
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
    assert "Guide version:** `0.9.5.20260902.54`" in guide
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
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "`--moon` remains 49I.2C" in guide
    assert "Fernando scientifically and architecturally accepted 49I.2B" in guide


def test_49i2c_installs_one_symbolic_moon_without_physical_disk_claims():
    contract = " ".join(read(MOON_LAYER).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**Implementation baseline:** `0416474`",
        "`MoonLayer` is a thin specialization",
        "`SkyContentSelection.solar_system_objects`",
        "`--planet venus` selects Venus",
        "`--moon` selects the Moon",
        "sky/solar_system/natural_satellites/moon",
        "89 direct Moon, shared-point, Venus, CLI",
        "219 request, detail, style, realization",
        "1,887 routine tests with 30 deselected",
        "all 1,917 tests in 92.36 seconds",
        "54 current-documentation tests in 1.91 seconds",
        "2026-08-29 20:00 local time at UTC-4",
        "relative position against nearby Pisces stars corresponded closely",
        "Fernando accepted the shared internal Solar-System selection",
        "does not authorize physical lunar-disk or phase geometry",
        "adds no physical lunar disk",
        "remain 49I.3",
    ):
        assert phrase in contract

    assert "Milestone 49I.2C — First drawable Moon point" in roadmap
    assert (
        "Fernando scientifically, architecturally, and visually accepted"
        in roadmap
    )
    assert "The accepted 49I.2C implementation installs" in architecture
    assert "First drawable Moon point (Milestone 49I.2C)" in implementation
    assert "src/wenu/sky/moon.py" in source_tree
    assert "13.2.17 49I.2C first drawable Moon point" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "Physical disk and phase remain 49I.3" in guide
    assert (
        "Fernando scientifically, architecturally, and visually accepted"
        in guide
    )


def test_49i2d_audits_fixed_frame_vectorized_solar_system_tracks():
    contract = " ".join(read(SOLAR_SYSTEM_TRACK_AUDIT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `d1971f5`",
        "--planet-track venus",
        "--track-start 2026-08-30T00:00:00Z",
        "--track-sample-step 1h",
        "--track-tick-step 7d",
        "--track-tick-count 4",
        "Sample instants",
        "Chart-frame instant",
        "one fixed observer-local product frame",
        "one ordinary `SphericalCurves` value before projection",
        "visible perpendicular ticks are projected annotations",
        "regional and binocular charts",
        "Planisphere and all-sky products remain outside",
        "49I.3 physical apparent-disk contract",
        "add runtime source",
    ):
        assert phrase in contract

    assert "Milestone 49I.2D — Solar-System trajectory contract" in roadmap
    assert "The accepted 49I.2D audit places" in architecture
    assert (
        "Accepted Solar-System track contract (Milestone 49I.2D)"
        in implementation
    )
    assert "solar_system_track_audit_49i2d.md" in source_tree
    assert "13.2.18 49I.2D Solar-System trajectories" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "per-sample time provenance" in instructions
    assert "Scientifically and architecturally accepted" in contract
    assert "55 current-documentation tests in 3.02 seconds" in contract
    assert "1,889 routine tests with 30 deselected in 28.02 seconds" in contract
    assert "all 1,919 tests in 90.48 seconds" in contract
    assert "49I.2D scientific and architectural acceptance" in guide
    assert "Runtime slices remain separately authorized" in roadmap


def test_49i2d1_implements_scientific_curve_without_drawing():
    contract = " ".join(read(SOLAR_SYSTEM_TRACK_CURVE).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `ea03400`",
        "`SolarSystemTrackRequest`",
        "`SolarSystemTrackResult`",
        "`SolarSystemTrackRealizer.curve()`",
        "Regular samples include both endpoints",
        "Exact tick offsets",
        "observer barycentric state",
        "one open `SphericalCurves`",
        "`CoordinateService.transform()` is then invoked exactly once",
        "complete `ApparentDirection` per vertex",
        "`tests/test_solar_system_tracks.py`",
        "`tools/validate_49i2d1_venus_track.py`",
        "`1e-7` degree per ICRS component",
        "adds no:",
        "public `--planet-track`",
    ):
        assert phrase in contract

    assert "Milestone 49I.2D.1 — Scientific Solar-System track curve" in roadmap
    assert "The accepted 49I.2D.1 implementation adds" in architecture
    assert (
        "Scientific Solar-System track curve (Milestone 49I.2D.1)"
        in implementation
    )
    assert "src/wenu/sky/solar_system_tracks.py" in source_tree
    assert "13.2.19 49I.2D.1 scientific track curve" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "solar_system_track_curve_49i2d1.md" in instructions
    assert "Scientifically and architecturally accepted" in contract
    assert "`4.293e-10` degree in right ascension" in contract
    assert "`8.471e-11` degree in declination" in contract
    assert "40 focused scientific tests in 2.12 seconds" in contract
    assert "56 current-documentation tests in 1.86 seconds" in contract
    assert "1,899 routine tests with 30 deselected in 26.92 seconds" in contract
    assert "all 1,929 tests in 89.19 seconds" in contract
    assert "49I.2D.1 scientific and architectural acceptance" in guide
    assert "49I.2D.2 remains separately authorized" in roadmap


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

    assert "**Guide version:** `0.9.5.20260902.54`" in guide
    assert "**Last updated:** `2026-09-02T23:59:30Z`" in guide
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
            "**Guide version:** `0.9.5.20260902.54`",
            "**Last updated:** `2026-09-02T23:59:30Z`",
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
        "--center-on constellation:Cen,Cru,Mus",
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


def test_configuration_schema_v2_freezes_structure_and_validation():
    schema = read(CONFIGURATION_SCHEMA)
    roadmap = read(ROADMAP)

    assert "**Schema version:** `2`" in schema
    ordered_sections = (
        "`data`",
        "`observer`",
        "`constellations`",
        "`centers`",
        "`masks`",
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
        "schema_version = 2",
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
        DEVELOPER / "configuration_schema_v2.md"
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



def test_49i2d2_records_accepted_drawable_venus_track():
    contract = " ".join(read(DRAWABLE_VENUS_TRACK).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Milestone 49I.2D.2 — Drawable Venus track",
        "--planet-track venus",
        "--track-tick-labels",
        "exactly two possible anchors",
        "two complete passes",
        "amber orange",
        "#FFB000",
        "sky/solar_system/planets/venus/track",
        "sixteen-week stress test",
        "127 focused track, style, request, and command tests",
        "1,924 routine tests with 30 deselected",
        "all 1,955 tests",
    ):
        assert phrase in contract

    assert "Milestone 49I.2D.2 — Drawable Venus track" in roadmap
    assert "Accepted drawable Solar-System trajectory" in architecture
    assert "Accepted drawable Venus track" in implementation
    assert "solar_system_track_annotations.py" in source_tree
    assert "13.2.20 49I.2D.2 drawable Venus track" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "drawable_venus_track_49i2d2.md" in instructions
    assert "Scientifically, architecturally, and visually accepted" in contract


def test_49i3a_audits_symbolic_and_resolved_solar_system_appearance():
    contract = " ".join(read(PHYSICAL_APPARENT_DISK_AUDIT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `449a3c9`",
        "**Symbolic representation.**",
        "**Resolved representation.**",
        "physical angular diameter",
        "illuminated fraction",
        "bright-limb position angle",
        "body-axis orientation",
        "apparent magnitude",
        "display magnification",
        "object-specific and opt-in",
        "factor `1` means physical angular scale",
        "regional and binocular charts",
        "Planisphere and all-sky products retain symbolic representation",
        "not merely a large scatter marker",
        "49I.3B — Venus physical-appearance state",
        "49I.3C — First resolved Venus disk",
        "49I.3D — Symbolic photometry and planet glyphs",
        "49I.3E — Moon physical-appearance state",
        "49I.3F — First resolved Moon disk",
        "changes no runtime type, public command, style, geometry, chart, or output",
    ):
        assert phrase in contract

    assert "Milestone 49I.3A — Physical apparent-disk contract audit" in roadmap
    assert "Deferred physical Solar-System appearance" in architecture
    assert "Accepted physical apparent-disk boundary" in implementation
    assert "Milestone 49I.3A audit ownership" in source_tree
    assert "13.2.21 49I.3A physical apparent-disk audit" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "physical_apparent_disk_audit_49i3a.md" in instructions
    assert "Scientifically and architecturally accepted" in contract
    assert "Initial acceptance verification passed all 58" in contract
    assert "current-documentation tests passed in 1.95 seconds" in contract
    assert "1,926 tests with 30 deselected in 28.95 seconds" in contract
    assert "all 1,956 tests in 91.38 seconds" in contract
    assert "does not pre-accept the future" in contract


def test_49i3b_records_accepted_venus_physical_appearance_state():
    contract = " ".join(read(VENUS_PHYSICAL_APPEARANCE).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `217abbe`",
        "`SolarSystemApparentDisk`",
        "`SolarSystemAppearanceRealizer`",
        "`6051.8 km`",
        "Sun–target–observer",
        "`29.287846514361 arcsec`",
        "`101.448595072558 deg`",
        "`0.400755659841`",
        "`295.354967208388 deg`",
        "`185.355190511946 deg`",
        "`1e-8 arcsec`",
        "`1e-9 deg`",
        "`1e-11`",
        "all 9 deterministic appearance tests in 1.38 seconds",
        "116 focused architectural tests in 4.73 seconds",
        "1,936 routine tests with 30 deselected in 27.32 seconds",
        "all 1,966 tests in 89.97 seconds",
        "adds no disk geometry, chart layer, request option, style",
        "49I.3C remains responsible",
    ):
        assert phrase in contract

    assert "Milestone 49I.3B — Venus physical-appearance state" in roadmap
    assert "Accepted Venus physical-appearance state" in architecture
    assert "Venus physical-appearance state" in implementation
    assert "Milestone 49I.3B ownership" in source_tree
    assert "13.2.22 49I.3B Venus physical-appearance state" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "venus_physical_appearance_49i3b.md" in instructions
    assert "Scientifically and architecturally accepted" in contract


def test_49i3c_audits_resolved_venus_disk_geometry():
    contract = " ".join(read(RESOLVED_VENUS_DISK_AUDIT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `a9d8342`",
        "Scientifically and architecturally accepted",
        "illuminated-face `SphericalPolygons` layer",
        "limb `SphericalCurves` layer",
        "terminator `SphericalCurves` layer",
        "`SphericalGrid` is deliberately curve-only",
        "positive finite, object-specific display magnification",
        "scales every projected vertex around the separately projected",
        "factor of `1` means physical projected scale",
        "Magnification alone must not silently enable a disk",
        "Pre-projection sampling must be fine enough",
        "regional and binocular",
        "planisphere and all-sky",
        "several requested instants in one chart",
        "one fixed chart product frame",
        "49I.3C.1 — Resolved Venus spherical geometry",
        "49I.3C.2 — First drawable resolved Venus disk",
        "49I.3C.3 — Multi-epoch resolved Venus disks",
        "scatter-marker approximation",
        "all 60 current-documentation tests in 1.80 seconds",
        "all 60 documentation tests passed in 2.81 seconds",
        "1,937 routine tests passed with 30 deselected in 28.40 seconds",
        "all 1,967 tests passed in 89.14 seconds",
        "Runtime geometry, command vocabulary",
    ):
        assert phrase in contract

    assert "Milestone 49I.3C — Resolved Venus disk audit" in roadmap
    assert "Accepted resolved Venus disk boundary" in architecture
    assert "Accepted resolved Venus disk boundary" in implementation
    assert "Milestone 49I.3C audit ownership" in source_tree
    assert "13.2.23 49I.3C resolved Venus disk audit" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "resolved_venus_disk_audit_49i3c.md" in instructions
    assert "Fernando accepted this boundary on 2026-08-31" in contract


def test_49i3c1_records_accepted_venus_spherical_disk_geometry():
    contract = " ".join(read(VENUS_DISK_SPHERICAL_GEOMETRY).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `a308ba2`",
        "Scientifically and architecturally accepted",
        "`SolarSystemDiskGeometry`",
        "`SolarSystemDiskGeometryRealizer.geometry()`",
        "`DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES = 720`",
        "orthographic spherical phase with radial angular-offset mapping",
        "one-point `SphericalPoints` centre",
        "one-curve closed `SphericalCurves` limb",
        "one-curve open `SphericalCurves` terminator",
        "one-polygon `SphericalPolygons` illuminated face",
        "`14.643923257181 arcsec`",
        "`9.799e-11 arcsec`",
        "`0.000e+00 arcsec`",
        "`-5.087e-06`",
        "`-1.495e-10 deg`",
        "`1e-7 arcsec`",
        "`2e-5`",
        "`1e-9 deg`",
        "All 29 appearance and disk-geometry tests passed in 1.94 seconds",
        "All 54 focused appearance, coordinate-service, and dependency-boundary tests passed in 4.80 seconds",
        "all 61 current-documentation tests in 2.35 seconds",
        "1,958 routine tests with 30 deselected in 27.07 seconds",
        "all 1,988 tests in 89.21 seconds",
        "adds no sky layer, chart request, display magnification",
        "49I.3C.2",
    ):
        assert phrase in contract

    assert "Milestone 49I.3C.1 — Venus spherical disk geometry" in roadmap
    assert "output-neutral physical centre" in architecture
    assert "Venus spherical disk geometry" in implementation
    assert "Milestone 49I.3C.1 ownership" in source_tree
    assert "13.2.24 49I.3C.1 Venus spherical disk geometry" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "venus_disk_spherical_geometry_49i3c1.md" in instructions
    assert "Fernando accepted the geometry model" in contract


def test_49i3c2_records_accepted_drawable_venus_disk():
    contract = " ".join(read(DRAWABLE_VENUS_DISK).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `da0e332`",
        "Scientifically, architecturally, and visually accepted",
        "`--planet-appearance venus=resolved`",
        "`--planet-disk-magnification venus=FACTOR`",
        "Factor `1` means physical angular scale",
        "Magnification alone cannot enable a resolved disk",
        "regional and binocular",
        "Planisphere and all-sky products retain symbolic representation",
        "`29.287846514361 arcsec`",
        "`0.400755659841`",
        "1.62710258413117",
        "600-dpi Virgo rendering",
        "171 closure-focused request, execution, style, semantic, and dependency tests passed in 5.75 seconds",
        "1,970 routine tests passed with 30 deselected in 28.32 seconds",
        "All 2,000 tests passed in 90.30 seconds",
        "49I.3C.3",
    ):
        assert phrase in contract

    assert "Milestone 49I.3C.2 — First drawable resolved Venus disk" in roadmap
    assert "Drawable resolved Venus disk" in architecture
    assert "Drawable resolved Venus disk (Milestone 49I.3C.2)" in implementation
    assert "Milestone 49I.3C.2 ownership" in source_tree
    assert "13.2.25 49I.3C.2 first drawable resolved Venus disk" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "drawable_venus_disk_49i3c2.md" in instructions


def test_49i3c3_audits_two_mode_planet_disk_sequences():
    contract = " ".join(
        read(
            DEVELOPER / "archive/milestone_history/49i_solar_system/planet_disk_sequence_audit_49i3c3.md"
        ).split()
    )
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `6745403`",
        "Scientifically and architecturally accepted",
        "observed sequence",
        "frozen-Earth ecliptic sequence",
        "n_steps = 8",
        "nine disk samples",
        "There is no minor step",
        "full physical distance with declared origin and unit",
        "future 3D Solar-System visualizer",
        "One common magnification",
        "frozen-observer geometric direction",
        "central six-point Sun",
        "sky/solar_system/star/sun",
        "--planet-disk-sequence venus",
        "--disk-sequence-model observed|frozen-earth-ecliptic",
        "49I.3C.3.1 — Observed multi-epoch Venus disks",
        "49I.3C.3.2 — Frozen-Earth ecliptic Venus sequence",
        "49I.3C.3.3 — Mercury generalization and validation",
        "changes no runtime type, public command, geometry, style, chart",
    ):
        assert phrase in contract

    assert "Milestone 49I.3C.3 — Multi-epoch resolved planet-disk audit" in roadmap
    assert "Accepted multi-epoch resolved planet-disk boundary" in architecture
    assert "Accepted multi-epoch planet-disk sequence" in implementation
    assert "Milestone 49I.3C.3 audit ownership" in source_tree
    assert "13.2.26 49I.3C.3 multi-epoch resolved planet-disk audit" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "planet_disk_sequence_audit_49i3c3.md" in instructions

    assert "Initial acceptance verification passed all 63" in contract
    assert "current-documentation tests in 1.88 seconds" in contract
    assert "1,971 routine tests with 30 deselected in 27.08 seconds" in contract
    assert "all 2,001 tests in 85.97 seconds" in contract


def test_49i3c31a_records_observed_venus_disk_sequence():
    contract = " ".join(
        read(
            DEVELOPER / "archive/milestone_history/49i_solar_system/observed_venus_disk_sequence_49i3c31a.md"
        ).split()
    )
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `8a6cb0f`",
        "Scientifically and architecturally accepted",
        "`ObservedSolarSystemDiskSequenceRequest`",
        "`ObservedSolarSystemDiskSequenceRealizer.sequence()`",
        "`ObservedSolarSystemDiskSequence`",
        "`n_steps = 8` produces nine exact sample instants",
        "origin `observer` and unit `au`",
        "future 3D Solar-System visualizer",
        "`4.615e-10 deg`",
        "`1.946e-10 deg`",
        "`3.128e-12 AU`",
        "`3.795e-10 arcsec`",
        "`7.096e-10 deg`",
        "`4.823e-12`",
        "`4.301e-09 deg`",
        "all 51 focused tests passed in 1.89 seconds",
        "All 91 focused sequence",
        "49I.3C.3.1B",
        "adds no public command",
    ):
        assert phrase in contract

    assert "Milestone 49I.3C.3.1A" in roadmap
    assert "Accepted output-neutral observed Venus disk sequence" in architecture
    assert "Observed Venus disk sequence (Milestone 49I.3C.3.1A)" in implementation
    assert "Milestone 49I.3C.3.1A ownership" in source_tree
    assert "13.2.27 49I.3C.3.1A observed Venus disk sequence" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "observed_venus_disk_sequence_49i3c31a.md" in instructions
    assert "all 64 current-documentation tests in 2.23 seconds" in contract
    assert "1,985 tests with 30 deselected in 25.46 seconds" in contract
    assert "all 2,015 tests in 84.38 seconds" in contract


def test_49i3c31b_records_drawable_observed_venus_sequence():
    contract = " ".join(read(DRAWABLE_OBSERVED_VENUS_SEQUENCE).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `7fd2a6a`",
        "Scientifically, architecturally, visually, and operationally accepted",
        "`ObservedVenusDiskSequenceRealization`",
        "`MagnifyProjectedDiskSequence`",
        "one fixed product frame",
        "observer/AU distances",
        "`--planet-disk-sequence venus`",
        "--disk-sequence-model observed",
        "`--disk-sequence-labels`",
        "`--planet-disk-magnification venus=FACTOR`",
        "`--no-equatorial-grid`",
        "`--grid-references ecliptic`",
        "All 211 focused tests passed in 5.74 seconds",
        "1,988 tests with 30 deselected in 25.91 seconds",
        "all 2,018 tests in 85.27 seconds",
        "Frozen-Earth ecliptic mode",
        "Mercury",
    ):
        assert phrase in contract

    assert "Milestone 49I.3C.3.1B" in roadmap
    assert "Drawable observed Venus disk sequence" in architecture
    assert "Drawable observed Venus disk sequence (Milestone 49I.3C.3.1B)" in implementation
    assert "Milestone 49I.3C.3.1B ownership" in source_tree
    assert "13.2.28 49I.3C.3.1B drawable observed Venus sequence" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "drawable_observed_venus_sequence_49i3c31b.md" in instructions


def test_49i3c32a_records_frozen_earth_venus_sequence_state():
    contract = " ".join(read(FROZEN_EARTH_VENUS_SEQUENCE).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `447e701`",
        "Scientifically and architecturally accepted",
        "`FrozenEarthDiskSequenceRequest`",
        "`FrozenEarthDiskSequenceRealizer.sequence()`",
        "`FrozenEarthGeometricDisk`",
        "origin `frozen-earth` and unit `au`",
        "fixed J2000 mean-ecliptic axes",
        "future 3D Solar-System visualizer",
        "not topocentric, astrometric, apparent",
        "`4.337e-12 AU`",
        "`1.968e-10 deg`",
        "`2.064e-11 deg`",
        "`1.274e-12 AU`",
        "`1.627e-10 deg`",
        "All 63 focused sequence",
        "1,997 tests with 30 deselected in 26.69 seconds",
        "all 2,027 tests in 84.73 seconds",
        "49I.3C.3.2B",
        "49I.3C.3.3",
    ):
        assert phrase in contract

    assert "Milestone 49I.3C.3.2A" in roadmap
    assert "Accepted output-neutral frozen-Earth Venus sequence" in architecture
    assert "Frozen-Earth Venus sequence state (Milestone 49I.3C.3.2A)" in implementation
    assert "Milestone 49I.3C.3.2A ownership" in source_tree
    assert "13.2.29 49I.3C.3.2A frozen-Earth Venus state" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "frozen_earth_venus_sequence_49i3c32a.md" in instructions
    assert "All 66 current-documentation tests passed in 2.07 seconds" in contract


def test_49i3c32b_records_drawable_frozen_earth_venus_sequence():
    contract = " ".join(
        read(DRAWABLE_FROZEN_EARTH_VENUS_SEQUENCE).split()
    )
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Implementation baseline:** `c30785c`",
        "Scientifically, architecturally, visually, and operationally accepted",
        "`FrozenEarthVenusDiskSequenceRealization`",
        "fixed J2000 mean-ecliptic axes",
        "product-frame latitude zero",
        "neither reference passes through observer-dependent AltAz geometry",
        "Secuencia de Venus desde una Tierra fija",
        "31 independently realized disks",
        "all 2,037 tests in 84.41 seconds",
        "All 67 current-documentation tests passed",
        "49I.3C.3.3",
    ):
        assert phrase in contract

    assert "Milestone 49I.3C.3.2B" in roadmap
    assert "Drawable frozen-Earth Venus disk sequence" in architecture
    assert (
        "Drawable frozen-Earth Venus sequence (Milestone 49I.3C.3.2B)"
        in implementation
    )
    assert "Milestone 49I.3C.3.2B ownership" in source_tree
    assert (
        "13.2.30 49I.3C.3.2B drawable frozen-Earth Venus sequence"
        in guide
    )
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert (
        "drawable_frozen_earth_venus_sequence_49i3c32b.md"
        in instructions
    )


def test_49i3c33_audits_mercury_generalization_and_validation():
    audit = " ".join(read(MERCURY_DISK_SEQUENCE_AUDIT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**As-is baseline:** `3a713fb`",
        "Scientifically and architecturally accepted",
        "`2439.4 km`",
        "equatorial radius `2440.53 km`",
        "NAIF body code `199`",
        "Mercury barycentre code `1`",
        "actual `provider_target_id`",
            "49I.3C.3.3B — Output-neutral Mercury state",
            "49I.3C.3.3C — Drawable frozen-Earth Mercury sequence",
        "`--planet-disk-sequence mercury`",
        "sky/solar_system/planets/mercury/frozen_earth_sequence",
        "does not authorize observed/topocentric Mercury sequences",
        "changes no runtime type",
        "all 68 current-documentation tests",
        "Fernando scientifically and architecturally accepted",
    ):
        assert phrase in audit

    assert "Milestone 49I.3C.3.3" in roadmap
    assert "Mercury generalization audit boundary" in architecture
    assert "Milestone 49I.3C.3.3 audit ownership" in source_tree
    assert "13.2.31 49I.3C.3.3 Mercury generalization audit" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "mercury_disk_sequence_audit_49i3c33.md" in instructions


def test_49i3c33a_records_descriptor_driven_moving_body_foundation():
    contract = " ".join(read(MOVING_BODY_ARCHITECTURE).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    for phrase in (
        "SolarSystemBodyDescriptor",
        "A planet does not contain its satellites",
        "Capabilities, not classification",
        "synthetic minor body",
        "Mercury remains unregistered",
        "does not add Mercury",
        "all 2,045 tests in 86.49 seconds",
        "Scientifically, architecturally, and visually accepted",
        "three Venus compatibility renders",
    ):
        assert phrase in contract
    assert "13.2.32 49I.3C.3.3A moving-body foundation" in guide
    assert "Milestone 49I.3C.3.3A moving-body ownership" in source_tree
    assert "moving_body_architecture_49i3c33a.md" in instructions


def test_49i3c33c_proposes_descriptor_driven_drawable_mercury():
    contract = " ".join(
        read(DRAWABLE_FROZEN_EARTH_MERCURY_SEQUENCE).split()
    )
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    for phrase in (
        "Scientifically, architecturally, visually, and operationally accepted",
        "adds no Mercury-specific layer, factory, projection, preparation",
        "`frozen_earth_disk_sequence` capability",
        "`--disk-sequence-model observed`",
        "`Mercury` and `Mercurio`",
        "sky/solar_system/planets/mercury/frozen_earth_sequence",
        "sky/solar_system/star/sun",
        "`--planet-disk-sequence mercury`",
        "`--disk-sequence-step 2d`",
        "`--disk-sequence-n-steps 44`",
        "PNG/PDF/SVG parity",
        "all 2,052 tests in 89.90 seconds",
        "same frozen-state realizer, disk-geometry realizer",
    ):
        assert phrase in contract
    assert "Milestone 49I.3C.3.3C drawable frozen-Earth Mercury" in source_tree
    assert "Milestone 49I.3C.3.3C — Drawable frozen-Earth Mercury" in roadmap
    assert "drawable_frozen_earth_mercury_sequence_49i3c33c.md" in instructions


def test_49i3d1_proposes_shared_apparent_major_planets():
    contract = " ".join(read(APPARENT_MAJOR_PLANETS).split())
    user_guide = " ".join(
        read(ROOT / "docs/user_guide/configuration.md").split()
    )
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    for phrase in (
        "DE440 validation passed; compact-glyph visual acceptance pending",
        "Mercury, Venus, Mars, Jupiter, Saturn, Uranus, and Neptune",
        "Earth is not a drawable apparent target",
        "same apparent symbolic-point machinery",
        "barycentre targets: Mars `4`, Jupiter `5`, Saturn `6`",
        "physical planet IDs `499`, `599`, `699`, `799`, and `899`",
        "`solar_system_objects` selection",
        "sky/solar_system/planets/<planet>",
        "`1e-7 deg` component tolerance",
        "`--planet mercury,venus,mars,jupiter,saturn,uranus,neptune`",
        "conventional astronomical symbol",
        "accepted Venus cream `#FFE6A3`",
        "corresponding `planisphere` render",
        "only `ol1` produces the unnatural broad envelope",
        "replace only explicitly supplied fields",
        "`--mw-contour OL1[,OL2,...]|all`",
        "single-feature GeoJSON file",
    ):
        assert phrase in contract
    assert "Milestone 49I.3D.1 apparent major planets" in source_tree
    assert "Milestone 49I.3D.1 — Apparent major-planet symbolic points" in roadmap
    assert "apparent_major_planets_49i3d1.md" in instructions
    for phrase in (
        "## Planet symbols",
        "`mercury` | Mercury | ☿",
        "`venus` | Venus | ♀",
        "`mars` | Mars | ♂",
        "`jupiter` | Jupiter | ♃",
        "`saturn` | Saturn | ♄",
        "`uranus` | Uranus | ♅",
        "`neptune` | Neptune | ♆",
        "Earth is the observer's reference body",
    ):
        assert phrase in user_guide


def test_49i3e0_audits_resolved_moon_science_and_generic_reuse():
    audit = " ".join(read(RESOLVED_MOON_AUDIT).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**As-is baseline:** `a8296f5`",
        "**Status:** Scientifically and architecturally accepted",
        "changes no runtime type",
        "No runtime Moon behavior is authorized",
        "`SolarSystemBodyDescriptor`",
        "`natural_satellite`",
        "physical body ID `301`",
        "parent `earth`",
        "equal-volume mean radius `1737.4 km`",
        "quoted uncertainty `0.1 km`",
        "Topocentric parallax is essential",
        "`d = 2 asin(R / Delta)`",
        "`k = (1 + cos(i)) / 2`",
        "zero at celestial north and increases toward apparent east",
        "`t_j = start + j * step`",
        "`n_steps + 1` physical samples",
        "one product coordinate specification and projection fixed at `t_c`",
        "Transforming every spherical vertex",
        "must not transform the scalar `chi_j`",
        "--moon-appearance resolved|symbolic",
        "--moon-disk-sequence",
        "Only `observed` is accepted",
        "`1 <= M_moon <= 1000`",
        "display-only",
        "unrelated to Wenu's `presentation` output mode",
        "same rule applies in atlas and presentation modes",
        "refuses downloads",
        "`1e-7 deg`",
        "sky/solar_system/natural_satellites/moon",
        "all five chart-family enablement",
        "changes no implemented coordinate transformation",
        "frozen-Earth lunar sequences",
        "Fernando scientifically and architecturally accepted this audit on 2026-09-02",
        "acceptance authorizes only 49I.3E.1",
    ):
        assert phrase in audit

    for phrase in (
        "resolved_moon_audit_49i3e0.md",
        "one fixed chart-epoch product frame",
        "do not treat the scalar bright-limb angle as frame-invariant",
        "Do not add runtime Moon behavior under 49I.3E.0",
    ):
        assert phrase in instructions


def test_49i3e1_records_output_neutral_lunar_appearance():
    contract = " ".join(read(LUNAR_PHYSICAL_APPEARANCE).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Scientifically accepted and regression-verified; ready for integration",
        "**Implementation baseline:** `86bbbf1`",
        "NAIF physical body ID `301`",
        "parent key `earth`",
        "English `Moon` and Spanish `Luna`",
        "equal-volume mean radius `1737.4 km`",
        "`spherical_physical_appearance`",
        "`EARTH_BODY`",
        "NAIF body ID `399`",
        "does not yet advertise `resolved_spherical_disk`",
        "No lunar appearance class was added",
        "topocentric retarded observer–Moon distance",
        "has no display magnification",
        "refuses to download a missing kernel",
        "`2e-7 deg`",
        "`5e-12 au`",
        "`5e-6 arcsec`",
        "`1e-9`",
        "revised envelope on 2026-09-02",
        "independent margins rather than fitted",
        "scientifically accepted the 49I.3E.1 numerical validation",
        "`1.338e-07 deg`",
        "`2.994e-06 arcsec`",
        "`0.272607 deg`",
        "All residuals satisfy the accepted envelope",
        "73 documentation tests in `2.75 s`",
        "124 focused tests in `8.36 s`",
        "all 2,081 tests in `91.18 s`",
        "nonzero geocentric/topocentric parallax",
        "does not add disk geometry",
    ):
        assert phrase in contract

    assert "Output-neutral lunar physical appearance" in architecture
    assert "Milestone 49I.3E.1 — Output-neutral lunar" in roadmap
    assert "Lunar physical-appearance state (Milestone 49I.3E.1)" in implementation
    assert "Milestone 49I.3E.1 lunar appearance ownership" in source_tree
    assert "13.2.33 49I.3E.1 lunar physical appearance" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "lunar_physical_appearance_49i3e1.md" in instructions


def test_49i3e2_records_pending_drawable_resolved_moon_contract():
    contract = " ".join(read(DRAWABLE_RESOLVED_MOON).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Scientifically, architecturally, visually, operationally, and regression accepted",
        "Supplying `--moon` now requests one resolved physical Moon by default",
        "`--moon-appearance symbolic` preserves the earlier point",
        "equal-volume mean radius `1737.4 km`",
        "shared default of `720` samples",
        "sky/solar_system/natural_satellites/moon/disk/illuminated",
        "`regional`, `binocular`, `circumpolar`, `planisphere`, and `all_sky`",
        "`1 <= M_moon <= 1000`",
        "display-only",
        "unrelated to Wenu's `presentation` output mode",
        "There is no Moon-specific renderer",
        "python tools/render_49i3e2_resolved_moon_review.py",
        "equatorial coordinates center the binocular chart",
        "horizontal coordinates center the regional chart",
        "magnitude `11.0`",
        "magnified Moon is present and legible in every family",
        "69 focused Moon/display tests in 2.43 seconds",
        "74 current-documentation tests in 3.19 seconds",
        "2,074 routine tests with 30 deselected in 31.19 seconds",
        "all 2,104 tests in 100.17 seconds",
        "Milestone 49I.3E.3 multi-epoch Moon behavior remains unimplemented",
    ):
        assert phrase in contract

    assert "Drawable resolved single-epoch Moon" in architecture
    assert "Milestone 49I.3E.2 — Drawable resolved" in roadmap
    assert "Drawable resolved Moon (Milestone 49I.3E.2)" in implementation
    assert "Milestone 49I.3E.2 resolved single-Moon ownership" in source_tree
    assert "13.2.34 49I.3E.2 drawable resolved Moon" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "drawable_resolved_moon_49i3e2.md" in instructions



def test_49i3e3_records_observed_fixed_chart_moon_sequence():
    contract = " ".join(read(OBSERVED_MOON_SEQUENCE).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    user_guide = " ".join(
        read(ROOT / "docs/user_guide/configuration.md").split()
    )

    for phrase in (
        "Scientifically, architecturally, visually, operationally, and regression accepted",
        "`--moon-disk-sequence`",
        "--disk-sequence-model observed",
        "`COUNT + 1` independently realized samples",
        "one chart-epoch product frame",
        "never treats the scalar bright-limb position angle as frame-invariant",
        "regional, binocular, circumpolar, planisphere, and all-sky",
        "sky/solar_system/natural_satellites/moon/disk_sequence",
        "python tools/validate_49i3e3_observed_moon_sequence.py",
        "`5.458e-08 deg`",
        "`3.800e-12 au`",
        "`1.193e-07 deg`",
        "`0.196988 deg`",
        "python tools/render_49i3e3_observed_moon_sequence_review.py",
        "35 sequence, output-mode, and compatibility tests passed in 3.58 seconds",
        "accepted all five chart-family sequences",
        "75 current-documentation tests in 2.23 seconds",
        "161 expanded focused tests in 5.73 seconds",
        "2,088 routine tests with 30 deselected",
        "all 2,118 tests in 88.61 seconds",
        "Frozen-Earth",
    ):
        assert phrase in contract

    assert "Observed multi-epoch Moon sequence" in architecture
    assert "Milestone 49I.3E.3 — Observed fixed-chart Moon sequence" in roadmap
    assert "Observed Moon disk sequence (Milestone 49I.3E.3)" in implementation
    assert "Milestone 49I.3E.3 observed Moon sequence ownership" in source_tree
    assert "13.2.35 49I.3E.3 observed Moon sequence" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "observed_moon_disk_sequence_49i3e3.md" in instructions
    assert "## Resolved Moon and observed sequences" in user_guide


def test_49i3e_parent_milestone_is_closed_without_new_runtime_scope():
    plan = " ".join(read(RESOLVED_MOON_PLAN).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    assert "**Status:** Accepted and closed on 2026-09-02" in plan
    for phrase in (
        "49I.3E.0 through 49I.3E.3",
        "PRs #70 through #73",
        "`bc45cc0`",
        "75 documentation tests",
        "161 expanded focused tests",
        "2,088 routine tests with 30 deselected",
        "all 2,118 tests",
        "Parent-closure verification passed 76 documentation tests in 9.55 seconds",
        "2,089 routine tests with 30 deselected in 31.89 seconds",
        "all 2,119 tests in 87.44 seconds",
        "No additional runtime behavior is authorized by this parent closure",
    ):
        assert phrase in roadmap

    assert "Completed resolved Moon capability (Milestone 49I.3E)" in architecture
    assert "Resolved Moon integration closure (Milestone 49I.3E)" in implementation
    assert "Milestone 49I.3E resolved Moon ownership closure" in source_tree
    assert "13.2.36 49I.3E resolved Moon closure" in guide
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "Last updated:** `2026-09-02T23:59:30Z`" in guide
    assert "resolved-Moon program 49I.3E.0 through 49I.3E.3 is closed" in instructions

    for document in (plan, architecture, roadmap, implementation, source_tree, guide):
        assert "Frozen-Earth lunar sequences" in document
    assert "Frozen-Earth" in instructions


def test_49j0_freezes_performance_measurement_before_optimization():
    audit = " ".join(read(PERFORMANCE_CLOSURE_AUDIT).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    guide = read(COORDINATE_GUIDE)

    for phrase in (
        "**Audit baseline:** `ea6f340`",
        "**Status:** Architecturally accepted and regression-verified on 2026-09-02",
        "**Runtime effect:** None",
        "Fernando also selected conservative documentation cleanup",
        "`docs/user_guide/` remains separate",
        "76 passed",
        "2,089 passed; 30 deselected",
        "31.89 s",
        "2,119 passed",
        "87.44 s",
        "about 6.3 percent",
        "not the 49J independent-frame baseline",
        "non-overlapping wall-time spans",
        "`time.perf_counter_ns()`",
        "Cold independent-frame oracle",
        "Reusable-sphere comparison",
        "Test-loop characterization",
        "identical projected records",
        "immutable key",
        "49J.1 — Independent-frame benchmark harness",
        "49J.2 — Routine-suite characterization and remediation",
        "49J.3 — First scientifically keyed reuse",
        "49J.4 — Post-v0.9 closure",
        "49J.0 does not authorize",
        "deletion or reclassification of tests",
        "94 combined current-documentation and user-guide tests in 2.61 seconds",
        "2,092 routine tests with 30 deselected in 37.88 seconds",
        "all 2,122 tests in 93.31 seconds",
        "49J.0 is ready for integration",
    ):
        assert phrase in audit

    assert "Milestone 49J.0 — Performance and closure audit" in roadmap
    assert "Every slice remains separately authorized" in roadmap
    assert "Architecturally accepted and regression-verified" in roadmap
    assert "all 2,122 tests" in roadmap
    assert "Performance closure boundary (Milestone 49J)" in architecture
    assert "Performance diagnostics and oracle (Milestone 49J.0)" in implementation
    assert "Milestone 49J performance-program ownership" in source_tree
    assert "performance_and_closure_audit_49j0.md" in instructions
    assert "Do not add caching or optimization under 49J.0" in instructions
    assert "Guide version:** `0.9.5.20260902.54`" in guide
    assert "Last updated:** `2026-09-02T23:59:30Z`" in guide


def test_moving_object_data_resolution_audit_preserves_offline_rendering():
    audit = read(MINOR_BODY_HISTORY / "moving_object_data_resolution_audit_50a3h.md")
    roadmap = read(FUTURE_ROADMAP)
    instructions = read(DEVELOPER / "assistant_instructions.md")

    for phrase in (
        "acquire-if-missing",
        "offline",
        "refresh",
        "content-addressed immutable cache",
        "One shell command does not imply one architectural phase",
        "network I/O",
        "Keplerian element calculation",
        "SGP4/SDP4-compatible propagation",
        "comet numerical validation",
    ):
        assert phrase.lower() in audit.lower()

    assert "Accepted 50A.3H" in roadmap
    assert "104 focused documentation\ntests passed" in roadmap
    assert "installed-CLI preflight phase" in instructions
    assert "Never allow request generation" in instructions


def test_numbered_asteroid_cli_preflight_contract_is_documented():
    document = " ".join(read(
        MINOR_BODY_HISTORY / "numbered_asteroid_cli_preflight_50a3i.md"
    ).split())
    for phrase in (
        "acquire-if-missing",
        "offline",
        "refresh",
        "content-addressed immutable publication",
        "before sphere, view, request, or rendering construction",
        "positive permanent",
        "artificial satellites",
    ):
        assert phrase.lower() in document.lower()


def test_50a4_audits_comet_numerics_before_runtime_behavior():
    audit = " ".join(read(
        MINOR_BODY_HISTORY / "comet_numerical_validation_audit_50a4.md"
    ).split())
    for phrase in (
        "2P/Encke",
        "non-gravitational model",
        "A1`, `A2`, `A3`, or `DT",
        "geocentric astrometric ICRS",
        "topocentric astrometric and apparent ICRS",
        "explicit `--characterize` mode",
        "not an independent rederivation",
        "does not add `--comet`",
        "must never contact SBDB or Horizons",
    ):
        assert phrase.lower() in audit.lower()


def test_50a4_closure_is_offline_accepted_and_non_drawable():
    document = " ".join(read(
        MINOR_BODY_HISTORY / "comet_numerical_validation_50a4.md"
    ).split())
    source_tree = read(DEVELOPER / "source_tree.md")
    implementation = read(DEVELOPER / "implementation_reference.md")
    guide = read(DEVELOPER / "coordinate_system_guide_v0.9.5.md")

    for phrase in (
        "Scientifically, operationally, and regression accepted",
        "build_50a4_comet_fixture.py",
        "validate_50a4_comet.py",
        '"accepted": true',
        '"accepted": false',
        '"tolerances": null',
        "explicit JD TDB",
        "five decimal degrees",
        "No descriptor, chart request, CLI selector, drawing, or exporter",
        "151 focused tests",
        "complete 2,262-test suite",
    ):
        assert phrase.lower() in document.lower()
    assert "compact-oracle construction" in source_tree
    assert "apparition command" in implementation
    assert "This review introduces no new coordinate or product frame" in guide
    assert "barycentric ICRF position | `1e-10 au`" in guide


def test_developer_root_contains_only_active_authority_and_wip_documents():
    assert {
        path.name
        for path in DEVELOPER.iterdir()
        if path.is_file() and not path.name.startswith(".")
    } == {
        "README.md",
        "assistant_instructions.md",
        "artificial_satellite_crossing_audit_50s0.md",
        "comet_discovery_and_reporting_audit_50a5d.md",
        "comet_model_magnitude_audit_50a5d1b.md",
        "configuration_schema_v2.md",
        "coordinate_system_guide_v0.9.5.md",
        "current_architecture_v0.9.md",
        "implementation_reference.md",
        "post_v0.9_architecture_roadmap.md",
        "satchecker_provider_contract_audit_50s2a.md",
        "satellite_report_drawing_audit_50s3a.md",
        "satellite_crossing_oracle_audit_50s5a.md",
        "satellite_crossing_acceleration_audit_50s6a.md",
        "satellite_crossing_coordination_audit_50s6c.md",
        "satellite_multifov_interchange_audit_50s6e.md",
        "satellite_delivery_audit_50s6g.md",
        "satellite_snapshot_preflight_audit_50s6g1b.md",
        "satellite_exact_crossing_report_audit_50s6g2a.md",
        "satellite_tabular_report_audit_50s6g2b.md",
        "satellite_snapshot_admission_audit_50s6g1b2a.md",
        "satellite_medium_specimen_audit_50s6g1b2c.md",
        "satellite_equivalence_matrix_audit_50s6g1b2d.md",
        "satellite_snapshot_propagation_audit_50s4a.md",
        "satellite_guide.md",
        "satellite_program_log.md",
        "source_tree.md",
        "target_architecture_v0.9.5.md",
    }
    for name in (
        "chart_cli_semantics_audit_50a3f.md",
        "cli_contract_acceptance_50a3g.md",
        "moving_object_data_resolution_audit_50a3h.md",
        "numbered_asteroid_cli_preflight_50a3i.md",
        "numbered_asteroids_50a3d.md",
        "object_centered_regional_charts_50a3e.md",
        "comet_numerical_validation_audit_50a4.md",
        "comet_numerical_validation_50a4.md",
        "first_drawable_comet_audit_50a5a.md",
        "solar_system_temporal_components_audit_50a5b1.md",
        "second_drawable_comet_audit_50a5c.md",
        "comet_discovery_50a5d1a.md",
        "comet_name_resolution_audit_50a5d2a.md",
        "comet_acquisition_audit_50a5d2b.md",
        "comet_cli_preflight_audit_50a5d2c.md",
    ):
        assert (MINOR_BODY_HISTORY / name).is_file()
        assert not (DEVELOPER / name).exists()
    assert TEST_PERFORMANCE_PROGRAM.is_file()
    assert not (DEVELOPER / "test_performance_and_future_program_49j_50.md").exists()


def test_50s0_audits_satellite_crossing_search_and_photometry():
    audit = " ".join(read(
        DEVELOPER / "artificial_satellite_crossing_audit_50s0.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    roadmap = " ".join(read(
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).split())

    for phrase in (
        "Accepted by Fernando on 2026-09-14",
        "no runtime satellite, catalogue acquisition, or public crossing command",
        "must not discard a true crossing",
        "Adopt OMM as the canonical ingestion model",
        "Never truncate a catalogue identifier to five digits",
        "Adopt the Vallado-compatible SGP4 implementation",
        "TEME is neither ICRS nor an observer frame",
        "adaptive complete scan as the oracle",
        "HEALPix plus time slabs remains the leading optional index",
        "zero false negatives",
        "Near-zenith intervals",
        "empirical satellite-family magnitude distribution",
        "A single standard magnitude is not a substitute for a phase function",
        "Detector contamination remains later work",
        "checked 2026-09-14",
        "at most one supported bulk request",
        "No per-object requests, polling loop, parallel downloads, or automatic retry",
        "Space-Track is valuable as an authenticated independent source",
        "SatChecker first as a bounded online crossing provider and external oracle",
        "strict separation of crossing, illumination, apparent magnitude",
        "The orbital-plane test is topocentric",
        "small, geometrically representative immutable OMM snapshot",
        "developer specimen builder",
        "50S.0 through 50S.3 end with SatChecker reports/charts",
    ):
        assert phrase in audit

    assert "artificial_satellite_crossing_audit_50s0.md" in index
    for phrase in (
        "50S.0 scientific and architectural decisions accepted by Fernando on 2026-09-14",
        "50S.1 — Provider-neutral satellite crossing domain",
        "50S.2 — SatChecker crossing adapter",
        "50S.3A — Satellite report and drawing contract audit",
        "50S.3B — SatChecker sampled-candidate reports and tracks",
        "50S.4A — Snapshot and propagation contract audit",
        "50S.4B — Immutable OMM element snapshot",
        "50S.4C — Validated SGP4/TEME propagation",
        "50S.4D — Earth-orientation and topocentric state",
        "50S.4E — Propagated specimen builder and closure",
        "50S.5 — Complete local FoV-crossing oracle",
        "50S.6 — Conservative local crossing acceleration",
        "50S.7 — Independent illumination and night geometry",
        "50S.8 — Apparent-brightness estimation and validation",
        "50S.9 — Detector-specific contamination",
        "50S.10 — Night, season, and sky-position products and closure",
    ):
        assert phrase in roadmap


def test_satellite_guide_preserves_50s_scientific_boundaries():
    guide = " ".join(read(DEVELOPER / "satellite_guide.md").split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    audit = " ".join(read(
        DEVELOPER / "artificial_satellite_crossing_audit_50s0.md"
    ).split())

    for phrase in (
        "Living 50S work-in-progress guide",
        "intentionally separate from `coordinate_system_guide_v0.9.5.md`",
        "Acronyms and specialized abbreviations",
        "OMM and TLE are not two competing propagation models",
        "OMM — Orbit Mean-Elements Message",
        "TLE — two-line element set",
        "SGP4 — Simplified General Perturbations 4",
        "TEME — True Equator, Mean Equinox",
        "HEALPix — Hierarchical Equal Area isoLatitude Pixelization",
        "EOP — Earth-orientation parameters",
        "geometric crossing",
        "illumination",
        "apparent brightness",
        "detector contamination",
        "validated immutable OMM/TLE snapshot",
        "No later stage may change the result of an earlier geometric crossing test",
        "must not define the internal identity model",
        "A snapshot is a frozen copy of the provider's orbit catalogue",
        "It is not a set of satellite positions",
        "one supported bulk request",
        "TEME is not ICRS, GCRS, ITRS, or topocentric AltAz",
        "A fixed sampling grid alone is not a completeness proof",
        "omega = |rho x rho_dot| / |rho|^2",
        "Near-zenith or otherwise singular intervals",
        "zero false negatives",
        "HEALPix is the leading pixelization candidate",
        "orbital-plane/FoV-cone intersection",
        "Testing only the angular distance to a geocentric orbital great circle is unsafe",
        "provider data from cache wherever possible",
        "small representative OMM snapshot",
        "developer specimen builder",
        "dense/adaptive brute-force reference path must remain independent",
        "missing flare evidence produces `unknown`, never zero flare probability",
        "A single standard magnitude does not replace a phase function",
        "Measured maxima tune performance but never replace conservative bounds",
        "must not duplicate Wenu's coordinate service",
        "do not merge documents mechanically",
    ):
        assert phrase in guide

    assert "satellite_guide.md" in index
    assert "satellite_guide.md" in audit

    archived = {
        "archive/audits/coordinate_transformation_audit_09a2afd.md",
        "archive/audits/public_interface_audit_v0.9.5.md",
        "archive/migration_history/deprecations_v0.5.md",
        "archive/roadmap_history/wenu_cli_feature_requests.md",
        "archive/milestone_history/49d_scene/celestial_scene_dependency_audit_49d1.md",
        "archive/milestone_history/49e_ephemeris/ephemeris_provider_contract_49e1.md",
        "archive/milestone_history/49i_solar_system/resolved_moon_plan_49i3e.md",
        "archive/milestone_history/49i_solar_system/observed_moon_disk_sequence_49i3e3.md",
        "archive/milestone_history/49j_performance/performance_and_closure_audit_49j0.md",
        "archive/milestone_history/49j_performance/test_architecture_and_accepted_practice_audit_49j1.md",
        "archive/milestone_history/49j_performance/test_practice_decisions_49j2.md",
        "archive/milestone_history/49j_performance/test_entry_and_admission_49j3a.md",
        "archive/milestone_history/49j_performance/marker_truthfulness_49j3b.md",
        "archive/milestone_history/49j_performance/repository_source_index_49j3c.md",
        "archive/milestone_history/49j_performance/immutable_catalogue_fixture_49j3d.md",
        "archive/milestone_history/49j_performance/cold_builder_kernel_oracles_49j3e.md",
        "archive/milestone_history/49j_performance/calendar_layout_cost_49j3f.md",
        "archive/milestone_history/49j_performance/observer_time_sequence_oracle_49j3g.md",
        "archive/milestone_history/49j_performance/test_suite_optimization_closure_49j3h.md",
        "archive/milestone_history/49j_performance/cold_frame_performance_baseline_49j4.md",
        "archive/milestone_history/50a_minor_bodies/minor_body_state_provider_50a1.md",
        "archive/milestone_history/50a_minor_bodies/asteroid_numerical_validation_50a2.md",
        "archive/milestone_history/50a_minor_bodies/drawable_ceres_50a3b.md",
    }
    for relative in archived:
        assert (DEVELOPER / relative).is_file()

    archive_index = read(ARCHIVE / "README.md")
    for folder in (
        "49d_scene",
        "49e_ephemeris",
        "49i_solar_system",
        "49j_performance",
        "50a_minor_bodies",
    ):
        assert f"`milestone_history/{folder}/`" in archive_index


def test_50a5a_audits_first_drawable_comet_without_runtime_behavior():
    audit = " ".join(read(
        MINOR_BODY_HISTORY / "first_drawable_comet_audit_50a5a.md"
    ).split())
    for phrase in (
        "Runtime effect:** None",
        "Scientifically and architecturally accepted",
        "2P/Encke",
        "sky/solar_system/minor_bodies/comets/2p",
        "--comet 2P",
        "--comet-track 2P",
        "explicit installed resource directory",
        "A1",
        "A2",
        "`P`, `D`, `I`, `C`, `X`, and `A`",
        "recognizing a well-formed designation is not a promise",
        "a `D` object normally fails",
        "a future validated `I` SPK",
        "fragment suffixes",
        "central long spoke points **antisolar**",
        "constructed vector symbol",
        "one hollow central circle",
        "several evenly distributed short radial spokes",
        "three longer adjacent spokes",
        "initial total fan angle",
        "1.5` times",
        "must not depend on a Unicode comet glyph",
        "one canonical reusable vector symbol",
        "placement, orientation, and magnification",
        "must not reconstruct its circle and spokes from scratch",
        "immutable and safe to reuse",
        "must not redefine the geometry",
        "one semantic comet-symbol entity",
        "physical direction claim",
        "apparent comet and Sun directions",
        "independent direct-Horizons apparent Sun and comet directions",
        "number of normal spokes",
        "immutable collection",
        "--comet-track 2P --planet-track venus --asteroid-track 79989",
        "all selected tracks share",
        "Artificial-satellite tracks remain outside",
        "not a resolved nucleus, coma, tail, brightness, visibility",
        "must not extend the numbered-asteroid automatic preflight",
        "the existing observer, astrometric, apparent",
        "That acceptance authorizes only the bounded 50A.5B",
    ):
        assert phrase.lower() in audit.lower()


def test_current_49j_50_program_records_research_decisions_and_order():
    program = " ".join(read(TEST_PERFORMANCE_PROGRAM).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())

    for phrase in (
        "Adopt",
        "Adapt",
        "Reject",
        "Defer",
        "49J.1 — Test architecture and accepted-practice audit",
        "49J.2 — Wenu test-practice decisions",
        "49J.3 — Test-suite optimization",
        "49J.4 — Cold chart and sequence performance baseline",
        "49J.5 — First scientifically keyed chart reuse",
        "49J.6 — Performance closure",
        "Program 50A — Asteroids and comets",
        "50B.0 — Accepted-practice review",
        "50B.1 — Wenu publication-standard decisions",
        "PDF/X",
        "WCAG",
        "printed star atlases",
        "Screen PNG review is not sufficient",
    ):
        assert phrase in program

    assert "49J.1 test architecture and accepted-practice audit" in roadmap
    assert "Program 50A - Asteroids and comets" in roadmap
    assert "Program 50B - Publication legibility" in roadmap


def test_49j1_records_current_practice_static_evidence_and_pending_timings():
    audit = " ".join(read(TEST_PRACTICE_AUDIT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "**Audit baseline:** `d92f393`",
        "**Runtime effect:** None",
        "187 `test_*.py` modules",
        "1,767 test-function definitions",
        "2,123 test cases",
        "16 declared fixtures",
        "No class-, package-, or session-scoped fixture",
        "no `tests/conftest.py`",
        "127 parametrization decorators",
        "Adopt",
        "Adapt",
        "Reject",
        "Defer",
        "pytest: How to use fixtures",
        "pytest: Flaky tests",
        "coverage.py: Dynamic contexts",
        "ISO/IEC/IEEE 29119-1:2022",
        "2,094",
        "27.16 s",
        "3.42 s",
        "2,124",
        "85.49 s",
        "2.19 s",
        "pytest_filter_subpackage",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
        "--durations=50",
        "No answer is adopted by this document",
        "coordinate-system guide was reviewed",
    ):
        assert phrase in audit

    assert "49J.1 is accepted and archived" in roadmap
    assert "The committed suite has no session-scoped fixture" in source_tree


def test_49j2_records_proposed_test_policy_and_duplication_control():
    decisions = " ".join(read(TEST_PRACTICE_DECISIONS).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "**Status:** Accepted by Fernando on 2026-09-09; ready for integration",
        "D4 — External pytest plugins: **Adopt**",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
        "D6 — Reuse of expensive immutable setup: **Adapt**",
        "D9 — Independent scientific recomputation: **Adopt**",
        "D12 — New-test admission and duplication control: **Adopt**",
        "does **not** automatically duplicate all lower-level tests",
        "What fault would this test catch that existing tests would not?",
        "D13 — Deleting or consolidating tests: **Adopt**",
        "D20 — Parallel execution: **Defer**",
        "D22 — Canonical observer-time sequence: **Reject** test removal",
        "Each materially different implementation group",
        "reviewed and accepted the ledger in five groups",
    ):
        assert phrase in decisions

    assert "Fernando accepted 49J.2 on 2026-09-09" in roadmap
    assert "Before adding a test" in instructions


def test_49j3a_installs_reproducible_entry_and_new_test_admission_rules():
    record = " ".join(read(TEST_ENTRY_ADMISSION).split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())

    for phrase in (
        "Reproducible test entry and admission rules (Milestone 49J.3A)",
        "**Status:** Accepted and merged in `21ee528`",
        "**Runtime effect:** None",
        "**Test behavior effect:** None",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest",
        "distinct contract or fault model",
        "closest existing coverage",
        "does not repeat all lower-level tests",
        "cannot claim a performance improvement",
        "coordinate-system guide was reviewed",
        "83 current-documentation tests in 2.12 seconds",
        "same 83 tests in 2.43 seconds",
    ):
        assert phrase in record

    assert "Before adding a test" in instructions
    assert "Which existing test is closest" in instructions
    assert "Which marker and gate" in instructions
    assert "Any required plugin must be explicitly loaded" in instructions
    for phrase in (
        "Layered post-change verification",
        "smallest focused gate that covers every changed responsibility",
        "Do not repeatedly run unrelated tests",
        "once before presenting a bounded implementation milestone",
        "before merging a milestone branch into its integration branch",
        "before merging the integration branch into `main`",
        "A previously passing full suite remains valid across a later documentation-only edit",
        "or non-documentation test collection changed",
        "Record the exact commit or remote tree covered by every focused and full-suite result",
        "Do not create a marker or empty future test file merely to name a branch or milestone",
    ):
        assert phrase in instructions
    assert source_tree.count("PYTEST_DISABLE_PLUGIN_AUTOLOAD=1") >= 4
    assert "49J.3A implemented only" in roadmap
    assert "83 current-documentation tests in 2.43" in roadmap


def test_49j3b_records_truthful_marker_scope_without_changing_assertions():
    record = " ".join(read(MARKER_TRUTHFULNESS).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "Test-marker truthfulness (Milestone 49J.3B)",
        "**Runtime effect:** None",
        "**Test assertion and fixture effect:** None",
        "Markers describe work and resources",
        "does not by itself require `visual`",
        "canonical observer-time sequence remains both `integration` and `slow`",
        "calendar-label containment check remains both `visual` and `slow`",
        "focused constants contract returns to the routine gate",
        "2,103 routine cases with 24 deselected",
        "21 integration cases, 3 visual cases, 2 slow cases",
        "No committed pytest case requires an installed DE440 kernel",
        "coordinate-system guide was reviewed",
        "94 focused tests in 9.21 seconds",
        "all 2,127 tests in 88.79 seconds",
    ):
        assert phrase in record

    assert "49J.3B audited marker truthfulness" in roadmap
    assert "2,103 routine tests with 24 deselected" in roadmap
    assert "all 2,127 tests" in roadmap
    assert "marker_truthfulness_49j3b.md" in architecture
    assert "Marker corrections change gate membership only" in source_tree

    planisphere = ast.parse(
        read(ROOT / "tests/test_planisphere_composition.py")
    )
    cen_a = ast.parse(read(ROOT / "tests/test_cen_a_binocular.py"))

    def marked_functions(tree, marker):
        return {
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and any(
                ast.unparse(decorator) == f"pytest.mark.{marker}"
                for decorator in node.decorator_list
            )
        }

    assert marked_functions(planisphere, "visual") == {
        "test_planisphere_export_has_transparent_corner_and_opaque_center",
        "test_default_planisphere_legends_are_outside_and_disjoint_from_axes",
    }
    assert marked_functions(cen_a, "integration") == {
        "test_chart_is_centered_on_cen_a_and_is_square",
        "test_circular_aperture_has_expected_projected_radius",
    }


def test_49j3c_records_complete_shared_source_index_and_retained_faults():
    record = " ".join(read(REPOSITORY_SOURCE_INDEX).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "Repository source index (Milestone 49J.3C)",
        "**Status:** Accepted and merged in `23d1b32`",
        "changes no installed package",
        "independent subprocess/import-isolation oracle",
        "all Python paths below `src`, `tests`, `examples`, `tools`, and `example_scripts`",
        "lazily caches its UTF-8 text and parsed AST",
        "proves exact inventory equality",
        "median 2.39 seconds",
        "observed median improvement is 0.38 seconds, or about 9.1 percent",
        "2,105 tests with 24 deselected",
        "all 2,129 tests",
        "median 89.59 seconds; range 1.29 seconds",
        "three routine and three complete Mac runs",
        "coordinate-system guide was reviewed",
    ):
        assert phrase in record

    assert "49J.3C completed" in roadmap
    assert "repository_source_index_49j3c.md" in architecture
    assert "tests/repository_sources.py" in source_tree


def test_49j3d_records_only_proved_immutable_catalogue_fixture_reuse():
    record = " ".join(read(IMMUTABLE_CATALOGUE_FIXTURE).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "Immutable catalogue fixture (Milestone 49J.3D)",
        "**Status:** Accepted and merged in `63beb17`",
        "canonical sphere is not eligible for session scope",
        "No sphere/build registry is installed",
        "nested `MappingProxyType` values",
        "outer and inner mutation attempts",
        "one assertion owns exact identifier presence and order",
        "other owns north/south overlap counts",
        "retains an independent cold canonical factory build",
        "forward, reverse, and isolated execution",
        "coordinate-system guide was reviewed",
        "median 1.27 seconds",
        "median 1.18 seconds",
        "local diagnostic reduction of about 7 percent",
        "exact missing identifier",
        "about 9.4 percent",
        "approximately 50-percent reduction",
        "159 focused documentation, catalogue, geometry, and cold-factory tests",
        "2,106 routine tests with 24 deselected",
        "all 2,130 tests in 85.61 seconds",
        "three distinct nodes",
    ):
        assert phrase in record

    assert "49J.3D completed" in roadmap
    assert "immutable_catalogue_fixture_49j3d.md" in architecture
    assert "catalogue_positions" in source_tree


def test_49j3e_preserves_cold_builders_and_independent_kernel_oracles():
    record = " ".join(read(COLD_BUILDER_KERNEL_ORACLES).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "Cold builders and installed-kernel oracles (Milestone 49J.3E)",
        "**Status:** Accepted and merged in `6db2272`",
        "no new fixture, build registry, kernel cache, observer cache",
        "independently recomputes its direct Skyfield comparison",
        "Direction, light-time, apparent-place, parallax, physical appearance",
        "commands run in separate processes",
        "refuse an unavailable kernel instead of downloading one",
        "Sharing an observer, requested time, direct Skyfield result",
        "retains the independent cold ordinary factory",
        "temporary horizon mutation and restoration",
        "real independent observer-time frames",
        "3.43 seconds for the cold ordinary factory",
        "20.72 seconds for the real observer-time sequence",
        "87 current-documentation tests in 2.54 seconds",
        "2,107 routine tests with 24 deselected in 28.34 seconds",
        "all 2,131 tests in 85.58 seconds",
        "3.42 seconds for the ordinary canonical factory",
        "21.27 seconds for the real observer-time sequence",
        "evidence supports preservation rather than consolidation",
        "No speedup is claimed",
        "**Runtime effect:** None",
        "**Test behavior effect:** None",
        "coordinate-system guide was reviewed",
    ):
        assert phrase in record

    assert "49J.3E completed" in roadmap
    assert "cold_builder_kernel_oracles_49j3e.md" in architecture
    assert "direct installed-kernel recomputation" in implementation
    assert "independently recomputed installed-DE440" in source_tree


def test_49j3f_removes_only_redundant_calendar_canvas_redraws():
    record = " ".join(read(CALENDAR_LAYOUT_COST).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "Calendar layout cost (Milestone 49J.3F)",
        "**Status:** Accepted and merged in `a190a09`",
        "all 83 day and month labels",
        "97.5 mm physical disk",
        "83 redundant full-canvas redraws",
        "`Text.get_window_extent(renderer=...)`",
        "anchors, font metrics, tangential/outward extents",
        "Median elapsed time fell from 6.77 to 1.88 seconds",
        "median call time fell from 5.98 to 0.90 seconds",
        "about 85 percent",
        "outer corner of 106.64 mm",
        "mutation was reverted before commit",
        "median 15.27 seconds",
        "median 3.14 seconds",
        "79.4 percent in elapsed time",
        "88.0 percent in call time",
        "93 focused documentation and page-rendering tests",
        "2,108 routine tests with 24 deselected",
        "all 2,132 tests in 77.94 seconds",
        "characterization evidence, not a threshold",
        "**Runtime effect:** None",
        "**Test behavior effect:** None",
        "does not reduce dpi, sample labels",
    ):
        assert phrase in record

    assert "49J.3F completed" in roadmap
    assert "calendar_layout_cost_49j3f.md" in architecture
    assert "redundant full-canvas redraws" in source_tree


def test_49j3g_preserves_the_canonical_observer_time_sequence_oracle():
    record = " ".join(read(OBSERVER_TIME_SEQUENCE_ORACLE).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "Canonical observer-time sequence oracle (Milestone 49J.3G)",
        "**Status:** Accepted and merged in `d7ba1d5`",
        "retain the test unchanged",
        "minimum scientifically meaningful sequence of two instants",
        "`generate_observer_time_chart_sequence()`",
        "`generate_chart_request()`",
        "equal image dimensions, different image bytes",
        "detect per-frame observer time errors",
        "current complete route binds each sphere",
        "would violate D22 directly",
        "independent-frame timing harness in 49J.4",
        "first fixed-sky reuse in 49J.5",
        "isolated real canonical sequence in 24.69 seconds",
        "22.90 seconds in the test call",
        "101 tests in 25.30 seconds",
        "2,109 tests with 24 deselected in 26.54 seconds",
        "all 2,133 tests passed in 76.85 seconds",
        "slowest test at 20.79 seconds",
        "neither removed, mocked, nor hidden",
        "No speedup is claimed",
        "**Runtime effect:** None",
        "**Test behavior effect:** None",
        "does not optimize chart generation",
    ):
        assert phrase in record

    assert "49J.3G completed" in roadmap
    assert "observer_time_sequence_oracle_49j3g.md" in architecture
    assert "cold two-frame canonical sequence" in implementation
    assert "cold complete observer-time route" in source_tree


def test_49j3h_closes_fault_models_and_governs_test_file_growth():
    record = " ".join(read(TEST_SUITE_OPTIMIZATION_CLOSURE).split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())

    for phrase in (
        "Test-suite optimization closure (Milestone 49J.3H)",
        "**Status:** Accepted and merged in `2c524d2`",
        "188 `test_*.py` files",
        "does not reorganize them retrospectively",
        "Retained fault-model map",
        "exact inventory coverage was added",
        "a 40-point mutation still fails",
        "Two real canonical frames",
        "three fresh routine runs and three fresh complete runs",
        "Timings remain characterization evidence, not enforced thresholds",
        "90 current-documentation tests in 2.95 seconds",
        "two consumers passed in reverse order in 1.67 seconds",
        "each passed isolated in 1.72 seconds",
        "2,110 tests with 24 deselected",
        "median 27.06 seconds, range 1.01 seconds",
        "all 2,134 tests",
        "median 78.95 seconds, range 1.19 seconds",
        "20.72, 21.35, and 20.43 seconds",
        "did not hide the retained complete route",
        "49J.4 may then add the independent cold chart/frame timing harness",
        "first such optimization remains 49J.5",
        "**Runtime effect:** None",
        "**Test behavior effect:** None",
    ):
        assert phrase in record

    for phrase in (
        "Test-file placement and growth",
        "existing file that owns the closest stable product responsibility",
        "Do not create a test file merely for a milestone",
        "Create a new test file only when",
        "closest existing test file",
        "Name test files for enduring responsibilities",
        "review test-file count, new files added, complete-route duplication",
        "Do not reorganize existing tests solely to reduce the number of files",
    ):
        assert phrase in instructions

    assert "49J.3H completed" in roadmap
    assert "test_suite_optimization_closure_49j3h.md" in architecture


def test_49j4_defines_a_cold_exclusive_nonoptimizing_harness():
    record = " ".join(read(COLD_FRAME_PERFORMANCE_BASELINE).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "Cold independent-frame performance baseline (Milestone 49J.4)",
        "**Status:** Accepted and merged in `f4dcf11`",
        "adds no cache, performance threshold, alternate renderer",
        "three accepted fixed-sky circumpolar frames",
        "`generate_chart_request()` complete-render oracle",
        "`tools/benchmark_reusable_sphere.py` remains a separate",
        "`time.perf_counter_ns()`",
        "deepest declared owner",
        "`unclassified_residual`",
        "equal `complete_frame` exactly",
        "median, minimum, maximum, and range",
        "Console progress advances from 0 to 100 percent",
        "La Ligua and three UTC instants",
        "SHA-256 digest, semantic paths, and projected record types",
        "canonical catalogue load profile, and DE440s ephemeris identity",
        "Three unit contracts were added to the existing fixed-sky baseline",
        "49J.5 reuse work is authorized only through separately reviewed bounded slices",
        "Python 3.11.7",
        "zero-nanosecond accounting deltas",
        "1677 by 1740 pixel dimensions",
        "`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`",
        "Median complete-frame time was 25.509 seconds",
        "5.869-second range",
        "8.447 catalogue/resource loading",
        "6.661 provider evaluation",
        "first-run-sensitive astronomical-transformation range",
        "139 focused tests in 7.31 seconds",
        "2,114 routine tests with 24 deselected in 28.03 seconds",
        "all 2,138 tests in 79.21 seconds",
        "slowest complete-suite test at 20.96 seconds",
        "no timing threshold or optimization claim",
        "**Runtime effect:** None outside explicit diagnostic execution",
    ):
        assert phrase in record

    assert "49J.4 completed" in roadmap
    assert "cold_frame_performance_baseline_49j4.md" in architecture
    assert "raw exclusive `perf_counter_ns` observations" in implementation
    assert "attributes every profiled interval to one exclusive" in source_tree


def test_49j5a_defines_only_the_loaded_sphere_reuse_seam():
    record = " ".join(read(LOADED_SPHERE_REUSE).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "Loaded-sphere reuse seam (Milestone 49J.5A)",
        "**Status:** Accepted and merged in `de78e14` through PR #88",
        "`cold` remains the independent complete-render oracle",
        "`reuse_loaded_sphere` loads one observer-independent canonical celestial sphere",
        "fresh scientific observer to every canonical frame request",
        "contains no bound observer",
        "creates and closes an `Observer`",
        "`generate_chart_request()` remains the complete static route",
        "rejects an unbound sphere without an observer",
        "canonical sphere build count",
        "no milestone-named test file",
        "did not itself claim performance improvement",
        "49J.5B before 49J.5 was accepted as a whole",
        "135 tests in 7.50 seconds",
        "2,118 selected tests with 24 deselected in 27.92 seconds",
        "all 2,142 tests in 79.04 seconds",
        "slowest complete test at 20.84 seconds",
        "final performance acceptance for 49J.5",
        "default cold route is unchanged",
    ):
        assert phrase in record

    assert "49J.5 is accepted" in roadmap
    assert "archive/milestone_history/49j_performance/loaded_sphere_reuse_49j5a.md" in architecture
    assert "FixedSkySequenceExecution.REUSE_LOADED_SPHERE" in implementation
    assert "observer-independent loaded-sphere sequence policy" in source_tree


def test_49j5b_defines_exact_reuse_equivalence_and_raw_measurement():
    record = " ".join(read(FIXED_SKY_REUSE_EQUIVALENCE).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())

    for phrase in (
        "Fixed-sky reuse equivalence (Milestone 49J.5B)",
        "**Status:** Accepted and merged in `a028e89` through PR #89",
        "same sequence orchestrator",
        "not an installed interface or second executor",
        "Raw sequence durations and ratios",
        "no timing threshold",
        "spherical and projected records",
        "composition, clipping",
        "PNG pixels in RGBA space",
        "volatile marker and clip identifiers",
        "Wenu semantic identifiers",
        "`pdftoppm` at 150 DPI",
        "fails closed",
        "Cold remains the default",
        "all three frames matched exactly",
        "macOS-10.16-x86_64-i386-64bit",
        "35.897 versus 25.267 seconds for PNG",
        "Fernando also visually accepted the six paired PNG frames",
        "Runtime effect:** None",
    ):
        assert phrase in record

    assert "archive/milestone_history/49j_performance/fixed_sky_reuse_equivalence_49j5b.md" in roadmap
    assert "archive/milestone_history/49j_performance/fixed_sky_reuse_equivalence_49j5b.md" in architecture
    assert "tools/benchmark_fixed_sky_reuse.py" in source_tree


def test_49j6_closes_performance_and_preserves_both_execution_routes():
    record = " ".join(read(PERFORMANCE_CLOSURE).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    instructions = " ".join(read(INSTRUCTIONS).split())
    user_sequences = " ".join(
        read(ROOT / "docs/user_guide/temporal_sequences.md").split()
    )

    for phrase in (
        "Performance closure (Milestone 49J.6)",
        "PR #88, merged as `de78e14`",
        "`a028e8945f5f2903702adbc2cbd2a46e3bffff06`",
        "Cold execution remains the default complete-render correctness oracle",
        "one observer-independent loaded canonical celestial sphere",
        "fresh `Observer`",
        "macOS-10.16-x86_64-i386-64bit",
        "normalized semantic SVG",
        "macOS `sips` renderer",
        "Fernando also visually accepted the six paired PNG frames",
        "| PNG | 35.897 s | 25.267 s | 1.421x |",
        "characterization evidence, not enforced performance thresholds",
        "2,122 passed, 24 deselected in 33.24 seconds",
        "24 passed, 2,122 deselected in 56.47 seconds",
        "all 2,146 collected tests",
        "No CLI example changes are required",
        "No architecture-diagram change is required",
        "Program 50A.0",
        "**Runtime effect:** None",
    ):
        assert phrase in record

    assert "49J.6 is accepted and archived" in roadmap
    assert "49J is closed. Program 50A.0 is next" in roadmap
    assert "performance_closure_49j6.md" in architecture
    assert "performance_closure_49j6.md" in implementation
    assert "performance_closure_49j6.md" in instructions
    assert "changes no CLI default or output" in user_sequences


def test_50a0_accepts_one_offline_minor_body_provider_boundary():
    audit = " ".join(read(MINOR_BODY_PROVIDER_AUDIT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())

    for phrase in (
        "Minor-body scientific and provider audit (Milestone 50A.0)",
        "**Status:** Accepted by Fernando",
        "Fernando accepted the scientific and architectural decisions",
        "Milestone 50A.0 is closed",
        "**Baseline:** `b96a033`",
        "bounded Horizons-generated small-body SPK",
        "Live Horizons/SBDB during rendering: Reject",
        "Orbital-element provider: Defer",
        "two-body Keplerian propagator",
        "simultaneous **geometric** Cartesian state",
        "Production state output converges on ICRF axes and TDB evaluation",
        "Wenu identity stays distinct from all provider-native identifiers",
        "Fail closed outside SPK segment coverage",
        "Asteroid photometry: Adapt",
        "Comet photometry and appearance: Defer",
        "Comet non-gravitational dynamics: Adapt",
        "Nucleus, coma, and tail semantics: Adopt",
        "No visual comparison is required",
        "The user guide and examples require no edit",
        "Architecture diagrams require no edit",
        "**Runtime effect:** None",
    ):
        assert phrase in audit

    for url in (
        "https://ssd-api.jpl.nasa.gov/doc/horizons.html",
        "https://ssd.jpl.nasa.gov/horizons/manual.html",
        "https://ssd-api.jpl.nasa.gov/doc/sbdb.html",
        "https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/spk.html",
        "https://docs.minorplanetcenter.net/",
        "https://doi.org/10.1086/111402",
    ):
        assert url in read(MINOR_BODY_PROVIDER_AUDIT)

    assert "50A.0 is accepted and archived" in roadmap
    assert "Minor-body provider boundary (accepted Milestone 50A.0)" in architecture
    assert "archive/milestone_history/50a_minor_bodies/" in implementation
    assert "Accepted 50A minor-body ownership" in source_tree
    assert "For 50A minor-body work" in instructions
    assert "50A.0 minor-body scientific and provider audit" in guide
    assert "Accepted by Fernando on 2026-09-10" in guide
    assert "Requests outside coverage fail closed" in guide
    assert "cannot become a silent two-body fallback" in guide
    assert "Wenu must neither discard nor reapply them" in guide
    assert "changes no coordinate calculation or visible output" in guide


def test_50a1_installs_only_the_offline_minor_body_state_provider_seam():
    record = " ".join(read(MINOR_BODY_STATE_PROVIDER).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    diagrams = " ".join(
        read(DEVELOPER / "diagrams/README.md").split()
    )
    provider_dot = read(
        DEVELOPER / "diagrams/minor_body_state_provider_50a1.dot"
    )
    provider_svg = read(
        DEVELOPER / "diagrams/minor_body_state_provider_50a1.svg"
    )

    for phrase in (
        "Generic minor-body state provider (Milestone 50A.1)",
        "**Status:** Accepted by Fernando on 2026-09-10",
        "**Base:** `9097d4f`",
        "One resolved Horizons small-body SPK",
        "EphemerisResourceChain",
        "MinorBodySolutionIdentity",
        "MinorBodyEphemerisState",
        "selected `MinorBodySegmentIdentity`",
        "selects the last covering target segment",
        "same TDB instant",
        "It does not extrapolate or silently substitute a two-body orbit",
        "tests/test_minor_body_ephemeris.py",
        "performs no network access",
        "User documentation and examples remain unchanged",
        "50A.2 numerical validation",
        "full macOS suite passed all 2166 tests",
        "No body, chart request, CLI option, direction, projection, rendering, or output",
    ):
        assert phrase in record

    assert "50A.1 is accepted" in roadmap
    assert "Minor-body state-provider seam (Milestone 50A.1 accepted)" in architecture
    assert "Generic minor-body state provider (Milestone 50A.1)" in implementation
    assert "50A.1 minor-body state-provider ownership" in source_tree
    assert "accepted 50A.1 and 50A.2 records" in instructions
    assert "50A.1 generic minor-body state provider" in guide
    assert "r_{BO}=\\mathbf r_{BC}+\\mathbf r_{CO}" in guide
    assert "resource-chain and geometric-state provider seam" in diagrams
    for phrase in (
        "EphemerisResourceChain",
        "SkyfieldMinorBodyStateSource",
        "MinorBodyEphemerisState",
        "not connected in 50A.1",
    ):
        assert phrase in provider_dot
        assert phrase in provider_svg


def test_50a2_validates_type_21_ceres_and_apophis_without_a_body():
    record = " ".join(read(ASTEROID_NUMERICAL_VALIDATION).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    program = " ".join(read(TEST_PERFORMANCE_PROGRAM).split())
    diagrams = " ".join(read(DEVELOPER / "diagrams/README.md").split())
    validation_dot = read(
        DEVELOPER / "diagrams/asteroid_validation_50a2.dot"
    )
    validation_svg = html.unescape(
        read(DEVELOPER / "diagrams/asteroid_validation_50a2.svg")
    )
    fixture = json.loads(
        read(ROOT / "tests/fixtures/horizons_asteroid_validation_50a2.json")
    )

    for phrase in (
        "Asteroid numerical validation (Milestone 50A.2)",
        "Accepted by Fernando on 2026-09-11",
        "SpiceyPy/CSPICE evaluates only the exact small-body segment",
        "does not furnish the file to SPICE's global kernel pool",
        "(1) Ceres",
        "(99942) Apophis",
        "5e-6 deg (18 mas)",
        "0.695321 degrees",
        "All seven epochs passed",
        "macOS-10.16-x86_64-i386-64bit and Python 3.11.7",
        "SpiceyPy 6.0.3",
        "CSPICE N0067",
        "aae80e3c547a419d589eca17a49348c599a883ef41b0d36c6609fa4a489be353",
        "d9cdb50eaa5af02e83babefbc0e37cab35f69fa288250b9dbf28bccf9a8bc9e7",
        "expected `dubious year` warnings",
        "passed 161 tests in 3.67 seconds",
        "passed all 2,170 tests in 84.28 seconds",
        "final documentation-contract gate passed 97 tests in 2.83 seconds",
        "does not authorize replacing Skyfield",
        "User documentation and examples require no edit",
        "adds no public selection, default, configuration, symbol, track, or visible result",
    ):
        assert phrase in record

    assert "50A.2 is accepted and archived" in roadmap
    assert "Milestone 50A.2 adds `SpiceMinorBodyKernel`" in architecture
    assert "`spiceypy>=6,<9`" in implementation
    assert "50A.2 asteroid numerical-validation ownership" in source_tree
    assert "50A.2 is accepted; 50A.3 is the next" in instructions
    assert "accepted in the 50A.2 scientific gate" in guide
    assert "50A.3 is next" in program
    assert "50A.2 asteroid-validation SVG" in diagrams
    for phrase in (
        "SpiceMinorBodyKernel",
        "exact type-21 descriptor",
        "Frozen direct Horizons oracle",
        "not connected in 50A.2",
    ):
        assert phrase in validation_dot
        assert phrase in validation_svg

    assert fixture["authority"]["api"] == "NASA/JPL Horizons API"
    assert fixture["authority"]["returned_version"] == "1.2"
    assert [item["key"] for item in fixture["objects"]] == [
        "ceres",
        "apophis",
    ]
    assert [len(item["epochs"]) for item in fixture["objects"]] == [3, 4]
    assert {
        item["spk"]["segment_type"] for item in fixture["objects"]
    } == {21}

    acquisition = read(ROOT / "tools/acquire_50a2_asteroid_resources.py")
    validator = read(ROOT / "tools/validate_50a2_asteroids.py")
    assert "https://ssd.jpl.nasa.gov/api/horizons.api" in acquisition
    assert "refusing to overwrite existing 50A.2 evidence" in acquisition
    assert '"".join(document["spk"].split()).encode("ascii")' in acquisition
    assert "base64.b64decode(encoded, validate=True)" in acquisition
    assert "removes only whitespace before strict base64 decoding" in record
    assert "POSITION_TOLERANCE_AU = 5.0e-12" in validator
    assert "DIRECTION_TOLERANCE_DEG = 5.0e-6" in validator
    assert "SpiceMinorBodyKernel" in validator
    assert '"--planetary-ephemeris-path"' in validator
    assert "DEFAULT_DATA_DIRECTORY / DEFAULT_EPHEMERIS" in validator
    assert "defaults to `~/.cache/wenu/de440s.bsp`" in record


def test_50a3a_audits_one_manifest_backed_drawable_ceres_route():
    audit = " ".join(read(FIRST_DRAWABLE_ASTEROID_AUDIT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    program = " ".join(read(TEST_PERFORMANCE_PROGRAM).split())

    for phrase in (
        "First drawable asteroid audit (Milestone 50A.3A)",
        "Accepted by Fernando on 2026-09-11",
        "Use **(1) Ceres**",
        "Apophis remains a numerical parallax oracle",
        "descriptor-aware source binding",
        "must not branch on `asteroid`",
        "sky/solar_system/minor_bodies/asteroids/ceres",
        "--minor-body-resource-directory PATH",
        "acquisition-report.json",
        "must not reopen the SPK per epoch",
        "--asteroid ceres",
        "--asteroid-track ceres",
        "small hollow diamond",
        "No magnitude field is admitted in 50A.3B",
        "Do not repeat 50A.2 CSPICE interpolation",
        "no user-guide or example edit is required yet",
        "No diagram edit is required by this audit",
        "Future field-planning compatibility",
        "OmegaCAM/Paranal use case",
        "current OMM or legacy TLE",
        "SGP4 evaluation in TEME",
        "must not be forced through the minor-body SPK/TDB/light-time provider",
        "collection of one or more targets and many sample instants",
        "result will be a risk estimate, not a guarantee of a clean exposure",
    ):
        assert phrase in audit

    assert "50A.3A is accepted and archived" in roadmap
    assert "is the accepted contract" in implementation
    assert "50A.3A first-drawable-asteroid audit ownership" in source_tree
    assert "Follow the accepted 50A.3A audit" in instructions
    assert "13.2.39 50A.3A first drawable asteroid audit" in guide
    assert "future collection-of-trajectories seam" in guide
    assert "WCS/mosaic footprint" in guide
    assert "50A.3A accepted by Fernando" in program


def test_50a3b_connects_only_manifest_backed_ceres_through_shared_routes():
    record = " ".join(read(DRAWABLE_CERES).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    architecture = " ".join(read(V09_CURRENT).split())
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    guide = " ".join(read(COORDINATE_GUIDE).split())
    program = " ".join(read(TEST_PERFORMANCE_PROGRAM).split())
    user_configuration = " ".join(
        read(ROOT / "docs/user_guide/configuration.md").split()
    )
    examples = " ".join(read(ROOT / "docs/user_guide/chart_examples.md").split())
    diagram_index = " ".join(read(DIAGRAMS / "README.md").split())
    dot = read(DIAGRAMS / "drawable_ceres_50a3b.dot")
    svg = read(DIAGRAMS / "drawable_ceres_50a3b.svg")

    for phrase in (
        "Drawable Ceres point and track (Milestone 50A.3B)",
        "Accepted by Fernando on 2026-09-11",
        "--asteroid ceres",
        "--asteroid-track ceres",
        "sky/solar_system/minor_bodies/asteroids/ceres",
        "EphemerisSourceBinding",
        "MinorBodyResourceSession",
        "opens the Ceres kernel at most once",
        "closes it exactly once",
        "Rendering never downloads",
        "fixed small hollow diamond",
        "no magnitude or angular-size meaning",
        "Artificial satellites may later share",
        "do not repeat 50A.2 CSPICE interpolation",
        "rejected the duplicated Ceres/start-date labels",
        "same body and instant as the track start",
        "single visible label `Ceres (1)` without a date",
        "opposite the initial projected direction of motion",
        "planetary cream `#FFE6A3`",
        "final complete repository gate passed all 2,184 tests",
        "88.01 seconds",
        "accepted the regenerated PNG and SVG",
        "This closes 50A.3",
    ):
        assert phrase in record

    assert "50A.3B is accepted and archived" in roadmap
    assert "Drawable Ceres point and track" in architecture
    assert "Drawable Ceres resource binding" in implementation
    assert "50A.3B drawable-Ceres ownership" in source_tree
    assert "bounded implementation is accepted and archived" in instructions
    assert "13.2.40 50A.3B drawable Ceres point and track" in guide
    assert "50A.3B is accepted and archived" in program
    assert "Ceres point and dated track" in user_configuration
    assert "--minor-body-resource-directory" in user_configuration
    assert "--asteroid-track ceres" in examples
    assert "50A.3B drawable-Ceres" in diagram_index
    for phrase in (
        "Ceres point and/or track",
        "Local manifest + Ceres SPK",
        "Descriptor-aware source binding",
        "Canonical output",
    ):
        assert phrase in dot
        assert phrase in svg


def test_50a3c_audits_generic_numbered_asteroids_before_comets():
    audit_path = (
        ARCHIVE / "milestone_history"
        / "50a_minor_bodies"
        / "numbered_asteroid_generalization_audit_50a3c.md"
    )
    audit = " ".join(read(audit_path).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    program = " ".join(read(TEST_PERFORMANCE_PROGRAM).split())

    for phrase in (
        "Numbered-asteroid generalization audit (Milestone 50A.3C)",
        "Accepted by Fernando on 2026-09-11",
        "permanent minor-planet number",
        "manifest-declared official name",
        "classifications, not distinct number spaces",
        "must not derive it arithmetically",
        "--asteroid 79989",
        "--asteroid-track 79989",
        "`--asteroid vesta`",
        "one descriptor whose stable identity is the permanent number",
        "case-folded for exact lookup",
        "fuzzy, locale-dependent",
        "Rendering remains explicit and offline",
        "manifest, not a Python module named for each asteroid",
        "request-owned extensions",
        "must not mutate the process-global built-in catalog",
        "Ceres (1)",
        "unnamed object: `(79989)`",
        "exact local lookup alias for the permanent number",
        "after an explicit resource refresh",
        "asteroids/79989/track",
        "no fewer than three epochs",
        "topocentric parallax",
        "no code may branch on `79989`",
        "Comet numerical validation remains 50A.4",
    ):
        assert phrase in audit

    assert "accepted 50A.0 through 50A.3C records" in index
    assert "accepted the bounded 50A.3C generalization audit" in roadmap
    assert (
        "numbered_asteroid_generalization_audit_50a3c.md`"
        in instructions
    )
    assert "50A.3C was accepted by Fernando" in program
    assert "50A.3B was accepted" in program


def test_50a3c_audit_changes_no_runtime_user_guide_or_diagram_contract():
    audit = " ".join(read(
        ARCHIVE / "milestone_history"
        / "50a_minor_bodies"
        / "numbered_asteroid_generalization_audit_50a3c.md"
    ).split())

    for phrase in (
        "This audit changes no runtime behavior",
        "Ceres remains the only currently drawable asteroid",
        "no user-guide example or architecture diagram changes in 50A.3C",
        "coordinate-system guide is reviewed",
        "does not admit provisional-only asteroids",
        "uninstalled or fuzzy name search",
        "confuse minor-planet numbers with periodic-comet numbers",
        "acceptance authorizes only the bounded 50A.3D",
    ):
        assert phrase in audit


def test_50a3d_documents_request_owned_installed_numbered_asteroids():
    record = " ".join(
        read(MINOR_BODY_HISTORY / "numbered_asteroids_50a3d.md").split()
    )
    implementation = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    guide = " ".join(read(COORDINATE_GUIDE).split())
    user_configuration = " ".join(
        read(ROOT / "docs/user_guide/configuration.md").split()
    )
    dot = read(DIAGRAMS / "numbered_asteroids_50a3d.dot")
    svg = read(DIAGRAMS / "numbered_asteroids_50a3d.svg")
    acquisition_tool = read(ROOT / "tools/acquire_numbered_asteroids.py")
    acquisition = read(ROOT / "src/wenu/minor_body_acquisition.py")

    for phrase in (
        "Generic numbered asteroids (Milestone 50A.3D)",
        "Accepted and merged to `main` before PR 98",
        "permanent number or an exact, case-folded official name",
        "Rendering remains offline",
        "`(79989)` is the acceptance specimen, not a special runtime case",
        "without mutating the built-in catalog",
        "`Name (number)` for named objects and `(number)` for unnamed",
        "unnamed main-belt asteroid `1999 FH1`",
        "internal layer is therefore `asteroid_79989`",
        "visibility is selected by the descriptor's public selection key",
        "SVG-only hierarchy-label conflict",
        "Fernando visually accepted the 7.5-degree binocular PNG and semantic SVG",
        "one `(79989)` label",
        "three epochs across 2026, 2027, and 2029",
        "`1.2029932605628346e-11 au`",
        "`3.6855067608865255e-14 au/day`",
        "`7.085531775067114e-08 deg`",
        "`2e-11 au` position tolerance",
        "does not change the accepted 50A.2 default of `5e-12 au`",
        "The enforcing run reported `accepted: true`",
        "focused minor-body, request, track, and documentation gate passed all 206 tests",
        "coincident Ceres label had changed",
        "omitted from the explicit optional-layer closure",
        "passed 7 tests in 2.49 seconds",
        "1 test in 1.93 seconds",
        "final complete repository gate passed all 2,201 tests",
        "81.36 seconds",
        "accepted the completed numerical, visual, focused-test, and full-suite evidence",
    ):
        assert phrase in record

    validator = read(ROOT / "tools/validate_50a2_asteroids.py")
    fixture = read(
        ROOT
        / "tests/fixtures/horizons_numbered_asteroid_validation_50a3d.json"
    )
    assert 'reference.get("tolerances", {})' in validator
    assert '"position_au": 2e-11' in fixture
    assert '"--characterize"' in validator
    assert '"accepted": not characterize' in validator

    assert "MinorBodyResourceCollection" in implementation
    assert "request-owned descriptor" in guide
    assert "--asteroid 79989" in user_configuration
    assert "official name" in user_configuration
    assert "permanent-number identity" in dot
    assert "request-owned installed asteroid" in svg
    assert "HORIZONS_API" in acquisition
    assert "SBDB_API" in acquisition
    assert "acquire_numbered_asteroids" in acquisition_tool


def test_user_guide_documents_every_chart_family_with_runnable_examples():
    index = " ".join(read(ROOT / "docs/user_guide/index.md").split())
    examples = read(ROOT / "docs/user_guide/chart_examples.md")
    configuration = read(ROOT / "docs/user_guide/configuration.md")
    temporal = read(ROOT / "docs/user_guide/temporal_sequences.md")

    assert "# Wenu v0.9.5 user guide" in index
    assert "five ordinary chart families and six canonical example scripts" in index
    assert "[runnable examples for every chart family](chart_examples.md)" in index

    for heading, command in (
        ("## Galactic all-sky map", "wenu_chart all-sky"),
        ("## Visible-sky planisphere", "wenu_chart planisphere"),
        ("## Regional chart", "wenu_chart regional"),
        ("## Circumpolar chart", "wenu_chart circumpolar"),
        ("## Binocular chart", "wenu_chart binocular"),
    ):
        assert heading in examples
        assert command in examples

    for script in (
        "examples/all_sky.py",
        "examples/planisphere.py",
        "examples/regional_constellation.py",
        "examples/regional_constellation_group.py",
        "examples/circumpolar.py",
        "examples/binocular_object.py",
    ):
        assert script in examples

    assert "--field-diameter 7.5" in examples
    assert "--magnitude-limit 11" in examples
    assert "--moon --moon-disk-magnification 8" in examples
    assert "[complete chart examples](chart_examples.md)" in configuration
    assert "Observed Moon disks within one fixed chart are supported separately" in temporal


def test_active_cli_documentation_matches_schema_v2_and_explicit_centers():
    root_readme = read(ROOT / "README.md")
    regional = read(ROOT / "docs/user_guide/regional_charts.md")
    all_sky = read(ROOT / "docs/user_guide/all_sky.md")
    planisphere = read(ROOT / "docs/user_guide/planisphere.md")
    configuration = read(ROOT / "docs/user_guide/configuration.md")
    architecture = read(V09_CURRENT)
    audit = read(MINOR_BODY_HISTORY / "chart_cli_semantics_audit_50a3f.md")
    acceptance = read(MINOR_BODY_HISTORY / "cli_contract_acceptance_50a3g.md")
    defaults = tomllib.loads(read(
        ROOT / "src/wenu/configuration/defaults.toml"
    ))

    for text in (root_readme, regional, architecture, audit, acceptance):
        assert "drawing selectors never supply a center" in text.lower() or (
            "content selector never changes the center" in text.lower()
        ) or "content but never change the center" in text.lower() or (
            "never become the center merely because" in text.lower()
        ) or (
            "no content selector changes the center" in text.lower()
        )
    assert "one selected\nplanet, Moon, or installed asteroid supplies" not in regional
    assert "`--group ALIAS`" not in all_sky
    assert "`--group ALIAS`" not in planisphere
    assert "version-1" not in configuration
    assert "Version 1" not in configuration
    assert "implementation pending" not in audit
    assert defaults["schema_version"] == 2
    assert defaults["constellations"]["system"] == "western"
    assert "subjects" not in defaults
    assert all(
        value["constellations"] == []
        for value in defaults["masks"].values()
    )


def test_50a5b1_records_shared_temporal_component_closure():
    audit = read(MINOR_BODY_HISTORY / "solar_system_temporal_components_audit_50a5b1.md")
    guide = read(DEVELOPER / "coordinate_system_guide_v0.9.5.md")
    roadmap = read(DEVELOPER / "post_v0.9_architecture_roadmap.md")
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Scientifically, architecturally, visually, operationally, and",
        "complete 2,331-test suite in 84.56 seconds",
        "this closes\n50A.5B.1",
    ):
        assert phrase.lower() in audit.lower()
    assert "Accepted 50A.5B.1 adds no coordinate or product frame" in guide
    assert "closing\n50A.5B.1" in roadmap
    assert "temporal_components.py" in source_tree


def test_50a5c_audits_a_second_comet_before_minor_body_closure():
    audit = read(MINOR_BODY_HISTORY / "second_drawable_comet_audit_50a5c.md")
    roadmap = read(DEVELOPER / "post_v0.9_architecture_roadmap.md")
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Accepted by Fernando on 2026-09-13",
        "161P/Hartley-IRAS",
        "Characterization must precede tolerance selection",
        "Provider `PsAng` has precedence",
        "one target evaluation per track sample",
        "performs no network access",
        "general comet catalogue, live service",
        "Implemented identity checkpoint",
        "Horizons record `90001107`",
        "NAIF\ntarget `1000042`",
        "both numerical and antisolar tolerances explicitly null",
        "common Encke-and-161P direction envelope",
        "`0.036 arcsec`",
        "install_comet_resource.py",
        "atomic publication",
        "complete Mac\nregression gate passed all 2,346 tests",
        "This closes 50A.5C",
    ):
        assert phrase.lower() in audit.lower()
    assert "Accepted 50A.5C uses 161P/Hartley-IRAS" in roadmap
    assert "bounded evidence acquisition" in source_tree
    assert "acquire_50a5c_comet_identity.py" in source_tree
    assert "acquire_50a5c_comet_evidence.py" in source_tree
    assert "build_50a5c_comet_fixture.py" in source_tree
    assert "validate_50a5c_comet.py" in source_tree
    assert "horizons_comet_validation_50a5c.json" in source_tree
    assert "generic offline comet installer" in source_tree
    assert "Milestone 50A.5C is\nclosed" in roadmap


def test_50a5d_audits_comet_discovery_acquisition_and_reports():
    audit = " ".join(read(
        DEVELOPER / "comet_discovery_and_reporting_audit_50a5d.md"
    ).split())

    for phrase in (
        "Accepted by Fernando on 2026-09-13",
        "This audit changes no runtime code",
        "wenu_retrieve_comets START STOP",
        "perihelion instant `tp` lies within the closed input interval",
        "It is not a visibility forecast",
        "provider's comet photometric parameters",
        "provider-trusted operational path",
        "P`, `D`, `I`, `C`, `X`, `A`",
        "10P/Tempel 2",
        "one report pair",
        "SolarSystemTrackResult",
        "must not repeat an ephemeris calculation",
        "mu_RA* = cos(dec) dRA/dt",
        "total sky-plane speed",
        "some request `dRA/dt`, others request `mu_RA*`",
        "artificial satellites remain outside",
        "Fernando accepted it on 2026-09-13 with the observed-angular-rate addition, authorizing only 50A.5D.1",
    ):
        assert phrase.lower() in audit.lower()


def test_50a5d1a_documents_bounded_deterministic_comet_discovery():
    implementation = " ".join(read(
        MINOR_BODY_HISTORY / "comet_discovery_50a5d1a.md"
    ).split())
    roadmap = read(DEVELOPER / "post_v0.9_architecture_roadmap.md")
    reference = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")
    coordinate_guide = " ".join(read(
        DEVELOPER / "coordinate_system_guide_v0.9.5.md"
    ).split())
    user_guide = " ".join(read(
        ROOT / "docs/user_guide/comet_discovery.md"
    ).split())
    project = read(ROOT / "pyproject.toml")

    for phrase in (
        "Accepted by Fernando on 2026-09-13",
        "complete inclusive UTC civil days",
        "not a visibility forecast",
        "sampling policy to a separately reviewed 50A.5D.1B",
        "does not implement `--observer-location`, model apparent magnitude, comet acquisition, chart preflight, reports",
    ):
        assert phrase in implementation
    assert "50A.5D.1A accepted by Fernando on 2026-09-13" in roadmap
    assert "Deterministic comet discovery" in reference
    assert "50A.5D.1A deterministic comet-discovery ownership" in source_tree
    assert "Returned `tp` values retain their TDB identity" in coordinate_guide
    for phrase in (
        "not a visibility forecast",
        "m_1 = M_1 + 5\\log_{10}(\\Delta) + K_1\\log_{10}(r)",
        "M1` is therefore the reference total magnitude",
        "K1` is not a magnitude",
        "not stellar absolute magnitudes defined at 10 parsecs",
        "deferred to the separately reviewed 50A.5D.1B",
    ):
        assert phrase in user_guide
    assert 'wenu_retrieve_comets = "wenu.cli.comets:main"' in project


def test_50a5d2a_audits_exact_comet_name_resolution():
    audit = " ".join(read(
        MINOR_BODY_HISTORY / "comet_name_resolution_audit_50a5d2a.md"
    ).split())
    roadmap = " ".join(read(
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).split())

    for phrase in (
        "Accepted by Fernando on 2026-09-13",
        "provider-backed exact comet identity",
        "case-folded after trimming and collapsing whitespace",
        "`10P/Tempel 2` may resolve to the same identity as `10P`",
        "`Tempel` is not an exact alias",
        "`10` is not `10P`",
        "No failure falls back to the first provider row",
        "tests/test_minor_body_identity.py",
        "production code may contain no `10P` conditional",
        "authorizes only the identity resolver",
    ):
        assert phrase in audit

    assert "accepted 50A.5D.2A audit" in roadmap
    assert "SPK acquisition" in roadmap

    for phrase in (
        "Accepted generic-core amendment",
        "resolve_minor_body_identity(selection, expected_class=...)",
        "mandatory and accepts only `comet` or `asteroid`",
        "does not connect asteroid names to the chart CLI",
        "Accepted by Fernando on 2026-09-13 after the focused Mac gate passed all 150 tests",
        "complete Mac regression passed all 2,380 tests in 89.08 seconds",
    ):
        assert phrase in audit

    reference = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")
    assert "Exact minor-body identity resolution" in reference
    assert "minor_body_identity.py" in source_tree
    assert "tests/test_minor_body_identity.py" in source_tree


def test_50a5d2b_audits_generic_comet_acquisition():
    audit = " ".join(read(
        MINOR_BODY_HISTORY / "comet_acquisition_audit_50a5d2b.md"
    ).split())
    roadmap = " ".join(read(
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).split())
    source_tree = " ".join(read(
        DEVELOPER / "source_tree.md"
    ).split())

    for phrase in (
        "Accepted by Fernando on 2026-09-13",
        "one already resolved comet identity",
        "does not yet connect acquisition to `wenu_chart`",
        "must not derive a Horizons record number arithmetically",
        "unique provider record, apparition when applicable",
        "must not silently select the first, latest",
        "solar-system centre `10`",
        "SPK segment type `21`",
        "Wenu neither reapplies nor removes those terms",
        "`offline` performs no network access",
        "Connecting exact comet selections and these policies to `wenu_chart` is deferred to 50A.5D.2C",
        "load unchanged through `MinorBodyResourceCollection`",
        "Extend `tests/test_minor_body_acquisition.py`",
        "Production code may contain no `10P` conditional",
        "authorizes only the bounded 50A.5D.2B acquisition service",
    ):
        assert phrase in audit

    assert "accepted 50A.5D.2B audit isolates the shared acquisition service" in roadmap
    assert "50A.5D.2B generic comet-acquisition audit ownership" in source_tree
    assert "no coordinate or product-frame meaning changes" in audit
    assert "This slice changes data availability and provenance only" in audit
    assert "does not authorize 50A.5D.2C CLI preflight integration" in audit
    assert "focused documentation gate passed all 114 tests" in audit
    assert "complete Mac regression passed all 2,381 tests in 87.20 seconds" in audit
    for phrase in (
        "Accepted implementation",
        "acquire_minor_body_resources()",
        "ensure_minor_body_resources()",
        "DES=<designation>;CAP;NOFRAG",
        "Horizons API version 1.2",
        "one type-21 target segment",
        "record `90000214`",
        "solution `JPL#K265/50`",
        "JD 2461284.5 through 2461344.5",
        "Implementation status:** Accepted by Fernando on 2026-09-13",
        "accepted the bounded 50A.5D.2B implementation on 2026-09-13",
        "This closes only the shared acquisition service",
        "Mac acceptance run acquired `10P/Tempel 2`",
        "reused the identical immutable resource under `offline`",
        "focused gate passed all 169 tests in 4.09 seconds",
        "complete Mac regression passed all 2,388 tests in 91.98 seconds",
    ):
        assert phrase in audit
    reference = read(DEVELOPER / "implementation_reference.md")
    assert "Resolved minor-body acquisition" in reference
    assert "accepted the bounded 50A.5D.2B acquisition-service implementation" in roadmap
    assert "CLI integration remains 50A.5D.2C" in roadmap


def test_50a5d2c_audits_exact_comet_cli_preflight():
    audit = " ".join(read(
        MINOR_BODY_HISTORY / "comet_cli_preflight_audit_50a5d2c.md"
    ).split())
    roadmap = " ".join(read(
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).split())
    source_tree = " ".join(read(
        DEVELOPER / "source_tree.md"
    ).split())

    for phrase in (
        "Accepted by Fernando on 2026-09-13",
        "request-level composition",
        "`--comet SELECTION`",
        "`--comet-track SELECTION`",
        "`--center-on comet:SELECTION`",
        "Provider-backed uninstalled center resolution requires the explicit",
        "`--asteroid Hygiea` remains outside",
        "one verified collection rather than acquire per-class directories",
        "remains authoritative and offline",
        "warm cache adequate for the full request performs no SBDB or Horizons access",
        "one closed TDB acquisition interval",
        "No network access may occur after chart construction begins",
        "Libraries do not print",
        "Production code may contain no special `10P`",
        "No failure falls back to the first provider result",
        "Extend existing owners rather than add a milestone-specific test module",
        "mixed asteroid-and-comet preflight uses one verified collection",
        "authorizes only the 50A.5D.2C exact comet CLI",
        "does not authorize observer-dependent comet magnitude",
        "focused current-documentation gate passed all 115 tests in 2.84 seconds",
        "updated 115-test documentation gate in 2.62 seconds",
        "complete 2,389-test regression in 82.59 seconds",
        "authorizes only implementation of the request-level exact",
        "Independent C/2021 T4 (Lemmon) comparison",
        "earthsky.org/astronomy-essentials/comet-c-2021-t4-lemmon-is-sweeping-southern-skies",
        "opposition on July 18",
        "declination -56 degrees on July 20",
        "an ecliptic crossing on September 10",
        "ordering, turning geometry, and constellation progression",
        "qualitative external acceptance comparison, not a numerical oracle",
        "must not be converted into artificial sub-degree regression tolerances",
        "existing direct-Horizons fixtures remain the numerical authority",
    ):
        assert phrase in audit

    assert "accepted 50A.5D.2C audit isolates exact comet CLI preflight" in roadmap
    assert (
        "50A.5D.2C exact comet CLI-preflight ownership "
        "(candidate implementation)" in source_tree
    )
    assert "one effective resource directory before sphere construction" in (
        source_tree
    )
    assert "introduces no coordinate system, origin, frame, epoch, equinox" in audit

def test_50a5d1b_audits_observer_dependent_comet_model_magnitude():
    audit = " ".join(read(
        DEVELOPER / "comet_model_magnitude_audit_50a5d1b.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    roadmap = " ".join(read(
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).split())

    for phrase in (
        "Accepted by Fernando on 2026-09-14",
        "authorizes only the bounded 50A.5D.1B implementation",
        "brightest sampled total model magnitude",
        "not a visibility forecast",
        "T-mag = M1 + 5 log10(delta) + k1 log10(r)",
        "N-mag = M2 + 5 log10(delta) + k2 log10(r) + phcof beta",
        "uncertain at roughly 1 magnitude in practice",
        "sequential rather than simultaneous API calls",
        "--magnitude-step DURATION",
        "positive whole number of hours or days",
        "proposed default is `1d`",
        "numerically smallest valid sampled `T-mag`",
        "nuclear magnitude is not substituted",
        "Unknown values sort after all known values",
        "at most 50 selected comet solutions",
        "at most 367 sample epochs per comet",
        "recommended first implementation is fail-whole",
        "not the minor-body SPK cache",
        "must not import chart, renderer, projection",
        "Extend it rather than creating a milestone-named test file",
        "the default cadence is `1d`",
        "367 sample epochs per comet and 50",
        "any Horizons failure fails the whole result",
        "same inclusive `START`/`STOP` interval",
        "does not authorize visibility prediction",
    ):
        assert phrase in audit

    assert "comet_model_magnitude_audit_50a5d1b.md" in index
    assert "accepted the 50A.5D.1B audit on 2026-09-14" in roadmap

def test_assistant_instructions_require_documentation_contract_preflight():
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Documentation-contract preflight",
        "exact top-level-file allowlist",
        "search for every exact-phrase assertion",
        "Never write a documentation assertion from memory",
        "verify after whitespace normalization",
        "developer-document index, resulting filesystem set, roadmap links",
        "Inspect the resulting branch contents",
        "every required edit actually applied",
        "Do not present the branch for Mac testing",
    ):
        assert phrase in instructions

def test_assistant_instructions_govern_production_module_placement():
    instructions = " ".join(read(INSTRUCTIONS).split())
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Source-tree alignment and production-module admission",
        "durable architectural responsibility",
        "closest existing owner",
        "same responsibility, dependencies, lifecycle, and reason to change",
        "distinct scientific or provider responsibility",
        "Create a subpackage when a coherent domain requires several collaborating modules",
        "not milestone number, CLI option, first specimen",
        "genuinely body-specific science",
        "never for copied orchestration, projection, rendering, or export",
        "Do not place domain behavior in `utils`",
        "File size alone neither requires nor justifies splitting",
        "intentional public or compatibility exports",
        "update `source_tree.md` whenever ownership or placement changes",
        "Keep structural reorganization separate from behavioral implementation",
        "Every new production file proposal must name the closest existing owner",
    ):
        assert phrase in instructions

    assert "├── resources.py                installed-resource access" in source_tree
    assert "├── resources/                  installed-resource access" not in source_tree

def test_50s1_documents_provider_neutral_satellite_crossing_domain():
    roadmap = " ".join(read(
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).split())
    guide = " ".join(read(DEVELOPER / "satellite_guide.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(
        DEVELOPER / "coordinate_system_guide_v0.9.5.md"
    ).split())

    for phrase in (
        "Accepted by Fernando on 2026-09-15; merged through PR #123",
        "explicitly framed closed circular FoV",
        "provider acquisition, propagation, charts, projection, rendering",
        "Spherical rectangles, WCS/instrument footprints",
        "SatChecker adaptation",
    ):
        assert phrase in roadmap

    for phrase in (
        "The 50S.1 admission review found no existing owner",
        "satellite_crossings.py",
        "SatelliteCrossingCandidate",
        "one connected visit",
        "accepts boundary touch",
        "src/wenu/satellites/",
    ):
        assert phrase in guide

    assert "advanced domain contracts" in reference
    assert "include both endpoints" in reference
    assert "Boundary touch is a valid zero-duration crossing" in reference
    assert "50S.1 provider-neutral satellite-crossing ownership" in source_tree
    assert "tests/test_satellite_crossings.py" in source_tree
    assert "adds no TEME state" in coordinate_guide
    assert "one chart observation instant" in coordinate_guide
    assert "dormant `satellite_crossings.py` domain boundary" in architecture
    assert "No satellite acquisition, orbit solution, propagation" in architecture
    for text in (
        roadmap,
        guide,
        architecture,
        reference,
        source_tree,
        coordinate_guide,
    ):
        assert "2,428 tests" in text
        assert "23b851b" in text


def test_50s2a_audits_satchecker_provider_contract_before_adapter():
    audit = " ".join(read(
        DEVELOPER / "satchecker_provider_contract_audit_50s2a.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    roadmap = " ".join(read(
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).split())
    guide = " ".join(read(DEVELOPER / "satellite_guide.md").split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(
        DEVELOPER / "coordinate_system_guide_v0.9.5.md"
    ).split())

    for phrase in (
        "This audit changes no runtime code",
        "normalize successful provider output only to `SatelliteCrossingCandidate`",
        "It must not construct `SatelliteCrossingResult`",
        "one-second grid with `numpy.arange`",
        "exclude the computed stop endpoint",
        "explicit UTC-to-UT1 conversion",
        "never trigger a hidden IERS download",
        "outside Wenu's closed requested FoV",
        "no parallel submissions, no automatic retry, and no hidden polling loop",
        "Corrupt, partial, mismatched, or obsolete-schema entries fail closed",
        "must not be committed, packaged, or redistributed",
        "Ordinary tests use synthetic source-shaped specimens",
        "Accepted by Fernando on 2026-09-15",
        "acceptance authorizes only the bounded 50S.2B cached-adapter implementation",
    ):
        assert phrase in audit

    assert "satchecker_provider_contract_audit_50s2a.md" in index
    assert "50S.2A — SatChecker provider-contract audit" in roadmap
    assert "candidate envelope and sampled evidence" in guide
    assert "50S.2A SatChecker provider-contract audit ownership (accepted)" in source_tree
    assert "one-second sampling grid excludes the stop endpoint" in coordinate_guide
    assert "Fernando accepted this scientific boundary on 2026-09-15" in coordinate_guide


def test_50s2b_documents_cached_satchecker_adapter_candidate():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    audit = " ".join(read(
        DEVELOPER / "satchecker_provider_contract_audit_50s2a.md"
    ).split())
    guide = " ".join(read(DEVELOPER / "satellite_guide.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "dormant `satchecker.py` provider boundary",
        "one-shot `submit()` and `poll()` operations",
        "does not create `SatelliteCrossingResult`",
        "Only 50S.3 reporting and drawing is authorized next",
    ):
        assert phrase in architecture
    for phrase in (
        "50S.2B status:** Accepted by Fernando on 2026-09-15",
        "content-addressed exact local cache",
        "No waiter loop, automatic retry, CLI, live fixture",
    ):
        assert phrase in roadmap
    for phrase in (
        "SatChecker crossing candidates",
        "Neither function retries, waits, loops, or runs concurrently",
        "No exact `SatelliteCrossingResult` is synthesized",
    ):
        assert phrase in reference
    assert "50S.2B SatChecker adapter ownership (accepted)" in (
        source_tree
    )
    assert "tests/test_satchecker.py" in source_tree
    assert "Astropy IERS automatic download is disabled" in coordinate_guide
    assert "Candidate 50S.2B implementation" in audit
    assert "accepted 50S.2B provider module is `satchecker.py`" in guide
    assert "satchecker_provider_contract_audit_50s2a.md" in instructions


def test_50s2b_records_bounded_live_provider_normalization():
    audit = " ".join(read(
        DEVELOPER / "satchecker_provider_contract_audit_50s2a.md"
    ).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    guide = " ".join(read(DEVELOPER / "satellite_guide.md").split())

    for phrase in (
        "Bounded live transport evidence",
        "failed before network access",
        "degraded accuracy was not enabled",
        "Exactly one versioned FOV submission returned HTTP 200 and PENDING",
        "Two separate explicit polls returned the same PENDING message",
        "No retry, replacement submission, concurrent access",
        "A later third explicit poll reached SUCCESS",
        "normalized 13 distinct NORAD identities and 26 ordered samples",
        "without constructing an exact connected visit",
    ):
        assert phrase in audit
    assert "SUCCESS receipt normalized to 13 candidates and 26 ordered samples" in (
        roadmap
    )
    assert "normalized 13 candidates and 26 ordered samples" in guide


def test_50s2b_records_accepted_implementation_and_gates():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    audit = " ".join(read(
        DEVELOPER / "satchecker_provider_contract_audit_50s2a.md"
    ).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())

    for text in (
        architecture,
        roadmap,
        reference,
        coordinate_guide,
        audit,
        guide,
    ):
        assert "2026-09-15" in text
    assert "all 2,457 tests in 88.48 seconds" in architecture
    assert "accepted 50S.3A now authorizes only bounded 50S.3B" in roadmap
    assert "accepted the bounded 50S.2B API and ownership" in reference
    assert "50S.2B SatChecker adapter ownership (accepted)" in source_tree
    assert "50S.2B acceptance" in audit
    assert "This closes only the cached SatChecker adapter" in audit
    assert "only the bounded 50S.3B implementation is authorized next" in guide



def test_50s3a_audits_sampled_candidate_reports_and_shared_path_drawing():
    audit = " ".join(read(
        DEVELOPER / "satellite_report_drawing_audit_50s3a.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())

    for phrase in (
        "This documentation-only audit",
        "provider-sampled candidate evidence, not a verified connected FoV crossing",
        "must not be used as a false type for provider samples",
        "SatChecker sampled candidate evidence — not verified crossings",
        "must not reparse provider JSON",
        "Candidate ordering is by NORAD catalogue identifier",
        "Two or more samples produce one open spherical polyline",
        "One sample produces one point marker",
        "No interpolation, extrapolation, smoothing, resampling",
        "sky/artificial_satellites/satchecker_candidates/norad_<catalogue_id>/sampled_track",
        "PNG, PDF, and SVG must all be produced by the same realized layer",
        "adds no CLI acquisition workflow",
        "authorizes only the bounded 50S.3B implementation",
        "Accepted by Fernando on 2026-09-15",
        "focused documentation gate passed all 126 tests",
    ):
        assert phrase in audit

    assert "satellite_report_drawing_audit_50s3a.md" in index
    assert "50S.3A — Satellite report and drawing contract audit" in roadmap
    assert "50S.3B — SatChecker sampled-candidate reports and tracks" in roadmap
    assert "only the bounded 50S.3B implementation is authorized next" in guide
    assert "50S.3A satellite report and drawing contract audit ownership (accepted)" in source_tree
    assert "Connecting ordered provider samples is presentation" in coordinate_guide



def test_50s3b_documents_candidate_reports_and_shared_path_layers():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_report_drawing_audit_50s3a.md"
    ).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "50S.3B sampled-candidate presentation boundary (accepted)",
        "satellite_presentations.py",
        "SatelliteCandidateTrackLayer",
        "SatelliteCandidateSamplesLayer",
        "No entry, exit, closest approach, interpolation",
    ):
        assert phrase in architecture
    for phrase in (
        "50S.3B — SatChecker sampled-candidate reports and tracks",
        "Accepted by Fernando on 2026-09-15",
        "shared PNG/PDF/SVG pipeline gate",
        "does not synthesize exact crossing events",
    ):
        assert phrase in roadmap
    for phrase in (
        "SatChecker sampled-candidate presentations",
        "SatChecker sampled candidate evidence — not verified crossings",
        "SUCCESS evidence is sorted by full NORAD catalogue identifier",
        "one sample becomes one",
        "perform no network access",
    ):
        assert phrase in reference
    assert "50S.3B satellite presentation ownership (accepted)" in source_tree
    assert "tests/test_satellite_presentations.py" in source_tree
    assert "fixed-product-frame track convention" in coordinate_guide
    assert "position generation" in coordinate_guide
    assert "Accepted 50S.3B implementation evidence" in audit
    assert "expanded focused gate passed all 90 tests" in audit
    assert "Accepted 50S.3B implementation" in guide
    assert "There is no entry, exit, closest approach" in guide
    assert "satellite_report_drawing_audit_50s3a.md" in instructions
    assert "tools/validate_50s3b_satellite_presentations.py" in source_tree
    assert "Fernando visually accepted" in architecture
    assert "centered FoV chart across PNG" in roadmap
    assert "four UTC annotations" in guide
    assert "FoV was labelled explicitly" in audit
    assert "all 217 tests" in architecture
    assert "all 2,473 tests in 83.98 seconds" in architecture
    assert "authorizes only 50S.4 next" in roadmap
    assert "only the documentation-only 50S.4A audit is authorized next" in guide
    assert "complete plugin-disabled suite passed all 2,473 tests" in audit
    assert "accepted the bounded 50S.3B implementation on 2026-09-15" in audit
    assert "Only 50S.4 is authorized next" in source_tree



def test_50s4a_audits_snapshot_propagation_and_topocentric_contracts():
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_propagation_audit_50s4a.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "This documentation-only audit",
        "50S.4B — immutable OMM snapshot and element domain",
        "50S.4C — validated SGP4/TEME propagation",
        "50S.4D — Earth-orientation and topocentric state chain",
        "50S.4E — developer specimen builder and closure",
        "sgp4>=2.25,<3",
        "Do not rely on Skyfield's transitive dependency",
        "WGS-72 is mandatory",
        "CCSDS 502.0-B-3",
        "synthetic and non-operational",
        "No live CelesTrak, Space-Track, or SatChecker response is committed",
        "split Julian date parts",
        "geocentric geometric TEME",
        "Astropy IERS automatic download remains disabled",
        "degraded accuracy is never enabled silently",
        "aberration-bearing result “geometric ICRS”",
        "Agreement between two paths using the same hidden inputs is not independent evidence",
        "propagated sampled specimens — not verified crossings",
        "It cannot emit",
        "Acceptance closes 50S.4A and authorizes only 50S.4B immutable OMM element",
    ):
        assert phrase in audit

    assert "satellite_snapshot_propagation_audit_50s4a.md" in index
    assert "Accepted 50S.4A snapshot and propagation audit" in architecture
    for phrase in (
        "50S.4A — Snapshot and propagation contract audit",
        "50S.4B — Immutable OMM element snapshot",
        "50S.4C — Validated SGP4/TEME propagation",
        "50S.4D — Earth-orientation and topocentric state",
        "50S.4E — Propagated specimen builder and closure",
    ):
        assert phrase in roadmap
    assert "50S.4 snapshot and propagation admission review" in guide
    assert "only 50S.4B immutable OMM element and snapshot work is authorized next" in guide
    assert "50S.4A snapshot and propagation contract audit ownership (accepted)" in source_tree
    assert "TEME and topocentric transformation admission note" in coordinate_guide
    assert "not automatically an ICRS astrometric position" in coordinate_guide
    assert "satellite_snapshot_propagation_audit_50s4a.md" in instructions
    assert "Accepted by Fernando on 2026-09-15" in audit
    assert "focused documentation gate passed all 128 tests" in audit
    assert "branch diff check was clean" in audit
    assert "authorizes only 50S.4B immutable OMM element and snapshot work" in roadmap


def test_50s4b_documents_immutable_omm_snapshot_boundary():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_propagation_audit_50s4a.md"
    ).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Accepted 50S.4B immutable element snapshot",
        "canonical-byte and record-level SHA-256 verification",
        "synthetic_50s4b_v1",
        "adds no propagator construction",
    ):
        assert phrase in architecture
    assert "50S.4B — Immutable OMM element snapshot" in roadmap
    for phrase in (
        "Local satellite elements and snapshots (50S.4B accepted)",
        "SatelliteElementRecord",
        "SatelliteSnapshotManifest",
        "SatelliteElementSnapshot",
        "load_snapshot",
        "performs no network access and no propagation",
    ):
        assert phrase in reference
    assert "50S.4B satellite element and snapshot ownership (accepted)" in source_tree
    assert "tests/test_satellite_elements.py" in source_tree
    assert "50S.4B element data remains pre-coordinate" in coordinate_guide
    assert "performs no propagation" in coordinate_guide
    assert "Candidate 50S.4B implementation evidence" in audit
    assert "focused element, package-boundary, and packaged-configuration gate passed all 29 tests" in audit
    assert "Accepted 50S.4B immutable OMM snapshot" in guide
    assert "copies no live CelesTrak, Space-Track, SatChecker" in guide
    assert "sgp4>=2.25,<3" in instructions

def test_50s4b_records_complete_and_installed_wheel_evidence():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_propagation_audit_50s4a.md"
    ).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    assert "production commit `d3cb597`" in architecture
    assert "expanded focused gate passed all 158 tests" in audit
    assert "complete plugin-disabled suite passed all 2,483 tests" in audit
    assert "isolated virtual environment" in audit
    assert "installed `site-packages` tree" in audit
    assert "b6ab95df3eb180b07694b1b9bafd47c2805b6cc7ebea8636490beec03cd71457" in audit
    assert "ordered full identifiers 900001, 900002, and 900003" in audit
    assert "Accepted by Fernando on 2026-09-15" in roadmap
    assert "This closes 50S.4B and authorizes only 50S.4C" in audit
    assert "only 50S.4C validated SGP4/TEME propagation is authorized next" in guide


def test_50s4c_documents_validated_sgp4_teme_boundary():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_propagation_audit_50s4a.md"
    ).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Accepted 50S.4C validated SGP4/TEME propagation",
        "separate Julian-day and fractional-day values",
        "SatelliteTemeState",
        "does not pass a hidden surrogate identity",
    ):
        assert phrase in architecture
    assert "50S.4C — Validated SGP4/TEME propagation" in roadmap
    for phrase in (
        "Validated SGP4 geometric TEME propagation (50S.4C accepted)",
        "split_julian_date",
        "Sgp4TemePropagator",
        "SatelliteTemeState",
        "SatellitePropagationError",
        "does not transform TEME",
    ):
        assert phrase in reference
    assert "50S.4C SGP4/TEME propagation ownership (accepted)" in source_tree
    assert "tests/test_satellite_sgp4.py" in source_tree
    assert "50S.4C typed TEME state boundary" in coordinate_guide
    assert "must not be labelled ICRS, GCRS, ITRS" in coordinate_guide
    assert "Accepted 50S.4C implementation evidence" in audit
    assert "upstream `Satrec` maximum 339999" in audit
    assert "initial satellite element/SGP4 gate passed all 15 tests" in audit
    assert "Accepted 50S.4C SGP4 and geometric TEME state" in guide
    assert "300001–300003" in guide
    assert "only the bounded 50S.4D" in instructions


def test_50s4c_records_complete_and_installed_wheel_evidence():
    architecture = " ".join(read(V09_CURRENT).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_propagation_audit_50s4a.md"
    ).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())

    assert "production commit `e0d7c78`" in architecture
    assert "expanded focused gate passed all 167 tests" in audit
    assert "complete plugin-disabled suite passed all 2,492 tests" in audit
    assert "isolated virtual environment" in audit
    assert "loaded from `site-packages`" in audit
    assert "2e5288a6aad9fbe29cfe6d9a60e0045be28501859d8c739135fd302460ece5fe" in audit
    for identifier in ("300001", "300002", "300003"):
        assert f"{identifier}: TEME/WGS-72/status 0" in audit
    assert "finite position and velocity" in audit
    assert "accepted 50S.4C on 2026-09-15" in guide
    assert "final documentation gate passed all 132 tests" in audit
    assert "branch diff check was clean" in audit
    assert "This closes 50S.4C and" in audit
    assert "authorizes only 50S.4D Earth-orientation and topocentric state work" in audit

def test_50s4d_documents_accepted_topocentric_boundary():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_propagation_audit_50s4a.md"
    ).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Accepted 50S.4D Earth-orientation and topocentric state",
        "topocentric geometric vector expressed in GCRS axes",
        "Fernando scientifically and architecturally accepted 50S.4D on 2026-09-15",
    ):
        assert phrase in architecture
    assert "Status:** Accepted by Fernando on 2026-09-15" in roadmap
    assert "17-test dedicated and 89-test expanded Mac gates" in roadmap
    assert "complete plugin-disabled suite of 2,511 tests in 95.10" in roadmap
    for phrase in (
        "SatelliteTopocentricTransformer().transform(teme_state, observer)",
        "SatelliteEarthOrientationEvidence",
        "SatelliteEarthOrientationError",
        "gcrs-axes",
        "50S.4D accepted",
    ):
        assert phrase in reference
    assert "50S.4D Earth-orientation/topocentric ownership (accepted)" in source_tree
    assert "tests/test_satellite_topocentric.py" in source_tree
    assert "50S.4D topocentric Cartesian and GCRS-axis boundary (accepted)" in coordinate_guide
    assert "does not make it an ICRS catalogue position" in coordinate_guide
    assert "Accepted 50S.4D implementation evidence" in audit
    assert "production-code commit `1c33f3`" in audit
    assert "complete plugin-disabled suite passes all 2,511 tests" in audit
    assert "observed near-zenith separation is 1.40 mas" in audit
    assert "expanded element/SGP4/topocentric/crossing/SatChecker/coordinate gate" in audit
    assert "Accepted 50S.4D local topocentric state" in guide
    assert "exact IERS-A SHA-256 and coverage" in guide
    assert "only the bounded 50S.4E propagated-specimen builder is authorized next" in instructions

def test_50s4e_documents_accepted_propagated_specimen_boundary():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_propagation_audit_50s4a.md"
    ).split())
    guide = " ".join(read(DEVELOPER / "satellite_guide.md").split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for text in (
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinate_guide,
        audit,
        guide,
        instructions,
    ):
        assert "propagated sampled specimens — not verified crossings" in text
    assert "tools/build_50s4_satellite_specimens.py" in architecture
    assert "caller-selected output directory" in architecture
    assert "Status:** Accepted by Fernando on 2026-09-15" in roadmap
    assert "tests/test_satellite_specimens.py" in source_tree
    assert "No new `src/wenu` module is admitted" in source_tree
    assert "topocentric geometric direction expressed in GCRS axes" in (
        coordinate_guide
    )
    assert "cannot emit `SatelliteCrossingResult`" in audit
    assert "does not find a useful field automatically" in guide
    assert "50S.5" in guide
    assert "hidden 50S.5 crossing oracle" in instructions

def test_50s4e_records_complete_and_accepted_gate_evidence():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_propagation_audit_50s4a.md"
    ).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())

    for text in (architecture, roadmap, audit, guide):
        assert "all 2,522 tests" in text
        assert "105.38 seconds" in text
        assert (
            "16137e9380404dca03789532ab029c4159755c69dd2ab0ca5990a82cd9c42374"
            in text
        )
        assert "accepted 50S.4E on 2026-09-15" in text
    assert "dedicated builder gate passed all 10 tests in 10.58 seconds" in (
        architecture
    )
    assert "expanded satellite/coordinate gate passed all 99 tests" in (
        architecture
    )
    assert "documentation gate passed all 134 tests in 2.45 seconds" in (
        architecture
    )
    assert "d4bb5af084caf3e82621bc75aad902dc7ad9e38e785a97d3fcac0a23d89644fb" in (
        audit
    )
    assert "All three default tracks were below the La Ligua horizon" in audit
    assert "git diff --check 243b75c...HEAD" in audit
    assert "closing 50S.4 and authorizing only bounded" in roadmap
    assert "50S.5 complete local FoV-crossing oracle work" in roadmap
    assert "50S.6 acceleration" in guide
    assert "remain unauthorized" in guide

def test_50s5a_audits_complete_local_crossing_oracle_contract():
    audit = " ".join(read(
        DEVELOPER / "satellite_crossing_oracle_audit_50s5a.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "documentation-only scientific and API audit",
        "topocentric geometric vector expressed in GCRS axes",
        "fixed unit vector expressed in GCRS axes",
        "validated numerical completeness under the declared time and angular tolerances",
        "It is not a formal interval-arithmetic proof",
        "scans every valid record",
        "SatelliteCrossingConvergenceError",
        "A fixed sampling grid",
        "bracket-preserving root method",
        "detects tangency without requiring a sign change",
        "Disconnected visits are separate results",
        "One invalid record does not silently disappear",
        "tests/test_satellite_crossing_oracle.py",
        "Analytic trajectory tests exercise the solver independently",
        "Acceptance of 50S.5A authorizes 50S.5B only",
    ):
        assert phrase in audit

    assert "satellite_crossing_oracle_audit_50s5a.md" in index
    assert "Accepted 50S.5A complete-oracle audit" in architecture
    assert "50S.5A — Complete local crossing-oracle audit" in roadmap
    assert "No callable local crossing oracle exists yet" in reference
    assert "accepted audit specifies" in reference
    assert "Accepted 50S.5A local crossing-oracle ownership" in source_tree
    assert "closest existing `tests/test_satellite_crossings.py`" in source_tree
    assert "Accepted 50S.5A crossing-coordinate contract" in coordinate_guide
    assert "Accepted 50S.5A complete local crossing-oracle audit" in guide
    assert "Uncertain numerical intervals must subdivide or fail closed" in (
        instructions
    )
    assert "50S.6 and later behavior remain unauthorized" in guide
    assert "focused plugin-disabled documentation gate passed all 136 tests" in (
        audit
    )
    assert "3.27 seconds" in audit
    assert "git diff --check 41978bc...HEAD" in audit
    assert "adds no runtime, dependency, package data, or generated product" in (
        audit
    )
    assert "final acceptance documentation gate passed all 136 tests" in audit
    assert "3.00 seconds" in audit
    assert "Fernando scientifically and architecturally accepted 50S.5A" in audit
    assert "only bounded 50S.5B implementation" in audit
    assert (
        "50S.6 acceleration and all later satellite behavior remain unauthorized"
        in audit
    )


def test_50s5b_documents_accepted_complete_local_crossing_oracle():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_crossing_oracle_audit_50s5a.md"
    ).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    assert "Accepted 50S.5B complete local crossing oracle" in architecture
    assert "50S.5B — Complete local crossing-oracle implementation" in roadmap
    assert "LocalSatelliteCrossingQuery" in reference
    assert "LocalSatelliteCrossingOracle" in reference
    assert "SatelliteCrossingConvergenceError" in reference
    assert "Accepted 50S.5B local crossing-oracle ownership" in source_tree
    assert "Accepted 50S.5B local crossing coordinates" in coordinate_guide
    assert "Accepted 50S.5B complete local crossing oracle" in guide
    assert "Accepted 50S.5B implementation boundary" in instructions
    for phrase in (
        "recursive sampling certifies continuous containment within the declared time and angular tolerances",
        "zero-duration boundary event",
        "tests/test_satellite_crossing_oracle.py",
        "Focused, complete-suite, documentation, and diff gates are complete",
        "dedicated plugin-disabled oracle gate passed all 13 tests",
        "expanded oracle, crossing, element, SGP4, topocentric, SatChecker",
        "complete plugin-disabled suite passed all 2,538 tests in 163.36 seconds",
        "git diff --check aa6f91a...HEAD",
        "scientifically and architecturally accepted 50S.5B on 2026-09-15",
        "Runtime acceleration and all later behavior remain unauthorized",
    ):
        assert phrase in audit
    assert "documentation-first 50S.6 conservative local crossing acceleration audit" in roadmap
    assert "Runtime acceleration and all later behavior remain unauthorized" in audit


def test_50s6a_records_accepted_conservative_crossing_acceleration():
    audit = " ".join(read(
        DEVELOPER / "satellite_crossing_acceleration_audit_50s6a.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "documentation-only scientific and API audit",
        "LocalSatelliteCrossingOracle.solve(query)",
        "tri-state: `reject`, `retain`, or `indeterminate`",
        "validated zero false negatives",
        "not a formal interval-arithmetic proof of SGP4",
        "Topocentric cone versus bounded orbital shell",
        "may not treat the epoch osculating plane as fixed",
        "A geocentric great-circle distance alone is insufficient",
        "Phase and reachable-arc rejection",
        "Sampling alone proves nothing between samples",
        "Horizon rejection",
        "would therefore change result semantics",
        "Earth-occultation rejection",
        "HEALPix and time indexing",
        "Every retained candidate reaches the accepted 50S.5",
        "tests/test_satellite_crossing_acceleration.py",
        "three-record synthetic snapshot proves composition, not useful speed",
        "50S.6B first implementation",
    ):
        assert phrase in audit

    assert "satellite_crossing_acceleration_audit_50s6a.md" in index
    assert "Accepted 50S.6A conservative acceleration audit" in architecture
    assert "50S.6A — Conservative local crossing acceleration audit" in roadmap
    assert "No acceleration API exists yet" in reference
    assert "Accepted 50S.6A acceleration ownership audit" in source_tree
    assert "Accepted 50S.6A acceleration coordinate boundary" in coordinate_guide
    assert "Accepted 50S.6A conservative crossing acceleration audit" in guide
    assert "Accepted 50S.6A acceleration-audit boundary" in instructions
    assert "creates neither future source nor acceleration test file" in source_tree
    assert "Phase/reachable-arc filtering, coarse vectorized propagation" in roadmap
    assert "passed all 138 plugin-disabled current-documentation tests" in audit
    assert "3.99 seconds" in audit
    assert "git diff --check cc454de...HEAD" in audit
    assert "corrected branch diff check was clean" in roadmap
    assert "scientifically and architecturally accepted 50S.6A on 2026-09-15" in audit
    assert "authorizes only a bounded 50S.6B first implementation" in audit
    assert "all later behavior would remain unauthorized" in audit


def test_50s6b_documents_accepted_cone_shell_selector():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_crossing_acceleration_audit_50s6a.md"
    ).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    assert "Accepted 50S.6B conservative cone-shell selector" in architecture
    assert "50S.6B — First conservative cone-shell selector" in roadmap
    assert "ConservativeConeShellSelector.select(query)" in reference
    assert "Accepted 50S.6B selector ownership" in source_tree
    assert "Accepted 50S.6B cone-shell coordinate evidence" in coordinate_guide
    assert "Accepted 50S.6B cone-shell selector" in guide
    assert "Accepted 50S.6B cone-shell selector boundary" in instructions
    for phrase in (
        "src/wenu/satellites/crossing_acceleration.py",
        "synthetic_50s4b_v1",
        "intervals no longer than 60 seconds",
        "2.5 safety factor",
        "0.6 km/s observer-speed allowance",
        "strict antipodal rejection",
        "exact-oracle absence for the rejected record",
        "all three installed records across the complete admitted interval",
        "dedicated gate passed all 9 tests in 34.58 seconds",
        "passed all 78 tests in 99.99 seconds",
        "Focused, complete-suite, documentation, and diff gates are complete",
        "documentation gate passed all 139 tests in 4.72 seconds",
        "complete plugin-disabled suite passed all 2,549 tests in 200.47 seconds",
        "git diff --check d609322...HEAD",
        "scientifically and architecturally accepted 50S.6B on 2026-09-16",
    ):
        assert phrase in audit
    assert "does not coordinate an accelerated solve" in reference
    assert "package exports expose the four selector contracts" in source_tree
    assert "documentation-first 50S.6C audit" in roadmap
    assert "Further runtime acceleration remains unauthorized" in roadmap


def test_50s6c_audits_exact_solver_coordination_and_admission():
    audit = " ".join(read(
        DEVELOPER / "satellite_crossing_coordination_audit_50s6c.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "documentation-only scientific and API audit",
        "LocalSatelliteCrossingOracle.solve(query)",
        "ConservativeConeShellSelector.select(query)",
        "AcceleratedLocalSatelliteCrossingOracle",
        "one shared exact record solver",
        "No public caller may supply an arbitrary subset",
        "Additional acceleration evidence may differ",
        "fall back to the complete exhaustive route",
        "Broader-domain admission",
        "cannot justify production-catalogue admission",
        "an instrumented proof that rejected records receive zero exact evaluations",
        "Mocked speedup is not benchmark evidence",
        "repeated cold and warm runs",
        "an accelerated coordinator must remain opt-in",
        "This audit creates no source, runtime test, benchmark tool",
        "git diff --check 93a7d41...HEAD",
        "bounded 50S.6D implementation",
        "all later behavior would remain unauthorized",
    ):
        assert phrase in audit

    assert "satellite_crossing_coordination_audit_50s6c.md" in index
    assert "Accepted 50S.6C exact-solver coordination audit" in architecture
    assert "50S.6C — Exact-solver coordination and admission audit" in roadmap
    assert "Accepted accelerated coordination contract (50S.6C audit)" in reference
    assert "Accepted 50S.6C coordination ownership audit" in source_tree
    assert "Accepted 50S.6C coordination coordinate boundary" in coordinate_guide
    assert "Accepted 50S.6C coordination and admission audit" in guide
    assert "Accepted 50S.6C coordination-audit boundary" in instructions
    assert "No accelerated crossing service exists" in reference
    assert "three-record snapshot proves composition, not useful speed" in roadmap
    assert "creates no source, runtime test, benchmark tool" in source_tree
    assert "passed all 140 tests in 3.55 seconds" in audit
    assert "Fernando scientifically and architecturally accepted 50S.6C" in audit
    assert "only a bounded 50S.6D implementation" in audit
    assert "only bounded 50S.6D" in roadmap
    assert "bounded 50S.6D coordinator" in instructions



def test_50s6d_documents_accepted_accelerated_coordinator():
    audit = " ".join(read(
        DEVELOPER / "satellite_crossing_coordination_audit_50s6c.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    assert "accepted exact-solver coordination" in index
    assert "Accepted 50S.6D bounded accelerated crossing coordinator" in (
        architecture
    )
    assert "50S.6D — Bounded accelerated exact-solver coordination" in roadmap
    assert "Accepted accelerated local crossing coordinator" in reference
    assert "Accepted 50S.6D coordinator ownership" in source_tree
    assert "Accepted 50S.6D unchanged coordinate boundary" in coordinate_guide
    assert "Accepted 50S.6D bounded accelerated coordinator" in guide
    assert "Accepted 50S.6D accelerated-coordinator boundary" in instructions
    for phrase in (
        "one package-internal exact-record seam",
        "AcceleratedCrossingPolicy",
        "AcceleratedCrossingEvidence",
        "AcceleratedLocalSatelliteCrossingOracle",
        "solve_with_evidence(query)",
        "fallback_exhaustive",
        "retain and indeterminate",
        "three-record, 60-second domain",
        "no useful-speed claim",
        "adds no broader domain",
    ):
        assert phrase in " ".join(
            (
                audit,
                architecture,
                roadmap,
                reference,
                source_tree,
                coordinate_guide,
                guide,
                instructions,
            )
        )
    assert "The coordinate guide was reviewed for 50S.6D" in coordinate_guide
    assert "No new production module or test file is admitted" in source_tree
    assert "complete plugin-disabled suite" in audit
    assert "Fernando's scientific and architectural review" in audit



def test_50s6d_records_accepted_verification_evidence():
    audit = " ".join(read(
        DEVELOPER / "satellite_crossing_coordination_audit_50s6c.md"
    ).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for text in (audit, architecture, roadmap):
        assert "commit `a7aecba`" in text
        assert "2,566" in text
    for phrase in (
        "37-test dedicated acceleration/oracle gate in 116.58 seconds",
        "93-test expanded acceleration, oracle, crossing-contract, element, SGP4",
        "package-boundary gate in 128.74 seconds",
        "141-test current-documentation gate in 4.36 seconds",
        "complete 2,566-test suite in 213.87 seconds",
        "No performance, broader-domain, default-enablement, or later acceleration claim",
    ):
        assert phrase in audit
    assert "Fernando scientifically and architecturally accepted 50S.6D" in audit
    assert "final pre-acceptance documentation gate passed all 142 tests" in audit
    assert "branch diff check was clean" in audit
    assert "working tree was clean" in audit
    assert "No later acceleration milestone is authorized automatically" in roadmap
    assert "separately accepted bounded milestone" in instructions


def test_50s6e_audits_multifov_interchange_and_lunar_illumination():
    audit = " ".join(read(
        DEVELOPER / "satellite_multifov_interchange_audit_50s6e.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "documentation-only scientific, API, performance, and interchange audit",
        "not a documented multi-FoV batch API",
        "any non-empty ordered number of circular FoV requests",
        "Ten FoVs are the reference workload",
        "not a hard-coded public cardinality",
        "same-interval workload is a special research and optimization case",
        "geometric vacuum AltAz",
        "plane-parallel `X = sec(z)`",
        "defaults to 2",
        "transforms only the field centre",
        "minimum centre altitude in this model",
        "FoV radius does not enter airmass admission",
        "complete interval must be conservatively certified",
        "non-positive centre altitude or uncertain numerical certification fails closed",
        "not a satellite horizon, Earth-occultation, illumination",
        "no civil-date, time-zone, solar-altitude, or inferred-twilight boundary",
        "disjoint, partially overlapping, and identical airmass-admissible intervals",
        "exactly equivalent to the ordered collection of independent exhaustive",
        "1, 2, 5, 10, 20, and, when practical, 50 FoVs",
        "JSON as the canonical nested exchange",
        "Astropy ECSV",
        "IVOA VOTable",
        "optional CCSDS OEM",
        "Paranal, ELT, and at least one other observatory",
        "direct Sunlight",
        "solar Earthshine",
        "direct Moonlight",
        "Lunar-Earthshine",
        "arXiv:2609.07057",
        "Fluxes, never magnitudes, are summed",
        "bounded 50S.6F implementation",
    ):
        assert phrase in audit

    assert "satellite_multifov_interchange_audit_50s6e.md" in index
    assert "Accepted 50S.6E multi-FoV and interchange direction" in architecture
    assert "50S.6E — Same-observer, airmass-bounded multi-FoV" in roadmap
    assert "Accepted multi-FoV and observatory interchange contract" in reference
    assert "Accepted 50S.6E documentation ownership" in source_tree
    assert "Accepted 50S.6E multi-FoV coordinate boundary" in coordinate_guide
    assert "Accepted 50S.6E multi-FoV and delivery sequence" in guide
    assert "Accepted 50S.6E boundary" in instructions
    assert "50S.6G.3 may accept binocular and regional chart products" in audit
    assert "50S.6G.4 may accept stereographic planisphere" in audit
    assert "no runtime or output" in roadmap
    assert "accepted 50S.6F implementation adds" in architecture
    assert "scientifically and architecturally accepted this audit" in audit
    assert "commit `f079d95`" in audit
    assert "all 143 plugin-disabled current-documentation tests" in audit
    assert "Only a bounded 50S.6F implementation is authorized next" in audit
    assert "| 28 | 50B.0 |" in roadmap
    assert "| 33 | 50B.5 |" in roadmap


def test_50s6f_documents_candidate_atomic_multifov_coordinator():
    audit = " ".join(read(
        DEVELOPER / "satellite_multifov_interchange_audit_50s6e.md"
    ).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "atomic validation on 2026-09-16",
        "collects every invalid field and reason in input order",
        "raises before any crossing solve",
        "returns no partial results",
        "future invalid input file may produce a validation file",
        "50S.6F neither reads nor writes that file",
        "satellites/crossing_batch.py",
        "ten-field execution chunk",
        "no representative-scale, useful-speed, or shared-state-cache claim",
    ):
        assert phrase in audit

    assert "accepted 50S.6F implementation" in architecture
    assert "Accepted bounded implementation" in roadmap
    assert "MultiFieldSatelliteCrossingCoordinator.solve(request)" in reference
    assert "Accepted 50S.6F production ownership" in source_tree
    assert "Accepted 50S.6F field-centre airmass realization" in (
        coordinate_guide
    )
    assert "Accepted 50S.6F bounded batch implementation" in guide
    assert "Accepted 50S.6F implementation boundary" in instructions
    assert "No projection, rendering, report, CLI, or exporter owner changes" in (
        source_tree
    )
    assert "no useful-speed or shared-physical-state-reuse claim" in roadmap
    assert "adds no CLI, file input, validation-output file" in instructions
    for document in (
        audit,
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinate_guide,
        guide,
        instructions,
    ):
        assert "scientifically and architecturally accepted" in document
        assert "2026-09-17" in document
        assert "2,577 plugin-disabled tests passed" in document
        assert "Only a separately bounded 50S.6G audit is authorized next" in (
            document
        )
    assert "no 50S.6G implementation is authorized" in instructions


def test_50s6g_audits_representative_delivery_reports_files_and_tracks():
    audit = " ".join(read(
        DEVELOPER / "satellite_delivery_audit_50s6g.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "documentation-only architecture, API, performance, interchange, CLI/file, and chart-delivery audit",
        "changes no executable behavior, public command",
        "explicit caller-selected snapshot directory",
        "at most one supported bulk request",
        "1, 2, 5, 10, 20, and, when practical, 50",
        "One canonical crossing information model",
        "JSON is the canonical nested exchange",
        "Astropy ECSV is a lossless unit-aware tabular encoding",
        "IVOA VOTable is a lossless astronomical interoperability encoding",
        "CCSDS OEM describes orbit ephemerides rather than Wenu crossing semantics",
        "Python calls and direct CLI argument mode are atomic",
        "File mode is also atomic",
        "Supplying the validation-output file in a second explicit invocation",
        "revalidates it against the current snapshot and policy",
        "If no valid fields remain, the derived request is absent",
        "ECSV and VOTable are output encodings, not initial request",
        "those three values alone are not a sufficiently controlled plotted curve",
        "Regional and binocular products are the first chart families",
        "Stereographic planispheres require a separate audit",
        "geometric crossings retained independently of illumination or brightness",
        "50S.6G.1A — External immutable snapshot seam",
        "50S.6G.4B — Stereographic planisphere tracks",
        "Only bounded 50S.6G.1A external immutable snapshot loading",
    ):
        assert phrase in audit

    assert "satellite_delivery_audit_50s6g.md" in index
    assert "accepted 50S.6G delivery audit" in architecture
    assert "50S.6G — Representative delivery, reports, files" in roadmap
    assert "Accepted 50S.6G delivery direction" in reference
    assert "Accepted 50S.6G delivery ownership" in source_tree
    assert "Accepted 50S.6G delivery coordinate boundary" in coordinate_guide
    assert "Accepted 50S.6G delivery sequence" in guide
    assert "Accepted 50S.6G delivery-audit boundary" in instructions
    assert "Accepted 50S.6G delivery refinement" in (
        " ".join(read(
            DEVELOPER / "satellite_multifov_interchange_audit_50s6e.md"
        ).split())
    )
    for document in (
        audit,
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinate_guide,
        guide,
        instructions,
    ):
        assert "scientifically and architecturally accepted" in document
        assert "2026-09-17" in document
        assert "145 plugin-disabled current-documentation tests passed" in (
            document
        )
        assert "Only bounded 50S.6G.1A external immutable snapshot loading" in (
            document
        )


def test_50s6g1a_documents_accepted_external_snapshot_loader():
    audit = " ".join(read(
        DEVELOPER / "satellite_delivery_audit_50s6g.md"
    ).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Accepted 50S.6G.1A implementation handoff",
        "load_snapshot_directory(directory)",
        "explicit local non-symlink directory",
        "Directory names do not define snapshot identity",
        "same immutable snapshot through the accepted complete schema",
        "no discovery, acquisition, provider access, network",
        "no new production or test file is added",
        "Only a separately bounded 50S.6G.1B",
        "not its implementation",
    ):
        assert phrase in audit

    assert "accepted 50S.6G.1A implementation" in architecture
    assert "Accepted bounded implementation" in roadmap
    assert "Accepted explicit-directory satellite snapshot loader" in (
        reference
    )
    assert "Accepted 50S.6G.1A production ownership" in source_tree
    assert "Accepted 50S.6G.1A coordinate review" in coordinate_guide
    assert "Accepted 50S.6G.1A external snapshot loading" in guide
    assert "Accepted 50S.6G.1A external snapshot boundary" in instructions
    assert "performs no network access, acquisition, publication" in reference
    assert "does not admit an external snapshot to the 50S.6F coordinator" in (
        roadmap
    )
    for document in (
        audit,
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinate_guide,
        guide,
        instructions,
    ):
        assert "scientifically and architecturally accepted" in document
        assert "2026-09-17" in document
        assert "2,583 plugin-disabled tests passed" in document


def test_50s6g1b_accepts_representative_snapshot_preflight_and_evidence():
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_preflight_audit_50s6g1b.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    delivery = " ".join(read(
        DEVELOPER / "satellite_delivery_audit_50s6g.md"
    ).split())

    for phrase in (
        "Accepted documentation-only provider, acquisition, publication, admission, and performance-evidence audit",
        "one explicit representative-scale population, not a complete resident-space-object catalogue",
        "Policy review and data acquisition are separate explicit operations",
        "exact SHA-256",
        "not a generic `--yes` flag",
        "at most one GP network request",
        "accepts only a direct HTTPS 200 response",
        "does not follow redirects and does not retry",
        "GROUP=active&FORMAT=CSV",
        "provider-defined active-satellite population",
        "not the complete public resident-space-object population",
        "CENTER_NAME = EARTH",
        "REF_FRAME = TEME",
        "TIME_SYSTEM = UTC",
        "MEAN_ELEMENT_THEORY = SGP4",
        "rejects duplicate NORAD identifiers",
        "staged directory is reloaded through `load_snapshot_directory()`",
        "Raw provider and policy bytes remain local evidence",
        "Medium representative specimen",
        "derived from one validated Active snapshot",
        "admitted by exact canonical-record SHA-256",
        "1, 2, 5, 10, 20, and, when practical, 50",
        "at least La Ligua, Paranal, ELT, and one northern-site explicit observer",
        "makes no useful-speed, shared-state-reuse, memory-bound, or production-capacity claim",
        "50S.6G.1B.1 — Policy receipt and deterministic builder",
        "50S.6G.1B.2 — Representative admission and evidence",
        "does not authorize a live CelesTrak request",
    ):
        assert phrase in audit

    assert "satellite_snapshot_preflight_audit_50s6g1b.md" in index
    assert "accepted 50S.6G.1B audit" in architecture
    assert "50S.6G.1B — Representative snapshot preflight" in roadmap
    assert "Accepted representative snapshot preflight contract" in reference
    assert "Accepted 50S.6G.1B acquisition and evidence ownership" in (
        source_tree
    )
    assert "Accepted 50S.6G.1B coordinate review" in coordinate_guide
    assert "Accepted 50S.6G.1B representative snapshot preflight" in guide
    assert "Accepted 50S.6G.1B provider-policy and evidence boundary" in (
        instructions
    )
    assert "Accepted 50S.6G.1B refinement" in delivery
    for document in (
        audit,
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinate_guide,
        guide,
        instructions,
        delivery,
    ):
        assert "scientifically and architecturally accepted" in document
        assert "2026-09-17" in document
        assert "147 plugin-disabled current-documentation tests passed" in (
            document
        )
    assert "no live CelesTrak request" in architecture
    assert "fake-transport" in roadmap


def test_50s6g1b1_documents_offline_snapshot_builder_boundary():
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_preflight_audit_50s6g1b.md"
    ).split())

    assert "Implemented 50S.6G.1B.1 offline snapshot builder" in architecture
    assert "mandatory injected transport" in roadmap
    assert "offline developer command" in reference
    assert "https://celestrak.org/usage-policy.php" in reference
    assert "gp-data-formats.php" in reference
    assert "snapshot_acquisition.py" in source_tree
    assert "build_satellite_snapshot.py" in source_tree
    assert "test_satellite_snapshot_acquisition.py" in source_tree
    assert "adds no coordinate transform" in coordinate_guide
    assert "preserves full NORAD identifiers" in guide
    assert "Preserve the absence of a default or live network adapter" in (
        instructions
    )
    assert "No live provider request or 50S.6G.1B.2 evidence" in audit
    for document in (
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinate_guide,
        guide,
        instructions,
        audit,
    ):
        assert "Fernando accepted" in document
        assert "2026-09-17" in document
        assert "2,594 plugin-disabled tests passed" in document
    assert "175 focused plugin-disabled tests passed" in audit
    assert "226.82 seconds" in audit
    assert "does not authorize a live policy or GP request" in audit
    for document in (architecture, reference, instructions, audit):
        assert "2,595 plugin-disabled tests passed" in document
    assert "https://celestrak.org/usage-policy.php" in architecture
    assert "no GP request was performed" in architecture
    assert "public, reliable, and genuinely independent" in guide
    assert "rather than a redistribution of CelesTrak" in roadmap
    assert "validation oracle" in guide
    assert "never as silent fallback" in guide
    for document in (
        architecture, roadmap, reference, guide, instructions, audit
    ):
        assert "67bf0faa7e026a7cd49799069db9d3355f2a867894133afd39e130d6185724aa" in document
        assert "10 focused tests" in document
    assert "14,643-byte" in audit
    assert "2.41 seconds" in audit
    assert "226.25 seconds" in audit
    assert "Explicit approval of this exact digest remains" in audit
    for document in (
        architecture, roadmap, reference, guide, instructions, audit
    ):
        assert "e54730e14b2097444c5e20bba6dd13d3e2d92f956797d49256ddb1a70ffe5014" in document
        assert "e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347" in document
        assert "16,559" in document
        assert "2,600" in document
    assert "YYYY-MM-DDTHH:MM:SS.ffffff" in audit
    assert "text/plain; charset=UTF-8" in audit
    assert "15 focused tests passed in 2.22 seconds" in audit
    assert "2,600 plugin-disabled tests passed in 223.57 seconds" in audit
    assert "No second provider request occurred" in audit
    assert "50S.6G.1B.2 remain separately authorized" in audit


def test_50s6g1b2a_accepts_exact_shared_external_admission():
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_admission_audit_50s6g1b2a.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Accepted documentation-only audit",
        "exact canonical-record SHA-256 plus validated manifest identity",
        "never by directory name",
        "Each present service admits by `snapshot_id`, independently",
        "satellites/snapshot_admission.py",
        "selector, accelerated coordinator, and multi-FoV batch",
        "ordinary installed default remains `synthetic_50s4b_v1`",
        "external token is explicit and evidence-only",
        "same `snapshot_id` with another digest fails",
        "50S.6G.1B.2B",
        "50S.6G.1B.2C",
        "50S.6G.1B.2D",
        "draws no track itself",
    ):
        assert phrase in audit

    assert "satellite_snapshot_admission_audit_50s6g1b2a.md" in index
    assert "Accepted 50S.6G.1B.2A external admission audit" in architecture
    assert "50S.6G.1B.2A — External snapshot admission audit" in roadmap
    assert "Accepted proposed external snapshot admission contract" in reference
    assert "Accepted 50S.6G.1B.2A admission ownership" in source_tree
    assert "Accepted 50S.6G.1B.2A coordinate review" in coordinate_guide
    assert "Accepted 50S.6G.1B.2A external admission" in guide
    assert "Accepted 50S.6G.1B.2A digest-admission boundary" in instructions

    for document in (
        audit,
        roadmap,
        reference,
        guide,
        instructions,
    ):
        assert "evidence-only" in document
    assert "no coordinate operation" in coordinate_guide
    assert "changes no runtime" in roadmap
    assert "No production or runtime test file is added" in source_tree


def test_50s6g1b2a_records_acceptance_and_bounded_next_step():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_snapshot_admission_audit_50s6g1b2a.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "scientifically and architecturally accepted" in document
        assert "2026-09-17" in document
        assert "150 plugin-disabled current-documentation tests passed" in document
        assert "3.84 seconds" in document
        assert "Only bounded 50S.6G.1B.2B" in document
    audit = documents[0]
    assert "does not authorize medium selection" in audit
    assert "matrix execution" in audit
    assert "chart integration" in audit
    assert "another provider request" in audit


def test_50s6g1b2b_documents_accepted_shared_digest_admission():
    audit = " ".join(read(
        DEVELOPER / "satellite_snapshot_admission_audit_50s6g1b2a.md"
    ).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    assert "Accepted 50S.6G.1B.2B implementation record" in audit
    assert "Accepted 50S.6G.1B.2B digest admission" in architecture
    assert "50S.6G.1B.2B accepted implementation" in roadmap
    assert "External snapshot admission API" in reference
    assert "Accepted 50S.6G.1B.2B ownership" in source_tree
    assert "Accepted 50S.6G.1B.2B coordinate review" in (
        coordinate_guide
    )
    assert "Accepted 50S.6G.1B.2B admission" in guide
    assert "Accepted 50S.6G.1B.2B admission boundary" in (
        instructions
    )
    for document in (
        audit,
        architecture,
        source_tree,
        instructions,
    ):
        assert "snapshot_admission.py" in document
    for document in (
        audit,
        architecture,
        roadmap,
        reference,
        source_tree,
        guide,
    ):
        assert "synthetic" in document
    assert "schema version, snapshot ID, canonical-record SHA-256" in audit
    assert "token contains no path" in architecture
    assert "cannot be directly constructed" in reference
    assert "before airmass or crossing work" in source_tree
    assert "performs no coordinate transformation" in coordinate_guide
    assert "No external snapshot is packaged, discovered" in guide
    assert "50S.6G.1B.2C and 50S.6G.1B.2D remain separately bounded" in roadmap
    assert "does not implement deterministic medium selection" in (
        audit
    )


def test_50s6g1b2b_records_acceptance_and_authorizes_only_medium_work():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_snapshot_admission_audit_50s6g1b2a.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "scientifically and architecturally accepted 50S.6G.1B.2B" in document
        assert "2026-09-17" in document
        assert "51 focused runtime tests" in document
        assert "151 current-documentation tests" in document
        assert "2,611 plugin-disabled tests passed" in document
        assert "215.89 seconds" in document
        assert "Only bounded 50S.6G.1B.2C" in document
        assert "50S.6G.1B.2D matrix execution" in document
        assert "separately unauthorized" in document


def test_50s6g1b2c_accepts_deterministic_medium_specimen():
    audit = " ".join(read(
        DEVELOPER / "satellite_medium_specimen_audit_50s6g1b2c.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Accepted documentation-only audit",
        "not a statistical sample",
        "retrieved_stopped_utc",
        "geo_deep_like",
        "meo_like",
        "leo_like",
        "e_over_0p25",
        "bstar_zero",
        "age_future",
        "norad_more_than_five",
        "default target is exactly **256 records**",
        "first two distinct records",
        "mandatory union exceeds the requested target",
        "selection-receipt.json",
        "two-per-non-empty-bin coverage rule",
        "no-population-frequency statement",
        "satellites/snapshot_evidence.py",
        "tests/test_satellite_snapshot_evidence.py",
        "does not run the matrix",
        "first real medium artifact",
    ):
        assert phrase in audit

    assert "satellite_medium_specimen_audit_50s6g1b2c.md" in index
    assert "Accepted 50S.6G.1B.2C medium-specimen audit" in architecture
    assert "50S.6G.1B.2C — Deterministic medium specimen" in roadmap
    assert "Accepted proposed deterministic medium-specimen contract" in reference
    assert "Accepted 50S.6G.1B.2C ownership" in source_tree
    assert "Accepted 50S.6G.1B.2C coordinate review" in coordinate_guide
    assert "Accepted 50S.6G.1B.2C medium specimen" in guide
    assert "Accepted 50S.6G.1B.2C medium-specimen boundary" in instructions
    assert "No source or runtime test file is added" in source_tree
    assert "performs no propagation" in coordinate_guide
    assert "first real subset operation" in roadmap
    assert "matrix execution" in instructions


def test_50s6g1b2c_records_acceptance_and_fake_data_only_authority():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_medium_specimen_audit_50s6g1b2c.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "scientifically and architecturally accepted" in document
        assert "2026-09-17" in document
        assert "153 plugin-disabled current-documentation tests passed" in document
        assert "4.58 seconds" in document
        assert "Only bounded fake-data" in document
        assert "first real medium selection" in document
        assert "50S.6G.1B.2D matrix execution" in document
        assert "separately unauthorized" in document

def test_50s6g1b2c_documents_candidate_fake_data_implementation():
    audit = " ".join(read(
        DEVELOPER / "satellite_medium_specimen_audit_50s6g1b2c.md"
    ).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    assert "Candidate 50S.6G.1B.2C fake-data implementation" in audit
    assert "Candidate 50S.6G.1B.2C deterministic medium evidence" in architecture
    assert "50S.6G.1B.2C candidate implementation state" in roadmap
    assert "Deterministic medium snapshot evidence API" in reference
    assert "Candidate 50S.6G.1B.2C ownership" in source_tree
    assert "Candidate 50S.6G.1B.2C coordinate review" in coordinate_guide
    assert "Candidate 50S.6G.1B.2C medium specimen" in guide
    assert "Candidate 50S.6G.1B.2C boundary" in instructions

    for document in (
        audit,
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinate_guide,
        guide,
        instructions,
    ):
        assert "snapshot_evidence.py" in document
        assert "30 plugin-disabled" in document
        assert "5.99 seconds" in document
        assert "real medium selection" in document
        assert "50S.6G.1B.2D" in document

    assert "captured provider-response bytes" in audit
    assert "ordinary installed default remains `synthetic_50s4b_v1`" in architecture
    assert "has no transport" in roadmap
    assert "receipt contains no filesystem path" in reference
    assert "authorization-only" in source_tree
    assert "performs no propagation" in coordinate_guide
    assert "not a statistical sample" in guide
    assert "Do not run it on the real 16,559-record parent" in instructions

def test_50s6g1b2c_records_accepted_fake_data_implementation_boundary():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_medium_specimen_audit_50s6g1b2c.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "accepted" in document.lower()
        assert "2026-09-17" in document
        assert "1d9d4e4" in document
        assert "2,622" in document
        assert "225.75 seconds" in document
        assert "185" in document
        assert "9.03 seconds" in document
        assert "real" in document.lower()
        assert "separate" in document.lower()
        assert "50S.6G.1B.2D" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Accepted fake-data implementation" in audit
    assert "Accepted 50S.6G.1B.2C implementation" in architecture
    assert "50S.6G.1B.2C accepted implementation" in roadmap
    assert "Accepted medium-evidence implementation" in reference
    assert "Accepted 50S.6G.1B.2C ownership" in source_tree
    assert "Accepted 50S.6G.1B.2C coordinate boundary" in coordinates
    assert "Accepted 50S.6G.1B.2C implementation" in guide
    assert "Accepted 50S.6G.1B.2C implementation boundary" in instructions
    assert "does not itself authorize executing `select-medium`" in audit
    assert "requires separate authorization" in architecture
    assert "requires no provider request" in roadmap
    assert "evidence-only" in reference
    assert "No real medium product was created" in source_tree
    assert "no propagation or coordinate transformation" in coordinates
    assert "No real medium snapshot has been produced" in guide
    assert "Require Fernando's separate approval" in instructions

def test_50s6g1b2c_documents_candidate_real_medium_evidence():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_medium_specimen_audit_50s6g1b2c.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b" in document
        assert "1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895" in document
        assert "e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347" in document
        assert "2026-09-17T15:52:23.000000Z" in document
        assert "50S.6G.1B.2D" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Candidate real-selection closure" in audit
    assert "Candidate real 50S.6G.1B.2C specimen evidence" in architecture
    assert "50S.6G.1B.2C real-selection closure candidate" in roadmap
    assert "Real medium specimen identity" in reference
    assert "Candidate real-selection evidence ownership" in source_tree
    assert "Candidate real medium specimen coordinate finding" in coordinates
    assert "Candidate real medium specimen" in guide
    assert "Candidate real 50S.6G.1B.2C artifact boundary" in instructions

    for document in (audit, architecture, roadmap, reference, guide, instructions):
        assert "48" in document
        assert "208" in document
        assert "24" in document

    assert "byte-for-byte unchanged" in audit
    assert "made no provider request" in audit
    assert "not packaged, installed, discovered" in architecture
    assert "remaining 50S.6G.1B.2C closure decision" in roadmap
    assert "external, immutable, and evidence-only" in reference
    assert "No repository source or data directory owns" in source_tree
    assert "performed no propagation or coordinate transformation" in coordinates
    assert "not a statistical sample" in guide
    assert "candidate evidence record preceded acceptance" in instructions

def test_50s6g1b2c_records_accepted_exact_real_specimen():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_medium_specimen_audit_50s6g1b2c.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b" in document
        assert "2026-09-17" in document
        assert "c4cd009" in document
        assert "157 plugin-disabled" in document
        assert "4.66 seconds" in document
        assert "50S.6G.1B.2D" in document
        assert "unauthorized" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Accepted real-selection closure" in audit
    assert "Accepted real 50S.6G.1B.2C specimen" in architecture
    assert "50S.6G.1B.2C accepted real-selection closure" in roadmap
    assert "Accepted real medium evidence" in reference
    assert "Accepted real 50S.6G.1B.2C evidence" in source_tree
    assert "Accepted real 50S.6G.1B.2C coordinate finding" in coordinates
    assert "Accepted real 50S.6G.1B.2C specimen" in guide
    assert "Accepted real 50S.6G.1B.2C artifact" in instructions

    for document in (audit, architecture, roadmap, reference, source_tree, guide, instructions):
        assert "1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895" in document

    assert "closes 50S.6G.1B.2C" in audit
    assert "installed synthetic default" in architecture
    assert "Only a separately authorized 50S.6G.1B.2D matrix audit" in roadmap
    assert "No other artifact is implied" in reference
    assert "outside the repository and package" in source_tree
    assert "no propagation or coordinate transformation" in coordinates
    assert "external, immutable, and non-statistical" in guide
    assert "Do not refresh, substitute, package, discover, or promote" in instructions

def test_50s6g1b2d_proposes_exact_equivalence_resource_matrix():
    audit = " ".join(read(
        DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Candidate documentation-only audit",
        "2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b",
        "1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895",
        "exactly **10 fields**",
        "same accepted 256-record snapshot",
        "different intervals within one UTC night",
        "one pair shares the same interval",
        "time_tolerance_seconds = 0.01",
        "angular_tolerance_deg = 1e-5",
        "selector_failure_mode = \"fail_closed\"",
        "Python result tuples must compare equal",
        "canonical result bytes must be identical",
        "no exhaustive fallback",
        "at least one conservative rejection",
        "three times after one unreported warm-up",
        "fresh subprocesses",
        "crossing_matrix.py",
        "run-equivalence-matrix",
        "tests/test_satellite_crossing_matrix.py",
        "does not",
    ):
        assert phrase in audit

    assert "satellite_equivalence_matrix_audit_50s6g1b2d.md" in index
    assert "Candidate 50S.6G.1B.2D equivalence-matrix audit" in architecture
    assert "50S.6G.1B.2D — Exact-equivalence and resource-matrix audit" in roadmap
    assert "Proposed exact-equivalence matrix contract" in reference
    assert "Candidate 50S.6G.1B.2D ownership" in source_tree
    assert "Candidate 50S.6G.1B.2D coordinate review" in coordinate_guide
    assert "Candidate 50S.6G.1B.2D equivalence matrix" in guide
    assert "Candidate 50S.6G.1B.2D audit boundary" in instructions

    for document in (
        audit,
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinate_guide,
        guide,
        instructions,
    ):
        assert "10" in document
        assert "same-observer" in document
        assert "matrix" in document.lower()

    assert "no matrix is executed" in architecture.lower()
    assert "real matrix execution requires separate authorization" in roadmap
    assert "Neither the owner nor command exists yet" in reference
    assert "No matrix runtime or evidence artifact exists yet" in source_tree
    assert "introduces no coordinate operation" in coordinate_guide
    assert "not a speed claim" in guide
    assert "Do not implement or run the matrix" in instructions

def test_50s6g1b2d_records_acceptance_and_fake_data_only_authority():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "accepted" in document.lower()
        assert "2026-09-17" in document
        assert "6e7a8b9" in document
        assert "159 plugin-disabled" in document
        assert "10.75 seconds" in document
        assert "fake-data" in document
        assert "real" in document.lower()
        assert "unauthorized" in document or "does not authorize" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Acceptance record" in audit
    assert "Accepted 50S.6G.1B.2D matrix audit" in architecture
    assert "50S.6G.1B.2D accepted audit" in roadmap
    assert "Accepted 50S.6G.1B.2D matrix contract" in reference
    assert "Accepted 50S.6G.1B.2D ownership proposal" in source_tree
    assert "Accepted 50S.6G.1B.2D coordinate finding" in coordinates
    assert "Accepted 50S.6G.1B.2D audit" in guide
    assert "Accepted 50S.6G.1B.2D audit boundary" in instructions

    assert "does not authorize execution" in audit
    assert "Only bounded fake-data implementation" in architecture
    assert "Only bounded fake-data matrix-harness implementation" in roadmap
    assert "using fake data only" in reference
    assert "No real matrix execution" in source_tree
    assert "real matrix execution" in coordinates
    assert "must not be executed" in guide
    assert "Do not read or execute the accepted real 256-record specimen" in instructions

def test_50s6g1b2d_documents_candidate_fake_data_implementation():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "19520f3" in document
        assert "2634 plugin-disabled" in document
        assert "230.25 seconds" in document
        assert "2026-09-17" in document
        assert "fake data" in document.lower() or "fake-data" in document.lower()
        assert "real" in document.lower()
        assert "acceptance" in document.lower()

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Candidate fake-data implementation record" in audit
    assert "Candidate 50S.6G.1B.2D fake-data matrix implementation" in architecture
    assert "50S.6G.1B.2D candidate fake-data implementation state" in roadmap
    assert "Candidate crossing equivalence matrix API" in reference
    assert "Candidate 50S.6G.1B.2D implementation ownership" in source_tree
    assert "Candidate 50S.6G.1B.2D coordinate review" in coordinates
    assert "Candidate 50S.6G.1B.2D fake-data implementation" in guide
    assert "Candidate 50S.6G.1B.2D implementation boundary" in instructions
    assert "matrix-manifest.json" in reference
    assert "No accepted real specimen was read" in architecture
    assert "no real matrix was executed" in audit.lower()

def test_50s6g1b2d_records_fake_data_implementation_acceptance():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "scientifically and architecturally accepted" in document
        assert "2026-09-17" in document
        assert "2634 plugin-disabled" in document
        assert "230.25 seconds" in document
        assert "19520f3" in document
        assert "161 plugin-disabled" in document
        assert "3.32 seconds" in document
        assert "3ef6a4d" in document
        assert "separately bounded real-execution audit" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Accepted fake-data implementation closure" in audit
    assert "Accepted 50S.6G.1B.2D fake-data matrix implementation" in architecture
    assert "50S.6G.1B.2D accepted fake-data implementation" in roadmap
    assert "Accepted crossing equivalence matrix boundary" in reference
    assert "Accepted 50S.6G.1B.2D ownership" in source_tree
    assert "Accepted 50S.6G.1B.2D coordinate boundary" in coordinates
    assert "Accepted 50S.6G.1B.2D fake-data implementation" in guide
    assert "Accepted 50S.6G.1B.2D implementation boundary" in instructions
    assert "does not authorize" in audit
    assert "real execution" in audit

def test_50s6g1b2d_audits_real_execution_readiness_fail_closed():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "9bdf301" in document
        assert "real" in document.lower()
        assert "fixture" in document.lower()
        assert "airmass" in document.lower()
        assert "subprocess" in document.lower()
        assert "command" in document.lower()
        assert "no" in document.lower() or "not" in document.lower()

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Candidate real-execution readiness audit" in audit
    assert "not ready for real execution" in audit
    assert "Candidate 50S.6G.1B.2D real-execution readiness finding" in architecture
    assert "50S.6G.1B.2D real-execution readiness gate" in roadmap
    assert "Proposed real-matrix execution surface" in reference
    assert "Candidate real-execution readiness ownership" in source_tree
    assert "Candidate real-matrix coordinate readiness finding" in coordinates
    assert "Candidate real-execution readiness audit" in guide
    assert "Candidate real-execution readiness boundary" in instructions
    assert "24 nonempty bins" in audit
    assert "48 mandatory representatives" in audit
    assert "208 fill records" in audit
    assert "run-equivalence-matrix" in audit
    assert "separate explicit authorization" in audit
    assert "do not attempt the real" in instructions.lower()

def test_50s6g1b2d_records_accepted_real_execution_readiness_audit():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "scientifically and architecturally accepted" in document
        assert "2026-09-17" in document
        assert "163 plugin-disabled" in document
        assert "3.80 seconds" in document
        assert "054ac39" in document
        assert "fake-data" in document or "fake data" in document
        assert "real" in document.lower()
        assert "unauthorized" in document or "not be executed" in document or "no authority" in document.lower()

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Accepted real-execution readiness finding" in audit
    assert "Accepted 50S.6G.1B.2D real-execution readiness finding" in architecture
    assert "50S.6G.1B.2D accepted real-execution readiness finding" in roadmap
    assert "Accepted real-execution readiness boundary" in reference
    assert "Accepted real-execution readiness ownership" in source_tree
    assert "Accepted real-matrix coordinate readiness finding" in coordinates
    assert "Accepted real-execution readiness audit" in guide
    assert "Accepted real-execution readiness boundary" in instructions
    assert "real matrix is not yet ready to run" in audit
    assert "does not authorize reading" in audit


def test_50s6g1b2d1_documents_single_real_execution_authorization():
    audit = " ".join(read(
        DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md"
    ).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Candidate 50S.6G.1B.2D.1 first-real-execution authorization",
        "authorize exactly one operator-started offline run",
        "at most 80 fresh subprocess invocations",
        "The existing worker timeout remains 3600 seconds per subprocess",
        "There is no automatic retry",
        "A successful command does not itself accept the evidence",
        "Until Fernando explicitly accepts this audit",
    ):
        assert phrase in audit
    for digest in (
        "2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b",
        "1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895",
        "e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347",
    ):
        assert digest in audit
    assert "Candidate first-real-execution authorization" in architecture
    assert "Candidate first real run policy" in reference
    assert "50S.6G.1B.2D.1 candidate first real execution" in roadmap
    assert "Candidate first-real-execution ownership" in source_tree
    assert "Candidate first-real-execution coordinate boundary" in coordinate_guide
    assert "Candidate first real equivalence run" in guide
    assert "Candidate first-real-execution authorization boundary" in instructions


def test_50s6g1b2d2_documents_parent_only_progress_boundary():
    audit = " ".join(read(
        DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md"
    ).split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(read(
        DEVELOPER / "implementation_reference.md"
    ).split())
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    coordinate_guide = " ".join(read(COORDINATE_GUIDE).split())
    guide = " ".join(read(SATELLITE_PROGRAM_LOG).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for phrase in (
        "Candidate parent-process matrix progress display",
        "The authorized execution has not started",
        "exactly 80 invocations",
        "excluded from canonical scientific evidence",
        "The real specimen must not be accessed",
    ):
        assert phrase in audit
    assert "Candidate matrix execution progress display" in architecture
    assert "Candidate matrix progress reporting" in reference
    assert "50S.6G.1B.2D.2 candidate progress display" in roadmap
    assert "Candidate matrix progress ownership" in source_tree
    assert "Candidate progress-display coordinate review" in coordinate_guide
    assert "Candidate equivalence-run progress display" in guide
    assert "Candidate matrix progress boundary" in instructions


def test_50s6g1b2d2_records_candidate_progress_verification():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "b0b4432" in document
        assert "2026-09-18" in document
        assert "180" in document
        assert "5.44 seconds" in document
        assert "2647" in document
        assert "239.53 seconds" in document
    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "git diff --check 5aff265...HEAD` reported no errors" in audit
    assert "Candidate 50S.6G.1B.2D.2 verification record" in audit
    assert "Candidate 50S.6G.1B.2D.2 progress verification" in architecture
    assert "50S.6G.1B.2D.2 candidate verification state" in roadmap
    assert "Candidate matrix progress verification" in reference
    assert "Candidate matrix progress verification ownership" in source_tree
    assert "Candidate progress-display verification review" in coordinates
    assert "Candidate equivalence-run progress verification" in guide
    assert "Candidate matrix progress verification boundary" in instructions
    assert "authorized execution has not started" in audit
    assert "renewed authorization remain separate decisions" in audit
    assert "real specimen was not accessed" in guide


def test_50s6g1b2d2_records_progress_display_acceptance():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "scientifically and architecturally accepted" in document
        assert "96b9ba0" in document
        assert "2026-09-18" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Accepted 50S.6G.1B.2D.2 progress-display closure" in audit
    assert "Accepted 50S.6G.1B.2D.2 progress display" in architecture
    assert "50S.6G.1B.2D.2 accepted progress-display state" in roadmap
    assert "Accepted matrix progress display" in reference
    assert "Accepted matrix progress ownership" in source_tree
    assert "Accepted progress-display coordinate review" in coordinates
    assert "Accepted equivalence-run progress display" in guide
    assert "Accepted matrix progress boundary" in instructions
    assert "does not merge the feature branch" in audit
    assert "does not itself authorize execution" in reference
    assert "post-merge renewed authorization" in guide


def test_50s6g1b2d3_records_renewed_single_real_run_authorization():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "9c4b808" in document
        assert "2026-09-18" in document
        assert "renew" in document.lower()
        assert "exactly one" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Renewed 50S.6G.1B.2D.3 one-run authorization" in audit
    assert "Renewed 50S.6G.1B.2D.3 one-run authority" in architecture
    assert "50S.6G.1B.2D.3 renewed single-run authorization" in roadmap
    assert "Renewed single real-run contract" in reference
    assert "Renewed real-run ownership" in source_tree
    assert "Renewed real-run coordinate boundary" in coordinates
    assert "Renewed single real equivalence run" in guide
    assert "Renewed one-run matrix authority" in instructions
    assert "at most 80 fresh subprocess invocations" in audit
    assert "There is no automatic retry or resume" in audit
    assert "consumes this authorization" in audit
    assert "candidate evidence requiring independent review" in audit


def test_50s6g1b2d3_records_acceptance_of_renewed_authorization():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "scientifically and architecturally accepted" in document
        assert "dd71e01" in document
        assert "2026-09-18" in document
        assert "169" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "4.29 seconds" in audit
    assert "Accepted 50S.6G.1B.2D.3 renewed authorization" in audit
    assert "Accepted 50S.6G.1B.2D.3 renewed authority" in architecture
    assert "50S.6G.1B.2D.3 accepted renewed authorization" in roadmap
    assert "Accepted renewed real-run contract" in reference
    assert "Accepted renewed real-run ownership" in source_tree
    assert "Accepted renewed real-run coordinate boundary" in coordinates
    assert "Accepted renewed single real run" in guide
    assert "Accepted renewed one-run authority" in instructions
    assert "run remains unstarted and unconsumed" in audit
    assert "only after this record is merged" in audit
    assert "external preflight" in audit


def test_50s6g1b2d4_records_candidate_first_real_matrix_evidence():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258" in document
        assert "9d93113" in document
        assert "2026-09-18" in document
        assert "zero crossings" in document
        assert "candidate" in document.lower()

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Candidate 50S.6G.1B.2D.4 first real-matrix evidence" in audit
    assert "Candidate 50S.6G.1B.2D.4 real-matrix evidence" in architecture
    assert "50S.6G.1B.2D.4 candidate real-matrix evidence" in roadmap
    assert "Candidate first real-matrix evidence" in reference
    assert "Candidate first real-matrix evidence ownership" in source_tree
    assert "Candidate first real-matrix coordinate finding" in coordinates
    assert "Candidate first real equivalence evidence" in guide
    assert "Candidate first real-matrix evidence boundary" in instructions

    for phrase in (
        "0cad196ea850a26d7cb5a2b73e73d932f06b2ae1ba2e36d745a1c3f1b2beb26c",
        "64b5b4f99ca09fc78cdabb4a487382425317bacf71075825d40b3f28d4adee72",
        "2,455 reject, 101 indeterminate, and 4 retain",
        "38,292.318 wall seconds",
        "13,636.603 wall seconds",
        "2.694 to 2.865",
        "authorization is consumed",
    ):
        assert phrase in audit
    assert "positive-crossing behavior remains covered by synthetic evidence" in audit
    assert "no universal speed, capacity, memory, or hardware claim" in audit


def test_50s6g1b2d4_records_acceptance_of_first_real_matrix_evidence():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_equivalence_matrix_audit_50s6g1b2d.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "scientifically and architecturally accepted" in document
        assert "186e255" in document
        assert "d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258" in document
        assert "2026-09-18" in document
        assert "zero crossings" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Accepted 50S.6G.1B.2D.4 first real-matrix evidence" in audit
    assert "Accepted 50S.6G.1B.2D.4 real-matrix evidence" in architecture
    assert "50S.6G.1B.2D.4 accepted first real-matrix evidence" in roadmap
    assert "Accepted first real-matrix evidence" in reference
    assert "Accepted first real-matrix evidence ownership" in source_tree
    assert "Accepted first real-matrix coordinate finding" in coordinates
    assert "Accepted first real equivalence evidence" in guide
    assert "Accepted first real-matrix evidence boundary" in instructions

    assert "171 plugin-disabled documentation tests passing in 4.46 seconds" in audit
    assert "deterministic empty-result equivalence" in audit
    assert "does not establish positive real-crossing validation" in audit
    assert "authorize another real run" in audit
    assert "authorize parallelization or refactoring" in audit


def test_50s6g1b_candidate_bounded_closure_preserves_limitations():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_snapshot_preflight_audit_50s6g1b.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "b010a6c" in document
        assert "zero crossings" in document
        assert "50S.6G.2A" in document
        assert "documentation audit" in document
        assert "unauthorized" in document or "not authorized" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Candidate 50S.6G.1B bounded closure audit" in audit
    assert "Candidate bounded 50S.6G.1B closure" in architecture
    assert "50S.6G.1B candidate bounded closure state" in roadmap
    assert "Candidate 50S.6G.1B closure boundary" in reference
    assert "Candidate 50S.6G.1B closure ownership" in source_tree
    assert "Candidate 50S.6G.1B closure coordinate review" in coordinates
    assert "Candidate bounded 50S.6G.1B closure" in guide
    assert "Candidate bounded 50S.6G.1B closure boundary" in instructions

    for phrase in (
        "d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258",
        "60 measured observations",
        "Positive-crossing behavior remains synthetic evidence",
        "full 16,559-record matrix",
        "FoV counts 1, 2, 5, 20, or 50",
        "The consumed one-run authority is not renewed",
        "changes no runtime",
        "not report implementation",
    ):
        assert phrase in audit

    assert "full-snapshot matrix" in roadmap
    assert "No production ownership changes" in source_tree
    assert "introduces no coordinate operation" in coordinates
    assert "The one-run authority is consumed" in instructions


def test_50s6g1b_records_accepted_bounded_closure():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_snapshot_preflight_audit_50s6g1b.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
        )
    )
    for document in documents:
        assert "scientifically and architecturally accepted" in document
        assert "2026-09-19" in document
        assert "c62a451" in document
        assert "173" in document
        assert "3.82 seconds" in document
        assert "50S.6G.2A documentation audit" in document
        assert "zero crossings" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, guide, instructions = documents
    assert "Accepted 50S.6G.1B bounded closure" in audit
    assert "Accepted bounded 50S.6G.1B closure" in architecture
    assert "50S.6G.1B accepted bounded closure" in roadmap
    assert "Accepted 50S.6G.1B closure boundary" in reference
    assert "Accepted 50S.6G.1B closure ownership" in source_tree
    assert "Accepted 50S.6G.1B closure coordinate review" in coordinates
    assert "Accepted bounded 50S.6G.1B closure" in guide
    assert "Accepted bounded 50S.6G.1B closure boundary" in instructions

    assert "The consumed execution authority is not renewed" in audit
    assert "Implementation is not authorized" in roadmap
    assert "No report API" in reference
    assert "no new production module" in source_tree
    assert "may not implement serialization" in coordinates
    assert "The one-run authority remains consumed" in instructions

def test_50s6g2a_candidate_exact_crossing_report_audit():
    audit = " ".join(read(
        DEVELOPER / "satellite_exact_crossing_report_audit_50s6g2a.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            SATELLITE_PROGRAM_LOG,
            INSTRUCTIONS,
            DEVELOPER / "satellite_delivery_audit_50s6g.md",
        )
    )

    assert "satellite_exact_crossing_report_audit_50s6g2a.md" in index
    for phrase in (
        "wenu.artificial_satellite_exact_crossing_report",
        "geometric exact local crossings — visibility not evaluated",
        "validated field with zero crossings",
        "satellite_presentations.py",
        "caller-supplied immutable creation time",
        "report_identity_sha256",
        "additionalProperties: false",
        "JSON Schema Draft 2020-12",
        "duplicate object keys",
        "from_json(report.to_json()) == report",
        "tests/test_satellite_crossing_reports.py",
        "future-science values must be JSON `null`",
        "Atomic filesystem publication belongs to 50S.6G.2C",
        "Until that acceptance, no 50S.6G.2A implementation is authorized",
    ):
        assert phrase in audit

    for document in documents:
        assert "50S.6G.2A" in document
        assert "candidate" in document.lower()
        assert "no runtime" in document.lower() or "no production" in document.lower() or "no implementation" in document.lower()

    assert "distinct renderer-neutral exact-crossing logical model" in documents[0]
    assert "No exact-report API exists" in documents[2]
    assert "closest existing owner is `satellite_presentations.py`" in documents[3]
    assert "introduces no coordinate operation" in documents[4]
    assert "not a visibility forecast" in documents[5]
    assert "Do not implement until Fernando separately accepts" in documents[6]
    assert "Candidate 50S.6G.2A exact-report refinement" in documents[7]

def test_satellite_guide_is_pedagogical_and_history_is_separate():
    guide = read(DEVELOPER / "satellite_guide.md")
    log = read(SATELLITE_PROGRAM_LOG)
    index = read(DEVELOPER / "README.md")

    for phrase in (
        "Acronyms and specialized abbreviations",
        "Canonical satellite flow",
        "Propagation and reference systems",
        "Field and crossing definitions",
        "Complete-scan correctness oracle",
        "Conservative high-performance search",
        "Illumination",
        "Apparent brightness",
        "Validation hierarchy",
        "Source ownership direction",
        "Exact crossing reports",
    ):
        assert phrase in guide

    assert "Candidate real-execution readiness audit" not in guide
    assert "Accepted first real equivalence evidence" not in guide
    assert "Candidate real-execution readiness audit" in log
    assert "Accepted first real equivalence evidence" in log
    assert "Accepted 50S.6G.2A exact-report audit" in log
    assert "pedagogical artificial-satellite" in index
    assert "chronological 50S" in index


def test_satellite_guide_explains_orbital_elements_and_precession():
    guide = " ".join(read(DEVELOPER / "satellite_guide.md").split())

    for phrase in (
        "Keplerian elements: osculating geometry and Wenu's mean-element input",
        "instantaneous two-body conic",
        "MEAN_ELEMENT_THEORY = SGP4",
        "does **not** turn a GP record into osculating elements",
        "dOmega/dt = -(3/2) J2 n (R_E / p)^2 cos(i)",
        "domega/dt = (3/4) J2 n (R_E / p)^2 (5 cos(i)^2 - 1)",
        "a^(-7/2)",
        "(1 - e^2)^(-2)",
        "critical inclinations near 63.4 and 116.6 degrees",
        "+0.986 degree per day",
        "GPS-like MEO",
        "about -0.04 degree/day",
        "SGP4 drag-like fit parameter",
        "https://public.ccsds.org/Pubs/502x0b3e1.pdf",
        "AIAA-2006-6753-Rev3.pdf",
        "gp-data-formats.php",
    ):
        assert phrase in guide

def test_50s6g2a_records_acceptance_and_bounded_implementation_authority():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            DEVELOPER / "satellite_exact_crossing_report_audit_50s6g2a.md",
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            INSTRUCTIONS,
            DEVELOPER / "satellite_delivery_audit_50s6g.md",
            SATELLITE_PROGRAM_LOG,
        )
    )
    for document in documents:
        assert "scientifically and architecturally accepted" in document or "Fernando accepted" in document
        assert "2026-09-19" in document
        assert "835ddfe" in document
        assert "175" in document
        assert "3.27 seconds" in document

    audit, architecture, roadmap, reference, source_tree, coordinates, instructions, delivery, log = documents
    assert "Accepted audit and handoff" in audit
    assert "Accepted 50S.6G.2A exact-report audit" in architecture
    assert "50S.6G.2A accepted audit state" in roadmap
    assert "Accepted 50S.6G.2A implementation authorization" in reference
    assert "Accepted 50S.6G.2A implementation ownership" in source_tree
    assert "Accepted 50S.6G.2A coordinate boundary" in coordinates
    assert "Accepted 50S.6G.2A implementation boundary" in instructions
    assert "Accepted 50S.6G.2A audit handoff" in delivery
    assert "Accepted 50S.6G.2A exact-report audit" in log
    assert "50S.6G.2B and later work remain unauthorized" in roadmap
    assert "Do not implement ECSV/VOTable" in instructions

def test_50s6g2a_candidate_implementation_is_bounded_and_propagated():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            DEVELOPER / "satellite_guide.md",
            INSTRUCTIONS,
            SATELLITE_PROGRAM_LOG,
        )
    )

    architecture, roadmap, reference, source_tree, coordinates, guide, instructions, log = documents
    assert "satellite_crossing_reports.py" in architecture
    assert "50S.6G.2A candidate implementation state" in roadmap
    assert "Candidate exact-crossing report API" in reference
    assert "satellite_exact_crossing_report_v1.schema.json" in source_tree
    assert "introduces no new frame" in coordinates
    assert "Null means “not evaluated,” not false, dark, zero, or absent" in guide
    assert "Do not add ECSV/VOTable" in instructions
    assert "99 tests in 119.54 seconds" in log
    assert "2,676 tests in 234.08 seconds" in log
    assert "a65e5ac" in log
    assert "ECSV/VOTable remains 50S.6G.2B" in roadmap
    assert "CLI/files and atomic publication remain 50S.6G.2C" in roadmap
    assert "exact tracks remain 50S.6G.3A" in roadmap

def test_50s6g2a_records_accepted_implementation_boundary():
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            INSTRUCTIONS,
            SATELLITE_PROGRAM_LOG,
        )
    )
    for document in documents:
        assert (
            "Fernando scientifically and architecturally accepted the bounded "
            "50S.6G.2A implementation on 2026-09-19"
        ) in document
        assert "a65e5ac" in document
        assert "2,676" in document
        assert "234.08 seconds" in document
        assert "8af0d14" in document
        assert "179" in document
        assert "5.05 seconds" in document

    architecture, roadmap, reference, source_tree, coordinates, instructions, log = documents
    assert "Accepted 50S.6G.2A exact-report implementation" in architecture
    assert "50S.6G.2A accepted implementation" in roadmap
    assert "Accepted 50S.6G.2A exact-report API" in reference
    assert "Accepted 50S.6G.2A implementation ownership" in source_tree
    assert "Accepted 50S.6G.2A coordinate finding" in coordinates
    assert "Accepted 50S.6G.2A implementation boundary" in instructions
    assert "Accepted 50S.6G.2A exact-report implementation" in log
    assert "No later milestone is authorized by this acceptance" in roadmap


def test_50s6g2b_candidate_tabular_audit_is_lossless_reusable_and_bounded():
    audit = " ".join(read(
        DEVELOPER / "satellite_tabular_report_audit_50s6g2b.md"
    ).split())
    index = " ".join(read(DEVELOPER / "README.md").split())
    documents = tuple(
        " ".join(read(path).split())
        for path in (
            V09_CURRENT,
            FUTURE_ROADMAP,
            DEVELOPER / "implementation_reference.md",
            DEVELOPER / "source_tree.md",
            COORDINATE_GUIDE,
            DEVELOPER / "satellite_guide.md",
            INSTRUCTIONS,
            DEVELOPER / "satellite_delivery_audit_50s6g.md",
            SATELLITE_PROGRAM_LOG,
        )
    )

    assert "satellite_tabular_report_audit_50s6g2b.md" in index
    for phrase in (
        "one shared reusable format-neutral tabular projection",
        "thin format adapters",
        "report_identity_sha256",
        "validated field with zero crossings",
        'serialize_method="data_mask"',
        "VOTable 1.5",
        "BINARY2",
        'timescale="UTC"',
        'refposition="TOPOCENTER"',
        "from_ecsv(report.to_ecsv()) == report",
        "from_votable(report.to_votable()) == report",
        "Atomic filesystem publication belongs to 50S.6G.2C",
        "no 50S.6G.2B implementation is authorized",
    ):
        assert phrase in audit

    for document in documents:
        assert "50S.6G.2B" in document
        assert "reusable" in document

    architecture, roadmap, reference, source_tree, coordinates, guide, instructions, delivery, log = documents
    assert "alternate lossless carriers" in architecture
    assert "Candidate 50S.6G.2B tabular API" in reference
    assert "exactly one format-neutral mapping" in source_tree
    assert "introduces no new frame" in coordinates
    assert "scientific flattening and validation are written once" in guide
    assert "Do not implement 50S.6G.2B" in instructions
    assert "authorizes no runtime work" in roadmap
    assert "authorizes no implementation" in delivery
    assert "candidate audit, not acceptance" in log


def test_50s6g2b_records_candidate_verification_without_acceptance():
    audit = " ".join(read(
        DEVELOPER / "satellite_tabular_report_audit_50s6g2b.md"
    ).split())
    log = " ".join(read(SATELLITE_PROGRAM_LOG).split())

    for document in (audit, log):
        assert "ef14bc1" in document
        assert "181" in document
        assert "4.88 seconds" in document
        assert "57c8bec" in document
        assert "clean" in document
        assert "synchronized" in document

    assert "documentation consistency only" in audit
    assert "not scientific or architectural acceptance" in log


def test_50s6g2b_records_scientific_and_architectural_acceptance():
    documents = (
        read(DEVELOPER / "satellite_tabular_report_audit_50s6g2b.md"),
        read(DEVELOPER / "assistant_instructions.md"),
        read(DEVELOPER / "current_architecture_v0.9.md"),
        read(DEVELOPER / "implementation_reference.md"),
        read(DEVELOPER / "post_v0.9_architecture_roadmap.md"),
        read(DEVELOPER / "coordinate_system_guide_v0.9.5.md"),
        read(DEVELOPER / "source_tree.md"),
        read(SATELLITE_PROGRAM_LOG),
    )
    normalized = tuple(" ".join(document.split()) for document in documents)

    for document in normalized:
        assert "scientifically and architecturally accepted" in document
        assert "2026-09-19" in document
        assert "ef14bc1" in document
        assert "181" in document
        assert "4.88 seconds" in document
        assert "reusable" in document

    audit, instructions, architecture, reference, roadmap, coordinates, source_tree, log = normalized
    assert "Only a bounded in-memory implementation is authorized next" in audit
    assert "Implement only one reusable format-neutral" in instructions
    assert "Canonical JSON and `report_identity_sha256` remain the logical authority" in architecture
    assert "to_ecsv()" in reference
    assert "50S.6G.2C filesystem/CLI publication" in roadmap
    assert "coordinate guide remains current" in coordinates
    assert "exactly one reusable format-neutral mapping" in source_tree
    assert "new execution remain unauthorized" in log



def test_50s6g2b_candidate_unicode_null_amendment_is_explicit_and_bounded():
    audit = " ".join(read(
        DEVELOPER / "satellite_tabular_report_audit_50s6g2b.md"
    ).split())
    instructions = " ".join(read(INSTRUCTIONS).split())

    for document in (audit, instructions):
        assert "Astropy 7.1.0" in document
        assert "BINARY2 null flags" in document
        assert "__is_null" in document
        assert "shared logical projection" in document
        assert "report_identity_sha256" in document
        assert "empty string as null" in document
        assert "runtime" in document

    assert "no further" in audit
    assert "make further runtime changes" in instructions
    assert "Astropy issue 8995" in audit
    assert "Numeric and Boolean nulls continue to use BINARY2 null flags" in audit
    assert "true indicator paired with a non-empty carrier" in audit
    assert "does not introduce a private BINARY2 parser" in audit
    assert "documentation-only and unaccepted" in instructions
