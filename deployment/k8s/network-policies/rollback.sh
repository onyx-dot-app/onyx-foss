#!/usr/bin/env bash
# ============================================================================
# NetworkPolicy Rollback-Skript (Notfall)
#
# Loescht ALLE NetworkPolicies im angegebenen Namespace.
# Ergebnis: Kubernetes-Default "allow-all" wird wiederhergestellt.
#
# Verwendung:
#   ./rollback.sh onyx-dev     # DEV Environment
#   ./rollback.sh onyx-test    # TEST Environment
#
# WARNUNG: Nach dem Rollback sind KEINE NetworkPolicies aktiv.
#          Der Namespace ist wieder vollstaendig offen.
#
# Audit-Referenz: C5/SEC-03 — docs/audit/networkpolicy-analyse.md
# ============================================================================

set -euo pipefail

NAMESPACE="${1:?Fehler: Namespace als Argument angeben. Verwendung: ./rollback.sh <namespace>}"

echo "============================================"
echo "NetworkPolicy ROLLBACK — Namespace: ${NAMESPACE}"
echo "============================================"

# Pruefen ob Namespace existiert
if ! kubectl get namespace "${NAMESPACE}" > /dev/null 2>&1; then
    echo "FEHLER: Namespace '${NAMESPACE}' existiert nicht."
    exit 1
fi

# Aktuelle Policies anzeigen
echo ""
echo "--- Aktuelle NetworkPolicies (werden geloescht) ---"
kubectl get networkpolicy -n "${NAMESPACE}" 2>/dev/null || echo "(keine)"

echo ""
echo "Loesche alle NetworkPolicies in ${NAMESPACE}..."
kubectl delete networkpolicy --all -n "${NAMESPACE}"

echo ""
echo "--- Verifikation ---"
kubectl get networkpolicy -n "${NAMESPACE}" 2>/dev/null || echo "(keine — Rollback erfolgreich)"

echo ""
echo "============================================"
echo "Rollback abgeschlossen: ${NAMESPACE}"
echo "WARNUNG: Namespace ist jetzt OFFEN (allow-all)"
echo "============================================"
