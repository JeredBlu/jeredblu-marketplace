# Changelog

## 1.0.0 — 2026-09-23
- Initial release. Sibling of agent-skill-evaluator / mcp-evaluator for general open-source software.
- `fetch.sh`: non-executing clone (temp dir, no hooks/submodules/LFS, optional tag).
- `scan.sh`: 20 danger categories + domain inventory + build-time code list + recent sensitive-file authors. Pins `/usr/bin/grep`; bash 3.2 compatible.
- `deps.py`: lockfile parsing (npm, PyPI, crates, Go, SwiftPM), git/URL deps, install-script deps, OSV.dev vuln lookup.
- `repo_meta.py`: repo/owner provenance, contributor concentration, release uploader (CI vs human), advisories, trust-keyword issue search, look-alikes, HN, registry cross-check. Stargazer timing unavailable (GitHub API 404s since 2026).
- `inspect_artifact.sh`: release zip/tar/dmg/pkg inspection without execution; signature, notarization, entitlements, helpers, dylibs, binary-only hosts vs source.
- Calibrated on nikitabobko/AeroSpace + an inert synthetic malicious fixture (all 11 planted categories detected).
- Requirements & tool strategy section (matches mcp-evaluator / agent-skill-evaluator): `gh` logged in = required, with a preflight check; web search order is Bright Data CLI → Bright Data MCP → other search MCP → built-in; osv-scanner and macOS are optional.
- Test-run fixes (ripgrep, Homebrew, oh-my-zsh): output saved inside the per-run workdir (concurrent runs were mixing `/tmp` output); categories 4–5 exclude docs; category 8 catches hand-rolled analytics; new 8b telemetry off-switch finder; category 14 precision; Homebrew core/cask resolution, multi-repo installers, `curl | sh` URL check, modular-repo read strategy, impostor-site check, repo-archetype noise table; "four scans" → three.
