#!/bin/bash
[ -n "${MNEME_INVOKED_BY:-}" ] && exit 0
# Count prompts and nudge at every multiple of fifteen.

MNEME_HOOK_DIR=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd)
. "$MNEME_HOOK_DIR/lib.sh" 2>/dev/null || exit 0

MNEME_SESSION_KEY=$(mneme_session_key 2>/dev/null || :)
[ -n "$MNEME_SESSION_KEY" ] || exit 0

MNEME_PROMPT_COUNT_FILE="$MNEME_STATE_DIR/prompt_count.$MNEME_SESSION_KEY"
MNEME_LOCK_DIR="$MNEME_PROMPT_COUNT_FILE.lock"
MNEME_LOCK_ATTEMPT=0
while ! mkdir "$MNEME_LOCK_DIR" 2>/dev/null; do
  MNEME_LOCK_ATTEMPT=$((MNEME_LOCK_ATTEMPT + 1))
  [ "$MNEME_LOCK_ATTEMPT" -lt 500 ] || exit 0
  sleep 0.01 2>/dev/null || sleep 1 2>/dev/null || exit 0
done
trap 'rmdir "$MNEME_LOCK_DIR" 2>/dev/null || :' EXIT
trap 'exit 0' HUP INT TERM

MNEME_COUNT=0
if [ -f "$MNEME_PROMPT_COUNT_FILE" ]; then
  MNEME_COUNT=$(sed -n '1p' "$MNEME_PROMPT_COUNT_FILE" 2>/dev/null || :)
fi
case "$MNEME_COUNT" in
  ''|*[!0-9]*) MNEME_COUNT=0 ;;
esac

MNEME_COUNT=$((MNEME_COUNT + 1))
MNEME_COUNT_TMP="$MNEME_PROMPT_COUNT_FILE.tmp.$$"
if printf '%s\n' "$MNEME_COUNT" > "$MNEME_COUNT_TMP" 2>/dev/null; then
  mv -f "$MNEME_COUNT_TMP" "$MNEME_PROMPT_COUNT_FILE" 2>/dev/null || :
fi
rm -f "$MNEME_COUNT_TMP" 2>/dev/null || :
rmdir "$MNEME_LOCK_DIR" 2>/dev/null || :
trap - EXIT HUP INT TERM

if [ $((MNEME_COUNT % 15)) -eq 0 ]; then
  mneme_emit UserPromptSubmit "[Hafıza] $MNEME_COUNT. mesaj. Oturum sonunda 🔮 850-Companion/Last-Session.md ve Threads.md güncellemeyi unutma."
fi
exit 0
