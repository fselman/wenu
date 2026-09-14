"""Exact installed and provider-backed minor-body identity contracts."""

from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu.minor_body_identity import (
    AmbiguousMinorBodyIdentityError,
    MinorBodyIdentityError,
    MinorBodyIdentityNotFoundError,
    ProviderResponse,
    identity_query_parameters,
    resolve_comet_identity,
    resolve_minor_body_identity,
)


FIXTURES = Path("tests/fixtures")
TEN_P = FIXTURES / "sbdb_minor_body_identity_10p.json"
TEMPEL = FIXTURES / "sbdb_minor_body_identity_tempel_ambiguous.json"
HYGIEA = FIXTURES / "sbdb_minor_body_identity_10_hygiea.json"
NOT_FOUND = FIXTURES / "sbdb_minor_body_identity_not_found.json"
NOW = datetime(2026, 9, 13, 23, 0, tzinfo=timezone.utc)


def response(path, status=200):
    return ProviderResponse(status, path.read_bytes())


def test_designations_use_exact_des_and_names_use_sstr():
    assert identity_query_parameters(
        "10P", expected_class="comet"
    )["des"] == "10P"
    assert identity_query_parameters(
        "10P/Tempel 2", expected_class="comet"
    )["des"] == "10P"
    assert identity_query_parameters(
        "Tempel 2", expected_class="comet"
    )["sstr"] == "Tempel 2"
    assert identity_query_parameters(
        "Hygiea", expected_class="asteroid"
    )["sstr"] == "Hygiea"


@pytest.mark.parametrize(
    "selection", ("10P", "10p", "  10P  ", "10P/Tempel 2", "Tempel 2")
)
def test_exact_comet_aliases_resolve_one_provider_identity(selection):
    calls = []

    identity = resolve_comet_identity(
        selection,
        fetch=lambda url, parameters: (
            calls.append((url, parameters)) or response(TEN_P)
        ),
        now=lambda: NOW,
    )

    assert len(calls) == 1
    assert identity.object_class == "comet"
    assert identity.kind == "cn"
    assert identity.canonical_designation == "10P"
    assert identity.primary_designation == "10P"
    assert identity.prefix == "P"
    assert identity.permanent_number == 10
    assert identity.fragment is None
    assert identity.name == "Tempel 2"
    assert identity.provider_spk_id == "1000094"
    assert identity.orbit_class_code == "JFc"
    assert identity.orbit_solution_id == "K265/50"
    assert identity.source == "provider"
    assert identity.retrieved_at_utc == NOW
    assert identity.raw_sha256
    assert "10P/Tempel 2" in identity.aliases


def test_generic_boundary_can_resolve_an_asteroid_when_explicitly_requested():
    identity = resolve_minor_body_identity(
        "Hygiea",
        expected_class="asteroid",
        fetch=lambda *values: response(HYGIEA),
        now=lambda: NOW,
    )

    assert identity.object_class == "asteroid"
    assert identity.kind == "an"
    assert identity.canonical_designation == "10"
    assert identity.permanent_number == 10
    assert identity.name == "Hygiea"
    assert identity.provider_spk_id == "20000010"
    assert "A849 GA" in identity.aliases


def test_bare_number_is_not_accepted_as_a_comet_or_sent_to_sbdb():
    calls = []

    with pytest.raises(
        MinorBodyIdentityNotFoundError, match="not a comet designation"
    ):
        resolve_comet_identity(
            "10", fetch=lambda *values: calls.append(values)
        )

    assert calls == []


def test_ambiguous_provider_result_never_selects_the_first_candidate():
    with pytest.raises(
        AmbiguousMinorBodyIdentityError, match="11 candidates"
    ) as failure:
        resolve_comet_identity(
            "Tempel",
            fetch=lambda *values: response(TEMPEL, status=300),
        )

    assert "9P/Tempel 1" in str(failure.value)
    assert "10P/Tempel 2" in str(failure.value)


@pytest.mark.parametrize("selection", ("pencils 10P", "Tempel_STA"))
def test_documented_not_found_response_is_an_exact_failure(selection):
    with pytest.raises(
        MinorBodyIdentityNotFoundError, match="no exact identity"
    ):
        resolve_comet_identity(
            selection, fetch=lambda *values: response(NOT_FOUND)
        )


def test_unsigned_unknown_error_shape_still_fails_closed():
    raw = b'{"code":"200","message":"different","moreInfo":"url"}'
    with pytest.raises(MinorBodyIdentityError, match="signature"):
        resolve_comet_identity(
            "missing",
            fetch=lambda *values: ProviderResponse(200, raw),
        )


def test_unique_non_comet_response_fails_the_comet_class_constraint():
    with pytest.raises(
        MinorBodyIdentityNotFoundError, match="not expected class 'comet'"
    ):
        resolve_comet_identity(
            "Hygiea", fetch=lambda *values: response(HYGIEA)
        )


def test_provider_signature_and_schema_drift_fail_closed():
    document = json.loads(TEN_P.read_text(encoding="utf-8"))
    cases = []

    changed = json.loads(json.dumps(document))
    changed["signature"]["version"] = "other"
    cases.append((changed, "signature"))

    changed = json.loads(json.dumps(document))
    changed["extra"] = {}
    cases.append((changed, "schema changed"))

    changed = json.loads(json.dumps(document))
    del changed["object"]["spkid"]
    cases.append((changed, "object.spkid"))

    for changed, message in cases:
        raw = json.dumps(changed).encode("utf-8")
        with pytest.raises(MinorBodyIdentityError, match=message):
            resolve_comet_identity(
                "10P",
                fetch=lambda *values, raw=raw: ProviderResponse(200, raw),
                now=lambda: NOW,
            )


def test_installed_exact_alias_wins_without_network_access():
    descriptor = SimpleNamespace(
        body_class="comet",
        canonical_designation="10P/Tempel 2",
        iau_number=10,
    )
    solution = SimpleNamespace(
        primary_designation="10P",
        aliases=("10P/Tempel 2", "Tempel 2"),
        name="Tempel 2",
        provider_spk_id="1000094",
        orbit_solution_id="K265/50",
        provider="NASA/JPL Horizons",
        service_version="1.2",
    )

    class Collection:
        def resolve(self, selection):
            assert selection == " tempel 2 "
            return descriptor

        def solution_for(self, value):
            assert value is descriptor
            return solution

    identity = resolve_comet_identity(
        " tempel 2 ",
        installed_collection=Collection(),
        fetch=lambda *values: pytest.fail("network access was attempted"),
    )

    assert identity.source == "installed"
    assert identity.canonical_designation == "10P/Tempel 2"
    assert identity.name == "Tempel 2"
    assert identity.raw_sha256 is None
    assert identity.request_parameters == ()


@pytest.mark.parametrize("expected", ("planet", "", None))
def test_expected_class_is_mandatory_and_closed(expected):
    with pytest.raises(ValueError, match="expected_class"):
        resolve_minor_body_identity("10P", expected_class=expected)
