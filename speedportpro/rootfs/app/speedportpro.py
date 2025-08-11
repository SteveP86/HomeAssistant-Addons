#!/usr/bin/env python3
"""
Speedport Pro Status Scraper für Home-Assistant
Liest die HTML-Statusseite des Speedport Pro aus und
veröffentlicht die Werte via MQTT (Discovery).
"""

import json
import os
import time
import requests
import paho.mqtt.client as mqtt
from bs4 import BeautifulSoup

# --------------------------------------------------------------------------- #
# Konfiguration aus Home-Assistant-Add-on
# --------------------------------------------------------------------------- #
def read_config() -> dict:
    """/data/options.json (vom Supervisor gemountet) einlesen."""
    with open("/data/options.json", "r", encoding="utf-8") as fp:
        return json.load(fp)


CFG = read_config()
ROUTER_HOST = CFG["router_host"]
SCAN_INT    = int(CFG["scan_interval"])
MQTT_HOST   = CFG["mqtt_host"]
MQTT_PORT   = int(CFG["mqtt_port"])
MQTT_USER   = CFG["mqtt_user"]
MQTT_PASS   = CFG["mqtt_pass"]
MQTT_TOPIC  = CFG["mqtt_topic_prefix"].rstrip("/")

# --------------------------------------------------------------------------- #
# MQTT
# --------------------------------------------------------------------------- #
mqtt_client = mqtt.Client()
if MQTT_USER and MQTT_PASS:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)


def mqtt_publish(topic: str, payload, retain=True):
    """Publiziert einen Wert unter <MQTT_TOPIC>/sensor/<topic>/state."""
    full_topic = f"{MQTT_TOPIC}/sensor/{topic}/state"
    mqtt_client.publish(full_topic, str(payload), qos=0, retain=retain)


def mqtt_ha_config(sensor_id: str, name: str, unit=None, dev_class=None):
    """Home-Assistant Discovery-Nachricht senden."""
    cfg = {
        "name": name,
        "state_topic": f"{MQTT_TOPIC}/sensor/{sensor_id}/state",
        "unique_id": f"speedport_{sensor_id}",
        "device": {
            "identifiers": ["speedport_pro"],
            "name": "Speedport Pro",
            "manufacturer": "Telekom",
            "model": "Speedport Pro",
        },
    }
    if unit:
        cfg["unit_of_measurement"] = unit
    if dev_class:
        cfg["device_class"] = dev_class

    disc_topic = f"homeassistant/sensor/speedport/{sensor_id}/config"
    mqtt_client.publish(disc_topic, json.dumps(cfg), qos=0, retain=True)


# --------------------------------------------------------------------------- #
# Router-Scraper
# --------------------------------------------------------------------------- #
def fetch_status() -> dict:
    """Router-Statusseite laden und relevante Werte extrahieren."""
    url = f"http://{ROUTER_HOST}/6.5/gui/status/"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Router nicht erreichbar: {exc}") from exc

    soup = BeautifulSoup(resp.text, "lxml")

    def sel(attr, cast=str):
        el = soup.select_one(f'[ng-bind="fields.{attr}"]')
        return cast(el.get_text(strip=True)) if el else None

    def label_sel(txt, cast=str):
        el = soup.select_one(f'label[translate="{txt}"] + label')
        return cast(el.get_text(strip=True)) if el else None

    # DSL-Sync
    dsl_down = label_sel("downstream", int)
    dsl_up   = label_sel("upstream", int)

    # DSL-Status
    dsl_status = "online" if soup.select_one('span[translate="status_content_online"]') else "offline"

    # Sonstiges
    dsl_pop      = sel("internet.dslPop")
    firmware     = sel("statusInformation.firmwareVersion")
    serial_no    = sel("statusInformation.serialNumber")

    # LAN-Port 1
    lan1_el = soup.select_one('.lanPort:-soup-contains("[1]") + span')
    lan1_speed = lan1_el.get_text(strip=True) if lan1_el else "offline"

    # WLAN-Clients
    wifi_2g_clients = sel("homeNetwork.devicesWifi2g.length", int) or 0
    wifi_5g_clients = sel("homeNetwork.devicesWifi5g.length", int) or 0

    # DECT
    dect_reg = sel("telephony.registeredTelephones", int) or 0

    return {
        "dsl_sync_down": dsl_down,
        "dsl_sync_up":   dsl_up,
        "dsl_status":    dsl_status,
        "dsl_pop":       dsl_pop,
        "firmware":      firmware,
        "serial":        serial_no,
        "lan1_speed":    lan1_speed,
        "wifi_2g_clients": wifi_2g_clients,
        "wifi_5g_clients": wifi_5g_clients,
        "dect_registered": dect_reg,
    }


# --------------------------------------------------------------------------- #
# Haupt-Loop
# --------------------------------------------------------------------------- #
def main():
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
    mqtt_client.loop_start()

    # Discovery anlegen
    mqtt_ha_config("dsl_sync_down", "DSL Sync Down", "kbit/s")
    mqtt_ha_config("dsl_sync_up",   "DSL Sync Up",   "kbit/s")
    mqtt_ha_config("dsl_status",    "DSL Status")
    mqtt_ha_config("dsl_pop",       "DSL POP")
    mqtt_ha_config("firmware",      "Firmware")
    mqtt_ha_config("serial",        "Serial")
    mqtt_ha_config("lan1_speed",    "LAN1 Speed")
    mqtt_ha_config("wifi_2g_clients", "2.4 GHz Clients")
    mqtt_ha_config("wifi_5g_clients", "5 GHz Clients")
    mqtt_ha_config("dect_registered", "DECT Registered")

    while True:
        try:
            data = fetch_status()
            for key, value in data.items():
                mqtt_publish(key, value)
        except Exception as exc:
            print("Fehler:", exc)
        time.sleep(SCAN_INT)


if __name__ == "__main__":
    main()
