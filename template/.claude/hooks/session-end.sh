#!/bin/bash
[ -n "${MNEME_INVOKED_BY:-}" ] && exit 0
# Mark relational-memory debt, then detach the automatic session flush.

MNEME_HOOK_DIR=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd)
. "$MNEME_HOOK_DIR/lib.sh" 2>/dev/null || exit 0

MNEME_HOOK_INPUT="$MNEME_STATE_DIR/hookin-$$.json"
umask 077
if ! cat > "$MNEME_HOOK_INPUT" 2>/dev/null; then
  rm -f "$MNEME_HOOK_INPUT" 2>/dev/null || :
  MNEME_HOOK_INPUT=""
fi

MNEME_SESSION_KEY=""
if [ -n "$MNEME_HOOK_INPUT" ]; then
  MNEME_SESSION_KEY=$(mneme_session_key < "$MNEME_HOOK_INPUT" 2>/dev/null || :)
fi

MNEME_MEMORY_DIR="$MNEME_PROJECT_DIR/🔮 850-Companion"
MNEME_START=0
MNEME_PROMPTS=0
MNEME_SESSION_START_FILE=""
MNEME_PROMPT_COUNT_FILE=""
MNEME_REFLECTION_FILE=""
if [ -n "$MNEME_SESSION_KEY" ]; then
  MNEME_SESSION_START_FILE="$MNEME_STATE_DIR/session_start_time.$MNEME_SESSION_KEY"
  MNEME_PROMPT_COUNT_FILE="$MNEME_STATE_DIR/prompt_count.$MNEME_SESSION_KEY"
  MNEME_REFLECTION_FILE="$MNEME_STATE_DIR/needs_reflection.$MNEME_SESSION_KEY"
  [ -f "$MNEME_SESSION_START_FILE" ] && MNEME_START=$(sed -n '1p' "$MNEME_SESSION_START_FILE" 2>/dev/null || :)
  [ -f "$MNEME_PROMPT_COUNT_FILE" ] && MNEME_PROMPTS=$(sed -n '1p' "$MNEME_PROMPT_COUNT_FILE" 2>/dev/null || :)
fi
case "$MNEME_START" in ''|*[!0-9]*) MNEME_START=0 ;; esac
case "$MNEME_PROMPTS" in ''|*[!0-9]*) MNEME_PROMPTS=0 ;; esac

MNEME_MODIFIED=0
if [ -f "$MNEME_MEMORY_DIR/Last-Session.md" ]; then
  MNEME_FILE_MTIME=$(mneme_mtime "$MNEME_MEMORY_DIR/Last-Session.md")
  case "$MNEME_FILE_MTIME" in ''|*[!0-9]*) MNEME_FILE_MTIME=0 ;; esac
  [ "$MNEME_FILE_MTIME" -gt "$MNEME_START" ] 2>/dev/null && MNEME_MODIFIED=1
fi

if [ "$MNEME_PROMPTS" -ge 5 ] && [ "$MNEME_MODIFIED" -eq 0 ] && [ -n "$MNEME_REFLECTION_FILE" ]; then
  printf 'Oturum hafıza güncellemeden bitti. Prompt: %s. %s\n' \
    "$MNEME_PROMPTS" "$(date '+%Y-%m-%d %H:%M' 2>/dev/null)" \
    > "$MNEME_REFLECTION_FILE" 2>/dev/null || :
fi

if [ -n "$MNEME_HOOK_INPUT" ]; then
  if command -v python3 >/dev/null 2>&1; then
    nohup python3 "$MNEME_PROJECT_DIR/.claude/scripts/flush.py" \
      --hook-input "$MNEME_HOOK_INPUT" >/dev/null 2>&1 &
  else
    mneme_mark_python_missing
    rm -f "$MNEME_HOOK_INPUT" 2>/dev/null || :
    mneme_emit SessionEnd 'Mneme arka plan özeti başlatılamadı: python3 bulunamadı. mneme-doktor çalıştır.'
  fi
fi

[ -n "$MNEME_SESSION_START_FILE" ] && rm -f "$MNEME_SESSION_START_FILE" 2>/dev/null || :
[ -n "$MNEME_PROMPT_COUNT_FILE" ] && rm -f "$MNEME_PROMPT_COUNT_FILE" 2>/dev/null || :
exit 0
