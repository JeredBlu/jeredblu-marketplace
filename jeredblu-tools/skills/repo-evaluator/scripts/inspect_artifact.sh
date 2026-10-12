#!/usr/bin/env bash
#
# inspect_artifact.sh — look inside a downloaded release artifact WITHOUT running it.
#
# SAFETY CONTRACT (do not weaken):
#   * Never opens, launches, installs, or double-clicks anything.
#   * .pkg: `pkgutil --expand-full` unpacks WITHOUT running install scripts — we then
#     READ those scripts (they run as root on a real install).
#   * .dmg: attached read-only, no auto-open, not shown in Finder, then detached.
#   * codesign/spctl/otool/strings only read the file. spctl --assess evaluates policy;
#     it does not execute the binary.
#   * The artifact must already be in a temp dir (e.g. `gh release download -D "$(mktemp -d)"`)
#     and the user must have OK'd the download.
#
# Usage: inspect_artifact.sh <file> [source_checkout_dir]
#   With a checkout dir, domains found in the binary are diffed against domains in source:
#   a host that appears ONLY in the binary is a red flag (binary ≠ reviewed source).

set -uo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
F="${1:-}"; SRC="${2:-}"
[[ -f "$F" || -d "$F" ]] || { echo "usage: inspect_artifact.sh <file> [source_checkout_dir]" >&2; exit 2; }
F="$(cd -- "$(dirname -- "$F")" && pwd)/$(basename -- "$F")"
INCOMPLETE=0
for tool in file shasum strings codesign spctl otool plutil; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "NOT PERFORMED: $tool unavailable; affected artifact checks remain incomplete." >&2
    INCOMPLETE=1
  fi
done
G=/usr/bin/grep; [[ -x "$G" ]] || G="$(command -v grep)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/artifact.XXXXXX")"
MNT=""
cleanup() { if [[ -n "$MNT" ]]; then hdiutil detach -quiet "$MNT" 2>/dev/null || echo "WARN: detach failed: $MNT" >&2; fi; }
trap cleanup EXIT

echo "== repo-evaluator :: artifact inspection (nothing is executed) =="
echo "file:   $F"
[[ -f "$F" ]] && echo "sha256: $(shasum -a 256 "$F" | cut -d' ' -f1)   size: $(du -h "$F" | cut -f1)"
[[ -f "$F" ]] && echo "type:   $(file -b "$F" | cut -c1-100)"

ROOT="$F"
case "$F" in
  *.zip)
    python3 -I "$SCRIPT_DIR/safe_archive.py" "$F" "$WORK/extracted" || exit 3
    ROOT="$WORK/extracted" ;;
  *.tar.gz|*.tgz|*.tar.xz|*.tar.bz2|*.tar)
    python3 -I "$SCRIPT_DIR/safe_archive.py" "$F" "$WORK/extracted" || exit 3
    ROOT="$WORK/extracted" ;;
  *.dmg)
    echo; echo "### dmg (attached read-only, no auto-open)"
    MNT="$WORK/mnt"; mkdir -p "$MNT"
    hdiutil attach -readonly -nobrowse -noautoopen -mountpoint "$MNT" "$F" >/dev/null 2>&1 \
      || { echo "ARTIFACT INSPECTION BLOCKED: attach failed" >&2; exit 3; }
    ROOT="$MNT" ;;
  *.pkg)
    echo; echo "### pkg — install scripts (these run as ROOT on install; read them in full)"
    pkgutil --expand-full "$F" "$WORK/pkg" 2>/dev/null \
      || { echo "ARTIFACT INSPECTION BLOCKED: pkg expansion failed" >&2; exit 3; }
    find "$WORK/pkg" -type f \( -name 'preinstall' -o -name 'postinstall' -o -name 'preflight' -o -name 'postflight' -o -path '*Scripts*' \) \
      | head -n 20 | sed 's/^/  /'
    pkgutil --check-signature "$F" 2>&1 | head -n 8 | sed 's/^/  /'
    ROOT="$WORK/pkg" ;;
esac

echo; echo "### Code signatures & notarization (per app bundle / Mach-O)"
if [[ "$(uname -s)" != Darwin ]]; then
  echo "NOT PERFORMED: macOS signature/notarization/linked-library checks unavailable on this host."
fi
TARGETS="$(find "$ROOT" -maxdepth 4 -name '*.app' -type d 2>/dev/null | head -n 5)"
[[ -z "$TARGETS" ]] && TARGETS="$(find "$ROOT" -type f -size +10k 2>/dev/null | head -n 400 \
  | xargs file --mime-type 2>/dev/null | "$G" -E 'x-mach-binary|x-executable|x-sharedlib|x-pie-executable|x-dosexec' | sed 's/: .*//' | head -n 5)"
while IFS= read -r t; do
  [[ -z "$t" ]] && continue
  echo "  -- $t"
  codesign -dv --verbose=2 "$t" 2>&1 | "$G" -E 'Identifier|Authority|TeamIdentifier|Signature|Timestamp|flags' | sed 's/^/     /'
  echo "     entitlements:"; codesign -d --entitlements - --xml "$t" 2>/dev/null | plutil -p - 2>/dev/null | sed 's/^/       /' | head -n 20
  echo "     gatekeeper: $(spctl -a -vv -t exec "$t" 2>&1 | tr '\n' ' ' | cut -c1-160)"
  if [[ -d "$t" ]]; then
    plist="$t/Contents/Info.plist"
    [[ -f "$plist" ]] && plutil -p "$plist" 2>/dev/null | "$G" -E 'CFBundleIdentifier|CFBundleShortVersion|LSUIElement|SUFeedURL|NS[A-Za-z]+UsageDescription' | sed 's/^/     /'
    ls "$t/Contents/Library/LaunchServices" "$t/Contents/Library/LoginItems" "$t/Contents/Library/SystemExtensions" 2>/dev/null | sed 's/^/     bundled helper: /'
  fi
done <<< "$TARGETS"

echo; echo "### Linked libraries (unexpected dylibs require investigation; not proof of injection)"
while IFS= read -r t; do
  [[ -z "$t" ]] && continue
  bin="$t"; [[ -d "$t" ]] && bin="$t/Contents/MacOS/$(plutil -extract CFBundleExecutable raw "$t/Contents/Info.plist" 2>/dev/null)"
  [[ -f "$bin" ]] && otool -L "$bin" 2>/dev/null | tail -n +2 | "$G" -vE '^\s*/(System|usr/lib)/' | head -n 20 | sed 's/^/  /'
done <<< "$TARGETS"

echo; echo "### Hosts embedded in the binaries"
find "$ROOT" -type f -size +1k 2>/dev/null | head -n 2000 | while IFS= read -r f; do strings -a "$f" 2>/dev/null; done \
  | "$G" -oE 'https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}' | sed -E 's#https?://##' | tr 'A-Z' 'a-z' | sort -u > "$WORK/bin_hosts"
sed 's/^/  /' "$WORK/bin_hosts" | "$G" -vE '(apple\.com|w3\.org|openssl\.org|swift\.org)$' | head -n 60
if [[ -n "$SRC" && -d "$SRC" ]]; then
  "$G" -rIohE --exclude-dir=.git 'https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$SRC" 2>/dev/null \
    | sed -E 's#https?://##' | tr 'A-Z' 'a-z' | sort -u > "$WORK/src_hosts"
  echo; echo "### Hosts in BINARY but NOT in source (red flag unless explained by a dependency/SDK)"
  comm -23 "$WORK/bin_hosts" "$WORK/src_hosts" | "$G" -vE '(apple\.com|w3\.org|openssl\.org|swift\.org|github\.com)$' | sed 's/^/  /' | head -n 40
fi
echo; echo "== end artifact inspection =="
echo "LIMITS: up to 5 signature targets, 400 candidate files, 2000 files for embedded hosts. This is not proof of source/binary equivalence."
echo "Inspection scratch (remove after saving needed evidence): $WORK"
if [[ "$INCOMPLETE" == 1 ]]; then exit 3; fi
