ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# Abhängigkeiten
RUN apk add --no-cache \
        curl \
        jq \
        mosquitto-clients \
        bash

# Deine Start-Skripte kopieren
COPY rootfs/ /

# Rechte nur für vorhandene Skripte setzen
RUN chmod +x /etc/services.d/*/run

# Kein CMD/ENTRYPOINT – s6 startet automatisch
