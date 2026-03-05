#!/usr/bin/env bash
# ============================================================================
# NetworkPolicy Apply-Skript (C5/SEC-03)
#
# Wendet alle 5 NetworkPolicies in sicherer Reihenfolge an:
#   1. Allow-Policies (02-05) — Verbindungen erlauben
#   2. Default-Deny (01) — alles andere sperren
#
# Verwendung:
#   ./apply.sh onyx-dev     # DEV Environment
#   ./apply.sh onyx-test    # TEST Environment
#
# Rollback bei Problemen:
#   ./rollback.sh onyx-dev
#
# Audit-Referenz: C5/SEC-03 — docs/audit/networkpolicy-analyse.md
# ============================================================================

set -euo pipefail

NAMESPACE="${1:?Fehler: Namespace als Argument angeben. Verwendung: ./apply.sh <namespace>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo "NetworkPolicy Apply — Namespace: ${NAMESPACE}"
echo "============================================"

# Pruefen ob Namespace existiert
if ! kubectl get namespace "${NAMESPACE}" > /dev/null 2>&1; then
    echo "FEHLER: Namespace '${NAMESPACE}' existiert nicht."
    exit 1
fi

# Aktuellen Stand anzeigen
echo ""
echo "--- Aktuelle NetworkPolicies in ${NAMESPACE} ---"
kubectl get networkpolicy -n "${NAMESPACE}" 2>/dev/null || echo "(keine)"
echo ""

# Schritt 1: Allow-Policies anwenden (ZUERST — bevor default-deny greift)
echo "--- Schritt 1/2: Allow-Policies anwenden ---"
for policy in 02-allow-dns-egress.yaml 03-allow-intra-namespace.yaml 04-allow-external-ingress-nginx.yaml 05-allow-external-egress.yaml; do
    echo "  Applying: ${policy}"
    kubectl apply -f "${SCRIPT_DIR}/${policy}" -n "${NAMESPACE}"
done

echo ""
echo "--- Schritt 2/2: Default-Deny anwenden ---"
kubectl apply -f "${SCRIPT_DIR}/01-default-deny-all.yaml" -n "${NAMESPACE}"

echo ""
echo "--- Ergebnis ---"
kubectl get networkpolicy -n "${NAMESPACE}"

echo ""
echo "============================================"
echo "Alle 5 Policies angewendet auf: ${NAMESPACE}"
echo "============================================"
echo ""
echo "Naechste Schritte — Verifikation:"
echo "  1. API Health:      kubectl exec -n ${NAMESPACE} deploy/${NAMESPACE}-api-server -- curl -sf http://localhost:8080/api/health"
echo "  2. DNS:             kubectl exec -n ${NAMESPACE} deploy/${NAMESPACE}-api-server -- nslookup google.com"
echo "  3. LoadBalancer:    curl -sf http://<LB-IP>/api/health"
echo "  4. Cross-NS block:  kubectl exec -n ${NAMESPACE} deploy/${NAMESPACE}-api-server -- curl -sf --max-time 3 http://<OTHER-NS>-api-service.<OTHER-NS>:8080/api/health"
echo ""
echo "Bei Problemen: ./rollback.sh ${NAMESPACE}"
