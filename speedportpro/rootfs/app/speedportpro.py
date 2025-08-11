#!/usr/bin/env python3
import os, time, json, requests, paho.mqtt.client as mqtt
from bs4 import BeautifulSoup

ROUTER_IP   = os.getenv('ROUTER_HOST', '192.168.2.1')
ROUTER_URL  = f'http://{ROUTER_IP}/6.5/gui/status/'
SCAN_INT    = int(os.getenv('SCAN_INTERVAL', 30))
MQTT_HOST   = os.getenv('MQTT_HOST', 'localhost')
MQTT_PORT   = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC  = os.getenv('MQTT_TOPIC_PREFIX', 'speedport')

s = requests.Session()

def mqtt_publish(topic, payload, retain=True):
    mqtt_client.publish(f'{MQTT_TOPIC}/{topic}', payload, retain=retain, qos=0)

def mqtt_ha_config(sensor_id, name, unit=None, dev_class=None):
    cfg = {
        "name": name,
        "state_topic": f'{MQTT_TOPIC}/sensor/{sensor_id}/state',
        "unique_id": f'speedport_{sensor_id}',
        "device": {
            "identifiers": ["speedport_pro"],
            "name": "Speedport Pro",
            "manufacturer": "Telekom",
            "model": "Speedport Pro"
        }
    }
    if unit: cfg["unit_of_measurement"] = unit
    if dev_class: cfg["device_class"] = dev_class
    mqtt_client.publish(f'homeassistant/sensor/speedport/{sensor_id}/config',
                        json.dumps(cfg), retain=True)

def fetch_status():
    r = s.get(ROUTER_URL, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    def sel(attr, cast=str):
        el = soup.select_one(f'[ng-bind="fields.{attr}"]')
        return cast(el.get_text(strip=True)) if el else None

    def label_sel(label_trans, cast=str):
        el = soup.select_one(f'label[translate="{label_trans}"] + label')
        return cast(el.get_text(strip=True)) if el else None

    data = {
        'dsl_sync_down': label_sel('downstream', int),
        'dsl_sync_up'  : label_sel('upstream', int),
        'dsl_status'   : 'online' if soup.select_one('span[translate="status_content_online"]') else 'offline',
        'dsl_pop'      : sel('internet.dslPop'),
        'firmware'     : sel('statusInformation.firmwareVersion'),
        'serial'       : sel('statusInformation.serialNumber'),
        'lan1_speed'   : soup.select_one('.lanPort:-soup-contains("[1]") + span').get_text(strip=True) if soup.select_one('.lanPort:-soup-contains("[1]") + span') else 'offline',
        'wifi_2g_ssid' : sel('homeNetwork.wifi2gSSID'),
        'wifi_5g_ssid' : sel('homeNetwork.wifi5gSSID'),
        'wifi_2g_clients': sel('homeNetwork.devicesWifi2g.length', int) or 0,
        'wifi_5g_clients': sel('homeNetwork.devicesWifi5g.length', int) or 0,
        'dect_registered': sel('telephony.registeredTelephones', int) or 0
    }
    return data

def main():
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
    mqtt_client.loop_start()

    # Home-Assistant Discovery anlegen
    mqtt_ha_config('dsl_sync_down', 'DSL Sync Down', 'kbit/s')
    mqtt_ha_config('dsl_sync_up',   'DSL Sync Up',   'kbit/s')
    mqtt_ha_config('dsl_status',    'DSL Status')
    mqtt_ha_config('dsl_pop',       'DSL POP')
    mqtt_ha_config('firmware',      'Firmware')
    mqtt_ha_config('serial',        'Serial')
    mqtt_ha_config('lan1_speed',    'LAN1 Speed')
    mqtt_ha_config('wifi_2g_clients', '2.4 GHz Clients')
    mqtt_ha_config('wifi_5g_clients', '5 GHz Clients')
    mqtt_ha_config('dect_registered', 'DECT Registered')

    while True:
        try:
            data = fetch_status()
            for k, v in data.items():
                mqtt_publish(f'sensor/{k}/state', v)
        except Exception as e:
            print('Fehler:', e)
        time.sleep(SCAN_INT)

if __name__ == '__main__':
    mqtt_client = mqtt.Client()
    main()
