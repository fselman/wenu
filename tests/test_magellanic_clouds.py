"""Current magellanic clouds contracts."""

# Contracts consolidated from test_milestone34b_magellanic_clouds.py.
import json

import numpy as np
import pytest
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time

from wenu.charts.styles import PublicationStyle
from wenu.rendering import layers
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.magellanic_clouds import MagellanicCloudIsophotes
from wenu.sky.semantic_identity import semantic_layer_identity


class Observer:
    altaz_frame = AltAz(
        obstime=Time("2026-08-15 21:00"),
        location=EarthLocation.from_geodetic(-71.23, -32.45),
    )


def _catalogue(path, cloud):
    features = []
    for level, fraction in enumerate((0.08, 0.16, 0.32, 0.55), start=1):
        offset = float(level)
        ring = [
            [75.0 + offset, -72.0],
            [76.0 + offset, -72.0],
            [76.0 + offset, -71.0],
            [75.0 + offset, -71.0],
            [75.0 + offset, -72.0],
        ]
        features.append(
            {
                "type": "Feature",
                "id": f"{cloud}-level-{level}",
                "properties": {
                    "cloud": cloud.upper(),
                    "level": level,
                    "fraction_of_peak": fraction,
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [[ring]],
                },
            }
        )
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "properties": {"cloud": cloud.upper()},
                "features": features,
            }
        )
    )
    return path


def test_cloud_and_level_selection_are_explicit(tmp_path):
    layer = MagellanicCloudIsophotes(
        Observer(),
        cloud="LMC",
        levels=(4, 2),
    )
    layer.load(_catalogue(tmp_path / "lmc.json", "lmc"))
    geometry = layer.spherical_geometry(Observer())

    assert layer.cloud == "lmc"
    assert layer.levels == (2, 4)
    assert geometry.metadata["cloud"].tolist() == ["lmc", "lmc"]
    assert geometry.metadata["level"].tolist() == [2, 4]
    assert geometry.metadata["fraction_of_peak"] == pytest.approx(
        [0.16, 0.55]
    )
    assert geometry.metadata["semantic_entity_keys"].tolist() == [
        "isophote_2", "isophote_4"
    ]
    assert geometry.metadata[
        "semantic_entity_display_names"
    ].tolist() == ["Isophote 2", "Isophote 4"]
    assert all(np.all(np.isfinite(values)) for values in geometry.lon_deg)


def test_clouds_own_distinct_semantic_hierarchy_branches():
    lmc = semantic_layer_identity(
        MagellanicCloudIsophotes(Observer(), cloud="lmc")
    )
    smc = semantic_layer_identity(
        MagellanicCloudIsophotes(Observer(), cloud="smc")
    )

    assert lmc.semantic_path == (
        "sky",
        "milky_way_and_magellanic_clouds",
        "lmc",
    )
    assert lmc.display_name == "Large Magellanic Cloud"
    assert lmc.svg_id == "lmc-isophotes"
    assert smc.semantic_path == (
        "sky",
        "milky_way_and_magellanic_clouds",
        "smc",
    )
    assert smc.display_name == "Small Magellanic Cloud"
    assert smc.svg_id == "smc-isophotes"


def test_level_selection_can_change_per_render_without_mutation(tmp_path):
    layer = MagellanicCloudIsophotes(
        Observer(), cloud="lmc"
    ).load(_catalogue(tmp_path / "lmc.json", "lmc"))

    selected = layer.spherical_geometry(Observer(), levels={4, 2})
    complete = layer.spherical_geometry(Observer())

    assert selected.metadata["level"].tolist() == [2, 4]
    assert complete.metadata["level"].tolist() == [1, 2, 3, 4]
    assert layer.levels == layer.default_levels


def test_invalid_clouds_levels_and_mismatched_files_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unknown Magellanic Cloud"):
        MagellanicCloudIsophotes(Observer(), cloud="both")
    with pytest.raises(ValueError, match="Unknown.*level"):
        MagellanicCloudIsophotes(Observer(), cloud="lmc", levels=(5,))

    layer = MagellanicCloudIsophotes(Observer(), cloud="lmc")
    with pytest.raises(ValueError, match="Expected LMC"):
        layer.load(_catalogue(tmp_path / "smc.json", "smc"))


def test_celestial_sphere_registers_clouds_independently(tmp_path):
    sky = CelestialSphere(Observer())
    lmc = sky.add_magellanic_cloud_isophotes(
        "lmc",
        filename=_catalogue(tmp_path / "lmc.json", "lmc"),
    )
    smc = sky.add_magellanic_cloud_isophotes(
        "smc",
        filename=_catalogue(tmp_path / "smc.json", "smc"),
        levels=(2, 3, 4),
    )

    assert sky.magellanic_cloud_isophotes == {
        "lmc": lmc,
        "smc": smc,
    }
    assert lmc in sky.layers
    assert smc in sky.layers
    with pytest.raises(ValueError, match="already registered"):
        sky.add_magellanic_cloud_isophotes(
            "lmc",
            filename=tmp_path / "lmc.json",
        )


def test_publication_style_configures_clouds_independently(tmp_path):
    sky = CelestialSphere(Observer())
    lmc = sky.add_magellanic_cloud_isophotes(
        "lmc",
        filename=_catalogue(tmp_path / "lmc.json", "lmc"),
    )
    smc = sky.add_magellanic_cloud_isophotes(
        "smc",
        filename=_catalogue(tmp_path / "smc.json", "smc"),
    )
    style = PublicationStyle(
        lmc_color="cyan",
        lmc_alpha=0.18,
        smc_color="cornflowerblue",
        smc_alpha=0.12,
    )
    options = style.layer_options(sky)

    lmc_fill = options[lmc]["render"]["polygon_fill_style"]
    smc_fill = options[smc]["render"]["polygon_fill_style"]
    assert lmc_fill["facecolor"] == "cyan"
    assert lmc_fill["face_alpha"] == pytest.approx(0.18)
    assert smc_fill["facecolor"] == "cornflowerblue"
    assert smc_fill["face_alpha"] == pytest.approx(0.12)
    assert lmc_fill["zorder"] == layers.MAGELLANIC_CLOUDS
    assert smc_fill["zorder"] == layers.MAGELLANIC_CLOUDS
    assert callable(options[lmc]["prepare"])
    assert callable(options[smc]["prepare"])


def test_packaged_snapshots_have_four_levels():
    for cloud in MagellanicCloudIsophotes.available_clouds:
        layer = MagellanicCloudIsophotes(
            Observer(),
            cloud=cloud,
        ).load()
        assert tuple(layer.features) == layer.available_levels


def test_default_cloud_opacities_match_milky_way_scale():
    style = PublicationStyle()
    assert style.milky_way_alpha == pytest.approx(0.10)
    assert style.lmc_alpha == pytest.approx(0.08)
    assert style.smc_alpha == pytest.approx(0.06)
    assert style.smc_alpha < style.lmc_alpha <= style.milky_way_alpha


def test_level_selections_share_one_maximal_observed_geometry(
    tmp_path, monkeypatch
):
    layer = MagellanicCloudIsophotes(
        Observer(), cloud="lmc"
    ).load(_catalogue(tmp_path / "lmc.json", "lmc"))
    observer = Observer()
    original = layer._transform_rings
    calls = []

    def transform(rings, resolved):
        calls.append(len(rings))
        return original(rings, resolved)

    monkeypatch.setattr(layer, "_transform_rings", transform)
    selected = layer.spherical_geometry(observer, levels={2})
    complete = layer.spherical_geometry(
        observer, levels=layer.available_levels
    )

    assert selected.metadata["level"].tolist() == [2]
    assert complete.metadata["level"].tolist() == [1, 2, 3, 4]
    assert calls == [len(complete)]
    assert len(layer._observed_polygon_cache) == 1
