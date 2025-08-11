ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# Installiere Abhängigkeiten
RUN apk add --no-cache \
        curl \
        jq \
        mosquitto-clients \
        bash

# Skripte in die richtige s6-Pfadstruktur kopieren
COPY rootfs/ /

# Rechte korrigieren
RUN chmod +x /etc/services.d/*/run /etc/cont-init.d/*

# Kein CMD/ENTRYPOINT nötig – s6 übernimmt alles
