ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk add --no-cache \
    python3 py3-pip \
    chromium nss freetype freetype-dev harfbuzz ca-certificates ttf-freefont

COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && \
    playwright install chromium --with-deps

COPY src/ /src/
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD [ "/run.sh" ]
