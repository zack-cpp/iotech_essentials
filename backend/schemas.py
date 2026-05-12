from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ==================== Counting Devices ====================

class CountingDeviceBase(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=50, examples=["C071"])
    cloud_uid: str = Field(..., min_length=1, max_length=100, examples=["dd880e00-xxxx-xxxx"])
    device_secret: str = Field(..., min_length=1, max_length=150, examples=["N0Tlslo..."])
    ok_channel: int = Field(default=0, ge=0, examples=[0])
    ng_channel: int = Field(default=1, ge=0, examples=[1])
    is_active: bool = True


class CountingDeviceCreate(CountingDeviceBase):
    gateway_id: Optional[str] = None


class CountingDeviceUpdate(CountingDeviceBase):
    gateway_id: Optional[str] = None


class CountingDeviceResponse(CountingDeviceBase):
    id: int
    gateway_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Inspection Devices ====================

class InspectionDeviceBase(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=50, examples=["Q005"])
    cloud_uid: str = Field(..., min_length=1, max_length=100, examples=["dd880e00-xxxx-xxxx"])
    device_secret: str = Field(..., min_length=1, max_length=150, examples=["N0Tlslo..."])
    total_sensor: int = Field(default=1, ge=1, examples=[12])
    is_active: bool = True


class InspectionDeviceCreate(InspectionDeviceBase):
    gateway_id: Optional[str] = None


class InspectionDeviceUpdate(InspectionDeviceBase):
    gateway_id: Optional[str] = None


class InspectionDeviceResponse(InspectionDeviceBase):
    id: int
    gateway_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Gateway Status ====================

class GatewayStatus(BaseModel):
    gateway_id: str
    mqtt_connected: bool = False
    counting_devices: int = 0
    inspection_devices: int = 0
    uptime_seconds: float = 0


# ==================== Sensor Fusion Rules ====================

class SensorFusionRuleBase(BaseModel):
    source_node_id: str = Field(..., min_length=1, max_length=50)
    source_channel: int = Field(..., ge=0)
    source_field: str = Field(default="voltage", min_length=1, max_length=50)
    formula: str = Field(..., min_length=1, max_length=500)
    destination_node_id: str = Field(..., min_length=1, max_length=50)
    destination_channel: int = Field(..., ge=0)
    is_active: bool = True


class SensorFusionRuleCreate(SensorFusionRuleBase):
    gateway_id: Optional[str] = None


class SensorFusionRuleUpdate(SensorFusionRuleBase):
    gateway_id: Optional[str] = None


class SensorFusionRuleResponse(SensorFusionRuleBase):
    id: int
    gateway_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SensorFusionValidateRequest(BaseModel):
    formula: str
    source_field: str = "voltage"
    dummy_value: float = 1.0
