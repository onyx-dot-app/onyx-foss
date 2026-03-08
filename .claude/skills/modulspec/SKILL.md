---
name: modulspec
description: Erstellt eine Modulspezifikation nach dem Enterprise-Template. Immer aufrufen bevor ein neues Feature implementiert wird.
---

# Modulspezifikation erstellen

Erstelle eine vollständige Modulspezifikation unter:
```
docs/technisches-feinkonzept/{modulname}.md
```

## Pflichtinhalt (jeder Abschnitt MUSS ausgefüllt sein)

### 1. Übersicht
- Modulname, Zweck, betroffene User-Rollen
- Feature Flag Name: `EXT_{MODULNAME}_ENABLED`
- Abhängigkeiten zu anderen ext_-Modulen

### 2. API-Endpoints
Pro Endpoint dokumentiere:
| Feld | Wert |
|------|------|
| Pfad | `/api/ext/{modul}/...` |
| Methode | GET/POST/PUT/DELETE |
| Auth | Required (Entra ID) |
| Request Body | Pydantic Schema (alle Felder mit Typen) |
| Response | Pydantic Schema (alle Felder mit Typen) |
| Fehlercodes | 400, 401, 403, 404, 500 mit Beschreibung |

### 3. Datenbankschema
Pro Tabelle:
- Name: `ext_{modulname}_{entity}`
- Spalten mit Typen, Constraints, Defaults
- Foreign Keys (auf welche Onyx/ext_-Tabelle)
- Indizes
- Migrations-Strategie (neues Alembic Script)

### 4. Fehlerbehandlung
Liste JEDEN möglichen Fehlerfall:
- Ungültige Inputs → 400 + Fehlermeldung
- Nicht authentifiziert → 401
- Keine Berechtigung → 403
- Ressource nicht gefunden → 404
- Interner Fehler → 500 + Logging
- Feature Flag deaktiviert → 404 (Router nicht registriert)

### 5. Feature Flag Verhalten
- Flag Name + Default-Wert
- Verhalten wenn aktiviert (vollständig beschreiben)
- Verhalten wenn deaktiviert (Onyx unverändert, keine Seiteneffekte)

### 6. Betroffene Core-Dateien
Liste JEDE der 10 Core-Dateien die verändert wird:
- Welche Datei
- Was genau geändert wird (exakte Zeilen/Code)
- Warum es nicht anders geht

### 7. Tests
- Unit Tests: Welche Funktionen
- Integration Tests: Welche Endpoints
- Feature Flag Tests: Flag=true und Flag=false
- Edge Cases: Welche spezifischen Fälle

Vorlage falls vorhanden: `docs/technisches-feinkonzept/template-modulspezifikation.md`

**Nach Fertigstellung: Niko die Spec zeigen und Freigabe abwarten.**
