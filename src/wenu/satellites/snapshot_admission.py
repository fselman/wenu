"""Explicit digest-bound admission for external satellite snapshots."""

from __future__ import annotations

from dataclasses import dataclass

from .snapshots import SatelliteElementSnapshot


SNAPSHOT_ADMISSION_IMPLEMENTATION = (
    "wenu external satellite snapshot admission/1"
)
CELESTRAK_ACTIVE_20260917_POLICY_IDENTITY = (
    "wenu.celestrak-active-20260917-admission/1"
)


def _text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must be non-empty.")
    return value


def _digest(value, *, name):
    value = _text(value, name=name).lower()
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(
            f"{name} must contain exactly 64 hexadecimal characters."
        )
    return value


@dataclass(frozen=True)
class ExternalSnapshotIdentity:
    """Exact canonical content plus validated manifest identity."""

    schema_version: int
    snapshot_id: str
    content_sha256: str
    source_identity: str
    source_url: str
    builder_identity: str

    def __post_init__(self):
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1.")
        for name in (
            "snapshot_id",
            "source_identity",
            "source_url",
            "builder_identity",
        ):
            object.__setattr__(
                self, name, _text(getattr(self, name), name=name)
            )
        object.__setattr__(
            self,
            "content_sha256",
            _digest(self.content_sha256, name="content_sha256"),
        )

    @classmethod
    def from_snapshot(cls, snapshot):
        """Derive identity only from an already validated immutable snapshot."""
        if not isinstance(snapshot, SatelliteElementSnapshot):
            raise TypeError("snapshot must be a SatelliteElementSnapshot.")
        manifest = snapshot.manifest
        return cls(
            schema_version=manifest.schema_version,
            snapshot_id=manifest.snapshot_id,
            content_sha256=manifest.content_sha256,
            source_identity=manifest.source_identity,
            source_url=manifest.source_url,
            builder_identity=manifest.builder_identity,
        )


CELESTRAK_ACTIVE_20260917_IDENTITY = ExternalSnapshotIdentity(
    schema_version=1,
    snapshot_id="celestrak_active_e80306c843b9e300",
    content_sha256=(
        "e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347"
    ),
    source_identity="CelesTrak GP GROUP=active",
    source_url=(
        "https://celestrak.org/NORAD/elements/"
        "gp.php?GROUP=active&FORMAT=CSV"
    ),
    builder_identity="wenu.satellites.snapshot_acquisition/1",
)


_ADMISSION_FACTORY = object()


@dataclass(frozen=True, init=False)
class ExternalSnapshotAdmission:
    """Opaque evidence that one exact external snapshot was admitted."""

    identity: ExternalSnapshotIdentity
    policy_identity: str
    implementation: str

    def __init__(
        self,
        identity,
        policy_identity,
        implementation=SNAPSHOT_ADMISSION_IMPLEMENTATION,
        *,
        _factory=None,
    ):
        if _factory is not _ADMISSION_FACTORY:
            raise TypeError(
                "ExternalSnapshotAdmission must be produced by an "
                "ExternalSnapshotAdmissionPolicy."
            )
        if not isinstance(identity, ExternalSnapshotIdentity):
            raise TypeError(
                "identity must be an ExternalSnapshotIdentity."
            )
        object.__setattr__(self, "identity", identity)
        object.__setattr__(
            self,
            "policy_identity",
            _text(policy_identity, name="policy_identity"),
        )
        object.__setattr__(
            self,
            "implementation",
            _text(implementation, name="implementation"),
        )

    def require(self, snapshot):
        """Fail unless this token identifies the exact query snapshot."""
        actual = ExternalSnapshotIdentity.from_snapshot(snapshot)
        if actual != self.identity:
            raise ValueError(
                "external snapshot admission does not match the query "
                "snapshot identity."
            )
        return snapshot


@dataclass(frozen=True)
class ExternalSnapshotAdmissionPolicy:
    """Explicit finite allowlist for evidence-only external admission."""

    policy_identity: str
    admitted_identities: tuple[ExternalSnapshotIdentity, ...]

    def __post_init__(self):
        object.__setattr__(
            self,
            "policy_identity",
            _text(self.policy_identity, name="policy_identity"),
        )
        if isinstance(self.admitted_identities, (str, bytes)):
            raise TypeError(
                "admitted_identities must contain ExternalSnapshotIdentity "
                "values."
            )
        try:
            identities = tuple(self.admitted_identities)
        except TypeError as error:
            raise TypeError(
                "admitted_identities must contain ExternalSnapshotIdentity "
                "values."
            ) from error
        if not identities or not all(
            isinstance(item, ExternalSnapshotIdentity) for item in identities
        ):
            raise ValueError(
                "admitted_identities must contain ExternalSnapshotIdentity "
                "values."
            )
        if len(set(identities)) != len(identities):
            raise ValueError("admitted_identities must be unique.")
        object.__setattr__(self, "admitted_identities", identities)

    def admit(self, snapshot):
        """Return a token only after complete exact-identity comparison."""
        actual = ExternalSnapshotIdentity.from_snapshot(snapshot)
        if actual not in self.admitted_identities:
            raise ValueError(
                "snapshot identity is not admitted by the external policy."
            )
        return ExternalSnapshotAdmission(
            actual,
            self.policy_identity,
            _factory=_ADMISSION_FACTORY,
        )
