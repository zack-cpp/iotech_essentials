import os
import datetime
import threading

# Create logs directory at backend/logs
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

class MqttLogger:
    """
    Thread-safe logger for MQTT payloads, writing to date-stamped log files.
    Maintains enable/disable state per device.
    Since this is instantiated per-process, the MQTT control topic must be 
    subscribed to by each process that uses this logger.
    """
    def __init__(self):
        self.enabled_devices = {}
        self.lock = threading.Lock()
        
        if not os.path.exists(LOGS_DIR):
            try:
                os.makedirs(LOGS_DIR)
            except Exception as e:
                print(f"[LOGGER] Error creating logs directory: {e}")

    def enable(self, device_id: str):
        """Enable logging for a specific device or 'all'."""
        with self.lock:
            self.enabled_devices[device_id] = True
            print(f"[LOGGER] Logging enabled for: {device_id}")

    def disable(self, device_id: str):
        """Disable logging for a specific device or 'all'."""
        with self.lock:
            if device_id == "all":
                self.enabled_devices.clear()
            else:
                self.enabled_devices[device_id] = False
            print(f"[LOGGER] Logging disabled for: {device_id}")

    def is_enabled(self, device_id: str) -> bool:
        """Check if logging is active for a device."""
        with self.lock:
            state = self.enabled_devices.get(device_id)
            if state is not None:
                return state
            return self.enabled_devices.get("all", False)

    def log(self, device_id: str, topic: str, payload: str):
        """Write a log line if logging is enabled for the device."""
        if not self.is_enabled(device_id):
            return
            
        now = datetime.datetime.now()
        date_str = now.strftime("%d-%m-%Y")
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        log_file = os.path.join(LOGS_DIR, f"{date_str}.log")
        # Ensure payload is on a single line if it contains newlines
        safe_payload = payload.replace('\n', ' ').replace('\r', '')
        log_line = f"[{time_str}] [{device_id}] [{topic}] {safe_payload}\n"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"[LOGGER] Error writing to log file: {e}")

# Singleton instance for the current process
mqtt_logger = MqttLogger()
