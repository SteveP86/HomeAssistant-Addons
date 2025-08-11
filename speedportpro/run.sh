#!/usr/bin/with-contenv bashio
set -euo pipefail

# Warten, bis Home Assistant die Konfig-Datei erzeugt hat
CONFIG="/data/options.json"
while [ ! -f "$CONFIG" ]; do
    bashio::log.info "Warte auf $CONFIG …"
    sleep 2
done

# Konfiguration einlesen
ROUTER_IP=$(bashio::config 'router_ip')
USERNAME=$(bashio::config 'username')
PASSWORD=$(bashio::config 'password')

# Logging-Funktion (jetzt via bashio)
log() {
    bashio::log.info "$1"
}

# Teste Router-Verbindung
test_connection() {
    log "Versuche Verbindung zum Router..."
    if ! curl -fsS -u "${USERNAME}:${PASSWORD}" "http://${ROUTER_IP}/api/v1/status" >/dev/null; then
        bashio::log.error "Router nicht erreichbar!"
        exit 1
    fi
}

# Hauptfunktion
main() {
    test_connection
    log "Verbunden mit Speedport Pro (${ROUTER_IP})"

    while true; do
        DATA=$(curl -fsS -u "${USERNAME}:${PASSWORD}" "http://${ROUTER_IP}/api/v1/status" || {
            log "API-Aufruf fehlgeschlagen – warte 30 s"
            sleep 30
            continue
        })

        mosquitto_pub -h "hassio" -t "speedport/status" -m "$DATA" || \
            log "MQTT-Veröffentlichung fehlgeschlagen"

        sleep 60
    done
}

main
