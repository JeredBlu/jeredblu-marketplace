#!/usr/bin/env python3
"""Single-pass, bounded static text scan. Matches are leads, not judgments.

No target files are executed/imported. Symlinks and special files are not read.
Exit 0: completed pattern scan; 3: explicit coverage gaps; 2: invalid input.
"""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys

PATTERNS = Path(__file__).resolve().parent.parent / 'references/scan-patterns.json'


def scan(target, max_file=8*1024*1024, max_total=64*1024*1024, max_files=10000, max_leads=50000):
    root = Path(target)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('target must be a non-symlink directory')
    patterns = [(p['category'], re.compile(p['pattern'], re.I)) for p in json.loads(PATTERNS.read_text())]
    result = {'target': str(root.resolve()), 'files_read': [], 'skipped': [], 'leads': [],
              'categories': {name: 0 for name, _ in patterns}, 'bytes_read': 0}
    def gap(path, reason):
        result['skipped'].append({'file': str(path), 'reason': reason})
    def error(exc):
        gap(exc.filename or '.', str(exc))
    count = 0
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=error):
        dirs.sort(); files.sort()
        for name in dirs[:]:
            path = Path(directory) / name
            if path.is_symlink() or name == '.git':
                dirs.remove(name)
                gap(path.relative_to(root), 'symlink directory' if path.is_symlink() else 'VCS metadata excluded')
        for name in files:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            count += 1
            if count > max_files:
                gap(relative, 'file-count limit reached; remaining tree not scanned')
                result['complete'] = False
                return result
            try:
                mode = path.lstat().st_mode
                if not stat.S_ISREG(mode):
                    gap(relative, 'symlink or special file'); continue
                # O_NOFOLLOW avoids following a final-component symlink swapped in after lstat.
                fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
                with os.fdopen(fd, 'rb') as handle:
                    if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                        gap(relative, 'file changed to special file'); continue
                    size = os.fstat(handle.fileno()).st_size
                    if size > max_file or result['bytes_read'] + size > max_total:
                        gap(relative, 'file or total byte limit'); continue
                    data = handle.read(min(max_file, max_total-result['bytes_read']) + 1)
                if len(data) > max_file or result['bytes_read'] + len(data) > max_total:
                    gap(relative, 'file grew past byte limit'); continue
                result['bytes_read'] += len(data)
                if b'\0' in data:
                    gap(relative, 'binary/NUL content; manual format inspection needed'); continue
                try:
                    content = data.decode('utf-8')
                except UnicodeDecodeError:
                    gap(relative, 'non-UTF-8 content; manual decoding needed'); continue
                result['files_read'].append(relative)
                for number, line in enumerate(content.split('\n'), 1):
                    for category, pattern in patterns:
                        if pattern.search(line):
                            if len(result['leads']) >= max_leads:
                                gap(relative, 'lead limit reached; remaining content not scanned')
                                result['complete'] = False
                                return result
                            result['categories'][category] += 1
                            result['leads'].append({'category': category, 'file': relative, 'line': number, 'text': line})
            except OSError as exc:
                gap(relative, str(exc))
    result['complete'] = not result['skipped']
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target')
    parser.add_argument('--json', action='store_true', help='Full machine-readable leads and coverage inventory')
    args = parser.parse_args()
    try:
        result = scan(args.target)
    except (OSError, ValueError) as exc:
        print('SCAN FAILED: ' + str(exc), file=sys.stderr); return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print('Read-only pattern scan: leads, not proof of malice or safety.')
        for category, count in result['categories'].items():
            print(f'{category}: {count} lead(s)')
        for lead in result['leads']:
            # JSON quoting preserves unusual filenames and escapes terminal control characters.
            print(json.dumps(lead, ensure_ascii=True))
        for skipped in result['skipped']:
            print('NOT SCANNED: ' + json.dumps(skipped, ensure_ascii=True))
        print(f"Text files scanned: {len(result['files_read'])}; gaps: {len(result['skipped'])}. Zero leads is not a pass.")
    return 0 if result['complete'] else 3


if __name__ == '__main__':
    sys.exit(main())
