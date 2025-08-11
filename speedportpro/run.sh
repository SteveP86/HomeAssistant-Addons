#!/usr/bin/env bash
set -euo pipefail

# Lade Konfiguration
CONFIG="/data/options.json"
ROUTER_IP=$(jq -r '.router_ip' "$CONFIG")
USERNAME=$(jq -r '.username' "$CONFIG")
PASSWORD=$(jq -r '.password' "$CONFIG")

# Logging-Funktion
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Teste Router-Verbindung
test_connection() {
    log "Versuche Verbindung zum Router..."
    if ! curl -fsS -u "${USERNAME}:${PASSWORD}" "http://${ROUTER_IP}/api/v1/status" >/dev/null; then
        log "FEHLER: Router nicht erreichbar!"
        exit 1
    fi
}

# Hauptfunktion
main() {
    test_connection
    log "Verbunden mit Speedport Pro (${ROUTER_IP})"

    # Endlosschleife für kontinuierliche Abfrage
    while true; do
        DATA=$(curl -fsS -u "${USERNAME}:${PASSWORD}" "http://${ROUTER_IP}/api/v1/status" || {
            log "API-Aufruf fehlgeschlagen"
            sleep 30
            continue
        })

        # Daten an MQTT senden
        if ! mosquitto_pub -h "hassio" -t "speedport/status" -m "$DATA"; then
            log "MQTT-Veröffentlichung fehlgeschlagen"
        fi

        sleep 60  # Warte 1 Minute
    done
}

main
