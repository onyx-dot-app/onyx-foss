# ADR-001: Onyx FOSS als Basis-Plattform

**Status**: Akzeptiert
**Aktualisiert**: 2026-02-12
**Author**: CCJ / Coffee Studios

---

## Context

Die VÖB benötigt einen **Enterprise-AI-Chatbot** für die deutsche Bankenwirtschaft mit folgenden Anforderungen:

### Business Requirements
- Retrieval-Augmented Generation (RAG) Capabilities
- Skalierbar auf deutsche Bankenmitglieder
- Datenschutz und Datensouveränität (EU/Deutschland)
- Kostenkontrollierbar (Token-Limits für LLM-Nutzung)
- Schnelle Time-to-Market

### Technische Anforderungen
- Open Source oder proprietary
- Modern Stack (Python/FastAPI Backend, Next.js/React Frontend, Kubernetes)
- Gut dokumentiert und wartbar
- Community-Support oder kommerzieller Support
- RAG + Vector Search Capabilities

### Entscheidungs-Alternativen
Die folgenden Optionen waren zur Diskussion:

1. **Komplett Custom-Entwicklung**: Von Grund auf neu bauen
2. **Open Source Basis**: LibreChat, Onyx FOSS, oder ähnlich
3. **Kommerzielle SaaS**: OpenAI Platform, Microsoft Copilot Studio, etc.

---

## Decision

**Wir wählen Onyx FOSS als Basis-Plattform für den VÖB Service Chatbot.**

### Implementierungs-Details

```
┌─────────────────────────────────────────────────────────────────┐
│ VÖB Service Chatbot (Zielarchitektur)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Onyx FOSS (MIT-Lizenz)                                  │   │
│  │ - Conversation Management                               │   │
│  │ - RAG Engine (Vespa Integration)                         │   │
│  │ - Web UI / Chat Interface                               │   │
│  │ - Base User Management                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Custom Extension Layer (VÖB-Specific)                   │   │
│  │ - Authentifizierung (Entra ID / OIDC)                   │   │
│  │ - Token Limits Management                               │   │
│  │ - RBAC via ext_user_groups                              │   │
│  │ - Branding & Theming                                    │   │
│  │ - System Prompts Management                             │   │
│  │ - Analytics & Reporting                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Onyx FOSS Auswahl

**Onyx** ist ein moderne, Open Source AI Chatbot Plattform mit:

- **Lizenz**: MIT (vollständig Open Source)
- **Basis-Tech**: Node.js / Next.js (Frontend), Python (Backend)
- **Kern-Features**:
  - RAG mit Vespa Vektorspeicher
  - Multi-Conversation Support
  - Benutzer- und Organisationsverwaltung
  - Erweiterbare Architektur
- **Datenspeicherung**: PostgreSQL (Datenbank), Vespa (Vector Store)
- **Deployment**: Container-ready (Docker), Kubernetes-fähig
- **Community**: Aktive Entwicklung, regelmäßige Updates

### Lizenz & IP-Considerations

- **Onyx FOSS**: MIT License (Erlaubt kommerzielle Nutzung, Modifikationen, Redistributions)
- **Enterprise Extensions**: Können proprietär entwickelt werden
- **IP-Schutz**: Custom Code bleibt bei Auftragnehmer (CCJ / Coffee Studios) oder VÖB
- **Upstream Contributions**: Optional, aber erwünscht (gibt Community zurück)

---

## Rationale

### Warum Onyx FOSS?

#### Vorteile:
1. **Schneller Start**: Basis-Features bereits implementiert (RAG, Conversations, UI)
   - Time-to-Market ~3-6 Monate statt 12+ Monate für Custom-Build

2. **Bewährte Architektur**: Onyx basiert auf bewährten Patterns
   - Vespa für Vektorsuche (produktionsreif)
   - PostgreSQL für Datenmanagement
   - Next.js für Modern Web UI

3. **Open Source Vorteile**:
   - Keine Vendor Lock-In
   - Quellcode-Zugriff (Sicherheit, Audit)
   - Community-Support
   - Kostentransparenz

4. **Datenhoheit**: Datenbank und Vektorspeicher können on-premise oder in German Cloud (StackIT) deployed werden
   - DSGVO-konform möglich
   - Keine Abhängigkeit von US-basierten Systemen

5. **Enterprise-readiness**:
   - Bereits Skalierbar auf große Nutzer-Basen
   - Monitoring und Logging vorhanden
   - Authentifizierungs-Framework vorhanden (ausbaubar auf OIDC/Entra ID)

6. **Erweiterbarkeit**: "Extend, don't modify"-Prinzip ermöglicht:
   - Custom Features ohne Core-Modifikation
   - Einfache Upstream-Merges bei Updates
   - Clear Separation of Concerns

#### Akzeptierte Nachteile:
1. **Upstream-Sync erforderlich**: Regelmäßige Integration von Updates
2. **Enterprise Features müssen gebaut werden**:
   - Token Limits, RBAC, Branding, System Prompts sind nicht im Core
   - Aber: Architektur ist dafür ausgelegt
3. **Community statt kommerziellem Support**:
   - Mitigiert durch: In-House Expertise (CCJ / Coffee Studios), Open Source Community, Optional: Onyx-Kommerzieller Support
4. **Performance-Tuning nötig**:
   - Vespa, PostgreSQL, Caching müssen optimiert werden
   - Standard-Setup möglicherweise nicht für große Lasten ausgelegt

---

## Alternatives Considered

### Alternative 1: Komplett Custom-Entwicklung

**Ansatz**: Von Grund auf neu bauen (LLM Integration, Conversations, UI, etc.)

**Vorteile**:
- Volle Kontrolle über Features und Architecture
- Keine Upstream-Abhängigkeiten
- Maßgeschneiderter Tech-Stack

**Nachteile**:
- **Very High Effort**: 12-18 Monate Entwicklung (nur Core-Features)
- **Hohe Kosten**: Größeres Team, längere Timeline
- **Risk**: Mehr Moving Parts, Testing-Aufwand
- **Verzögerter Go-Live**: Nicht akzeptabel für VÖB Timeline

**Entscheidung**: Abgelehnt wegen Time-to-Market und Kosten

---

### Alternative 2: LibreChat (andere Open Source Lösung)

**Ansatz**: Nutzung einer anderen Open Source Chatbot-Lösung (z. B. LibreChat)

**LibreChat Features**:
- Auch Open Source, ähnliche Architecture
- Multi-Model Support (verschiedene LLM-Provider)
- Web-basiert

**Nachteile im Vergleich zu Onyx**:
- Weniger RAG-Integration out-of-the-box
- Weniger Enterprise-Features
- Kleinere Community als Onyx
- Weniger produktionsreif

**Entscheidung**: Abgelehnt – Onyx besser für RAG/Enterprise-Requirements

---

### Alternative 3: Kommerzielle SaaS (OpenAI, Microsoft, etc.)

**Ansatz**: Nutzung einer kommerziellen Chatbot-Plattform als SaaS

**Beispiele**:
- OpenAI Platform (ChatGPT API + Custom Assistants)
- Microsoft Copilot Studio
- Google Vertex AI

**Nachteile für Banking-Sektor**:
- **Datenschutz**: Daten geht an US-basierte Server (DSGVO-Risiko)
- **Datenhoheit**: Keine volle Kontrolle über Infrastruktur
- **Vendor Lock-In**: Schwierig zu wechseln, Abhängigkeit von Pricing
- **Compliance**: BAIT und Banking-Standards schwer umsetzbar
- **Kosten**: Recurring Costs für SaaS-Nutzung, skaliert mit Nutzung

**Entscheidung**: Abgelehnt – Nicht akzeptabel für deutsche Bankenwirtschaft (Datenhoheit, Compliance)

---

## Consequences

### Positive Auswirkungen

1. **Schneller Go-Live**: ~6 Monate statt 12+ Monate
2. **Kosteneffizienz**: MIT-Lizenz, In-House Entwicklung statt Vendor-Kosten
3. **Datenhoheit**: Volle Kontrolle, DSGVO-konform möglich
4. **Skalierbarkeit**: Proven Architecture für große Nutzerbasen
5. **Wartbarkeit**: Clean Code, gute Dokumentation
6. **Zukunftssicherheit**: Open Source, keine Vendor Lock-In

### Negative Auswirkungen / Mitigation

1. **Upstream-Sync Overhead**
   - Mitigation: Regelmäßige Merge-Planung, "Extend, don't modify" Prinzip (ADR-002)
   - Impact: ~1-2 Tage pro Quarter für Major Updates

2. **Enterprise-Features müssen gebaut werden**
   - Mitigation: Gut geplante Extension-Architektur (ADR-002)
   - Impact: Bereits berücksichtigt in Project Timeline (Phase 4)

3. **Community Support statt SLA**
   - Mitigation: In-House Expertise, optional: Kommerzieller Support-Contract mit Onyx
   - Impact: Könnte längere Debug-Zeiten bei kritischen Issues bedeuten

4. **Performance-Tuning erforderlich**
   - Mitigation: Load Testing geplant (Phase 5), Caching-Strategy definiert
   - Impact: Zusätzliche Optimierungs-Arbeit in Phase 5

---

## Implementation Notes

### Onyx Setup Schritte

1. **Phase 1-2**: Onyx FOSS Repository clonen, auf StackIT deployen
2. **Phase 3**: Extension-Points evaluieren, Authentication integrieren
3. **Phase 4a-4f**: Custom Modules implementieren (Token Limits, RBAC, etc.)
4. **Phase 5**: Load Testing, Performance Optimization
5. **Phase 6**: Production Deployment

### Repository Management

```bash
# Upstream Tracking
git remote add upstream https://github.com/onyx-dot-app/onyx-foss.git
git fetch upstream
git merge upstream/main  # Regelmäßig (jeden Quarter)

# Custom Code
backend/ext/                    # Custom Backend-Module
web/src/ext/                    # Custom Frontend-Module
deployment/terraform/           # IaC (StackIT Provider)
deployment/helm/values/         # Helm Value-Overlays
deployment/docker_compose/      # Docker Compose (Local Dev)
```

### Versionierung

- **Onyx Core**: Upstream Version tracking (z. B. Onyx v2.1.3)
- **VÖB Extensions**: Semantic Versioning (z. B. vob-chatbot v1.0.0)
- **Combined**: Release Notes für beide

---

## Related ADRs

- **ADR-002**: Extension-Architektur ("Extend, don't modify")
  - Wie wir Custom Features ohne Core-Modifikationen bauen
- **ADR-003**: StackIT als Cloud Provider
  - Wo Onyx FOSS gehostet wird

---

## Approval & Sign-off

| Rolle | Name | Datum | Signatur |
|-------|------|-------|----------|
| Technischer Leiter (CCJ) | Nikolaj Ivanov | 2026-02-12 | __ |
| Projektleiter (CCJ) | Nikolaj Ivanov | 2026-02-12 | __ |
| Auftraggeber (VÖB) | [TBD] | [TBD] | __ |
| Architektur-Review | [TBD] | [TBD] | __ |

---

**ADR Status**: Akzeptiert
**Letzte Aktualisierung**: 2026-02-12
**Version**: 1.0
