#!/usr/bin/env bash
#
# scan.sh — read-only danger sweep of a checked-out repo, for the repo-evaluator skill.
#
# SAFETY CONTRACT (do not weaken):
#   * Only reads: find, grep, perl (as a text matcher), file, awk, git log.
#   * NEVER executes, sources, imports, builds, or installs anything from the target.
#
# Usage:  scan.sh <checkout_dir>
# Output: categorized LEADS grouped by file, a domain inventory ("who might it
#         talk to"), build-time code list, binaries, and a summary.
#
# Exit code is always 0: this is a net, not a gate. "No hits" != "safe".
# Every category must be addressed in the report — 0 hits => "scanned, none found".

set -uo pipefail

TARGET="${1:-}"
if [[ -z "$TARGET" || ! -d "$TARGET" ]]; then
  echo "usage: scan.sh <checkout_dir>" >&2
  exit 2
fi
TARGET="$(cd "$TARGET" && pwd)"

# Pin BSD/GNU grep for deterministic behavior (some machines alias grep → ugrep).
G=/usr/bin/grep; [[ -x "$G" ]] || G="$(command -v grep)"

EXCL=(--exclude-dir=.git --exclude-dir=node_modules)
DOCS=(--exclude=*.md --exclude=*.markdown --exclude=*.rst --exclude=*.adoc --exclude=*.txt
      --exclude=*.html --exclude=*.htm --exclude=LICENSE* --exclude=CHANGELOG* --exclude=*.svg
      --exclude=*.lock --exclude=package-lock.json --exclude=Package.resolved --exclude=go.sum)

total=0
declare -a SUMMARY=()

# scan "<label>" "<ERE>" [code|all] [exclude-ERE applied to matched lines]
scan() {
  local label="$1" pattern="$2" scope="${3:-all}" drop="${4:-}"
  local -a args=(-rIniE "${EXCL[@]}")
  [[ "$scope" == code ]] && args+=("${DOCS[@]}")
  local raw; raw="$(cd "$TARGET" && "$G" "${args[@]}" -- "$pattern" . 2>/dev/null)"
  [[ -n "$drop" && -n "$raw" ]] && raw="$(printf '%s\n' "$raw" | "$G" -viE -- "$drop")"
  echo "### ${label}  [${scope}]"
  if [[ -z "$raw" ]]; then
    echo "  none"; echo; SUMMARY+=("$(printf '%-44s %s' "$label" 0)"); return
  fi
  local n; n="$(printf '%s\n' "$raw" | "$G" -c .)"
  total=$((total + n))
  # Group by file so one noisy file can't bury the one that matters.
  printf '%s\n' "$raw" | awk -F: '
    { file=$1; line=$2; rest=$0; sub(/^[^:]*:[^:]*:[ \t]*/,"",rest);
      cnt[file]++; if (!(file in fl)) { fl[file]=line; ft[file]=rest } }
    END { for (f in cnt) printf "%s\t%d\t%s\t%s\n", f, cnt[f], fl[f], ft[f] }' \
    | sort -t$'\t' -k2 -rn | head -n 40 \
    | while IFS=$'\t' read -r f c l t; do
        printf '  %s  (%s)  L%s: %s\n' "$f" "$c" "$l" "${t:0:140}"
      done
  local files; files="$(printf '%s\n' "$raw" | cut -d: -f1 | sort -u | "$G" -c .)"
  echo "  (${files} file(s), ${n} hit(s); top 40 files shown)"
  echo
  SUMMARY+=("$(printf '%-44s %s' "$label" "$n")")
}

echo "== repo-evaluator :: read-only danger scan =="
echo "target: $TARGET  ($(find "$TARGET" -path "$TARGET/.git" -prune -o -type f -print | wc -l | tr -d ' ') files)"
echo "(every hit is a LEAD to confirm or dismiss in the report — not proof)"
echo

# --- Execution & install-time behavior -------------------------------------------------
scan "1. Remote execution (download-and-run)" \
  'curl[^|]*\|[^|]*(ba|z)?sh|wget[^|]*\|[^|]*(ba|z)?sh|iwr[^|]*\|[^|]*iex|invoke-expression|downloadstring\(|bash -c[^)]*curl|\$\((curl|wget)|exec\(.*(urlopen|requests\.get)|eval\(.*(fetch|urlopen|requests\.get)'

scan "2. Install-time hooks / quarantine bypass" \
  '"(pre|post)?install" *:|"prepare" *:|"prepublish" *:|cmdclass|postflight|post_install|preflight|binding\.gyp|xattr +-[a-z]*d[a-z]* +com\.apple\.quarantine|--no-quarantine|spctl +--master-disable'

scan "3. Persistence (runs at login / on schedule)" \
  'launchagents|launchdaemons|launchctl +(load|bootstrap|enable|submit)|smappservice|lssharedfilelist|smloginitem|crontab|cron\.d|systemctl +(--user +)?enable|wantedby=|currentversion\\+run|schtasks|>> *["~$a-z/{}]*\.(zshrc|bashrc|bash_profile|zprofile|profile)' \
  all

scan "4. Privilege escalation / security-setting changes" \
  '(^|[^a-z])sudo +|authorizationexecutewithprivileges|with administrator privileges|chmod +[0-7]*4[0-7]{3}|chmod +[ug]\+s|setuid\(|csrutil|kextload|systemextensions|smjobbless|tccutil|spctl +--(add|enable|disable)' \
  code

scan "5. Destructive commands" \
  'rm +-(rf|fr) +(/|~|\$home|\$\{home)([ /"]|$)|diskutil +(erase|zerodisk|secureerase)|mkfs|dd +if=[^ ]+ +of=/dev/|shred +|format +c:' \
  code

# --- Data access & surveillance ----------------------------------------------------------
scan "6. Credential / secret-store access" \
  'gh auth token|\.aws/credentials|id_rsa|id_ed25519|\.ssh/(id|config|known)|security +(find|dump)-(generic-password|internet-password|keychain)|keychains/|secitemcopymatching|gcloud auth print|aws_secret_access_key|\.npmrc|\.pypirc|\.netrc|\.docker/config\.json|\.kube/config|login data|key4\.db|logins\.json|cookies\.sqlite|local state"|wallet\.dat|nkbihfbeogaeaoehlefnkodbefgpgknn|(open|read|source|load)[^;|]{0,30}[^a-z]\.env([^a-z]|$)' \
  code

scan "7. Surveillance capability (keys / screen / clipboard / mic / cam)" \
  'cgeventtapcreate|addglobalmonitorforevents|pynput|keyboard\.on_press|setwindowshookex|getasynckeystate|iohidmanager|cgwindowlistcreateimage|scstream|screencapturekit|imagegrab|screencapture +-|avcapturedevice|getusermedia|pbpaste|pyperclip\.paste|clipboard\.readtext|getclipboarddata|pasteboard\.(string|data|readobjects)\(' \
  code

# --- Network: telemetry, phone-home, updates -------------------------------------------
scan "8. Telemetry / analytics / crash-report SDKs" \
  'posthog|api\.segment\.io|analytics-node|mixpanel|amplitude\.com|@amplitude|@sentry/|sentry_sdk|sentry\.io|sentry-cocoa|google-analytics\.com|googletagmanager|gtag\(|datadoghq|bugsnag|rudderstack|plausible\.io|umami|countly|appcenter\.ms|firebase.?analytics|heapanalytics|telemetry|analytics|usage.?stats|/v[0-9]/(track|events|collect)' \
  code

scan "8b. Telemetry off-switches (use to decide: on by default or opt-in?)" \
  'no_analytics|do_not_track|donottrack|disable_telemetry|telemetry_disabled|no_telemetry|telemetry_opt|analytics_opt|opt.?out' \
  all

scan "9. Phone-home / exfil endpoints (webhooks, raw IPs, tunnels, paste sites)" \
  'discord(app)?\.com/api/webhooks|hooks\.slack\.com|api\.telegram\.org/bot|webhook\.site|requestbin|pipedream\.net|ngrok(-free)?\.(io|app)|pastebin\.com|transfer\.sh|interact\.sh|oast\.(fun|pro|live|site|online|me)|burpcollaborator|duckdns\.org|no-ip\.|ddns\.net|https?://[0-9]{1,3}(\.[0-9]{1,3}){3}' \
  code \
  'https?://(127\.|0\.0\.0\.0|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|169\.254\.)'

scan "10. Auto-update / downloads code later (bypasses this review)" \
  'sparkle|sufeedurl|autoupdater|electron-updater|self[-_]?update|check_?for_?updates|update[-_]?check|releases/latest' \
  code

scan "11. Opens browser / URLs at runtime" \
  'webbrowser\.open|shell\.openexternal|nsworkspace\.shared\.open\(|xdg-open|(^|[^a-z])open +"?https?:|start +https?:' \
  code

# --- Promotion / monetization / output pollution -------------------------------------
scan "12. Auto-star / auto-follow your GitHub account" \
  '/user/starred/|/user/following/|starred/[a-z0-9_.-]+/[a-z0-9_.-]+|gh +repo +star|gh api +-x +put'

scan "13. Self-promo / affiliate / monetization in CODE (docs excluded)" \
  '[?&](ref|aff|affiliate|referral|refcode)=[a-z0-9_-]+|amzn\.to|tag=[a-z0-9-]+-20|utm_source=|star (this|the|our) repo|give (us|it) a star|buymeacoffee|ko-fi\.com|patreon\.com|gumroad|opencollective|skool\.com|github\.com/sponsors' \
  code

scan "14. Branding injected into user output" \
  'powered by [a-z0-9]|made with (love|❤|♥)|🤖 generated|generated (by|with) \[|\(generated (by|with) ' \
  code

# --- Hiding techniques ----------------------------------------------------------------
scan "15. Obfuscation / dynamic eval / shell-out" \
  'eval\(function\(p,a,c,k,e|b64decode|atob\(|fromcharcode|marshal\.loads|zlib\.decompress|pickle\.loads|codecs\.decode|new function\(|(^|[^a-z_.])eval\(|(^|[^a-z_.])exec\(|os\.system|shell *= *true|child_process|([a-z0-9+/]{100}){3,}' \
  code

scan "16. Crypto-mining" \
  'stratum\+tcp|xmrig|coinhive|cryptonight|minexmr|nicehash|--donate-level'

scan "17. Dev-environment triggers (run when you open/clone the folder)" \
  '"runon" *: *"folderopen"|postcreatecommand|poststartcommand|postattachcommand|pull_request_target'

# --- Non-grep sections ---------------------------------------------------------------------
echo "### 18. Trojan-source Unicode (bidi overrides / zero-width spaces in code; data files skipped)"
tro="$(cd "$TARGET" && find . -path ./.git -prune -o -path ./node_modules -prune -o -type f -size -2M -print 2>/dev/null \
  | "$G" -viE '\.(md|rst|txt|po|json5?|ya?ml|csv|strings|xliff|svg|png|jpe?g|gif|ico|pdf|ttf|woff2?)$' \
  | while IFS= read -r f; do
      perl -CSD -ne 'if (/\x{202A}|\x{202B}|\x{202C}|\x{202D}|\x{202E}|\x{2066}|\x{2067}|\x{2068}|\x{2069}|\x{200B}/) { print "$ARGV:$.\n"; close ARGV }' "$f" 2>/dev/null
    done | head -n 30)"
if [[ -z "$tro" ]]; then echo "  none"; else echo "$tro" | sed 's/^/  /'; SUMMARY+=("$(printf '%-44s %s' '18. Trojan-source Unicode' "$(echo "$tro" | wc -l | tr -d ' ')")"); fi
echo

echo "### 19. Committed binaries / compiled code (can't be reviewed as source)"
bins="$(cd "$TARGET" && find . -path ./.git -prune -o -type f -size +0 -size -200M -print0 2>/dev/null \
  | xargs -0 file --mime-type 2>/dev/null \
  | "$G" -E ': +application/(x-mach-binary|x-executable|x-sharedlib|x-pie-executable|x-dosexec|vnd\.microsoft\.portable-executable|x-elf|java-archive|wasm|x-object|x-archive|x-xar|x-apple-diskimage|vnd\.debian\.binary-package|x-rpm|x-msi|x-python-code)' \
  | head -n 40)"
if [[ -z "$bins" ]]; then echo "  none"; else echo "$bins" | sed 's/^/  /'; SUMMARY+=("$(printf '%-44s %s' '19. Committed binaries' "$(echo "$bins" | wc -l | tr -d ' ')")"); fi
echo

echo "### 20. Minified / packed code committed as source (lines > 1500 chars)"
mini="$(cd "$TARGET" && find . -path ./.git -prune -o -path ./node_modules -prune -o -type f \
  \( -name '*.js' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.ts' -o -name '*.py' -o -name '*.sh' -o -name '*.rb' -o -name '*.php' -o -name '*.ps1' \) -print 2>/dev/null \
  | while IFS= read -r f; do awk 'length($0)>1500 { print FILENAME "  (line " NR ", " length($0) " chars)"; exit }' "$f"; done | head -n 30)"
if [[ -z "$mini" ]]; then echo "  none"; else echo "$mini" | sed 's/^/  /'; fi
echo

echo "### 21. Code that runs at BUILD/INSTALL time — read every one of these in full"
(cd "$TARGET" && find . -path ./.git -prune -o -path ./node_modules -prune -o -type f \( \
    -name 'build.rs' -o -name 'setup.py' -o -name 'setup.cfg' -o -name 'pyproject.toml' -o -name 'package.json' \
    -o -name 'binding.gyp' -o -name 'Makefile' -o -name 'makefile' -o -name 'GNUmakefile' -o -name 'CMakeLists.txt' \
    -o -name 'Package.swift' -o -name 'build.gradle*' -o -name 'Podfile' -o -name '*.podspec' -o -name 'Dockerfile' \
    -o -name 'install*.sh' -o -name 'install*.ps1' -o -name '*.rb' -path '*Formula*' -o -name '*.rb' -path '*Casks*' \
    -o -name 'Brewfile' -o -name '.envrc' -o -name 'mise.toml' -o -name '.tool-versions' -o -name 'tasks.json' \
    -o -name 'devcontainer.json' -o -name '.pre-commit-config.yaml' -o -name 'go.mod' -o -name 'Cargo.toml' \) -print 2>/dev/null \
  | "$G" -v '/test' | sort | head -n 60 | sed 's/^/  /')
echo "  + release/CI:"; (cd "$TARGET" && ls .github/workflows 2>/dev/null | sed 's/^/    .github\/workflows\//') || true
echo

echo "### 22. Domain inventory — every host referenced in CODE (docs excluded)"
echo "  (classify each: project's own / well-known infra / third-party service / UNKNOWN)"
(cd "$TARGET" && "$G" -rIohE "${EXCL[@]}" "${DOCS[@]}" 'https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}' . 2>/dev/null \
  | sed -E 's#https?://##' | tr 'A-Z' 'a-z' \
  | "$G" -vE '^(www\.)?(w3\.org|schemas\.|xmlns|example\.(com|org)|localhost)' \
  | sort | uniq -c | sort -rn | head -n 80 | awk '{printf "  %5d  %s\n", $1, $2}')
echo

echo "### 23. Who changed install/build/release/network code in the last 12 months"
if git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$TARGET" log --since='12 months ago' --date=short --format='  %h %ad %an <%ae>  %s' -- \
    '*.sh' 'Makefile' 'makefile' '*.rb' 'package.json' 'setup.py' 'pyproject.toml' 'build.rs' \
    '.github/workflows/*' 'Package.swift' '*.gradle' 'Dockerfile' '*install*' '*release*' '*update*' 2>/dev/null \
    | head -n 30
  echo "  -- authors (last 12 months, by commit count):"
  git -C "$TARGET" log --since='12 months ago' --format='%an <%ae>' 2>/dev/null | sort | uniq -c | sort -rn | head -n 12 | sed 's/^/  /'
  echo "  (shallow clone: history limited to fetched depth)"
else
  echo "  no git history available"
fi
echo

echo "== summary: ${total} grep lead(s) =="
printf '  %s\n' "${SUMMARY[@]}"
echo
echo "Resolve EVERY lead (confirm or dismiss with reason). Then read in full: section 21 files,"
echo "entrypoints, and every file with a hit in categories 1-12. grep is the net; reading is the verdict."
