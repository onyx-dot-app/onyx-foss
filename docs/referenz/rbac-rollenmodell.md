# RBAC-Rollenmodell — VÖB Service Chatbot

**Stand:** 2026-03-07
**Status:** Entwurf — wartet auf Abstimmung mit VÖB
**Erstellt von:** Nikolaj Ivanov (CCJ / Coffee Studios)
**Quelle:** Notizen aus dem Kickoff-Meeting + Sicherheitskonzept + Onyx-Analyse

---

## 1. Ausgangslage

### Was Onyx FOSS mitbringt

Onyx FOSS hat ein einfaches Rollensystem mit 7 Rollen:

| Rolle | Beschreibung |
|-------|-------------|
| `admin` | Volle Admin-Rechte (erster Login wird automatisch Admin) |
| `basic` | Standard-User |
| `curator` | Admin-Rechte fuer zugewiesene Gruppen |
| `global_curator` | Admin-Rechte fuer alle Gruppen |
| `limited` | Eingeschraenkter API-Zugriff |
| `slack_user` | Slack-Integration (nicht relevant fuer VoeB) |
| `ext_perm_user` | Externer Permission User (nicht relevant fuer VoeB) |

### Was fehlt (EE-Feature, nicht in FOSS enthalten)

Die folgenden Features sind **ausschliesslich in der kostenpflichtigen Enterprise Edition** verfuegbar und muessen fuer VoeB **custom in `backend/ext/` entwickelt** werden:

- **User Groups / Nutzergruppen** — Gruppen erstellen, Nutzer zuweisen
- **Gruppen-basierte Zugriffssteuerung** — Agenten, Assistenten, Dokumente pro Gruppe freigeben
- **Curator-Funktionalitaet** — Gruppen-Admins, die ihre eigene Gruppe verwalten
- **Entra ID Gruppen-Sync** — Automatische Zuordnung basierend auf Entra ID Gruppenmitgliedschaft
- **LLM-Modellzugriff pro Gruppe** — Unterschiedliche Modelle fuer unterschiedliche Gruppen

---

## 2. Rollenmodell (Entwurf)

### 4 Rollen

| Rolle | Mapping auf Onyx | Beschreibung |
|-------|------------------|-------------|
| **System-Admin** | `admin` | Volle Systemkontrolle |
| **Gruppen-Admin** | `curator` (erweitert) | Verwaltet eine oder mehrere Abteilungsgruppen |
| **Power-User** | `basic` (erweitert) | Kann Agenten/Assistenten erstellen |
| **Standard-User** | `basic` | Nutzt den Chatbot im Rahmen der Gruppenfreigaben |

### Rolle: System-Admin

**Wer:** CCJ (Nikolaj Ivanov) + ggf. 1 Person VoeB IT

**Rechte:**
- Alle Rechte eines Gruppen-Admins
- LLM-Modelle hinzufuegen, konfigurieren, entfernen
- System-Prompt verwalten (global, nicht ueberschreibbar durch User)
- Gruppen erstellen und loeschen
- Gruppen-Admins ernennen
- Token-Budgets und Rate Limits festlegen (pro Gruppe)
- Monitoring ueber alle Gruppen (Nutzung, Kosten, Feedback)
- Konnektoren (Datenquellen) verwalten
- Systemkonfiguration (Feature Flags, Branding)

### Rolle: Gruppen-Admin

**Wer:** Pro Abteilung 1-2 Personen (z.B. Pascal, Leif fuer uebergreifende Admin-Gruppe)

**Rechte:**
- Alle Rechte eines Power-Users
- Nutzer in eigener Gruppe verwalten (hinzufuegen/entfernen)
- Agenten/Assistenten fuer eigene Gruppe freigeben oder sperren
- LLM-Modelle fuer eigene Gruppe freischalten (aus der Liste der vom System-Admin konfigurierten Modelle)
- Monitoring der eigenen Gruppe (Nutzung pro Person, Feedback-Auswertung)
- Prompt Templates fuer eigene Gruppe freigeben
- Ggf. Nutzer aus anderen Abteilungen temporaer in eigene Gruppe aufnehmen (Cross-Abteilungs-Zugriff)

### Rolle: Power-User

**Wer:** Ausgewaehlte Mitarbeiter pro Abteilung

**Rechte:**
- Alle Rechte eines Standard-Users
- Agenten/Assistenten erstellen (sichtbar nur fuer eigene Gruppe, bis Gruppen-Admin freigibt)
- Prompt Templates erstellen
- Dokumente verwalten (hochladen, organisieren, loeschen)

**Offene Frage:** Wird diese Rolle benoetigt, oder reicht die Unterscheidung Admin / Standard-User?

### Rolle: Standard-User

**Wer:** Alle VoeB-Mitarbeiter mit Chatbot-Zugang

**Rechte:**
- Chatten (mit freigegebenen Modellen)
- Freigegebene Agenten/Assistenten nutzen
- Dokumente hochladen (Entscheidung aus Kickoff: alle duerfen uploaden)
- Feedback geben (Daumen hoch/runter mit optionalem Kommentar)
- Eigene Chats und Projekte verwalten

**Einschraenkungen:**
- Kann System-Prompt nicht ueberschreiben (Sicherheitsentscheidung aus Kickoff)
- Sieht nur Agenten/Assistenten, die fuer seine Gruppe freigegeben sind
- Sieht nur LLM-Modelle, die fuer seine Gruppe freigeschaltet sind

---

## 3. Gruppenstruktur

### Prinzip: Gruppen = VoeB-Abteilungen

Aus dem Kickoff-Meeting:
- VoeB hat ein bestehendes Rollenkonzept in Entra ID, basierend auf **Abteilungen**
- Keine Untergruppen pro Produkt innerhalb der Abteilungen
- Fuer den Chatbot wird auf die bestehende Struktur aufgesetzt ("kein neues Fass aufmachen")
- Freigaben erfolgen **per Gruppe, nicht per Person**

### Gruppenstruktur (Entwurf — muss mit VoeB abgestimmt werden)

| Gruppe | Entra ID Gruppe | Gruppen-Admin(s) | Bemerkung |
|--------|-----------------|-------------------|-----------|
| [Abteilung 1] | [bestehende Entra ID Gruppe?] | [Name(n)] | |
| [Abteilung 2] | [bestehende Entra ID Gruppe?] | [Name(n)] | |
| ... | ... | ... | |
| **Admin-Gruppe** | [neu zu erstellen] | Pascal, Leif | Uebergreifende Verwaltung |

> **Die konkrete Abteilungsliste muss von VoeB kommen.** Siehe offene Fragen (Abschnitt 5).

### Zugriffsteuerung pro Gruppe

| Ressource | Steuerung | Wer steuert |
|-----------|-----------|-------------|
| **Agenten/Assistenten** | Pro Gruppe freigeben | Gruppen-Admin |
| **LLM-Modelle** | Pro Gruppe freischalten | Gruppen-Admin (aus System-Admin-Liste) |
| **Prompt Templates** | Pro Gruppe freigeben | Gruppen-Admin |
| **Dokumente** | Abteilungsweise getrennt | Automatisch nach Gruppenzugehoerigkeit |
| **Chats/Logs** | Abteilungsweise erfasst | Automatisch (DSGVO + EU AI Act) |

---

## 4. Entra ID Integration

### Ziel-Architektur

```
Entra ID (VoeB)                    Chatbot (ext/)
  |                                  |
  +-- Abteilungs-Gruppen  -------->  ext_user_groups (Sync)
  +-- User + Gruppenzugehoerigkeit -> ext_group_members
  +-- OIDC Token (groups Claim)  --> Rollen-Mapping bei Login
```

### Stufenplan

| Phase | Was | Code-Aenderung |
|-------|-----|----------------|
| **3a** | OIDC-Login mit Entra ID | Zero Code — `AUTH_TYPE: oidc` in Helm Values |
| **3b** | Rollen-Mapping (Entra ID Gruppe → Chatbot-Rolle) | `backend/ext/` — Login-Hook |
| **4b** | Gruppen-Sync (Entra ID Gruppen → Chatbot-Gruppen) | `backend/ext/` — Sync-Service |
| **4c** | Gruppen-basierte Zugriffssteuerung (UI + API) | `backend/ext/` + `web/src/ext/` |
| **5** | Deprovisioning (User aus Entra ID entfernt → Chatbot-Zugang gesperrt) | `backend/ext/` — Cleanup-Job |

### Auth-Architektur: Ein AUTH_TYPE pro Instanz (verifiziert)

Onyx unterstuetzt **genau einen** `AUTH_TYPE` pro Instanz (`basic`, `google_oauth`, `oidc`, `saml`, `cloud`). Es gibt kein "OIDC + Basic gleichzeitig". Wenn `AUTH_TYPE=oidc` gesetzt ist, ist Entra ID der einzige Login-Weg.

**Wichtig:** `AUTH_TYPE: disabled` ist seit Upstream-Version abgeschafft. Onyx faellt automatisch auf `basic` zurueck (Warning im Log).

**Konsequenz fuer Environments:**

| Environment | AUTH_TYPE | Begruendung |
|-------------|-----------|-------------|
| **DEV** | `basic` | Entwicklung ohne Entra-ID-Abhaengigkeit. CCJ arbeitet unabhaengig. |
| **TEST** | `oidc` | Auth-Flow testen. CCJ als Entra ID B2B-Gastbenutzer eingeladen. |
| **PROD** | `oidc` | Pflicht fuer VoeB-Nutzer. CCJ als Entra ID B2B-Gastbenutzer eingeladen. |

### Externer Dienstleister-Zugang (CCJ)

Da CCJ (Nikolaj Ivanov) nicht Teil des VoeB-Tenants ist, wird der Zugang ueber **Entra ID B2B-Collaboration** (Gastbenutzer) geloest:

- VoeB laedt `n.ivanov@scale42.de` als Gastbenutzer im Entra ID Portal ein (Externe Identitaeten → Benutzer einladen)
- Niko authentifiziert sich mit seinem eigenen Microsoft-/Email-Konto
- Entra ID erkennt ihn als autorisierten Gast im VoeB-Tenant
- Onyx provisioniert ihn automatisch per JIT (Just-in-Time Provisioning, Zeile 220-222 `backend/onyx/auth/users.py`):
  ```python
  if AUTH_TYPE in {AuthType.SAML, AuthType.OIDC}:
      # SSO providers manage membership; allow JIT provisioning regardless of invites
      return
  ```
- Nach erstem Login: System-Admin-Rolle in Onyx zuweisen

**Dies ist Standard-Praxis fuer externe Dienstleister im Enterprise-Bereich und erfordert keinen Custom-Code.**

### Voraussetzungen von VoeB IT

| Was | Beschreibung | Status |
|-----|-------------|--------|
| App-Registrierung in Entra ID | Client ID, Tenant ID, Client Secret | Blockiert |
| `groups` Claim im OIDC Token | Damit der Chatbot weiss, in welcher Abteilung ein User ist | Zu klaeren |
| Redirect URI | `https://dev.chatbot.voeb-service.de/auth/oidc/callback` (nach TLS) | Wartet auf TLS |
| User Assignment Required | Nur Mitarbeiter mit Chatbot-Zugang koennen sich anmelden | Zu klaeren |
| B2B-Gastbenutzer fuer CCJ | `n.ivanov@scale42.de` als Gast einladen | Offen |

---

## 5. Offene Fragen an VoeB

### Gruppenstruktur

1. **Welche Abteilungen gibt es bei VoeB?**
   Wir brauchen die vollstaendige Liste der Abteilungen, damit wir die Gruppen im Chatbot 1:1 darauf mappen koennen.

2. **Existieren diese Abteilungen bereits als Gruppen in Entra ID?**
   Oder muessen neue Gruppen fuer den Chatbot angelegt werden?

3. **Wer wird Gruppen-Admin pro Abteilung?**
   Pro Gruppe 1-2 Personen, die ihre Abteilung im Chatbot verwalten.

4. **Uebergreifende Admin-Gruppe:**
   Wir schlagen vor, die Teilnehmer des Kickoff-Meetings (Pascal, Leif + weitere) als uebergreifende Admin-Gruppe einzurichten. Stimmt das?

### Zugriffssteuerung

5. **Cross-Abteilungs-Zugriff:**
   Soll ein Gruppen-Admin Personen aus anderen Abteilungen temporaer in seine Gruppe aufnehmen koennen? (z.B. wenn Marketing mit Recht an einem Projekt zusammenarbeitet)

6. **LLM-Modelle pro Gruppe:**
   Sollen alle Abteilungen die gleichen Modelle bekommen, oder gibt es Unterschiede? (Im Kickoff-Meeting wurde als Beispiel genannt: Marketing bekommt Zugriff auf Bild-Modelle, andere Abteilungen nicht.)

### Rollen

7. **Power-User-Rolle:**
   Braucht ihr eine Zwischenstufe zwischen Standard-User und Gruppen-Admin? Also Mitarbeiter, die Agenten/Assistenten erstellen koennen, aber keine Gruppenverwaltung machen? Oder reichen zwei Stufen (Admin / Standard-User)?

### Entra ID (technisch)

8. **`groups` Claim:**
   Kann die App-Registrierung in Entra ID so konfiguriert werden, dass der OIDC-Token einen `groups` Claim enthaelt? Damit erkennt der Chatbot automatisch, in welcher Abteilung ein Nutzer ist.

9. **User Assignment Required:**
   Soll der Zugang zum Chatbot auf bestimmte Entra ID Gruppen beschraenkt werden? Oder duerfen alle VoeB-Mitarbeiter sich anmelden?

10. **B2B-Gastbenutzer fuer CCJ:**
    Nikolaj Ivanov (CCJ / Coffee Studios) benoetigt als externer Dienstleister Zugang zu TEST und PROD. Bitte `n.ivanov@scale42.de` als B2B-Gastbenutzer in Entra ID einladen. Dies kann gleichzeitig mit der App-Registrierung erfolgen.

---

## 6. Monitoring und Feedback (aus Kickoff)

Zusaetzlich zum Rollenmodell wurden im Kickoff folgende Monitoring-Anforderungen besprochen:

| Feature | Sichtbar fuer | Beschreibung |
|---------|--------------|-------------|
| Nutzungsstatistiken pro Abteilung | Gruppen-Admin, System-Admin | Wie intensiv wird der Chatbot genutzt? |
| Nutzungsstatistiken pro Person | Gruppen-Admin (nur eigene Gruppe) | Wer nutzt den Chatbot wie oft? |
| Token-Verbrauch pro Anfrage | Alle User | Transparenz ueber Kosten |
| Feedback (Daumen hoch/runter) | Gruppen-Admin, System-Admin | Mit optionalem Freitext-Kommentar |
| Verwendetes Modell pro Anfrage | System-Admin | Vergleichbarkeit der Modellqualitaet |

**Wichtig:** Chat-Inhalte sind fuer Admins **nicht einsehbar** (Datenschutz). Nur aggregierte Metriken und Feedback-Bewertungen.

---

## Referenzen

| Dokument | Pfad |
|----------|------|
| Sicherheitskonzept (Rollen + Zugriffsmatrix) | `docs/sicherheitskonzept.md` |
| Entra ID Kundenfragen | `docs/entra-id-kundenfragen.md` |
| Extension Framework Spezifikation | `docs/technisches-feinkonzept/ext-framework.md` |
| Meilensteinplan (M2, M3) | `docs/abnahme/meilensteinplan.md` |
| Kickoff-Meeting Notizen | `docs/referenz/kickoff-transkription.md` |
