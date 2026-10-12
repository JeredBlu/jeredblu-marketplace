#!/usr/bin/env python3
"""Dependency leads, not a complete dependency audit. No package-manager execution.
OSV receives package names/versions only; --offline disables it. Exit 3 means gaps.
"""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
import urllib.parse
import urllib.request
try:
    import tomllib
except ImportError:
    tomllib = None

SKIP = {'.git', 'node_modules', 'vendor', 'third_party', 'Pods', '.build', 'target', 'dist'}
MANIFESTS = {'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'requirements.txt',
             'pyproject.toml', 'poetry.lock', 'uv.lock', 'Pipfile.lock', 'setup.py', 'Cargo.toml',
             'Cargo.lock', 'go.mod', 'go.sum', 'Package.swift', 'Package.resolved', 'Gemfile',
             'Gemfile.lock', 'Podfile', 'Podfile.lock', 'composer.json', 'composer.lock',
             'build.gradle', 'build.gradle.kts', 'pom.xml'}
LOCKS = {'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'uv.lock', 'Pipfile.lock',
         'Cargo.lock', 'go.sum', 'Package.resolved', 'Gemfile.lock', 'Podfile.lock', 'composer.lock'}
SUPPORTED = {'package.json', 'package-lock.json', 'poetry.lock', 'uv.lock', 'Cargo.lock',
             'go.sum', 'Package.resolved', 'Pipfile.lock'}
MAX_BYTES = 8 * 1024 * 1024


def osv(pkgs):
    findings = []
    for start in range(0, len(pkgs), 500):
        chunk = pkgs[start:start + 500]
        body = json.dumps({'queries': [{'package': {'ecosystem': e, 'name': n}, 'version': v}
                                      for e, n, v in chunk]}).encode()
        req = urllib.request.Request('https://api.osv.dev/v1/querybatch', data=body,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=60) as response:
            results = json.load(response).get('results')
        if not isinstance(results, list) or len(results) != len(chunk):
            raise ValueError('OSV returned incomplete/malformed results')
        for (eco, name, version), result in zip(chunk, results):
            if not isinstance(result, dict):
                raise ValueError('OSV result is not an object')
            # Paginated responses need a follow-up; never turn a partial batch into clean.
            if result.get('next_page_token'):
                raise ValueError('OSV results paginated; run osv-scanner or follow up manually')
            for vuln in result.get('vulns', []):
                findings.append({'ecosystem': eco, 'name': name, 'version': version, 'id': vuln['id']})
    return findings


def parse(name, text, output):
    pinned, sources, scripts, notes = output['packages'], output['unusual_sources'], output['install_scripts'], output['notes']
    def add(eco, n, v):
        if not isinstance(n, str) or not isinstance(v, str) or not n or not v:
            raise ValueError('invalid package name/version')
        pinned.append((eco, n, v))
    if name == 'package.json':
        obj = json.loads(text)
        for section in ('dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies'):
            for n, v in (obj.get(section) or {}).items():
                if re.search(r'^(git|github:|https?:|file:|link:)|/', str(v)) and not str(v).startswith('npm:'):
                    sources.append(f'{n}: {v}')
        for k, v in (obj.get('scripts') or {}).items():
            if k in {'preinstall', 'install', 'postinstall', 'prepare', 'prepublish'}:
                scripts.append(f'{k}: {v}')
    elif name == 'package-lock.json':
        obj = json.loads(text)
        if obj.get('lockfileVersion') == 1:
            def legacy(deps):
                for n, meta in deps.items():
                    add('npm', n, meta['version'])
                    if meta.get('resolved') and urllib.parse.urlsplit(meta['resolved']).hostname != 'registry.npmjs.org':
                        sources.append(f'{n}: {meta["resolved"]}')
                    legacy(meta.get('dependencies', {}))
            legacy(obj.get('dependencies', {}))
            notes.append('npm lockfile v1 does not establish dependency install-script coverage')
        elif obj.get('lockfileVersion') in (2, 3) and isinstance(obj.get('packages'), dict):
            for path, meta in obj['packages'].items():
                if not path:
                    continue
                if meta.get('link'):
                    notes.append(f'linked/local dependency requires manual review: {path}')
                    continue
                n = meta.get('name') or path.split('node_modules/')[-1]
                add('npm', n, meta['version'])
                if meta.get('hasInstallScript'):
                    scripts.append(f'{n}@{meta["version"]}: dependency has install script')
                if meta.get('resolved') and urllib.parse.urlsplit(meta['resolved']).hostname != 'registry.npmjs.org':
                    sources.append(f'{n}: {meta["resolved"]}')
        else:
            raise ValueError('unsupported/malformed npm lockfile version')
    elif name.startswith('requirements') and name.endswith('.txt'):
        for line in text.splitlines():
            line = line.split('#')[0].strip()
            if not line:
                continue
            m = re.fullmatch(r'([A-Za-z0-9_.\-]+)(?:\[[^\]]+\])?==([A-Za-z0-9_.\-+!]+)', line)
            if m:
                add('PyPI', *m.groups())
            else:
                notes.append('unresolved requirement (range, marker, include, URL or option): ' + line)
                if re.search(r'git\+|https?://|--index-url|--extra-index-url', line):
                    sources.append(line)
    elif name in {'poetry.lock', 'uv.lock', 'Cargo.lock'}:
        if tomllib is None:
            raise ValueError('TOML parser unavailable: use Python 3.11+; not checked')
        obj = tomllib.loads(text)
        if not isinstance(obj.get('package'), list):
            raise ValueError('missing package list in TOML lockfile')
        for package in obj['package']:
            source = package.get('source')
            if isinstance(source, dict) and ('editable' in source or 'virtual' in source):
                notes.append('local/workspace package requires manual review: ' + str(package.get('name')))
                continue
            add('crates.io' if name == 'Cargo.lock' else 'PyPI', package['name'], package['version'])
            if source:
                value = source if isinstance(source, str) else json.dumps(source)
                # These are leads, not proof of a trustworthy source.
                if not (value == 'registry+https://github.com/rust-lang/crates.io-index' or
                        isinstance(source, dict) and source.get('registry') == 'https://pypi.org/simple'):
                    sources.append(f'{package["name"]}: {value}')
    elif name == 'go.sum':
        for line in text.splitlines():
            fields = line.split()
            if len(fields) != 3:
                raise ValueError('malformed go.sum line')
            add('Go', fields[0], fields[1].removesuffix('/go.mod'))
        notes.append('go.sum may include unused versions; selected dependency graph and replacements need manual review')
    elif name == 'Package.resolved':
        obj = json.loads(text)
        pins = obj.get('pins', (obj.get('object') or {}).get('pins'))
        if not isinstance(pins, list):
            raise ValueError('missing Swift pins')
        for pin in pins:
            location = pin.get('location') or pin.get('repositoryURL')
            state = pin.get('state') or {}
            if location and state.get('version'):
                add('SwiftURL', location, state['version'])
            else:
                notes.append('Swift dependency without a version needs manual advisory review: ' + str(location))
    elif name == 'Pipfile.lock':
        obj = json.loads(text)
        if not any(k in obj for k in ('default', 'develop')):
            raise ValueError('missing Pipfile package sections')
        for section in ('default', 'develop'):
            for n, meta in obj.get(section, {}).items():
                version = meta.get('version', '')
                if not version.startswith('=='):
                    notes.append('unresolved Pipfile dependency: ' + n)
                else:
                    add('PyPI', n, version[2:])


def inspect(root, offline=False):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('target must be a directory')
    result = {'status': 'complete', 'files': [], 'packages': [], 'unusual_sources': [], 'install_scripts': [],
              'notes': [], 'errors': [], 'skipped_directories': [], 'osv': {'status': 'not_run', 'findings': []}}
    def walk_error(exc):
        result['errors'].append(str(exc))
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        kept = []
        for name in sorted(dirs):
            path = Path(directory) / name
            if name in SKIP or path.is_symlink():
                if name != '.git':
                    result['skipped_directories'].append(str(path.relative_to(root)))
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(files):
            if name not in MANIFESTS and not (name.startswith('requirements') and name.endswith('.txt')):
                continue
            path = Path(directory) / name
            item = {'path': str(path.relative_to(root)), 'status': 'parsed'}
            result['files'].append(item)
            if name not in SUPPORTED and not name.startswith('requirements'):
                item['status'] = 'unsupported' if name in LOCKS else 'manifest_only'
                item['reason'] = 'Listed, not parsed. Dependency/advisory coverage requires another tool or explicit review.'
                continue
            try:
                if not stat.S_ISREG(path.lstat().st_mode):
                    raise ValueError('symlink/non-regular manifest not opened')
                fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
                with os.fdopen(fd, 'rb') as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise ValueError('manifest changed to non-regular file')
                    data = stream.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise ValueError('manifest exceeds size limit')
                local = {'packages': [], 'unusual_sources': [], 'install_scripts': [], 'notes': []}
                parse(name, data.decode('utf-8'), local)
                for key, values in local.items():
                    result[key].extend(values if key == 'packages' else [item['path'] + ': ' + v for v in values])
            except (ValueError, OSError, KeyError, TypeError, AttributeError, RecursionError) as exc:
                item.update(status='failed', reason=str(exc))
                result['errors'].append(item['path'] + ': ' + str(exc))
    result['packages'] = sorted(set(result['packages']))
    result['lockfiles_present'] = [x['path'] for x in result['files'] if Path(x['path']).name in LOCKS]
    if result['files'] and not result['lockfiles_present']:
        result['notes'].append('No recognized lockfile; requirements pins alone may omit transitive dependencies')
    if offline:
        result['osv']['status'] = 'skipped_offline'
    elif not result['packages']:
        result['osv']['status'] = 'not_checked_no_resolved_packages'
    else:
        try:
            result['osv'] = {'status': 'checked_parsed_packages_only', 'findings': osv(result['packages'])}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result['osv'] = {'status': 'failed', 'error': str(exc), 'findings': []}
            result['errors'].append('OSV query failed: ' + str(exc))
    if (result['errors'] or result['notes'] or result['skipped_directories'] or
            any(x['status'] != 'parsed' for x in result['files']) or
            result['osv']['status'] != 'checked_parsed_packages_only'):
        result['status'] = 'incomplete'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        result = inspect(args.target, args.offline)
    except (ValueError, OSError) as exc:
        print('Dependency check failed: ' + str(exc), file=sys.stderr)
        return 2
    if not args.json:
        print('== Dependency evidence: ' + result['status'].upper() + ' ==')
        print('Listed manifests are not necessarily parsed. OSV findings cover parsed package versions only.')
    print(json.dumps(result, indent=2))
    return 3 if result['status'] == 'incomplete' else 0


if __name__ == '__main__':
    sys.exit(main())
