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
    url = f"http://{ROUTER_HOST}/6.5/gui/status/"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Router nicht erreichbar: {exc}") from exc

    text = resp.text

    # 1. JavaScript-Block mit "fields = {" ... "};"
    import re, json
    m = re.search(r'fields\s*=\s*({.*?});', text, flags=re.S)
    if not m:
        raise RuntimeError("Kein 'fields = {...}' im HTML gefunden")

    # 2. Inhalt als JSON laden
    fields = json.loads(m.group(1))

    # 3. Werte extrahieren
    info = fields.get("statusInformation", {})
    inet = fields.get("internet", {})
    net  = fields.get("homeNetwork", {})
    tel  = fields.get("telephony", {})

    return {
        "dsl_sync_down": inet.get("internetConnectionDownstream"),
        "dsl_sync_up":   inet.get("internetConnectionUpstream"),
        "dsl_status":    "online" if inet.get("dslLink") == "up" else "offline",
        "dsl_pop":       inet.get("dslPop"),
        "firmware":      info.get("firmwareVersion"),
        "serial":        info.get("serialNumber"),
        "lan1_speed":    "1 Gbit/s" if net.get("devicesAtLan", {}).get("lan1") == "up" else "offline",
        "wifi_2g_clients": len(net.get("devicesWifi2g", [])),
        "wifi_5g_clients": len(net.get("devicesWifi5g", [])),
        "dect_registered": tel.get("registeredTelephones", 0),
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
