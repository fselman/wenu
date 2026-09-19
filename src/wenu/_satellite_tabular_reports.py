"""Lossless in-memory tabular interchange for exact crossing reports."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO, StringIO
import json
import re
from typing import Any

import numpy as np
from astropy import __version__ as ASTROPY_VERSION
from astropy.io import ascii
from astropy.io.votable import parse
from astropy.io.votable.tree import (
    Param,
    Resource,
    TableElement,
    TimeSys,
    VOTableFile,
)
from astropy.table import MaskedColumn, Table

from wenu import satellite_crossing_reports as _reports


TABULAR_SCHEMA_VERSION = 1
TABULAR_ENCODER = "wenu exact crossing tabular encoder v1"
_MAX_INPUT_BYTES = 16 * 1024 * 1024
_MAX_ROWS = 100_000
_MAX_CELL_CHARACTERS = 1_000_000
_RESOURCE_ID = "wenu_exact_crossing_report"
_TIMESYS_ID = "wenu_utc_topocenter"
_COMMON_COLUMNS = (
    "record_kind",
    "field_ordinal",
    "field_id",
    "crossing_ordinal",
    "norad_catalog_id",
)
_KINDS = ("report", "field", "crossing")
_XML_FORBIDDEN = re.compile(
    br"<!\s*(?:DOCTYPE|ENTITY)|\b(?:SYSTEM|PUBLIC)\b|xlink\s*:\s*href",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class _ColumnSpec:
    name: str
    record_kind: str
    path: tuple[str, ...]
    value_kind: str
    nullable: bool
    unit: str | None


@dataclass(frozen=True)
class _TabularProjection:
    columns: tuple[_ColumnSpec, ...]
    rows: tuple[tuple[Any | None, ...], ...]
    metadata: tuple[tuple[str, str | int], ...]

    @property
    def column_names(self):
        return _COMMON_COLUMNS + tuple(column.name for column in self.columns)


def _schema_types(schema):
    value = schema.get("type")
    if value is None:
        return ()
    return (value,) if isinstance(value, str) else tuple(value)


def _resolve(schema):
    return _reports._resolve(schema, _reports._REPORT_SCHEMA)


def _unit_for(path):
    name = path[-1]
    if name.endswith("_deg_per_s"):
        return "deg / s"
    if name.endswith("_deg"):
        return "deg"
    if name.endswith("_seconds"):
        return "s"
    if name.endswith("_km"):
        return "km"
    if name.endswith("_m"):
        return "m"
    return None


def _leaf_kind(schema):
    types = set(_schema_types(schema))
    if not types and "const" in schema:
        constant = schema["const"]
        if isinstance(constant, bool):
            types = {"boolean"}
        elif isinstance(constant, int):
            types = {"integer"}
        elif isinstance(constant, float):
            types = {"number"}
        elif isinstance(constant, str):
            types = {"string"}
        elif constant is None:
            types = {"null"}
    nullable = "null" in types
    types.discard("null")
    if not types:
        return "string", True
    if types == {"integer"}:
        return "integer", nullable
    if types == {"number"} or types == {"integer", "number"}:
        return "number", nullable
    if types == {"boolean"}:
        return "boolean", nullable
    return "string", nullable


def _schema_columns(record_kind, schema, *, excluded=(), prefix=()):
    schema = _resolve(schema)
    result = []
    if "object" not in _schema_types(schema):
        raise RuntimeError("tabular record schema must be an object.")
    for name, child in schema.get("properties", {}).items():
        path = prefix + (name,)
        if path in excluded:
            continue
        child = _resolve(child)
        types = _schema_types(child)
        if "object" in types:
            result.extend(
                _schema_columns(
                    record_kind,
                    child,
                    excluded=excluded,
                    prefix=path,
                )
            )
            continue
        value_kind, nullable = _leaf_kind(child)
        result.append(
            _ColumnSpec(
                name=record_kind + "__" + "__".join(path),
                record_kind=record_kind,
                path=path,
                value_kind=value_kind,
                nullable=nullable,
                unit=_unit_for(path),
            )
        )
    return result


def _column_specs():
    root = _reports._REPORT_SCHEMA
    field_schema = _resolve(root["properties"]["fields"])["items"]
    field_schema = _resolve(field_schema)
    crossing_schema = _resolve(field_schema["properties"]["crossings"])["items"]
    return tuple(
        _schema_columns("report", root, excluded=(("fields",),))
        + _schema_columns("field", field_schema, excluded=(("crossings",),))
        + _schema_columns("crossing", crossing_schema)
    )


_COLUMNS = _column_specs()
_COMMON_SPECS = (
    _ColumnSpec("record_kind", "", (), "string", False, None),
    _ColumnSpec("field_ordinal", "", (), "integer", True, None),
    _ColumnSpec("field_id", "", (), "string", True, None),
    _ColumnSpec("crossing_ordinal", "", (), "integer", True, None),
    _ColumnSpec("norad_catalog_id", "", (), "integer", True, None),
)


def _canonical_array(value):
    return _reports._canonical(value)


def _flatten(value, prefix=()):
    result = {}
    for name, item in value.items():
        path = prefix + (name,)
        if isinstance(item, dict):
            result.update(_flatten(item, path))
        elif isinstance(item, list):
            result[path] = _canonical_array(item)
        else:
            result[path] = item
    return result


def _nested_set(target, path, value):
    current = target
    for name in path[:-1]:
        current = current.setdefault(name, {})
    current[path[-1]] = value


def _metadata(document, tabular_format):
    coordinate_values = [
        field["field_of_view"]["coordinate_spec"] for field in document["fields"]
    ]
    observer = document["observer"]
    return (
        ("astropy_version", ASTROPY_VERSION),
        ("coordinate_frames_json", _canonical_array([x["frame"] for x in coordinate_values])),
        ("coordinate_origins_json", _canonical_array([x["origin"] for x in coordinate_values])),
        ("earth_orientation_policy", observer["earth_orientation_policy"]),
        ("position_statuses_json", _canonical_array([x["position_status"] for x in coordinate_values])),
        ("refraction_policy", observer["refraction_policy"]),
        ("report_identity_sha256", document["report_identity_sha256"]),
        ("time_scales_json", _canonical_array([x["time_scale"] for x in coordinate_values])),
        ("wenu_product", document["product"]),
        ("wenu_report_schema_version", document["schema_version"]),
        ("wenu_scientific_status", document["scientific_status"]),
        ("wenu_tabular_encoder", TABULAR_ENCODER),
        ("wenu_tabular_format", tabular_format),
        ("wenu_tabular_schema_version", TABULAR_SCHEMA_VERSION),
    )


def _projection_from_report(report, tabular_format):
    if not isinstance(report, _reports.ExactSatelliteCrossingReport):
        raise TypeError("report must be an ExactSatelliteCrossingReport.")
    document = report.document
    rows = []

    def add(kind, value, field_ordinal=None, crossing_ordinal=None):
        flat = _flatten(value)
        field_id = value.get("field_id")
        norad = value.get("norad_catalog_id")
        common = (kind, field_ordinal, field_id, crossing_ordinal, norad)
        cells = []
        for column in _COLUMNS:
            if column.record_kind != kind:
                cells.append(None)
                continue
            item = flat.get(column.path)
            if item is None and not column.nullable:
                raise ValueError(f"{column.name} is missing from the logical report.")
            cells.append(item)
        rows.append(common + tuple(cells))

    report_value = dict(document)
    fields = report_value.pop("fields")
    add("report", report_value)
    for field_ordinal, field in enumerate(fields):
        field_value = dict(field)
        crossings = field_value.pop("crossings")
        add("field", field_value, field_ordinal=field_ordinal)
        for crossing_ordinal, crossing in enumerate(crossings):
            add(
                "crossing",
                crossing,
                field_ordinal=field_ordinal,
                crossing_ordinal=crossing_ordinal,
            )
    return _TabularProjection(
        columns=_COLUMNS,
        rows=tuple(rows),
        metadata=_metadata(document, tabular_format),
    )


def _parse_array(value, name):
    if not isinstance(value, str) or len(value) > _MAX_CELL_CHARACTERS:
        raise ValueError(f"{name} contains an invalid JSON-array cell.")
    try:
        result = json.loads(
            value,
            object_pairs_hook=_reports._pairs,
            parse_constant=_reports._reject_constant,
        )
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"{name} contains invalid JSON.") from error
    if not isinstance(result, list):
        raise ValueError(f"{name} must contain a JSON array.")
    return result


def _decode_cell(column, value):
    schema = _reports._REPORT_SCHEMA
    # Arrays are the only logical values represented as JSON cell text.
    current = schema
    if column.record_kind == "field":
        current = _resolve(schema["properties"]["fields"])["items"]
    elif column.record_kind == "crossing":
        field = _resolve(schema["properties"]["fields"])["items"]
        current = _resolve(field)["properties"]["crossings"]["items"]
    for name in column.path:
        current = _resolve(current)["properties"][name]
    current = _resolve(current)
    if "array" in _schema_types(current):
        return _parse_array(value, column.name)
    return value


def _report_from_projection(projection):
    if projection.columns != _COLUMNS:
        raise ValueError("tabular projection has an unexpected column contract.")
    if len(projection.rows) > _MAX_ROWS:
        raise ValueError("tabular report contains too many rows.")
    metadata = dict(projection.metadata)
    if tuple(sorted(metadata)) != tuple(name for name, _ in projection.metadata):
        raise ValueError("tabular metadata must use canonical name order.")
    expected = dict(_metadata_from_identity(metadata))
    if metadata != expected:
        raise ValueError("tabular metadata is incomplete or contains unknown values.")

    report_value = None
    fields = []
    current_field = None
    for index, row in enumerate(projection.rows):
        common = dict(zip(_COMMON_COLUMNS, row[: len(_COMMON_COLUMNS)]))
        kind = common["record_kind"]
        if kind not in _KINDS:
            raise ValueError("tabular report contains an unknown record kind.")
        value = {}
        cells = row[len(_COMMON_COLUMNS):]
        for column, cell in zip(_COLUMNS, cells):
            if column.record_kind != kind:
                if cell is not None:
                    raise ValueError("inapplicable tabular cells must be masked.")
                continue
            if cell is None:
                if not column.nullable:
                    raise ValueError(f"{column.name} is unexpectedly masked.")
                decoded = None
            else:
                decoded = _decode_cell(column, cell)
            _nested_set(value, column.path, decoded)

        if kind == "report":
            if index != 0 or report_value is not None:
                raise ValueError("the report row must be first and unique.")
            if any(common[name] is not None for name in _COMMON_COLUMNS[1:]):
                raise ValueError("the report row contains unexpected join values.")
            report_value = value
        elif kind == "field":
            expected_ordinal = len(fields)
            if common["field_ordinal"] != expected_ordinal:
                raise ValueError("field rows are reordered or duplicated.")
            if common["field_id"] != value["field_id"]:
                raise ValueError("field join identity is inconsistent.")
            if common["crossing_ordinal"] is not None or common["norad_catalog_id"] is not None:
                raise ValueError("field rows contain crossing join values.")
            value["crossings"] = []
            fields.append(value)
            current_field = value
        else:
            if current_field is None:
                raise ValueError("crossing row is orphaned.")
            if common["field_ordinal"] != len(fields) - 1:
                raise ValueError("crossing row belongs to another field.")
            if common["field_id"] != value["field_id"]:
                raise ValueError("crossing field identity is inconsistent.")
            if common["norad_catalog_id"] != value["norad_catalog_id"]:
                raise ValueError("crossing NORAD identity is inconsistent.")
            if common["crossing_ordinal"] != len(current_field["crossings"]):
                raise ValueError("crossing rows are reordered or duplicated.")
            current_field["crossings"].append(value)

    if report_value is None:
        raise ValueError("tabular report is missing its report row.")
    report_value["fields"] = fields
    result = _reports.ExactSatelliteCrossingReport._from_document(report_value)
    if result.report_identity_sha256 != metadata["report_identity_sha256"]:
        raise ValueError("tabular report identity does not match metadata.")
    return result


def _metadata_from_identity(metadata):
    required = {
        "astropy_version",
        "coordinate_frames_json",
        "coordinate_origins_json",
        "earth_orientation_policy",
        "position_statuses_json",
        "refraction_policy",
        "report_identity_sha256",
        "time_scales_json",
        "wenu_product",
        "wenu_report_schema_version",
        "wenu_scientific_status",
        "wenu_tabular_encoder",
        "wenu_tabular_format",
        "wenu_tabular_schema_version",
    }
    if set(metadata) != required:
        raise ValueError("tabular metadata keys are not the fixed contract.")
    if metadata["wenu_product"] != _reports.EXACT_REPORT_PRODUCT:
        raise ValueError("tabular product is unsupported.")
    if metadata["wenu_scientific_status"] != _reports.EXACT_REPORT_STATUS:
        raise ValueError("tabular scientific status is unsupported.")
    if metadata["wenu_report_schema_version"] != _reports.EXACT_REPORT_SCHEMA_VERSION:
        raise ValueError("tabular report schema version is unsupported.")
    if metadata["wenu_tabular_schema_version"] != TABULAR_SCHEMA_VERSION:
        raise ValueError("tabular schema version is unsupported.")
    if metadata["wenu_tabular_encoder"] != TABULAR_ENCODER:
        raise ValueError("tabular encoder is unsupported.")
    if not _reports._DIGEST.fullmatch(str(metadata["report_identity_sha256"])):
        raise ValueError("tabular report identity is invalid.")
    for name in (
        "coordinate_frames_json",
        "coordinate_origins_json",
        "position_statuses_json",
        "time_scales_json",
    ):
        _parse_array(metadata[name], name)
    return tuple(sorted(metadata.items()))


def _dtype(column):
    return {
        "integer": np.int64,
        "number": np.float64,
        "boolean": np.bool_,
        "string": str,
    }[column.value_kind]


def _table_from_rows(projection, rows=None, columns=None):
    rows = projection.rows if rows is None else tuple(rows)
    columns = projection.columns if columns is None else tuple(columns)
    names = _COMMON_COLUMNS + tuple(column.name for column in columns)
    result = Table(masked=True)
    all_specs = _COMMON_SPECS + columns
    indices = [projection.column_names.index(name) for name in names]
    for spec, index in zip(all_specs, indices):
        values = [row[index] for row in rows]
        mask = [value is None for value in values]
        data = [
            ("" if spec.value_kind == "string" else False if spec.value_kind == "boolean" else 0)
            if value is None else value
            for value in values
        ]
        column = MaskedColumn(data, name=spec.name, dtype=_dtype(spec), mask=mask)
        if spec.unit is not None:
            column.unit = spec.unit
        column.info.serialize_method["ecsv"] = "data_mask"
        result.add_column(column)
    return result


def _projection_from_table(table, tabular_format):
    expected_names = _COMMON_COLUMNS + tuple(column.name for column in _COLUMNS)
    if tuple(table.colnames) != expected_names:
        raise ValueError("tabular columns do not match the fixed ordered contract.")
    rows = []
    for table_row in table:
        values = []
        for name in expected_names:
            item = table_row[name]
            values.append(None if np.ma.is_masked(item) else item.item() if hasattr(item, "item") else item)
        rows.append(tuple(values))
    metadata = tuple(sorted(table.meta.items()))
    metadata = tuple(
        (name, tabular_format if name == "wenu_tabular_format" else value)
        for name, value in metadata
    )
    return _TabularProjection(_COLUMNS, tuple(rows), metadata)


def to_ecsv(report):
    projection = _projection_from_report(report, "ecsv")
    table = _table_from_rows(projection)
    table.meta.update(dict(projection.metadata))
    output = StringIO()
    ascii.write(table, output, format="ecsv")
    return output.getvalue()


def from_ecsv(value):
    text = _text_input(value, "ECSV")
    try:
        table = ascii.read(text, format="ecsv")
    except Exception as error:
        raise ValueError("report must be valid strict ECSV.") from error
    return _report_from_projection(_projection_from_table(table, "ecsv"))


def _text_input(value, name):
    if isinstance(value, bytes):
        if len(value) > _MAX_INPUT_BYTES:
            raise ValueError(f"{name} input exceeds the byte limit.")
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"{name} input must be UTF-8.") from error
    if not isinstance(value, str):
        raise TypeError(f"{name} input must be text or UTF-8 bytes.")
    if len(value.encode("utf-8")) > _MAX_INPUT_BYTES:
        raise ValueError(f"{name} input exceeds the byte limit.")
    return value


def _scope_columns(kind):
    return tuple(column for column in _COLUMNS if column.record_kind == kind)


def _votable_specs(kind):
    return _COMMON_SPECS + _scope_columns(kind)


def _votable_names(kind):
    names = []
    for spec in _votable_specs(kind):
        names.append(spec.name)
        if spec.nullable and spec.value_kind == "string":
            names.append(f"{spec.name}__is_null")
    return tuple(names)


def _scope_table(projection, kind):
    columns = _scope_columns(kind)
    rows = [row for row in projection.rows if row[0] == kind]
    table = _table_from_rows(projection, rows=rows, columns=columns)
    for spec in _votable_specs(kind):
        if not (spec.nullable and spec.value_kind == "string"):
            continue
        nulls = np.asarray(table[spec.name].mask, dtype=bool).copy()
        table[spec.name].mask = np.zeros(len(table), dtype=bool)
        indicator = MaskedColumn(
            nulls,
            name=f"{spec.name}__is_null",
            dtype=np.bool_,
            mask=np.zeros(len(table), dtype=bool),
        )
        table.add_column(indicator, index=table.colnames.index(spec.name) + 1)
    return table


def to_votable(report):
    projection = _projection_from_report(report, "votable")
    votable = VOTableFile(version="1.5")
    # Astropy 7 validates version 1.5 but does not populate the child-element
    # version flags until parsing.  Populate them from Astropy's own authority.
    votable._config.update(votable._get_version_checks())
    votable._config["version"] = votable.version
    resource = Resource(
        ID=_RESOURCE_ID,
        name="Wenu exact satellite crossing report",
        config=votable._config,
    )
    votable.resources.append(resource)
    resource.time_systems.append(
        TimeSys(
            ID=_TIMESYS_ID,
            timescale="UTC",
            refposition="TOPOCENTER",
            config=votable._config,
        )
    )
    for name, value in projection.metadata:
        resource.params.append(
            Param(
                votable,
                ID=name,
                name=name,
                value=str(value),
                datatype="unicodeChar",
                arraysize="*",
            )
        )
    for kind in _KINDS:
        table = _scope_table(projection, kind)
        element = TableElement.from_table(votable, table)
        # Astropy 7.1 loses masks on variable-length Unicode columns while
        # converting Table -> TableElement.  Restore every source mask so
        # BINARY2 writes the projection's authoritative null flags.
        for name in table.colnames:
            element.array.mask[name] = np.asarray(table[name].mask, dtype=bool)
        element.ID = kind
        element.name = kind
        for field in element.fields:
            field.ID = field.name
            field.description = field.name.replace("__", ".")
            if field.name.endswith("_utc") or field.name.endswith("_instant") or field.name.endswith("_epoch"):
                field.ref = _TIMESYS_ID
        resource.tables.append(element)
    output = BytesIO()
    votable.to_xml(output, tabledata_format="binary2")
    return output.getvalue()


def from_votable(value):
    text = _text_input(value, "VOTable")
    raw = text.encode("utf-8")
    if _XML_FORBIDDEN.search(raw):
        raise ValueError("unsafe XML constructs are forbidden.")
    try:
        votable = parse(BytesIO(raw), verify="exception", invalid="exception")
    except Exception as error:
        raise ValueError("report must be valid strict VOTable 1.5 XML.") from error
    if str(votable.version) != "1.5" or len(votable.resources) != 1:
        raise ValueError("VOTable version or RESOURCE structure is unsupported.")
    resource = votable.resources[0]
    if resource.ID != _RESOURCE_ID or tuple(table.ID for table in resource.tables) != _KINDS:
        raise ValueError("VOTable TABLE structure is unsupported.")
    times = resource.time_systems
    if (
        len(times) != 1
        or times[0].ID != _TIMESYS_ID
        or times[0].timescale != "UTC"
        or times[0].refposition != "TOPOCENTER"
    ):
        raise ValueError("VOTable TIMESYS metadata is invalid.")
    metadata = {param.name: str(param.value) for param in resource.params}
    for name in ("wenu_report_schema_version", "wenu_tabular_schema_version"):
        try:
            metadata[name] = int(metadata[name])
        except (KeyError, ValueError) as error:
            raise ValueError("VOTable numeric metadata is invalid.") from error
    metadata["wenu_tabular_format"] = "votable"

    rows_by_kind = {}
    expected_names = _COMMON_COLUMNS + tuple(column.name for column in _COLUMNS)
    for kind, element in zip(_KINDS, resource.tables):
        table = element.to_table(use_names_over_ids=True)
        expected_scope = _votable_names(kind)
        if tuple(table.colnames) != expected_scope:
            raise ValueError("VOTable FIELD structure is unsupported.")
        for field in element.fields:
            if (
                field.name.endswith("_utc")
                or field.name.endswith("_instant")
                or field.name.endswith("_epoch")
            ) and field.ref != _TIMESYS_ID:
                raise ValueError("VOTable UTC FIELD lacks the required TIMESYS reference.")
        for row_index, row in enumerate(table):
            mapping = {}
            for spec in _votable_specs(kind):
                name = spec.name
                item = row[name]
                masked = bool(np.all(table[name].mask[row_index]))
                if spec.nullable and spec.value_kind == "string":
                    indicator_name = f"{name}__is_null"
                    indicator = row[indicator_name]
                    indicator_masked = bool(
                        np.all(table[indicator_name].mask[row_index])
                    )
                    if indicator_masked or not isinstance(
                        indicator, (bool, np.bool_)
                    ):
                        raise ValueError(
                            "VOTable Unicode null indicator is invalid."
                        )
                    if masked:
                        raise ValueError(
                            "VOTable Unicode carriers must be unmasked."
                        )
                    item = item.item() if hasattr(item, "item") else item
                    if bool(indicator):
                        if item != "":
                            raise ValueError(
                                "VOTable Unicode null indicator contradicts its carrier."
                            )
                        mapping[name] = None
                    else:
                        mapping[name] = item
                    continue
                mapping[name] = (
                    None
                    if masked
                    else item.item()
                    if hasattr(item, "item")
                    else item
                )
            rows_by_kind.setdefault(kind, []).append(
                tuple(mapping.get(name) for name in expected_names)
            )

    report_rows = rows_by_kind.get("report", [])
    field_rows = rows_by_kind.get("field", [])
    crossing_rows = rows_by_kind.get("crossing", [])
    ordered_rows = list(report_rows)
    for ordinal, field_row in enumerate(field_rows):
        ordered_rows.append(field_row)
        ordered_rows.extend(
            row for row in crossing_rows if row[1] == ordinal
        )
    if len(ordered_rows) != len(report_rows) + len(field_rows) + len(crossing_rows):
        raise ValueError("VOTable rows cannot be joined without loss.")
    projection = _TabularProjection(
        _COLUMNS,
        tuple(ordered_rows),
        tuple(sorted(metadata.items())),
    )
    return _report_from_projection(projection)
