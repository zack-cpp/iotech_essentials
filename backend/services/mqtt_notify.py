"""
MQTT notification helper — publishes a reload signal so the MQTT worker
processes pick up database changes (hot-swap).
"""
import paho.mqtt.client as mqtt
from config import get_settings


def notify_gateway_reload():
    """Publish a reload signal to the MQTT broker."""
    settings = get_settings()
    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
        client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 5)
        client.publish("system/gateway/reload_config", "")
        client.disconnect()
        print("[API] Gateway notified to hot-reload mappings via MQTT.")
    except Exception as e:
        print(f"[API] Failed to trigger gateway hot-reload: {e}")
