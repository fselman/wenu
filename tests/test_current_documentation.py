Warning: truncated output (original token count: 91245)
Total output lines: 8510

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
            DEVELOPER / "archive/milestone_history/49i_solar_system/observed_venus_disk_sequence_49i3c…41245 tokens truncated…-only provider, acquisition, publication, admission, and performance-evidence audit",
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

    (
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinates,
        instructions,
        log,
    ) = documents
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



def test_50s6g2b_records_unicode_null_amendment_acceptance():
    documents = (
        read(DEVELOPER / "satellite_tabular_report_audit_50s6g2b.md"),
        read(INSTRUCTIONS),
    )
    for document in (" ".join(value.split()) for value in documents):
        assert "scientifically and architecturally accepted" in document
        assert "5038e4a" in document
        assert "184" in document
        assert "5.28 seconds" in document
        assert "__is_null" in document
        assert "shared logical projection" in document
        assert "ECSV" in document
        assert "canonical JSON" in document



def test_50s6g2b_records_candidate_implementation_verification():
    documents = (
        read(DEVELOPER / "satellite_tabular_report_audit_50s6g2b.md"),
        read(INSTRUCTIONS),
        read(SATELLITE_PROGRAM_LOG),
    )
    for document in (" ".join(value.split()) for value in documents):
        assert "3bbd82f" in document
        assert "208" in document
        assert "6.68 seconds" in document
        assert "2,689" in document
        assert "215.15 seconds" in document
        assert "canonical JSON" in document
        assert "report_identity_sha256" in document
        assert "__is_null" in document
        assert "candidate" in document
        assert "acceptance" in document
        assert "50S.6G.2C" in document

    audit = " ".join(documents[0].split())
    assert "coordinate-system guide was reviewed and remains current" in audit
    assert "verification evidence, not scientific or architectural acceptance" in audit



def test_50s6g2b_records_complete_implementation_acceptance():
    paths = (
        DEVELOPER / "satellite_tabular_report_audit_50s6g2b.md",
        INSTRUCTIONS,
        V09_CURRENT,
        DEVELOPER / "implementation_reference.md",
        DEVELOPER / "source_tree.md",
        FUTURE_ROADMAP,
        COORDINATE_GUIDE,
        SATELLITE_PROGRAM_LOG,
    )
    documents = tuple(" ".join(read(path).split()) for path in paths)

    for document in documents:
        assert "scientifically and architecturally accepted the complete bounded" in document
        assert "2026-09-19" in document
        assert "3bbd82f" in document
        assert "208" in document
        assert "6.68 seconds" in document
        assert "2,689" in document
        assert "215.15 seconds" in document
        assert "ece80c7" in document
        assert "186" in document
        assert "4.60 seconds" in document
        assert "canonical json" in document.lower()
        assert "report_identity_sha256" in document
        assert "__is_null" in document
        assert "no later" in document.lower()

    audit, instructions, architecture, reference, source_tree, roadmap, coordinates, log = documents
    assert "Accepted complete 50S.6G.2B implementation" in audit
    assert "Accepted complete 50S.6G.2B implementation boundary" in instructions
    assert "Accepted complete 50S.6G.2B in-memory interoperability" in architecture
    assert "Accepted complete 50S.6G.2B tabular API" in reference
    assert "Accepted complete 50S.6G.2B ownership" in source_tree
    assert "50S.6G.2B complete implementation accepted" in roadmap
    assert "Accepted complete 50S.6G.2B coordinate finding" in coordinates
    assert "Accepted complete 50S.6G.2B in-memory interoperability" in log
    assert "50S.6G.2C filesystem/CLI publication" in roadmap


def test_50s6g2c_candidate_cli_file_protocol_is_atomic_explicit_and_bounded():
    audit = " ".join(read(
        DEVELOPER / "satellite_cli_file_protocol_audit_50s6g2c.md"
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

    assert "satellite_cli_file_protocol_audit_50s6g2c.md" in index
    for phrase in (
        "wenu_satellite_crossings",
        "direct arguments",
        "--request PATH",
        "--validated-request PATH",
        "no FoV is solved",
        "derived_request: null",
        "report.json",
        "report.ecsv",
        "report.vot",
        "manifest.json",
        "manifest_identity_sha256",
        "no-clobber failure",
        "SIGINT/KeyboardInterrupt returns 130",
        "SIGTERM",
        "Filesystem atomicity is limited to one filesystem",
        "invalid FoVs do not reach",
        "This candidate authorizes no implementation",
    ):
        assert phrase in audit

    for document in documents:
        assert "50S.6G.2C" in document

    architecture, roadmap, reference, source_tree, coordinates, guide, instructions, delivery, log = documents
    assert "dedicated CLI adapter" in architecture
    assert "authorizes no implementation" in roadmap
    assert "mutually exclusive" in reference
    assert "No production module or test file is added" in source_tree
    assert "introduces no new frame" in coordinates
    assert "audit-preserving selection protocol" in guide
    assert "Do not implement 50S.6G.2C" in instructions
    assert "authorizes no implementation" in delivery
    assert "candidate audit, not acceptance" in log


def test_50s6g2c_records_acceptance_and_only_bounded_implementation_authority():
    audit = " ".join(read(
        DEVELOPER / "satellite_cli_file_protocol_audit_50s6g2c.md"
    ).split())
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

    for phrase in (
        "scientifically and architecturally accepted",
        "bcac40453ae244348b9fc33447246db1c587d722",
        "188 plugin-disabled",
        "5.29 seconds",
        "Implement only the bounded offline CLI/filesystem adapter",
        "This acceptance does not authorize provider access",
    ):
        assert phrase in audit

    architecture, roadmap, reference, source_tree, coordinates, guide, instructions, delivery, log = documents
    assert "Accepted 50S.6G.2C audit boundary" in architecture
    assert "50S.6G.2C accepted audit and next authority" in roadmap
    assert "Accepted 50S.6G.2C implementation authorization" in reference
    assert "Accepted 50S.6G.2C implementation ownership" in source_tree
    assert "Accepted 50S.6G.2C coordinate finding" in coordinates
    assert "Accepted 50S.6G.2C reader boundary" in guide
    assert "Accepted 50S.6G.2C audit boundary" in instructions
    assert "Accepted 50S.6G.2C audit handoff" in delivery
    assert "Accepted 50S.6G.2C audit" in log
    assert "50S.6G.3A and all track, chart" in roadmap


def test_50s6g2c_candidate_implementation_is_bounded_and_offline():
    project = read(ROOT / "pyproject.toml")
    cli = read(ROOT / "src/wenu/cli/satellite_crossings.py")
    batch = read(ROOT / "src/wenu/satellites/crossing_batch.py")
    source_tree = " ".join(read(DEVELOPER / "source_tree.md").split())
    architecture = " ".join(read(V09_CURRENT).split())
    roadmap = " ".join(read(FUTURE_ROADMAP).split())
    reference = " ".join(
        read(DEVELOPER / "implementation_reference.md").split()
    )
    instructions = " ".join(read(INSTRUCTIONS).split())

    assert (
        'wenu_satellite_crossings = "wenu.cli.satellite_crossings:main"'
        in project
    )
    assert "def validate(self, request):" in batch
    assert "without solving any crossing" in batch
    for phrase in (
        "REQUEST_PRODUCT",
        "VALIDATION_PRODUCT",
        "MANIFEST_PRODUCT",
        "RENAME_EXCL",
        "RENAME_NOREPLACE",
        "report.json",
        "report.ecsv",
        "report.vot",
        "manifest.json",
        "return 130",
        "return 143",
    ):
        assert phrase in cli
    for name in (
        "satellite_crossing_request_v1.schema.json",
        "satellite_crossing_validation_v1.schema.json",
        "satellite_crossing_bundle_manifest_v1.schema.json",
    ):
        assert (ROOT / "src/wenu/data" / name).is_file()

    assert "Candidate 50S.6G.2C implementation state" in architecture
    assert "50S.6G.2C candidate implementation" in roadmap
    assert "Candidate 50S.6G.2C executable API" in reference
    assert "Candidate 50S.6G.2C implementation placement" in source_tree
    assert "Candidate 50S.6G.2C implementation boundary" in instructions
    assert "Do not merge or begin 50S.6G.3A" in instructions


def test_50s6g2c_records_candidate_verification_without_acceptance():
    audit = " ".join(read(
        DEVELOPER / "satellite_cli_file_protocol_audit_50s6g2c.md"
    ).split())
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

    for phrase in (
        "e08ebf5e0061dbf1e69c8cc58a55a9696e785300",
        "235-test immediate",
        "7.63 seconds",
        "2,709-test plugin-disabled suite",
        "237.35 seconds",
        "verified candidate awaiting",
        "not acceptance",
        "Do not merge or begin 50S.6G.3A",
    ):
        assert phrase in audit

    (
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinates,
        instructions,
        log,
    ) = documents
    assert "Verified candidate 50S.6G.2C implementation" in architecture
    assert "50S.6G.2C verified candidate state" in roadmap
    assert "Verified candidate 50S.6G.2C API" in reference
    assert "Verified candidate 50S.6G.2C placement" in source_tree
    assert "Verified candidate 50S.6G.2C coordinate review" in coordinates
    assert (
        "Candidate 50S.6G.2C implementation verification boundary"
        in instructions
    )
    assert "Verified candidate 50S.6G.2C implementation" in log
    assert "Merge and 50S.6G.3A remain unauthorized" in roadmap


def test_50s6g2c_records_accepted_implementation_and_next_audit_only():
    audit = " ".join(read(
        DEVELOPER / "satellite_cli_file_protocol_audit_50s6g2c.md"
    ).split())
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

    for phrase in (
        "scientifically and architecturally accepted",
        "e08ebf5e0061dbf1e69c8cc58a55a9696e785300",
        "f2bb49c6f44281428d546d5d2adbf35f74b7fc6d",
        "2,709 plugin-disabled tests",
        "191 current-documentation tests",
        "Only a separately bounded documentation-first 50S.6G.3A",
        "no track implementation is authorized",
    ):
        assert phrase in audit

    architecture, roadmap, reference, source_tree, coordinates, instructions, log = documents
    assert "Accepted 50S.6G.2C implementation" in architecture
    assert "50S.6G.2C accepted implementation" in roadmap
    assert "Accepted 50S.6G.2C executable API" in reference
    assert "Accepted 50S.6G.2C ownership" in source_tree
    assert "Accepted 50S.6G.2C coordinate closure" in coordinates
    assert "Accepted 50S.6G.2C implementation boundary" in instructions
    assert "Accepted 50S.6G.2C implementation" in log
    assert "50S.6G.3A documentation audit is authorized next" in roadmap

def test_50s6g3a_candidate_exact_local_track_audit_is_bounded():
    audit = " ".join(read(
        DEVELOPER / "satellite_exact_local_track_audit_50s6g3a.md"
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

    assert "satellite_exact_local_track_audit_50s6g3a.md" in index
    for phrase in (
        "one accepted connected visit",
        "entry, closest-approach, and exit",
        "normalized spherical chord midpoint",
        "maximum sample interval",
        "It is not a proof of a global continuous maximum error",
        "returns no partial track",
        "track_identity_sha256",
        "exact local connected-visit track",
        "SatChecker sampled candidate evidence — not verified crossings",
        "must not reuse `SolarSystemTrackResult`",
        "report.json",
        "This candidate authorizes no implementation",
        "50S.6G.3B chart integration",
        "50S.6G.4A/B planisphere work",
    ):
        assert phrase in audit

    (
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinates,
        guide,
        instructions,
        delivery,
        log,
    ) = documents
    assert "Candidate 50S.6G.3A exact-local-track boundary" in architecture
    assert "50S.6G.3A candidate audit state" in roadmap
    assert "Candidate 50S.6G.3A exact-local-track API" in reference
    assert "Candidate 50S.6G.3A ownership" in source_tree
    assert "Candidate 50S.6G.3A exact-track coordinate finding" in coordinates
    assert "Candidate exact local track evidence" in guide
    assert "Candidate 50S.6G.3A audit boundary" in instructions
    assert "50S.6G.3A candidate refinement" in delivery
    assert "Candidate 50S.6G.3A exact-local-track audit" in log
    assert "50S.6G.3B binocular/regional chart integration" in roadmap
    assert "no implementation is yet authorized" in guide

def test_50s6g3a_records_acceptance_and_only_bounded_implementation_authority():
    audit = " ".join(read(
        DEVELOPER / "satellite_exact_local_track_audit_50s6g3a.md"
    ).split())
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

    for phrase in (
        "scientifically and architecturally accepted",
        "ce549715889c135e17b87749f3860855b1b54447",
        "193 plugin-disabled current-documentation tests",
        "5.73 seconds",
        "Implement only the bounded 50S.6G.3A",
        "This acceptance does not authorize 50S.6G.3B",
        "implementation remains a candidate",
    ):
        assert phrase in audit

    architecture, roadmap, reference, source_tree, coordinates, guide, instructions, delivery, log = documents
    assert "Accepted 50S.6G.3A audit boundary" in architecture
    assert "50S.6G.3A accepted audit and next authority" in roadmap
    assert "Accepted 50S.6G.3A implementation authorization" in reference
    assert "Accepted 50S.6G.3A implementation ownership" in source_tree
    assert "Accepted 50S.6G.3A coordinate boundary" in coordinates
    assert "Accepted exact local track audit" in guide
    assert "Accepted 50S.6G.3A audit boundary" in instructions
    assert "Accepted 50S.6G.3A audit refinement" in delivery
    assert "Accepted 50S.6G.3A audit" in log
    assert "50S.6G.3B and 50S.6G.4A/B remain unauthorized" in roadmap

def test_50s6g3a_candidate_implementation_is_exact_output_neutral_and_bounded():
    audit = " ".join(read(
        DEVELOPER / "satellite_exact_local_track_audit_50s6g3a.md"
    ).split())
    source = read(ROOT / "src/wenu/satellites/exact_tracks.py")
    layer = read(ROOT / "src/wenu/sky/satellite_exact_track_layer.py")
    coordinate_service = read(ROOT / "src/wenu/coordinate_service.py")
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

    for phrase in (
        "Accepted implementation-preflight representation resolution",
        "sample_time_scale",
        "Candidate 50S.6G.3A implementation",
        "98a756d4405ba60756e3899d9a0886029cfa8afd",
        "69 tests in 75.58 seconds",
        "not scientific or architectural implementation acceptance",
    ):
        assert phrase in audit
    for phrase in (
        "class ExactLocalTrackPolicy",
        "class ExactLocalSatelliteTrackSample",
        "class ExactLocalSatelliteTrack",
        "class ExactLocalTrackError",
        "class ExactLocalSatelliteTrackRealizer",
        "track_identity_sha256",
        "maximum_step_seconds",
        "adaptive subdivision exceeded",
    ):
        assert phrase in source
    assert "class SatelliteExactTrackLayer" in layer
    assert "class SatelliteExactTrackEventsLayer" in layer
    assert "recomputed" in layer
    assert 'if frame == "gcrs-axes"' in coordinate_service

    architecture, roadmap, reference, source_tree, coordinates, guide, instructions, delivery, log = documents
    assert "Candidate 50S.6G.3A implementation state" in architecture
    assert "50S.6G.3A candidate implementation" in roadmap
    assert "Candidate 50S.6G.3A executable API" in reference
    assert "Candidate 50S.6G.3A implementation placement" in source_tree
    assert "Candidate 50S.6G.3A implemented coordinate representation" in coordinates
    assert "Candidate exact local track implementation" in guide
    assert "Candidate 50S.6G.3A implementation boundary" in instructions
    assert "50S.6G.3A candidate implementation state" in delivery
    assert "Candidate 50S.6G.3A implementation" in log
    assert "Do not merge or begin 50S.6G.3B" in instructions

def test_50s6g3a_records_complete_candidate_verification_without_acceptance():
    audit = " ".join(read(
        DEVELOPER / "satellite_exact_local_track_audit_50s6g3a.md"
    ).split())
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

    for phrase in (
        "f0a41648dc5565e4a8deed5d7bb6640a3df4e2d1",
        "2,728 plugin-disabled repository tests",
        "222.01 seconds",
        "195 tests in 5.86 seconds",
        "not scientific or architectural implementation acceptance",
        "Do not merge or begin 50S.6G.3B",
    ):
        assert phrase in audit

    architecture, roadmap, reference, source_tree, coordinates, instructions, log = documents
    assert "Verified candidate 50S.6G.3A implementation" in architecture
    assert "50S.6G.3A verified candidate state" in roadmap
    assert "Verified candidate 50S.6G.3A API" in reference
    assert "Verified candidate 50S.6G.3A placement" in source_tree
    assert "Verified candidate 50S.6G.3A coordinate representation" in coordinates
    assert (
        "Candidate 50S.6G.3A implementation verification boundary"
        in instructions
    )
    assert "Verified candidate 50S.6G.3A implementation" in log
    assert "Merge and 50S.6G.3B remain unauthorized" in roadmap

def test_50s6g3a_records_accepted_implementation_and_next_audit_only():
    audit = " ".join(read(
        DEVELOPER / "satellite_exact_local_track_audit_50s6g3a.md"
    ).split())
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

    for phrase in (
        "scientifically and architecturally accepted",
        "f0a41648dc5565e4a8deed5d7bb6640a3df4e2d1",
        "0182224a5e41074f87ce6507d52b981eeeda5ed8",
        "2,728 plugin-disabled repository tests",
        "196 documentation tests",
        "Only a separately bounded documentation-first 50S.6G.3B",
        "No chart implementation",
    ):
        assert phrase in audit

    architecture, roadmap, reference, source_tree, coordinates, guide, instructions, delivery, log = documents
    assert "Accepted 50S.6G.3A implementation" in architecture
    assert "50S.6G.3A accepted implementation" in roadmap
    assert "Accepted 50S.6G.3A API" in reference
    assert "Accepted 50S.6G.3A ownership" in source_tree
    assert "Accepted 50S.6G.3A coordinate representation" in coordinates
    assert "Accepted exact local track implementation" in guide
    assert "Accepted 50S.6G.3A implementation boundary" in instructions
    assert "Accepted 50S.6G.3A implementation closure" in delivery
    assert "Accepted complete 50S.6G.3A implementation" in log
    assert "Chart implementation and 50S.6G.4A/B remain unauthorized" in roadmap

def test_50s6g3b_candidate_chart_integration_audit_is_bounded():
    audit = " ".join(read(
        DEVELOPER / "satellite_binocular_regional_track_audit_50s6g3b.md"
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

    assert "satellite_binocular_regional_track_audit_50s6g3b.md" in index
    for phrase in (
        "SatelliteExactTrackDisplayRequest",
        "satellite_exact_tracks",
        "regional",
        "binocular",
        "already-realized",
        "draw_path",
        "draw_events",
        "label_events",
        "Fixed product-frame meaning",
        "chart observer UTC instant equals",
        "does not reinterpret each vertex as simultaneous",
        "request-build cleanup",
        "track_identity_sha256",
        "PNG, PDF, and semantic SVG",
        "must not recursively serialize the full exact evidence object",
        "No invalid or mismatched track is silently dropped",
        "This candidate authorizes no implementation",
        "50S.6G.4A/B planisphere work",
    ):
        assert phrase in audit

    architecture, roadmap, reference, source_tree, coordinates, guide, instructions, delivery, log = documents
    assert "Candidate 50S.6G.3B binocular/regional chart boundary" in architecture
    assert "50S.6G.3B candidate audit state" in roadmap
    assert "Candidate 50S.6G.3B chart-request API" in reference
    assert "Candidate 50S.6G.3B ownership" in source_tree
    assert "Candidate 50S.6G.3B fixed product-frame finding" in coordinates
    assert "Candidate binocular and regional exact-track charts" in guide
    assert "Candidate 50S.6G.3B audit boundary" in instructions
    assert "50S.6G.3B candidate refinement" in delivery
    assert "Candidate 50S.6G.3B chart-integration audit" in log
    assert "50S.6G.4A/B planisphere work" in roadmap

def test_50s6g3b_records_acceptance_and_only_bounded_implementation_authority():
    audit = " ".join(read(
        DEVELOPER / "satellite_binocular_regional_track_audit_50s6g3b.md"
    ).split())
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

    for phrase in (
        "scientifically and architecturally accepted",
        "ef58180f62b99423abbb92da56f9ef08dce8c173",
        "198 plugin-disabled current-documentation tests",
        "5.30 seconds",
        "Implement only the bounded 50S.6G.3B",
        "This acceptance does not authorize 50S.6G.4A/B",
        "implementation remains a candidate",
    ):
        assert phrase in audit

    architecture, roadmap, reference, source_tree, coordinates, guide, instructions, delivery, log = documents
    assert "Accepted 50S.6G.3B audit boundary" in architecture
    assert "50S.6G.3B accepted audit and next authority" in roadmap
    assert "Accepted 50S.6G.3B implementation authorization" in reference
    assert "Accepted 50S.6G.3B implementation ownership" in source_tree
    assert "Accepted 50S.6G.3B coordinate boundary" in coordinates
    assert "Accepted binocular/regional chart audit" in guide
    assert "Accepted 50S.6G.3B audit boundary" in instructions
    assert "Accepted 50S.6G.3B audit refinement" in delivery
    assert "Accepted 50S.6G.3B audit" in log
    assert "50S.6G.4A/B and all later science remain unauthorized" in roadmap


def test_50s6g4a_corrective_altaz_planisphere_audit_is_bounded():
    audit = " ".join(read(
        DEVELOPER
        / "satellite_stereographic_planisphere_track_audit_50s6g4a.md"
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

    assert (
        "satellite_stereographic_planisphere_track_audit_50s6g4a.md"
        in index
    )
    for phrase in (
        'ChartRequest(family="planisphere")',
        "observer-horizontal planisphere",
        "one FullSkyChart",
        "zenith-centred stereographic projection",
        "horizon as the chart boundary",
        "SatelliteExactTrackDisplayRequest",
        "fixed AltAz product frame",
        "track_identity_sha256",
        "No invalid or mismatched track is silently dropped",
        "does not create a crossing entry or exit event",
        "PNG, PDF, and semantic SVG",
        "must not serialize samples",
        "authorizes no implementation",
    ):
        assert phrase in audit

    (
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinates,
        guide,
        instructions,
        delivery,
        log,
    ) = documents
    assert "Corrective 50S.6G.4A ordinary-planisphere boundary" in architecture
    assert "50S.6G.4A corrective audit state" in roadmap
    assert "Corrective 50S.6G.4A proposed request boundary" in reference
    assert "Corrective 50S.6G.4A ownership" in source_tree
    assert "Corrective 50S.6G.4A fixed AltAz planisphere finding" in coordinates
    assert "Corrective ordinary AltAz planisphere audit" in guide
    assert "Corrective 50S.6G.4A AltAz planisphere boundary" in instructions
    assert "Corrective 50S.6G.4A delivery refinement" in delivery
    assert "Corrective 50S.6G.4A AltAz planisphere audit" in log
    assert "This candidate authorizes no implementation" in roadmap


def test_50s6g4a_records_corrective_acceptance_and_bounded_authority():
    audit = " ".join(read(
        DEVELOPER / "satellite_stereographic_planisphere_track_audit_50s6g4a.md"
    ).split())
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

    for phrase in (
        "scientifically and architecturally accepted this corrective",
        "80855938a8711b7cec05190b5c7d33557dace9a9",
        "all 201 plugin-disabled current-documentation tests",
        "6.14 seconds",
        "Implement only the bounded corrected 50S.6G.4B",
        "ordinary AltAz stereographic planisphere integration",
        "This acceptance does not authorize paired polar disks",
        "implementation remains a candidate",
    ):
        assert phrase in audit

    (
        architecture,
        roadmap,
        reference,
        source_tree,
        coordinates,
        guide,
        instructions,
        delivery,
        log,
    ) = documents
    assert (
        "Accepted corrective 50S.6G.4A AltAz planisphere boundary"
        in architecture
    )
    assert "50S.6G.4A corrective audit accepted and next authority" in roadmap
    assert (
        "Accepted corrective 50S.6G.4A implementation authorization"
        in reference
    )
    assert (
        "Accepted corrective 50S.6G.4A implementation ownership"
        in source_tree
    )
    assert "Accepted corrective 50S.6G.4A AltAz coordinate boundary" in coordinates
    assert "Accepted corrective AltAz planisphere audit" in guide
    assert "Accepted corrective 50S.6G.4A boundary" in instructions
    assert "Accepted corrective 50S.6G.4A refinement" in delivery
    assert "Accepted corrective 50S.6G.4A audit" in log
    assert "later satellite work remain unauthorized" in roadmap


def test_50s6g4b_records_verified_altaz_planisphere_candidate():
    audit = read(
        DEVELOPER
        / "satellite_stereographic_planisphere_track_audit_50s6g4a.md"
    )
    documents = tuple(
        read(path)
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

    for phrase in (
        "50S.6G.4B verified candidate implementation record",
        "91eafff5ca7f0069806f7f059d19f7bb9ca123aa",
        "252-test focused gate passed in 7.08 seconds",
        "2,744 plugin-disabled repository tests passed in 220.63 seconds",
        "65 retained samples",
        "3f526de147caae6832c7a56330d460948c4b8963c7cdbf753618682e70d4248a",
        "non-blocking long specimen title",
        "candidate remains unaccepted",
    ):
        assert phrase in audit

    expected = (
        "Verified candidate 50S.6G.4B ordinary-planisphere implementation",
        "50S.6G.4B verified candidate state",
        "Verified candidate 50S.6G.4B request behavior",
        "Verified candidate 50S.6G.4B implementation placement",
        "Verified candidate 50S.6G.4B AltAz behavior",
        "Verified candidate ordinary-planisphere exact track",
        "Verified candidate 50S.6G.4B implementation boundary",
        "Verified candidate 50S.6G.4B delivery evidence",
        "Verified candidate 50S.6G.4B implementation",
    )
    for document, phrase in zip(documents, expected, strict=True):
        assert phrase in document
