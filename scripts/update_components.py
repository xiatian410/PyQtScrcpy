#!/usr/bin/env python3
"""Install pinned official bundles, with checksums and rollback. Standard library only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def host_platform():
    system, machine = platform.system(), platform.machine().lower()
    arm = machine in ('arm64', 'aarch64')
    if system == 'Windows':
        return 'windows-arm64' if arm else 'windows-x86_64'
    if system == 'Darwin':
        return 'macos-arm64' if arm else 'macos-x86_64'
    if system == 'Linux' and machine in ('x86_64', 'amd64'):
        return 'linux-x86_64'
    raise ValueError(f'No official bundle for {system}/{machine}; install adb/scrcpy via your package manager')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def download(asset, cache):
    target = cache / asset['url'].rsplit('/', 1)[-1]
    if target.exists() and digest(target) == asset['sha256']:
        return target
    partial = target.with_suffix(target.suffix + '.partial')
    try:
        request = urllib.request.Request(asset['url'], headers={'User-Agent': 'PyQtScrcpy-component-updater'})
        with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as output:
            shutil.copyfileobj(response, output)
        if digest(partial) != asset['sha256']:
            raise ValueError(f'SHA-256 mismatch: {target.name}')
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    return target


def safe_member(name):
    path = PurePosixPath(name.replace('\\', '/'))
    if path.is_absolute() or '..' in path.parts or any(':' in part for part in path.parts):
        raise ValueError(f'Unsafe archive member: {name}')


def extract(archive, destination):
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                safe_member(member.filename)
                if (member.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Symlinks are not allowed in ZIP bundles')
            bundle.extractall(destination)
    else:
        with tarfile.open(archive) as bundle:
            for member in bundle.getmembers():
                safe_member(member.name)
                if not member.isdir() and not member.isfile():
                    raise ValueError('Only files and directories are allowed in bundles')
            bundle.extractall(destination, filter='data')


def install_component(name, asset, destination, cache, windows):
    archive = download(asset, cache)
    executable = ('adb' if name == 'platform-tools' else 'scrcpy') + ('.exe' if windows else '')
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.update-', dir=destination) as temporary:
        stage = Path(temporary)
        extract(archive, stage)
        candidates = list(stage.rglob(executable))
        if len(candidates) != 1:
            raise ValueError(f'Expected exactly one {executable} in {archive.name}')
        source = candidates[0].parent
        if not windows:
            candidates[0].chmod(candidates[0].stat().st_mode | 0o755)
        if name == 'scrcpy' and not (source / 'scrcpy-server').is_file():
            raise ValueError('scrcpy-server missing from bundle')
        (source / 'component.json').write_text(json.dumps(asset, indent=2) + '\n', encoding='utf-8')
        target, backup = destination / name, destination / (name + '.previous')
        if backup.exists():
            shutil.rmtree(backup)
        if target.exists():
            target.rename(backup)
        try:
            shutil.move(str(source), str(target))
        except Exception:
            if backup.exists():
                backup.rename(target)
            raise
        print(f'Installed {name} {asset["version"]}: {target}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', help='Override host platform (e.g. windows-x86_64)')
    parser.add_argument('--destination', type=Path, default=ROOT / 'tools')
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache' / 'components')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'components.lock.json').read_text(encoding='utf-8'))
    target = args.platform or host_platform()
    assets = manifest['platforms'][target]
    args.cache.mkdir(parents=True, exist_ok=True)
    for name, asset in assets.items():
        install_component(name, asset, args.destination, args.cache, target.startswith('windows'))


if __name__ == '__main__':
    main()
