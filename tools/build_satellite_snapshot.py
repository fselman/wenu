#!/usr/bin/env python3
"""Build 50S.6G.1B.1 receipts from explicitly supplied response files.

This command is intentionally offline.  It supplies captured bytes through
the same injected-transport seam used by tests and cannot contact CelesTrak.
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
    return parser.parse_args()


def main():
    args = _arguments()
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
