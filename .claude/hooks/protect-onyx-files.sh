#!/bin/bash
# Claude Code Hook: Blockiert Änderungen an Onyx-Dateien (deterministisch)
# Triggert bei Edit/Write Tool — Exit Code 2 = Aktion blockieren

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty')

# Kein Dateipfad → durchlassen
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Erlaubte Verzeichnisse (unser Code)
if [[ "$FILE_PATH" == */backend/ext/* ]] || \
   [[ "$FILE_PATH" == */web/src/ext/* ]] || \
   [[ "$FILE_PATH" == */docs/* ]] || \
   [[ "$FILE_PATH" == */.claude/* ]] || \
   [[ "$FILE_PATH" == */.github/* ]] || \
   [[ "$FILE_PATH" == */.githooks/* ]] || \
   [[ "$FILE_PATH" == */deployment/docker_compose/.env* ]]; then
  exit 0  # Erlaubt
fi

# 7 erlaubte Core-Dateien (korrigierte Pfade, Stand 2026-02-12)
ALLOWED_CORE=(
  "backend/onyx/main.py"
  "backend/onyx/llm/multi_llm.py"
  "backend/onyx/access/access.py"
  "backend/onyx/chat/prompt_utils.py"
  "web/src/app/layout.tsx"
  "web/src/components/header/"
  "web/src/lib/constants.ts"
)

for allowed in "${ALLOWED_CORE[@]}"; do
  if [[ "$FILE_PATH" == *"$allowed"* ]]; then
    exit 0  # Core-Datei — erlaubt (mit Vorsicht)
  fi
done

# Onyx-Code? → BLOCKIEREN
if [[ "$FILE_PATH" == */backend/onyx/* ]] || \
   [[ "$FILE_PATH" == */web/src/app/* ]] || \
   [[ "$FILE_PATH" == */web/src/components/* ]] || \
   [[ "$FILE_PATH" == */web/src/lib/* ]]; then
  echo "❌ BLOCKIERT: $FILE_PATH gehört zum Onyx-Core und darf nicht verändert werden." >&2
  echo "Erlaubt sind nur: backend/ext/, web/src/ext/, docs/, und die 7 definierten Core-Dateien." >&2
  exit 2  # Exit 2 = Aktion wird deterministisch blockiert
fi

# Alles andere durchlassen
exit 0
