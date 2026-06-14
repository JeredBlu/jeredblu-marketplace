# Frugal Fable — mid-task cheatsheet

## Route each slice (highest axis sets the floor; go up, never down)

- Stakes ↑ (ships / architectural / security) · Reversibility ↑ (one-way / hard to test) · Ambiguity ↑ (needs judgment → Fable)

| Slice | Model |
|---|---|
| scan / grep / inventory / log + test-output reduction / doc summary | Haiku |
| bounded patch (well-specified) / adversarial verify / targeted tests | Sonnet (build+tests must pass) |
| hard refactor / correctness- or security-critical / Sonnet struggled | Opus (Fable reviews diff) |
| decompose / architect / coordinate shared files / integrate / final review | Fable (never delegate) |

Conservative floor: architectural/high-stakes/one-way → Opus or Fable only. Unsure → go up one tier.

## Context firewall

Delegated agent writes to `.frugal-fable/<task>/` and returns ONLY: `path + 3-line summary + confidence`.
Fable reads files on demand at synthesis/review — never pulls all output into context up front.

## Harness

1 slice / coupled / interactive → Fable direct. Few independent → inline `Agent`. Many independent → `Workflow` (out-of-context). Research → `deep-research-cheap` as-is.

## Handoff packet (every delegation)

objective + repo path · in-scope / out-of-scope · where to write + what to return (path+summary+confidence, not full content) · verification commands + success criteria · stop conditions (mismatch / failed retry / needs out-of-scope → stop & report).

## Quality gate

No delegated patch accepted until it passes the verification its stakes demand. Fable integrates + reviews the diff. Reports are leads, not facts — reopen cited files before relying on high-impact findings.

## Research tooling

`bdata search` / `bdata scrape` / bdata data-feeds over built-in web tools (broader reach, fewer blocks, writes to file). Fall back to WebSearch/WebFetch.
