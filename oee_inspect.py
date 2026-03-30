# ================ NEW CODE =======================

import json
import time
import hmac
import hashlib
import threading
import requests
import paho.mqtt.client as mqtt
import os

# ================= CONFIG =================
BROKER = "localhost"
PORT = int(os.getenv("NODE_MQTT_PORT"))
TOPIC = "counter/mesin/jobsend"

MQTT_USERNAME = os.getenv("NODE_MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("NODE_MQTT_PASSWORD")
BASE_URL = os.getenv("NODE_BASE_URL")

HEARTBEAT_INTERVAL = 10  # seconds
# =========================================


# ===== DEVICE ID MAPPING =====
arr_device_ID_from = [
  "HAS-AI-0002",
  "HAS-AI-0010"
]

arr_device_ID_to = [
  "0bd548e2-1833-408d-a7f2-45166edaa80d",
  "cc4bd528-5867-45e3-8034-9cb3462ea1e7"
]

# DEVICE_SECRET for API (same index!)
arr_device_secret = [
  "AsWtA0I-dPRkWWGlZp-M_jfNZ94V2aoh97F2lk5fOAg",
  "IzR39wTVo5bOD6WUDG2MjW-9JMUh2LPwlTV9baUh72U"
]

# TOTAL SENSOR PER DEVICE
arr_total_sensor = [
  24,
  16
]

assert (
  len(arr_device_ID_from)
  == len(arr_device_ID_to)
  == len(arr_device_secret)
  == len(arr_total_sensor)
), "Device mapping arrays length mismatch"
# =============================


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
    client.subscribe(TOPIC)
  else:
    print(f"[MQTT] Connect failed rc={reason_code}")

def on_disconnect(client, userdata, reason_code, properties):
  print("[MQTT] Disconnected")


def on_message(client, userdata, msg):
  try:
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
threading.Thread(
  target=heartbeat_loop,
  daemon=True
).start()

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.reconnect_delay_set(min_delay=1, max_delay=30)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.connect(BROKER, PORT, keepalive=60)
client.loop_forever()
