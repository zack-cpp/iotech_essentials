# OEE IoT Gateway CLI Tool

The OEE IoT Gateway includes a powerful Command Line Interface (CLI) for managing device configurations. This tool is designed to work seamlessly with the existing backend, ensuring that all data validation and hot-reload signals are shared with the web dashboard.

## 🚀 Architecture

The CLI acts as a pure API client. It communicates with the FastAPI backend over HTTP. This means:
* **Centralized Logic**: Business logic and database integrity are maintained by the backend.
* **Hot-Reload Support**: Adding or updating devices via the CLI immediately triggers MQTT reload signals to edge nodes.
* **Remote Management**: The CLI can target the local gateway or a remote one over the LAN/Web.

---

## 🛠 Setup & Usage

The CLI is best used via the provided Docker container, but it can also be run locally with Python.

### 1. Via Docker (Recommended)
The CLI is integrated into the `docker-compose.yml` under the `cli` profile.

```bash
# Run a command (e.g., status)
docker compose run --rm cli status
```

### 2. Local Python Setup
If you prefer running it outside Docker:
```bash
pip install -r requirements-cli.txt
python gateway_cli.py status
```

---

## 📖 Global Options

These flags can be used before any command:

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--api-url`, `-u` | Base URL of the target API | `http://localhost:8000` |
| `--json`, `-j` | Output raw JSON instead of tables | `False` |

*Example: Targeting a remote machine with JSON output*
```bash
docker compose run --rm cli --api-url http://192.168.1.50:8000 --json status
```

---

## 📋 Command Reference

### `status`
Displays the current system health, device counts, and uptime.
```bash
docker compose run --rm cli status
```

---

### `counting` Commands
Manage production throughput (OK/NG) nodes.

| Command | Usage | Description |
| :--- | :--- | :--- |
| `list` | `cli counting list` | Shows all counting devices in a table. |
| `get` | `cli counting get [ID]` | Shows detailed info for a specific device. |
| `add` | `cli counting add [FLAGS]` | Creates a new device (interactive if flags missing). |
| `update` | `cli counting update [ID] [FLAGS]` | Updates specified fields for a device. |
| `delete` | `cli counting delete [ID]` | Deletes a device (requires confirmation). |

**Add Device Flags:**
`--node-id`, `--cloud-uid`, `--device-secret`, `--ok-channel`, `--ng-channel`, `--active/--inactive`

**Update Examples:**
```bash
# Rename node
docker compose run --rm cli counting update 1 --node-id NEW_ID

# Toggle status
docker compose run --rm cli counting update 1 --inactive
```

---

### `inspection` Commands
Manage quality control sensor nodes.

| Command | Usage | Description |
| :--- | :--- | :--- |
| `list` | `cli inspection list` | Shows all inspection devices in a table. |
| `get` | `cli inspection get [ID]` | Shows detailed info for a specific device. |
| `add` | `cli inspection add [FLAGS]` | Creates a new device. |
| `update` | `cli inspection update [ID] [FLAGS]` | Updates specified fields. |
| `delete` | `cli inspection delete [ID]` | Deletes a device. |

**Add Device Flags:**
`--node-id`, `--cloud-uid`, `--device-secret`, `--total-sensor`, `--active/--inactive`

---

### `log` Commands
Control MQTT message logging per device. Logs are written to `backend/logs/dd-mm-yyyy.log`.

| Command | Usage | Description |
| :--- | :--- | :--- |
| `status` | `cli log status` | Show which devices have logging enabled/disabled. |
| `enable` | `cli log enable [DEVICE_ID]` | Enable logging for a device (or `all`). |
| `disable` | `cli log disable [DEVICE_ID]` | Disable logging for a device (or `all`). |

**Examples:**
```bash
# Enable logging for a specific node
docker compose run --rm cli log enable NODE_01

# Enable logging for all devices
docker compose run --rm cli log enable all

# Disable logging
docker compose run --rm cli log disable NODE_01
```

**Notes:**
- Logs are stored in `backend/logs/` inside the backend container, one file per day (`dd-mm-yyyy.log`).
- Each line: `[timestamp] [device_id] [topic] payload`
- For counting devices, the device ID is the `node_id`.
- For inspection devices, the device ID is the `MESIN_ID` from the message payload.
- Logging state is held in memory per worker process and resets on restart.

---

## 💡 Pro Tips

### Interactive Prompts
If you run `add` without any flags, the CLI will guide you through the process with interactive prompts and masked input for secrets.

### Scripting with JSON
Use the `--json` flag to pipe data into other tools like `jq`.
```bash
# Get only the Cloud UID of device #2
docker compose run --rm cli --json counting get 2 | jq -r '.cloud_uid'
```

### Force Delete
Skip the deletion confirmation prompt.
```bash
docker compose run --rm cli counting delete 5 --force
```

### Windows Compatibility
The CLI automatically uses ASCII surrogates for symbols (OK/X instead of Checkmarks) when running in environments where Unicode rendering might be unstable (like legacy Windows consoles).
