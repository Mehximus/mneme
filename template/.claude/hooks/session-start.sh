#!/bin/bash
[ -n "${MNEME_INVOKED_BY:-}" ] && exit 0
# Inject relational memory, rules, recent journal context, and the knowledge index.

MNEME_HOOK_DIR=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd)
. "$MNEME_HOOK_DIR/lib.sh" 2>/dev/null || exit 0

MNEME_MEMORY_DIR="$MNEME_PROJECT_DIR/🔮 850-Companion"
mkdir -p "$MNEME_STATE_DIR" 2>/dev/null || :
mneme_cleanup_session_state

MNEME_SESSION_KEY=$(mneme_session_key 2>/dev/null || :)
if [ -n "$MNEME_SESSION_KEY" ]; then
  MNEME_SESSION_START_FILE="$MNEME_STATE_DIR/session_start_time.$MNEME_SESSION_KEY"
  MNEME_PROMPT_COUNT_FILE="$MNEME_STATE_DIR/prompt_count.$MNEME_SESSION_KEY"
  date '+%s' > "$MNEME_SESSION_START_FILE" 2>/dev/null || :
  printf '%s\n' 0 > "$MNEME_PROMPT_COUNT_FILE" 2>/dev/null || :
fi

MNEME_LAST_SESSION=""
if [ -f "$MNEME_MEMORY_DIR/Last-Session.md" ]; then
  MNEME_LAST_SESSION=$(awk '
    /^## Session:/ { active = 1 }
    active && /^## Previous/ { exit }
    active { print }
  ' "$MNEME_MEMORY_DIR/Last-Session.md" 2>/dev/null | sed -n '1,50p')
fi

MNEME_THREADS=""
if [ -f "$MNEME_MEMORY_DIR/Threads.md" ]; then
  MNEME_THREADS=$(sed -n '/^## Active/,/^## Closed/p' "$MNEME_MEMORY_DIR/Threads.md" 2>/dev/null \
    | grep -E '^### |^\*\*Status:\*\*' 2>/dev/null \
    | sed -n '1,12p')
fi

MNEME_RULES=""
if [ -f "$MNEME_MEMORY_DIR/Kurallar.md" ]; then
  MNEME_RULES=$(sed -n '1,60p' "$MNEME_MEMORY_DIR/Kurallar.md" 2>/dev/null)
fi

MNEME_JOURNAL=""
if [ -f "$MNEME_MEMORY_DIR/Journal.md" ]; then
  MNEME_JOURNAL_LINE=$(grep -n '^## ' "$MNEME_MEMORY_DIR/Journal.md" 2>/dev/null \
    | tail -n 1 | cut -d: -f1)
  case "$MNEME_JOURNAL_LINE" in
    ''|*[!0-9]*) ;;
    *)
      MNEME_JOURNAL_END=$((MNEME_JOURNAL_LINE + 9))
      MNEME_JOURNAL=$(sed -n "${MNEME_JOURNAL_LINE},${MNEME_JOURNAL_END}p" \
        "$MNEME_MEMORY_DIR/Journal.md" 2>/dev/null)
      ;;
  esac
fi

MNEME_INDEX=""
if [ -f "$MNEME_PROJECT_DIR/knowledge/index.md" ]; then
  MNEME_INDEX=$(sed -n '1,150p' "$MNEME_PROJECT_DIR/knowledge/index.md" 2>/dev/null)
fi

MNEME_DAILY=""
MNEME_TODAY=$(date '+%Y-%m-%d' 2>/dev/null || :)
MNEME_DAILY_FILE=""
if [ -n "$MNEME_TODAY" ] && [ -f "$MNEME_PROJECT_DIR/daily/$MNEME_TODAY.md" ]; then
  MNEME_DAILY_FILE="$MNEME_PROJECT_DIR/daily/$MNEME_TODAY.md"
else
  MNEME_YESTERDAY=$(mneme_yesterday)
  if [ -n "$MNEME_YESTERDAY" ] && [ -f "$MNEME_PROJECT_DIR/daily/$MNEME_YESTERDAY.md" ]; then
    MNEME_DAILY_FILE="$MNEME_PROJECT_DIR/daily/$MNEME_YESTERDAY.md"
  fi
fi
[ -n "$MNEME_DAILY_FILE" ] && MNEME_DAILY=$(tail -n 25 "$MNEME_DAILY_FILE" 2>/dev/null)

MNEME_NL='
'
MNEME_REFLECTION=""
for MNEME_REFLECTION_FILE in \
  "$MNEME_STATE_DIR/needs_reflection" \
  "$MNEME_STATE_DIR"/needs_reflection.*
do
  [ -f "$MNEME_REFLECTION_FILE" ] || continue
  MNEME_REFLECTION_DETAIL=$(sed -n '1p' "$MNEME_REFLECTION_FILE" 2>/dev/null || :)
  if [ -n "$MNEME_REFLECTION_DETAIL" ]; then
    [ -n "$MNEME_REFLECTION" ] && MNEME_REFLECTION="${MNEME_REFLECTION}${MNEME_NL}"
    MNEME_REFLECTION="${MNEME_REFLECTION}⚠️ Önceki oturum hafıza güncellemeden bitti: ${MNEME_REFLECTION_DETAIL}. Anlamlı bir şey olduysa 🔮 850-Companion dosyalarını güncelle."
  fi
  rm -f "$MNEME_REFLECTION_FILE" 2>/dev/null || :
done

# Hard section entry caps, including truncation notes: Last Session 4000,
# Threads 2000, Kurallar 4000, Journal 1500, reflection debt 1000 characters.
mneme_cap_section() {
  MNEME_CAP_VALUE=$1
  MNEME_CAP_LIMIT=$2
  MNEME_CAP_NOTE=$3
  if [ "${#MNEME_CAP_VALUE}" -le "$MNEME_CAP_LIMIT" ]; then
    printf '%s' "$MNEME_CAP_VALUE"
    return 0
  fi

  MNEME_CAP_KEEP=$((MNEME_CAP_LIMIT - ${#MNEME_CAP_NOTE} - 1))
  [ "$MNEME_CAP_KEEP" -gt 0 ] || MNEME_CAP_KEEP=0
  printf '%s\n%s' "${MNEME_CAP_VALUE:0:$MNEME_CAP_KEEP}" "$MNEME_CAP_NOTE"
}

MNEME_LAST_SESSION=$(mneme_cap_section "$MNEME_LAST_SESSION" 4000 \
  '[not: son oturum 4.000 karakterde kırpıldı, mneme-doktor çalıştır]')
MNEME_THREADS=$(mneme_cap_section "$MNEME_THREADS" 2000 \
  '[not: aktif konular 2.000 karakterde kırpıldı, mneme-doktor çalıştır]')
MNEME_RULES=$(mneme_cap_section "$MNEME_RULES" 4000 \
  '[not: kurallar 4.000 karakterde kırpıldı, mneme-doktor çalıştır]')
MNEME_JOURNAL=$(mneme_cap_section "$MNEME_JOURNAL" 1500 \
  '[not: son Journal 1.500 karakterde kırpıldı, mneme-doktor çalıştır]')
MNEME_REFLECTION=$(mneme_cap_section "$MNEME_REFLECTION" 1000 \
  '[not: hafıza uyarıları 1.000 karakterde kırpıldı, mneme-doktor çalıştır]')

MNEME_TRUNCATED=0
MNEME_CLOSING='[Hafıza] Süreklilik senin sorumluluğun. Bu kullanıcı için kim olduğunu anlamak üzere 🔮 850-Companion/Core.md dosyasını oku.
Hafıza protokolü zorunludur.'
MNEME_TRUNCATION_NOTE='[not: indeks kırpıldı, mneme-doktor çalıştır]'
MNEME_CAP_DIAGNOSTIC='Mneme uyarısı: Oturum başlangıç bağlamı 16.000 karakter sınırına sığmadı. Bölüm limitlerini kontrol etmek için mneme-doktor çalıştır.'

mneme_build_context() {
  MNEME_CONTEXT=""
  [ -n "$MNEME_REFLECTION" ] && MNEME_CONTEXT="${MNEME_CONTEXT}${MNEME_REFLECTION}${MNEME_NL}${MNEME_NL}"
  [ -n "$MNEME_LAST_SESSION" ] && MNEME_CONTEXT="${MNEME_CONTEXT}[Hafıza: Son Oturum]${MNEME_NL}${MNEME_LAST_SESSION}${MNEME_NL}${MNEME_NL}"
  [ -n "$MNEME_THREADS" ] && MNEME_CONTEXT="${MNEME_CONTEXT}[Hafıza: Aktif Konular]${MNEME_NL}${MNEME_THREADS}${MNEME_NL}${MNEME_NL}"
  [ -n "$MNEME_RULES" ] && MNEME_CONTEXT="${MNEME_CONTEXT}[Hafıza: Kurallar]${MNEME_NL}${MNEME_RULES}${MNEME_NL}${MNEME_NL}"
  [ -n "$MNEME_JOURNAL" ] && MNEME_CONTEXT="${MNEME_CONTEXT}[Hafıza: Son Journal]${MNEME_NL}${MNEME_JOURNAL}${MNEME_NL}${MNEME_NL}"
  [ -n "$MNEME_INDEX" ] && MNEME_CONTEXT="${MNEME_CONTEXT}[Bilgi Tabanı: İndeks]${MNEME_NL}${MNEME_INDEX}${MNEME_NL}${MNEME_NL}"
  [ -n "$MNEME_DAILY" ] && MNEME_CONTEXT="${MNEME_CONTEXT}[Bugünün Logu]${MNEME_NL}${MNEME_DAILY}${MNEME_NL}${MNEME_NL}"
  [ "$MNEME_TRUNCATED" -eq 1 ] && MNEME_CONTEXT="${MNEME_CONTEXT}${MNEME_TRUNCATION_NOTE}${MNEME_NL}${MNEME_NL}"
  MNEME_CONTEXT="${MNEME_CONTEXT}${MNEME_CLOSING}"
}

mneme_build_context
if [ "${#MNEME_CONTEXT}" -gt 16000 ]; then
  MNEME_TRUNCATED=1
  mneme_build_context

  MNEME_OVER=$(( ${#MNEME_CONTEXT} - 16000 ))
  if [ "$MNEME_OVER" -gt 0 ] && [ -n "$MNEME_INDEX" ]; then
    if [ "$MNEME_OVER" -ge "${#MNEME_INDEX}" ]; then
      MNEME_INDEX=""
    else
      MNEME_KEEP=$(( ${#MNEME_INDEX} - MNEME_OVER ))
      MNEME_INDEX=${MNEME_INDEX:0:$MNEME_KEEP}
    fi
    mneme_build_context
  fi

  MNEME_OVER=$(( ${#MNEME_CONTEXT} - 16000 ))
  if [ "$MNEME_OVER" -gt 0 ] && [ -n "$MNEME_DAILY" ]; then
    if [ "$MNEME_OVER" -ge "${#MNEME_DAILY}" ]; then
      MNEME_DAILY=""
    else
      MNEME_DAILY=${MNEME_DAILY:$MNEME_OVER}
    fi
    mneme_build_context
  fi

  # Journal and reflection are the only remaining non-protected sections.
  MNEME_OVER=$(( ${#MNEME_CONTEXT} - 16000 ))
  if [ "$MNEME_OVER" -gt 0 ] && [ -n "$MNEME_JOURNAL" ]; then
    if [ "$MNEME_OVER" -ge "${#MNEME_JOURNAL}" ]; then
      MNEME_JOURNAL=""
    else
      MNEME_KEEP=$(( ${#MNEME_JOURNAL} - MNEME_OVER ))
      MNEME_JOURNAL=${MNEME_JOURNAL:0:$MNEME_KEEP}
    fi
    mneme_build_context
  fi

  MNEME_OVER=$(( ${#MNEME_CONTEXT} - 16000 ))
  if [ "$MNEME_OVER" -gt 0 ] && [ -n "$MNEME_REFLECTION" ]; then
    if [ "$MNEME_OVER" -ge "${#MNEME_REFLECTION}" ]; then
      MNEME_REFLECTION=""
    else
      MNEME_KEEP=$(( ${#MNEME_REFLECTION} - MNEME_OVER ))
      MNEME_REFLECTION=${MNEME_REFLECTION:0:$MNEME_KEEP}
    fi
    mneme_build_context
  fi
fi

if [ "${#MNEME_CONTEXT}" -gt 16000 ]; then
  MNEME_CONTEXT=$MNEME_CAP_DIAGNOSTIC
fi

[ -n "$MNEME_CONTEXT" ] && mneme_emit SessionStart "$MNEME_CONTEXT"

# The evening compile is triggered from SessionEnd, which means a day whose last
# session closes before 18:00 never reaches it and its log sits uncompiled. Fire
# the catch-up pass here, detached and after the context is already emitted so it
# can neither delay the session nor corrupt the hook's JSON on stdout. flush.py
# decides whether anything is actually due; the call is cheap when it is not.
if command -v python3 >/dev/null 2>&1; then
  nohup python3 "$MNEME_PROJECT_DIR/.claude/scripts/flush.py" \
    --maybe-compile >/dev/null 2>&1 &
fi

exit 0
