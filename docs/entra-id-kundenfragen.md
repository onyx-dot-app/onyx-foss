# Entra ID Integration — Fragenkatalog für VÖB

**Projekt:** VÖB Chatbot — Phase 3 (Authentifizierung)
**Ziel:** Microsoft Entra ID (OIDC) als einziger Login-Weg für den Chatbot
**Stand:** 2026-03-03

---

## 1. App Registration in Entra ID

**Frage:** Können Sie eine App Registration in Ihrem Entra ID (Azure Portal) für unseren Chatbot anlegen?

**Was wir daraus brauchen:**

| Wert | Bezeichnung in Azure Portal |
|------|-----------------------------|
| Tenant ID | Verzeichnis-ID (Mandanten-ID) |
| Client ID | Anwendungs-ID |
| Client Secret | Geheimer Clientschlüssel |

**Warum:** OIDC funktioniert so: Unser Chatbot leitet den User zu Microsoft weiter zum Einloggen. Damit Microsoft weiss, dass unsere App vertrauenswuerdig ist, muss sie dort registriert sein. Die Tenant ID sagt "welches Unternehmen", die Client ID sagt "welche App", und das Client Secret ist das Passwort, mit dem unser Backend sich bei Microsoft authentifiziert, um den Login-Code gegen ein Token einzutauschen.

**Zustaendig:** VÖB IT. Nur jemand mit Azure AD Admin-Rechten kann das anlegen. Wir koennen eine Anleitung mitliefern, aber die Registrierung muss in deren Portal passieren.

---

## 2. Redirect URI / Domain

**Frage:** Wie lautet die finale Domain fuer den Chatbot? (z.B. `chatbot.voeb.de`)

**Was in Entra ID hinterlegt werden muss:**

```
https://<domain>/auth/oidc/callback
```

**Warum:** Nach dem Login bei Microsoft wird der User zurueck zu unserem Chatbot geschickt — an genau diese URL. Microsoft prueft strikt, dass die Redirect URI exakt mit der registrierten uebereinstimmt. Stimmt sie nicht, blockt Microsoft den Login. Das ist ein Sicherheitsmechanismus, damit niemand Tokens an eine fremde URL umleiten kann.

**Zustaendig:** Gemeinsam. VÖB entscheidet die Domain, VÖB IT oder wir richten den DNS-Eintrag ein, und wir tragen die URI in unsere Konfiguration ein. VÖB IT muss dieselbe URI in der App Registration hinterlegen.

---

## 3. Benutzer-Scope

**Frage:** Sollen alle Mitarbeiter im VÖB-Tenant Zugang haben, oder nur bestimmte Gruppen/Abteilungen?

**Falls eingeschraenkt:** Soll die Zugriffskontrolle in Entra ID passieren oder im Chatbot?

**Warum:** Es gibt zwei Wege, den Zugang einzuschraenken:

- **In Entra ID** (empfohlen): In der App Registration "User Assignment Required" aktivieren und nur bestimmte Gruppen/User zuweisen. Nicht-zugewiesene Mitarbeiter sehen die App gar nicht erst.
- **Im Chatbot:** Jeder kann sich einloggen, aber wir filtern intern nach Gruppen-Zugehoerigkeit.

Der Entra-ID-Weg ist sauberer, weil unberechtigte User gar nicht erst bis zu unserer App kommen.

**Zustaendig:** VÖB entscheidet die Policy, VÖB IT setzt sie in Entra ID um.

---

## 4. Benutzer-Attribute / E-Mail

**Frage:** Wird die E-Mail-Adresse als primaerer Identifier genutzt? Haben alle Zielnutzer eine E-Mail im Entra ID hinterlegt?

**Warum:** Onyx identifiziert User ueber die E-Mail-Adresse aus dem OIDC-Token. Wenn ein User in Entra ID keine E-Mail hinterlegt hat (z.B. bei technischen Accounts oder Shared Mailboxes), kann Onyx keinen Account anlegen. Der erste User, der sich einloggt, bekommt automatisch Admin-Rechte — das sollte also jemand von VÖB sein, nicht ein Test-Account.

**Zustaendig:** VÖB IT prueft, ob die User-Attribute korrekt gepflegt sind. Wir muessen nichts tun — Onyx liest die E-Mail automatisch aus dem Token.

---

## 5. Token & Session Policy

**Frage:** Wie lange soll eine Login-Session gueltig sein? Und: Soll der Chatbot den User abmelden, wenn das Entra-ID-Token ablaeuft?

**Zwei Modi:**

- **Standard** (empfohlen fuer Usability): User loggt sich ein, Session laeuft 7 Tage. Auch wenn Entra ID das Token nach 1 Stunde ablaufen laesst, bleibt der User im Chatbot eingeloggt.
- **Strikt** (empfohlen fuer Compliance): Wenn Entra ID das Token widerruft (z.B. Mitarbeiter gesperrt), wird der User sofort aus dem Chatbot geworfen.

**Warum das wichtig ist:** Bei einem Bankendienstleister mit BAIT-Anforderungen ist der strikte Modus moeglicherweise Pflicht. Wenn ein Mitarbeiter das Unternehmen verlaesst und in Entra ID deaktiviert wird, soll er im strikten Modus sofort keinen Zugang mehr haben — nicht erst nach 7 Tagen.

**Zustaendig:** VÖB entscheidet (ggf. in Abstimmung mit Compliance/Informationssicherheit). Wir setzen die entsprechende Konfiguration.

---

## 6. Netzwerk / Conditional Access

**Frage:** Gibt es IP-Einschraenkungen oder Conditional Access Policies in Ihrem Entra ID?

**Warum:** Der Login-Flow hat zwei Teile:

1. Der User wird im Browser zu Microsoft weitergeleitet — das passiert ueber das Netzwerk des Users.
2. Unser Backend tauscht den Login-Code gegen ein Token bei Microsoft ein — das passiert von unserer StackIT-IP `188.34.74.187` aus.

Wenn VÖB Conditional Access Policies hat, die nur bestimmte IPs zulassen (z.B. nur VPN/Buero-Netzwerk), dann muss unsere Server-IP freigeschaltet werden, sonst schlaegt Schritt 2 fehl.

**Zustaendig:** VÖB IT prueft ihre Conditional Access Policies. Falls Einschraenkungen bestehen, muessen sie unsere IP whitelisten.

---

## 7. DNS-Eintrag

**Frage:** Wer richtet den DNS-Eintrag ein? (A-Record oder CNAME auf unsere StackIT-IP)

**Warum:** Ohne Domain kein HTTPS-Zertifikat (Let's Encrypt braucht eine Domain). Ohne HTTPS kein sicherer OIDC-Flow — Microsoft erlaubt in Produktion keine `http://`-Redirect-URIs, nur `https://`. Die Kette ist:

```
DNS -> TLS-Zertifikat -> HTTPS -> OIDC funktioniert
```

**Zustaendig:** Haengt davon ab, wem die Domain gehoert. Wenn `voeb.de`: VÖB IT muss den DNS-Eintrag setzen. Wenn wir eine eigene Domain nutzen: wir.

---

## Zusammenfassung: Wer muss was tun?

| Aufgabe | VÖB IT | Wir (CCJ) |
|---------|--------|-----------|
| App Registration anlegen | Ja | Anleitung liefern |
| Tenant ID, Client ID, Secret uebergeben | Ja | Entgegennehmen, sicher speichern |
| Redirect URI eintragen | Ja (in Entra ID) | Ja (in Helm Config) |
| User Assignment / Gruppen | Ja | — |
| Conditional Access pruefen | Ja | IP mitteilen |
| DNS-Eintrag | Ja (wenn voeb.de) | TLS-Zertifikat einrichten |
| Session Policy entscheiden | Ja | Konfigurieren |
| Onyx OIDC konfigurieren | — | Ja (5 Env-Variablen) |
| Testen | Gemeinsam | Gemeinsam |

---

## Minimum-Ergebnis aus dem Gespraech

| Was | Warum |
|-----|-------|
| **Tenant ID** | Fuer die OpenID Config URL |
| **Client ID + Secret** | OAuth Credentials |
| **Wer richtet App Registration ein** | Klaerung Verantwortlichkeit |
| **Domain-Entscheidung** | Redirect URI + DNS + TLS |
| **User-Scope** | Alle oder nur bestimmte Gruppen |
| **Session Policy** | Standard vs. Strikt (BAIT-relevant) |
