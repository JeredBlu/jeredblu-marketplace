#!/usr/bin/env python3
"""Read-only lead inventory. Exit 0 complete within limits, 3 incomplete, 2 invalid.

--json retains EVERY match. Text previews declare truncation. Target code is never
imported, built, installed or executed; symlinks and opaque files are not followed.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

PATTERNS = Path(__file__).resolve().parent.parent / "references" / "scan-patterns.json"
DOCS = {".md", ".markdown", ".rst", ".adoc", ".txt", ".svg", ".lock"}
LOCKS = {"package-lock.json", "Package.resolved", "go.sum"}
BUILDS = {"build.rs", "setup.py", "setup.cfg", "pyproject.toml", "package.json", "binding.gyp",
          "Makefile", "makefile", "GNUmakefile", "CMakeLists.txt", "Package.swift", "Podfile",
          "Dockerfile", "Brewfile", ".envrc", "mise.toml", ".tool-versions", "tasks.json",
          "devcontainer.json", ".pre-commit-config.yaml", "go.mod", "Cargo.toml", "configure", "configure.ac"}
AGENTS = {"agents.md", "claude.md", "gemini.md", "copilot-instructions.md", ".mcp.json", "mcp.json",
          ".cursorrules", ".windsurfrules"}
DOMAIN = re.compile(r"https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,})", re.I)
UNICODE = re.compile("[\u202a-\u202e\u2066-\u2069\u200b]")
MAGICS = (b"MZ", b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce",
          b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe", b"\x00asm", b"PK\x03\x04", b"xar!", b"!<arch>")


def inspect(root, max_bytes=2 * 1024 * 1024, max_files=50000):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("target must be a directory")
    categories = json.loads(PATTERNS.read_text())
    compiled = [(c, re.compile(c["pattern"], re.I)) for c in categories]
    result = {"target": str(root), "status": "complete", "files_read": 0, "errors": [], "skipped": [],
              "categories": [{"id": c["id"], "title": c["title"], "scope": c["scope"], "matches": []} for c in categories],
              "build_files": [], "agent_files": [], "binary_files": [], "unicode_leads": [],
              "minified_files": [], "domains": {}, "history": [],
              "limits": {"max_file_bytes": max_bytes, "max_files": max_files, "excluded_directories": [".git", "node_modules"]}}
    domains = Counter()
    visited = 0
    def failure(exc):
        result["errors"].append(str(exc))
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=failure):
        kept = []
        for name in sorted(dirs):
            path = Path(directory) / name
            rel = str(path.relative_to(root))
            if path.is_symlink():
                result["skipped"].append({"path": rel, "reason": "symlink directory not followed"})
            elif name in {".git", "node_modules"}:
                if name != ".git":
                    result["skipped"].append({"path": rel, "reason": "dependency directory excluded; not reviewed"})
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(files):
            visited += 1
            if visited > max_files:
                failure("file-count limit reached; remaining files not scanned")
                break
            path = Path(directory) / name
            rel = str(path.relative_to(root))
            if name in BUILDS or name.startswith(("install", "build.gradle")) or name.endswith((".podspec", ".m4")) or rel.startswith(".github/workflows/") or (name.endswith(".rb") and any(x in path.parts for x in ("Formula", "Casks"))):
                result["build_files"].append(rel)
            if name.lower() in AGENTS or any(x in path.parts for x in (".claude", ".codex", ".cursor", ".agents")) or rel.startswith(".github/instructions/"):
                result["agent_files"].append(rel)
            try:
                if not stat.S_ISREG(path.lstat().st_mode):
                    result["skipped"].append({"path": rel, "reason": "symlink or non-regular file not opened"})
                    continue
                fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
                with os.fdopen(fd, "rb") as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise ValueError("file changed to a non-regular file")
                    data = stream.read(max_bytes + 1)
                if len(data) > max_bytes:
                    result["skipped"].append({"path": rel, "reason": "file-size limit exceeded"})
                    continue
                if data.startswith(MAGICS) or b"\x00" in data[:8192]:
                    result["binary_files"].append(rel)
                    result["skipped"].append({"path": rel, "reason": "binary/opaque content needs artifact review"})
                    continue
                text = data.decode("utf-8")
            except (OSError, ValueError, UnicodeError) as exc:
                failure(f"{rel}: {exc}")
                continue
            result["files_read"] += 1
            is_doc = path.suffix.lower() in DOCS or name in LOCKS or name.startswith(("LICENSE", "CHANGELOG"))
            for number, line in enumerate(text.splitlines(), 1):
                for (category, pattern), output in zip(compiled, result["categories"]):
                    if category["scope"] == "code" and is_doc:
                        continue
                    if pattern.search(line):
                        output["matches"].append({"file": rel, "line": number, "text": line})
                if UNICODE.search(line) and not is_doc:
                    result["unicode_leads"].append({"file": rel, "line": number})
                if len(line) > 1500 and path.suffix.lower() in {".js", ".mjs", ".cjs", ".ts", ".py", ".sh", ".rb", ".php", ".ps1"}:
                    result["minified_files"].append({"file": rel, "line": number, "length": len(line)})
                if not is_doc:
                    domains.update(host.lower() for host in DOMAIN.findall(line))
        if visited > max_files:
            break
    result["domains"] = dict(sorted(domains.items()))
    if (root / ".git").exists():
        try:
            proc = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", str(root),
                                   "log", "--no-show-signature", "--since=12 months ago", "--format=%h %ad %an %s", "--date=short", "-n", "30", "--",
                                   "*.sh", "package.json", "build.rs", ".github/workflows/*", "*install*", "*release*", "*update*"],
                                  capture_output=True, text=True, timeout=30)
            if proc.returncode:
                failure("git history lookup failed: " + proc.stderr.strip())
            else:
                result["history"] = proc.stdout.splitlines()
        except (OSError, subprocess.SubprocessError) as exc:
            failure("git history unavailable: " + str(exc))
    result["status"] = "incomplete" if result["errors"] or result["skipped"] else "complete"
    return result


def render(result):
    print("== repo-evaluator :: static lead scan ==")
    print(f"STATUS: {result['status'].upper()}; text files read: {result['files_read']}")
    print("Patterns are leads, not verdicts. No matches is not proof of safety. Use --json for the full ledger.")
    for c in result["categories"]:
        print(f"\n### {c['title']} [{c['scope']}]")
        for hit in c["matches"][:40]:
            print(f"  {hit['file']}:{hit['line']}: {hit['text'][:180]}")
        if not c["matches"]:
            print("  no matches in successfully scanned files" if result["status"] == "incomplete" else "  scanned, no matches")
        if len(c["matches"]) > 40:
            print(f"  TRUNCATED preview: {len(c['matches'])} matches; --json retains all")
    for key in ("build_files", "agent_files", "binary_files", "unicode_leads", "minified_files", "domains", "history", "skipped", "errors"):
        print("\n### " + key)
        print(json.dumps(result[key], indent=2, ensure_ascii=True))
    print("\nHistory is limited to fetched depth / 30 sensitive-path commits. Domains are literal HTTP(S) hosts, not all possible network behavior.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = inspect(args.target)
    except (OSError, ValueError) as exc:
        print("Scan failed: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2)) if args.json else render(result)
    return 3 if result["status"] == "incomplete" else 0


if __name__ == "__main__":
    sys.exit(main())
