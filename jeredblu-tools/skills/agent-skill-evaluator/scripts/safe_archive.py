#!/usr/bin/env python3
"""Conservative ZIP/TAR inspection extraction. No extractall, links or execution.

Validates the entire member list BEFORE writing any payload. Refuses links, special
files, ambiguous paths, duplicates and oversized archives. Rejection is not proof
of malice (e.g. legitimate app frameworks use symlinks); report inspection blocked.
"""
import argparse
from contextlib import closing
from pathlib import Path
import re
import shutil
import stat
import sys
import tarfile
import unicodedata
import zipfile


def normalized(name):
    if not isinstance(name, str) or len(name) > 4096 or "\\" in name or ":" in name or any(ord(c) < 32 for c in name):
        raise ValueError("ambiguous/control-character archive path")
    if name.startswith("/"):
        raise ValueError("absolute archive path")
    parts = [part for part in name.split("/") if part not in ("", ".")]
    if not parts or ".." in parts or any(p.endswith((".", " ")) for p in parts):
        raise ValueError("unsafe or traversal archive path: " + repr(name))
    if any(re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p) for p in parts):
        raise ValueError("reserved device archive path")
    return Path(*parts)


def unpack(source, destination, max_files=10000, max_total=512 * 1024 * 1024, max_file=128 * 1024 * 1024):
    source, destination = Path(source), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination must not exist")
    if source.is_symlink() or not source.is_file():
        raise ValueError("archive must be a regular non-symlink file")
    is_zip = zipfile.is_zipfile(source)
    archive = zipfile.ZipFile(source) if is_zip else tarfile.open(source, mode="r:*")
    with closing(archive):
        plan, seen, total = [], {}, 0
        members = archive.infolist() if is_zip else archive
        for index, member in enumerate(members):
            if index >= max_files:
                raise ValueError("archive member-count limit exceeded")
            if is_zip:
                name, size, directory = member.filename, member.file_size, member.is_dir()
                kind = stat.S_IFMT(member.external_attr >> 16)
                if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or member.flag_bits & 1:
                    raise ValueError("archive link/special/encrypted entry refused: " + repr(name))
                if size > max(1, member.compress_size) * 1000:
                    raise ValueError("archive expansion-ratio limit exceeded")
            else:
                name, size, directory = member.name, member.size, member.isdir()
                if not (member.isfile() or directory):
                    raise ValueError("archive link/special entry refused: " + repr(name))
            # A tar root directory contributes no output; all child paths are checked.
            if directory and name in (".", "./"):
                continue
            path = normalized(name)
            key = unicodedata.normalize("NFC", path.as_posix()).casefold()
            if key in seen:
                raise ValueError("duplicate/ambiguous archive path: " + repr(name))
            if any(parent in seen and not seen[parent] for parent in _parents(key)):
                raise ValueError("file used as archive directory")
            if not directory and any(other.startswith(key + "/") for other in seen):
                raise ValueError("directory replaced by archive file")
            if size < 0 or size > max_file:
                raise ValueError("archive member-size limit exceeded")
            total += size
            if total > max_total:
                raise ValueError("archive total-size limit exceeded")
            seen[key] = directory
            plan.append((member, path, directory, size))
        # The destination is fresh, all links are forbidden, and no target code runs.
        destination.mkdir(mode=0o700)
        try:
            for member, path, directory, size in plan:
                target = destination / path
                if directory:
                    target.mkdir(parents=True, exist_ok=True, mode=0o700)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                stream = archive.open(member) if is_zip else archive.extractfile(member)
                with stream, target.open("xb") as output:
                    remaining = size
                    while remaining:
                        chunk = stream.read(min(65536, remaining))
                        if not chunk:
                            raise ValueError("truncated archive member")
                        output.write(chunk)
                        remaining -= len(chunk)
                    if stream.read(1):
                        raise ValueError("archive member exceeds declared size")
                target.chmod(0o600)
        except Exception:
            shutil.rmtree(destination)
            raise
    return {"files": len(plan), "bytes": total}


def _parents(key):
    parts = key.split("/")
    return ["/".join(parts[:i]) for i in range(1, len(parts))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()
    try:
        result = unpack(args.source, args.destination)
        print(f"Validated/extracted {result['files']} entries, {result['bytes']} bytes. Nothing executed.")
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile, RuntimeError) as exc:
        print("ARTIFACT INSPECTION BLOCKED: " + str(exc), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
