# Runbook: LLM- und Embedding-Konfiguration

**Zuletzt verifiziert:** 2026-03-04
**Ausgeführt von:** Nikolaj Ivanov

---

## Voraussetzungen

- Onyx-Instanz laeuft (alle Pods 1/1 Running)
- Admin-Zugang zur Onyx-UI (`http://<IP>/admin`)
- StackIT AI Model Serving Token vorhanden

---

## 1. StackIT AI Model Serving — Uebersicht

### Endpoint

| Feld | Wert |
|------|------|
| API Base | `https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1` |
| Protokoll | OpenAI-kompatible API (Chat Completions + Embeddings) |
| Auth | Bearer Token (StackIT AI Model Serving Token) |
| Region | EU01 Frankfurt (Daten bleiben in Deutschland) |

### Verfuegbare Modelle (Stand Maerz 2026)

#### Chat-Modelle

| Modell | Model ID | Kontext | Preis (Input/Output) |
|--------|----------|---------|----------------------|
| GPT-OSS 120B | `openai/gpt-oss-120b` | 131K Tokens | 0,45 / 0,65 EUR pro 1M Tokens |
| Qwen3-VL 235B | `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8` | 218K Tokens | 0,45 / 0,65 EUR pro 1M Tokens |
| Llama 3.3 70B | `meta-llama/Llama-3.3-70B-Instruct` | 128K Tokens | — |
| Gemma 3 27B | `google/gemma-3-27b-it` | — | — |
| Mistral-Nemo 12B | `mistralai/Mistral-Nemo-Instruct-2407` | — | — |

> **Hinweis:** In Onyx muss der Provider Name IMMER `openai` sein — unabhaengig vom tatsaechlichen Modell.

#### Embedding-Modelle

| Modell | Model ID | Dimensionen | Kontext | Sprachen |
|--------|----------|-------------|---------|----------|
| **Qwen3-VL-Embedding 8B** | `Qwen/Qwen3-VL-Embedding-8B` | 4096 (flexibel 64-4096) | 32.768 Tokens | 30+ inkl. Deutsch |
| E5 Mistral 7B | `intfloat/e5-mistral-7b-instruct` | 4096 | 4.096 Tokens | **Nur Englisch empfohlen** |

> **Empfehlung:** `Qwen/Qwen3-VL-Embedding-8B` fuer deutsche Dokumente. E5 Mistral ist offiziell nur fuer Englisch empfohlen.

### Token und Zugang

Der StackIT AI Model Serving Token wird im StackIT Portal erstellt:

1. Portal: `https://portal.stackit.cloud`
2. Projekt auswaehlen → AI Model Serving → API Keys
3. Token kopieren (wird nur einmal angezeigt!)

---

## 2. Chat-Modell konfigurieren

### Schritt-fuer-Schritt (Admin UI)

1. **Admin** → **LLM Models** (linke Sidebar unter "Configuration")
2. **Add Provider** → **Custom Models** → "Set Up"
3. Felder ausfuellen:

| Feld | Wert (Beispiel: GPT-OSS 120B) |
|------|-------------------------------|
| Display Name | `StackIT - GPT-OSS` |
| Provider | `openai` |
| API Key | StackIT AI Model Serving Token |
| API Base URL | `https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1` |
| Model Names | `openai/gpt-oss-120b` |
| Default Model | `openai/gpt-oss-120b` |

4. **Submit** → Provider erscheint unter "Available Providers"
5. **Default Model** Dropdown (oben) → auf das gewuenschte Modell setzen

### Zweites Chat-Modell hinzufuegen

Neuen Provider mit anderem Display Name anlegen (gleiche API Base + Key):

| Feld | Wert (Beispiel: Qwen3-VL) |
|------|---------------------------|
| Display Name | `StackIT - Qwen3-VL` |
| Provider | `openai` |
| API Key | Gleicher Token |
| API Base URL | Gleiche URL |
| Model Names | `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8` |
| Default Model | `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8` |

### Validierung

```bash
# API-Test (vom lokalen Rechner oder aus dem Cluster):
curl -s http://<IP>/api/health | jq .
# Erwartung: {"success": true}

# Chat-Test: Im Onyx UI eine Nachricht senden, Modell sollte antworten
```

---

## 3. Embedding-Modell konfigurieren

### Aktueller Status (Stand Maerz 2026)

> **WICHTIG:** Das Wechseln des Embedding-Modells ueber die Admin-UI ist im aktuellen Onyx-Release **temporaer deaktiviert**. Grund: Onyx refactored das Index-Management von Vespa auf OpenSearch (siehe [PR #7541](https://github.com/onyx-dot-app/onyx/pull/7541)). Die Onyx-Entwickler planen die Reaktivierung nach Abschluss der OpenSearch-Migration.
>
> **Workaround:** Das Default-Modell `nomic-ai/nomic-embed-text-v1` (self-hosted, laeuft auf dem Model Server im Cluster) ist automatisch aktiv und funktioniert fuer die Dokumentensuche. Es ist nicht optimal fuer deutsche Texte, aber funktional.

### Ziel-Konfiguration (sobald Upstream re-enabled)

Pfad: **Admin** → **Search Settings** → **Embedding Model**

1. Tab **"Cloud-based"** waehlen
2. **LiteLLM** Provider konfigurieren:

| Feld | Wert |
|------|------|
| API URL | `https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1/embeddings` |
| Model Name (for testing) | `Qwen/Qwen3-VL-Embedding-8B` |
| API Key | StackIT AI Model Serving Token |

> **WICHTIG:** Die API URL muss `/v1/embeddings` enthalten (nicht nur `/v1`). Onyx postet bei LiteLLM-Embeddings direkt an die angegebene URL ohne `/embeddings` anzuhaengen.

3. **Create** → Verbindungstest laeuft automatisch
4. Custom Model definieren:

| Feld | Wert |
|------|------|
| Model Name | `Qwen/Qwen3-VL-Embedding-8B` |
| Model Dimension | `4096` |
| Normalize | `false` |
| Query Prefix | leer |
| Passage Prefix | leer |

5. **Configure LiteLLM Model** → Modell auswaehlen → **Confirm**
6. Advanced Settings: Defaults belassen → **Re-index**
7. Onyx startet automatisches Re-Indexing aller vorhandenen Dokumente

### Unterschied: Chat-API vs. Embedding-API

| Typ | Onyx-Provider | API Endpoint |
|-----|---------------|-------------|
| Chat-Modelle | `openai` (unter LLM Models) | `.../v1/chat/completions` (automatisch) |
| Embedding-Modelle | `litellm` (unter Search Settings) | `.../v1/embeddings` (manuell angeben!) |

> **Nicht verwechseln:** Fuer Chat-Modelle wird der Provider `openai` verwendet (API Base ohne Suffix). Fuer Embedding-Modelle wird `litellm` verwendet, und die URL muss den vollstaendigen Pfad `/v1/embeddings` enthalten.

### Default-Modell (Self-Hosted)

Falls kein Cloud-Embedding konfiguriert ist, nutzt Onyx automatisch `nomic-ai/nomic-embed-text-v1`:

- Laeuft auf dem Model Server Pod im Cluster
- 768 Dimensionen, 8.192 Tokens Kontext
- Multilingual (inkl. Deutsch), aber schwaecher als Qwen3-VL bei nicht-englischen Texten
- Kein externer API-Call noetig (niedrigere Latenz, keine Kosten)

---

## 4. Reranking-Modell (Optional)

Pfad: **Admin** → **Search Settings** → **Reranking Model**

Reranking verbessert die Suchergebnisse, indem es die Top-N Ergebnisse nach Relevanz neu sortiert. Standardmaessig ist kein Reranking aktiv.

StackIT bietet aktuell kein dediziertes Reranking-Modell an. Optionen:

- **Ohne Reranking** (aktuell) — fuer den Start ausreichend
- **Cross-Encoder via LiteLLM** — falls spaeter benoetigt, analog zur Embedding-Konfiguration

---

## 5. Modell-Wechsel — Checkliste

Beim Wechsel eines Chat-Modells:

- [ ] Neuen Provider in Admin UI anlegen
- [ ] Test-Nachricht im Chat senden
- [ ] Default Model Dropdown umstellen (falls gewuenscht)
- [ ] Alte Provider koennen bestehen bleiben (Nutzer koennen pro Chat waehlen)

Beim Wechsel eines Embedding-Modells:

- [ ] **Achtung:** Loest vollstaendiges Re-Indexing aus!
- [ ] Dauer abhaengt von Dokumentenmenge (wenige Dokumente: Minuten, viele: Stunden/Tage)
- [ ] System bleibt waehrend Re-Indexing nutzbar (alte Embeddings werden weiter genutzt)
- [ ] Re-Indexing-Fortschritt unter Search Settings → Embedding Model sichtbar
- [ ] Nach Abschluss: Testsuche durchfuehren, Ergebnisqualitaet pruefen

---

## 6. Troubleshooting

### Chat-Modell antwortet nicht

1. **API-Key pruefen:** Token im StackIT Portal noch gueltig?
2. **Model ID pruefen:** Exakte Schreibweise inkl. Prefix (z.B. `openai/gpt-oss-120b`)
3. **Logs pruefen:**
   ```bash
   kubectl logs -n onyx-dev deployment/onyx-dev-api-server --tail=50 | grep -i llm
   ```
4. **Direkt testen:**
   ```bash
   curl -X POST \
     https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1/chat/completions \
     -H "Authorization: Bearer $STACKIT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hallo"}]}'
   ```

### Embedding-Test schlaegt fehl

1. **URL pruefen:** Muss `/v1/embeddings` sein (nicht `/v1`)
2. **Direkt testen:**
   ```bash
   curl -X POST \
     https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1/embeddings \
     -H "Authorization: Bearer $STACKIT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"model": "Qwen/Qwen3-VL-Embedding-8B", "input": ["Testtext"]}'
   ```
3. **Erwartete Antwort:** JSON mit `data[0].embedding` (Array mit 4096 Floats)

### "Setting new search settings is temporarily disabled"

Dieses Verhalten ist **kein Bug**, sondern eine bewusste Deaktivierung im Upstream-Code (Onyx [PR #7541](https://github.com/onyx-dot-app/onyx/pull/7541)). Onyx migriert von Vespa auf OpenSearch und hat den Embedding-Modell-Wechsel temporaer gesperrt.

**Was tun:**
- Das Default-Modell `nomic-embed-text-v1` weiter nutzen
- Bei jedem Upstream-Merge pruefen ob der Endpoint reaktiviert wurde
- Status verfolgen: [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) → Search Settings PRs

### Rate Limits (StackIT)

| Limit | Wert |
|-------|------|
| Chat: Tokens pro Minute | 200.000 TPM |
| Chat: Requests pro Minute | 600 RPM |
| Embedding: Tokens pro Minute | 200.000 TPM |
| Embedding: Requests pro Minute | 600 RPM |

Bei Rate-Limit-Fehlern (HTTP 429): Indexing-Geschwindigkeit in Onyx ist normalerweise niedrig genug. Falls doch Probleme: Batch-Groesse der Embedding-Requests in Onyx reduzieren (erfordert Code-Aenderung).

---

## 7. Umgebungsspezifische Konfiguration

| Feld | DEV | TEST | PROD |
|------|-----|------|------|
| URL | `http://188.34.74.187` | `http://188.34.118.201` | TBD |
| Chat Default | GPT-OSS 120B | GPT-OSS 120B | TBD |
| Embedding | nomic-embed-text-v1 (self-hosted) | nomic-embed-text-v1 (self-hosted) | TBD |
| Embedding (Ziel) | Qwen3-VL-Embedding 8B (StackIT) | Qwen3-VL-Embedding 8B (StackIT) | TBD |

> **Hinweis:** Die LLM-Konfiguration erfolgt **pro Umgebung separat** ueber die Admin-UI. Es gibt keine Helm-Values dafuer — die Einstellungen werden in der PostgreSQL-Datenbank gespeichert.

---

## Referenzen

- [StackIT AI Model Serving Docs](https://docs.stackit.cloud/products/data-and-ai/ai-model-serving/)
- [Verfuegbare Modelle](https://docs.stackit.cloud/products/data-and-ai/ai-model-serving/basics/available-shared-models/)
- [StackIT Release Notes](https://docs.stackit.cloud/products/data-and-ai/ai-model-serving/release-notes/)
- [Qwen3-VL-Embedding-8B (Hugging Face)](https://huggingface.co/Qwen/Qwen3-VL-Embedding-8B)
- [Onyx PR #7541 — Secondary Indices Disabled](https://github.com/onyx-dot-app/onyx/pull/7541)
- [Helm Deploy Runbook](./helm-deploy.md)
