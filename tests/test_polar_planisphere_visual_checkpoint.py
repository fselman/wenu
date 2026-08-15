from pathlib import Path


ROOT = Path(__file__).parents[1]
RUNNER = ROOT / "tools/render_48e2_polar_preview.py"


def test_visual_checkpoint_uses_canonical_sky_composition_and_rendering():
    source = RUNNER.read_text(encoding="utf-8")

    assert "generate_celestial_sphere()" in source
    assert 'compose_chart(chart, style="atlas", mode="print")' in source
    assert "chart.render(" in source
    assert "PolarCalendarFurnitureRequest().resolve(pair)" in source
    assert ").save(figure, destination)" in source
    assert "polar-planisphere-south.png" not in source
    assert 'f"polar-planisphere-{name}.png"' in source


def test_visual_checkpoint_has_both_projection_choices_and_fixed_observer():
    source = RUNNER.read_text(encoding="utf-8")

    assert 'location="La Ligua"' in source
    assert 'time="2026-08-15 21:00"' in source
    assert '"polar_azimuthal_equidistant", "stereographic"' in source
    assert source.count("ExportOptions(") == 1
