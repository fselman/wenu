"""Explicit offline resolution and lifecycle for minor-body resources."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from wenu.minor_body_ephemeris import (
    MinorBodySolutionIdentity,
    SkyfieldMinorBodyStateSource,
    SpiceMinorBodyKernel,
)
from wenu.sky.ceres import CERES_BODY, CERES_SOLUTION
from wenu.sky.solar_system_bodies import (
    APPARENT_TRACK,
    SYMBOLIC_POINT,
    SolarSystemBodyDescriptor,
)
from wenu.sky.solar_system_points import EphemerisSourceBinding
from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource


_MINOR_BODY_SPECS = {
    CERES_BODY.selection_key: (CERES_BODY, CERES_SOLUTION),
}


def _normalized_selection(value):
    value = str(value).strip()
    if not value:
        raise ValueError("minor-body selection must be non-empty.")
    return value.casefold()


def _solution_from_record(record, *, number, name):
    values = record.get("solution")
    if not isinstance(values, dict):
        raise ValueError(
            f"minor-body manifest record {number!r} requires solution metadata."
        )
    pairs = {}
    for field in ("model_parameters", "quality_fields"):
        value = values.get(field, ())
        if isinstance(value, dict):
            value = tuple(sorted(value.items()))
        pairs[field] = tuple(tuple(item) for item in value)
    return MinorBodySolutionIdentity(
        provider=values["provider"],
        service_version=values["service_version"],
        wenu_target=str(number),
        object_class=values["object_class"],
        primary_designation=values["primary_designation"],
        horizons_command=values["horizons_command"],
        provider_spk_id=values["provider_spk_id"],
        orbit_solution_id=values["orbit_solution_id"],
        solution_date=values["solution_date"],
        osculating_epoch=values["osculating_epoch"],
        reference_system=values["reference_system"],
        iau_number=number,
        name=name,
        aliases=tuple(values.get("aliases", ())),
        model_parameters=pairs["model_parameters"],
        quality_fields=pairs["quality_fields"],
        provenance=tuple(values.get("provenance", ())),
    )


class MinorBodyResourceCollection:
    """Validated manifest-derived identities for installed asteroids."""

    def __init__(self, resource_directory):
        self.resource_directory = Path(resource_directory).expanduser().resolve(
            strict=True
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
        descriptors = {}
        solutions = {}
        aliases = {}
        record_map = {}
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("minor-body manifest records must be objects.")
            identity = record.get("identity")
            if identity is None and record.get("key") == "ceres":
                descriptor, solution = CERES_BODY, CERES_SOLUTION
            else:
                if not isinstance(identity, dict):
                    raise ValueError(
                        "minor-body manifest records require structured identity."
                    )
                number = identity.get("permanent_number")
                if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
                    raise ValueError("permanent minor-planet number must be positive.")
                if identity.get("object_class") != "asteroid":
                    raise ValueError("numbered-asteroid records require asteroid class.")
                name = identity.get("name")
                if name is not None and (
                    not isinstance(name, str) or not name.strip()
                ):
                    raise ValueError("official asteroid name must be non-empty.")
                name = None if name is None else name.strip()
                designation = f"({number})" if name is None else f"{name} ({number})"
                descriptor = SolarSystemBodyDescriptor(
                    target=str(number),
                    entity_key=f"asteroid_{number}",
                    display_name=name or f"({number})",
                    selection_key=str(number),
                    body_class="asteroid",
                    physical_body_id=str(identity["provider_spk_id"]),
                    canonical_designation=designation,
                    iau_number=number,
                    classifications=frozenset(identity.get("classifications", ())),
                    capabilities=frozenset({SYMBOLIC_POINT, APPARENT_TRACK}),
                    ephemeris_source_key="minor_body_spk",
                )
                solution = _solution_from_record(
                    record, number=number, name=name
                )
                if solution.provider_spk_id != str(identity["provider_spk_id"]):
                    raise ValueError("minor-body identity and solution targets differ.")
            key = descriptor.selection_key
            if key in descriptors:
                raise ValueError(f"duplicate permanent minor-planet number: {key}.")
            descriptors[key] = descriptor
            solutions[key] = solution
            record_map[key] = record
            names = [key]
            if solution.name is not None:
                names.append(solution.name)
            names.extend(solution.aliases)
            if key == "ceres":
                names.append("1")
            for candidate in names:
                normalized = _normalized_selection(candidate)
                prior = aliases.get(normalized)
                if prior is not None and prior != key:
                    raise ValueError(
                        f"duplicate minor-body selection alias: {candidate!r}."
                    )
                aliases[normalized] = key
        self._descriptors = descriptors
        self._solutions = solutions
        self._aliases = aliases
        self._records = record_map

    def resolve(self, selection):
        """Resolve a permanent number or exact installed official name."""
        normalized = _normalized_selection(selection)
        try:
            key = self._aliases[normalized]
        except KeyError as error:
            raise KeyError(
                f"minor-body resource set has no installed asteroid {selection!r}."
            ) from error
        return self._descriptors[key]

    def solution_for(self, descriptor):
        key = descriptor.selection_key
        if key not in self._descriptors:
            raise FileNotFoundError(
                f"minor-body manifest has no resource for {key!r}."
            )
        if self._descriptors[key] != descriptor:
            raise ValueError("minor-body descriptor differs from its manifest identity.")
        return self._solutions[key]

    def record_for(self, descriptor):
        self.solution_for(descriptor)
        return self._records[descriptor.selection_key]


def request_minor_body_descriptors(request):
    """Return selected minor-body descriptors in stable catalog order."""
    from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG

    keys = set(request.content.solar_system_objects or ())
    if request.solar_system_track is not None:
        keys.add(request.solar_system_track.descriptor.selection_key)
    external = tuple(getattr(request, "minor_body_descriptors", ()))
    external_by_key = {value.selection_key: value for value in external}
    return tuple(
        descriptor
        for descriptor in (
            external_by_key.get(key) or SOLAR_SYSTEM_BODY_CATALOG.resolve(key)
            for key in sorted(keys)
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
        self.collection = MinorBodyResourceCollection(self.resource_directory)
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
        solution = self.collection.solution_for(descriptor)
        if key not in self._sources:
            self._sources[key] = self._open_source(key, solution)
        return EphemerisSourceBinding(
            self._sources[key], self.planetary_source
        )

    def _open_source(self, key, solution):
        try:
            record = self.collection.record_for(
                self.collection.resolve(key)
            )
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
            f"soln ref.= {solution.orbit_solution_id}",
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
