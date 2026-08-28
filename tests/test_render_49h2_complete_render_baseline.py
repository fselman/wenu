"""Reproducible 49H.2 complete-render baseline audit-tool tests."""

from argparse import Namespace
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from tools import render_49h2_complete_render_baseline as tool


def arguments(tmp_path, **overrides):
    values = {
        "output": tmp_path / "audit",
        "start": "2026-08-21T21:00:00-04:00",
        "stop": "2026-08-22T03:00:00-04:00",
        "frames": 3,
        "display_timezone": "America/Santiago",
        "location": "La Ligua",
        "pole": "south",
        "limiting_declination": -60.0,
        "restart_policy": "restart",
    }
    values.update(overrides)
    return Namespace(**values)



def test_real_audit_default_field_intersects_la_ligua_horizon():
    options = tool.parser().parse_args([])

    assert options.limiting_declination == -50.0


def test_audit_request_selects_time_sensitive_circumpolar_content(tmp_path):
    request = tool.baseline_request(arguments(tmp_path))

    assert request.chart.family == "circumpolar"
    assert request.chart.horizon
    assert request.chart.product.output == (
        tmp_path / "audit" / "candidate-reserved"
    )
    assert request.chart.detail.enabled_layers == frozenset({
        "stars",
        "constellation_lines",
        "constellation_labels",
        "equatorial_grid",
        "altaz_grid",
        "horizon",
    })
    assert request.chart.detail.grid_label_layers == frozenset({
        "equatorial_grid",
        "altaz_grid",
    })
    assert request.frame_count == 3
    assert request.celestial_anchor_time.isoformat() == (
        "2026-08-22T01:00:00+00:00"
    )


def test_audit_records_manifest_times_dimensions_and_hashes(
    tmp_path,
    monkeypatch,
):
    options = arguments(tmp_path)
    baseline = options.output / "complete-render-baseline"
    baseline.mkdir(parents=True)
    outputs = []
    for index, color in enumerate(((10, 20, 30), (30, 20, 10))):
        path = baseline / f"frame-{index:04d}.png"
        Image.new("RGB", (4, 3), color).save(path)
        outputs.append(path)
    manifest = baseline / "wenu-sequence-manifest.json"
    manifest.write_text(
        json.dumps({"identity_sha256": "abc123"}),
        encoding="utf-8",
    )

    def generate(request, output, *, restart_policy):
        assert output == baseline
        assert restart_policy == "restart"
        return SimpleNamespace(
            outputs=tuple(outputs),
            manifest_path=manifest,
            rendered_count=2,
            reused_count=0,
        )

    monkeypatch.setattr(
        tool,
        "generate_fixed_sky_complete_render_baseline",
        generate,
    )
    options.frames = 2

    destination = tool.audit(options)
    report = json.loads(destination.read_text(encoding="utf-8"))

    assert report["audit_kind"] == "fixed_sky_complete_render_baseline"
    assert report["role"] == "unregistered_complete_render_baseline"
    assert report["target_pixel_oracle"] is False
    assert report["manifest_identity_sha256"] == "abc123"
    assert report["frame_count"] == 2
    assert report["rendered_count"] == 2
    assert report["reused_count"] == 0
    assert report["uniform_dimensions"]
    assert report["distinct_frame_hashes"] == 2
    assert [frame["dimensions"] for frame in report["frames"]] == [
        [4, 3],
        [4, 3],
    ]
    assert len(report["simulation_times"]) == 2
    assert len(report["display_times"]) == 2


def test_audit_rejects_a_baseline_that_does_not_change(
    tmp_path,
    monkeypatch,
):
    options = arguments(tmp_path, frames=2)
    baseline = options.output / "complete-render-baseline"
    baseline.mkdir(parents=True)
    outputs = []
    for index in range(2):
        path = baseline / f"frame-{index:04d}.png"
        Image.new("RGB", (4, 3), (10, 20, 30)).save(path)
        outputs.append(path)
    manifest = baseline / "wenu-sequence-manifest.json"
    manifest.write_text(
        json.dumps({"identity_sha256": "abc123"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        tool,
        "generate_fixed_sky_complete_render_baseline",
        lambda *args, **kwargs: SimpleNamespace(
            outputs=tuple(outputs),
            manifest_path=manifest,
            rendered_count=2,
            reused_count=0,
        ),
    )

    try:
        tool.audit(options)
    except RuntimeError as error:
        assert "do not change" in str(error)
    else:
        raise AssertionError("Identical baseline frames must be rejected.")
