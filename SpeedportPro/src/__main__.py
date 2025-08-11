#!/usr/bin/env python3
import os, time, requests
from playwright.sync_api import sync_playwright

ROUTER_IP   = os.getenv("router_ip", "192.168.2.1")
ROUTER_PWD  = os.getenv("router_password")
INTERVAL    = int(os.getenv("interval", 60))

HASS_URL   = "http://supervisor/core/api"
HASS_TOKEN = os.getenv("SUPERVISOR_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {HASS_TOKEN}",
    "Content-Type": "application/json"
}

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        try:
            page.goto(f"http://{ROUTER_IP}/6.5/gui/login/")
            page.fill('input[name="password"]', ROUTER_PWD)
            page.click('button[type="submit"]')
            page.wait_for_url(f"http://{ROUTER_IP}/6.5/gui/status/")

            return {
                "dsl_down":   int(page.locator("label[ng-bind='fields.internet.internetConnectionDownstream']").inner_text(timeout=5000).strip()),
                "dsl_up":     int(page.locator("label[ng-bind='fields.internet.internetConnectionUpstream']").inner_text(timeout=5000).strip()),
                "dsl_status": page.locator("span[translate='dslLink'] + div span").inner_text(timeout=5000).strip(),
                "lte_status": page.locator("span[translate='status_content_28'] + div span").inner_text(timeout=5000).strip(),
                "dsl_pop":    page.locator("span[ng-bind='fields.internet.dslPop']").inner_text(timeout=5000).strip(),
            }
        finally:
            browser.close()

def publish_hass(data):
    for key, value in data.items():
        unit = "kbit/s" if key.endswith(("down", "up")) else None
        payload = {
            "state": value,
            "attributes": {"unit_of_measurement": unit}
        }
        url = f"{HASS_URL}/states/sensor.speedport_{key}"
        requests.post(url, headers=HEADERS, json=payload)

if __name__ == "__main__":
    while True:
        try:
            publish_hass(scrape())
        except Exception as e:
            print("Fehler:", e)
        time.sleep(INTERVAL)
