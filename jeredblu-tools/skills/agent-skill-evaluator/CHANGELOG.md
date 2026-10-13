# Changelog — agent-skill-evaluator

All notable changes to this skill. Versioning follows [SemVer](https://semver.org).

## [1.4.0] — 2026-10-13

- Replaced freehand dimension scores with 14 anchored evidence checks, deterministic arithmetic, explicit unknown coverage and severity caps. No safety probability or certification claim.
- Single-pass static scanner preserves every structured lead, reports skipped content and limits, and no longer silently hides files beyond the first 60. Uses Python standard library only.
- Conservative archive inspection/extraction rejects path traversal, links and ambiguous/oversized archives. Corrected the claim that a temporary directory alone prevents zip-slip.
- Default Markdown, one reusable local snapshot/evidence ledger, bounded external research and unique report workspace reduce avoidable work. Static-only and all trust-relevant top-risk disclosure remain.
- Corrected reference examples that wrongly equated a string-prefix check with containment or a working directory with a sandbox.
- Version moved to standard `metadata.version`; see tests/test_evaluator.py for offline behavior tests. Real skill judgment still requires evidence review; fixtures do not prove attack detection completeness.

## [1.3.0] — 2026-07-18

Robustness pass. On a real 275-file repo, a lower-effort run (Sonnet medium) skimmed,
**missed the forced promo footer at line 119 of a 271-line SKILL.md, and returned a false
`SAFE` / "no output-pollution" verdict** — while also silently skipping the reputation
check. Root cause: nothing forced the skill's own steps to actually run to completion
(Matt Pocock's "premature completion"). This release makes thoroughness a property of the
skill instead of the model/effort level.

### Added
- **`scripts/scan.sh` — bundled read-only danger scanner (§5.0).** Greps the extracted
  target across all eight danger categories and prints leads grouped by file. Tuned for
  **precision** (rare high-signal tokens like `skool.com`, `gh auth token`, `curl|sh`,
  `"command":"npx"`) so legitimate domain vocabulary — an SEO tool says "backlink" 400
  times — doesn't bury the real signal or train the reader to ignore the category.
  SAFETY: the scanner only ever *reads* (find + grep); it never executes, sources, or
  installs anything from the target. It is the mechanism that lets the evaluator avoid
  running a skill's own code. Validated: catches all 8 planted-issue fixtures, stays
  silent on the benign and SSRF fixtures (SSRF is a logic flaw, not a keyword — that is
  the full-read's job, and the skill says so).
- **Leading word "exhaustive"** threaded through Step 5 as the standard for coverage.

### Changed
- **Full-coverage read is now mandatory (§5.2).** Read every instruction/command file in
  full, not a sample; forced-output instructions hide mid-file and in per-command files.
- **Coverage line required in the verdict (Step 6).** "Read in full: SKILL.md + N command
  files + M scripts; provenance checked / NOT checked." A `SAFE`/clean verdict or the
  "no output-pollution" sentence is not permitted without it — a skim can no longer
  launder itself into a clean bill of health.
- **Provenance mandatory when a URL is given (§5.1).** If skipped, that becomes a prominent
  top-of-verdict limitation ("source reputation NOT checked"), not a quiet closing footnote.
- **Caps → reasoning pass (Step 6 + verdict rules).** Per Anthropic `skill-creator` and
  Pocock: all-caps NEVER/ALWAYS is a yellow flag. Softened emphasis-only caps into explained
  reasoning; kept hard imperatives only for the Step 3 security guardrails (never execute
  the target), each paired with its why.

### Notes
- Added a `scripts/` directory (first bundled executable) and a table of contents to
  `references/attack_patterns.md`.
- Considered but did NOT adopt from the Pocock material: user-invoked/`disable-model-invocation`
  (the evaluator should stay model-invoked so it fires on "is this safe"), and splitting the
  evaluator into multiple sequential skills (the checkable coverage criterion + bundled
  scanner achieve the same anti-premature-completion goal without fracturing the skill).

## [1.2.1] — 2026-07-17

### Fixed
- **Version banner reliability.** In testing, the self-reported banner was printed
  with the wrong number once and skipped entirely once — because the model stated it
  from memory. Moved the announcement to a mandatory **Step 0** (literal first action)
  that requires *reading the `version:` field from the frontmatter and echoing it
  verbatim*, and instructs the agent to say "could not read skill version" rather than
  guess. Note: LLM self-report can still slip; for a guaranteed check, read the file
  directly: `grep '^version:' ~/.claude/skills/agent-skill-evaluator/SKILL.md`.

## [1.2.0] — 2026-07-17

Tuning pass after a real-world run on a 275-file SEO plugin. The v1.1.0 verdict
was accurate but (a) treated GitHub stars as a trust signal and (b) used
unexplained security jargon (e.g. "SSRF") in the chat verdict a non-coder reads.

### Changed
- **§5.1 Provenance** — popularity metrics (stars, forks, downloads, follower
  counts, self-reported adoption) are still recorded and evaluated, but re-weighted
  as *weak, gameable evidence* rather than proof of safety: a high count isn't proof
  it's good, an absence isn't proof it's bad, and skepticism rises when the numbers
  don't add up (e.g. a brand-new repo with an outsized star count). The actual trust
  call leans on verifiable signals (commit history, real maintainer identity,
  independent reviews/CVEs, issue handling). Added an author-honesty cross-check: one
  inflated or misrepresented claim re-weights that author's other claims — including
  popularity and safety — downward.
- **Step 6 Top Risks — plain-language recipe.** Each risk now leads with plain-English
  *impact* (what it does to the user), not mechanism. Every security term must be
  glossed in ≤8 words in parentheses the moment it appears (SSRF, RCE, exfiltration,
  credential, etc.) or described instead of named. Each bullet capped at ~1–3 sentences;
  long technical detail moves to the Full Report. Technical precision preserved — the
  goal is clearer, not dumber.

### Added
- `test-fixtures/ssrf-fetcher/` — fixture whose script fetches a user-supplied URL
  server-side, to verify the evaluator glosses "SSRF" in plain words rather than
  dropping the bare acronym.

## [1.1.0] — 2026-07-17

Improvement pass: the evaluator correctly found trust issues but under-surfaced
them in the final chat message, assuming the user would read the full report.
This release forces every trust-relevant finding to the top of the chat verdict
and adds the scan categories it was missing. Same analysis engine — additive only.

### Added
- **§5.2-D Trust-Relevant Behavior Scan (REQUIRED)** — 9 mandatory categories with
  `file:line` evidence and a 4-way classification (confirmed malicious / suspicious /
  legitimate-but-high-risk / benign-but-trust-relevant):
  forced output content (promo footers, backlinks, no-opt-out branding), auto-execution
  (hooks/installers/MCP/package-manager), remote execution (`curl|sh`, download cradles),
  obfuscation (base64/hex/eval), phone-home/callbacks, credential access
  (`.env`/SSH/keychain/`gh auth token`), project infection (build phases/CI/cron), supply
  chain (npx/npm/pip/postinstall), and scope mismatch.
- **Severity Floors table** — minimum severities per behavior; any Critical finding
  (`curl|sh`, credential exfiltration, hidden remote execution) caps the overall verdict
  at DO NOT USE.
- **Step 3 Safety Guardrails** — static analysis only; never execute the evaluated skill's
  scripts/installers/hooks; extract ZIPs to an isolated temp dir (zip-slip containment);
  decode-to-read never decode-to-eval; dynamic testing requires explicit user OK + sandbox.

### Changed
- **Step 6 rewritten** from "Make Confident Judgments" (5 vague bullets) to a **required,
  standalone 5-section chat verdict**: Verdict / Top Risks / Should You Install? /
  Safer Path / Full Report. The report file is now explicitly a backup, not the deliverable.
- **Wording rules (hard):** bare "use with caution" is banned — must be followed by
  `use with caution because: [specific bullets]`; findings may not be buried or softened
  for brevity; lead with the worst finding. Clean skills must use the exact sentence:
  "No obvious auto-execution, phone-home, credential exfiltration, remote execution, or
  output-pollution behavior found in static review."
- **Step 4 report path** made runtime-agnostic (`/mnt/user-data/outputs/` if present, else
  current working directory) so local runs don't fail writing the report.
- **Description** expanded with the new detection keywords.

### Testing
- 9 inert acceptance fixtures added under `test-fixtures/` (promo footer, `curl|sh`,
  base64 blob, post-edit hook, MCP-npx, `gh auth token` reader, webhook callback, Xcode
  build phase, benign control).
- TDD verified: RED baseline (old skill opened with bare "use with caution", buried the
  footer) → GREEN (new skill leads with each planted issue in the 5-section format; benign
  control correctly returns SAFE with no false positive).

## [1.0.0] — prior

Original release: source acquisition, ZIP extraction, SKILL.md / scripts / references /
assets analysis, community research, attack-pattern matching, 0–100 risk scoring, and
markdown assessment report.
