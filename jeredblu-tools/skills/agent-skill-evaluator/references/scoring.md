# Evidence scoring (rubric 1.0.0)

This is a **reviewed-evidence score**, not a probability of safety, malware detector, certification, or functional test. Weights express judgment priorities and have not been calibrated against an incident dataset. Higher is better. The model still must inspect evidence and make defensible classifications; the calculator only validates structure and arithmetic.

## Ledger

Use `scripts/score.py --template`. Identify the target name, origin (`source`), full 40-hex commit or 64-hex archive/snapshot SHA-256 (`revision`), and exact review scope. For local directories, record file hashes or a stable snapshot identity alongside the report. Do not pretend a branch name pins bytes.

For each rubric check supply `id`, `status`, `severity`, `reason`, and `evidence`. An evidence item has `source` and `detail`, optionally positive `line_start`/`line_end`. The ledger cannot override weights/points. Missing check rows become unknown. Unknown and pass must have severity `none`; concern is low/medium; fail is medium/high/critical and must meet that check's floor.

- **pass**: actual inspection supports the criteria, including a demonstrated absence of the relevant capability; earns the full weight.
- **concern**: bounded, evidenced low/medium issue; earns half weight.
- **fail**: established substantial violation; earns zero. A fail must meet the rubric severity floor; escalate high/critical consequences, not simply suspicious keywords.
- **unknown**: unavailable, unread, unresolved or outside the permitted review; earns no assessed credit and reduces coverage, not a failure. Explain the gap. There is no N/A escape hatch: established absence is a pass, unestablished absence is unknown.

For a concern/failure, quote active behavior and explain impact, authorization, reachable context and mitigation. A quoted attack example, necessary scoped API credential, normal user-authorized package installation, or MCP declaration is not automatically malicious. Conversely, documented behavior is not automatically acceptable: undisclosed/forced promo has at least medium severity (high for client/white-label output); unreviewed download-and-run or credential exfiltration is critical; unconsented hooks, broad credential reads, and unauthorized persistence can be high. Normal process invocation is not itself remote-code execution. Keep trust-relevant legitimate behavior visible even if it passes.

## Calculation and verdict

`earned / assessed weight × 100`, then cap by the worst resolved severity: low/none 100, medium 69, high 49, critical 29. Coverage is `assessed / 100 × 100` (weighted checks), not source-code coverage. Category totals and every check's points are printed. Never average hand-assigned category scores.

Critical -> DO NOT USE; high -> NOT RECOMMENDED; all unknown -> INCOMPLETE with no number. Otherwise <30 -> DO NOT USE, <50 -> NOT RECOMMENDED, <85 -> USE WITH CAUTION. At least 85 with unknowns -> REVIEWED WITH LIMITATIONS, otherwise NO MAJOR RISKS IDENTIFIED. Even 100/100 with 5% coverage is only a provisional score over those assessed checks, not a clean result. State the main missing surfaces immediately next to it.

Display score, provisional flag, coverage, highest severity/cap and actual file-read scope together. Points-only full-rubric bounds are supplied for transparency; they are not confidence intervals and newly discovered serious findings can lower them. Keep the generated JSON/Markdown with the evidence ledger, scanner output and report. These tools never execute the evaluated target or authenticate the truth of submitted evidence.
