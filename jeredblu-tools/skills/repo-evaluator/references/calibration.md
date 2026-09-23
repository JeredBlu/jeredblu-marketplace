# Calibration

## Worked example — nikitabobko/AeroSpace (2026-09-23) → LIKELY SAFE

macOS tiling window manager, Swift, MIT, ~23k★, 3+ yrs, one dominant maintainer (94% of commits, ex-JetBrains, 10-yr-old account).

| Lead | Resolution |
|---|---|
| Cask `postflight` strips quarantine | Legit-but-trust-relevant: app is deliberately unnotarized (README says so) → Gatekeeper check skipped. Medium. |
| `SMAppService.mainApp` (persistence) | Opt-in `start-at-login` config key. Benign. |
| `tccutil reset Accessibility <own id>` | Resets only its own permission (recovery after re-sign). Benign. |
| `sudo xcode-select` | CI script under `.github/`. Not shipped. Dismissed. |
| `addGlobalMonitorForEvents` | Mouse-moved / mouse-up only (focus-follows-mouse). No keyboard tap. Benign. |
| `NSWorkspace.open(github.com/sponsors/…)` | "Sponsor" menu item user clicks. Low. |
| `exec-and-forget` → `/bin/bash` | Runs commands from the user's own config. By design. |
| Unix socket in `/tmp` | Any same-user process can send commands (incl. exec) — but such a process already has user rights. Low. |
| Releases uploaded by maintainer, no checksums; CI only builds ad-hoc-signed test builds | Binary not provably == source. Medium → safer path: build from source at tag. |
| Network | None outbound — only local Unix socket. |
| Deps | 4 SwiftPM deps, all well-known, 0 OSV vulns. |
| Reputation | 0 advisories; 524-pt HN thread; positive blog reviews; complaints are bugs (Tahoe), not safety. |

Verdict shape: **LIKELY SAFE** — needs Accessibility (inherent), unnotarized + quarantine stripped, binary built off-CI. Safer path: build from source at the release tag.

## Real incidents to pattern-match against

| Incident | Pattern | What would have caught it |
|---|---|---|
| **xz-utils (2024)** | Long-game maintainer takeover; backdoor injected only in release **tarballs** via build scripts, not in git source | Release artifact ≠ source diff; build-time code (m4/configure) read in full; new maintainer touching release tooling |
| **event-stream (2018)** | New maintainer given publish rights added a dependency (`flatmap-stream`) with an encrypted payload targeting a crypto wallet | Ownership change + new dep added right after; obfuscated/minified code in dep |
| **ua-parser-js / coa / rc (2021)** | Maintainer npm accounts hijacked; malicious versions with `preinstall` downloading a miner/stealer | Install-script category; lockfile pinning; version not tagged in repo |
| **Shai-Hulud npm worm (2025)** | `postinstall` stole npm/GitHub tokens and republished itself into the victim's other packages | Install scripts in deps (`hasInstallScript`); credential-file reads; `gh auth token` |
| **tj-actions/changed-files (2025)** | Compromised GitHub Action dumped CI secrets to logs | Workflows pinned by tag not SHA; matters for anyone *using* the action |
| **Fake-star / "ghost" repo networks (2024–25)** | Clones of popular tools with bought stars; malware in release zips or README "download" links | Look-alike check; stars vs forks/issues/contributors; release uploader; README links to other owners/domains |
| **Typosquats (ongoing, npm/PyPI)** | Name one letter off a popular package; install hook steals env vars | Registry cross-check (repo URL mismatch); eyeball dep names |

## Verdict calibration

- **SAFE (85+)**: reviewed code does what it says, no network or only disclosed/opt-in network, builds in public CI or you build from source, reputable maintainer.
- **LIKELY SAFE (70–84)**: legit project with trust-relevant caveats (big permissions justified by purpose, unnotarized, off-CI releases, default-on but disclosed telemetry).
- **USE WITH CAUTION (50–69)**: undisclosed telemetry, persistence without opt-in, sudo installers, unpinned/git deps, thin reputation.
- **NOT RECOMMENDED (30–49)**: behavior outside stated purpose, self-promo abuse (auto-star, affiliate injection), obfuscation without explanation, suspicious provenance.
- **DO NOT USE (<30)**: any Critical floor hit.
