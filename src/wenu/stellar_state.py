"""Kernel adapter for explicit, unpropagated native catalogue directions.

A time-independent lookup is not a zero-proper-motion model. This adapter's
native-catalogue reference never advertises epoch_direction, physical accuracy,
temporal reuse, distance or velocity. Coverage describes lookup availability,
not validity of a requested-epoch astrometric prediction.
"""
from __future__ import annotations

from wenu_kernel.errors import InvalidQuery, UnsupportedCapability
from wenu_kernel.records import ReferenceSpec, TimePoint, UnboundedCoverage
from wenu.catalogue_state import (
    CatalogueDirectionProvider, catalogue_direction_angles as native_stellar_angles,
    catalogue_direction_states,
)

NATIVE_STELLAR_REFERENCE = ReferenceSpec(
    "icrs", "solar-system-barycenter", "native-catalogue", "direction", "rad",
    "unpropagated source directions; no requested-epoch astrometry",
)


class LegacyNativeStellarProvider(CatalogueDirectionProvider):
    """Compatibility facade for the admitted source-epoch stellar lookup."""

    def __init__(self, rows, *, namespace, source_epoch, provenance,
                 catalogue_edition="materialized-input/1", reference=NATIVE_STELLAR_REFERENCE):
        if type(source_epoch) is not TimePoint:
            raise InvalidQuery("an explicit source epoch is required")
        if reference != NATIVE_STELLAR_REFERENCE:
            raise UnsupportedCapability("Only admitted native ICRS reference semantics are supported.")
        super().__init__(rows, namespace=namespace, source_epoch=source_epoch,
            provenance=provenance, catalogue_edition=catalogue_edition,
            reference=reference, capability="native_direction", semantic_type="star",
            provider_id="wenu.legacy-native-stars:" + namespace,
            resource_id="derived-native-stellar-table:" + namespace,
            model_id="unpropagated-native-stars", coverage=UnboundedCoverage(source_epoch.scale))


def native_stellar_states(rows, *, namespace, source_epoch, provenance, catalogue_edition="materialized-input/1",
                          reference=NATIVE_STELLAR_REFERENCE):
    """Query the real kernel at the source epoch; close all owned scope state.

    Empty tables require no query. No global registry/session survives this
    call; published immutable rows remain valid after cleanup.
    """
    provider = LegacyNativeStellarProvider(rows, namespace=namespace,
                                         source_epoch=source_epoch, provenance=provenance,
                                         catalogue_edition=catalogue_edition, reference=reference)
    return catalogue_direction_states(provider, source_epoch)
