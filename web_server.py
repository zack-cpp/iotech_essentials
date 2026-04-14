import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import DeviceDB
import paho.mqtt.client as mqtt
from flask_socketio import SocketIO
import json
import threading

app = Flask(__name__, static_folder='static')
CORS(app)
db = DeviceDB()

# Initialize WebSockets for real-time UI data
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup MQTT broker params to signal oee_node.py
MQTT_BROKER = os.getenv("NODE_MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("NODE_MQTT_PORT", 1883))
MQTT_USER = os.getenv("NODE_MQTT_USERNAME", "andon_gateway")
MQTT_PASS = os.getenv("NODE_MQTT_PASSWORD", "andon_gateway")

def notify_gateway_hot_reload():
    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        if MQTT_USER and MQTT_PASS:
            client.username_pw_set(MQTT_USER, MQTT_PASS)
        client.connect(MQTT_BROKER, MQTT_PORT, 5)
        client.publish("system/gateway/reload_config", "")
        client.disconnect()
        print("[WEB_SERVER] Gateway notified to hot-reload mappings via MQTT.")
    except Exception as e:
        print(f"[WEB_SERVER] Failed to trigger gateway hot-reload: {e}")

MQTT_INSPECT_TOPIC = os.getenv("INSPECT_MQTT_TOPIC", "inspect/devices")

# Background task for consuming live gateway data for WebSockets
def mqtt_background_listener():
    try:
        def on_connect(client, userdata, flags, reason_code, properties):
            # Subscribe to all telemetry from counting nodes
            client.subscribe("+/counting")
            if MQTT_INSPECT_TOPIC:
                client.subscribe(MQTT_INSPECT_TOPIC)
            print("[WEB_SERVER] Connected to MQTT for Live UI Telemetry")
            
        def on_message(client, userdata, msg):
            try:
                topic = msg.topic
                payload_str = msg.payload.decode('utf-8', errors='replace')
                data = json.loads(payload_str)
                # Emit metrics automatically to browser sockets
                socketio.emit('live_device_metric', {'topic': topic, 'data': data})
            except Exception:
                pass

        listen_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        if MQTT_USER and MQTT_PASS:
            listen_client.username_pw_set(MQTT_USER, MQTT_PASS)
        listen_client.on_connect = on_connect
        listen_client.on_message = on_message
        
        import time
        while True:
            try:
                listen_client.connect(MQTT_BROKER, MQTT_PORT, 60)
                break
            except Exception as e:
                print(f"[WEB_SERVER] MQTT Connection failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)
                
        listen_client.loop_forever()
    except Exception as e:
        print(f"[WEB_SERVER] Background MQTT Listener failed: {e}")

# Spawn the MQTT reading thread
mqtt_thread = threading.Thread(target=mqtt_background_listener, daemon=True)
mqtt_thread.start()

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify(error=str(e)), 500

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/devices', methods=['GET'])
def get_devices():
    devices = db.get_all_devices()
    return jsonify(devices)

@app.route('/api/devices', methods=['POST'])
def add_device():
    data = request.json
    required_fields = ['device_id_from', 'device_id_to', 'device_secret', 'ok_channel', 'ng_channel']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400
    
    new_id = db.add_device(data)
    notify_gateway_hot_reload()
    return jsonify(id=new_id, message="Device mapping added successfully"), 201

@app.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    data = request.json
    # gateway_id is technically optional in the database logic (it falls back to env) but usually comes in updates.
    required_fields = ['device_id_from', 'device_id_to', 'device_secret', 'ok_channel', 'ng_channel']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400
            
    success = db.update_device(device_id, data)
    if success:
        notify_gateway_hot_reload()
        return jsonify(message="Device mapping updated successfully")
    else:
        return jsonify(error="Device not found"), 404

@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    success = db.delete_device(device_id)
    if success:
        notify_gateway_hot_reload()
        return jsonify(message="Device mapping deleted successfully")
    else:
        return jsonify(error="Device not found"), 404

# ================= INSPECTION API =================

@app.route('/api/inspectors', methods=['GET'])
def get_inspection_devices():
    devices = db.get_all_inspection_devices()
    return jsonify(devices)

@app.route('/api/inspectors', methods=['POST'])
def add_inspection_device():
    data = request.json
    required_fields = ['device_id_from', 'device_id_to', 'device_secret', 'total_sensor']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400
    
    new_id = db.add_inspection_device(data)
    notify_gateway_hot_reload()
    return jsonify(id=new_id, message="Inspection mapping added successfully"), 201

@app.route('/api/inspectors/<int:device_id>', methods=['PUT'])
def update_inspection_device(device_id):
    data = request.json
    required_fields = ['device_id_from', 'device_id_to', 'device_secret', 'total_sensor']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400
            
    success = db.update_inspection_device(device_id, data)
    if success:
        notify_gateway_hot_reload()
        return jsonify(message="Inspection mapping updated successfully")
    else:
        return jsonify(error="Device not found"), 404

@app.route('/api/inspectors/<int:device_id>', methods=['DELETE'])
def delete_inspection_device(device_id):
    success = db.delete_inspection_device(device_id)
    if success:
        notify_gateway_hot_reload()
        return jsonify(message="Inspection mapping deleted successfully")
    else:
        return jsonify(error="Device not found"), 404

if __name__ == '__main__':
    port = int(os.environ.get("FLASK_PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
