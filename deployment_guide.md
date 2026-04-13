# OEE Master Gateway Deployment Guide

This guide details the procedure for deploying exactly this containerized software suite (OEE Gateway, Web-UI, and Postgres Database) identically onto any new edge device or server using Docker Compose.

## 1. System Requirements
- **OS**: Any generic Linux edge deployment (Ubuntu, Debian, Raspberry Pi OS) or Windows (via WSL2).
- **Core Dependencies**:
  - [Docker](https://docs.docker.com/engine/install/)
  - [Docker Compose](https://docs.docker.com/compose/install/)

---

## 2. Prepare the Payload
Copy the core directory to your new edge device. You do **not** need `node_modules`, standard python caching folders, or local container volumes.
You only need the core source files:
- `docker-compose.yml`
- `Dockerfile`
- `.env`
- `supervisord.conf`
- `init.sql`
- `*.py` backend files
- `frontend/` folder

*Tip: A `git clone` or a compressed `.zip` is usually the safest method to transfer.*

---

## 3. Configure the Identity (`.env`)
Navigate to the transferred folder payload on your new device and inspect your `.env` file!

**Crucial Steps:**
1. **Network Configuration:** Update `NODE_MQTT_HOST` appropriately if the new gateway bridges to a different external MQTT cluster.
2. **Device Identity:** Update `GATEWAY_ID` (e.g., `GATEWAY_ID=NEW_EDGE_DEVICE_01`). This ID categorizes database entries directly.
3. **Database Defaults:** (Optional) Re-roll the `POSTGRES_PASSWORD` and `DB_PASSWORD` uniquely to secure the new PostgreSQL array. Keep them matched.

---

## 4. Spin Up the Ecosystem
Because we compiled the entire infrastructure (Node UI Compiler, Flask Proxy Server, UDP Thread Listener, and Multi-Process Supervisor) natively into purely one single container block under Docker Compose, deployment is identical globally:

```bash
# Enter the deployment folder
cd /path/to/iotech_essentials

# Build and deploy the array into the background
docker compose up -d --build
```
> **Note**: Because this heavily uses Multi-Stage Node caching inside the Dockerfile, the very first initial `--build` footprint will take up to ~80 seconds, but all subsequent restarts (`docker compose restart`) are sub-second.

---

## 5. Verifying Deployment
If everything went smoothly, the following checks should pass natively on your edge device:

1. **Dashboard Check-In**: Open a browser on the matching network and hit the localized IP or `http://localhost:5000`. You will see the React GUI Glassmorphic layout.
2. **Component Integrity Logs**:
    To manually ensure that Supervisor has correctly engaged all three native python services internally:
    ```bash
    docker exec -it web-ui supervisorctl status
    ```
    *Output should declare `oee_node`, `oee_inspect`, and `web_ui` explicitly as `RUNNING`.*

### Fresh Database Behaviors
Because this is a brand new edge installation without the `postgres_data` persistent volume mappings transferred over from your original testbench:
- The system will naturally execute `init.sql` during its very first PostgreSQL initialization! 
- The `devices` and `inspection_devices` schema tables will be fully structured and auto-filled with your generic dummy configurations naturally upon startup!
- Consequently, you will **not** experience the PostgreSQL `relation does not exist` debugging exceptions seen locally during mid-deployment schema overhauls.
