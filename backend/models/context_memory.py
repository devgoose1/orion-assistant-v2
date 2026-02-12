"""
ContextMemory model - long-term memory/knowledge base
"""
from sqlalchemy import Column, String, TIMESTAMP, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base
import uuid

class ContextMemory(Base):
    __tablename__ = 'context_memory'
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Memory key-value
    key = Column(String, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    
    # Scope
    device_id = Column(String, ForeignKey('devices.device_id'), nullable=True, index=True)
    scope = Column(String, default='global', index=True)  # global, device, session
    
    # Metadata
    category = Column(String, nullable=True, index=True)
    tags = Column(JSON, default=[])  # Array stored as JSON for SQLite
    
    # Expiration
    expires_at = Column(TIMESTAMP, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'device_id': self.device_id,
            'scope': self.scope,
            'category': self.category,
            'tags': self.tags,
            'expires_at': self.expires_at.isoformat() if self.expires_at is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }
