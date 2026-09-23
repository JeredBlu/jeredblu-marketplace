#!/usr/bin/env python3
"""
deps.py — dependency / supply-chain sweep for the repo-evaluator skill.

SAFETY CONTRACT: parses manifest & lockfiles as TEXT/JSON/TOML only. Never runs a
package manager (npm/pip/cargo/swift install or resolve all execute code). The only
network call is an optional query of package names+versions to the public OSV.dev
vulnerability database (use --offline to skip).

Usage: deps.py <checkout_dir> [--offline]

Reports: manifests found, dependency counts, deps pulled from git/URL/tarball (bypass
the registry), npm packages that run install scripts, and known vulnerabilities (OSV).
If `osv-scanner` is installed, prefer it (it is also read-only) and treat this as backup.
"""
import json, os, re, sys, urllib.request

try:
    import tomllib
except ImportError:  # py<3.11
    tomllib = None

SKIP = {".git", "node_modules", "vendor", "third_party", "Pods", ".build", "target", "dist"}
MANIFESTS = {"package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "requirements.txt",
             "pyproject.toml", "poetry.lock", "uv.lock", "Pipfile.lock", "setup.py", "Cargo.toml",
             "Cargo.lock", "go.mod", "go.sum", "Package.swift", "Package.resolved", "Gemfile",
             "Gemfile.lock", "Podfile", "Podfile.lock", "composer.json", "composer.lock",
             "build.gradle", "build.gradle.kts", "pom.xml"}


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            if f in MANIFESTS or f.startswith("requirements") and f.endswith(".txt"):
                yield os.path.join(d, f)


def load_toml(p):
    if not tomllib:
        return {}
    try:
        with open(p, "rb") as fh:
            return tomllib.load(fh)
    except Exception:
        return {}


pinned, odd_sources, install_scripts, notes = [], [], [], []


def rel(p):
    return os.path.relpath(p, ROOT)


def parse(p):
    f = os.path.basename(p)
    try:
        txt = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return
    if f == "package.json":
        try:
            j = json.loads(txt)
        except Exception:
            return
        for sec in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
            for n, v in (j.get(sec) or {}).items():
                if re.match(r"^(git|github:|http|https|file:|link:)|/", str(v)) and not str(v).startswith("npm:"):
                    odd_sources.append(f"{rel(p)}: {n} -> {v}")
        scr = j.get("scripts") or {}
        for k in ("preinstall", "install", "postinstall", "prepare", "prepublish"):
            if k in scr:
                install_scripts.append(f"{rel(p)}: THIS package's own '{k}': {scr[k][:120]}")
    elif f == "package-lock.json":
        try:
            j = json.loads(txt)
        except Exception:
            return
        for path, meta in (j.get("packages") or {}).items():
            if not path:
                continue
            name = meta.get("name") or path.split("node_modules/")[-1]
            if meta.get("version"):
                pinned.append(("npm", name, meta["version"]))
            if meta.get("hasInstallScript"):
                install_scripts.append(f"{rel(p)}: dependency '{name}@{meta.get('version')}' runs an install script")
            res = meta.get("resolved", "")
            if res and "registry.npmjs.org" not in res:
                odd_sources.append(f"{rel(p)}: {name} resolved from {res[:100]}")
    elif f.startswith("requirements") and f.endswith(".txt"):
        for line in txt.splitlines():
            line = line.split("#")[0].strip()
            m = re.match(r"^([A-Za-z0-9_.\-\[\]]+)==([A-Za-z0-9_.\-+!]+)", line)
            if m:
                pinned.append(("PyPI", re.sub(r"\[.*\]", "", m.group(1)), m.group(2)))
            elif re.search(r"(git\+|https?://|\.whl|\.tar\.gz|--index-url|--extra-index-url)", line):
                odd_sources.append(f"{rel(p)}: {line[:120]}")
    elif f in ("poetry.lock", "uv.lock", "Cargo.lock"):
        d = load_toml(p)
        eco = "crates.io" if f == "Cargo.lock" else "PyPI"
        for pk in d.get("package", []):
            if pk.get("name") and pk.get("version"):
                pinned.append((eco, pk["name"], pk["version"]))
            src = pk.get("source")
            src = src if isinstance(src, str) else json.dumps(src) if src else ""
            if src and not any(s in src for s in ("crates.io", "pypi.org", "editable", "virtual", '"."')):
                odd_sources.append(f"{rel(p)}: {pk.get('name')} from {src[:100]}")
    elif f == "go.sum":
        seen = set()
        for line in txt.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                v = parts[1].split("/go.mod")[0]
                if (parts[0], v) not in seen:
                    seen.add((parts[0], v))
                    pinned.append(("Go", parts[0], v))
    elif f == "Package.resolved":
        try:
            j = json.loads(txt)
        except Exception:
            return
        pins = j.get("pins") or (j.get("object") or {}).get("pins") or []
        for pn in pins:
            loc = pn.get("location") or pn.get("repositoryURL") or ""
            st = pn.get("state") or {}
            ver = st.get("version")
            if loc and ver:
                pinned.append(("SwiftURL", loc if loc.endswith(".git") else loc, ver))
            elif loc:
                odd_sources.append(f"{rel(p)}: {loc} pinned to branch/revision only ({st.get('branch') or st.get('revision','')[:10]})")
    elif f == "Pipfile.lock":
        try:
            j = json.loads(txt)
        except Exception:
            return
        for sec in ("default", "develop"):
            for n, meta in (j.get(sec) or {}).items():
                v = (meta.get("version") or "").lstrip("=")
                if v:
                    pinned.append(("PyPI", n, v))


def osv(pkgs):
    out = []
    for i in range(0, len(pkgs), 500):
        chunk = pkgs[i:i + 500]
        body = json.dumps({"queries": [
            {"package": {"ecosystem": e, "name": n}, "version": v} for e, n, v in chunk]}).encode()
        req = urllib.request.Request("https://api.osv.dev/v1/querybatch", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.load(r).get("results", [])
        for (e, n, v), rr in zip(chunk, res):
            ids = [x["id"] for x in (rr.get("vulns") or [])]
            if ids:
                out.append(f"{e}:{n}@{v}  {', '.join(ids[:6])}{' …' if len(ids) > 6 else ''}")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
        print("usage: deps.py <checkout_dir> [--offline]", file=sys.stderr)
        sys.exit(2)
    ROOT = os.path.abspath(sys.argv[1])
    offline = "--offline" in sys.argv
    files = sorted(walk(ROOT))
    print("== repo-evaluator :: dependency / supply-chain sweep ==")
    print("### Manifests & lockfiles")
    print("\n".join(f"  {rel(p)}" for p in files) or "  none")
    has_lock = any(os.path.basename(p).endswith(("lock", ".lock", "-lock.json", ".resolved", ".sum")) for p in files)
    if files and not has_lock:
        notes.append("NO LOCKFILE: dependency versions float — what you install may differ from what was reviewed")
    for p in files:
        parse(p)
    uniq = sorted(set(pinned))
    by_eco = {}
    for e, _, _ in uniq:
        by_eco[e] = by_eco.get(e, 0) + 1
    print("\n### Pinned dependencies (from lockfiles)")
    print("  " + (", ".join(f"{e}: {c}" for e, c in by_eco.items()) or "none parsed"))
    print("\n### Deps from git / URL / tarball / non-default registry (bypass normal registry checks)")
    print("\n".join(f"  {x}" for x in odd_sources[:40]) or "  none")
    print("\n### Install scripts (code that runs automatically during `npm install`)")
    print("\n".join(f"  {x}" for x in install_scripts[:40]) or "  none")
    print("\n### Known vulnerabilities (OSV.dev)")
    if offline:
        print("  skipped (--offline)")
    elif not uniq:
        print("  nothing to query")
    else:
        try:
            v = osv(uniq)
            print("\n".join(f"  {x}" for x in v[:60]) or f"  none found across {len(uniq)} pinned packages")
        except Exception as ex:
            print(f"  OSV query failed: {ex}")
    if notes:
        print("\n### Notes")
        print("\n".join(f"  {n}" for n in notes))
    print("\nTyposquat check is a judgment call: eyeball dep names for near-misses of popular packages.")
