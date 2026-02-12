"""
Session model - represents conversation sessions
"""
from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid

class Session(Base):
    __tablename__ = 'sessions'
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to device
    device_id = Column(String, ForeignKey('devices.device_id'), nullable=False, index=True)
    
    # Session status
    is_active = Column(Boolean, default=True, index=True)
    
    # Context (JSON storage)
    context = Column(JSON, default={})
    
    # Statistics
    message_count = Column(Integer, default=0)
    tool_execution_count = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    ended_at = Column(TIMESTAMP, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'is_active': self.is_active,
            'context': self.context,
            'message_count': self.message_count,
            'tool_execution_count': self.tool_execution_count,
            'started_at': self.started_at.isoformat() if self.started_at is not None else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at is not None else None
        }
