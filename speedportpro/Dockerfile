ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# Python-Abhängigkeiten
RUN apk add --no-cache \
    gcc musl-dev libxml2-dev libxslt-dev && \
    pip install --no-cache-dir \
    requests paho-mqtt beautifulsoup4 lxml

COPY rootfs/ /
COPY run.sh /run.sh

RUN chmod +x /run.sh /etc/services.d/speedportpro/run
