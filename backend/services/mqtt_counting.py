"""
Counting Node MQTT Service — dynamic replacement for oee_node.py.

Loads counting device mappings from the database, subscribes to
{node_id}/counting topics, classifies OK/NG by channel, and forwards
to the cloud via HTTP with HMAC signing.

Supports hot-reload via the system/gateway/reload_config MQTT topic.
"""
import json
import time
import threading
import sys
import os

import paho.mqtt.client as mqtt

# Ensure parent directory is on path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from database import SessionLocal, CountingDevice, SensorFusionRule
from services.http_forwarder import get_limiter
from services.mqtt_logger import mqtt_logger

settings = get_settings()

# ===== Dynamic device mappings =====
devices = []  # list of dicts from DB
fusion_rules = [] # list of fusion rules
devices_lock = threading.Lock()

import simpleeval
import math

def create_evaluator():
    s = simpleeval.SimpleEval()
    s.functions.update(math.__dict__)
    return s

HEARTBEAT_INTERVAL = 10


def load_config(client=None):
    """Load counting device mappings from PostgreSQL."""
    global devices
    try:
        db = SessionLocal()
        rows = db.query(CountingDevice).filter(
            CountingDevice.gateway_id == settings.GATEWAY_ID,
            CountingDevice.is_active == True,
        ).all()
        db.close()

        with devices_lock:
            # Unsubscribe old topics
            if client and client.is_connected():
                for d in devices:
                    client.unsubscribe(f"{d['node_id']}/counting")

            devices.clear()
            for row in rows:
                devices.append({
                    "node_id": row.node_id,
                    "cloud_uid": row.cloud_uid,
                    "device_secret": row.device_secret,
                    "ok_channel": row.ok_channel,
                    "ng_channel": row.ng_channel,
                })

            f_rows = db.query(SensorFusionRule).filter(
                SensorFusionRule.gateway_id == settings.GATEWAY_ID,
                SensorFusionRule.is_active == True,
            ).all()

            fusion_rules.clear()
            for r in f_rows:
                fusion_rules.append({
                    "id": r.id,
                    "source_node_id": r.source_node_id,
                    "source_channel": r.source_channel,
                    "source_field": r.source_field,
                    "formula": r.formula.replace("<source_1>", "source_1"),
                    "destination_node_id": r.destination_node_id,
                    "destination_channel": r.destination_channel,
                })

            # Subscribe to new topics
            if client and client.is_connected():
                for d in devices:
                    topic = f"{d['node_id']}/counting"
                    client.subscribe(topic)
                    print(f"[COUNTING] Subscribed to {topic}")
                for f in fusion_rules:
                    topic = f"{f['source_node_id']}/counting"
                    client.subscribe(topic)
                    print(f"[COUNTING] Subscribed to {topic} (Fusion)")

        print(f"[COUNTING] Loaded {len(devices)} device mappings and {len(fusion_rules)} fusion rules.")
    except Exception as e:
        print(f"[COUNTING] CRITICAL — failed to load config: {e}")
        if client is None:
            sys.exit(1)


def heartbeat_loop():
    """Periodic heartbeat for all active counting devices."""
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
        print("[COUNTING] MQTT connected")
        with devices_lock:
            for d in devices:
                topic = f"{d['node_id']}/counting"
                client.subscribe(topic)
                print(f"[COUNTING] Subscribed to {topic}")
            for f in fusion_rules:
                topic = f"{f['source_node_id']}/counting"
                client.subscribe(topic)
                print(f"[COUNTING] Subscribed to {topic} (Fusion)")
        client.subscribe("system/gateway/reload_config")
        client.subscribe("system/gateway/log_control")
    else:
        print(f"[COUNTING] MQTT connect failed rc={reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print("[COUNTING] MQTT disconnected")


def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload_str = msg.payload.decode("utf-8", errors="replace")

        # Hot-reload signal
        if topic == "system/gateway/reload_config":
            print("[COUNTING] Hot-reload signal received!")
            load_config(client)
            return

        # Log control signal
        if topic == "system/gateway/log_control":
            try:
                data = json.loads(payload_str)
                device_id = data.get("device_id")
                action = data.get("action")
                if action == "enable" and device_id:
                    mqtt_logger.enable(device_id)
                elif action == "disable" and device_id:
                    mqtt_logger.disable(device_id)
            except json.JSONDecodeError:
                pass
            return

        with devices_lock:
            current = list(devices)
            current_fusion = list(fusion_rules)

        try:
            data = json.loads(payload_str)
            channel = data.get("channel")
            
            # --- Fusion Rules Processing ---
            for f in current_fusion:
                if topic == f"{f['source_node_id']}/counting" and channel == f['source_channel']:
                    source_val = data.get(f['source_field'])
                    if source_val is not None:
                        try:
                            evaluator = create_evaluator()
                            evaluator.names = {"source_1": float(source_val)}
                            result = evaluator.eval(f['formula'])
                            
                            dest_device = next((d for d in current if d["node_id"] == f["destination_node_id"]), None)
                            if dest_device:
                                limiter = get_limiter(dest_device["cloud_uid"], dest_device["device_secret"], settings.HTTP_TARGET_URL)
                                limiter.enqueue("monitoring", channel=f["destination_channel"], value=result)
                                print(f"[FUSION] Evaluated rule {f['id']}: {result} -> Monitoring API ({dest_device['node_id']})")
                            else:
                                print(f"[FUSION] Error: Destination node {f['destination_node_id']} not found.")
                        except Exception as e:
                            print(f"[FUSION] Error evaluating rule {f['id']}: {e}")
        except json.JSONDecodeError:
            data = None

        for d in current:
            if topic == f"{d['node_id']}/counting":
                mqtt_logger.log(d['node_id'], topic, payload_str)
                if not data:
                    print(f"[COUNTING] Invalid JSON from {d['node_id']}")
                    return
                try:
                    channel = data.get("channel")
                    count = data.get("count", 1)

                    if channel == d["ok_channel"]:
                        status = "OK"
                    elif channel == d["ng_channel"]:
                        status = "NG"
                    else:
                        print(f"[COUNTING] Ignored channel {channel} for {d['node_id']}")
                        return

                    limiter = get_limiter(d["cloud_uid"], d["device_secret"], settings.HTTP_TARGET_URL)
                    limiter.enqueue("count", count=count, status=status)
                except Exception as e:
                    print(f"[COUNTING] Error handling payload from {d['node_id']}: {e}")
                return

    except Exception as e:
        print(f"[COUNTING] Error processing {topic}: {e}")


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
            print(f"[COUNTING] MQTT connection failed: {e}. Retrying in 5s...")
            time.sleep(5)

    client.loop_forever()


if __name__ == "__main__":
    main()
