# ================ NEW CODE =======================

import json
import time
import hmac
import hashlib
import threading
import requests
import paho.mqtt.client as mqtt
import os
import sys
from database import DeviceDB

# ================= CONFIG =================
BROKER = os.getenv("NODE_MQTT_HOST")
PORT = int(os.getenv("NODE_MQTT_PORT"))
TOPIC = os.getenv("INSPECT_MQTT_TOPIC")

MQTT_USERNAME = os.getenv("NODE_MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("NODE_MQTT_PASSWORD")
BASE_URL = os.getenv("NODE_BASE_URL")

HEARTBEAT_INTERVAL = 10  # seconds
# =========================================


# ===== DEVICE ID MAPPING (DYNAMIC) =====
arr_device_ID_from = []
arr_device_ID_to = []
arr_device_secret = []
arr_total_sensor = []

def load_inspection_config(client=None):
    global arr_device_ID_from, arr_device_ID_to, arr_device_secret, arr_total_sensor
    try:
        db = DeviceDB()
        mappings = db.load_inspection_mappings()
        
        arr_device_ID_from.clear()
        arr_device_ID_to.clear()
        arr_device_secret.clear()
        arr_total_sensor.clear()
        
        if not mappings:
            print("[CONFIG] WARNING: No inspection device mappings found in the database.")
            return
            
        for row in mappings:
            arr_device_ID_from.append(row['device_id_from'])
            arr_device_ID_to.append(row['device_id_to'])
            arr_device_secret.append(row['device_secret'])
            arr_total_sensor.append(row['total_sensor'])
            
        print(f"[CONFIG] Successfully loaded {len(mappings)} inspection device mappings.")
    except Exception as e:
        print(f"[CRITICAL] Error loading inspection mappings from database: {e}")
        if client is None:
            print("[CRITICAL] Stopping Inspection service execution.")
            sys.exit(1)

load_inspection_config()
# =========================================


def send_data(device_uid, secret, count, status, base_url):
  timestamp = int(time.time())
  payload = {"count": count, "status": status}
  body_bytes = json.dumps(payload).encode("utf-8")
  timestamp_str = str(timestamp)

  try:
    message = timestamp_str.encode("utf-8") + body_bytes
    signature = hmac.new(
      secret.encode("utf-8"),
      message,
      hashlib.sha256
    ).hexdigest()
  except Exception as e:
    print(f"[SEND] Sign error: {e}")
    return

  headers = {
    "X-Device-Uid": device_uid,
    "X-Timestamp": timestamp_str,
    "X-Signature": signature,
    "Content-Type": "application/json"
  }

  full_url = f"{base_url}/api/devices/counts"

  try:
    res = requests.post(full_url, data=body_bytes, headers=headers, timeout=5)
    print(f"[SEND] {device_uid} {status} -> {res.status_code}")
  except requests.exceptions.RequestException as e:
    print(f"[SEND] HTTP error: {e}")


def send_heartbeat(device_uid, secret, base_url):
  timestamp = int(time.time())
  body_bytes = b""
  timestamp_str = str(timestamp)

  try:
    message = timestamp_str.encode("utf-8") + body_bytes
    signature = hmac.new(
      secret.encode("utf-8"),
      message,
      hashlib.sha256
    ).hexdigest()
  except Exception as e:
    print(f"[HB] Sign error: {e}")
    return

  headers = {
    "X-Device-Uid": device_uid,
    "X-Timestamp": timestamp_str,
    "X-Signature": signature,
  }

  try:
    res = requests.post(
      f"{base_url}/api/devices/heartbeat",
      data=body_bytes,
      headers=headers,
      timeout=5
    )
    print(f"[HB] {device_uid} -> {res.status_code}")
  except requests.exceptions.RequestException as e:
    print(f"[HB] HTTP error: {e}")


def heartbeat_loop():
  while True:
    for uid, secret in zip(arr_device_ID_to, arr_device_secret):
      send_heartbeat(uid, secret, BASE_URL)
    time.sleep(HEARTBEAT_INTERVAL)


def on_connect(client, userdata, flags, reason_code, properties):
  if reason_code == 0:
    print("[MQTT] Connected")
    if TOPIC:
      client.subscribe(TOPIC)
    client.subscribe("system/gateway/reload_config")
  else:
    print(f"[MQTT] Connect failed rc={reason_code}")

def on_disconnect(client, userdata, reason_code, properties):
  print("[MQTT] Disconnected")


def on_message(client, userdata, msg):
  try:
    if msg.topic == "system/gateway/reload_config":
      print("[SYSTEM] Received hot-swap reload signal from Web UI!")
      load_inspection_config(client)
      return

    payload = json.loads(msg.payload.decode())

    mesin_id = payload.get("MESIN_ID")
    sensor_ids = list(map(int, payload.get("SENSOR_ID", [])))
    # count = payload.get("CYCLE", 1)
    count = 1

    if mesin_id not in arr_device_ID_from:
      print(f"[MAP] Unknown MESIN_ID: {mesin_id}")
      return

    idx = arr_device_ID_from.index(mesin_id)
    mapped_device_uid = arr_device_ID_to[idx]
    device_secret = arr_device_secret[idx]
    total_sensor = arr_total_sensor[idx]

    expected = list(range(1, total_sensor + 1))
    status = "OK" if sensor_ids == expected else "NG"

    send_data(
      device_uid=mapped_device_uid,
      secret=device_secret,
      count=count,
      status=status,
      base_url=BASE_URL
    )

  except Exception as e:
    print(f"[MQTT] Error processing message: {e}")


# ================= STARTUP =================

# Start heartbeat thread
# threading.Thread(
#   target=heartbeat_loop,
#   daemon=True
# ).start()

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.reconnect_delay_set(min_delay=1, max_delay=30)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.connect(BROKER, PORT, keepalive=60)
client.loop_forever()
