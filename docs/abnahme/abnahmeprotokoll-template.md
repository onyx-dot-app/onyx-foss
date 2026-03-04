# Abnahmeprotokoll-Template

**Dokumentstatus**: Template (wird bei Abnahme ausgefüllt)
**Version**: 1.0

---

## Allgemeine Informationen

| Feld | Wert |
|------|------|
| **Projekt** | VÖB Service Chatbot |
| **Projektphase / Meilenstein** | [z. B. M1: Infrastruktur + Dev Environment] |
| **Abnahmedatum** | [TBD] |
| **Ort** | [Online / Vor Ort] |

---

## Teilnehmer

### Auftragnehmer (Implementierer)

| Rolle | Name | Organisation | Unterschrift |
|-------|------|-------------|-------------|
| Projektleiter | [TBD] | CCJ | ____________ |
| Technischer Leiter | [TBD] | CCJ / Coffee Studios | ____________ |
| QA-Verantwortlicher | [TBD] | CCJ / Coffee Studios | ____________ |

### Auftraggeber (VÖB)

| Rolle | Name | Abteilung | Unterschrift |
|-------|------|----------|-------------|
| Projektverantwortlicher | [TBD] | VÖB | ____________ |
| Technischer Reviewer | [TBD] | VÖB IT | ____________ |
| Compliance / Audit | [TBD] | VÖB Risiko | ____________ |

### Weitere Beteiligte

- **StackIT Vertreter** (bei Infrastruktur-Abnahme): [TBD]
- **Externe Auditor** (optional): [TBD]

---

## Prüfgegenstand

### Phase / Meilenstein Details

**Meilenstein**: [M1-M6, z. B. M1: Infrastruktur + Development Environment]

**Geltungsumfang**:
- [Beschreibung was getestet/abgenommen wird]
- Beispiel M1:
  - StackIT Kubernetes Cluster
  - PostgreSQL Datenbank
  - Development Environment Setup
  - CI/CD Pipeline grundlagen

**Nicht im Umfang**:
- [Was ist bewusst ausgeschlossen]
- Beispiel M1:
  - Custom Extension Modules (folgen in M2-M4)
  - Production Monitoring Stack (M5)
  - UAT (M5)

### Referenzmaterialien

- [Link zu Technisches Feinkonzept](../technisches-feinkonzept/ext-framework.md)
- [Link zu Testkonzept](../testkonzept.md)
- [Link zu Meilensteinplan](./meilensteinplan.md)
- Test Report: [Datei TBD]
- Build Artifacts: [Location TBD]

---

## Abnahmekriterien

Nachfolgend sind die Abnahmekriterien für diesen Meilenstein aufgelistet. Der Status "Erfüllt: Ja/Nein" wird während der Abnahme ausgefüllt.

### Funktionale Abnahmekriterien

| Nr. | Kriterium | Soll-Zustand | Ist-Zustand (aktuell) | Erfüllt? | Bemerkung |
|-----|-----------|-------------|--------|---------|----------|
| F-1 | [Kriterium 1] | [Erwartet] | [Beobachtet] | [ ] Ja [ ] Nein | [Anmerkung] |
| F-2 | [Kriterium 2] | [Erwartet] | [Beobachtet] | [ ] Ja [ ] Nein | [Anmerkung] |

**Beispiel für M1 (Infrastruktur)**:

| Nr. | Kriterium | Soll-Zustand | Ist-Zustand | Erfüllt? | Bemerkung |
|-----|-----------|-------------|--------|---------|----------|
| F-1 | Kubernetes Cluster deployed | Cluster läuft mit 2 nodes | [TBD] | [ ] Ja [ ] Nein | [TBD] |
| F-2 | PostgreSQL erreichbar | DB Connection erfolgreich | [TBD] | [ ] Ja [ ] Nein | [TBD] |
| F-3 | Vespa läuft | 1 Vespa Pod (in-cluster), Index erstellt | [TBD] | [ ] Ja [ ] Nein | [TBD] |
| F-4 | Object Storage funktioniert | Bucket erstellt, Files upload/download | [TBD] | [ ] Ja [ ] Nein | [TBD] |
| F-5 | CI/CD Pipeline funktioniert | Git Push triggert Build | [TBD] | [ ] Ja [ ] Nein | [TBD] |

### Non-Funktionale Abnahmekriterien

| Nr. | Kriterium | Soll-Zustand | Ist-Zustand | Erfüllt? | Bemerkung |
|-----|-----------|-------------|--------|---------|----------|
| NF-1 | [Kriterium 1] | [Erwartet] | [Beobachtet] | [ ] Ja [ ] Nein | [Anmerkung] |
| NF-2 | [Kriterium 2] | [Erwartet] | [Beobachtet] | [ ] Ja [ ] Nein | [Anmerkung] |

**Beispiel für M1 (Infrastruktur)**:

| Nr. | Kriterium | Soll-Zustand | Ist-Zustand | Erfüllt? | Bemerkung |
|-----|-----------|-------------|--------|---------|----------|
| NF-1 | Verfügbarkeit | 99.5% über 7 Tage | [TBD]% | [ ] Ja [ ] Nein | [TBD] |
| NF-2 | Datenbank Response Time | < 100ms für einfache Queries | [TBD]ms | [ ] Ja [ ] Nein | [TBD] |
| NF-3 | Backup funktioniert | Tägliche Snapshots werden erstellt | [TBD] | [ ] Ja [ ] Nein | [TBD] |
| NF-4 | Netzwerksicherheit | Network Policies konfiguriert | [TBD] | [ ] Ja [ ] Nein | [TBD] |
| NF-5 | Logging | Alle Komponenten loggen zentral | [TBD] | [ ] Ja [ ] Nein | [TBD] |

### Sicherheits- und Compliance-Kriterien

| Nr. | Kriterium | Soll-Zustand | Ist-Zustand | Erfüllt? | Bemerkung |
|-----|-----------|-------------|--------|---------|----------|
| S-1 | [Kriterium 1] | [Erwartet] | [Beobachtet] | [ ] Ja [ ] Nein | [Anmerkung] |
| S-2 | [Kriterium 2] | [Erwartet] | [Beobachtet] | [ ] Ja [ ] Nein | [Anmerkung] |

**Beispiel für M1 (Infrastruktur)**:

| Nr. | Kriterium | Soll-Zustand | Ist-Zustand | Erfüllt? | Bemerkung |
|-----|-----------|-------------|--------|---------|----------|
| S-1 | TLS/HTTPS aktiviert | Alle API-Endpoints über HTTPS | [TBD] | [ ] Ja [ ] Nein | [TBD] |
| S-2 | Secrets verschlüsselt | API Keys in GitHub Actions Secrets + Kubernetes Secrets verwaltet | [TBD] | [ ] Ja [ ] Nein | [TBD] |
| S-3 | Datenverschlüsselung | DB Encryption at Rest aktiviert | [TBD] | [ ] Ja [ ] Nein | [TBD] |
| S-4 | Audit Logging | Alle Zugriffe werden protokolliert | [TBD] | [ ] Ja [ ] Nein | [TBD] |
| S-5 | Datensouveränität | Keine Daten außerhalb Deutschlands | [TBD] | [ ] Ja [ ] Nein | [TBD] |

---

## Festgestellte Mängel

Falls während der Abnahme Mängel / Defekte / Abweichungen gefunden werden, werden sie hier dokumentiert.

### Mängelliste

| ID | Beschreibung | Schwere | Frist zur Behebung | Status | Verantwortlicher |
|----|-------------|--------|-----------------|--------|-----------------|
| M-001 | [Mangel-Beschreibung] | [ ] Blocker [ ] Kritisch [ ] Normal [ ] Gering | [Datum] | [ ] Offen [ ] In Bearbeitung [ ] Gelöst | [Name] |
| M-002 | [Mangel-Beschreibung] | [ ] Blocker [ ] Kritisch [ ] Normal [ ] Gering | [Datum] | [ ] Offen [ ] In Bearbeitung [ ] Gelöst | [Name] |

### Beispiel-Mängel (für Referenz)

| ID | Beschreibung | Schwere | Frist | Status | Verantwortlicher |
|----|-------------|--------|-------|--------|-----------------|
| M-001 | PostgreSQL Performance: Queries brauchen 2s statt <100ms | Kritisch | 7 Tage | Offen | CCJ DBA |
| M-002 | Vespa Index konnte nicht vollständig geladen werden | Blocker | 3 Tage | In Bearbeitung | StackIT Support |
| M-003 | Dokumentation für Runbooks unvollständig | Normal | 14 Tage | Offen | CCJ Techwriter |

### Nachbearbeitung von Mängeln

**Prozess für Mangel-Behandlung**:
1. Mangel wird dokumentiert (oben)
2. Auftragnehmer erstellt Fix oder Plan
3. Auftraggeber genehmigt Plan
4. Fix wird implementiert und getestet
5. Verifikations-Test durch Auftraggeber
6. Mangel als "Gelöst" markiert

**Deadline für Mängelabschluss**: [TBD – typisch vor nächstem Meilenstein]

---

## Abnahme-Ergebnis

### Gesamtbewertung

Basierend auf den oben genannten Kriterien und festgestellten Mängeln, wird die Abnahme wie folgt festgestellt:

**Wählen Sie eine Option**:

- [ ] **Abnahme ohne Mängel**
  - Alle Kriterien erfüllt
  - Keine offenen Mängel
  - System ist in Produktionsbereitschaft

- [ ] **Abnahme mit Auflagen**
  - Alle kritischen Kriterien erfüllt
  - Einige normale Mängel vorhanden
  - System kann mit Mängel-Abschluss-Frist akzeptiert werden
  - **Mängel-Abschluss-Frist**: [Datum, typisch vor nächstem Meilenstein]

- [ ] **Abnahme verweigert**
  - Kritische oder Blocker-Mängel vorhanden
  - System erfüllt nicht die Anforderungen
  - Weitere Arbeit erforderlich vor Abnahme
  - **Nächste Abnahme geplant**: [Datum]

### Begründung (bei Auflagen oder Verweigerung)

[Begründung hier eintragen, falls Abnahme nicht ohne Mängel erfolgt]

**Beispiel**:
> Abnahme mit Auflagen erfolgt. PostgreSQL Performance-Issue (M-001) ist kritisch, aber CCJ hat Optimierungs-Plan vorgelegt. Frist: 7 Tage. Vespa Index-Problem (M-002) ist Blocker im Umfang, aber StackIT arbeitet aktiv daran. Frist: 3 Tage. Nach Behebung dieser Blocker werden wir ein Abnahme-Bestätigungs-Meeting durchführen.

---

## Unterschriften

Die unterzeichnenden Parteien bestätigen, dass die Abnahme gemäß diesem Protokoll durchgeführt wurde und die o.g. Ergebnisse korrekt sind.

### Auftragnehmer

**Name, Titel**: [TBD]
**Organisation**: CCJ / Coffee Studios
**Unterschrift**: _________________________ **Datum**: __________

### Auftraggeber

**Name, Titel**: [TBD]
**Organisation**: VÖB
**Unterschrift**: _________________________ **Datum**: __________

**Name, Titel**: [TBD] (optional: 2. Signatur)
**Organisation**: VÖB
**Unterschrift**: _________________________ **Datum**: __________

---

## Anlage A: Test-Report

[Verweis oder Anhang des detaillierten Test-Reports]

**Datei**: test-report-[Meilenstein]-[Datum].pdf
**Speicherort**: [TBD]

---

## Anlage B: Checkliste für Abnahme-Durchführung

Diese Checkliste hilft bei der Durchführung der Abnahme:

- [ ] Alle Teilnehmer sind anwesend (oder online zugeschaltet)
- [ ] Testumgebung ist verfügbar und stabil
- [ ] Alle Test-Artefakte sind vorhanden (Test-Reports, Logs, etc.)
- [ ] Kriteria-Review durchgeführt
- [ ] Live-Demo durchgeführt (falls zutreffend)
- [ ] Q&A Session durchgeführt
- [ ] Mängel diskutiert und priorisiert
- [ ] Abnahme-Ergebnis festgestellt
- [ ] Unterschriften eingesammelt
- [ ] Protokoll an alle Parteien verteilt

---

## Anlage C: Unterschriften-Seite (getrennt ausdruckbar)

[Optional: Separate Seite zum Ausdrucken für physische Unterschriften]

```
_____________________________________________________________________________

VÖB Service Chatbot – Abnahmeprotokoll

Projekt:     VÖB Service Chatbot
Meilenstein: [TBD]
Datum:       [TBD]
Ort:         [TBD]

AUFTRAGNEHMER:

_________________________________          _________________________________
Name, Titel (Print)                        Unterschrift, Datum


_________________________________          _________________________________
Name, Titel (Print)                        Unterschrift, Datum


AUFTRAGGEBER (VÖB):

_________________________________          _________________________________
Name, Titel (Print)                        Unterschrift, Datum


_________________________________          _________________________________
Name, Titel (Print)                        Unterschrift, Datum


_____________________________________________________________________________
```

---

**Protokoll-Version**: 1.0
**Gültig ab**: [Datum]
**Nächste Überprüfung**: [Datum]
