import json
import time
import hmac
import hashlib
import threading
import requests
import paho.mqtt.client as mqtt
import os
from datetime import datetime
from collections import defaultdict
import queue
import concurrent.futures
import sys
from database import DeviceDB

# ================= CONFIG =================
BROKER = os.getenv("NODE_MQTT_HOST")
PORT = int(os.getenv("NODE_MQTT_PORT"))
MQTT_TOPIC_REQUEST_CH_CONFIG = os.getenv("NODE_MQTT_TOPIC_REQ")
MQTT_TOPIC_COUNTER_CH_CONFIG = os.getenv("NODE_MQTT_TOPIC_RES")

MQTT_USERNAME = os.getenv("NODE_MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("NODE_MQTT_PASSWORD")
BASE_URL = os.getenv("NODE_BASE_URL")

HEARTBEAT_INTERVAL = 10  # seconds
# =========================================

# MESH_REPEATER = "G003"

# ===== DEVICE ID MAPPING (DYNAMIC) =====
arr_device_ID_from = []
arr_device_ID_to = []
arr_device_secret = []
arr_ok_ng = []

def load_device_config():
    try:
        db = DeviceDB()
        mappings = db.load_mappings()
        
        if not mappings:
            print("[CONFIG] WARNING: No device mappings found in the database for this gateway.")
            return
            
        for row in mappings:
            arr_device_ID_from.append(row['device_id_from'])
            arr_device_ID_to.append(row['device_id_to'])
            arr_device_secret.append(row['device_secret'])
            arr_ok_ng.append([row['ok_channel'], row['ng_channel']])
            
        print(f"[CONFIG] Successfully loaded {len(mappings)} device mappings.")
    except Exception as e:
        print(f"[CRITICAL] Error loading mappings from database: {e}")
        print("[CRITICAL] Stopping service execution.")
        sys.exit(1)

load_device_config()
# =======================================

# Rate limiting tracking - last send time per device
last_send_time = defaultdict(float)
send_lock = threading.Lock()

# Message queue per device for rate-limited messages
device_message_queues = defaultdict(queue.Queue)
queue_processor_lock = threading.Lock()

# Thread pool for non-blocking HTTP requests
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

# Track if queue processor is running per device
queue_processor_running = defaultdict(bool)

def log_mqtt_message(topic, payload):
    """
    Logs every MQTT message to a file based on the current date.
    Creates a new file automatically if it doesn't exist.
    """
    try:
        # File name respects current date/time (e.g., mqtt_log_2026-03-26.log)
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_dir = "logs"
        log_filename = f"{log_dir}/mqtt_log_{current_date}.log"

        # Ensure the 'logs' directory exists inside the container
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Exact system time for the log entry inside the file
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # "a" mode creates the file if it doesn't exist and appends to it
        with open(log_filename, "a", encoding="utf-8") as f:
            f.write(f"[{current_time}] TOPIC: {topic} | PAYLOAD: {payload}\n")
    except Exception as e:
        print(f"[LOGGING ERROR] Failed to write to log: {e}")

def _send_data_blocking(device_uid, secret, count, status, base_url):
    """Internal blocking function that actually sends the data"""
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
        return False

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
        return res.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[SEND] HTTP error: {e}")
        return False

def _process_device_queue(device_uid, secret, base_url):
    """
    Background processor that sends queued messages for a device
    when rate limit allows (1 second between sends)
    """
    while True:
        current_time = time.time()
        
        with send_lock:
            time_since_last_send = current_time - last_send_time[device_uid]
            
            if time_since_last_send >= 1.0 and not device_message_queues[device_uid].empty():
                # Get next message from queue
                msg_data = device_message_queues[device_uid].get_nowait()
                
                # Update last send time
                last_send_time[device_uid] = current_time
            else:
                # Need to wait - release lock and sleep
                wait_time = max(0.1, 1.0 - time_since_last_send)
                # Check if queue is empty, if so, exit processor
                if device_message_queues[device_uid].empty():
                    with queue_processor_lock:
                        queue_processor_running[device_uid] = False
                    return
                # Release lock while sleeping
                pass
        
        # If we have a message to send, send it
        if time_since_last_send >= 1.0 and msg_data:
            count, status = msg_data
            executor.submit(_send_data_blocking, device_uid, secret, count, status, base_url)
            msg_data = None
        else:
            # Wait before checking again
            time.sleep(0.1)

def send_data(device_uid, secret, count, status, base_url):
    """
    Non-blocking send_data function with rate limiting (max once per second per device)
    Messages that exceed rate limit are queued and sent later
    """
    current_time = time.time()
    
    with send_lock:
        # Check if we can send immediately (at least 1 second since last send for this device)
        if current_time - last_send_time[device_uid] >= 1.0:
            # Update last send time immediately to prevent multiple quick calls
            last_send_time[device_uid] = current_time
            
            # Submit the actual sending to thread pool (non-blocking)
            executor.submit(_send_data_blocking, device_uid, secret, count, status, base_url)
            print(f"[SEND] {device_uid} - sent immediately")
            return True
        else:
            # Rate limited - queue the message for later
            msg_data = (count, status)
            device_message_queues[device_uid].put(msg_data)
            print(f"[SEND] {device_uid} - rate limited, message queued (queue size: {device_message_queues[device_uid].qsize()})")
            
            # Start queue processor if not already running for this device
            with queue_processor_lock:
                if not queue_processor_running[device_uid]:
                    queue_processor_running[device_uid] = True
                    threading.Thread(
                        target=_process_device_queue,
                        args=(device_uid, secret, base_url),
                        daemon=True
                    ).start()
            
            return False

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
        #client.subscribe(TOPIC)
        for device_id in arr_device_ID_from:
            topic = f"{device_id}/counting"
            client.subscribe(topic)
            print(f"[MQTT] Subscribed to {topic}")
        
        # subscribe to config response topic
        client.subscribe(MQTT_TOPIC_COUNTER_CH_CONFIG)
        print(f"[MQTT] Subscribed to {MQTT_TOPIC_COUNTER_CH_CONFIG}")

        # publish request config (only once after connect)
        # publish config request for each node
        # for node_id in arr_device_ID_from:
        #     doc = {
        #         "repeater_id": MESH_REPEATER,
        #         "node_id": node_id
        #     }
        #     payload = json.dumps(doc)
        #     client.publish(MQTT_TOPIC_REQUEST_CH_CONFIG, payload)
        #     print(f"[MQTT] Sent config request: {payload}")
        # print(f"[MQTT] Published config request to {MQTT_TOPIC_REQUEST_CH_CONFIG}")

    else:
        print(f"[MQTT] Connect failed rc={reason_code}")

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print("[MQTT] Disconnected")

def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload_str = msg.payload.decode('utf-8', errors='replace')

        log_mqtt_message(topic, payload_str)

        # ===== CONFIG RESPONSE =====
        if topic == MQTT_TOPIC_COUNTER_CH_CONFIG:
            print(f"[CONFIG RESPONSE] {payload_str}")
            return

        for i, device_id in enumerate(arr_device_ID_from):
            target_topic = f"{device_id}/counting"
            
            if topic == target_topic:
                print(f"[MQTT] Incoming from {device_id}: {payload_str}")
                
                try:
                    data = json.loads(payload_str)
                    
                    # 1. Extract the channel from the JSON payload
                    channel = data.get("channel")
                    
                    # 2. Get the OK and NG channel numbers for this specific device
                    ok_channel = arr_ok_ng[i][0]
                    ng_channel = arr_ok_ng[i][1]
                    
                    # 3. Determine the status based on the channel
                    if channel == ok_channel:
                        status = "OK"
                    elif channel == ng_channel:
                        status = "NG"
                    else:
                        print(f"[MQTT] Ignored: Channel {channel} is not mapped as OK or NG for {device_id}.")
                        return # Stop here, don't send unknown channels to the cloud
                    
                    # 4. Extract count (default to 1 if not present in your JSON)
                    count = data.get("count", 1) 
                    
                    # Forward to Cloud API with the new dynamic status
                    # This is now non-blocking and rate-limited with queuing
                    send_data(
                        arr_device_ID_to[i], 
                        arr_device_secret[i], 
                        count, 
                        status, 
                        BASE_URL
                    )
                except json.JSONDecodeError:
                    print(f"[MQTT] Error: Received invalid JSON from {device_id}")
                return

    except Exception as e:
        print(f"[MQTT] Error processing message on topic {topic}: {e}")


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
