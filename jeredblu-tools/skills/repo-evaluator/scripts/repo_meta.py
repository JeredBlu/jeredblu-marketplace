#!/usr/bin/env python3
"""
repo_meta.py — provenance & reputation dump for the repo-evaluator skill.

SAFETY CONTRACT: read-only lookups — GitHub API via `gh api`, HN Algolia, and registry
metadata (npm view / PyPI JSON / crates.io JSON). Never installs or runs anything.

Usage: repo_meta.py <github-url | owner/repo> [checkout_dir]
  checkout_dir (optional) enables the registry cross-check: does the published
  package actually point back to THIS repo?
"""
import datetime as dt, json, os, re, subprocess, sys, time, urllib.parse, urllib.request

try:
    import tomllib
except ImportError:
    tomllib = None


def gh(path, *extra):
    try:
        out = subprocess.run(["gh", "api", *extra, path], capture_output=True, text=True, timeout=60)
        return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None
    except Exception:
        return None


def http_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "repo-evaluator"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except Exception:
        return None


def days_since(iso):
    return (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))).days


def sec(t):
    print(f"\n### {t}")


def parse_spec(s):
    s = re.sub(r"^(https?://)?(www\.)?github\.com/", "", s.strip()).rstrip("/")
    s = re.sub(r"\.git$", "", s)
    parts = s.split("/")
    if len(parts) < 2:
        sys.exit(f"could not parse owner/repo from: {s}")
    return parts[0], parts[1]


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: repo_meta.py <github-url | owner/repo> [checkout_dir]")
    owner, name = parse_spec(sys.argv[1])
    R = f"{owner}/{name}"
    DIR = sys.argv[2] if len(sys.argv) > 2 else None
    if subprocess.run(["gh", "auth", "status"], capture_output=True).returncode != 0:
        print("WARN: gh not authenticated — low rate limits, some sections may be empty")
    print("== repo-evaluator :: provenance & reputation ==")

    sec("Repository")
    m = gh(f"repos/{R}")
    if not m:
        sys.exit(f"  repo not found / inaccessible: {R}")
    age = days_since(m["created_at"])
    print(f"  requested: {R}   resolved: {m['full_name']}")
    if m["full_name"].lower() != R.lower():
        print("  !! NAME MISMATCH — repo was renamed or TRANSFERRED to a new owner; find out when and why")
    print(f"  fork: {m['fork']}   parent: {(m.get('parent') or {}).get('full_name', '-')}")
    print(f"  created: {m['created_at'][:10]} ({age} days ago)   last push: {m['pushed_at'][:10]}")
    stars = m["stargazers_count"]
    print(f"  stars: {stars}  forks: {m['forks_count']}  watchers: {m.get('subscribers_count')}  open issues+PRs: {m['open_issues_count']}")
    print(f"  stars/day of life: {stars / max(age, 1):.1f}   forks per 100 stars: {100 * m['forks_count'] / max(stars, 1):.1f}"
          "   (apps ~2-5, libraries higher; <1 with huge stars = suspicious)")
    print(f"  license: {(m.get('license') or {}).get('spdx_id', 'NONE')}   archived: {m['archived']}   default branch: {m['default_branch']}")
    print(f"  homepage: {m.get('homepage') or '-'}   topics: {', '.join(m.get('topics', []))}")

    sec("Owner")
    u = gh(f"users/{m['owner']['login']}") or {}
    print(f"  {u.get('login')} ({u.get('type')})   name: {u.get('name') or '-'}   company: {u.get('company') or '-'}")
    if u.get("created_at"):
        print(f"  account created: {u['created_at'][:10]} ({days_since(u['created_at'])} days)   followers: {u.get('followers')}   public repos: {u.get('public_repos')}")
    print(f"  blog: {u.get('blog') or '-'}   bio: {(u.get('bio') or '-')[:140]}")
    repos = gh(f"users/{m['owner']['login']}/repos?per_page=100&sort=pushed") or []
    print("  top repos:")
    for r in sorted(repos, key=lambda r: -r["stargazers_count"])[:5]:
        print(f"    {r['stargazers_count']}★  {r['full_name']}{' (fork)' if r['fork'] else ''}")

    sec("Languages")
    langs = gh(f"repos/{R}/languages") or {}
    print("  " + ", ".join(sorted(langs, key=lambda k: -langs[k])))

    sec("Contributors (bus factor / concentration)")
    c = gh(f"repos/{R}/contributors?per_page=100") or []
    tot = sum(x["contributions"] for x in c) or 1
    print(f"  {len(c)}{'+' if len(c) == 100 else ''} contributors")
    for x in c[:6]:
        print(f"    {x['login']:<26} {x['contributions']:>6}  ({100 * x['contributions'] / tot:.0f}%)")

    sec("Releases (who uploads binaries? bot/CI = built in public; a human = built on a private machine)")
    rs = gh(f"repos/{R}/releases?per_page=5") or []
    if not rs:
        print("  no GitHub releases")
    for r in rs:
        print(f"  {r['tag_name']}  {(r.get('published_at') or '')[:10]}  author: {r['author']['login']}{'  (prerelease)' if r['prerelease'] else ''}")
        for a in r["assets"][:8]:
            print(f"      {a['name']}  {a['size'] // 1024} KB  uploader: {(a.get('uploader') or {}).get('login', '?')}  downloads: {a['download_count']}")
        names = " ".join(a["name"].lower() for a in r["assets"])
        flags = [k for k in ("sha256", "checksums", ".sig", ".asc", ".intoto", ".sbom", "attestation", ".pem") if k in names]
        print(f"      integrity files: {', '.join(flags) if flags else 'NONE'}")

    sec("CI workflows")
    wf = gh(f"repos/{R}/actions/workflows") or {}
    for w in wf.get("workflows", []):
        print(f"  {w['path']}  [{w['state']}]")
    if not wf.get("workflows"):
        print("  none / inaccessible")

    sec("Security posture")
    adv = gh(f"repos/{R}/security-advisories")
    print(f"  published repo security advisories: {len(adv) if isinstance(adv, list) else '?'}")
    for a in (adv or [])[:5]:
        print(f"    {a['ghsa_id']} {a.get('severity')} {(a.get('published_at') or '')[:10]} {a.get('summary', '')[:90]}")
    for p in ("SECURITY.md", ".github/SECURITY.md", "docs/SECURITY.md"):
        if gh(f"repos/{R}/contents/{p}"):
            print(f"  security policy: {p}")
            break
    else:
        print("  security policy: none")

    sec("Issue/PR search for trust keywords (counts are noisy — READ the titles)")
    for kw in ["malware", "virus", "trojan", "backdoor", "spyware", "telemetry", '"phones home"',
               "privacy", "miner", "vulnerability", "compromised", "antivirus", "EDR"]:
        q = urllib.parse.quote(f"repo:{R} {kw}")
        res = gh(f"search/issues?q={q}&per_page=3") or {}
        n = res.get("total_count", "?")
        print(f"  {kw:<14} {n}")
        for it in res.get("items", [])[:3]:
            print(f"      [{it['state']}] {it['created_at'][:10]} {it['title'][:95]}  {it['html_url']}")
        time.sleep(2.1)  # search API: 30 req/min

    sec("Star timing")
    print("  GitHub no longer exposes stargazer lists/timestamps (404 as of 2026-09). If stars look")
    print("  inflated vs forks/issues/contributors, check the curve at https://star-history.com/#" + R)

    sec("Look-alikes (is this the ORIGINAL? copycat forks with near-identical names are a common trap)")
    q = urllib.parse.quote(f"{name} in:name")
    for it in (gh(f"search/repositories?q={q}&sort=stars&per_page=8") or {}).get("items", []):
        tag = "  <== THIS" if it["full_name"].lower() == R.lower() else ""
        print(f"  {it['stargazers_count']}★  {it['full_name']}{' (fork)' if it['fork'] else ''}  created {it['created_at'][:10]}{tag}")

    sec("Hacker News stories linking to this repo")
    hn = http_json("https://hn.algolia.com/api/v1/search?tags=story&restrictSearchableAttributes=url&query="
                   + urllib.parse.quote(f"github.com/{R}")) or {}
    hits = sorted(hn.get("hits", []), key=lambda x: -(x.get("points") or 0))[:6]
    if not hits:
        print("  none")
    for x in hits:
        print(f"  {x.get('points')}pts {x.get('num_comments')}c {x['created_at'][:10]}  {x.get('title', '')[:80]}  https://news.ycombinator.com/item?id={x['objectID']}")

    if DIR and os.path.isdir(DIR):
        sec("Package-registry cross-check (does the published package point back to THIS repo?)")
        found = False
        pj = os.path.join(DIR, "package.json")
        if os.path.isfile(pj):
            try:
                pkg = json.load(open(pj)).get("name")
            except Exception:
                pkg = None
            if pkg:
                found = True
                out = subprocess.run(["npm", "view", pkg, "repository.url", "dist-tags.latest", "maintainers", "--json"],
                                     capture_output=True, text=True, timeout=60)
                print(f"  npm {pkg}: {out.stdout.strip()[:400] or 'not on npm'}")
        if tomllib:
            for fn, key, url in (("pyproject.toml", "project", "https://pypi.org/pypi/{}/json"),
                                 ("Cargo.toml", "package", "https://crates.io/api/v1/crates/{}")):
                p = os.path.join(DIR, fn)
                if not os.path.isfile(p):
                    continue
                try:
                    n = tomllib.load(open(p, "rb")).get(key, {}).get("name")
                except Exception:
                    n = None
                if not n:
                    continue
                found = True
                d = http_json(url.format(n))
                if not d:
                    print(f"  {fn} {n}: not published")
                elif "info" in d:
                    print(f"  PyPI {n}: latest {d['info']['version']}  urls: {json.dumps(d['info'].get('project_urls'))[:300]}")
                elif "crate" in d:
                    print(f"  crates.io {n}: latest {d['crate']['max_version']}  repo: {d['crate'].get('repository')}")
        if not found:
            print("  no npm/PyPI/crates manifest — check Homebrew tap / app store / install docs manually")

    print("\n== end provenance ==")
    print("Soft signals (stars, followers) are gameable — weigh below code evidence. Next: web search")
    print(f'(Bright Data CLI/MCP, or built-in web search) for: "{name}" review | "{name}" malware | "{name}" reddit | "{owner}"')


if __name__ == "__main__":
    main()
