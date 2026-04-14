from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db, InspectionDevice
from schemas import InspectionDeviceCreate, InspectionDeviceUpdate, InspectionDeviceResponse
from config import get_settings
from services.mqtt_notify import notify_gateway_reload

router = APIRouter(prefix="/api/inspectors", tags=["Inspection Devices"])
settings = get_settings()


@router.get("", response_model=List[InspectionDeviceResponse])
def list_inspectors(db: Session = Depends(get_db)):
    """List all inspection device mappings."""
    return db.query(InspectionDevice).order_by(InspectionDevice.created_at.desc()).all()


@router.get("/{device_id}", response_model=InspectionDeviceResponse)
def get_inspector(device_id: int, db: Session = Depends(get_db)):
    """Get a single inspection device by ID."""
    device = db.query(InspectionDevice).filter(InspectionDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Inspection device not found")
    return device


@router.post("", response_model=InspectionDeviceResponse, status_code=201)
def create_inspector(data: InspectionDeviceCreate, db: Session = Depends(get_db)):
    """Create a new inspection device mapping."""
    device = InspectionDevice(
        gateway_id=data.gateway_id or settings.GATEWAY_ID,
        node_id=data.node_id,
        cloud_uid=data.cloud_uid,
        device_secret=data.device_secret,
        total_sensor=data.total_sensor,
        is_active=data.is_active,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    notify_gateway_reload()
    return device


@router.put("/{device_id}", response_model=InspectionDeviceResponse)
def update_inspector(device_id: int, data: InspectionDeviceUpdate, db: Session = Depends(get_db)):
    """Update an existing inspection device mapping."""
    device = db.query(InspectionDevice).filter(InspectionDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Inspection device not found")

    device.gateway_id = data.gateway_id or settings.GATEWAY_ID
    device.node_id = data.node_id
    device.cloud_uid = data.cloud_uid
    device.device_secret = data.device_secret
    device.total_sensor = data.total_sensor
    device.is_active = data.is_active

    db.commit()
    db.refresh(device)
    notify_gateway_reload()
    return device


@router.delete("/{device_id}")
def delete_inspector(device_id: int, db: Session = Depends(get_db)):
    """Delete an inspection device mapping."""
    device = db.query(InspectionDevice).filter(InspectionDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Inspection device not found")

    db.delete(device)
    db.commit()
    notify_gateway_reload()
    return {"message": "Inspection device deleted successfully"}
