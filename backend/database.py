from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CountingDevice(Base):
    __tablename__ = "counting_devices"

    id = Column(Integer, primary_key=True, index=True)
    gateway_id = Column(String(50), nullable=False)
    node_id = Column(String(50), nullable=False)
    cloud_uid = Column(String(100), nullable=False)
    device_secret = Column(String(150), nullable=False)
    ok_channel = Column(Integer, nullable=False, default=0)
    ng_channel = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InspectionDevice(Base):
    __tablename__ = "inspection_devices"

    id = Column(Integer, primary_key=True, index=True)
    gateway_id = Column(String(50), nullable=False)
    node_id = Column(String(50), nullable=False)
    cloud_uid = Column(String(100), nullable=False)
    device_secret = Column(String(150), nullable=False)
    total_sensor = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist (auto-migration on boot)."""
    Base.metadata.create_all(bind=engine)
