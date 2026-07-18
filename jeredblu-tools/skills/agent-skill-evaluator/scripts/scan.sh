#!/usr/bin/env bash
#
# scan.sh — read-only danger-pattern sweep for the agent-skill-evaluator skill.
#
# SAFETY CONTRACT (do not weaken):
#   * This script ONLY reads. It runs `find` and `grep` over the target's files.
#   * It NEVER executes, sources, imports, or installs anything from the target.
#   * It exists precisely so the evaluator does not have to run a skill's own code
#     to understand it. Reading a malicious script is safe; running it is not.
#
# Usage:  scan.sh <extracted_target_dir>
# Output: a categorized hit-list (CATEGORY | file:line | matched text) plus a
#         summary count. Every hit is something the evaluator MUST address in its
#         report — a category with 0 hits is documented as clean, not skipped.
#
# Exit code is always 0: this is a scanner, not a gate. "No hits" != "safe";
# it means "these patterns did not match" — the human/agent still judges.

set -uo pipefail

TARGET="${1:-}"
if [[ -z "$TARGET" || ! -d "$TARGET" ]]; then
  echo "usage: scan.sh <extracted_target_dir>" >&2
  exit 2
fi

# Common grep options: recursive, ignore-case, line numbers, skip binaries,
# skip the VCS dir. We never follow symlinks out of the tree.
GREP=(grep -rIniE --exclude-dir=.git --exclude-dir=node_modules)

total=0

scan() {
  # scan "<Category label>" "<extended regex>"
  local label="$1" pattern="$2" hits
  local raw; raw="$(cd "$TARGET" && "${GREP[@]}" -- "$pattern" . 2>/dev/null)"
  echo "### ${label}"
  if [[ -z "$raw" ]]; then
    echo "  none"
    echo
    return
  fi
  local n; n="$(printf '%s\n' "$raw" | grep -c .)"
  total=$((total + n))
  # Group by file so a noisy doc can't bury the one instruction file that matters.
  # One line per file: "<file>  (<hits>)  first-match L<line>: <text>". Every
  # hit-bearing file stays visible regardless of how many hits any other file has.
  printf '%s\n' "$raw" | awk -F: '
    { file=$1; line=$2;
      $1=""; $2=""; sub(/^:+/,""); sub(/^[ \t]+/,"");
      cnt[file]++; if (!(file in firstL)) { firstL[file]=line; firstT[file]=$0 } }
    END { for (f in cnt) printf "%s\t%d\t%s\t%s\n", f, cnt[f], firstL[f], firstT[f] }' \
    | sort -t$'\t' -k2 -rn | head -n 60 \
    | while IFS=$'\t' read -r f c l t; do
        t="${t:0:120}"
        printf '  %s  (%s hit(s))  L%s: %s\n' "$f" "$c" "$l" "$t"
      done
  local files; files="$(printf '%s\n' "$raw" | cut -d: -f1 | sort -u | grep -c .)"
  echo "  (${files} file(s), ${n} hit(s))"
  echo
}

echo "== agent-skill-evaluator :: read-only danger scan =="
echo "target: $TARGET"
echo "(patterns matched below are LEADS to verify, not proof of malice)"
echo

# 1. Forced output content — promo footers, backlinks, attribution, no-opt-out branding.
#    PRECISION over recall. Bare words like "footer", "backlink", "community", "sponsor"
#    are legitimate domain vocabulary (an SEO tool says "backlink" 400 times) and, if
#    matched, bury the real signal and train the reader to ignore the category. So this
#    matches only tokens that rarely appear except in a forced-promo instruction:
#    monetization destinations and the append/"do not remove" instruction phrases.
#    Subtler promo (e.g. a bare vanity URL) is caught by the mandatory full-read of
#    SKILL.md + command files, not here — grep is the net, the full read is the backstop.
scan "Forced output / promo / backlink" \
  'skool\.com|patreon\.com|ko-fi\.com|buymeacoffee|gumroad|discord\.(gg|com/invite)|t\.me/|append this footer|community footer|as the (very )?last output|do ?n.?t remove (this|the) (footer|link|attribution|line|section)'

# 2. Remote execution — download-and-run
scan "Remote execution (download-and-run)" \
  'curl[^|]*\|[^|]*(ba)?sh|wget[^|]*\|[^|]*(ba)?sh|iwr[^|]*\|[^|]*iex|bash -c[^)]*curl|\$\(curl|\$\(wget'

# 3. Credential access.
#    PRECISION: bare "api_key"/"oauth"/"bearer" are normal in any tool that talks to an
#    API and generate hundreds of legitimate hits. Match instead the tells of a script
#    *extracting* a secret it has no business touching: the token-print command, reads of
#    named secret files (ssh keys, aws creds), and keychain extraction.
scan "Credential access (extraction)" \
  'gh auth token|\.aws/credentials|id_rsa|\.ssh/id|security find-(generic|internet)-password|gcloud auth print|aws_secret_access_key|(cat|open|read|source|load|dotenv)[^;|]{0,30}\.env'

# 4. Auto-execution — hooks / installers / startup
scan "Auto-execution (hooks / installers / startup)" \
  'posttooluse|pretooluse|sessionstart|hooks\.json|"hooks"|postinstall|preinstall|launchagents|launchdaemons|crontab|cron\.d'

# 5. Supply chain — package managers / external MCP.
#    PRECISION: bare "npm install"/"pip install" appear all over install docs. Match the
#    auto-run flavors: unattended installs and MCP server command registration that pulls
#    and runs a package (the real "you registered a third party" risk).
scan "Supply chain (auto-run installs / MCP)" \
  'npx +-y|npx +--yes|npm install +-g|pipx run|uvx +|postinstall|"command" *: *"(npx|uvx|node|python[0-9]?)"'

# 6. Phone-home / callbacks.
#    PRECISION: "analytics"/"track"/"collect" are core SEO vocabulary — matching them
#    floods this category on any marketing tool. Match the tells of a skill quietly
#    calling home: webhooks, raw-IP URLs, and beacon/ingest endpoints.
scan "Phone-home / callbacks" \
  'webhook|telemetry|/(beacon|ingest)\b|hooks\.[a-z0-9.-]+\.[a-z]+/|https?://[0-9]{1,3}(\.[0-9]{1,3}){3}'

# 7. Obfuscation / dynamic eval
scan "Obfuscation / dynamic eval" \
  'base64|b64decode|atob\(|fromcharcode|rot13|codecs\.decode|eval\(|exec\(|os\.system|subprocess\.(popen|run|call).*shell=true'

# 8. Project infection — writes into the user's own project/system
scan "Project infection (build phases / CI / cron)" \
  'pbxshellscript|\.pbxproj|run script phase|\.github/workflows|package\.json|\.git/hooks|pre-commit|launchctl'

echo "== summary: ${total} total lead(s) across all categories =="
echo "Reminder: address EVERY category above in the report — 0 hits => document as"
echo "'scanned, none found', never silently omit. Then read the files in full to"
echo "confirm or dismiss each lead; grep is the net, the full read is the verdict."
