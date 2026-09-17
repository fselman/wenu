"""Local artificial-satellite state and resource domain."""

from .crossing_oracle import (
    LocalSatelliteCrossingOracle,
    LocalSatelliteCrossingQuery,
    SatelliteCrossingConvergenceError,
)
from .crossing_acceleration import (
    AcceleratedCrossingEvidence,
    AcceleratedCrossingPolicy,
    AcceleratedLocalSatelliteCrossingOracle,
    ConeShellDecision,
    ConeShellPolicy,
    ConeShellSelection,
    ConservativeConeShellSelector,
)
from .crossing_batch import (
    FieldAirmassAdmission,
    FieldAirmassCertifier,
    MultiFieldCrossingPolicy,
    MultiFieldCrossingRequest,
    MultiFieldCrossingResult,
    MultiFieldCrossingValidationError,
    MultiFieldSatelliteCrossingCoordinator,
    MultiFieldValidationFailure,
)
from .elements import SatelliteElementRecord
from .sgp4 import (
    SatellitePropagationError,
    SatelliteTemeState,
    Sgp4TemePropagator,
    split_julian_date,
)
from .snapshots import (
    DEFAULT_SNAPSHOT_ID,
    SatelliteElementSnapshot,
    SatelliteSnapshotManifest,
    load_snapshot,
    load_snapshot_directory,
)
from .topocentric import (
    SatelliteFieldCenterAltitudeEvaluator,
    SatelliteEarthOrientationError,
    SatelliteEarthOrientationEvidence,
    SatelliteTopocentricState,
    SatelliteTopocentricTransformer,
)

__all__ = [
    "AcceleratedCrossingEvidence",
    "AcceleratedCrossingPolicy",
    "AcceleratedLocalSatelliteCrossingOracle",
    "ConeShellDecision",
    "ConeShellPolicy",
    "ConeShellSelection",
    "ConservativeConeShellSelector",
    "FieldAirmassAdmission",
    "FieldAirmassCertifier",
    "DEFAULT_SNAPSHOT_ID",
    "LocalSatelliteCrossingOracle",
    "LocalSatelliteCrossingQuery",
    "MultiFieldCrossingPolicy",
    "MultiFieldCrossingRequest",
    "MultiFieldCrossingResult",
    "MultiFieldCrossingValidationError",
    "MultiFieldSatelliteCrossingCoordinator",
    "MultiFieldValidationFailure",
    "SatelliteCrossingConvergenceError",
    "SatelliteEarthOrientationError",
    "SatelliteEarthOrientationEvidence",
    "SatelliteFieldCenterAltitudeEvaluator",
    "SatelliteElementRecord",
    "SatelliteElementSnapshot",
    "SatelliteSnapshotManifest",
    "SatellitePropagationError",
    "SatelliteTemeState",
    "SatelliteTopocentricState",
    "SatelliteTopocentricTransformer",
    "Sgp4TemePropagator",
    "split_julian_date",
    "load_snapshot",
    "load_snapshot_directory",
]
