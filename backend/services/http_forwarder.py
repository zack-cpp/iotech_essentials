"""
Shared HTTP forwarding logic — HMAC-SHA256 signing and cloud API posting.
Extracted from the original oee_node.py and oee_inspect.py scripts.
"""
import json
import time
import hmac
import hashlib
import requests


def send_count_data(device_uid: str, secret: str, count: int, status: str, base_url: str):
    """Sign and POST a count event to the cloud API."""
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
        print(f"[HTTP] Sign error: {e}")
        return False

    headers = {
        "X-Device-Uid": device_uid,
        "X-Timestamp": timestamp_str,
        "X-Signature": signature,
        "Content-Type": "application/json",
    }

    full_url = f"{base_url}/api/devices/counts"

    try:
        res = requests.post(full_url, data=body_bytes, headers=headers, timeout=5)
        print(f"[HTTP] {device_uid} {status} -> {res.status_code}")
        return res.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[HTTP] POST error: {e}")
        return False


def send_heartbeat(device_uid: str, secret: str, base_url: str):
    """Sign and POST a heartbeat to the cloud API."""
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
            timeout=5,
        )
        print(f"[HB] {device_uid} -> {res.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[HB] HTTP error: {e}")
