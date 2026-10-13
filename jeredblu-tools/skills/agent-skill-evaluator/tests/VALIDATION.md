# Local validation — 2026-10-13

Run from the repository root:

```bash
python3 -B -m unittest discover -s jeredblu-tools/skills/agent-skill-evaluator/tests -v
/usr/bin/python3 -B -m unittest discover -s jeredblu-tools/skills/agent-skill-evaluator/tests -q
bash -n jeredblu-tools/skills/agent-skill-evaluator/scripts/scan.sh
```

31 tests pass on Python 3.14.6 and macOS Python 3.9.6. The installed skill-creator `quick_validate.py` also passes (run using an existing interpreter with PyYAML; no dependency installed). `git diff --check` passes for this skill.

Coverage includes deterministic clean/partial/all-unknown/severe outcomes; per-check half credit; duplicate/invalid ledger records, line ranges, revision identity and weight overrides; all scanner categories; 61 lead-bearing files; binary/non-UTF-8/oversized files, resource limits, read failures, symlinks and special files; unusual names and line boundaries; traversal/link/duplicate/oversized archives; CLI JSON/exit codes. Inert script fixtures are read, never executed.

These tests validate helper behavior and arithmetic, not model judgment accuracy or universal detection of malicious skills. Pattern matching still misses semantic/multiline/unknown attacks; full source and data-path reading remains necessary. Archive links and some legitimate opaque assets are conservatively refused or left unreviewed. The single-pass scanner reduces repeated filesystem reads, but no end-to-end token/latency improvement has been benchmarked. Independent forward-testing results, if performed, must be reported separately rather than inferred from these unit tests.
