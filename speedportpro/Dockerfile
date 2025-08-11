ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

RUN apk add --no-cache \
        python3 \
        py3-requests \
        py3-paho-mqtt \
        py3-beautifulsoup4 \
        py3-lxml

COPY rootfs/ /
COPY run.sh /run.sh

WORKDIR /app

RUN chmod +x /run.sh /etc/services.d/speedportpro/run
