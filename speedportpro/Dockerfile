ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# Installiere Abhängigkeiten
RUN apk add --no-cache \
    curl \
    jq \
    mosquitto-clients \
    bash

# Kopiere Skripte
COPY run.sh /
RUN chmod a+x /run.sh

# Startbefehl
CMD [ "/bin/bash", "/run.sh" ]
