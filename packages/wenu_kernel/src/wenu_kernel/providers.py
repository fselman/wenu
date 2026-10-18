"""Provider protocol; concrete provider packages are never imported here."""

from typing import Protocol

from .reuse import ReuseCertificate

from .records import (
    CapabilityDecision, CatalogueRef, CatalogueSnapshot, ProviderDescriptor,
    StateBatch, StateQuery, DirectionReusePlan,
)


class StateProvider(Protocol):
    def describe(self) -> ProviderDescriptor: ...
    def catalogue(self, reference: CatalogueRef) -> CatalogueSnapshot: ...
    def supports(self, query: StateQuery) -> CapabilityDecision: ...
    def evaluate(self, query: StateQuery) -> StateBatch: ...
    def certify(self, query: StateQuery, anchor: StateBatch) -> ReuseCertificate: ...
    def close(self) -> None: ...


class CanonicalDirectionProvider(StateProvider, Protocol):
    """Optional capability: pure deterministic model/query-based anchor planning.

    Planning must not read cache history, propagate states, acquire resources
    or mutate provider/session state. Conformance checks test this obligation.
    """

    def plan_reuse(self, query: StateQuery) -> DirectionReusePlan: ...
