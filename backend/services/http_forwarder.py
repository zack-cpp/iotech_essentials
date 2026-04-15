"""
Shared HTTP forwarding logic — HMAC-SHA256 signing and cloud API posting.

Includes:
- Persistent requests.Session with connection pooling and automatic retry
- Per-device DeviceRateLimiter enforcing >= 500ms between requests
- Thread-safe queue-based processing
"""
import json
import time
import hmac
import hashlib
import threading
import queue
from typing import Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── Persistent HTTP Session ────────────────────────────────────

_session_lock = threading.Lock()
_session: requests.Session = None


def _get_session() -> requests.Session:
    """Return a shared, thread-safe requests.Session with retry + backoff."""
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:
                s = requests.Session()
                retry = Retry(
                    total=3,
                    backoff_factor=1,          # 1s, 2s, 4s
                    status_forcelist=[502, 503, 504],
                    # 429 is NOT in status_forcelist — we handle it manually
                    # so we can log it and respect per-device timing
                    allowed_methods=["POST"],
                    raise_on_status=False,
                )
                adapter = HTTPAdapter(
                    max_retries=retry,
                    pool_connections=10,
                    pool_maxsize=20,
                )
                s.mount("https://", adapter)
                s.mount("http://", adapter)
                _session = s
    return _session


# ─── Core HTTP Functions ────────────────────────────────────────

MAX_429_RETRIES = 3
RETRY_429_DELAY = 1.0  # seconds to wait after a 429


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
    session = _get_session()

    for attempt in range(1, MAX_429_RETRIES + 1):
        try:
            res = session.post(full_url, data=body_bytes, headers=headers, timeout=10)
            if res.status_code == 429:
                print(f"[HTTP] {device_uid} {status} -> 429 (attempt {attempt}/{MAX_429_RETRIES})")
                if attempt < MAX_429_RETRIES:
                    time.sleep(RETRY_429_DELAY * attempt)  # linear backoff: 1s, 2s, 3s
                    continue
                return False
            print(f"[HTTP] {device_uid} {status} -> {res.status_code}")
            return res.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"[HTTP] POST error: {e}")
            return False

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

    session = _get_session()

    try:
        res = session.post(
            f"{base_url}/api/devices/heartbeat",
            data=body_bytes,
            headers=headers,
            timeout=10,
        )
        print(f"[HB] {device_uid} -> {res.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[HB] HTTP error: {e}")


# ─── Per-Device Rate Limiter ────────────────────────────────────

MIN_INTERVAL = 0.5  # 500ms between requests per device
IDLE_TIMEOUT = 30.0  # worker thread exits after 30s of no messages


class DeviceRateLimiter:
    """
    Thread-safe, per-device rate limiter with a background worker.

    Accepts enqueue() calls from any thread (MQTT callbacks). A single
    worker thread per device processes the queue, enforcing MIN_INTERVAL
    between the *completion* of one request and the *start* of the next.
    """

    def __init__(self, device_uid: str, secret: str, base_url: str):
        self.device_uid = device_uid
        self.secret = secret
        self.base_url = base_url
        self._queue: queue.Queue = queue.Queue()
        self._worker_running = False
        self._lock = threading.Lock()

    def enqueue(self, msg_type: str, **kwargs):
        """
        Non-blocking enqueue. msg_type is 'count' or 'heartbeat'.
        For 'count', pass count=int, status=str.
        """
        self._queue.put((msg_type, kwargs))
        self._ensure_worker()

    def _ensure_worker(self):
        with self._lock:
            if not self._worker_running:
                self._worker_running = True
                t = threading.Thread(target=self._worker, daemon=True)
                t.start()

    def _worker(self):
        """Process queued messages with rate limiting."""
        while True:
            try:
                msg_type, kwargs = self._queue.get(timeout=IDLE_TIMEOUT)
            except queue.Empty:
                with self._lock:
                    # Double-check: if something was added while we were
                    # deciding to exit, keep going
                    if self._queue.empty():
                        self._worker_running = False
                        return

            if msg_type == "count":
                send_count_data(
                    self.device_uid,
                    self.secret,
                    kwargs["count"],
                    kwargs["status"],
                    self.base_url,
                )
            elif msg_type == "heartbeat":
                send_heartbeat(self.device_uid, self.secret, self.base_url)

            # Enforce minimum interval AFTER the request completes
            time.sleep(MIN_INTERVAL)


# ─── Limiter Registry ───────────────────────────────────────────

_limiters: Dict[str, DeviceRateLimiter] = {}
_limiters_lock = threading.Lock()


def get_limiter(device_uid: str, secret: str, base_url: str) -> DeviceRateLimiter:
    """Get or create the rate limiter for a given device."""
    if device_uid not in _limiters:
        with _limiters_lock:
            if device_uid not in _limiters:
                _limiters[device_uid] = DeviceRateLimiter(device_uid, secret, base_url)
    return _limiters[device_uid]
