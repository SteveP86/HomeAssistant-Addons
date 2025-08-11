ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

RUN apk add --no-cache curl jq mosquitto-clients bash

COPY rootfs/ /
COPY run.sh /run.sh

RUN chmod +x /run.sh /etc/services.d/speedportpro/run
