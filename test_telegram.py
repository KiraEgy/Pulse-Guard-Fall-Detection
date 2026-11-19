"""
Pulse-Guard Diagnostic Script — Stage 3: Wi-Fi & Telegram API Dispatch Test
Hardware: Raspberry Pi Pico 2 W (2.4 GHz Wi-Fi only)
Purpose: Independently verifies 2.4 GHz Wi-Fi connectivity, Telegram Bot API
         authentication, HTTP 200 status delivery, and round-trip alert latency.

Note: Replace the placeholder credentials below with your own before running.
"""
import network
import time
import urequests

# ---------------- CONFIGURATION (Placeholders for GitHub) ----------------
WIFI_SSID = "YOUR_2.4GHZ_WIFI_NAME"
WIFI_PASS = "YOUR_WIFI_PASSWORD"
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"


def run_diagnostic():
    print("1. Connecting to 2.4 GHz Wi-Fi:", WIFI_SSID)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)

    for attempt in range(1, 21):
        if wlan.isconnected():
            break
        print(f"   Waiting for Wi-Fi... ({attempt}/20)")
        time.sleep(0.5)

    if not wlan.isconnected():
        print("WIFI ERROR: Failed to connect.")
        print("Verify SSID/password and confirm the router/hotspot uses 2.4 GHz.")
        return

    print("   Wi-Fi Connected! Local IP:", wlan.ifconfig()[0])
    print("2. Sending test message to Telegram Bot API...")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "Pulse-Guard Diagnostic: 2.4 GHz Wi-Fi and Telegram API are operational!"
    }

    t0 = time.ticks_ms()
    try:
        response = urequests.post(url, json=payload)
        latency_s = time.ticks_diff(time.ticks_ms(), t0) / 1000.0
        print(f"   Telegram HTTP Status: {response.status_code}")
        print(f"   Dispatch Latency: {latency_s:.2f} s")
        print(f"   Server Reply: {response.text}")
        response.close()

        if response.status_code == 200:
            print("RESULT: PASS — Telegram alert delivered successfully.")
        elif response.status_code == 401:
            print("RESULT: FAIL (401) — Invalid TELEGRAM_BOT_TOKEN.")
        elif response.status_code == 400:
            print("RESULT: FAIL (400) — Check TELEGRAM_CHAT_ID or send /start to your bot.")
        else:
            print("RESULT: FAIL — Unexpected HTTP status.")
    except Exception as e:
        print("NETWORK ERROR:", e)


if __name__ == "__main__":
    run_diagnostic()
