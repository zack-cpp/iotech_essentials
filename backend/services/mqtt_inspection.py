"""
Inspection Node MQTT Service — dynamic replacement for oee_inspect.py.

Loads inspection device mappings from the database, subscribes to the
configured inspection topic, compares sensor arrays, and forwards
OK/NG classification to the cloud via HTTP with HMAC signing.

Supports hot-reload via the system/gateway/reload_config MQTT topic.
"""
import json
import time
import threading
import sys
import os

import paho.mqtt.client as mqtt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from database import SessionLocal, InspectionDevice
from services.http_forwarder import get_limiter

settings = get_settings()

# ===== Dynamic device mappings =====
devices = []  # list of dicts from DB
devices_lock = threading.Lock()

HEARTBEAT_INTERVAL = 10


def load_config(client=None):
    """Load inspection device mappings from PostgreSQL."""
    global devices
    try:
        db = SessionLocal()
        rows = db.query(InspectionDevice).filter(
            InspectionDevice.gateway_id == settings.GATEWAY_ID,
            InspectionDevice.is_active == True,
        ).all()
        db.close()

        with devices_lock:
            devices.clear()
            for row in rows:
                devices.append({
                    "node_id": row.node_id,
                    "cloud_uid": row.cloud_uid,
                    "device_secret": row.device_secret,
                    "total_sensor": row.total_sensor,
                })

        print(f"[INSPECT] Loaded {len(devices)} inspection device mappings.")
    except Exception as e:
        print(f"[INSPECT] CRITICAL — failed to load config: {e}")
        if client is None:
            sys.exit(1)


def heartbeat_loop():
    """Periodic heartbeat for all active inspection devices."""
    while True:
        with devices_lock:
            current = list(devices)
        for d in current:
            limiter = get_limiter(d["cloud_uid"], d["device_secret"], settings.HTTP_TARGET_URL)
            limiter.enqueue("heartbeat")
        time.sleep(HEARTBEAT_INTERVAL)


# ===== MQTT Callbacks =====

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[INSPECT] MQTT connected")
        if settings.INSPECT_MQTT_TOPIC:
            client.subscribe(settings.INSPECT_MQTT_TOPIC)
            print(f"[INSPECT] Subscribed to {settings.INSPECT_MQTT_TOPIC}")
        client.subscribe("system/gateway/reload_config")
    else:
        print(f"[INSPECT] MQTT connect failed rc={reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print("[INSPECT] MQTT disconnected")


def on_message(client, userdata, msg):
    try:
        # Hot-reload signal
        if msg.topic == "system/gateway/reload_config":
            print("[INSPECT] Hot-reload signal received!")
            load_config(client)
            return

        payload = json.loads(msg.payload.decode())

        mesin_id = payload.get("MESIN_ID")
        sensor_ids = list(map(int, payload.get("SENSOR_ID", [])))
        count = 1

        with devices_lock:
            current = list(devices)

        # Find matching device
        target = None
        for d in current:
            if d["node_id"] == mesin_id:
                target = d
                break

        if not target:
            print(f"[INSPECT] Unknown MESIN_ID: {mesin_id}")
            return

        # Compare sensor array against expected full range
        expected = list(range(1, target["total_sensor"] + 1))
        status = "OK" if sensor_ids == expected else "NG"

        limiter = get_limiter(
            device_uid=target["cloud_uid"],
            secret=target["device_secret"],
            base_url=settings.HTTP_TARGET_URL,
        )
        limiter.enqueue("count", count=count, status=status)

    except Exception as e:
        print(f"[INSPECT] Error processing message: {e}")


# ===== Main =====

def main():
    load_config()

    # Start heartbeat
    threading.Thread(target=heartbeat_loop, daemon=True).start()

    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
        client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    while True:
        try:
            client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
            break
        except Exception as e:
            print(f"[INSPECT] MQTT connection failed: {e}. Retrying in 5s...")
            time.sleep(5)

    client.loop_forever()


if __name__ == "__main__":
    main()
