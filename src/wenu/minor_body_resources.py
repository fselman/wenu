"""Explicit offline resolution and lifecycle for minor-body resources."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from wenu.minor_body_ephemeris import (
    SkyfieldMinorBodyStateSource,
    SpiceMinorBodyKernel,
)
from wenu.sky.ceres import CERES_BODY, CERES_SOLUTION
from wenu.sky.solar_system_points import EphemerisSourceBinding
from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource


_MINOR_BODY_SPECS = {
    CERES_BODY.selection_key: (CERES_BODY, CERES_SOLUTION),
}


def request_minor_body_descriptors(request):
    """Return selected minor-body descriptors in stable catalog order."""
    from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG

    keys = set(request.content.solar_system_objects or ())
    if request.solar_system_track is not None:
        keys.add(request.solar_system_track.descriptor.selection_key)
    return tuple(
        descriptor
        for descriptor in (
            SOLAR_SYSTEM_BODY_CATALOG.resolve(key) for key in sorted(keys)
        )
        if descriptor.ephemeris_source_key == "minor_body_spk"
    )


def bind_sky_source_resolver(sky, resolver):
    """Bind one resolver to registered moving points and return prior values."""
    previous = []
    for layer in getattr(sky, "solar_system_bodies", {}).values():
        previous.append((layer, layer.source_resolver))
        layer.source_resolver = resolver
    moon = getattr(sky, "moon", None)
    if moon is not None and all(layer is not moon for layer, _ in previous):
        previous.append((moon, moon.source_resolver))
        moon.source_resolver = resolver
    return tuple(previous)


def restore_sky_source_resolvers(previous):
    """Restore bindings after a request on a reusable sphere."""
    for layer, resolver in previous:
        layer.source_resolver = resolver


def _digest(path):
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


class MinorBodyResourceSession:
    """Resolve a manifest-backed collection and own each opened SPK once."""

    def __init__(self, resource_directory, observer):
        self.resource_directory = Path(resource_directory).expanduser().resolve(
            strict=True
        )
        if not self.resource_directory.is_dir():
            raise NotADirectoryError(
                f"minor-body resource path is not a directory: "
                f"{self.resource_directory}"
            )
        self.observer = observer
        self.planetary_source = SkyfieldEphemerisStateSource.from_observer(
            observer
        )
        manifest_path = self.resource_directory / "acquisition-report.json"
        try:
            document = json.loads(manifest_path.read_text(encoding="utf-8"))
            records = document["resources"]
        except FileNotFoundError:
            raise FileNotFoundError(
                f"missing minor-body acquisition manifest: {manifest_path}"
            ) from None
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(
                f"invalid minor-body acquisition manifest: {manifest_path}"
            ) from error
        if not isinstance(records, list):
            raise ValueError("minor-body manifest resources must be a list.")
        keyed = {}
        for record in records:
            if not isinstance(record, dict) or not isinstance(
                record.get("key"), str
            ):
                raise ValueError(
                    "minor-body manifest records require a string key."
                )
            key = record["key"].strip().lower()
            if not key or key in keyed:
                raise ValueError(
                    "minor-body manifest keys must be non-empty and unique."
                )
            keyed[key] = record
        self._records = keyed
        self._kernels = {}
        self._sources = {}
        self._closed = False

    def source_binding(self, descriptor, observer):
        """Return a cached descriptor-selected target/observer binding."""
        if self._closed:
            raise ValueError("minor-body resource session is closed.")
        if observer is not self.observer:
            raise ValueError(
                "minor-body resource session belongs to a different observer."
            )
        if descriptor.ephemeris_source_key == "skyfield":
            return EphemerisSourceBinding(
                self.planetary_source, self.planetary_source
            )
        if descriptor.ephemeris_source_key != "minor_body_spk":
            raise ValueError(
                "unknown ephemeris source key: "
                f"{descriptor.ephemeris_source_key!r}."
            )
        key = descriptor.selection_key
        try:
            expected_descriptor, solution = _MINOR_BODY_SPECS[key]
        except KeyError as error:
            raise KeyError(
                f"no installed minor-body provider specification for {key!r}."
            ) from error
        if descriptor != expected_descriptor:
            raise ValueError(
                "minor-body descriptor differs from its provider specification."
            )
        if key not in self._sources:
            self._sources[key] = self._open_source(key, solution)
        return EphemerisSourceBinding(
            self._sources[key], self.planetary_source
        )

    def _open_source(self, key, solution):
        try:
            record = self._records[key]
        except KeyError as error:
            raise FileNotFoundError(
                f"minor-body manifest has no resource for {key!r}."
            ) from error
        required = ("filename", "sha256", "spk_file_id", "horizons_result")
        if any(not isinstance(record.get(name), str) for name in required):
            raise ValueError(
                f"minor-body manifest record {key!r} is incomplete."
            )
        if record["spk_file_id"] != solution.provider_spk_id:
            raise ValueError(
                f"minor-body manifest target differs for {key!r}."
            )
        result = record["horizons_result"]
        for expected in (
            solution.primary_designation,
            solution.orbit_solution_id.replace("#", " "),
            solution.solution_date,
        ):
            if expected not in result:
                raise ValueError(
                    f"minor-body manifest solution identity differs for {key!r}."
                )
        path = (self.resource_directory / record["filename"]).resolve(
            strict=True
        )
        if path.parent != self.resource_directory:
            raise ValueError("minor-body resource must remain in its directory.")
        if _digest(path) != record["sha256"]:
            raise ValueError(
                f"minor-body SPK digest differs from the manifest for {key!r}."
            )
        kernel = SpiceMinorBodyKernel(path)
        try:
            matching = tuple(
                segment for segment in kernel.segments
                if segment.target == int(solution.provider_spk_id)
            )
            if len(matching) != 1:
                raise ValueError(
                    f"minor-body SPK must contain one target segment for {key!r}."
                )
            segment = matching[0]
            if segment.center != 10 or segment.frame_id != 1 or (
                segment.data_type != 21
            ):
                raise ValueError(
                    f"minor-body SPK segment identity differs for {key!r}."
                )
            source = SkyfieldMinorBodyStateSource.from_kernels(
                small_body_kernel=kernel,
                planetary_source=self.planetary_source,
                timescale=self.observer.timescale,
                solution=solution,
                model=f"Horizons {solution.orbit_solution_id}",
            )
        except BaseException:
            kernel.close()
            raise
        self._kernels[key] = kernel
        return source

    def close(self):
        """Close every opened resource exactly once."""
        if self._closed:
            return
        for kernel in reversed(tuple(self._kernels.values())):
            kernel.close()
        self._closed = True

    def __enter__(self):
        if self._closed:
            raise ValueError("minor-body resource session is closed.")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        del exc_type, exc_value, traceback
        self.close()
