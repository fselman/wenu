#!/usr/bin/env python3
"""Build satellite snapshot evidence from explicitly supplied local files.

This command is intentionally offline. It supplies captured bytes through the
same injected-transport seam used by tests and cannot contact CelesTrak.
"""

import argparse
from pathlib import Path

from wenu.satellites.snapshot_acquisition import (
    ACTIVE_GP_URL,
    POLICY_URL,
    TransportResponse,
    acquire_active_snapshot,
    freeze_policy_receipt,
)
from wenu.satellites.snapshot_admission import (
    CELESTRAK_ACTIVE_20260917_IDENTITY,
    CELESTRAK_ACTIVE_20260917_POLICY_IDENTITY,
    ExternalSnapshotAdmissionPolicy,
)
from wenu.satellites.crossing_matrix import MatrixSpecimenIdentity
from wenu.satellites.crossing_matrix_execution import (
    ACCEPTED_MEDIUM_IDENTITY,
    REAL_EXECUTION_ACKNOWLEDGEMENT,
    run_production_equivalence_matrix,
)
from wenu.satellites.snapshot_evidence import select_medium_snapshot
from wenu.satellites.snapshots import load_snapshot_directory


def _transport(url, body, media_type, started, stopped):
    def request(requested_url):
        if requested_url != url:
            raise ValueError("offline response was requested for another URL.")
        return TransportResponse(
            requested_url=url,
            resolved_url=url,
            status=200,
            media_type=media_type,
            body=body,
            started_utc=started,
            stopped_utc=stopped,
        )

    return request


def _arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    policy = commands.add_parser("freeze-policy")
    policy.add_argument("--response", type=Path, required=True)
    policy.add_argument("--output", type=Path, required=True)
    policy.add_argument("--started-utc", required=True)
    policy.add_argument("--stopped-utc", required=True)
    policy.add_argument("--media-type", required=True)
    acquire = commands.add_parser("build")
    acquire.add_argument("--response", type=Path, required=True)
    acquire.add_argument("--policy-directory", type=Path, required=True)
    acquire.add_argument("--snapshot-root", type=Path, required=True)
    acquire.add_argument("--accept-policy-sha256", required=True)
    acquire.add_argument("--accepted-utc", required=True)
    acquire.add_argument("--started-utc", required=True)
    acquire.add_argument("--stopped-utc", required=True)
    acquire.add_argument("--media-type", required=True)
    select = commands.add_parser("select-medium")
    select.add_argument("--parent-directory", type=Path, required=True)
    select.add_argument("--output-root", type=Path, required=True)
    select.add_argument("--target-count", type=int, default=256)
    select.add_argument(
        "--accept-parent-sha256",
        required=True,
        help="Explicit acknowledgement of the accepted parent canonical digest.",
    )
    matrix = commands.add_parser("run-equivalence-matrix")
    matrix.add_argument("--snapshot-directory", type=Path, required=True)
    matrix.add_argument("--output-root", type=Path, required=True)
    matrix.add_argument("--accept-medium-sha256", required=True)
    matrix.add_argument("--accept-receipt-sha256", required=True)
    matrix.add_argument("--accept-parent-sha256", required=True)
    matrix.add_argument(
        "--acknowledgement",
        required=True,
        help="Exact explicit acknowledgement required for a real offline run.",
    )
    return parser.parse_args()


def _select_medium(args):
    expected = CELESTRAK_ACTIVE_20260917_IDENTITY
    if args.accept_parent_sha256.lower() != expected.content_sha256:
        raise ValueError(
            "--accept-parent-sha256 must equal the accepted CelesTrak "
            "Active canonical digest."
        )
    snapshot = load_snapshot_directory(args.parent_directory)
    admission = ExternalSnapshotAdmissionPolicy(
        CELESTRAK_ACTIVE_20260917_POLICY_IDENTITY,
        (expected,),
    ).admit(snapshot)
    return select_medium_snapshot(
        args.parent_directory,
        args.output_root,
        admission=admission,
        target_count=args.target_count,
    )


def _run_equivalence_matrix(args):
    expected = ACCEPTED_MEDIUM_IDENTITY
    supplied = MatrixSpecimenIdentity(
        content_sha256=args.accept_medium_sha256,
        selection_receipt_sha256=args.accept_receipt_sha256,
        parent_content_sha256=args.accept_parent_sha256,
        record_count=expected.record_count,
    )
    if supplied != expected:
        raise ValueError("the supplied digests do not identify the accepted medium.")
    if args.acknowledgement != REAL_EXECUTION_ACKNOWLEDGEMENT:
        raise ValueError(
            "--acknowledgement must contain the exact explicit offline-run phrase."
        )
    return run_production_equivalence_matrix(
        args.snapshot_directory,
        args.output_root,
        specimen_identity=supplied,
        acknowledgement=args.acknowledgement,
    )


def main():
    args = _arguments()
    if args.operation == "select-medium":
        result = _select_medium(args)
    elif args.operation == "run-equivalence-matrix":
        result = _run_equivalence_matrix(args)
    else:
        body = args.response.read_bytes()
        if args.operation == "freeze-policy":
            result = freeze_policy_receipt(
                args.output,
                transport=_transport(
                    POLICY_URL,
                    body,
                    args.media_type,
                    args.started_utc,
                    args.stopped_utc,
                ),
            )
        else:
            result = acquire_active_snapshot(
                args.snapshot_root,
                args.policy_directory,
                accepted_policy_sha256=args.accept_policy_sha256,
                accepted_utc=args.accepted_utc,
                transport=_transport(
                    ACTIVE_GP_URL,
                    body,
                    args.media_type,
                    args.started_utc,
                    args.stopped_utc,
                ),
            )
    print(result)


if __name__ == "__main__":
    main()
