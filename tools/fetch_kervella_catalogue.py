#!/usr/bin/env python3
"""Explicit bounded download of the pinned published Kervella Table A.1.

No network on import, retries, mirror fallback, per-star queries or new matching.
The original table/ReadMe bytes stay outside the repository and are verified
before a complete receipt is published. Existing verified captures are reused.
"""
from __future__ import annotations

import argparse
import gzip
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import shutil
import tempfile
from urllib.request import Request, HTTPRedirectHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'docs/developer/data/kervella_association_source_v1.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def bounded_read(stream, maximum):
    parts, size = [], 0
    while True:
        block = stream.read(min(1024 * 1024, maximum - size + 1))
        if not block:
            return b''.join(parts)
        size += len(block)
        require(size <= maximum, 'Published-table byte budget exceeded')
        parts.append(block)


def verify_capture(directory, profile_payload):
    manifest = json.loads((directory / 'source_manifest_v1.json').read_text())
    require(manifest.get('schema') == 'wenu-kervella-source-capture/1'
            and manifest.get('complete') is True, 'Incomplete Kervella capture')
    require(manifest['profile_sha256'] == sha256(profile_payload).hexdigest(),
            'Kervella source profile mismatch')
    profile = json.loads(profile_payload)
    expected = {r['filename']: r for r in profile['resources']}
    expected['tablea1.dat'] = profile['expanded_table']
    require(set(manifest['products']) == set(expected), 'Kervella product-set mismatch')
    for name, specification in expected.items():
        require(Path(name).name == name, 'Unsafe Kervella source path')
        raw = (directory / name).read_bytes()
        actual = {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}
        require(actual == manifest['products'][name]
                and actual['bytes'] == specification['bytes']
                and actual['sha256'] == specification['sha256'],
                'Kervella source digest/size mismatch: ' + name)
    return manifest


def fetch(directory, profile_payload, *, open_request=None):
    directory = Path(directory)
    profile = json.loads(profile_payload)
    if directory.exists():
        return verify_capture(directory, profile_payload)
    directory.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.' + directory.name + '-', dir=directory.parent))
    open_request = open_request or build_opener(NoRedirect()).open
    products, receipts = {}, []
    try:
        for resource in profile['resources']:
            name, url = resource['filename'], resource['url']
            require(Path(name).name == name and name in ('ReadMe', 'tablea1.dat.gz'),
                    'Unexpected Kervella resource')
            require(url == 'https://cdsarc.cds.unistra.fr/ftp/J/A+A/657/A7/' + name,
                    'Unexpected Kervella source URL')
            request = Request(url, headers={'User-Agent': 'Wenu-published-associations/1',
                                             'Accept-Encoding': 'identity'})
            with open_request(request, timeout=60) as response:
                require(response.status == 200 and response.geturl() == url,
                        'Unexpected Kervella HTTP response')
                payload = bounded_read(response, profile['transport_cap_bytes'])
                receipts.append({'url': url, 'status': response.status,
                    'last_modified': response.headers.get('Last-Modified'),
                    'content_type': response.headers.get('Content-Type')})
            actual = {'bytes': len(payload), 'sha256': sha256(payload).hexdigest()}
            require(actual['bytes'] == resource['bytes'] and actual['sha256'] == resource['sha256'],
                    'Published Kervella resource changed; review a new version')
            (temporary / name).write_bytes(payload)
            products[name] = actual
        with gzip.GzipFile(fileobj=BytesIO((temporary / 'tablea1.dat.gz').read_bytes())) as stream:
            payload = bounded_read(stream, profile['expanded_cap_bytes'])
        specification = profile['expanded_table']
        actual = {'bytes': len(payload), 'sha256': sha256(payload).hexdigest()}
        require(actual['bytes'] == specification['bytes'] and actual['sha256'] == specification['sha256'],
                'Expanded Kervella source changed')
        (temporary / 'tablea1.dat').write_bytes(payload)
        products['tablea1.dat'] = actual
        manifest = {'schema': 'wenu-kervella-source-capture/1', 'complete': True,
            'profile_sha256': sha256(profile_payload).hexdigest(), 'products': products,
            'http_receipts': receipts, 'citation': profile['citation']}
        (temporary / 'source_manifest_v1.json').write_text(json.dumps(manifest, indent=2) + '\n')
        directory.mkdir()
        try:
            for path in sorted(temporary.iterdir(), key=lambda p: p.name == 'source_manifest_v1.json'):
                path.replace(directory / path.name)
        except BaseException:
            shutil.rmtree(directory)
            raise
        return manifest
    finally:
        shutil.rmtree(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = fetch(args.output.expanduser(), PROFILE.read_bytes())
    print(json.dumps({'complete': manifest['complete'], 'products': manifest['products']}, indent=2))
    print('KERVELLA SOURCE READY:', args.output.expanduser().resolve())


if __name__ == '__main__':
    main()
