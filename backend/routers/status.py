import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db, CountingDevice, InspectionDevice
from schemas import GatewayStatus
from config import get_settings

router = APIRouter(prefix="/api/status", tags=["Gateway Status"])
settings = get_settings()

# Track app start time
_start_time = time.time()


@router.get("", response_model=GatewayStatus)
def get_status(db: Session = Depends(get_db)):
    """Returns gateway health information."""
    counting_count = db.query(CountingDevice).filter(CountingDevice.gateway_id == settings.GATEWAY_ID).count()
    inspection_count = db.query(InspectionDevice).filter(InspectionDevice.gateway_id == settings.GATEWAY_ID).count()

    return GatewayStatus(
        gateway_id=settings.GATEWAY_ID,
        mqtt_connected=True,  # Will be wired to actual MQTT client state later
        counting_devices=counting_count,
        inspection_devices=inspection_count,
        uptime_seconds=round(time.time() - _start_time, 1),
    )
