# MCP rubric 1.0.0

Use `rubric-v1.json` as the single definition of checks, weights and result criteria. The 14 checks total 100: security 45, privacy 20, launch/supply 15, reliability 10, transparency 10. These are explicit heuristic priorities, not calibrated incident probabilities. MCP tool authorization, transport, input sinks and data destinations are core checks.

## Ledger

Generate the input with `scripts/score.py --template`. Fill `target.identity`, `transport`, `review_basis`, `revision`, and `deployment` with the selected scope. For source review `revision` must be a full 40-hex commit or 64-hex supplied snapshot SHA; a hash identifies the snapshot, not its trustworthiness. For hosted documentation use `hosted_docs`, `remote_http`, and a meaningful date/version label instead. Never invent an immutable revision.

Each check needs:

```json
{"id":"security.inputs","status":"concern","severity":"low","reason":"Intentional general-purpose command tool is disclosed but requires a restricted account.","evidence":[{"source":"src/tools.py @ COMMIT","line_start":20,"line_end":48,"detail":"Handler accepts selected commands and executes with the documented user's authority."}]}
```

- **pass**: full check criterion established in reviewed scope. Evidence required, severity `none`.
- **concern**: concrete, bounded residual issue; half points, severity `low` or `medium`. Not a substitute for missing evidence.
- **fail**: demonstrated criterion failure; zero points, `medium`/`high`/`critical`, respecting the check's severity floor. Severity reflects exploitability, data sensitivity, exposure and impact, not keyword presence. Upgrade to critical for such consequences as demonstrated covert credential exfiltration or destructive control.
- **unknown**: insufficient evidence, declined inspection, failed access, missing dependency results, unread relevant code; no points in assessed denominator and lower coverage. Severity `none`; explain the gap.
- **not_applicable**: only `privacy.hosted` for `stdio`/`local_http`, with evidence establishing local deployment. External API calls by a local server still belong in data-destination/credential checks. Remote servers cannot exclude hosted behavior just because it was not reviewed.

Missing checks become unknown. Duplicate checks/JSON keys, injected weights, unsupported statuses and resolved checks without evidence are rejected. A partial check cannot pass based on the reviewed fragment: use unknown unless available evidence already demonstrates a concrete failure.

## Arithmetic and gates

- Earned = sum(check weight × status credit), with pass 1, concern 0.5, fail 0.
- Applicable = 100 minus permitted N/A weight (6 for a verified local deployment).
- Assessed = applicable minus unknown weight.
- Reviewed-evidence score = 100 × earned / assessed, then severity cap.
- Weighted coverage = 100 × assessed / applicable. This is **not percent of source read**.
- Caps: none/low 100, medium 69, high 49, critical 29. Severe findings cannot be averaged away by polished documentation.
- Critical → DO NOT USE; high → NOT RECOMMENDED. Otherwise any missing core check or zero assessed checks → INCOMPLETE. With resolved core checks: below 30 DO NOT USE; below 50 NOT RECOMMENDED; below 85 USE WITH CAUTION; 85+ with unknowns REVIEWED WITH LIMITATIONS, otherwise NO MAJOR RISKS IDENTIFIED.
- All unknown → no numerical score. Some evidence → numerical score still shown, but marked provisional beside coverage, including when verdict is INCOMPLETE. Verdicts use unrounded values; display uses one decimal place.

Never present `100/100 at 5% coverage` as safe. Repeat the core gap and selected deployment beside a provisional score. Group totals derive directly from their checks; there is no separately invented usability or overall rating. Failed/blocked current advisory or incident research is not negative evidence. Document current source/tool limitations without assuming absent findings prove safety.
