"""Body-driven moving-object infrastructure independent of Venus."""

from wenu.sky.frozen_earth_disk_sequences import FrozenEarthDiskSequenceRequest
from wenu.sky.frozen_earth_venus_disk_sequence import (
    frozen_earth_solar_system_disk_sequence_layers,
)
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.solar_system_bodies import (
    FROZEN_EARTH_DISK_SEQUENCE,
    OBSERVED_DISK_SEQUENCE,
    RESOLVED_SPHERICAL_DISK,
    SYMBOLIC_POINT,
    SolarSystemBodyCatalog,
    SolarSystemBodyDescriptor,
)
from wenu.sky.solar_system_disk_sequences import (
    ObservedSolarSystemDiskSequenceRequest,
)
from wenu.sky.solar_system_points import SolarSystemPointLayer
from wenu.sky.venus_disk import solar_system_disk_layers
from wenu.sky.venus_disk_sequence import (
    observed_solar_system_disk_sequence_layers,
)
from wenu.charts.request_disks import (
    FrozenEarthSolarSystemDiskSequenceDisplayRequest,
    SolarSystemDiskDisplayRequest,
    configure_chart_request_disks,
)


TEST_BODY = SolarSystemBodyDescriptor(
    target="test body",
    entity_key="test_body",
    display_name="Test Body",
    selection_key="test-body",
    body_class="minor_body",
    physical_body_id="2000001",
    parent_body_key="sun",
    classifications=frozenset({"minor_planet", "dwarf_planet"}),
    physical_radius_km=470.0,
    radius_model="deterministic test mean radius",
    capabilities=frozenset({
        SYMBOLIC_POINT,
        RESOLVED_SPHERICAL_DISK,
        OBSERVED_DISK_SEQUENCE,
        FROZEN_EARTH_DISK_SEQUENCE,
    }),
    localized_display_names=(("en", "Test Body"), ("es", "Cuerpo de prueba")),
)


def observed_request():
    return ObservedSolarSystemDiskSequenceRequest(
        descriptor=TEST_BODY,
        start_instant="2026-08-30T00:00:00Z",
        start_time_scale="utc",
        step_days=2.0,
        n_steps=2,
        display_name=TEST_BODY.display_name,
        physical_radius_km=TEST_BODY.physical_radius_km,
        radius_model=TEST_BODY.radius_model,
    )


def frozen_request():
    return FrozenEarthDiskSequenceRequest(
        descriptor=TEST_BODY,
        start_instant="2026-08-30T00:00:00Z",
        start_time_scale="utc",
        step_days=2.0,
        n_steps=2,
        display_name=TEST_BODY.display_name,
        physical_radius_km=TEST_BODY.physical_radius_km,
        radius_model=TEST_BODY.radius_model,
    )


def test_catalog_records_classification_and_relationship_without_containment():
    sun = SolarSystemBodyDescriptor(
        target="sun",
        entity_key="sun",
        display_name="Sun",
        selection_key="sun",
        body_class="star",
    )
    catalog = SolarSystemBodyCatalog((sun, TEST_BODY))
    assert catalog.resolve("test-body") is TEST_BODY
    assert catalog.children_of("sun") == (TEST_BODY,)
    assert TEST_BODY.classifications == {"minor_planet", "dwarf_planet"}
    assert TEST_BODY.display_name_for("es") == "Cuerpo de prueba"
    assert TEST_BODY.display_name_for("fr") == "Test Body"


def test_symbolic_point_and_semantics_are_descriptor_driven():
    layer = SolarSystemPointLayer(TEST_BODY)
    assert layer.layer_name == "test_body"
    assert semantic_layer_identity(layer).semantic_path_text == (
        "sky/solar_system/minor_bodies/test_body"
    )


def test_resolved_disk_factory_requires_no_body_specific_class():
    layers = solar_system_disk_layers(TEST_BODY, magnification=4.0)
    assert tuple(layer.layer_name for layer in layers) == (
        "test_body_disk_illuminated",
        "test_body_disk_limb",
        "test_body_disk_terminator",
    )
    assert tuple(
        semantic_layer_identity(layer).semantic_path_text for layer in layers
    ) == (
        "sky/solar_system/minor_bodies/test_body/disk/illuminated",
        "sky/solar_system/minor_bodies/test_body/disk/limb",
        "sky/solar_system/minor_bodies/test_body/disk/terminator",
    )


def test_observed_and_frozen_factories_derive_all_layer_names_from_metadata():
    observed = observed_solar_system_disk_sequence_layers(
        observed_request(), label_dates=True
    )
    frozen = frozen_earth_solar_system_disk_sequence_layers(
        frozen_request(), label_dates=True
    )
    assert tuple(layer.layer_name for layer in observed) == (
        "test_body_disk_sequence_illuminated",
        "test_body_disk_sequence_limb",
        "test_body_disk_sequence_terminator",
        "test_body_disk_sequence_labels",
    )
    assert tuple(layer.layer_name for layer in frozen) == (
        "test_body_disk_sequence_frozen_illuminated",
        "test_body_disk_sequence_frozen_limb",
        "test_body_disk_sequence_frozen_terminator",
        "test_body_disk_sequence_frozen_labels",
        "frozen_earth_sun",
    )


def test_chart_installs_nonvenus_components_without_body_specific_control_flow():
    class Sky:
        def __init__(self):
            self._layers = []

        @property
        def layers(self):
            return tuple(self._layers)

        def add(self, layer):
            self._layers.append(layer)

        def remove(self, layer):
            self._layers.remove(layer)

    sky = Sky()
    request = type("Request", (), {
        "solar_system_disks": (SolarSystemDiskDisplayRequest(TEST_BODY),),
        "solar_system_disk_sequence": None,
    })()
    configure_chart_request_disks(sky, request)
    assert tuple(layer.layer_name for layer in sky.layers) == (
        "test_body_disk_illuminated",
        "test_body_disk_limb",
        "test_body_disk_terminator",
    )

    request = type("Request", (), {
        "solar_system_disks": (),
        "solar_system_disk_sequence": (
            FrozenEarthSolarSystemDiskSequenceDisplayRequest(
                frozen_request()
            )
        ),
    })()
    configure_chart_request_disks(sky, request)
    assert tuple(layer.layer_name for layer in sky.layers) == (
        "test_body_disk_sequence_frozen_illuminated",
        "test_body_disk_sequence_frozen_limb",
        "test_body_disk_sequence_frozen_terminator",
        "frozen_earth_sun",
    )
