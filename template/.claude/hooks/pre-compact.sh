#!/bin/bash
[ -n "${MNEME_INVOKED_BY:-}" ] && exit 0
# Detach a pre-compaction flush without changing live session state.

MNEME_HOOK_DIR=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd)
. "$MNEME_HOOK_DIR/lib.sh" 2>/dev/null || exit 0

MNEME_HOOK_INPUT="$MNEME_STATE_DIR/hookin-$$.json"
umask 077
if ! cat > "$MNEME_HOOK_INPUT" 2>/dev/null; then
  rm -f "$MNEME_HOOK_INPUT" 2>/dev/null || :
  MNEME_HOOK_INPUT=""
fi

if [ -n "$MNEME_HOOK_INPUT" ]; then
  if command -v python3 >/dev/null 2>&1; then
    nohup python3 "$MNEME_PROJECT_DIR/.claude/scripts/flush.py" \
      --hook-input "$MNEME_HOOK_INPUT" --reason precompact >/dev/null 2>&1 &
  else
    mneme_mark_python_missing
    rm -f "$MNEME_HOOK_INPUT" 2>/dev/null || :
    mneme_emit PreCompact 'Mneme sıkıştırma öncesi özeti başlatılamadı: python3 bulunamadı. mneme-doktor çalıştır.'
  fi
fi
exit 0
