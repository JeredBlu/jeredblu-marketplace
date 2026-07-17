# Codex delegation — cross-CLI recipes (the second pool)

Read this before the first `codex exec` of a session. Everything in SKILL.md
still applies — handoff packets, context firewall, vetting. This file adds
only the Codex-specific mechanics.

The consent gate lives in SKILL.md — it must be satisfied (Codex present,
user said yes, slices named) before any `codex exec`.

## Current model mappings (as of 2026-07 — the ONLY place model IDs live)

| Role (SKILL.md routing) | Codex model | Use for |
|---|---|---|
| Scan tier (≈Haiku) | `gpt-5.6-luna` | genuine volume reads only |
| Construction tier (≈Sonnet) | `gpt-5.6-terra` | **default** — bounded patches, targeted tests |
| Frontier tier (≈Opus+) | `gpt-5.6-sol` | hard slices, adversarial review, PR review |

Effort dial: `-c model_reasoning_effort=` one of
`low | medium | high | xhigh | max` (`max` verified on codex-cli 0.144.1).

**Generous-quota bias:** Codex subscription limits are looser than Claude's.
Default Terra at `high`; escalate to Sol `xhigh` freely for anything hard.
When models churn, update this table only — no prose elsewhere names a model.

## Recipes (exact — flags before the prompt, do not improvise)

Build slice (write-capable, sandboxed to the repo):

```bash
codex exec -s workspace-write -C <repo> \
  -m gpt-5.6-terra -c model_reasoning_effort=high \
  -c 'notify=[]' \
  -o .frugal-fable/<task>/codex-report.md \
  "<handoff packet>" </dev/null
```

Adversarial review / second opinion (read-only, structured verdict):

```bash
codex exec -s read-only -C <repo> \
  -m gpt-5.6-sol -c model_reasoning_effort=xhigh \
  -c 'notify=[]' \
  --output-schema <verdict-schema.json> \
  -o .frugal-fable/<task>/codex-verdict.json \
  "<review packet>" </dev/null
```

Repo/PR review (runs against the current repo — `cd` there first;
pick ONE scope flag: `--base <branch>` | `--uncommitted` | `--commit <sha>`):

```bash
cd <repo> && codex exec review --base main \
  -m gpt-5.6-sol -c 'notify=[]' \
  -o .frugal-fable/<task>/codex-review.md \
  "<focus instructions>" </dev/null
```

Amendments — same session, synchronous (never a detached wrapper).
Resume does NOT keep the original run's flags: it reverts to
`~/.codex/config.toml` defaults (verified: a `workspace-write` run resumed as
`danger-full-access`). Re-pin sandbox via `-c` (resume has no `-s`):

```bash
codex exec resume --last -c 'sandbox_mode="workspace-write"' \
  -c 'notify=[]' \
  -o .frugal-fable/<task>/amend-report.md \
  "<amendment packet>" </dev/null
```

Prefer capturing the session id from the first run's output and using
`codex exec resume <session-id> ...` when multiple Codex workers ran.

## Firewall + coordination

- `-o` writes Codex's final message to the scratch dir — that file, not
  stdout, is the report. Read it on demand like any subagent report.
- **Disjoint file ownership** per concurrent worker (Codex or Claude); the
  orchestrator commits serially on return.

## Gotchas

- Runs inherit `~/.codex/config.toml` (often `danger-full-access` +
  `approval=never`). Always pass `-s` explicitly; `read-only` for reviews.
- Everything in the prompt position is task text — a stray `--help` there
  becomes a live Codex run. Flags go before the prompt string.
- `</dev/null` is load-bearing: an open stdin is appended to the prompt and
  can stall the run. `-c 'notify=[]'` keeps delegated workers from firing the
  user's turn-end notify hook on every completion.
- If the user will use this lane often, suggest allowlisting `codex exec` as
  a Bash prefix in `.claude/settings.json` to avoid permission prompts.
- The `openai-codex` Claude Code plugin's wrapper detaches runs and drops
  follow-up messages (observed 2026-07-15) — never orchestrate through it;
  call `codex exec` directly.
