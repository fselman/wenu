"""Documentation protection for the 49H.1 ownership contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs" / "developer"


def test_fixed_sky_contract_separates_celestial_and_local_time_owners():
    contract = (
        DEVELOPER / "fixed_sky_rotating_horizon_49h1.md"
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
        "FixedSkyRotatingHorizonSequenceRequest",
        "celestial_anchor_time",
        "frame simulation time",
        "catalogue reference epoch",
        "Do not add caching before",
    ):
        assert value in contract

    assert "49H.1 fixed celestial-anchor" in roadmap
    assert "scientifically keyed reuse remain" in roadmap
    assert "FixedSkyRotatingHorizonSequenceRequest" in implementation
    assert "charts/fixed_sky_sequence.py" in source_tree


def test_fixed_sky_baseline_documents_complete_rendering_limits():
    contract = (
        DEVELOPER / "fixed_sky_complete_render_baseline_49h2.md"
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
        "generate_observer_time_chart_sequence()",
        "separate output directory",
        "PngFrameComparisonTolerance",
        "equality is the default",
        "target_pixel_oracle = false",
        "tools/render_49h2_complete_render_baseline.py",
        "fixed-sky-baseline-audit.json",
        "constellation content and the equatorial grid rotate with it",
        "fixed-sky oracle must independently express",
    ):
        assert value in contract

    assert "49H.2 complete-render circumpolar baseline" in roadmap
    assert "generate_fixed_sky_complete_render_baseline()" in implementation
    assert "charts/fixed_sky_baseline.py" in source_tree



def test_fixed_sky_reference_documents_accepted_target_behavior():
    contract = (
        DEVELOPER / "fixed_sky_reference_rendering_49h3.md"
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
        "stars remain fixed in the viewport",
        "semantic horizon rotates",
        "fixed_sky_circumpolar_orientation()",
        "identical projected coordinates",
        "generate_fixed_sky_rotating_horizon_sequence()",
        "generate_chart_request()",
        "tools/render_49h3_fixed_sky_reference.py",
        "proper-motion realization remain independent",
        "49H.4 may introduce scientifically keyed reuse",
        "1774 passed in 83.10s",
    ):
        assert value in contract

    assert "49H.3 renderer-neutral anchor transformation" in roadmap
    assert "Scientifically keyed reuse remains pending" in roadmap
    assert "generate_fixed_sky_rotating_horizon_sequence()" in implementation
    assert "charts/fixed_sky_orientation.py" in source_tree
