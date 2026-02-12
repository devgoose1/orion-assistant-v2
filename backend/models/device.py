"""
Device model - represents connected devices
"""
from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, JSON, ARRAY, Text
from sqlalchemy.sql import func
from database import Base
import uuid

class Device(Base):
    __tablename__ = 'devices'
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Device identification
    device_id = Column(String, unique=True, nullable=False, index=True)
    hostname = Column(String, nullable=False)
    os_type = Column(String, nullable=False)  # Windows, Linux, macOS
    os_version = Column(String)
    
    # Capabilities (JSON)
    capabilities = Column(JSON, default={})
    
    # Permissions (stored as JSON for SQLite compatibility)
    # Will use proper ARRAY for PostgreSQL
    allowed_tools = Column(JSON, default=[])
    allowed_paths = Column(JSON, default=[])
    allowed_apps = Column(JSON, default=[])
    
    # Hardware metadata
    cpu_info = Column(Text)
    ram_gb = Column(Integer)
    disk_gb = Column(Integer)
    
    # Status
    status = Column(String, default='online')  # online, idle, offline
    last_heartbeat = Column(TIMESTAMP)
    
    # Timestamps
    registered_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'hostname': self.hostname,
            'os_type': self.os_type,
            'os_version': self.os_version,
            'capabilities': self.capabilities,
            'allowed_tools': self.allowed_tools,
            'allowed_paths': self.allowed_paths,
            'allowed_apps': self.allowed_apps,
            'cpu_info': self.cpu_info,
            'ram_gb': self.ram_gb,
            'disk_gb': self.disk_gb,
            'status': self.status,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat is not None else None,
            'registered_at': self.registered_at.isoformat() if self.registered_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }
