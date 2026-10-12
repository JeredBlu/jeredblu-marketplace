#!/usr/bin/env bash
#
# fetch.sh — fetch a GitHub repo for STATIC review without executing anything from it.
#
# SAFETY CONTRACT (do not weaken):
#   * Clones into a fresh mktemp dir — never the user's project or home dir.
#   * git clone never runs repo-supplied hooks (hooks are not cloned). We still
#     null the hooks path and disable fsmonitor so a user-global config can't fire.
#   * No submodules (they can point anywhere), no LFS smudge (big/opaque blobs),
#     no local-file protocol, no credential prompts.
#   * NEVER follow up by running the repo's installers, build scripts, package
#     manager, Makefile, or tests. Reading is safe; running is the attack surface.
#   * Do NOT `cd` into the clone from an interactive shell: direnv/mise/asdf shell
#     hooks can act on .envrc / .tool-versions. Use absolute paths and `git -C`.
#
# Usage:  fetch.sh <github-url | owner/repo> [depth=300] [ref]
#   ref = tag or branch to review (e.g. the tag a release was built from).
# Output: last line is the absolute path of the checkout.

set -euo pipefail

SPEC="${1:-}"
DEPTH="${2:-300}"
REF="${3:-}"
if [[ -z "$SPEC" ]]; then
  echo "usage: fetch.sh <github-url | owner/repo> [depth] [ref]" >&2
  exit 2
fi

# Normalize to owner/repo
R="${SPEC#https://}"; R="${R#http://}"; R="${R#www.}"; R="${R#github.com/}"
R="${R%.git}"; R="${R%/}"
R="$(printf '%s' "$R" | cut -d/ -f1-2)"
if ! [[ "$R" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  echo "could not parse owner/repo from: $SPEC" >&2
  exit 2
fi

DEST="$(mktemp -d "${TMPDIR:-/tmp}/repo-eval.XXXXXX")"
BRANCH_ARGS=()
[[ -n "$REF" ]] && BRANCH_ARGS=(--branch "$REF")

# Ignore user/system filter configuration as well as hooks. Public HTTPS repos only;
# this deliberately does not inherit credential helpers for private repositories.
GIT_LFS_SKIP_SMUDGE=1 GIT_TERMINAL_PROMPT=0 GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_COUNT=0 git \
  -c init.templateDir= \
  -c core.hooksPath=/dev/null \
  -c core.fsmonitor=false \
  -c protocol.file.allow=never \
  -c submodule.recurse=false \
  clone --quiet --depth "$DEPTH" --single-branch --no-recurse-submodules \
  "${BRANCH_ARGS[@]+"${BRANCH_ARGS[@]}"}" \
  "https://github.com/${R}.git" "$DEST/src"

SRC="$DEST/src"
echo "repo:    $R"
echo "revision: $(git -C "$SRC" rev-parse HEAD)"
echo "commit:  $(git -C "$SRC" log -1 --format='%h %ad %an' --date=short)"
echo "files:   $(find "$SRC" -path "$SRC/.git" -prune -o -type f -print | wc -l | tr -d ' ')"
echo "size:    $(du -sh "$SRC" 2>/dev/null | cut -f1) (incl. .git)"
[[ -f "$SRC/.gitmodules" ]] && echo "NOTE:    has .gitmodules (submodules NOT fetched — list them in the report)"
[[ -f "$SRC/.gitattributes" ]] && grep -qi 'filter=lfs' "$SRC/.gitattributes" 2>/dev/null \
  && echo "NOTE:    uses Git LFS (LFS blobs NOT fetched — pointer files only)"
echo "workdir: $DEST   <- save all scan/report scratch output here (e.g. $DEST/scan.txt), never a fixed /tmp name"
echo "$SRC"
