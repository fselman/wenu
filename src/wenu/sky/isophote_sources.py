"""Source admission for diffuse contour products, outside numerical geometry.

Receipts preserve declarations rather than assigning a stellar epoch or physical
origin to morphology. Geometry hashes cover original encodings and topology.
"""
from dataclasses import dataclass
import hashlib
import json
from collections.abc import Mapping

import numpy as np


def _plain(value):
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, np.ndarray)):
        return [_plain(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _json(value):
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def geometry_digest(compounds):
    normalized = []
    for compound in compounds:
        if not compound:
            raise ValueError("Isophote polygon has no exterior ring.")
        rings = []
        for ring in compound:
            array = np.asarray(ring, dtype=float)
            if (array.ndim != 2 or array.shape[1] != 2 or len(array) < 3
                    or not np.all(np.isfinite(array)) or np.any(np.abs(array[:, 1]) > 90)):
                raise ValueError("Invalid isophote source ring.")
            if len(array) - int(np.allclose(array[0], array[-1])) < 3:
                raise ValueError("Isophote source ring is too short.")
            rings.append(array.tolist())
        normalized.append(rings)
    return _sha(_json(normalized).encode())


def source_receipt(raw, document, feature):
    """Capture exact bytes and unmodified document/feature properties."""
    return dict(source_sha256=_sha(raw), properties=document.get("properties", {}),
                feature_id=feature.get("id"), feature_properties=feature.get("properties", {}),
                geometry_sha256=geometry_digest(feature["geometry"]["coordinates"]))


@dataclass(frozen=True)
class IsophoteSourceMetadata:
    """Immutable JSON envelope; returned dictionaries are detached copies."""
    record_json: str

    @classmethod
    def admit(cls, family, receipts, *, evidence=()):
        record = dict(format="wenu-isophote-source-v1", family=family,
                      admission="source", levels=receipts, evidence=evidence)
        return cls.from_record(record)

    @classmethod
    def legacy(cls, family, features, source_digests):
        receipts = {str(level): dict(source_sha256=source_digests[str(level)],
                    properties=None, feature_id=None, feature_properties=None,
                    geometry_sha256=geometry_digest(compounds))
                    for level, compounds in features.items()}
        return cls.from_record(dict(format="wenu-isophote-source-v1", family=family,
                                   admission="legacy", levels=receipts, evidence=[]))

    @classmethod
    def from_record(cls, record):
        record = _plain(record)
        if (set(record) != {"format", "family", "admission", "levels", "evidence"}
                or record["format"] != "wenu-isophote-source-v1"
                or record["family"] not in ("milky_way", "lmc", "smc")
                or record["admission"] not in ("source", "legacy")):
            raise ValueError("Invalid isophote source metadata.")
        levels = record["levels"]
        expected = {f"ol{i}" for i in range(1, 6)} if record["family"] == "milky_way" else {str(i) for i in range(1, 5)}
        if not isinstance(levels, dict) or set(levels) != expected:
            raise ValueError("Incomplete isophote source metadata.")
        for level, receipt in levels.items():
            if set(receipt) != {"source_sha256", "properties", "feature_id", "feature_properties", "geometry_sha256"}:
                raise ValueError("Invalid isophote level receipt.")
            for name in ("source_sha256", "geometry_sha256"):
                value = receipt[name]
                if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                    raise ValueError("Invalid isophote source digest.")
            if record["admission"] == "legacy":
                if any(receipt[name] is not None for name in ("properties", "feature_id", "feature_properties")):
                    raise ValueError("Legacy contours cannot acquire source declarations.")
                continue
            for props in (receipt["properties"], receipt["feature_properties"]):
                if not isinstance(props, dict):
                    raise ValueError("Isophote properties must be mappings.")
                if not isinstance(props.get("frame", "ICRS"), str) or props.get("frame", "ICRS").lower() != "icrs":
                    raise ValueError("Unsupported declared isophote frame.")
                if any(props.get(key, "deg") not in ("deg", "degrees") for key in ("units", "coordinate_units")):
                    raise ValueError("Unsupported declared isophote units.")
                # The current static contour model has no epoch/origin transform.
                if any(props.get(key) is not None for key in ("epoch", "reference_epoch", "origin")):
                    raise ValueError("Unsupported declared contour epoch/origin.")
                if record["family"] != "milky_way" and str(props.get("cloud", record["family"])).lower() != record["family"]:
                    raise ValueError("Isophote Cloud metadata is misbound.")
            if record["family"] == "milky_way":
                identity = receipt["feature_id"] or receipt["feature_properties"].get("id")
                if str(identity) != level:
                    raise ValueError("Milky Way feature identity is misbound.")
            if record["family"] != "milky_way":
                props = receipt["feature_properties"]
                if type(props.get("level")) is not int or str(props["level"]) != level:
                    raise ValueError("Isophote feature level is misbound.")
        if not isinstance(record["evidence"], list):
            raise ValueError("Invalid isophote evidence.")
        for evidence in record["evidence"]:
            if (set(evidence) != {"sha256", "text"}
                    or _sha(evidence["text"].encode()) != evidence["sha256"]):
                raise ValueError("Isophote evidence checksum differs.")
        # Captured provenance can only describe these source bytes, not a
        # replacement document under the same path or Cloud name.
        for evidence in record["evidence"]:
            data = json.loads(evidence["text"])
            if record["family"] in ("lmc", "smc"):
                outputs = [v for v in data.get("outputs", []) if v.get("cloud") == record["family"]]
                if len(outputs) != 1 or any(v["source_sha256"] != outputs[0]["sha256"] for v in levels.values()):
                    raise ValueError("Cloud provenance describes different source bytes.")
        if record["admission"] == "legacy" and record["evidence"]:
            raise ValueError("Legacy contours have no captured provenance envelope.")
        return cls(_json(record))

    def to_record(self):
        return json.loads(self.record_json)

    @property
    def fingerprint(self):
        return _sha(self.record_json.encode())

    @property
    def provider(self):
        record = self.to_record()
        for evidence in record["evidence"]:
            data = json.loads(evidence["text"])
            title = data.get("catalogue") or data.get("title")
            if title:
                return title
        title = next(iter(record["levels"].values()))["properties"]
        if title and title.get("title"):
            return title["title"]
        return f'{record["admission"]} {record["family"]} isophotes'

    def validate(self, family, features, *, fractions=None, source_digests=None):
        record = self.from_record(self.to_record()).to_record()
        if record["family"] != family or set(map(str, features)) != set(record["levels"]):
            raise ValueError("Isophote metadata is bound to another layer.")
        for level, compounds in features.items():
            receipt = record["levels"][str(level)]
            if receipt["geometry_sha256"] != geometry_digest(compounds):
                raise ValueError("Isophote geometry differs from admitted source.")
            if source_digests is not None and receipt["source_sha256"] != source_digests[str(level)]:
                raise ValueError("Isophote metadata disagrees with snapshot source digest.")
            if fractions is not None and record["admission"] == "source":
                expected = receipt["feature_properties"].get("fraction_of_peak")
                actual = fractions[level]
                if expected is None:
                    if not np.isnan(actual):
                        raise ValueError("Isophote fraction was not declared.")
                elif actual != expected or not np.isfinite(actual):
                    raise ValueError("Isophote fraction differs from source.")


def packaged_evidence(path, *, receipts, cloud=None):
    """Read existing local provenance; never acquire resources during rendering."""
    from pathlib import Path
    path = Path(path)
    raw = path.read_bytes()
    document = json.loads(raw)
    if cloud is None:
        canonical = path.parent / document["canonical_file"]
        if _sha(canonical.read_bytes()) != document["canonical_sha256"]:
            raise ValueError("Milky Way canonical provenance checksum differs.")
        original = json.loads(canonical.read_bytes())
        originals = {str(f.get("id") or f.get("properties", {}).get("id")): f
                     for f in original["features"]}
        for level, receipt in receipts.items():
            if (receipt["geometry_sha256"] != geometry_digest(originals[level]["geometry"]["coordinates"])
                    or receipt["feature_properties"] != originals[level].get("properties", {})):
                raise ValueError("Milky Way split contour differs from canonical provenance.")
    return ((dict(sha256=_sha(raw), text=raw.decode("utf-8"))),)
