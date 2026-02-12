"""
Event model - device events (low disk space, errors, etc.)
"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.sql import func
from database import Base
import uuid

class Event(Base):
    __tablename__ = 'events'
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key
    device_id = Column(String, ForeignKey('devices.device_id'), nullable=False, index=True)
    
    # Event details
    event_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)  # info, warning, error, critical
    data = Column(JSON, nullable=True)
    
    # Status
    acknowledged = Column(Boolean, default=False, index=True)
    resolved = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    acknowledged_at = Column(TIMESTAMP, nullable=True)
    resolved_at = Column(TIMESTAMP, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'event_type': self.event_type,
            'severity': self.severity,
            'data': self.data,
            'acknowledged': self.acknowledged,
            'resolved': self.resolved,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at is not None else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at is not None else None
        }
