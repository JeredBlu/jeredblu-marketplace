# Changelog — jeredblu-tools

## 1.5.0 (2026-09-23)

- **prd-creator: deeper, more conversational discovery.** Validated with a new
  conversation eval (simulated users who only reveal key details when asked
  the right question; blind-graded against the previous version — won on both).
  - Back to **one question per message** (as in the original Claude project
    prompt), with explicit rules for when to keep asking and when to stop —
    typical interviews now run 12–22 questions instead of stopping early.
  - **Big decisions are made with you, not silently:** platform, where data
    lives, sign-in, and **build vs. buy** (starting with tools you already pay
    for) are each presented as options with trade-offs and a recommendation.
  - Budget reality checks (free-tier limits, app-store fees), deadline and
    "who's building it" are now core discovery areas.
  - New **Assumptions & Open Questions** section: guesses are never presented
    as requirements. PRDs are right-sized instead of padded.
  - Works in any harness (Claude Code, Codex, chat apps) — no separate ports needed.

## 1.4.0 (2026-09-23)

- **New skill: repo-evaluator** — pre-install safety check for any open-source
  project on GitHub (apps, CLIs, libraries, scripts, dotfiles). Never installs
  or runs the target: clones it inertly, then scans for install-time hooks,
  persistence, sudo/privilege use, phone-home and telemetry (incl. whether it's
  on by default), credential access, keylogging/screen capture, self-promo
  (affiliate links, auto-starring your GitHub), obfuscation, committed binaries,
  dependency vulns (OSV.dev), release-binary vs source mismatch, and maintainer
  reputation. Delivers a plain-English verdict: what it is, what installing it
  does to your computer, who it talks to, and whether to install.
- Bundled read-only scripts: `fetch.sh`, `scan.sh`, `deps.py`, `repo_meta.py`,
  `inspect_artifact.sh` (inspects release .zip/.dmg/.pkg without running them).
- Requires the GitHub CLI (`gh`) logged in. Web search: Bright Data CLI or MCP
  recommended; falls back to built-in search.

## 1.3.0 (2026-07-18)

- agent-skill-evaluator v1.3.0: bundled precision scanner + exhaustive coverage.

## 1.2.0 (2026-07-17)

- **frugal-fable: cross-CLI Codex delegation ("the second pool").** If OpenAI's
  Codex CLI is installed, the skill can — with your explicit consent, asked
  in-session — offload delegable slices to Codex models (GPT-5.6 Sol/Terra/Luna),
  which run on a separate subscription quota and consume no Claude usage.
- New `references/codex-delegation.md`: tier mapping, exact synchronous
  `codex exec` recipes (build slices, adversarial review, repo/PR review,
  same-session amendments), sandbox rules, and live-verified gotchas
  (resume reverts to config defaults; stdin handling; notify-hook silencing).
- Consent gate: never routes to Codex without asking; silent when Codex is
  absent; running unsupervised it proceeds on Claude models and surfaces the
  offer afterward.
- All model IDs live in one mapping table — future model churn is a
  one-table edit.

## 1.1.0 (2026-06-14)

- Added **frugal-fable**: premium-model orchestration + cheap-model delegation
  (research / build / testing / debugging lanes), file-based context firewall,
  bundled budget-capped `frugal-research.js` workflow. Bright Data primary for
  research collection.

## 1.0.0

- Initial release: prd-creator, agent-skill-evaluator, mcp-evaluator.
