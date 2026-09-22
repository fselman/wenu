"""Run the controlled 50S.7D.3B LIME inspection on macOS.

The tool verifies and expands, but never installs, the exact accepted LIME
Toolbox package.  It executes only direct-selenographic CLI cases inside the
macOS sandbox with networking denied, uses an isolated HOME, inventories the
selected coefficient netCDF through its bundled netCDF C library, and writes
an immutable evidence manifest.  It adds no Wenu runtime behavior.
"""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile


PACKAGE_BYTES = 516_220_150
PACKAGE_SHA256 = (
    "e0a84e250dc4f5beb8a8305278756bbc0b2b136814b9c4defb053970f983ba21"
)
COEFFICIENT_FILENAME = "LIME_MODEL_COEFS_20251010_V01.nc"
COEFFICIENT_VERSION = "20251010_v1"
COEFFICIENT_BYTES = 154_366
COEFFICIENT_SHA256 = (
    "8e6839d95315eb2d797484be559ad70b69010cc1eb9b614770f61bb5ce2cf691"
)
SANDBOX_PROFILE = "(version 1) (allow default) (deny network*)"
REQUIRED_MACOS_TOOLS = {
    "pkgutil": Path("/usr/sbin/pkgutil"),
    "codesign": Path("/usr/bin/codesign"),
    "sandbox-exec": Path("/usr/bin/sandbox-exec"),
}


@dataclass(frozen=True)
class LimeCase:
    name: str
    phase_angle_deg: float
    expected_outside_model_domain: bool


CASES = (
    LimeCase("negative_above_domain", -90.001, True),
    LimeCase("negative_edge_90", -90.0, False),
    LimeCase("negative_mid", -15.0, False),
    LimeCase("negative_edge_2", -2.0, False),
    LimeCase("negative_below_domain", -1.999, True),
    LimeCase("positive_below_domain", 1.999, True),
    LimeCase("positive_edge_2", 2.0, False),
    LimeCase("positive_mid", 15.0, False),
    LimeCase("positive_edge_90", 90.0, False),
    LimeCase("positive_above_domain", 90.001, True),
)

SUN_MOON_DISTANCE_AU = 0.98
OBSERVER_MOON_DISTANCE_KM = 420_000.0
OBSERVER_SELENO_LATITUDE_DEG = 20.5
OBSERVER_SELENO_LONGITUDE_DEG = -30.2
SOLAR_SELENO_LONGITUDE_DEG = 69.0

_NUMERIC_TYPES = {1, 3, 4, 5, 6, 7, 8, 9, 10, 11}


def _digest(path: Path) -> str:
    result = sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            result.update(block)
    return result.hexdigest()


def _run(command, *, cwd=None, env=None, check=True):
    return subprocess.run(
        tuple(str(item) for item in command),
        cwd=cwd,
        env=env,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _write_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8", newline="\n")


def _case_csv() -> str:
    # LIME's read_selenopoints() consumes six numeric columns without a header.
    rows = []
    for case in CASES:
        rows.append(
            ",".join(
                (
                    str(SUN_MOON_DISTANCE_AU),
                    str(OBSERVER_MOON_DISTANCE_KM),
                    str(OBSERVER_SELENO_LATITUDE_DEG),
                    str(OBSERVER_SELENO_LONGITUDE_DEG),
                    str(SOLAR_SELENO_LONGITUDE_DEG),
                    str(case.phase_angle_deg),
                )
            )
        )
    return "\n".join(rows) + "\n"


def _assert_package(path: Path):
    if not path.is_file():
        raise AssertionError(f"package does not exist: {path}")
    if path.stat().st_size != PACKAGE_BYTES:
        raise AssertionError("LIME package byte-count mismatch")
    if _digest(path) != PACKAGE_SHA256:
        raise AssertionError("LIME package SHA-256 mismatch")


def _find_exactly_one(root: Path, pattern: str) -> Path:
    matches = tuple(root.rglob(pattern))
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one {pattern!r} below {root}, found {len(matches)}"
        )
    return matches[0]


def _tree_summary(root: Path):
    files = tuple(path for path in root.rglob("*") if path.is_file())
    return {
        "file_count": len(files),
        "byte_count": sum(path.stat().st_size for path in files),
    }


def _notice_inventory(resources: Path):
    tokens = ("license", "licence", "notice", "copying", "copyright")
    records = []
    for path in resources.rglob("*"):
        if not path.is_file() or not any(
            token in path.name.lower() for token in tokens
        ):
            continue
        records.append(
            {
                "path": path.relative_to(resources).as_posix(),
                "byte_count": path.stat().st_size,
                "sha256": _digest(path),
            }
        )
    return sorted(records, key=lambda item: item["path"])


class _NetCDF:
    """Small read-only wrapper around the package's bundled netCDF C library."""

    def __init__(self, library: Path):
        self._library = ctypes.CDLL(str(library))
        int_pointer = ctypes.POINTER(ctypes.c_int)
        self._library.nc_strerror.restype = ctypes.c_char_p
        self._library.nc_open.argtypes = (
            ctypes.c_char_p,
            ctypes.c_int,
            int_pointer,
        )
        self._library.nc_open.restype = ctypes.c_int
        self._library.nc_close.argtypes = (ctypes.c_int,)
        self._library.nc_close.restype = ctypes.c_int
        self._library.nc_inq.argtypes = (
            ctypes.c_int,
            int_pointer,
            int_pointer,
            int_pointer,
            int_pointer,
        )
        self._library.nc_inq.restype = ctypes.c_int
        self._library.nc_inq_dim.argtypes = (
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_size_t),
        )
        self._library.nc_inq_dim.restype = ctypes.c_int
        self._library.nc_inq_var.argtypes = (
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
            int_pointer,
            int_pointer,
            int_pointer,
            int_pointer,
        )
        self._library.nc_inq_var.restype = ctypes.c_int
        self._library.nc_inq_attname.argtypes = (
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
        )
        self._library.nc_inq_attname.restype = ctypes.c_int
        self._library.nc_inq_att.argtypes = (
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
            int_pointer,
            ctypes.POINTER(ctypes.c_size_t),
        )
        self._library.nc_inq_att.restype = ctypes.c_int
        self._library.nc_get_att_text.argtypes = (
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_void_p,
        )
        self._library.nc_get_att_text.restype = ctypes.c_int
        self._library.nc_get_att_double.argtypes = (
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_double),
        )
        self._library.nc_get_att_double.restype = ctypes.c_int
        self._library.nc_get_att_string.argtypes = (
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_char_p),
        )
        self._library.nc_get_att_string.restype = ctypes.c_int
        self._library.nc_free_string.argtypes = (
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_char_p),
        )
        self._library.nc_free_string.restype = ctypes.c_int
        self._library.nc_get_var_double.argtypes = (
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_double),
        )
        self._library.nc_get_var_double.restype = ctypes.c_int

    def _check(self, status: int):
        if status:
            message = self._library.nc_strerror(status).decode("utf-8")
            raise AssertionError(f"netCDF error {status}: {message}")

    def inspect(self, path: Path, value_variables=()):
        ncid = ctypes.c_int()
        self._check(self._library.nc_open(os.fsencode(path), 0, ctypes.byref(ncid)))
        try:
            return self._inspect_open(ncid.value, set(value_variables))
        finally:
            self._check(self._library.nc_close(ncid.value))

    def _inspect_open(self, ncid: int, value_variables: set[str]):
        ndims = ctypes.c_int()
        nvars = ctypes.c_int()
        ngatts = ctypes.c_int()
        unlim = ctypes.c_int()
        self._check(
            self._library.nc_inq(
                ncid,
                ctypes.byref(ndims),
                ctypes.byref(nvars),
                ctypes.byref(ngatts),
                ctypes.byref(unlim),
            )
        )
        dimensions = []
        dimension_lengths = {}
        for dimid in range(ndims.value):
            name = ctypes.create_string_buffer(257)
            length = ctypes.c_size_t()
            self._check(
                self._library.nc_inq_dim(
                    ncid, dimid, name, ctypes.byref(length)
                )
            )
            decoded = name.value.decode("utf-8")
            dimension_lengths[dimid] = length.value
            dimensions.append({"name": decoded, "length": length.value})
        variables = []
        selected_values = {}
        for varid in range(nvars.value):
            name = ctypes.create_string_buffer(257)
            xtype = ctypes.c_int()
            variable_ndims = ctypes.c_int()
            dimids = (ctypes.c_int * 32)()
            variable_natts = ctypes.c_int()
            self._check(
                self._library.nc_inq_var(
                    ncid,
                    varid,
                    name,
                    ctypes.byref(xtype),
                    ctypes.byref(variable_ndims),
                    dimids,
                    ctypes.byref(variable_natts),
                )
            )
            decoded = name.value.decode("utf-8")
            dims = [
                dimensions[dimids[index]]["name"]
                for index in range(variable_ndims.value)
            ]
            shape = [
                dimension_lengths[dimids[index]]
                for index in range(variable_ndims.value)
            ]
            attributes = []
            for index in range(variable_natts.value):
                attribute_name = ctypes.create_string_buffer(257)
                self._check(
                    self._library.nc_inq_attname(
                        ncid, varid, index, attribute_name
                    )
                )
                attributes.append(
                    self._attribute(
                        ncid, varid, attribute_name.value.decode("utf-8")
                    )
                )
            variables.append(
                {
                    "name": decoded,
                    "netcdf_type": xtype.value,
                    "dimensions": dims,
                    "shape": shape,
                    "attributes": sorted(
                        attributes, key=lambda item: item["name"]
                    ),
                }
            )
            if decoded in value_variables:
                if xtype.value not in _NUMERIC_TYPES:
                    raise AssertionError(
                        f"requested non-numeric netCDF variable: {decoded}"
                    )
                count = math.prod(shape)
                values = (ctypes.c_double * count)()
                self._check(
                    self._library.nc_get_var_double(ncid, varid, values)
                )
                selected_values[decoded] = list(values)
        global_attributes = []
        for index in range(ngatts.value):
            attribute_name = ctypes.create_string_buffer(257)
            self._check(
                self._library.nc_inq_attname(ncid, -1, index, attribute_name)
            )
            global_attributes.append(
                self._attribute(
                    ncid, -1, attribute_name.value.decode("utf-8")
                )
            )
        return {
            "dimensions": dimensions,
            "variables": variables,
            "global_attributes": sorted(
                global_attributes, key=lambda item: item["name"]
            ),
            "selected_values": selected_values,
        }

    def _attribute(self, ncid: int, varid: int, name: str):
        xtype = ctypes.c_int()
        length = ctypes.c_size_t()
        encoded = name.encode("utf-8")
        self._check(
            self._library.nc_inq_att(
                ncid,
                varid,
                encoded,
                ctypes.byref(xtype),
                ctypes.byref(length),
            )
        )
        record = {
            "name": name,
            "netcdf_type": xtype.value,
            "length": length.value,
        }
        if xtype.value == 2:
            value = ctypes.create_string_buffer(length.value + 1)
            self._check(
                self._library.nc_get_att_text(ncid, varid, encoded, value)
            )
            record["value"] = value.raw[: length.value].decode(
                "utf-8", errors="replace"
            )
        elif xtype.value in _NUMERIC_TYPES:
            values = (ctypes.c_double * length.value)()
            self._check(
                self._library.nc_get_att_double(ncid, varid, encoded, values)
            )
            record["value"] = list(values)
        elif xtype.value == 12:
            values = (ctypes.c_char_p * length.value)()
            self._check(
                self._library.nc_get_att_string(ncid, varid, encoded, values)
            )
            try:
                record["value"] = [
                    ""
                    if value is None
                    else value.decode("utf-8", errors="replace")
                    for value in values
                ]
            finally:
                self._check(self._library.nc_free_string(length.value, values))
        return record


def _netcdf_library(app: Path) -> Path:
    candidates = sorted(
        path
        for path in app.rglob("*")
        if path.is_file()
        and path.name.lower().startswith("libnetcdf")
        and path.suffix in {".dylib", ".so"}
    )
    if candidates:
        return candidates[0]
    raise AssertionError("no bundled netCDF C library found")


def _lime_environment(home: Path):
    temporary = home / "tmp"
    temporary.mkdir(exist_ok=True)
    environment = dict(os.environ)
    environment.update(
        {
            "HOME": str(home),
            "TMPDIR": str(temporary),
            "NO_PROXY": "*",
            "no_proxy": "*",
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "ALL_PROXY": "socks5://127.0.0.1:9",
        }
    )
    return environment


def _run_lime(executable, resources, home, arguments, log_path):
    command = (
        "/usr/bin/sandbox-exec",
        "-p",
        SANDBOX_PROFILE,
        str(executable),
        *arguments,
    )
    result = _run(
        command,
        cwd=resources,
        env=_lime_environment(home),
        check=False,
    )
    _write_text(log_path, result.stdout)
    if result.returncode:
        raise AssertionError(
            f"LIME exited {result.returncode}; inspect {log_path}"
        )
    return command


def _output_values(reader: _NetCDF, path: Path):
    names = (
        "cimel_wlens",
        "irr_cimel",
        "irr_cimel_unc",
        "refl_cimel",
        "refl_cimel_unc",
        "outside_mpa_range",
        "distance_sun_moon",
        "distance_obs_moon",
        "sun_lon",
        "obs_lat",
        "obs_lon",
        "mpa",
    )
    inspection = reader.inspect(path, names)
    return {
        "schema": {
            "dimensions": inspection["dimensions"],
            "variables": inspection["variables"],
            "global_attributes": inspection["global_attributes"],
        },
        "values": inspection["selected_values"],
    }


def _assert_domain_flags(values):
    actual = [bool(round(value)) for value in values["outside_mpa_range"]]
    expected = [case.expected_outside_model_domain for case in CASES]
    if actual != expected:
        raise AssertionError(
            f"LIME model-domain flags differ: {actual!r} != {expected!r}"
        )


def _assert_deterministic_values(first, second):
    names = (
        "cimel_wlens",
        "irr_cimel",
        "refl_cimel",
        "outside_mpa_range",
        "distance_sun_moon",
        "distance_obs_moon",
        "sun_lon",
        "obs_lat",
        "obs_lon",
        "mpa",
    )
    for name in names:
        if first[name] != second[name]:
            raise AssertionError(
                f"repeated deterministic native values differ for {name}"
            )


def _json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


def _json_text(value):
    return json.dumps(
        _json_safe(value), allow_nan=False, indent=2, sort_keys=True
    ) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("output_directory", type=Path)
    arguments = parser.parse_args()

    if sys.platform != "darwin":
        raise AssertionError("50S.7D.3B must run on macOS")
    if arguments.output_directory.exists():
        raise AssertionError("output directory must not already exist")
    if Path("/Applications/LimeTBX.app").exists():
        raise AssertionError(
            "an installed /Applications/LimeTBX.app would make resource "
            "selection ambiguous; remove it before this isolated inspection"
        )
    for name, path in REQUIRED_MACOS_TOOLS.items():
        if not path.exists():
            raise AssertionError(f"required macOS tool is unavailable: {name}")

    _assert_package(arguments.package)
    arguments.output_directory.mkdir(parents=True)
    output = arguments.output_directory.resolve()
    _write_text(output / "cases.csv", _case_csv())

    with tempfile.TemporaryDirectory(prefix="wenu-lime-50s7d3b-") as temporary:
        temporary_path = Path(temporary)
        expanded = temporary_path / "expanded"
        signature = _run(
            (REQUIRED_MACOS_TOOLS["pkgutil"], "--check-signature", arguments.package)
        )
        _write_text(output / "package-signature.txt", signature.stdout)
        expansion = _run(
            (
                REQUIRED_MACOS_TOOLS["pkgutil"],
                "--expand-full",
                arguments.package,
                expanded,
            )
        )
        _write_text(output / "package-expansion.txt", expansion.stdout)

        app = _find_exactly_one(expanded, "LimeTBX.app")
        resources = app / "Contents" / "Resources"
        executable = app / "Contents" / "MacOS" / "LimeTBX.exe"
        if not executable.is_file() or not resources.is_dir():
            raise AssertionError("expanded LIME app layout is incomplete")
        codesign = _run(
            (
                REQUIRED_MACOS_TOOLS["codesign"],
                "--verify",
                "--deep",
                "--strict",
                "--verbose=2",
                app,
            )
        )
        _write_text(output / "app-codesign.txt", codesign.stdout)

        coefficient = resources / "coeff_data" / "versions" / COEFFICIENT_FILENAME
        if coefficient.stat().st_size != COEFFICIENT_BYTES:
            raise AssertionError("coefficient byte-count mismatch")
        if _digest(coefficient) != COEFFICIENT_SHA256:
            raise AssertionError("coefficient SHA-256 mismatch")

        netcdf_library = _netcdf_library(app)
        reader = _NetCDF(netcdf_library)
        coefficient_schema = reader.inspect(coefficient, ("wavelength",))
        _write_text(
            output / "coefficient-schema.json",
            _json_text(coefficient_schema),
        )

        isolated_home = temporary_path / "home"
        isolated_home.mkdir()
        commands = []
        commands.append(
            _run_lime(
                executable,
                resources,
                isolated_home,
                ("-v",),
                output / "lime-version.txt",
            )
        )
        commands.append(
            _run_lime(
                executable,
                resources,
                isolated_home,
                ("-h",),
                output / "lime-help.txt",
            )
        )

        deterministic_paths = []
        for suffix in ("a", "b"):
            destination = output / f"deterministic-{suffix}.nc"
            commands.append(
                _run_lime(
                    executable,
                    resources,
                    isolated_home,
                    (
                        "-C",
                        COEFFICIENT_VERSION,
                        "-i",
                        json.dumps(
                            {
                                "skip_uncertainties": "True",
                                "show_cimel_points": "True",
                                "show_interp_spectrum": "False",
                            },
                            separators=(",", ":"),
                        ),
                        "-l",
                        str(output / "cases.csv"),
                        "-o",
                        f"nc,{destination}",
                    ),
                    output / f"deterministic-{suffix}.log",
                )
            )
            deterministic_paths.append(destination)

        uncertainty = output / "uncertainty.nc"
        commands.append(
            _run_lime(
                executable,
                resources,
                isolated_home,
                (
                    "-C",
                    COEFFICIENT_VERSION,
                    "-i",
                    json.dumps(
                        {
                            "skip_uncertainties": "False",
                            "show_cimel_points": "True",
                            "show_interp_spectrum": "False",
                        },
                        separators=(",", ":"),
                    ),
                    "-l",
                    str(output / "cases.csv"),
                    "-o",
                    f"nc,{uncertainty}",
                ),
                output / "uncertainty.log",
            )
        )

        deterministic_a = _output_values(reader, deterministic_paths[0])
        deterministic_b = _output_values(reader, deterministic_paths[1])
        _assert_deterministic_values(
            deterministic_a["values"], deterministic_b["values"]
        )
        _assert_domain_flags(deterministic_a["values"])
        uncertainty_values = _output_values(reader, uncertainty)
        _assert_domain_flags(uncertainty_values["values"])
        _write_text(
            output / "deterministic-native-output.json",
            _json_text(deterministic_a),
        )
        _write_text(
            output / "uncertainty-native-output.json",
            _json_text(uncertainty_values),
        )

        manifest = {
            "milestone": "50S.7D.3B",
            "status": "offline_lime_evidence_only",
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "network_sandbox": SANDBOX_PROFILE,
            "installed": False,
            "package": {
                "filename": arguments.package.name,
                "byte_count": arguments.package.stat().st_size,
                "sha256": _digest(arguments.package),
            },
            "expanded_tree": _tree_summary(app),
            "coefficient": {
                "filename": coefficient.name,
                "version": COEFFICIENT_VERSION,
                "byte_count": coefficient.stat().st_size,
                "sha256": _digest(coefficient),
            },
            "executable": {
                "path": executable.relative_to(app).as_posix(),
                "byte_count": executable.stat().st_size,
                "sha256": _digest(executable),
            },
            "netcdf_library": {
                "path": netcdf_library.relative_to(app).as_posix(),
                "byte_count": netcdf_library.stat().st_size,
                "sha256": _digest(netcdf_library),
            },
            "notices": _notice_inventory(app),
            "cases": [asdict(case) for case in CASES],
            "commands": [list(command) for command in commands],
            "outputs": {},
            "production_runtime_changed": False,
            "moonlight_status": "not_evaluated",
        }
        for path in sorted(output.iterdir(), key=lambda item: item.name):
            if path.is_file() and path.name != "manifest.json":
                manifest["outputs"][path.name] = {
                    "byte_count": path.stat().st_size,
                    "sha256": _digest(path),
                }
        _write_text(
            output / "manifest.json",
            _json_text(manifest),
        )

    print(f"output_directory={output}")
    print(f"package_sha256={PACKAGE_SHA256}")
    print(f"coefficient_sha256={COEFFICIENT_SHA256}")
    print(f"case_count={len(CASES)}")
    print("network_access=false")
    print("installed=false")
    print("production_runtime_changed=false")
    print("moonlight_status=not_evaluated")


if __name__ == "__main__":
    main()
