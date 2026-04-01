import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import DeviceDB

app = Flask(__name__, static_folder='static')
CORS(app)
db = DeviceDB()

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
        return jsonify(message="Device mapping updated successfully")
    else:
        return jsonify(error="Device not found"), 404

@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    success = db.delete_device(device_id)
    if success:
        return jsonify(message="Device mapping deleted successfully")
    else:
        return jsonify(error="Device not found"), 404

if __name__ == '__main__':
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
