"""Verified data-only snapshots of the currently admitted native ICRS sky.

Only original native layer owners realize/project content. No live objects,
observer state, dynamic imports or pickle payloads are persisted.
"""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import fields, is_dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
from types import MappingProxyType

import numpy as np
import pandas as pd

from wenu.atlas_design import AtlasBandTiling
from wenu import resources
from wenu import star_designations as designations
from wenu.stellar_research import StellarResearch
from wenu.objects.stars import Stars
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.constellation_lines import ConstellationLines
from wenu.sky.constellation_labels import ConstellationLabels
from wenu.sky.constellations import Constellations
from wenu.sky.magellanic_clouds import MagellanicCloudIsophotes
from wenu.sky.milky_way import MilkyWayIsophotes
from wenu.sky.maximal_sphere import (
    CANONICAL_MAXIMAL_SPHERE_PROFILE, CelestialSphereLoadProfile,
    generate_native_icrs_sphere, _require_native_profile,
)

LAYERS = ("milky_way", "magellanic_clouds", "stars",
          "constellation_lines", "constellation_labels")
COMPATIBILITY = "wenu-native-sky-records-v1"
_RECORDS = {c.__name__: c for c in (
    designations.HipLink, designations.DesignationStatement,
    designations.NameCandidate, designations.CuratedDesignation,
    designations.CuratedName, designations.StarDesignations,
    designations.StarDesignationCatalogue,
    StellarResearch,
)}
_COLUMNS = ("magnitude", "ra_degrees", "dec_degrees", "parallax_mas",
            "ra_mas_per_year", "dec_mas_per_year", "ra_hours", "epoch_year",
            "variability_type", "variability_annex", "light_curve_annex",
            "is_variable", "ccdm_id", "ccdm_entry_count", "component_count",
            "multiple_annex", "component_position_angle_deg",
            "component_separation_arcsec", "component_magnitude_difference",
            "is_multiple", "is_constellation_vertex")
_EVIDENCE = {f"designation_{name}" for name in (
    "manifest.json", "wikidata.json", "curation_manifest.json", "curation.json",
    "research_manifest.json", "research.json", "research_policy.json")}


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _keys(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError("Unknown or missing snapshot fields.")


def _json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate snapshot JSON key.")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError("Nonfinite JSON value.")))


def _bytes(path, maximum=64 * 1024 * 1024):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ValueError("Missing, unsafe or oversized snapshot payload.")
    return path.read_bytes()


class _Encoder:
    def __init__(self, directory):
        self.directory = directory
        self.payloads = {}
        self.arrays = {}
        self.array_index = {}

    def flush(self):
        """Pack by dtype; each worker maps a few files, not every ring."""
        groups = {}
        for name, array in self.arrays.items():
            groups.setdefault(array.dtype.str, []).append((name, array))
        for dtype, items in groups.items():
            filename = f"array-{len(self.payloads):04d}.npy"
            offset = 0
            for name, array in items:
                self.array_index[name] = dict(payload=filename, offset=offset,
                                             shape=list(array.shape))
                offset += array.size
            packed = np.concatenate([array.reshape(-1) for _, array in items])
            np.save(self.directory / filename, packed, allow_pickle=False)
            raw = (self.directory / filename).read_bytes()
            self.payloads[filename] = dict(sha256=_digest(raw), size=len(raw),
                                          dtype=dtype, shape=list(packed.shape))

    def encode(self, value):
        if isinstance(value, np.ndarray):
            array = value
            if array.dtype.hasobject:
                if not all(isinstance(v, str) for v in array.flat):
                    raise ValueError("Object arrays are not snapshot payloads.")
                array = array.astype(str)
            if array.dtype.kind not in "bifuU" or array.ndim not in (1, 2):
                raise ValueError("Unsupported snapshot array.")
            name = f"data-{len(self.arrays):04d}"
            self.arrays[name] = array
            return {"array": name}
        if is_dataclass(value) and type(value).__name__ in _RECORDS:
            return {"record": type(value).__name__,
                    "fields": {f.name: self.encode(getattr(value, f.name))
                               for f in fields(value)}}
        if isinstance(value, (dict, MappingProxyType)):
            return {"mapping": [[self.encode(k), self.encode(v)]
                                for k, v in value.items()]}
        if isinstance(value, (list, tuple)):
            return {"tuple": [self.encode(v) for v in value]}
        if isinstance(value, (set, frozenset)):
            return {"frozenset": [self.encode(v) for v in sorted(value)]}
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, float) and not math.isfinite(value):
            return {"float": "nan" if math.isnan(value) else
                    "inf" if value > 0 else "-inf"}
        if value is None or type(value) in (str, bool, int, float):
            return value
        raise ValueError(f"Unsupported snapshot record: {type(value).__name__}.")


def _decode(value, arrays):
    if not isinstance(value, dict):
        if value is None or type(value) in (str, bool, int, float):
            return value
        raise ValueError("Unsupported snapshot scalar.")
    if set(value) == {"array"}:
        if value["array"] not in arrays:
            raise ValueError("Unknown snapshot array reference.")
        return arrays[value["array"]]
    if set(value) in ({"tuple"}, {"frozenset"}):
        name = next(iter(value))
        if not isinstance(value[name], list):
            raise ValueError("Invalid snapshot sequence.")
        items = tuple(_decode(v, arrays) for v in value[name])
        return items if name == "tuple" else frozenset(items)
    if set(value) == {"mapping"}:
        items = value["mapping"]
        if not isinstance(items, list) or any(not isinstance(p, list) or len(p) != 2 for p in items):
            raise ValueError("Invalid snapshot mapping.")
        result = {}
        for key, item in items:
            key = _decode(key, arrays)
            if key in result:
                raise ValueError("Duplicate snapshot mapping key.")
            result[key] = _decode(item, arrays)
        return MappingProxyType(result)
    if set(value) == {"float"} and value["float"] in ("nan", "inf", "-inf"):
        return float(value["float"])
    if set(value) == {"record", "fields"} and value["record"] in _RECORDS:
        owner = _RECORDS[value["record"]]
        _keys(value["fields"], (f.name for f in fields(owner)))
        return owner(**{k: _decode(v, arrays) for k, v in value["fields"].items()})
    raise ValueError("Unsupported snapshot record tag.")


class _NativeOnly:
    def load(self, *args, **kwargs):
        raise RuntimeError("Frozen snapshot layers cannot reload source catalogues.")

    def spherical_geometry(self, observer, **options):
        raise ValueError("A persisted native sky requires native ICRS realization.")


class _SnapshotStars(_NativeOnly, Stars):
    def _render_catalog(self, *, magnitude_limit=None, **options):
        limit = self.magnitude_limit if magnitude_limit is None else magnitude_limit
        if isinstance(limit, bool) or not np.isfinite(limit) or limit > self.magnitude_limit:
            raise ValueError("Insufficient snapshot stellar magnitude coverage; prepare a new revision.")
        identifiers = options.get("include_ids")
        if identifiers is not None and not set(identifiers) <= set(self.source_catalog.index):
            raise ValueError("Requested stellar identities are absent from the snapshot.")
        return super()._render_catalog(magnitude_limit=magnitude_limit, **options)


class _SnapshotLines(_NativeOnly, ConstellationLines):
    pass


class _SnapshotMilkyWay(_NativeOnly, MilkyWayIsophotes):
    pass


class _SnapshotCloud(_NativeOnly, MagellanicCloudIsophotes):
    pass


class _SnapshotLabels(_NativeOnly, ConstellationLabels):
    pass


def _rings(features):
    # Retain level -> compound -> exterior/hole ring nesting exactly.
    return {level: tuple(tuple(np.asarray(ring, dtype=float) for ring in compound)
                         for compound in compounds)
            for level, compounds in features.items()}


def _sky_records(sky):
    stars = sky.stars
    return dict(
        star_ids=stars.source_catalog.index.to_numpy(dtype=np.int64),
        columns={key: stars.source_catalog[key].to_numpy() for key in _COLUMNS},
        designation_catalogue=stars.designation_catalogue,
        research=sky.stellar_research,
        edges=dict(sky.constellation_lines.edges_by_constellation),
        milky_way=dict(features=_rings(sky.milky_way_isophotes.features),
                       source=sky.milky_way_isophotes.source,
                       sources=sky.milky_way_isophotes.sources),
        clouds={cloud: dict(features=_rings(layer.features), fractions=layer.fractions,
                            source=layer.source)
                for cloud, layer in sky.magellanic_cloud_isophotes.items()},
    )


def _source_paths(profile, stack):
    from importlib.resources import as_file
    def resolve(value):
        return Path(stack.enter_context(as_file(value)))
    result = {"hipparcos": resolve(profile.star_filename or resources.catalog_path("hipparcos")),
              "western_lines": resolve(profile.constellation_lines_filename or resources.constellation_lines_path()),
              "lmc": resolve(profile.lmc_filename or resources.magellanic_cloud_isophotes_path("lmc")),
              "smc": resolve(profile.smc_filename or resources.magellanic_cloud_isophotes_path("smc"))}
    if profile.milky_way_filename is not None:
        result["milky_way"] = resolve(profile.milky_way_filename)
    else:
        result.update((f"milky_way_{level}", resolve(resources.milky_way_isophote_path(level)))
                      for level in MilkyWayIsophotes.available_levels)
    root = resolve(resources.star_designations_manifest_path()).parent
    result.update((f"designation_{name}", root / name) for name in
                  ("manifest.json", "wikidata.json", "curation_manifest.json",
                   "curation.json", "research_manifest.json", "research.json",
                   "research_policy.json"))
    return result


def prepare_native_sky_snapshot(design_bytes, destination, *,
                                profile=CANONICAL_MAXIMAL_SPHERE_PROFILE):
    """Prepare a complete admitted native sphere once and commit a new bundle.

    The manifest is linked last as the completion marker in an exclusively
    reserved directory. Existing destinations are never replaced. Reuse reads
    the bundle explicitly; preparation never silently refreshes an old bundle.
    """
    if not isinstance(design_bytes, bytes):
        raise TypeError("design_bytes must be bytes.")
    _require_native_profile(profile)
    atlas = AtlasBandTiling.from_json(design_bytes.decode("utf-8"))
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Snapshot destination exists; choose a new revision.")
    if not destination.parent.is_dir():
        raise ValueError("Snapshot parent directory must exist.")
    with ExitStack() as stack:
        paths = _source_paths(profile, stack)
        before = {key: _digest(path.read_bytes()) for key, path in paths.items()}
        sky = generate_native_icrs_sphere(profile=profile)
        stage = Path(tempfile.mkdtemp(prefix=".wenu-native-snapshot-", dir=destination.parent))
        reserved = False
        try:
            encoder = _Encoder(stage)
            records = encoder.encode(_sky_records(sky))
            encoder.flush()
            (stage / "design.json").write_bytes(design_bytes)
            payloads = encoder.payloads
            payloads["design.json"] = dict(sha256=_digest(design_bytes), size=len(design_bytes))
            # Retain exact source evidence/curation/research metadata, separately
            # from the already decoded effective designation records.
            evidence = {}
            for position, (key, path) in enumerate(paths.items()):
                if _digest(path.read_bytes()) != before[key]:
                    raise ValueError("A source changed during snapshot preparation.")
                if key.startswith("designation_"):
                    name = f"evidence-{position:04d}.json"
                    data = path.read_bytes()
                    (stage / name).write_bytes(data)
                    payloads[name] = dict(sha256=_digest(data), size=len(data))
                    evidence[key] = name
            manifest = dict(schema_version=1, document_kind="wenu-native-sky-snapshot",
                            compatibility=COMPATIBILITY, frame="icrs",
                            origin="solar-system-barycenter", stellar_epoch="J1991.25",
                            position_status="astrometric", coordinate_units="deg",
                            full_sphere=True, layers=list(LAYERS),
                            star_magnitude_limit=profile.star_magnitude_limit,
                            design_id=atlas.geometry.design_id,
                            design_revision=atlas.geometry.revision,
                            payloads=payloads, array_index=encoder.array_index, source_digests=before,
                            evidence=evidence, records=records)
            raw = (json.dumps(manifest, sort_keys=True, allow_nan=False,
                              separators=(",", ":")) + "\n").encode()
            (stage / "manifest.json").write_bytes(raw)
            # Read/admit staged bytes before exposing the completion marker.
            read_native_sky_snapshot(stage)
            destination.mkdir()
            reserved = True
            for path in stage.iterdir():
                if path.name != "manifest.json":
                    os.link(path, destination / path.name)
            os.link(stage / "manifest.json", destination / "manifest.json")
            reserved = False
            return _digest(raw)
        finally:
            if reserved:
                # This invocation exclusively created the destination.
                shutil.rmtree(destination)
            shutil.rmtree(stage)


class NativeSkySnapshot:
    """Verified immutable mapped data; each invocation gets local layer state."""

    def __init__(self, directory, manifest, arrays, records, design_bytes, manifest_sha256):
        self.directory = directory
        self._manifest = manifest
        self.arrays = MappingProxyType(arrays)
        self._records = records
        self.design_bytes = design_bytes
        self.manifest_sha256 = manifest_sha256

    @property
    def star_magnitude_limit(self):
        return self._manifest["star_magnitude_limit"]

    @property
    def source_digests(self):
        return MappingProxyType(dict(self._manifest["source_digests"]))

    def require(self, *, layers=LAYERS, star_magnitude_limit=None, design_sha256=None):
        if isinstance(layers, str) or not set(layers) <= set(LAYERS):
            raise ValueError("Unsupported or absent native snapshot layer.")
        limit = self.star_magnitude_limit if star_magnitude_limit is None else star_magnitude_limit
        if isinstance(limit, bool) or not isinstance(limit, (int, float)) or (
                not math.isfinite(limit) or limit > self.star_magnitude_limit):
            raise ValueError("Insufficient snapshot stellar magnitude coverage; prepare a new revision.")
        if design_sha256 is not None and design_sha256 != _digest(self.design_bytes):
            raise ValueError("Snapshot is bound to a different design.")
        return self

    def make_sky(self):
        """Reconstruct local native facades, never original catalogue loading."""
        data = self._records
        sky = CelestialSphere(None)
        sky.stellar_research = data["research"]
        sky.load_profile = CelestialSphereLoadProfile(star_magnitude_limit=self.star_magnitude_limit)
        mw = _SnapshotMilkyWay(None, levels=MilkyWayIsophotes.available_levels)
        mw.features, mw.source, mw.sources = (
            data["milky_way"][key] for key in ("features", "source", "sources"))
        sky.milky_way_isophotes = sky.add(mw)
        for cloud, content in data["clouds"].items():
            layer = _SnapshotCloud(None, cloud=cloud)
            layer.features, layer.fractions, layer.source = (
                content[key] for key in ("features", "fractions", "source"))
            sky.magellanic_cloud_isophotes[cloud] = sky.add(layer)
        stars = _SnapshotStars(None, magnitude_limit=self.star_magnitude_limit)
        stars.designation_catalogue = data["designation_catalogue"]
        source = pd.DataFrame(dict(data["columns"]), index=data["star_ids"], copy=False)
        source["star_designations"] = [stars.designation_catalogue.get(int(hip)) for hip in source.index]
        stars.source_catalog = source
        stars.catalog = source[source["magnitude"] <= stars.magnitude_limit].copy()
        stars.hip_df = stars.catalog.copy()
        stars.constellation_vertex_ids = frozenset(
            hip for edges in data["edges"].values() for edge in edges for hip in edge)
        sky.stars = sky.add(stars)
        lines = object.__new__(_SnapshotLines)
        lines.stars, lines.system, lines.semantic_system_key = stars, "western", "western"
        lines.filename, lines.constellations = None, None
        lines.edges_by_constellation = dict(data["edges"])
        lines.edges = [edge for edges in lines.edges_by_constellation.values() for edge in edges]
        sky.constellation_lines = sky.add(lines)
        constellation = object.__new__(Constellations)
        constellation.stars, constellation.observer, constellation.system = stars, None, "western"
        constellation.selected, constellation.lines, constellation.boundaries = None, lines, None
        sky.constellations = constellation
        sky.constellation_labels = sky.add(_SnapshotLabels(stars))
        return sky


def read_native_sky_snapshot(directory, *, expected_manifest_sha256=None):
    """Verify all records before returning read-only memory-mapped payloads."""
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Unsafe snapshot directory.")
    raw = _bytes(directory / "manifest.json")
    digest = _digest(raw)
    if expected_manifest_sha256 is not None and digest != expected_manifest_sha256:
        raise ValueError("Snapshot manifest checksum differs from the expected revision.")
    m = _json(raw)
    _keys(m, ("schema_version", "document_kind", "compatibility", "frame", "origin",
              "stellar_epoch", "position_status", "coordinate_units", "full_sphere",
              "layers", "star_magnitude_limit", "design_id", "design_revision",
              "payloads", "array_index", "source_digests", "evidence", "records"))
    expected = dict(schema_version=1, document_kind="wenu-native-sky-snapshot",
                    compatibility=COMPATIBILITY, frame="icrs",
                    origin="solar-system-barycenter", stellar_epoch="J1991.25",
                    position_status="astrometric", coordinate_units="deg",
                    full_sphere=True, layers=list(LAYERS))
    if any(type(m[key]) is not type(value) or m[key] != value for key, value in expected.items()):
        raise ValueError("Unsupported native snapshot schema or coordinate/layer semantics.")
    limit = m["star_magnitude_limit"]
    if type(limit) not in (int, float) or not math.isfinite(limit) or limit <= 0:
        raise ValueError("Invalid snapshot coverage.")
    if not isinstance(m["payloads"], dict) or len(m["payloads"]) > 20000:
        raise ValueError("Invalid snapshot payload index.")
    if set(path.name for path in directory.iterdir()) != set(m["payloads"]) | {"manifest.json"}:
        raise ValueError("Snapshot has missing or unlisted payloads.")
    packed_arrays = {}
    for name, entry in m["payloads"].items():
        if not isinstance(name, str) or not re.fullmatch(
                r"(?:array-[0-9]{4}\.npy|evidence-[0-9]{4}\.json|design\.json)", name):
            raise ValueError("Unsafe snapshot payload name.")
        array = name.endswith(".npy")
        _keys(entry, ("sha256", "size", "dtype", "shape") if array else ("sha256", "size"))
        payload = _bytes(directory / name)
        if type(entry["size"]) is not int or entry["size"] != len(payload) or entry["sha256"] != _digest(payload):
            raise ValueError("Snapshot payload checksum/size mismatch.")
        if array:
            dtype = np.dtype(entry["dtype"])
            if dtype.hasobject or dtype.kind not in "bifuU" or len(entry["shape"]) > 2:
                raise ValueError("Unsafe snapshot array dtype/shape.")
            mapped = np.load(directory / name, mmap_mode="r", allow_pickle=False)
            if mapped.dtype.str != entry["dtype"] or list(mapped.shape) != entry["shape"]:
                raise ValueError("Snapshot array shape/dtype mismatch.")
            if mapped.ndim != 1:
                raise ValueError("Packed snapshot arrays must be one-dimensional.")
            packed_arrays[name] = mapped
    arrays = {}
    if not isinstance(m["array_index"], dict) or len(m["array_index"]) > 20000:
        raise ValueError("Invalid logical snapshot array index.")
    spans = {name: [] for name in packed_arrays}
    for name, descriptor in m["array_index"].items():
        if not isinstance(name, str) or not re.fullmatch("data-[0-9]{4}", name):
            raise ValueError("Invalid logical snapshot array name.")
        _keys(descriptor, ("payload", "offset", "shape"))
        payload, offset, shape = (descriptor[key] for key in ("payload", "offset", "shape"))
        if (payload not in packed_arrays or type(offset) is not int or offset < 0
                or not isinstance(shape, list) or len(shape) not in (1, 2)
                or any(type(n) is not int or n < 0 for n in shape)):
            raise ValueError("Invalid packed snapshot array descriptor.")
        length = math.prod(shape)
        if offset + length > len(packed_arrays[payload]):
            raise ValueError("Snapshot array span exceeds its payload.")
        spans[payload].append((offset, offset + length))
        arrays[name] = packed_arrays[payload][offset:offset + length].reshape(shape)
    for name, segments in spans.items():
        cursor = 0
        for start, stop in sorted(segments):
            if start != cursor:
                raise ValueError("Snapshot array spans overlap or omit data.")
            cursor = stop
        if cursor != len(packed_arrays[name]):
            raise ValueError("Snapshot payload has unindexed data.")
    if "design.json" not in m["payloads"]:
        raise ValueError("Snapshot has no design.")
    design_bytes = _bytes(directory / "design.json")
    atlas = AtlasBandTiling.from_json(design_bytes.decode("utf-8"))
    if (atlas.geometry.design_id, atlas.geometry.revision) != (m["design_id"], m["design_revision"]):
        raise ValueError("Snapshot design identity mismatch.")
    if not isinstance(m["source_digests"], dict) or not m["source_digests"] or any(
            not isinstance(value, str) or not re.fullmatch("[0-9a-f]{64}", value)
            for value in m["source_digests"].values()):
        raise ValueError("Invalid snapshot source identities.")
    sources = set(m["source_digests"])
    common = {"hipparcos", "western_lines", "lmc", "smc"} | _EVIDENCE
    if sources not in (common | {"milky_way"}, common | {
            f"milky_way_{level}" for level in MilkyWayIsophotes.available_levels}):
        raise ValueError("Unsupported or incomplete snapshot source profile.")
    if not isinstance(m["evidence"], dict) or any(
            key not in m["source_digests"] or name not in m["payloads"]
            or m["payloads"][name]["sha256"] != m["source_digests"][key]
            for key, name in m["evidence"].items()):
        raise ValueError("Invalid snapshot source evidence.")
    if set(m["evidence"]) != _EVIDENCE:
        raise ValueError("Incomplete snapshot designation/research evidence.")
    data = _decode(m["records"], arrays)
    if not isinstance(data, MappingProxyType) or set(data) != {
            "star_ids", "columns", "designation_catalogue", "research", "edges", "milky_way", "clouds"}:
        raise ValueError("Invalid native snapshot content.")
    ids, columns = data["star_ids"], data["columns"]
    if (not isinstance(ids, np.ndarray) or ids.ndim != 1 or ids.dtype.kind not in "iu"
            or np.any(ids <= 0) or len(np.unique(ids)) != len(ids)
            or set(columns) != set(_COLUMNS)
            or any(not isinstance(v, np.ndarray) or v.shape != ids.shape for v in columns.values())):
        raise ValueError("Invalid snapshot stellar records.")
    if not np.allclose(columns["ra_hours"] * 15, columns["ra_degrees"], equal_nan=True):
        raise ValueError("Inconsistent native stellar directions.")
    for name, values in columns.items():
        expected_kind = ("b" if name.startswith("is_") else "iu" if name in
                         {"ccdm_entry_count", "component_count"} else "U" if name in
                         {"variability_type", "variability_annex", "light_curve_annex",
                          "ccdm_id", "multiple_annex"} else "f")
        if values.dtype.kind not in expected_kind:
            raise ValueError("Invalid snapshot stellar column dtype.")
    ra, dec, epoch = (columns[name] for name in ("ra_degrees", "dec_degrees", "epoch_year"))
    if (np.any(np.isinf(ra)) or np.any(np.isinf(dec))
            or np.any((ra[np.isfinite(ra)] < 0) | (ra[np.isfinite(ra)] >= 360))
            or np.any(np.abs(dec[np.isfinite(dec)]) > 90)
            or np.any(~np.isfinite(epoch)) or np.any(epoch != 1991.25)):
        raise ValueError("Invalid snapshot native stellar coordinates/epoch.")
    if not isinstance(data["designation_catalogue"], designations.StarDesignationCatalogue):
        raise ValueError("Invalid frozen designation catalogue.")
    catalogue = data["designation_catalogue"]
    research = data["research"]
    if (not isinstance(research, StellarResearch)
            or research.source_sha256 != m["source_digests"].get("designation_research.json")
            or research.policy_sha256 != m["source_digests"].get("designation_research_policy.json")
            or len(research.by_hip) != 77):
        raise ValueError("Frozen shared-star policy disagrees with source provenance.")
    if (catalogue.source_sha256 != m["source_digests"].get("designation_wikidata.json")
            or catalogue.curation_sha256 != m["source_digests"].get("designation_curation.json")
            or any(type(hip) is not int or hip <= 0
                   or not isinstance(record, designations.StarDesignations) or record.hip != hip
                   for hip, record in catalogue.by_hip.items())):
        raise ValueError("Frozen designation identities disagree with source provenance.")
    if set(data["clouds"]) != {"lmc", "smc"} or set(data["milky_way"]["features"]) != set(MilkyWayIsophotes.available_levels):
        raise ValueError("Snapshot is missing isophote coverage.")
    if any(set(content["features"]) != set(MagellanicCloudIsophotes.available_levels)
           for content in data["clouds"].values()):
        raise ValueError("Snapshot is missing Cloud levels.")
    for content in (data["milky_way"], *data["clouds"].values()):
        for compounds in content["features"].values():
            for compound in compounds:
                if not compound:
                    raise ValueError("Snapshot polygon has no exterior ring.")
                for ring in compound:
                    if (not isinstance(ring, np.ndarray) or ring.ndim != 2
                            or ring.shape[1] != 2 or len(ring) < 4
                            or not np.all(np.isfinite(ring))
                            or np.any(np.abs(ring[:, 1]) > 90)):
                        raise ValueError("Invalid snapshot polygon ring.")
    if not data["edges"] or any(
            len(edge) != 2 or any(type(hip) is not int or hip <= 0 for hip in edge)
            for edges in data["edges"].values() for edge in edges):
        raise ValueError("Invalid constellation connectivity.")
    return NativeSkySnapshot(directory, m, arrays, data, design_bytes, digest)
