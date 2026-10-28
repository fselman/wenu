"""Explicit offline preparation of a new exact-event stellar epoch bundle."""
import argparse
import json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stellar-motion-config', required=True,
                        help='Existing explicit stellar motion TOML, with local source/model/event bindings')
    parser.add_argument('--destination', required=True, help='New directory; existing outputs are never replaced')
    args = parser.parse_args(argv)
    from wenu.stellar_state import load_stellar_motion_request
    from wenu.stellar_epoch import prepare_stellar_epoch
    digest = prepare_stellar_epoch(load_stellar_motion_request(args.stellar_motion_config), args.destination)
    print(json.dumps(dict(destination=args.destination, manifest_sha256=digest,
                         interpretation='exact-event local stellar data; no chart/observer/nearby-epoch adoption')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
