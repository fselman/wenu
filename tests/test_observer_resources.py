"""Milestone 45G.1 observer ephemeris resource contracts."""

from wenu import Observer


def test_observer_close_is_idempotent():
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )

    assert observer._ephemeris_finalizer.alive
    observer.close()
    assert not observer._ephemeris_finalizer.alive
    observer.close()


def test_observer_context_manager_closes_ephemeris():
    with Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    ) as observer:
        finalizer = observer._ephemeris_finalizer
        assert finalizer.alive

    assert not finalizer.alive


def _resolve_site(name, **overrides):
    arguments = dict(
        location=name, lat_deg=None, lon_deg=None,
        elevation_m=None, timezone_name=None,
    )
    arguments.update(overrides)
    return Observer._resolve_location(**arguments)


def test_packaged_locations_cover_municipalities_and_preserve_legacy_sites():
    import math
    from zoneinfo import ZoneInfo
    from wenu.observer import _registered_locations

    records = _registered_locations()
    seats = [site for site in records if site["kind"] == "municipal_seat"]
    assert len(seats) == 345
    assert len({site["commune_code"] for site in seats}) == 345
    assert len({site["region_code"] for site in seats}) == 16
    assert any(site["kind"] == "observatory" for site in records)
    for site in records:
        assert site["country"] == "Chile"
        assert site["country_code"] == "CL"
        assert -90 <= site["lat_deg"] <= 90
        assert -180 <= site["lon_deg"] <= 180
        assert math.isfinite(site["lat_deg"])
        assert math.isfinite(site["lon_deg"])
        ZoneInfo(site["timezone"])
        resolved = _resolve_site(site["qualified_name"])
        assert resolved[:2] == (site["lat_deg"], site["lon_deg"])
        assert _resolve_site(site["id"]) == resolved
        if site["runtime_height_reference"] != "legacy_wenu_unspecified":
            assert abs(
                site["elevation_m"] - site["height_m"]
                - site["geoid_undulation_m"]
            ) < 0.0011
    assert _resolve_site("La Ligua") == (
        -32.443342, -71.230289, 52.0, "America/Santiago", "La Ligua"
    )
    assert _resolve_site("Papudo") == (
        -32.5078, -71.4411, 15.0, "America/Santiago", "Papudo"
    )


def test_location_suffixes_accents_and_regional_timezone_defaults():
    assert _resolve_site("Chile:Valparaíso:Petorca:La Ligua:La Ligua") == (
        _resolve_site("La Ligua")
    )
    assert _resolve_site("Valparaíso:Petorca:La Ligua:La Ligua") == (
        _resolve_site("la ligua")
    )
    assert _resolve_site("Petorca:La Ligua:La Ligua") == _resolve_site(
        "La Ligua:La Ligua"
    )
    assert _resolve_site("  NUBLE:DIGUILLIN:CHILLAN:CHILLAN  ")[4] == "Chillán"
    assert _resolve_site("Coyhaique")[3] == "America/Coyhaique"
    assert _resolve_site("Punta Arenas")[3] == "America/Punta_Arenas"
    assert _resolve_site("Hanga Roa")[3] == "Pacific/Easter"
    assert _resolve_site("Cabo de Hornos")[4] == "Puerto Williams"
    assert _resolve_site("Camarones")[4] == "Cuya"
    assert _resolve_site("Paranal")[4] == "Observatorio Paranal"
    assert _resolve_site("La Ligua", elevation_m=75, timezone_name="UTC") == (
        -32.443342, -71.230289, 75.0, "UTC", "La Ligua"
    )


def test_location_ambiguity_is_not_silently_resolved(monkeypatch):
    import pytest
    import wenu.observer as module

    records = (
        dict(id="one", name="San Pedro", country="Chile", region="R1", province="P1",
             commune="C1", qualified_name="Chile:R1:P1:C1:San Pedro",
             aliases=(), region_aliases=()),
        dict(id="two", name="San Pedro", country="Chile", region="R2", province="P2",
             commune="C2", qualified_name="Chile:R2:P2:C2:San Pedro",
             aliases=(), region_aliases=()),
    )
    monkeypatch.setattr(module, "_registered_locations", lambda: records)
    with pytest.raises(ValueError, match="Ambiguous location") as error:
        module._resolve_registered_location("San Pedro")
    assert "R1:P1:C1:San Pedro" in str(error.value)
    assert "R2:P2:C2:San Pedro" in str(error.value)
    assert module._resolve_registered_location("C2:San Pedro")["id"] == "two"
    with pytest.raises(ValueError, match="Unknown location"):
        module._resolve_registered_location("R2:P1:C1:San Pedro")
    with pytest.raises(ValueError, match="Unknown location"):
        module._resolve_registered_location("Argentina:R1:P1:C1:San Pedro")
    with pytest.raises(ValueError, match="Location must"):
        module._resolve_registered_location("R1::C1:San Pedro")
    foreign = dict(records[0], id="foreign", country="Argentina",
                   qualified_name="Argentina:R1:P1:C1:San Pedro")
    monkeypatch.setattr(module, "_registered_locations", lambda: (*records, foreign))
    assert module._resolve_registered_location(
        "Chile:R1:P1:C1:San Pedro"
    )["id"] == "one"
    assert module._resolve_registered_location(
        "Argentina:R1:P1:C1:San Pedro"
    )["id"] == "foreign"
    with pytest.raises(ValueError, match="Ambiguous location"):
        module._resolve_registered_location("R1:P1:C1:San Pedro")


def test_location_snapshot_is_immutable_and_missing_height_requires_override(
    monkeypatch,
):
    import pytest
    import wenu.observer as module

    site = module._resolve_registered_location("La Ligua")
    with pytest.raises(TypeError):
        site["lat_deg"] = 0
    missing = dict(site, elevation_m=None)
    monkeypatch.setattr(module, "_resolve_registered_location", lambda _: missing)
    with pytest.raises(ValueError, match="No usable height"):
        _resolve_site("La Ligua")
    assert _resolve_site("La Ligua", elevation_m=123)[2] == 123


def test_location_snapshot_rejects_changed_packaged_bytes(monkeypatch, tmp_path):
    import json
    import pytest
    import wenu.observer as module

    (tmp_path / "chile_locations_v1.json").write_text("{}")
    (tmp_path / "chile_locations_manifest_v1.json").write_text(
        json.dumps({"catalogue_sha256": "0" * 64})
    )
    monkeypatch.setattr(module, "files", lambda _: tmp_path)
    with pytest.raises(ValueError, match="digest mismatch"):
        module._registered_locations.__wrapped__()
