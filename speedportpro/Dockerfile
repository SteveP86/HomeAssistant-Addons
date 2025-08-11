ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

RUN apk add --no-cache curl jq mosquitto-clients bash

# 1. s6-Service kopieren
COPY rootfs/ /

# 2. run.sh aus dem ADDON-Ordner nach / kopieren
COPY run.sh /run.sh

# Rechte setzen
RUN chmod +x /etc/services.d/speedportpro/run /run.sh
