# Changelog

## 1.2.0 — 2026-10-12
- Rubric 1.1.0 gives a numeric reviewed-evidence score normalized over assessed checks, with separate coverage, unknowns and scope. Severity caps still apply; no-evidence reviews do not invent a score.
- Partial reviews use REVIEWED WITH LIMITATIONS or an adverse verdict, not an automatic overall INCOMPLETE label.
- Package inspection is explicitly optional; respect a prior decline without asking again or blocking the source-review result.
- Preserve original rubric-1.0.0 ledgers/results when recalculating under the new policy.

## 1.1.0 — 2026-10-12
- Versioned 22-check, 100-point evidence rubric with deterministic calculation, per-check/per-dimension output, explicit unknowns and severity caps. No unqualified SAFE label or extra API key.
- Full JSON lead inventory; explicit skipped/failed checks; agent-instruction review and prompt-injection leads.
- Dependency coverage now distinguishes unsupported formats, parse failures, offline checks and failed OSV responses.
- ZIP/TAR extraction validates all entries first and rejects traversal, links, path aliases and size/count limits.
- Metadata lookup failures are explicit; release uploader is no longer treated as proof of build origin. Public fetch ignores global Git filters/templates.
- Offline inert-fixture regression suite; see references/scoring.md for scope and limitations.


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
