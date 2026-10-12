# Repo Evaluator 1.1.0 validation

Validated locally on macOS on 2026-10-12. Rubric version: 1.0.0.

## Reproduce

From the repository root:

```sh
python3 -B -m unittest discover -s jeredblu-tools/skills/repo-evaluator/tests -v
```

## Results

- Python 3.14.6: **45 tests passed** (including parameterized/subtest cases).
- macOS system Python 3.9.6: **44 passed, 1 skipped**. The TOML-success test is
  intentionally skipped because 3.9 lacks `tomllib`; the missing-parser warning
  regression still runs and passes.
- Shell syntax checks: `bash -n` on all three shell helpers passed.
- Skill frontmatter/structure validator passed using an existing PyYAML-enabled
  environment. No packages were installed. Version is under `metadata.version`.
- Download ZIP: all 18 packaged files match the source byte-for-byte; all 45 tests
  also passed from a fresh extraction using the archive validation helper.
- Public HTTPS fetch smoke test succeeded against JeredBlu/jeredblu-marketplace
  revision `8946664033ea20cc9b0ccd8b10c11b4a113c690b` without building/installing it.
- JSON scan smoke: 32 text files read, five opaque/binary gaps, exit 3/incomplete.
  Dependency smoke with `--offline`: explicitly incomplete, not a clean OSV result.
- CLI evidence-ledger example with missing reputation evidence: INCOMPLETE,
  score withheld, range 89.4–100 and 89.4% weighted rubric coverage. This used a
  synthetic source-only fixture, not a safety assessment of the public repository.

## Properties exercised

- Every check contributes its documented weight; all weights sum to 100.
- Per-dimension totals, deterministic ordering, monotonic deductions, unknown
  bounds, N/A denominator adjustment and severity caps/floors.
- Invalid/duplicate IDs and JSON keys, score overrides, missing evidence and
  incompatible severity/status combinations rejected.
- Critical findings cannot be averaged away or downgraded below their rubric floor.
- More than 40 matches retained in JSON; truncated text previews labeled.
- Prompt-injection and code-risk fixtures produce leads without executing payloads.
- HTML scripts, build files in test directories and agent configurations included.
- Read failures, invalid encoding, symlinks, opaque files and size/count limits
  remain explicit gaps rather than negative findings.
- Unsupported lockfiles, malformed inputs, missing TOML support, OSV failure and
  partial/paginated responses remain distinguishable from successful checks.
- ZIP/TAR traversal, absolute/device paths, symbolic/hard links, special files,
  aliases/collisions and oversized archives rejected before payload extraction.
- Normal inert archives extract without executable bits; the shell artifact
  wrapper stops on blocked archives before signature inspection.
- Git fetch does not inherit global filter configuration, templates or hooks.
- Metadata lookup failures report NOT CHECKED rather than absence of evidence.

## Limits

These are regression and plumbing tests, **not a malware-detection benchmark**.
They do not establish recall/precision on adversarial real repositories, empirical
calibration of weights, model consistency, or security certification. No target
repository code or fixture payload was executed. Live OSV failure handling uses
mocked responses; notarization, DMG/PKG parsers and actual release/source equivalence
were not validated against a corpus of production artifacts. No Jev call or other
hosted semantic-review integration was introduced. Changes are local until published.
