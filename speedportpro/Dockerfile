ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

RUN apk add --no-cache curl jq mosquitto-clients bash

# Debug: vorher anzeigen, was vorhanden ist
RUN echo "=== Vor COPY ===" && ls -la / && echo "---"

# 1. rootfs/ kopieren
COPY rootfs/ /

# 2. run.sh kopieren
COPY run.sh /run.sh

# Debug: nachher anzeigen
RUN echo "=== Nach COPY ===" && \
    ls -la /run.sh /etc/services.d/speedportpro/run 2>/dev/null || \
    (echo "FEHLER: Dateien fehlen!" && exit 1)

# Rechte setzen
RUN chmod +x /run.sh /etc/services.d/speedportpro/run
