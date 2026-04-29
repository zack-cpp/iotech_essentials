"""
OEE IoT Gateway — FastAPI Application

Main entrypoint for the web API. Handles CORS, mounts CRUD routers,
and runs database auto-migration on startup.
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import devices, inspectors, status, fusion


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hooks."""
    # --- Startup ---
    print("[API] Initializing database tables...")
    # Retry loop for DB readiness
    for attempt in range(10):
        try:
            init_db()
            print("[API] Database ready.")
            break
        except Exception as e:
            print(f"[API] DB not ready (attempt {attempt + 1}/10): {e}")
            time.sleep(3)
    else:
        print("[API] WARNING: Could not connect to database after 10 attempts.")

    yield

    # --- Shutdown ---
    print("[API] Shutting down.")


app = FastAPI(
    title="OEE IoT Gateway",
    description="MQTT-to-HTTP bridge with device management dashboard",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow the Nginx frontend and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(devices.router)
app.include_router(inspectors.router)
app.include_router(status.router)
app.include_router(fusion.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "oee-gateway-api"}
