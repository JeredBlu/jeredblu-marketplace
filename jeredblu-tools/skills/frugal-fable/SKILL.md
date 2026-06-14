---
name: frugal-fable
description: Use when running on Claude Fable (or any premium model) and the work is token-heavy — building features, multi-file changes, research, testing, debugging, migrations, or anything spanning many files/sources. Keeps Fable on the judgment (decompose, architect, synthesize, review) and delegates bounded, verifiable heavy-lifting to cheaper models (Haiku/Sonnet/Opus) — with a quality floor so construction work is never owned by a weak agent. Triggers on requests to "be efficient with Fable", "don't burn tokens", orchestrate subagents, or delegate work.
---

# Frugal Fable

Fable is expensive because Fable is good. Spend it on judgment, not on scans,
boilerplate, and log-reading. Delegate the heavy, repeatable, *verifiable* work
to cheaper models — but never let a weak agent own quality-critical construction.

**The deal:** cheaper agents *gather signal and produce candidate work to files*.
Fable *decides, integrates, and reviews*. Truth-judgment and final quality stay
with Fable, always.

## ⚠️ Turn Ultracode OFF before using this skill

frugal-fable and **Ultracode are opposites** and must not run together.
Ultracode's standing order is *"run a workflow for every task, token cost is not
a constraint, be exhaustive, run several workflows in sequence, loop until
nothing is left."* frugal-fable's whole purpose is to **conserve**. Run both and
you get the worst case: cheap workers fan out, *and then* Fable launches extra
exhaustive passes on top — which is exactly how usage gets blown (it has happened).

- If Ultracode is on, **say so and stop** — ask the user to toggle it off (`/ultracode` or the toggle by the model selector), then proceed.
- This skill is a *guide*, not a hard cap. A guide cannot beat Ultracode's "spend everything" directive. The only thing that truly enforces a ceiling is a **token budget in the workflow** (see Budget discipline). Use it.
- After a delegated workflow returns, **do NOT autonomously launch a second "gap-fill" research round.** Read the saved files, synthesize, and stop. Widen scope only if the user asks.

## Budget discipline (the real brake)

A skill convention biases behavior; it cannot force a spend limit. When the user
is on a constrained usage window — or you're running unsupervised — use a
workflow with a **hard token cap**, not just routing advice:

- For research, use the bundled **`references/frugal-research.js`** workflow (hard caps: 4 angles / 8 fetches / 10 claims / 2 votes, a `budget.remaining()` gate that stops fanning out, synthesis pinned to Sonnet). Run it via the `Workflow` tool with `{scriptPath: "<abs path to references/frugal-research.js>"}`, or copy it to `~/.claude/workflows/frugal-research.js` to invoke by name. (If you also have the community `deep-research-cheap` workflow installed, that's the deeper, uncapped alternative for when you have headroom.)
- In any custom `Workflow`, gate fan-out on `budget.remaining()` and keep a reserve for synthesis. See `references/fanout-template.js`.
- **Scope is a cost lever.** A 6-lane, 12-question mega-prompt makes even "cheap" workflows expensive (verify fans out per claim). Split huge asks into focused runs, or cap the angles. Tell the user the tradeoff instead of silently fanning out to 100 agents.
- "Cheap model" ≠ "cheap run." 75 Sonnet agents at ~27k each is still ~2M tokens. Watch the *count*, not just the per-agent tier.

## What stays with Fable (never delegated)

- Decomposing ambiguous work into clean, independent slices.
- Architecture, product, and safety tradeoffs.
- Shared-file coordination and integrating partial work into one coherent whole.
- Resolving conflicting subagent reports — deciding what's actually true.
- Final review, risk assessment, and user-facing synthesis.

## Model routing — decide per slice, at runtime

We don't know in advance what we're building, so route each slice when you reach
it. Score it on three axes; the highest one sets the **floor** (you may always go
higher, never lower):

- **Stakes** — ships to prod? architectural? security/correctness-critical? → raises floor
- **Reversibility** — one-way door, hard to test, destructive? → raises floor
- **Ambiguity** — spec fuzzy, needs real judgment? → raises floor, often stays with Fable

| Slice | Owner | Gate before Fable accepts |
|---|---|---|
| Scans, grep, repo/web inventory, log & test-output reduction, doc summaries | **Haiku** | low-stakes; sanity-check only |
| Bounded, well-specified patches; adversarial verification; targeted tests | **Sonnet** | build + relevant tests pass |
| Hard refactors, correctness/security-critical code, slices where Sonnet visibly struggles | **Opus** | Fable reviews the diff |
| Decompose, architect, coordinate, integrate, final review | **Fable** | — |

**Conservative build floor (this project's default):** cheap models do mechanical
work and bounded patches that come with passing tests. Anything architectural,
high-stakes, or one-way stays with **Opus or Fable**. When unsure which tier, go
up one — a re-run on a cheap model that wasn't good enough costs more than starting
at the right tier.

## The context firewall (this is the main token saver)

The thing that nukes Fable's budget is subagent output landing *in Fable's
context*. So don't return it there.

- Delegated agents **write findings/patches/logs to a scratch dir**
  (`.frugal-fable/<task>/` in the repo, gitignored) and **return only**:
  `path` + a 3-line summary + a confidence level.
- Fable reads a file **on demand** — only the ones that matter, only at the moment
  it needs them (usually synthesis/review). Not all of them, not up front.
- For research specifically, prefer tools that already write to file over ones that
  dump into context (the Bright Data skills do this — see Research lane).

This keeps Fable's working set small even across dozens of subagents.

## Handoff packets

Write every delegated prompt as if the agent has zero chat context. Include only:

- Exact objective + the repo path.
- In-scope files/surfaces, and what's explicitly **out of scope**.
- **Where to write output** (the scratch path) and **what to return** (path + summary + confidence — *not* the full content).
- Verification commands / browser flows to run, and what success looks like.
- **Stop conditions:** if code doesn't match the prompt, a command fails after one
  retry, or the task needs out-of-scope files — stop and report, don't improvise.

## Choosing the harness — not every task needs a workflow

- **1 slice, or tightly coupled / interactive** → Fable does it directly. No delegation; coordination cost would exceed savings.
- **A few independent slices** → inline `Agent` calls (set the model per the table).
- **Many independent slices / heavy fan-out** → author a `Workflow` (agents run *outside* Fable's context — cheapest). Adapt `references/fanout-template.js`.
- **Research** → use `frugal-research` (hard budget cap) when usage is constrained or you're unsupervised; `deep-research-cheap` when you have headroom and want maximum depth. Don't rebuild either.

## Lanes (soft defaults, not rigid rules)

- **Build/execute:** Fable plans + owns shared files, integration, and final review.
  Cheaper agents produce *candidate* bounded patches to the scratch dir with passing
  tests. **Quality gate:** no patch is accepted until it passes the verification its
  stakes demand (build, targeted tests, or Fable diff-review for high-stakes). Fable
  integrates and reviews — it never rubber-stamps a delegated diff.
- **Research:** delegate to `deep-research-cheap` (Haiku collects via `bdata` + WebSearch,
  Sonnet verifies adversarially, Fable synthesizes). For one-off lookups, a single Haiku
  agent with `bdata search`/`bdata scrape` writing to a scratch file. Prefer `bdata` over
  built-in web tools — broader reach, fewer blocks, and the bdata skills output to file.
- **Testing:** Fable names the validation direction and which checks matter. Lighter agents
  run targeted tests, browser flows, screenshots, and log reduction; report exact commands,
  failures, likely cause, and whether failures look real / flaky / environmental.
- **Debugging:** cheaper agents cluster logs, reproduce, and try small fixes to files; Fable
  decides which diagnosis is trustworthy and owns the real fix.

If a task is tiny, or the validation itself needs delicate judgment, keep it with Fable.

## Vetting delegated work

Treat subagent reports as **leads, not facts**. Before relying on a high-impact
finding, opening a PR, or telling the user it's done: reopen the cited file(s),
confirm the line refs / failures, and review the final diff against the task.
Let lighter agents gather signal; keep truth-judgment with Fable.

## References

- `references/frugal-research.js` — budget-capped research `Workflow` (Haiku collect → Sonnet
  verify → Sonnet synthesize, hard caps + token gate). Run via the `Workflow` tool with
  `{scriptPath}`, or copy to `~/.claude/workflows/` to invoke by name. Requires a Fable-class
  runtime that exposes the `Workflow` tool.
- `references/fanout-template.js` — adaptable `Workflow` script for the general fan-out case
  (route by model, verify, synthesize). Copy and adapt per task; don't run blind.
- `references/routing-cheatsheet.md` — one-screen version of the routing table + firewall
  protocol for quick recall mid-task.

## Credits

Adapted from BuilderIO's `efficient-fable` skill, extended here with explicit model tiers, a
conservative build-quality floor, the file-based context firewall, harness selection, and a
budget-capped research workflow (`frugal-research.js`). Lanes: research, build/dev, testing,
debugging. As with all delegation, the orchestrator verifies delegated work before relying on
it — see **Vetting delegated work** above. That review step is the point, not an afterthought.
