ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# 1) Python inkl. pip nachinstallieren
RUN apk add --no-cache \
        python3 \
        py3-pip \
        gcc \
        musl-dev \
        libxml2-dev \
        libxslt-dev

# 2) Python-Abhängigkeiten
RUN pip3 install --no-cache-dir \
        requests \
        paho-mqtt \
        beautifulsoup4 \
        lxml

COPY rootfs/ /
COPY run.sh /run.sh

WORKDIR /app

RUN chmod +x /run.sh /etc/services.d/speedportpro/run
