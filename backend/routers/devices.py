from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db, CountingDevice
from schemas import CountingDeviceCreate, CountingDeviceUpdate, CountingDeviceResponse
from config import get_settings
from services.mqtt_notify import notify_gateway_reload

router = APIRouter(prefix="/api/devices", tags=["Counting Devices"])
settings = get_settings()


@router.get("", response_model=List[CountingDeviceResponse])
def list_devices(db: Session = Depends(get_db)):
    """List all counting device mappings."""
    return db.query(CountingDevice).order_by(CountingDevice.created_at.desc()).all()


@router.get("/{device_id}", response_model=CountingDeviceResponse)
def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get a single counting device by ID."""
    device = db.query(CountingDevice).filter(CountingDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("", response_model=CountingDeviceResponse, status_code=201)
def create_device(data: CountingDeviceCreate, db: Session = Depends(get_db)):
    """Create a new counting device mapping."""
    device = CountingDevice(
        gateway_id=data.gateway_id or settings.GATEWAY_ID,
        node_id=data.node_id,
        cloud_uid=data.cloud_uid,
        device_secret=data.device_secret,
        ok_channel=data.ok_channel,
        ng_channel=data.ng_channel,
        is_active=data.is_active,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    notify_gateway_reload()
    return device


@router.put("/{device_id}", response_model=CountingDeviceResponse)
def update_device(device_id: int, data: CountingDeviceUpdate, db: Session = Depends(get_db)):
    """Update an existing counting device mapping."""
    device = db.query(CountingDevice).filter(CountingDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.gateway_id = data.gateway_id or settings.GATEWAY_ID
    device.node_id = data.node_id
    device.cloud_uid = data.cloud_uid
    device.device_secret = data.device_secret
    device.ok_channel = data.ok_channel
    device.ng_channel = data.ng_channel
    device.is_active = data.is_active

    db.commit()
    db.refresh(device)
    notify_gateway_reload()
    return device


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Delete a counting device mapping."""
    device = db.query(CountingDevice).filter(CountingDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    notify_gateway_reload()
    return {"message": "Device deleted successfully"}
