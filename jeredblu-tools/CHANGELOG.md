# Changelog — jeredblu-tools

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
